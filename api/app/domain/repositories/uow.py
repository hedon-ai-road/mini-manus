from typing import TypeVar, Optional, Type
from types import TracebackType
from abc import ABC, abstractmethod

from app.domain.repositories.file_repository import FileRepository
from app.domain.repositories.session_repository import SessionRepository

T = TypeVar("T", bound="IUnitOfWork")

class IUnitOfWork(ABC):
    """单元工作单元"""
    file: FileRepository
    session: SessionRepository

    @abstractmethod
    async def commit(self) -> None:
        """提交工作单元"""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """回滚工作单元"""
        ...

    @abstractmethod
    async def __aenter__(self: T) -> T:
        """异步进入上下文管理器"""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], exec_tb: Optional[TracebackType]):
        """异步退出上下文管理器"""
        ...