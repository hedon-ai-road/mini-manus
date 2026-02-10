from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream


from mcp.shared.message import SessionMessage


from mcp.client.streamable_http import GetSessionIdCallback


import asyncio
from contextlib import AsyncExitStack
import json
import os
import dotenv
from typing import Optional

from mcp.client.session import ClientSession
from mcp.client.session_group import streamable_http_client
from openai import OpenAI
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall

dotenv.load_dotenv()

GAODE_URL = f"https://mcp.amap.com/mcp?key={os.getenv('GAODE_KEY')}"
SYSTEM_PROMPT = """你是一个强大的智能机器人，可以根据用户的问题判断是否调用工具并最终解决用户的问题，不知道请直接说不知道。"""


class ReActAgent:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("DEEPSEEK_API_URL"),
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.model = "deepseek-chat"
        self.tools = []
        self.async_exit_stack = AsyncExitStack()
        self.mcp_session: Optional[ClientSession] = None
        

    async def init_mcp_session(self) -> None:
        transport: tuple[MemoryObjectReceiveStream[SessionMessage | Exception], MemoryObjectSendStream[SessionMessage], GetSessionIdCallback] = await self.async_exit_stack.enter_async_context(streamable_http_client(url=GAODE_URL))
        read, write, _ = transport
        self.mcp_session = await self.async_exit_stack.enter_async_context(ClientSession(read, write))
        await self.mcp_session.initialize()


    async def init_gaode_mcp(self) -> None :
        """初始化高德 MCP 服务"""
        list_tools_response = await self.mcp_session.list_tools()
        self.tools = [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema
            }
        }
        for tool in list_tools_response.tools
    ]

    async def call_gaode_mcp(self, name: str, arguments: dict) -> str:
        """调用高德 MCP 服务"""
        # 1. 发起请求调用高德 MCP 服务
        tools_call_response = await self.mcp_session.call_tool(name, arguments)
        tools_call_data = tools_call_response.content[0].text
        return tools_call_data

    async def process_query(self, query: str="") -> None:
        # 将用户传递的数据添加到消息列表中
        if query != "":
            self.messages.append({"role": "user", "content": query})
        print("Assistant: ", end="", flush=True)

        # 调用 deepseek 发送请求
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
            stream=True,
        )

        # 判断是否需要工具调用
        is_tool_calls = False
        content = ""
        tool_call_obj: dict[str, ChoiceDeltaToolCall] = {}

        for chunk in response:
            chunk_content = chunk.choices[0].delta.content
            chunk_tool_calls = chunk.choices[0].delta.tool_calls

            if chunk_content:
                content += chunk_content
            if chunk_tool_calls:
                for chunk_tool_call in chunk_tool_calls:
                    if tool_call_obj.get(chunk_tool_call.index) is None:
                        tool_call_obj[chunk_tool_call.index] = chunk_tool_call
                    else:
                        tool_call_obj[chunk_tool_call.index].function.arguments += chunk_tool_call.function.arguments

            # 如果是直接生成则流式打印内容
            if chunk_content:
                print(chunk_content, end="", flush=True)
            
            # 如果还未区分出生成的内容是答案还是工具调用，则循环判断
            if is_tool_calls is False:
                if chunk_tool_calls:
                    is_tool_calls = True

        # 如果是工具调用，则需要将 tool_calls_obj 转为列表
        tool_calls_json = [tool_call for tool_call in tool_call_obj.values()]

        # 将模型第一次回复的内容添加到列表中
        self.messages.append({
            "role": "assistant",
            "content": content if content != "" else None,
            "tool_calls": tool_calls_json if tool_calls_json else None,
        })

        if is_tool_calls:
            # 循环调用对应的工具
            for tool_call in tool_calls_json:
                tool_name = tool_call.function.name
                tool_arguments = json.loads(tool_call.function.arguments)
                print("\nTool Call:", tool_name)
                print("Tool Parameters:", tool_arguments)

                # 调用工具
                try:
                    result = await self.call_gaode_mcp(tool_name, tool_arguments)
                except Exception as e:
                    result = f"工具调用出错：Error: {str(e)}"

                print(f"Tool [{tool_name}] Result: {result}")

                # 将工具执行结果添加到信息中
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result,
                })
            await self.process_query()

        print("\n")

    async def chat_loop(self) -> None:
        while True:
            try:
                query = input("Query: ").strip()
                if query.lower() == "quit":
                    break
                await self.process_query(query)
            except Exception as e:
                print(f"\nError: {str(e)}")
            finally:
                await self.clearup()

    async def clearup(self):
        await self.async_exit_stack.aclose()

async def main() -> None:
    agent = ReActAgent()
    await agent.init_mcp_session()
    await agent.init_gaode_mcp()
    await agent.chat_loop()

if __name__ == "__main__":
    asyncio.run(main())