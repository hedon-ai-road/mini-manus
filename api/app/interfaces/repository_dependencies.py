from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.storage.posgres import get_db_session
from app.infrastructure.repositories.db_session_repository import DBSessionRepository
from app.infrastructure.repositories.db_file_repository import DBFileRepository
from app.domain.repositories.file_repository import FileRepository
from fastapi import Depends

@lru_cache()
def get_db_session_repository(db_session: AsyncSession = Depends(get_db_session)) -> DBSessionRepository:
    """获取数据库会话仓库"""
    return DBSessionRepository(db_session)

@lru_cache()
def get_file_repository(db_session: AsyncSession = Depends(get_db_session)) -> FileRepository:
    """获取文件仓库"""
    return DBFileRepository(db_session)