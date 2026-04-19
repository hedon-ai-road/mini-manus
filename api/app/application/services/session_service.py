import logging
from typing import Callable, List

from app.domain.models.session import Session
from app.application.errors.exceptions import NotFoundError
from app.domain.repositories.uow import IUnitOfWork

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self, uow_factory: Callable[[], IUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def create_session(self) -> Session:
        """创建一个空白的新任务会话"""
        logger.info(f"创建一个空白新任务会话")
        session = Session(title="新对话")
        async with self._uow_factory() as uow:
            await uow.session.save(session)
        logger.info(f"成功创建一个新任务会话: {session.id}")
        return session

    async def get_all_sessions(self) -> List[Session]:
        """获取项目所有任务会话列表"""
        async with self._uow_factory() as uow:
            return await uow.session.get_all()

    async def clear_unread_message_count(self, session_id: str) -> None:
        """清空指定会话未读消息数"""
        logger.info(f"清除会话[{session_id}]未读消息数")
        async with self._uow_factory() as uow:
            await uow.session.update_unread_message_count(session_id, 0)

    async def delete_session(self, session_id: str) -> None:
        """根据传递的会话id删除任务会话"""
        logger.info(f"正在删除会话, 会话id: {session_id}")
        async with self._uow_factory() as uow:
            # 1.先检查会话是否存在
            session = await uow.session.get_by_id(session_id)
            if not session:
                logger.error(f"会话[{session_id}]不存在, 删除失败")
                raise NotFoundError(f"会话[{session_id}]不存在, 删除失败")

            # 2.根据传递的会话id删除会话
            await uow.session.delete_by_id(session_id)
        logger.info(f"删除会话[{session_id}]成功")

    async def get_session(self, session_id: str) -> Session:
        """获取指定会话详情信息"""
        async with self._uow_factory() as uow:
            return await uow.session.get_by_id(session_id)