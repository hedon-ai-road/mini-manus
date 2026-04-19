from datetime import datetime
import io
import logging
import os
from typing import BinaryIO, Callable, Tuple
import uuid

from fastapi import UploadFile
from alibabacloud_oss_v2.models import (
    GetObjectResult,
    PutObjectRequest,
    DeleteObjectRequest,
    GetObjectRequest,
    PutObjectResult
)

from app.domain.external.file_storage import FileStorage
from app.domain.models.file import File
from app.domain.repositories.uow import IUnitOfWork
from app.infrastructure.storage.oss import OSS

logger = logging.getLogger(__name__)



class OSSFileStorage(FileStorage):
    """阿里云 OSS 文件存储"""

    def __init__(self, bucket: str, oss: OSS, uow_factory: Callable[[], IUnitOfWork]) -> None:
        self.bucket = bucket
        self.oss = oss
        self._uow_factory = uow_factory

    async def upload_file(self, upload_file: UploadFile) -> File:
        """上传文件"""
        try:
            # 构造文件 ID 和 OSS 键
            file_id = str(uuid.uuid4())
            _, file_extension = os.path.splitext(upload_file.filename)
            if not file_extension:
                file_extension = ""

            date_path = datetime.now().strftime("%Y/%m/%d")
            oss_key = f"{date_path}/{file_id}{file_extension}"

            # 使用 fastapi 的线程池来上传文件
            put_object_result: PutObjectResult = await self.oss.client.put_object(
                request=PutObjectRequest(
                    bucket=self.bucket,
                    key=oss_key,
                    content_type=upload_file.content_type,
                    content_length=upload_file.size,
                    body=upload_file.file,
                ),
            )
            if put_object_result.status_code != 200:
                raise Exception(f"文件上传失败：{put_object_result.status_code} {put_object_result.status}")
            logger.info(f"文件上传成功：{upload_file.filename} -> {oss_key}")

            # 存储 file 数据，如果存储失败，则删除 OSS 中的文件
            file = File(
                id=file_id,
                filename=upload_file.filename,
                key=oss_key,
                extension=file_extension,
                mime_type=upload_file.content_type,
                size=upload_file.size,
            )
            try:
                async with self._uow_factory() as uow:
                    await uow.file.save(file)
            except Exception as e:
                logger.error(f"存储 file [{file.id}] 数据失败，删除 OSS 中的文件[{oss_key}]：{str(e)}")
                await self.oss.client.delete_object(
                    request=DeleteObjectRequest(
                        bucket=self.bucket,
                        key=oss_key,
                    ),
                )
                raise

            return file
        except Exception as e:
            logger.error(f"上传文件[{upload_file.filename}]失败: {str(e)}")
            raise
    
    async def download_file(self, file_id: str) -> Tuple[BinaryIO, File]:
        """下载文件"""
        try:
            # 获取文件信息
            async with self._uow_factory() as uow:
                file = await uow.file.get_by_id(file_id)
            if not file:
                raise FileNotFoundError(f"文件[{file_id}]不存在")

            # 下载文件
            response: GetObjectResult = await self.oss.client.get_object(
                request=GetObjectRequest(bucket=self.bucket, key=file.key),
            )
            if response.status_code != 200:
                raise Exception(f"文件下载失败：{response.status_code} {response.status}")
            if response.body is None:
                raise RuntimeError(f"文件[{file_id}]下载响应无正文")
            data = await response.body.read()
            return io.BytesIO(data), file
        except Exception as e:
            logger.error(f"下载文件[{file_id}]失败: {str(e)}")
            raise