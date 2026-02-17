from datetime import datetime
from enum import Enum
from typing import Any, List, Literal, Union
from pydantic import BaseModel, Field
import uuid

from app.domain.models.plan import Plan, Step

class PlanEventStatus(str, Enum):
    """规划事件状态"""
    CREATED = "created" # 已创建
    UPDATED = "updated" # 已更新
    COMPLETED = "completed" # 已完成

class StepEventStatus(str, Enum):
    """步骤事件状态"""
    STARTED = "started" # 已开始
    COMPLETED = "completed" # 已完成
    FAILED = "failed" # 失败

class BaseEvent(BaseModel):
    """基础事件类型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())) # 事件 ID
    type: Literal[""] = "" # 事件类型
    created_at: datetime = Field(default_factory=datetime.now) # 事件创建时间

class PlanEvent(BaseEvent):
    """规划事件"""
    type: Literal["plan"] = "plan"
    plan: Plan # 规划
    status: PlanEventStatus = PlanEventStatus.CREATED # 规划事件状态

class TitleEvent(BaseEvent):
    """标题事件"""
    type: Literal["title"] = "title"
    title: str = "" # 标题

class StepEvent(BaseEvent):
    """步骤事件"""
    type: Literal["step"] = "step"
    step: Step # 步骤信息
    status: StepEventStatus = StepEventStatus.STARTED # 步骤状态

class MessageEvent(BaseEvent):
    """消息事件：人类/ai 消息"""
    type: Literal["message"] = "message"
    role: Literal["user", "assistent"] = "assistent" # 消息角色
    message: str = "" # 消息本身
    # todo: 附件文件结构待完善
    attachments: List[Any] = Field(default_factory=list) # 附件列表

class ToolEvent(BaseEvent):
    """工具事件"""
    # todo: 工具事件等待工具模块接入完善
    type: Literal["tool"] = "tool"

class WaitEvent(BaseEvent):
    """等待事件：等待用户输入确认"""
    type: Literal["wait"] = "wait"

class ErrorEvent(BaseEvent):
    """错误事件"""
    type: Literal["error"] = "error"
    error: str = "" # 错误信息


class DoneEvent(BaseEvent):
    """结束事件"""
    type: Literal["done"] = "done"

# 定义应用事件类型声明
Event = Union[
    PlanEvent,
    TitleEvent,
    StepEvent,
    MessageEvent,
    ToolEvent,
    WaitEvent,
    ErrorEvent,
    DoneEvent,
]