from typing import Any, Dict, List, Optional
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Memory(BaseModel):
    """记忆类，定义 Agent 的记忆基础信息"""
    messages: List[Dict[str, Any]] = Field(default_factory=list)

    def get_message_role(self, message: Dict[str, Any]) -> str:
        """根据传递的消息来获取信息的角色信息"""
        return message.get("role")

    def add_message(self, message: Dict[str, Any]) -> None:
        """往记忆中添加一条消息"""
        self.messages.append(message)

    def add_messages(self, messages: List[Dict[str, Any]]) -> None:
        """往记忆中添加多条消息"""
        self.messages.extend(messages)

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        return self.messages[-1] if len(self.messages) > 0 else None

    def roll_back(self) -> None:
        self.messages = self.messages[:-1]

    def compact(self) -> None:
        """记忆压缩，将记忆中已经执行的工具(搜索/网页源码获取/浏览器访问结果)这类已经执行过的消息进行压缩简化"""
        for message in self.messages:
            if self.get_message_role(message) == "tool":
                # todo: 工具的名字待定
                if message.get("function_name") in []:
                    # todo: 工具的调用结果待确定
                    message["content"] = "(REMOVED)"
                    logger.debug(f"从记忆中移除对应工具的结果: {message['function_name']}")

    @property
    def empty(self) -> bool:
        """检查记忆是否为空"""
        return len(self.messages) == 0
    
    