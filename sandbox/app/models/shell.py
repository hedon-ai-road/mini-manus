from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
import asyncio

class ConsoleRecord(BaseModel):
    """shell 命令行控制台记录"""
    ps1: str = Field(..., description="ps1")
    command: str = Field(..., description="执行命令")
    output: str = Field(default="", description="命令输出")

class Shell(BaseModel):
    """shell 会话模型"""
    process: asyncio.subprocess.Process = Field(..., description="会话中的子进程")
    exec_dir: str = Field(..., description="会话执行目录")
    output: str = Field(..., description="会话输出")
    console_records: List[ConsoleRecord] = Field(default_factory=list, description="shell 会话中的控制台记录列表")

    model_config = ConfigDict(
        arbitrary_types_allowed=True, # 允许 python 原生对象或者自定义的对象作为字段类型
    )

class ShellWaitResult(BaseModel):
    """会话等待结果模型"""
    returncode: int = Field(..., description="子进程返回代码")

class ShellReadResult(BaseModel):
    """shell 命令结果模型"""
    session_id: str = Field(..., description="shell 会话 id")
    output: str = Field(..., description="shell 会话输出内容")
    console_records: List[ConsoleRecord] = Field(default_factory=list, description="控制台记录")

class ShellExecuteResult(BaseModel):
    """shell 命令执行结果"""
    session_id: str = Field(..., description="shell 会话 ID")
    command: str = Field(..., description="执行命令")
    status: str = Field(..., description="命令执行状态")
    returncode: Optional[int] = Field(default=None, description="进程返回代码，只有进程结束时才有值")
    output: Optional[str] = Field(default=None, description="进程执行结果，只有进程结束时才有值")

class ShellWriteResult(BaseModel):
    """shell 写入结果"""
    status: str = Field(..., description="写入状态")

class ShellKillResult(BaseModel):
    """shell 命令关闭结果"""
    status: str = Field(..., description="进程的状态")
    returncode: int = Field(..., description="进程返回代码")