from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
import uuid

from app.domain.models.file import File
from app.domain.models.plan import Plan, Step
from app.domain.models.tool_result import ToolResult

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

class ToolEventStatus(str, Enum):
    """工具事件状态"""
    CALLING = "calling" # 调用中
    CALLED = "called" # 调用完毕

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
    attachments: List[File] = Field(default_factory=list) # 附件列表

class BrowserToolContent(BaseModel):
    """浏览器工具扩展内容"""
    screenshot: str # 浏览器快照截图

class MCPToolContent(BaseModel):
    """MCP 工具内容"""
    result: Any # MCP 工具执行结果

# todo: 工具扩展内容待完善
ToolContent = Union[BrowserToolContent, MCPToolContent]


class ToolEvent(BaseEvent):
    """工具事件"""
    type: Literal["tool"] = "tool"
    tool_call_id: str # 工具调用 ID
    tool_name: str # 工具集的名字
    tool_content: Optional[ToolContent] = None # 特殊工具的额外信息
    function_name: str # LLM 调用的工具名字
    function_args: Dict[str, Any] # LLM 生成的工具调用参数
    function_result: Optional[ToolResult] = None # 工具调用结果
    status: ToolEventStatus = ToolEventStatus.CALLING # 工具事件状态

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