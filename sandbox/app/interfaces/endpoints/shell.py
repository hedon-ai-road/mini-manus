import os
from fastapi import APIRouter, Depends

from app.interfaces.schemas.base import Response
from app.interfaces.schemas.shell import ExecCommandRequest
from app.models.shell import ShellExecResult
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