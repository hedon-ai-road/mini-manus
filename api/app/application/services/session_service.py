import logging
from typing import List

from app.domain.repositories.session_repository import SessionRepository
from app.domain.models.session import Session
from app.application.errors.exceptions import NotFoundError

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self, session_repository: SessionRepository) -> None:
        self._session_repository = session_repository

    async def create_session(self) -> Session:
        """创建一个空白的新任务会话"""
        logger.info(f"创建一个空白新任务会话")
        session = Session(title="新对话")
        await self._session_repository.save(session)
        logger.info(f"成功创建一个新任务会话: {session.id}")
        return session

    async def get_all_sessions(self) -> List[Session]:
        """获取项目所有任务会话列表"""
        return await self._session_repository.get_all()

    async def clear_unread_message_count(self, session_id: str) -> None:
        """清空指定会话未读消息数"""
        logger.info(f"清除会话[{session_id}]未读消息数")
        await self._session_repository.update_unread_message_count(session_id, 0)

    async def delete_session(self, session_id: str) -> None:
        """根据传递的会话id删除任务会话"""
        # 1.先检查会话是否存在
        logger.info(f"正在删除会话, 会话id: {session_id}")
        session = await self._session_repository.get_by_id(session_id)
        if not session:
            logger.error(f"会话[{session_id}]不存在, 删除失败")
            raise NotFoundError(f"会话[{session_id}]不存在, 删除失败")

        # 2.根据传递的会话id删除会话
        await self._session_repository.delete_by_id(session_id)
        logger.info(f"删除会话[{session_id}]成功")

    async def get_session(self, session_id: str) -> Session:
        """获取指定会话详情信息"""
        return await self._session_repository.get_by_id(session_id)