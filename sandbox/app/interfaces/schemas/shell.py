from typing import Optional
from pydantic import BaseModel, Field

class ShellExecutionRequest(BaseModel):
    """执行命令请求结构体"""
    session_id: Optional[str] = Field(default=None, description="shell 会话唯一标识符")
    exec_dir: Optional[str] = Field(default=None, description="执行命令的工作目录，必须使用绝对路径")
    command: str = Field(..., description="要执行的 shell 命令")

class ShellReadRequest(BaseModel):
    """查看 shell 执行内容请求结构体"""
    session_id: str = Field(...,  description="shell 会话唯一标识符")
    console: Optional[bool] = Field(default=None, description="是否返回控制台记录列表")

class ShellWaitRequest(BaseModel):
    """等待 shell 命令执行请求结构体"""
    session_id: str = Field(...,  description="shell 会话唯一标识符")
    seconds: Optional[int] = Field(default=None, description="等待超时时间(s)")

class ShellWriteRequest(BaseModel):
    """写入数据到子进程请求结构体"""
    session_id: str = Field(...,  description="shell 会话唯一标识符")
    input_text: str = Field(..., description="需要写入的内容文本")
    press_enter: bool = Field(default=True, description="是否按下回车键，默认为True")

class ShellKillRequest(BaseModel):
    """关闭子进程请求结构体"""
    session_id: str = Field(...,  description="shell 会话唯一标识符")