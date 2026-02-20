from abc import ABC
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
import asyncio
import uuid

from app.domain.external.json_parser import JsonParser
from app.domain.external.llm import LLM
from app.domain.models.event import ErrorEvent, Event, ToolEvent, ToolEventStatus
from app.domain.models.memory import Memory
from app.domain.models.message import Message
from app.domain.models.tool_result import ToolResult
from app.domain.models.app_config import AgentConfig
from app.domain.services.tools.base import BaseTool

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """基础 Agent 智能体"""
    name: str = "" # 智能体名字
    _system_prompt: str = "" # 系统预设提示词
    _format: Optional[str] = None # Agent 的响应格式
    _retry_interval: float = 1.0 # 重试间隔
    _tool_choice: Optional[str] = None # 工具选择策略

    def __init__(
        self,
        agent_config: AgentConfig,  # Agent 配置
        llm: LLM,                   # 语言模型协议
        memory: Memory,             # 记忆
        json_parser: JsonParser,    # JSON 输出解析器
        tools: List[BaseTool],      # 工具列表
    ) -> None:
        self._agent_config = agent_config
        self._llm = llm
        self._memory = memory
        self._json_parser = json_parser
        self._tools = tools

    @property
    def memory(self) -> Memory:
        return self._memory

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取 Agent 所有可用的工具列表参数声明"""
        available_tools = []
        for tool in self._tools:
            available_tools.extend(tool.get_tools())
        return available_tools
    
    def _get_tool(self, tool_name: str) -> BaseTool:
        """获取对应工具所在的工具集"""
        for tool in self._tools:
            if tool.has_tool(tool_name):
                return tool
        raise ValueError(f"未知工具: {tool_name}")

    async def _invoke_llm(self, messages: List[Dict[str, Any]], format: Optional[str] = None) -> Dict[str, Any]:
        """调用语言模型并处理记忆内容"""
        # 1. 将消息添加到记忆中
        await self._add_to_memory(messages)

        # 2. 组装语言模型的响应格式
        response_format = {"type": format} if format else None

        # 3. 循环向 LLM 发起提问直到最大重试次数
        for _ in range(self._agent_config.max_retries):
            try:
                # 4. 调用语言模型获取响应内容
                message = await self._llm.invoke(
                    messages=messages,
                    tools=self._get_available_tools(),
                    response_format=response_format,
                    tool_choice=self._tool_choice,
                )

                # 5. 处理 AI 响应内容，避免空回复
                if message.get("role") == "assistant":
                    if not message.get("content") and not message.get("tool_calls"):
                        logger.warning(f"LLM 回复了空内容，执行重试")
                        await self._add_to_memory([
                            {"role": "assistant", "content": ""},
                            {"role": "user", "content": "AI 无响应内容，请继续。"}
                        ])
                        await asyncio.sleep(self._retry_interval)
                        continue

                    # 6. 取出非空消息并处理工具调用
                    filtered_message = {"role": "assistant", "content": message.get("content")}
                    if message.get("tool_calls"):
                        # 7. 取出工具调用的数据，限制 LLM 一次只能调用一个工具
                        filtered_message["tool_calls"] = message.get("tool_calls")[:1]
                else:
                    # 8. 非 AI 消息则记录日志并存储消息
                    logger.warning(f"LLM 响应内容无法确认消息角色: {message.get("role")}")
                    filtered_message = message

                # 9. 将消息添加到记忆中
                await self._add_to_memory([filtered_message])

            except Exception as e:
                logger.error(f"调用语言模型发生错误: {str(e)}")
                await asyncio.sleep(self._retry_interval)
                continue

    async def _invoke_tool(self, tool: BaseTool, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """调用工具"""
        err = ""
        for _ in range(self._agent_config.max_retries):
            try:
                return await tool.invoke(tool_name, **arguments)
            except Exception as e:
                err = str(e)
                logger.exception(f"调用工具[{tool_name}]出错，错误: {err}")
                await asyncio.sleep(self._retry_interval)
                continue
        
        return ToolResult(success=False, message=err)
    
    async def _add_to_memory(self, messages: List[Dict[str, Any]]) -> None:
        """将对应的信息添加到记忆中"""
        if self._memory.empty:
            self._memory.add_message({
                "role": "system",
                "content": self._system_prompt,
            })
        self._memory.add_messages(messages)

    async def compact_memory(self) -> None:
        """压缩记忆"""
        self._memory.compact()

    async def roll_back(self, message: Message) -> None:
        """Agent 状态回滚，该函数用于确保 Agent 消息列表状态是正确的，用于发送新消息、停止任务、通知用户"""
        # 1. 取出记忆中的最后一条消息，检查是否是工具调用
        last_message = self._memory.get_last_message()
        if (
            not last_message or
            not last_message.get("tool_calls") or
            len(last_message.get("tool_calls")) == 0
        ):
            return
        
        # 2. 取出消息中的工具调用参数
        tool_call = last_message.get("tool_calls")[0]

        # 3. 提取工具名字和 id
        function_name = tool_call.get("function", {}).get("name")
        tool_call_id = tool_call.get("id")

        # 4. 判断当前工具是否是通知用户(message_ask_user)
        if function_name == "message_ask_user":
            self.memory.add_message({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "function_name": function_name,
                "content": message.model_dump_json(),
            })
        else:
            # 5. 否则直接删除最后一条消息
            self._memory.roll_back()

    async def invoke(self, query: str, format: Optional[str] = None) -> AsyncGenerator[Event, None]:
        """传递消息+响应格式调用程序生成异步迭代内容"""
        format = format if format else self._format
        
        message = await self._invoke_llm(
            [{"role": "user", "content": query}],
            format,
        )

        for _ in range(self._agent_config.max_iterations):
            if not message.get("tool_calls"):
                break
            tool_messages = []
            for tool_call in message["tool_calls"]:
                if not tool_call.get("function"):
                    continue

                tool_call_id = tool_call["id"] or str(uuid.uuid4())
                function_name = tool_call["function"]["name"]
                function_args = await self._json_parser.invoke(tool_call["function"]["arguments"])
                tool = self._get_tool(function_name)

                # 返回工具即将调用事件，TODO: tool_content 还没写
                yield ToolEvent(
                    tool_call_id=tool_call_id,
                    tool_name=tool.name,
                    function_name=function_name,
                    function_args=function_args,
                    status=ToolEventStatus.CALLING,
                )

                result = await self._invoke_tool(tool, function_name, function_args)

                # 返回工具执行结果事件
                yield ToolEvent(
                    tool_call_id=tool_call_id,
                    tool_name=tool.name,
                    function_name=function_name,
                    function_args=function_args,
                    function_result=result,
                    status=ToolEventStatus.CALLED,
                )

                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "function_name": function_name,
                    "content": result.model_dump(),
                })
            
            message = await self._invoke_llm(tool_messages)
        else:
            yield ErrorEvent(error=f"Agent 迭代操作最大次数: {self._agent_config.max_iterations}，任务处理失败")

