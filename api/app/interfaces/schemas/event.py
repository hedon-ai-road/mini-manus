from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Type, Union, get_args

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.event import Event, ToolEventStatus
from app.domain.models.tool_result import ToolResult as DomainToolResult
from app.domain.models.file import File
from app.domain.models.plan import ExecutionStatus

# 事件类型处理的核心底层思路与设计原因说明：
#
# 1. 为什么要这样设计：
#    为了支持系统中多样化、异步化的事件处理和前后端的数据流同步，事件类型需要标准、灵活地进行定义与序列化。
#    本模块采用 Pydantic 的 BaseModel（或 dataclass）作为事件数据结构的基础，确保所有事件均有统一的核心字段（如 event_id, created_at），
#    同时可以通过继承扩展各自业务需要的数据。这样既保证了 SSE（Server-Sent Events）、WebSocket 等推送方式下数据结构统一、
#    扩展方便，也使得前端消费这些事件数据时可以依赖类型约束、易于解析。
#
# 2. 上下游关系说明：
#    - 上游（事件生产者/领域层）：系统各处理模块（如 Tool、File、Plan 模块）在业务流程中创建 Event 领域对象，
#      上报/保存到数据库或内存的事件流中。
#    - 本模块（事件 schema 转换层）：通过提供 from_event 等类方法，将领域层的 Event 实体转化为接口层的数据结构（BaseEventData 及扩展类），
#      便于前端消费。
#    - 下游（事件推送/接口层）：FastAPI 路由、SSE 推送 handler、WebSocket 或 HTTP 接口通过本模块导出的事件 schema，
#      序列化为标准 JSON 或 SSE 数据格式，发送给前端页面、终端或其他订阅者，实现事件驱动的 UI 实时更新、日志流、进度跟踪等功能。
#
#    通过分层、规范的事件对象和 schema 结构，实现松耦合、易扩展的事件流，形成领域层到接口再到前端 UI 的高内聚、低耦合流程。


class BaseEventData(BaseModel):
    """基础事件数据"""
    event_id: Optional[str] = None # 事件ID
    created_at: Optional[datetime] = Field(default_factory=datetime.now) # 事件创建时间

    model_config = ConfigDict(json_encoders={
        datetime: lambda v: int(v.timestamp())
    })

    @classmethod
    def base_event_data(cls, event: Event) -> Dict[str, Any]:
        """类方法，用于将事件Domain模型转换成基础事件数据字典，方便后续SSE事件推送"""
        return {
            "event_id": event.id,
            "created_at": int(event.created_at.timestamp()),
        }

    @classmethod
    def from_event(cls, event: Event) -> "BaseEventData":
        """类方法，用于将事件Domain模型转换成基础事件数据模型"""
        return cls(
            **cls.base_event_data(event),
            **event.model_dump(mode="json", exclude={"id", "type", "created_at"}),
        )

class BaseSSEEvent(BaseModel):
    """基础SSE事件"""
    event: str  # 事件类型
    data: BaseEventData  # 基础事件数据

    @classmethod
    def from_event(cls, event: Event) -> "BaseSSEEvent":
        """类方法，用于将事件Domain模型转换成基础SSE事件模型"""

        # 获取事件数据的类型，如果没有则使用基础事件数据BaseEventData
        data_class: Type[BaseEventData] = cls.__annotations__.get("data", BaseEventData)

        # 调用构造函数完成初始化
        return cls(
            event=event.type,
            data=data_class.from_event(event),
        )

