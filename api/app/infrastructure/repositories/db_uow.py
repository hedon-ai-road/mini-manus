import asyncio
from typing import Optional, Type
from types import TracebackType
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.domain.repositories.uow import IUnitOfWork
from app.infrastructure.repositories.db_file_repository import DBFileRepository
from app.infrastructure.repositories.db_session_repository import DBSessionRepository

logger = logging.getLogger(__name__)

class DBUnitOfWork(IUnitOfWork):
    """基于 Postgres 数据库的工作单元"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """构造函数，完成工作单元的初始化"""
        self.session_factory = session_factory
        self.db_session: Optional[AsyncSession] = None

    async def commit(self) -> None:
        """提交工作单元"""
        await self.db_session.commit()

    async def rollback(self) -> None:
        """回滚工作单元"""
        await self.db_session.rollback()

    async def __aenter__(self) -> "DBUnitOfWork":
        # 为每一个上下文新建新的会话
        self.db_session = self.session_factory()

        # 初始化所有的数据库仓库
        self.file = DBFileRepository(self.db_session)
        self.session = DBSessionRepository(self.db_session)

        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], exec_tb: Optional[TracebackType]):
        """
        当SSE客户端断开连接时，sse_starlette的cancel scope会取消所有await操作，
        包括此处的commit/rollback/close。如果不妥善处理CancelledError，
        会导致连接池中的连接处于异常状态，影响后续使用该池的其他任务。
        """
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        except asyncio.CancelledError:
            logger.warning("DBUnitOfWork 工作单元退出时被取消")
        except Exception as e:
            logger.warning(f"DBUnitOfWork 工作单元退出时发生错误: {str(e)}")
        finally:
            try:
                if self.db_session is not None:
                    await self.db_session.close()
            except asyncio.CancelledError:
                logger.warning("DBUnitOfWork 工作单元退出时被取消")
            except Exception as e:
                logger.warning(f"DBUnitOfWork 工作单元退出时发生错误: {str(e)}")
            finally:
                self.db_session = None