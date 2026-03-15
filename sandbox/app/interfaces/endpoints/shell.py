import os
from fastapi import APIRouter, Depends

from app.interfaces.errors.exception import BadRequestException
from app.interfaces.schemas.base import Response
from app.interfaces.schemas.shell import ShellExecutionRequest, ShellKillRequest, ShellReadRequest, ShellWaitRequest, ShellWriteRequest
from app.models.shell import ShellExecuteResult, ShellKillResult, ShellReadResult, ShellWaitResult, ShellWriteResult
from app.interfaces.service_dependencies import get_shell_service
from app.services.shell import ShellService

router = APIRouter(prefix="/shell", tags=["Shell模块"])

@router.post(
    path="/exec-command",
    response_model=Response[ShellExecuteResult],
)
async def exec_command(
    req: ShellExecutionRequest,
    shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellExecuteResult]:
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
    path="/read-shell-output",
    response_model=Response[ShellReadResult],
)
async def read_shell_output(
    req: ShellReadRequest,
    shell_service: ShellService = Depends(get_shell_service)
) -> Response[ShellReadResult]:
    if not req.session_id or req.session_id == "":
        raise BadRequestException("session_id 为空")
    
    result = await shell_service.read_shell_output(req.session_id, req.console if req.console else False)
    return Response.success(data=result)

@router.post(
    path="/wait-process",
    response_model=Response[ShellWaitResult],
)
async def wait_process(
    req: ShellWaitRequest,
    shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellWaitResult]:
    if not req.session_id or req.session_id == "":
        raise BadRequestException("session_id 为空")

    result = await shell_service.wait_process(req.session_id, req.seconds)
    return Response.success(
        msg=f"进程结束，返回状态码(returncode): {result.returncode}",
        data=result,
    )

@router.post(
    path="/write-shell-input",
    response_model=Response[ShellWriteResult],
)
async def write_shell_input(
    req: ShellWriteRequest,
    shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellWriteResult]:
    if not req.session_id or req.session_id == "":
        raise BadRequestException("session_id 为空")

    result = await shell_service.write_shell_input(req.session_id, req.input_text, req.press_enter)
    return Response.success(
        msg="向进程写入数据成功",
        data=result,
    )

@router.post(
    path="/kill-process",
    response_model=Response[ShellKillResult]
)
async def kill_process(
    req: ShellKillRequest,
    shell_service: ShellService = Depends(get_shell_service),
) -> Response[ShellKillResult]:
    if not req.session_id or req.session_id == "":
        raise BadRequestException("session_id 为空")

    result = await shell_service.kill_process(req.session_id)
    return Response.success(
        msg="进程终止" if result.status == "terminated" else "进程已结束",
        data=result,
    )