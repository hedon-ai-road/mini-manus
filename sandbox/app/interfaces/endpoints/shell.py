import os
from fastapi import APIRouter, Depends

from app.interfaces.errors.exception import BadRequestException
from app.interfaces.schemas.base import Response
from app.interfaces.schemas.shell import ExecCommandRequest, KillProcessRequest, ViewShellRequest, WaitForProcessRequest, WriteToProcessRequest
from app.models.shell import ShellExecResult, ShellKillResult, ShellViewResult, ShellWaitResult, ShellWriteResult
from app.interfaces.service_dependecies import get_shell_service
from app.services.shell import ShellService

router = APIRouter(prefix="/shell", tags=["Shell模块"])

@router.post(
    path="/exec-command",
    response_model=Response[ShellExecResult],
)
async def exec_command(
    req: ExecCommandRequest,
    shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellExecResult]:
    if not req.session_id or req.session_id == "":
        req.session_id = shell_service.create_session_id()
    
    if not req.exec_dir or req.exec_dir == "":
        req.exec_dir = os.path.expanduser("~")
    
    result = await shell_service.exec_command(
        session_id=req.session_id,
        exec_dir=req.exec_dir,
        command=req.command,
    )

    return Response.success(data=result)


@router.post(
    path="/view-shell",
    response_model=Response[ShellViewResult],
)
async def view_shell(
    req: ViewShellRequest,
    shell_service: ShellService = Depends(get_shell_service)
) -> Response[ShellViewResult]:
    if not req.session_id or req.session_id == "":
        raise BadRequestException("session_id 为空")
    
    result = await shell_service.view_shell(req.session_id, req.console if req.console else False)
    return Response.success(data=result)

@router.post(
    path="/wait-for-process",
    response_model=Response[ShellWaitResult],
)
async def wait_for_process(
    req: WaitForProcessRequest,
    shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellWaitResult]:
    if not req.session_id or req.session_id == "":
        raise BadRequestException("session_id 为空")

    result = await shell_service.wait_for_process(req.session_id, req.seconds)
    return Response.success(
        msg=f"进程结束，返回状态码(returncode): {result.returncode}",
        data=result,
    )

@router.post(
    path="/write-to-process",
    response_model=Response[ShellWriteResult],
)
async def write_to_process(
    req: WriteToProcessRequest,
    shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellWriteResult]:
    if not req.session_id or req.session_id == "":
        raise BadRequestException("session_id 为空")

    result = await shell_service.write_to_process(req.session_id, req.input_text, req.press_enter)
    return Response.success(
        msg="向进程写入数据成功",
        data=result,
    )

@router.post(
    path="/kill-process",
    response_model=Response[ShellKillResult]
)
async def kill_process(
    req: KillProcessRequest,
    shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellKillResult]:
    if not req.session_id or req.session_id == "":
        raise BadRequestException("session_id 为空")

    result = await shell_service.kill_process(req.session_id)
    return Response.success(
        msg="进程终止" if result.status == "terminated" else "进程已结束",
        data=result,
    )