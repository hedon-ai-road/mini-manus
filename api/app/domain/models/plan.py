from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

class ExecutionStatus(str, Enum):
    """规划/任务的执行的状态"""
    PENDING = "pending" # 空闲 or 等待中
    RUNNING = "running" # 执行中
    COMPLETED = "completed" # 执行完成
    FAILED = "failed" # 执行失败

class Step(BaseModel):
    """计划中的每一个步骤"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())) # 步骤 ID
    description: str = "" # 步骤描述信息
    status: ExecutionStatus = ExecutionStatus.PENDING # 步骤状态
    result: Optional[str] = None # 结果
    error: Optional[str] = None # 错误信息
    success: bool = False # 是否执行成功
    attachments: List[str] = Field(default_factory=list) # 附件列表信息

    @property
    def done(self) -> bool:
        """步骤是否结束"""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]


class Plan(BaseModel):
    """规划领域模型，用于存储用户传递消息拆分出来的子任务/子步骤"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())) # 计划 ID
    title: str = "" # 任务标题
    goal: str = ""  # 任务目标
    language: str = "" # 工作语言
    steps: List[Step] = Field(default_factory=list) # 步骤/子任务列表
    message: str = "" # 用户传递的消息
    status: ExecutionStatus = ExecutionStatus.PENDING # 规划状态
    error: Optional[str] = None # 错误信息
    # todo: 未预留 result 用于记录规划的结果信息
    
    @property
    def done(self) -> bool:
        """计划是否结束"""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    def get_next_step(self) -> Optional[Step]:
        """获取下一个执行步骤"""
        return next((step for step in self.steps if not step.done), None)