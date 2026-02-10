from typing import Any, List, Protocol, Dict

class LLM(Protocol):
    """用于 Agent 应用与 LLM 进行交互的接口协议"""

    async def invoke(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None,
        response_format: Dict[str, Any] = None,
        tool_choice: str = None,
    ) -> Dict[str, Any]:
        """调用 LLM 接口

        Args:
            messages: 消息列表
            tools: 工具列表. Defaults to None.
            response_format: 响应格式. Defaults to None.
            tool_choice: 工具选择策略. Defaults to None.
        """
        ...
    
    @property
    def model_name(self) -> str:
        """返回 LLM 的名字"""
        ...

    @property
    def temperature(self) -> float:
        """返回 LLM 的温度"""
        ...

    @property
    def max_tokens(self) -> int:
        """返回 LLM 返回的最大 token 树"""
        ...