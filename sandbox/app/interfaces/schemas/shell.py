from typing import Optional
from pydantic import BaseModel, Field

class ExecCommandRequest(BaseModel):
    """执行命令请求结构体"""
    session_id: Optional[str] = Field(default=None, description="shell 会话唯一标识符")
    exec_dir: Optional[str] = Field(default=None, description="执行命令的工作目录，必须使用绝对路径")
    command: str = Field(..., description="要执行的 shell 命令")
