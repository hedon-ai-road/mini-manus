from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ToolResult(BaseModel, Generic[T]):
    """工具结果领域模型"""
    success: bool = True # 是否成功调用
    message: Optional[str] = None # 额外的信息提示
    data: Optional[T] = None # 工具的执行结果/数据


    @classmethod
    def from_sandbox(cls, code: int, msg: str, data: Optional[T] = None, **kwargs) -> "ToolResult":
        """从沙箱返回的结果中创建 ToolResult 实例"""
        return cls(success=code < 300, message=msg, data=data)