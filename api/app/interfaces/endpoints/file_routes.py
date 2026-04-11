import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse

from app.interfaces.schemas.base import Response
from app.domain.models.file import File as FileInfo
from app.interfaces.service_dependencies import get_file_service
from app.application.services.file_service import FileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["文件模块"])

@router.post(
    path="",
    response_model=Response[FileInfo],
    summary="文件上传接口",
    description="传递文件返回文件的 File 信息",
)
async def upload_file(
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
) -> Response[FileInfo]:
    """文件上传接口，传递文件返回文件的 File 信息"""
    file_info = await file_service.upload_file(upload_file=file)
    return Response.success(msg="文件上传成功", data=file_info)

@router.get(
    path="/{file_id}",
    response_model=Response[FileInfo],
    summary="获取文件信息",
    description="获取指定会话中对应文件的基础信息"
)
async def get_file_info(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
) -> Response[FileInfo]:
    """获取指定会话中对应文件的基础信息"""
    file_info = await file_service.get_file_info(file_id=file_id)
    return Response.success(msg="文件信息获取成功", data=file_info)

@router.get(
    path="/{file_id}/download",
    summary="下载文件",
    description="根据传递的文件 ID 下载文件并返回文件流和文件信息"
)
async def download_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
) -> StreamingResponse:
    """根据传递的文件 ID 下载文件并返回文件流和文件信息"""
    file_stream, file_info = await file_service.download_file(file_id=file_id)
    
    encoded_filename = quote(file_info.filename)

    return StreamingResponse(
        content=file_stream,
        media_type=file_info.mime_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Length": str(file_info.size),
        }
    )