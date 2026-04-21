import logging
import asyncio
import io
from typing import AsyncGenerator, BinaryIO, Callable, List
import uuid
from fastapi import UploadFile
from pydantic import TypeAdapter
from datetime import datetime

from app.domain.models.search import SearchResults
from app.domain.models.tool_result import ToolResult
from core.config import get_settings
from app.domain.external.file_storage import FileStorage
from app.domain.external.json_parser import JsonParser
from app.domain.external.llm import LLM
from app.domain.external.task import Task, TaskRunner
from app.domain.models.app_config import A2AConfig, AgentConfig, MCPConfig
from app.domain.models.event import A2AToolContent, BaseEvent, BrowserToolContent, DoneEvent, ErrorEvent, Event, FileToolContent, MCPToolContent, MessageEvent, SearchToolContent, ShellToolContent, TitleEvent, ToolEvent, ToolEventStatus, WaitEvent
from app.domain.models.file import File
from app.domain.models.message import Message
from app.domain.models.session import SessionStatus
from app.domain.repositories.uow import IUnitOfWork
from app.domain.services.flows.planner_react import PlannerReActFlow
from app.domain.services.tools.a2a import A2ATool
from app.domain.services.tools.mcp import MCPTool
from app.domain.external.search import SearchEngine
from app.domain.external.browser import Browser
from app.domain.external.sandbox import Sandbox

logger = logging.getLogger(__name__)