class CommonEventData(BaseEventData):
    """通用事件数据，让结构允许填充额外的数据"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: int(v.timestamp())
        },
        extra="allow"
    )

class CommonSSEEvent(BaseSSEEvent):
    """通用SSE事件"""
    event: str
    data: CommonEventData

class MessageEventData(BaseEventData):
    """消息事件数据"""
    role: Literal["user", "assistant"] = "assistant"
    message: str
    attachments: List[File] = Field(default_factory=list)

class MessageSSEEvent(BaseSSEEvent):
    """消息SSE事件"""
    event: Literal["message"] = "message"
    data: MessageEventData

    @classmethod
    def from_event(cls, event: Event) -> "MessageSSEEvent":
        """类方法，用于将消息事件Domain模型转换成消息SSE事件模型"""
        return cls(
            data =MessageEventData(
                **BaseEventData.base_event_data(event),
                role=event.role,
                message=event.message,
                attachments=event.attachments,
            )
        )

class TitleEventData(BaseEventData):
    """标题事件数据"""
    title: str

class TitleSSEEvent(BaseSSEEvent):
    """标题SSE事件"""
    event: Literal["title"] = "title"
    data: TitleEventData

class StepEventData(BaseEventData):
    """步骤事件数据"""
    id: str # 步骤id
    status: ExecutionStatus # 步骤执行状态
    description: str # 步骤描述

class StepSSEEvent(BaseSSEEvent):
    """步骤SSE事件"""
    event: Literal["step"] = "step"
    data: StepEventData

    @classmethod
    def from_event(cls, event: Event) -> "StepSSEEvent":
        """类方法，用于将步骤事件Domain模型转换成步骤SSE事件模型"""
        return cls(
            data=StepEventData(
                **BaseEventData.base_event_data(event),
                id=event.step.id,
                status=event.step.status,
                description=event.step.description,
            )
        )

class PlanEventData(BaseEventData):
    """计划事件数据"""
    steps: List[StepEventData] = Field(default_factory=list)

class PlanSSEEvent(BaseSSEEvent):
    """计划SSE事件"""
    event: Literal["plan"] = "plan"
    data: PlanEventData

    @classmethod
    def from_event(cls, event: Event) -> "PlanSSEEvent":
        """类方法，用于将计划事件Domain模型转换成计划SSE事件模型"""
        return cls(
            data=PlanEventData(
                **BaseEventData.base_event_data(event),
                steps=[
                    StepEventData(
                        **BaseEventData.base_event_data(event),
                        id=step.id,
                        status=step.status,
                        description=step.description,
                    ) for step in event.plan.steps
                ],
            )
        )

class ToolResultData(BaseModel):
    """工具执行结果数据（仅包含 success 和 message，data 不传输到前端）"""
    success: bool
    message: Optional[str] = None

class ToolEventData(BaseEventData):
    """工具事件数据"""
    tool_call_id: str # 工具调用ID
    name: str # 工具箱名称
    status: ToolEventStatus # 工具状态
    function: str # 工具名称
    args: Dict[str, Any] # 工具参数
    content: Optional[Any] = None # 工具调用结果（截图/文件内容等富内容）
    result: Optional[ToolResultData] = None # 工具调用成功/失败状态

class ToolSSEEvent(BaseSSEEvent):
    """工具SSE事件"""
    event: Literal["tool"] = "tool"
    data: ToolEventData

    @classmethod
    def from_event(cls, event: Event) -> "ToolSSEEvent":
        """类方法，用于将工具事件Domain模型转换成工具SSE事件模型"""
        result: Optional[ToolResultData] = None
        if event.function_result is not None:
            result = ToolResultData(
                success=event.function_result.success,
                message=event.function_result.message,
            )
        return cls(
            data=ToolEventData(
                **BaseEventData.base_event_data(event),
                tool_call_id=event.tool_call_id,
                name=event.tool_name,
                status=event.status,
                function=event.function_name,
                args=event.function_args,
                content=event.tool_content,
                result=result,
            )
        )
    

class DoneSSEEvent(BaseSSEEvent):
    """完成SSE事件"""
    event: Literal["done"] = "done"


class WaitSSEEvent(BaseSSEEvent):
    """等待SSE事件"""
    event: Literal["wait"] = "wait"

class ErrorEventData(BaseEventData):
    """错误事件数据"""
    error: str # 错误信息

class ErrorSSEEvent(BaseSSEEvent):
    """错误SSE事件"""
    event: Literal["error"] = "error"
    data: ErrorEventData

class ThinkingEventData(BaseEventData):
    """思考事件数据"""
    content: str = "" # 思考内容块
    status: str = "thinking" # thinking=流式块, done=思考完毕

class ThinkingSSEEvent(BaseSSEEvent):
    """思考SSE事件"""
    event: Literal["thinking"] = "thinking"
    data: ThinkingEventData

AgentSSEEvent=Union[
    CommonSSEEvent,
    MessageSSEEvent,
    TitleSSEEvent,
    StepSSEEvent,
    PlanSSEEvent,
    ToolSSEEvent,
    DoneSSEEvent,
    ErrorSSEEvent,
    WaitSSEEvent,
    ThinkingSSEEvent,
]

@dataclass
class EventMapping:
    """事件映射数据类，用于存储事件映射信息，涵盖流式事件类型、数据类、事件类型字符串"""
    sse_event_type: Type[BaseSSEEvent]
    data_class: Type[BaseEventData]
    event_type: str

class EventMapper:
    """事件映射类，利用Python自身提供的自省机制，将业务逻辑中的Event转换成适合流式传输的AgentSSEEvent"""
    _cache_mapping: Optional[Dict[str, EventMapping]] = None

    @staticmethod
    def event_to_sse_event(event: Event) -> AgentSSEEvent:
        """将领域事件转换为Agent流式事件模型"""
        # 获取领域事件映射表
        event_type_mapping = EventMapper._get_event_type_mapping()

        # 根据传递进来的事件获取映射类
        event_mapping = event_type_mapping.get(event.type)

        # 如果找到了类型则进行转换
        if event_mapping is not None:
            return event_mapping.sse_event_type.from_event(event)
        
        # 如果未找到类型，则返回通用事件
        return CommonSSEEvent.from_event(event)

    @staticmethod
    def events_to_sse_events(events: List[Event]) -> List[AgentSSEEvent]:
        """将领域事件模型列表转换为SSE流式事件列表"""
        return list(filter(lambda x: x is not None, [
            EventMapper.event_to_sse_event(event) for event in events
        ]))

    @staticmethod
    def _get_event_type_mapping() -> Dict[str, EventMapping]:
        """通过反射动态构建从事件类型字符串到AgentSSEEvent的映射"""
        # 判断缓存映射是否存在，如果存在则直接返回
        if EventMapper._cache_mapping is not None:
            return EventMapper._cache_mapping
        
        # 获取 AgentSSEEvent 的所有可能存在类
        sse_event_classes = get_args(AgentSSEEvent)
        mapping = {}

        # 循环遍历所有可能的AgentSSEEvent类，构建映射
        for sse_event_class in sse_event_classes:
            # 跳过基类
            if sse_event_class is BaseSSEEvent:
                continue

            # 检查类是否包含 event 属性
            if hasattr(sse_event_class, "__annotations__") and "event" in sse_event_class.__annotations__:
                # 提取事件字段
                event_field = sse_event_class.__annotations__["event"]

                # 提取事件的具体值(Literal的值)
                if hasattr(event_field, "__args__") and len(event_field.__args__) > 0:
                    event_type = event_field.__args__[0]

                    # 提取 sse 的 payload
                    data_class = None
                    if hasattr(sse_event_class, "__annotations__") and "data" in sse_event_class.__annotations__:
                        data_class = sse_event_class.__annotations__["data"]

                    # 构建映射
                    mapping[event_type] = EventMapping(
                        sse_event_type=sse_event_class,
                        data_class=data_class,
                        event_type=event_type,
                    )
        
        # 缓存映射
        EventMapper._cache_mapping = mapping
        return mapping