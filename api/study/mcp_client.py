import asyncio
from mcp import StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

async def main() -> None:
    # 初始化服务端连接参数
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "--directory",
            "/Users/hedon/mycode/python/mini-manus/api",
            "run",
            "./study/mcp_server.py",
        ],
        env=None,
    )

    # 创建一个异步上下文管理器
    exit_stack = AsyncExitStack()

    # 创建标准输入输出客户端
    try:
        # 获取写入和写出流
        transport = await exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = transport

        # 创建客户端会话上下文
        session = await exit_stack.enter_async_context(ClientSession(stdio, write))
        
        # 初始化 mcp 服务器连接
        await session.initialize()

        # 获取工具列表信息
        list_tools_response = await session.list_tools()
        tools = list_tools_response.tools
        print("工具列表：", [tool.name for tool in tools])

        # 调用工具
        call_tool_response = await session.call_tool("calculator", {"expression": "100+10"})
        print("工具结果：", call_tool_response)
    finally:
        await exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())