class AgentTaskRunner(TaskRunner):
    """基于 Agent 智能体的任务运行器"""

    def __init__(
        self,
        llm: LLM, # 语言模型
        agent_config: AgentConfig, # Agent 配置
        mcp_config: MCPConfig, # MCP 配置
        a2a_config: A2AConfig, # A2A 配置
        session_id: str, # 会话 ID
        uow_factory: Callable[[], IUnitOfWork],
        file_storage: FileStorage, # 文件存储
        json_parser: JsonParser, # JSON 输出解析器
        browser: Browser, # 浏览器
        sandbox: Sandbox, # 沙箱
        search_engine: SearchEngine, # 搜索引擎
    ) -> None:
        self._session_id = session_id
        self._uow_factory = uow_factory
        self._uow = uow_factory()
        self._mcp_config = mcp_config
        self._mcp_tool = MCPTool()
        self._a2a_config = a2a_config
        self._a2a_tool = A2ATool()
        self._file_storage = file_storage
        self._browser = browser
        self._sandbox = sandbox
        self._flow = PlannerReActFlow(
            session_id=session_id,
            uow_factory=uow_factory,
            llm=llm,
            agent_config=agent_config,
            json_parser=json_parser,
            browser=browser,
            sandbox=sandbox,
            search_engine=search_engine,
            mcp_tool=self._mcp_tool,
            a2a_tool=self._a2a_tool,
        )

    async def invoke(self, task: Task) -> None:
        """根据传递的任务处理 agent 消息队列并运行 agent 流"""
        try:
            # 确保沙箱/MCP/A2A均初始化完成
            await self._sandbox.ensure_sandbox()
            await self._mcp_tool.initialize(self._mcp_config)
            await self._a2a_tool.initialize(self._a2a_config)

            # 循环读取任务中的输入消息队列
            while not await task.input_stream.is_empty():
                event = await self._pop_event(task)
                if event is None:
                    logger.warning("AgentTaskRunner 弹出空事件，跳过")
                    continue
                message = ""

                # 判断事件类型是否为消息事件，如果是则处理消息并将附近同步到沙箱中
                if isinstance(event, MessageEvent):
                    message = event.message or ""
                    await self._sync_message_attachments_to_sandbox(event)
                    logger.info(f"AgentTaskRunner 收到消息事件: {message[:50]}...")

                # 将消息事件转换为消息对象
                message_obj = Message(
                    message=message,
                    attachments=[attachment.filepath for attachment in event.attachments]
                )

                # 传递消息对象并运行 PlannerReActFlow
                async for event in self._run_flow(message_obj):
                    # 将得到的事件添加到消息队列中
                    await self._put_and_add_event(task, event)

                    # 根据不同的事件类型进行特殊处理
                    if isinstance(event, TitleEvent):
                        # 如果事件类型为标题事件则更新会话标题
                        async with self._uow:
                            await self._uow.session.update_title(self._session_id, event.title)
                    elif isinstance(event, MessageEvent):
                        # 如果是消息事件，则更新最新消息并新增未读消息数
                        async with self._uow:
                            await self._uow.session.update_latest_message(self._session_id, event.message, datetime.now())
                            await self._uow.session.increment_unread_message_count(self._session_id)
                    elif isinstance(event, WaitEvent):
                        # 如果是等待事件，则更新会话状态并终止流程
                        async with self._uow:
                            await self._uow.session.update_status(self._session_id, SessionStatus.WAITING)
                        return
                    
                    if not await task.input_stream.is_empty():
                        break
            
            # 更新会话状态为已完成
            async with self._uow:
                await self._uow.session.update_status(self._session_id, SessionStatus.COMPLETED)
        except asyncio.CancelledError:
            # 异步任务被取消，推送结束事件并更新状态
            logger.info(f"AgentTaskRunner 任务[{task.id}]被取消")
            await self._put_and_add_event(task, DoneEvent())
            async with self._uow:
                await self._uow.session.update_status(self._session_id, SessionStatus.COMPLETED)
            raise
        except Exception as e:
            logger.exception(f"AgentTaskRunner 任务[{task.id}]运行出错: {str(e)}")
            # 往任务消息队列写入异常数据并更新会话状态
            await self._put_and_add_event(task, ErrorEvent(error=f"AgentTaskRunner 运行出错: {str(e)}"))
            async with self._uow:
                await self._uow.session.update_status(self._session_id, SessionStatus.COMPLETED)
        finally:
            """
            在同一个 asyncio Task 上下文中清理 MCP/A2A 工具资源，
            确保不会在多个不同的 asyncio Task 上下文中重复清理。
            """
            await self._cleanup_tools()

    async def destory(self) -> None:
        """销毁任务并释放资源"""
        # 清除沙箱
        logger.info(f"开始清除 AgentTaskRunner 资源: {self._session_id}")
        if self._sandbox:
            logger.info(f"开始清除沙箱资源: {self._session_id}")
            await self._sandbox.destroy()

        # 清除 MCP 和 A2A 工具
        await self._cleanup_tools()

    async def on_done(self, task: Task) -> None:
        """执行任务完成时对应的回调函数"""
        logger.info("AgentTaskRunner 任务执行结束")

    async def _cleanup_tools(self) -> None:
        """清理 MCP 和 A2A 工具"""
        try:
            if self._mcp_tool:
                logger.info(f"清理 AgentTaskRunner 中的 MCP 工具: {self._session_id}")
                await self._mcp_tool.cleanup()
        except Exception as e:
            logger.warning(f"清理 AgentTaskRunner 中的 MCP 工具失败: {str(e)}")
        try:
            if self._a2a_tool:
                logger.info(f"清理 AgentTaskRunner 中的 A2A 工具: {self._session_id}")
                await self._a2a_tool.manager.cleanup()
        except Exception as e:
            logger.warning(f"清理 AgentTaskRunner 中的 A2A 工具失败: {str(e)}")

    async def _put_and_add_event(self, task: Task, event: Event) -> None:
        """往指定任务的消息队列写入事件数据并更新会话状态"""
        event_id = await task.output_stream.put(event.model_dump_json())
        event.id = event_id

        # 思考流式块（status="thinking"）仅推送到 Redis stream 供 SSE 实时传递，不持久化到 DB
        # 只有 status="done" 的思考摘要事件才持久化
        from app.domain.models.event import ThinkingEvent as _ThinkingEvent
        if isinstance(event, _ThinkingEvent) and event.status == "thinking":
            return

        async with self._uow:
            await self._uow.session.add_event(self._session_id, event)

    async def _pop_event(self, task: Task) -> Event:
        """从指定任务的消息队列中弹出事件数据"""
        event_id, event_str = await task.input_stream.pop()
        if event_str is None:
            logger.warning(f"AgentTaskRunner 收到空消息")
            return None
        
        event = TypeAdapter(Event).validate_json(event_str)
        event.id = event_id
        return event

    async def _sync_message_attachments_to_sandbox(self, event: MessageEvent) -> None:
        """将消息中的附件同步到沙箱中"""
        attachments: List[str] = []
        try:
            if event.attachments:
                for attachment in event.attachments:
                    file = await self._sync_file_to_sandbox(attachment.id)
                    if file:
                        attachments.append(file)
                        async with self._uow:
                            await self._uow.session.add_file(self._session_id, file)
        
            event.attachments = attachments
        except Exception as e:
            logger.exception(f"AgentTaskRunner 同步消息附件到沙箱失败: {str(e)}")

    async def _sync_file_to_sandbox(self, file_id: str) -> File:
        """将指定文件同步到沙箱中"""
        try:
            file_data, file = await self._file_storage.download_file(file_id=file_id)
            if file_data is None:
                logger.warning(f"AgentTaskRunner 下载文件 [{file_id}] 失败")
                return None
            if file is None:
                logger.warning(f"AgentTaskRunner 获取文件 [{file_id}] 信息失败")
                return None
            
            filepath = f"/home/ubuntu/upload/{file.filename}"
            
            tool_result = await self._sandbox.upload_file(
                file_data=file_data,
                filepath=filepath,
                filename=file.filename
            )

            if tool_result.success:
                file.filepath = filepath
                async with self._uow:
                    await self._uow.file.save(file)
                return file
            else:
                logger.warning(f"AgentTaskRunner 同步文件 [{file_id}] 到沙箱失败: {tool_result.message}")
                return None
        except Exception as e:
            logger.exception(f"AgentTaskRunner 同步文件 [{file_id}] 到沙箱失败: {str(e)}")

    async def _run_flow(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        """运行 PlannerReActFlow 并返回事件"""
        if not message.message:
            logger.warning("AgentTaskRunner 收到空消息")
            yield ErrorEvent(error="空消息错误")
            return
        
        async for event in self._flow.invoke(message):
            if isinstance(event, ToolEvent):
                # 处理工具事件
                await self._handle_tool_event(event)
            elif isinstance(event, MessageEvent):
                # 消息事件则将 AI 消息中的附近同步到存储中
                await self._sync_message_attachments_to_storage(event)
            yield event

    async def _handle_tool_event(self, event: ToolEvent) -> None:
        """处理工具事件"""
        try:
            # 如果事件状态为已调用则进行特殊处理
            if event.status == ToolEventStatus.CALLED:
                if event.tool_name == "browser":
                    # 工具为浏览器则补全浏览器工具内容
                    event.tool_content = BrowserToolContent(
                        screenshot=await self._get_browser_screenshot(),
                    )
                elif event.tool_name == "search":
                    # 工具为搜索则添加搜索内容
                    search_results: ToolResult[SearchResults] = event.function_result
                    event.tool_content = SearchToolContent(results=search_results.data.results)
                elif event.tool_name == "shell":
                    # 工具为 shell 则生成 shell 工具内容
                    if "session_id" in event.function_args:
                        shell_result = await self._sandbox.read_shell_output(
                            event.function_args["session_id"],
                            console=True,
                        )
                        event.tool_content = ShellToolContent(
                            console=(shell_result.data or {}).get("console_records", [])
                        )
                    else:
                        event.tool_content = ShellToolContent(console="(No console)")
                elif event.tool_name == "file":
                    # 工具为 file 则将文件同步到对象存储
                    if "filepath" in event.function_args:
                        filepath = event.function_args["filepath"]
                        file_read_result = await self._sandbox.read_file(filepath)
                        file_content: str = (file_read_result.data or {}).get("content", "")
                        event.tool_content = FileToolContent(content=file_content)
                        await self._sync_file_to_storage(filepath)
                    else:
                        event.tool_content = FileToolContent(content="(No file content)")
                elif event.tool_name in ["mcp", "a2a"]:
                    # 工具为 mcp/a2a 则处理调用结果
                    logger.info(f"处理 MCP/A2A 工具事件，function_result: {event.function_result}")
                    if event.function_result:
                        # 如果结果包含 data 则提取 data
                        if hasattr(event.function_result, "data") and event.function_result.data:
                            logger.info(f"MCP/A2A 工具调用结果: {event.function_result.data}")
                            event.tool_content = MCPToolContent(result=event.function_result.data) \
                                if event.tool_name == "mcp" \
                                else A2AToolContent(a2a_result=event.function_result.data)
                        elif hasattr(event.function_result, "success") and event.function_result.success:
                            logger.info(f"MCP/A2A 工具调用成功，但无结果: {event.function_result}")
                            result_data = event.function_result.model_dump() \
                                if hasattr(event.function_result, "model_dump") \
                                else str(event.function_result)
                            event.tool_content = MCPToolContent(result=result_data) \
                                if event.tool_name == "mcp" \
                                else A2AToolContent(a2a_result=result_data)
                        else:
                            # 其他情况转为字符串进行传递
                            logger.info(f"MCP/A2A 工具记录: {event.function_result}")
                            event.tool_content = MCPToolContent(result=str(event.function_result)) \
                                if event.tool_name == "mcp" \
                                else A2AToolContent(a2a_result=str(event.function_result))
                    else:
                        logger.warning("MCP/A2A 工具无结果")
                        event.tool_content = MCPToolContent(result="(No MCP result)") \
                            if event.tool_name == "mcp" \
                            else A2AToolContent(a2a_result="(No A2A result)")
        except Exception as e:
            logger.exception(f"AgentTaskRunner 处理工具事件失败: {str(e)}")

    async def _get_browser_screenshot(self) -> str:
        """获取浏览器截图"""
        # 调用浏览器完成截图
        screenshot = await self._browser.screenshot()

        # 将浏览器截图上传到文件存储中
        file = await self._file_storage.upload_file(UploadFile(
            file=io.BytesIO(screenshot),
            filename=f"{str(uuid.uuid4())}.png",
            size=self._get_stream_size(io.BytesIO(screenshot)),
        ))

        settings = get_settings()
        return f"https://{settings.oss_bucket}.{settings.oss_endpoint}/{file.key}"

    async def _sync_message_attachments_to_storage(self, event: MessageEvent) -> None:
        """将消息中的附件同步到存储中"""
        attachments: List[File] = []
        try:
            if event.attachments:
                for attachment in event.attachments:
                    file = await self._sync_file_to_storage(attachment.filepath)
                    if file:
                        attachments.append(file)
            
            event.attachments = attachments
        except Exception as e:
            logger.exception(f"AgentTaskRunner 同步消息附件到存储失败: {str(e)}")

    async def _sync_file_to_storage(self, filepath: str) -> File:
        """将指定文件同步到存储中"""
        try:
            # 根据文件路径从会话中查找文件
            async with self._uow:
                file = await self._uow.session.get_file_by_path(filepath=filepath)
            
            # 从沙箱中下载文件
            file_data = await self._sandbox.download_file(filepath)
            
            # 如果会话中存在文件，则删除
            if file:
                async with self._uow:
                    await self._uow.session.remove_file(self._session_id, file.id)

            # 提取文件名字、文件信息并更新文件路径
            filename = filepath.split("/")[-1]
            upload_file = UploadFile(
                file=file_data,
                filename=filename,
                size=self._get_stream_size(file_data),
            )

            # 上传文件到文件存储桶
            file = await self._file_storage.upload_file(upload_file)
            file.filepath = filepath

            # 往会话中添加一个文件信息
            async with self._uow:
                await self._uow.session.add_file(self._session_id, file)
            return file
        except Exception as e:
            logger.exception(f"AgentTaskRunner 同步文件 [{filepath}] 到存储失败: {str(e)}")

    @classmethod
    def _get_stream_size(cls, f: BinaryIO) -> int:
        """根据传递的文件流，计算文件的大小"""
        # 记录当前文件指针位置
        current_pos = f.tell()

        # 将指针移动到文件末尾，seek, 0: 偏移量; 2: 相对文件末尾
        f.seek(0, 2)

        # 获取当前位置，也就是文件大小
        size = f.tell()

        # 恢复指针到原始位置
        f.seek(current_pos)

        return size
