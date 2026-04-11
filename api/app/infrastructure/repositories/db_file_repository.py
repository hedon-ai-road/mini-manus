from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.file import File
from app.domain.repositories.file_repository import FileRepository
from app.infrastructure.models.file import FileModel

class DBFileRepository(FileRepository):
    """基于 Postgres 数据库的文件仓库"""

    def __init__(self, db_session: AsyncSession) -> None:
        """构造函数，完成数据仓库的初始化"""
        self.db_session = db_session

    async def save(self, file: File) -> None:
        """新增或更新文件信息"""
        stmt = select(FileModel).where(FileModel.id == file.id)
        result = await self.db_session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            record = FileModel.from_domain(file)
            self.db_session.add(record)
        else:
            record.update_from_domain(file)

    async def get_by_id(self, file_id: str) -> Optional[File]:
        """根据传递的文件id获取文件信息"""
        stmt = select(FileModel).where(FileModel.id == file_id)
        result = await self.db_session.execute(stmt)
        record = result.scalar_one_or_none()
        return record.to_domain() if record else None