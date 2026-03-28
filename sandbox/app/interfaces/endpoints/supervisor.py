from typing import List
from fastapi import APIRouter, Depends

from app.interfaces.schemas.base import Response
from app.interfaces.service_dependencies import get_supervisor_service
from app.models.supervisor import ProcessInfo
from app.services.supervisor import SupervisorService

router = APIRouter(prefix="/supervisor", tags=["Supervisor模块"])

@router.get(
    path="/status",
    response_model=Response[List[ProcessInfo]]
)
async def get_status(
    supervisor_service: SupervisorService = Depends(get_supervisor_service),
) -> Response[List[ProcessInfo]]:
    """获取沙箱中所有进程服务的状态信息"""
    processes = await supervisor_service.get_all_processes()
    return Response.success(
        msg="获取沙箱进程服务成功",
        data=processes,
    )