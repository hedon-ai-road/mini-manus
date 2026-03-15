import asyncio
import glob
import logging
import os.path
import re
from typing import Optional

from fastapi import UploadFile

from app.interfaces.errors.exception import (
    NotFoundException,
    BadRequestException,
    AppException
)
from app.models.file import (
    FileReadResult,
    FileWriteResult,
    FileReplaceResult,
    FileSearchResult,
    FileFindResult,
    FileUploadResult,
    FileCheckResult,
    FileDeleteResult
)

logger = logging.getLogger(__name__)


class FileService:
    """文件沙箱服务"""

    def __init__(self) -> None:
        pass

    @classmethod
    async def read_file(
            cls,
            filepath: str,
            start_line: Optional[int] = None,
            end_line: Optional[int] = None,
            sudo: bool = False,
            max_length: Optional[int] = 10000,
    ) -> FileReadResult:
        """根据传递的文件路径+起始行号+权限+最大长度读取文件内容"""
        try:
            # 1. 检查是否有权限
            if not os.path.exists(filepath) and not sudo:
                logger.error(f"要读取的文件不存在或无权限: {filepath}")
                raise NotFoundException(f"要读取的文件不存在或无权限: {filepath}")
            
            # 2. 统一使用 utf-8
            encoding = "utf-8"

            # 3. 判断是否为 sudo
            if sudo:
                # 4.使用sudo cat命令读取文件内容
                command = f"sudo cat '{filepath}'"
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                # 5. 读取子进程的输出，并等待子进程结束
                stdout, stderr = process.communicate()

                # 6.判断子进程的状态是否正常结束
                if process.returncode != 0:
                    raise BadRequestException(f"阅读文件失败: {stderr.decode()}")
                
                # 7. 读取输出内容
                content = stdout.decode(encoding, errors="replace")
            else:
                # 8. 创建一个内部读取函数
                def async_read_file() -> str:
                    try:
                        with open(filepath, "r", encoding=encoding) as f:
                            return f.read()
                    except Exception as async_read_file_exception:
                        raise AppException(msg=f"读取文件失败: {str(async_read_file_exception)}")
                
                # 使用 asyncio 创建线程读取文件
                content = await asyncio.to_thread(async_read_file)
            
            # 10.判断是否传递了读取范围
            if start_line is not None or end_line is not None:
                # 11.将内容切割成行，并且提取指定范围行号的数据
                lines = content.splitlines()
                start = start_line if start_line is not None else 0
                end = end_line if end_line is not None else len(lines)
                content = "\n".join(lines[start:end])
            
            # 12.裁切下数据长度
            if max_length is not None and 0 < max_length < len(content):
                content = content[:max_length] + "(truncated)"

            return FileReadResult(filepath=filepath, content=content)
        except Exception as e:
            # 13.判断异常类型执行不同操作
            if isinstance(e, BadRequestException) or isinstance(e, AppException):
                raise
            raise AppException(f"文件读取失败: {str(e)}")
