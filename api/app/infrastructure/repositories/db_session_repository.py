from datetime import datetime
from typing import List, Optional

from sqlalchemy import delete, func, select, update, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from app.domain.models.event import BaseEvent
from app.domain.models.file import File
from app.domain.models.memory import Memory
from app.domain.models.session import Session, SessionStatus
from app.domain.repositories.session_repository import SessionRepository
from app.infrastructure.models.session import SessionModel

class DBSessionRepository(SessionRepository):
    """基于 Postgres 数据库的会话仓库"""

    def __init__(self, session: AsyncSession):
        """构造函数，完成数据仓库的初始化"""
        self.db_session = session

    async def save(self, session: Session) -> None:
        """存储或更新传递进来的会话"""
        stmt = select(SessionModel).where(SessionModel.id == session.id)
        result = await self.db_session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            record = SessionModel.from_domain(session)
            self.db_session.add(record)
        else:
            record.update_from_domain(session)

    async def get_all(self) -> List[Session]:
        """获取所有会话列表信息"""
        stmt = select(SessionModel).order_by(SessionModel.latest_message_at.desc())
        result = await self.db_session.execute(stmt)
        records = result.scalars().all()
        return [record.to_domain() for record in records]

    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """根据传递的会话id查询会话"""
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await self.db_session.execute(stmt)
        record = result.scalar_one_or_none()
        return record.to_domain() if record else None

    async def delete_by_id(self, session_id: str) -> None:
        """根据传递的会话id删除会话"""
        stmt = delete(SessionModel).where(SessionModel.id == session_id)
        await self.db_session.execute(stmt)

    async def update_title(self, session_id: str, title: str) -> None:
        """根据传递的会话id+标题更新会话信息"""
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(title=title)
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

    async def update_latest_message(self, session_id: str, message: str, timestamp: datetime) -> None:
        """根据传递的信息更新最新消息"""
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                latest_message=message,
                latest_message_at=timestamp,
            )
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

    async def update_unread_message_count(self, session_id: str, count: int) -> None:
        """根据传递的信息更新未读消息数"""
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(unread_message_count=count)
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

    async def increment_unread_message_count(self, session_id: str) -> None:
        """根据传递的会话id新增未读消息数"""
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                unread_message_count=func.coalesce(SessionModel.unread_message_count, 0) + 1,
            )
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

    async def decrement_unread_message_count(self, session_id: str) -> None:
        """根据传递的会话id减少未读消息数"""
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                unread_message_count=func.greatest(
                    func.coalesce(SessionModel.unread_message_count, 0) - 1,
                    0
                )
            )
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

    async def update_status(self, session_id: str, status: SessionStatus) -> None:
        """根据传递的会话id更新会话状态"""
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(status=status)
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

    async def add_event(self, session_id: str, event: BaseEvent) -> None:
        """往会话中新增事件"""
        event_data = event.model_dump(mode="json")
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                events=func.coalesce(SessionModel.events, cast([], JSONB)) + cast([event_data], JSONB),
            )
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

    async def add_file(self, session_id: str, file: File) -> None:
        """往会话中新增文件"""
        file_data = file.model_dump(mode="json")
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                files=func.coalesce(SessionModel.files, cast([], JSONB)) + cast([file_data], JSONB),
            )
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

    async def remove_file(self, session_id: str, file_id: str) -> None:
        """根据传递的会话id+文件id移除文件"""
        stmt = select(SessionModel).where(SessionModel.id == session_id).with_for_update()
        result = await self.db_session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

        original_length = len(record.files)
        new_files = [file for file in record.files if file["id"] != file_id]
        if len(new_files) == original_length:
            return

        record.files = new_files

    async def get_file_by_path(self, session_id: str, filepath: str) -> Optional[File]:
        """查询会话中的文件信息"""
        stmt = select(SessionModel.files).where(SessionModel.id == session_id)
        result = await self.db_session.execute(stmt)
        files = result.scalar_one_or_none()
        if not files:
            return None
        for file in files:
            if file.get("filepath", "") == filepath:
                return File(**file)
        return None

    async def save_memory(self, session_id: str, agent_name: str, memory: Memory) -> None:
        """更新or创建会话中指定Agent的记忆"""
        memory_data = memory.model_dump(mode="json")
        patch_data = {agent_name: memory_data}

        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                memories=func.coalesce(SessionModel.memories, cast({}, JSONB)) + cast(patch_data, JSONB),
            )
        )
        result = await self.db_session.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"会话 {session_id} 不存在，请核实后重试！")

    async def get_memory(self, session_id: str, agent_name: str) -> Memory:
        """根据传递的会话id+Agent名字获取记忆"""
        stmt = select(SessionModel.memories[agent_name]).where(SessionModel.id == session_id)
        result = await self.db_session.execute(stmt)
        memory_data = result.scalar_one_or_none()
        if not memory_data:
            return Memory(messages=[])
        return Memory(**memory_data)
