from typing import Any, Dict, List, Optional, Protocol, Union

class JsonParser(Protocol):
    """JSON 解析器，用于解析 JSON 字符串并修复"""
    
    async def invoke(self, text: str, default_value: Optional[Any] = None) -> Union[Dict, List, Any]:
        """调用函数，用于将传递进来的文本进行 JSON 解析并返回"""
        ...