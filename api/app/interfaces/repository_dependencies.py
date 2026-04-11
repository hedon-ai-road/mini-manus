from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.storage.posgres import get_db_session
from app.infrastructure.repositories.db_session_repository import DBSessionRepository
from fastapi import Depends

@lru_cache()
def get_db_session_repository(db_session: AsyncSession = Depends(get_db_session)) -> DBSessionRepository:
    """获取数据库会话仓库"""
    return DBSessionRepository(db_session)