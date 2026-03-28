from typing import List
from fastapi import APIRouter, Depends

from app.interfaces.schemas.base import Response
from app.interfaces.service_dependencies import get_supervisor_service
from app.models.supervisor import ProcessInfo, SupervisorActionResult
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

@router.post(
    path="/stop-all-processes",
    response_model=Response[SupervisorActionResult]
)
async def stop_all_processes(
    supervisor_service: SupervisorService = Depends(get_supervisor_service),
) -> Response[SupervisorActionResult]:
    """停止所有进程"""
    result = await supervisor_service.stop_all_processes()
    return Response.success(
        msg="停止所有进程成功",
        data=result,
    )

@router.post(
    path="/shutdown",
    response_model=Response[SupervisorActionResult]
)
async def shutdown(
    supervisor_service: SupervisorService = Depends(get_supervisor_service),
) -> Response[SupervisorActionResult]:
    """关闭 supervisor 服务本身"""
    result = await supervisor_service.shutdown()
    return Response.success(
        msg="supervisor 关闭成功",
        data=result
    )

@router.post(
    path="/restart",
    response_model=Response[SupervisorActionResult]
)
async def restart(
    supervisor_service: SupervisorService = Depends(get_supervisor_service),
) -> Response[SupervisorActionResult]:
    """重启 supervisor 服务"""
    result = await supervisor_service.restart()
    return Response.success(
        msg="重启 supervisor 成功",
        data=result,
    )
