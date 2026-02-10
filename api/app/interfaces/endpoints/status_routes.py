from app.interfaces.service_dependencies import get_status_service
from fastapi import Depends
from app.application.services.status_service import StatusService
import logging
from typing import List

from fastapi import APIRouter

from app.domain.models.health_status import HealthStatus
from app.interfaces.schemas import Response


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["状态模块"])

@router.get(
    path="",
    response_model=Response[List[HealthStatus]],
    summary="系统监控检查",
    description="检查系统的 postgres/redis/fastapi 等组件的状态信息。"
)
async def get_status(
    status_service: StatusService = Depends(get_status_service),
) -> Response:
    states = await status_service.check_all()
    if any(item.status == "error" for item in states):
        return Response.fail(code=503, msg="系统存在服务异常", data=states)
    return Response.success(msg="系统健康检查成功", data=states)