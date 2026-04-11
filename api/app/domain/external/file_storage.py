from typing import BinaryIO, Protocol, Tuple
from fastapi import UploadFile

from app.domain.models.file import File


class FileStorage(Protocol):
    """文件存储协议"""

    async def upload_file(self, upload_file: UploadFile) -> File:
        """上传文件"""
        ...

    async def download_file(self, file_id: str) -> Tuple[BinaryIO, File]:
        """下载文件"""
        ...
    
