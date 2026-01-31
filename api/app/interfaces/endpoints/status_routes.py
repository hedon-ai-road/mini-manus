import logging

from fastapi import APIRouter

from app.interfaces.schemas import Response


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["状态模块"])

@router.get(
    path="",
    response_model=Response,
    summary="系统监控检查",
    description="检查系统的 postgres/redis/fastapi 等组件的状态信息。"
)
async def get_status() -> Response:
    return Response.success()