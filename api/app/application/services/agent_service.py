import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, List, Type, Callable

from pydantic import TypeAdapter

from app.domain.external.task import Task
from app.domain.models.event import BaseEvent, DoneEvent, ErrorEvent, Event, MessageEvent, WaitEvent
from app.domain.models.session import Session, SessionStatus
from app.application.errors.exceptions import NotFoundError
from app.domain.external.sandbox import Sandbox
from app.domain.services.agent_task_runner import AgentTaskRunner
from app.domain.external.file_storage import FileStorage
from app.domain.external.json_parser import JsonParser
from app.domain.external.llm import LLM
from app.domain.external.search import SearchEngine
from app.domain.models.app_config import A2AConfig, AgentConfig, MCPConfig
from app.domain.repositories.uow import IUnitOfWork

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(
        self,
        uow_factory: Callable[[], IUnitOfWork],
        file_storage: FileStorage,
        json_parser: JsonParser,
        search_engine: SearchEngine,
        llm: LLM,
        agent_config: AgentConfig,
        mcp_config: MCPConfig,
        a2a_config: A2AConfig,
        sandbox_cls: Type[Sandbox],
        task_cls: Type[Task],
    ) -> None:
        self._uow_factory = uow_factory
        self._file_storage = file_storage
        self._json_parser = json_parser
        self._search_engine = search_engine
        self._llm = llm
        self._agent_config = agent_config
        self._mcp_config = mcp_config
        self._a2a_config = a2a_config
        self._sandbox_cls = sandbox_cls
        self._task_cls = task_cls
        logger.info(f"AgentService初始化成功")

    async def chat(
        self,
        session_id: str,
        message: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        latest_event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> AsyncGenerator[BaseEvent, None]:
        """根据传递的信息调用Agent服务发起对话请求"""
        try:
            # 检查会话是否存在
            async with self._uow_factory() as uow:
                session = await uow.session.get_by_id(session_id)
            if not session:
                logger.error(f"尝试与不存在的任务会话[{session_id}]对话")
                raise NotFoundError("任务会话不存在, 请核实后重试")

            # 获取会话对应的任务
            task = await self._get_task(session)

            # 判断是否传递了 message
            if message:
                # 如果不是运行中则表示已完成或者空闲中，则需要创建新任务
                if session.status != SessionStatus.RUNNING or task is None:
                    task = await self._create_task(session)
                    if not task:
                        logger.error(f"会话[{session_id}]创建任务失败")
                        raise RuntimeError(f"会话[{session_id}]创建任务失败")

                # 传递了消息则更新会话中的最后一条消息
                async with self._uow_factory() as uow:
                    await uow.session.update_latest_message(
                        session_id=session_id,
                        message=message,
                        timestamp=timestamp or datetime.now(),
                    )

                # 从文件数据库中查询数据并更新 attachments 实际内容，并返回人类消息事件
                async with self._uow_factory() as uow:
                    db_attachments = [
                        await uow.file.get_by_id(id) for id in (attachments or [])
                    ]

                # 创建一个人类消息事件
                message_event = MessageEvent(
                    role="user",
                    message=message,
                    attachments=[attachment for attachment in db_attachments if attachment is not None],
                )

                # 将事件添加到任务的输入流中，好让 Agent 获取到数据
                event_id = await task.input_stream.put(message_event.model_dump_json())
                message_event.id = event_id
                yield message_event
                async with self._uow_factory() as uow:
                    await uow.session.add_event(session_id, message_event)

                # 执行任务
                await task.invoke()
                logger.info(f"往会话[{session_id}]输入消息队列写入消息: {message[:50]}...")
            
            # 记录日志展示会话已启动
            logger.info(f"会话[{session_id}]已启动")
            logger.info(f"会话[{session_id}]任务实例: {task}")

            # 从任务流中读取数据（勿用 not task.done 作为循环条件：任务已结束时 Redis 里可能仍有未读事件）
            while task:
                event_id, event_str = await task.output_stream.get(start_id=latest_event_id, block_ms=0)
                if event_id is not None:
                    latest_event_id = event_id
                if event_str is None:
                    if task.done:
                        break
                    await asyncio.sleep(0.05)
                    continue

                # 使用Pydantic提供的类型适配器将event_str转换为指定类实例
                event = TypeAdapter(Event).validate_json(event_str)
                event.id = event_id
                logger.debug(f"从会话[{session_id}]中获取事件: {type(event).__name__}")

                # 将未读消息重置为0
                async with self._uow_factory() as uow:
                    await uow.session.update_unread_message_count(session_id, 0)

                # 将事件返回并判断事件类型是否为结束类型
                yield event
                if isinstance(event, (DoneEvent, ErrorEvent, WaitEvent)):
                    break
            
            logger.info(f"会话[{session_id}]本轮运行结束, 状态: {session.status}")
        except Exception as e:
            logger.error(f"任务会话[{session_id}]聊天请求失败: {str(e)}")
            event = ErrorEvent(error=str(e))
            async with self._uow_factory() as uow:
                await uow.session.add_event(session_id, event)
            yield event

    async def _get_task(self, session: Session) -> Optional[Task]:
        """根据传递的会话获取对应的任务"""
        task_id = session.task_id
        if not task_id:
            return None
        return self._task_cls.get(task_id)

    async def _create_task(self, session: Session) -> Optional[Task]:
        """根据传递的会话创建一个新任务"""
        # 获取沙箱实例
        sandbox = None
        sandbox_id = session.sandbox_id
        if sandbox_id:
            sandbox = await self._sandbox_cls.get(sandbox_id)
        
        if not sandbox:
            sandbox: Sandbox = await self._sandbox_cls.create()
            session.sandbox_id = sandbox.id
            async with self._uow_factory() as uow:
                await uow.session.save(session)
        
        # 获取沙箱中的浏览器实例
        browser = await sandbox.get_browser()
        if not browser:
            logger.error(f"获取沙箱[{sandbox.id}]中的浏览器实例失败")
            raise RuntimeError(f"获取沙箱[{sandbox.id}]中的浏览器实例失败")

        # 创建 AgentTaskRunner
        task_runner = AgentTaskRunner(
            session_id=session.id,
            uow_factory=self._uow_factory,
            llm=self._llm,
            agent_config=self._agent_config,
            mcp_config=self._mcp_config,
            a2a_config=self._a2a_config,
            file_storage=self._file_storage,
            json_parser=self._json_parser,
            search_engine=self._search_engine,
            sandbox=sandbox,
            browser=browser,
        )

        # 创建 task 并更新会话中的信息
        task = self._task_cls.create(task_runner=task_runner)
        session.task_id = task.id
        async with self._uow_factory() as uow:
            await uow.session.save(session)
        return task

    async def stop_session(self, session_id: str) -> None:
        """根据传递的会话id停止对应任务会话"""

        # 检查会话是否存在
        async with self._uow_factory() as uow:
            session = await uow.session.get_by_id(session_id)
        if not session:
            logger.error(f"会话[{session_id}]不存在")
            raise NotFoundError(f"会话[{session_id}]不存在")
        
        # 根据会话获取任务信息
        task = await self._get_task(session)
        if task:
            task.cancel()

        # 更新会话状态
        async with self._uow_factory() as uow:
            await uow.session.update_status(session_id, SessionStatus.COMPLETED)
