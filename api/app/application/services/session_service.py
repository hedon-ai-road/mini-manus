import logging
from typing import Callable, List, Type

from app.domain.models.file import File
from app.domain.models.session import Session
from app.application.errors.exceptions import NotFoundError, ServerError
from app.domain.repositories.uow import IUnitOfWork
from app.interfaces.schemas.session import FileReadResponse, ShellReadResponse
from app.domain.external.sandbox import Sandbox

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self, 
        uow_factory: Callable[[], IUnitOfWork],
        sandbox_cls: Type[Sandbox],
    ) -> None:
        self._uow_factory = uow_factory
        self._sandbox_cls = sandbox_cls

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

    async def get_session_files(self, session_id: str) -> List[File]:
        """获取指定会话文件列表信息"""
        logger.info(f"获取指定会话[{session_id}]下的文件列表信息")
        async with self._uow_factory() as uow:
            session = await uow.session.get_by_id(session_id)
        if not session:
            logger.error(f"会话[{session_id}]不存在, 获取文件列表失败")
            raise NotFoundError(f"会话[{session_id}]不存在, 获取文件列表失败")
        return session.files

    async def read_file(self, session_id: str, filepath: str) -> FileReadResponse:
        """根据传递的会话id+文件路径查看沙箱中文件的内容信息"""
        logger.info(f"根据传递的会话id[{session_id}]+文件路径[{filepath}]查看沙箱中文件的内容信息")
        
        # 检查会话是否存在
        async with self._uow_factory() as uow:
            session = await uow.session.get_by_id(session_id)
        if not session:
            logger.error(f"会话[{session_id}]不存在, 读取文件内容失败")
            raise NotFoundError(f"会话[{session_id}]不存在, 读取文件内容失败")

        # 判断沙箱是否存在
        if not session.sandbox_id:
            logger.error(f"会话[{session_id}]不存在沙箱, 读取文件内容失败")
            raise NotFoundError(f"会话[{session_id}]不存在沙箱, 读取文件内容失败")
        sandbox = await self._sandbox_cls.get(session.sandbox_id)
        if not sandbox:
            logger.error(f"沙箱[{session.sandbox_id}]不存在, 读取文件内容失败")
            raise NotFoundError(f"沙箱[{session.sandbox_id}]不存在, 读取文件内容失败")

        # 读取文件内容
        result = await sandbox.read_file(filepath)
        if result.success:
            return FileReadResponse(**result.data)
        raise ServerError(msg=f"读取文件[{filepath}]内容失败: {result.message}")

    async def read_shell_output(self, session_id: str, shell_session_id: str) -> ShellReadResponse:
        """根据传递的会话id查看shell内容输出"""
        logger.info(f"根据传递的会话id[{session_id}]+shell会话id[{shell_session_id}]查看shell内容输出")

        # 检查会话是否存在
        async with self._uow_factory() as uow:
            session = await uow.session.get_by_id(session_id)
        if not session:
            logger.error(f"会话[{session_id}]不存在, 读取shell内容输出失败")
            raise NotFoundError(f"会话[{session_id}]不存在, 读取shell内容输出失败")

        # 判断沙箱是否存在
        if not session.sandbox_id:
            logger.error(f"会话[{session_id}]不存在沙箱, 读取shell内容输出失败")
            raise NotFoundError(f"会话[{session_id}]不存在沙箱, 读取shell内容输出失败")
        sandbox = await self._sandbox_cls.get(session.sandbox_id)
        if not sandbox:
            logger.error(f"沙箱[{session.sandbox_id}]不存在, 读取shell内容输出失败")
            raise NotFoundError(f"沙箱[{session.sandbox_id}]不存在, 读取shell内容输出失败")

        # 读取shell内容输出
        result = await sandbox.read_shell_output(session_id=shell_session_id, console=True)
        if result.success:
            return ShellReadResponse(**result.data)
        raise ServerError(msg=f"读取shell内容输出失败: {result.message}")

    async def get_vnc_url(self, session_id: str) -> str:
        """获取指定会话的vnc连接url"""
        logger.info(f"获取指定会话[{session_id}]的vnc连接url")

        # 检查会话是否存在
        async with self._uow_factory() as uow:
            session = await uow.session.get_by_id(session_id)
        if not session:
            logger.error(f"会话[{session_id}]不存在, 获取vnc连接url失败")
            raise NotFoundError(f"会话[{session_id}]不存在, 获取vnc连接url失败")

        # 判断沙箱是否存在
        if not session.sandbox_id:
            logger.error(f"会话[{session_id}]不存在沙箱, 获取vnc连接url失败")
            raise NotFoundError(f"会话[{session_id}]不存在沙箱, 获取vnc连接url失败")
        sandbox = await self._sandbox_cls.get(session.sandbox_id)
        if not sandbox:
            logger.error(f"沙箱[{session.sandbox_id}]不存在, 获取vnc连接url失败")
            raise NotFoundError(f"沙箱[{session.sandbox_id}]不存在, 获取vnc连接url失败")

        # 获取vnc连接url
        return sandbox.vnc_url
