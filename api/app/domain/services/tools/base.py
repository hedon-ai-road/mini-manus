"""
MiniManus 工具设计思路：

1. 所有工具都必须继承一个 BaseTool 基类，拥有统一的 invoke 方法用于调用该类下的对应工具；
2. 定义一个装饰器，被该装饰器装饰的方法会填充 _tool_name、_tool_description、_tool_schema 属性；
3. 工具类可以通过 get_tools 快速获取基于缓存的 schema 参数信息，这样 LLM 就可以便捷调用；
4. LLM 生成的内容有可能会有幻觉，在调用工具前需要筛选出 LLM 生成参数中符合工具的相关数据。
"""

from typing import Any, Callable, Dict, List
import inspect

from app.domain.models.tool_result import ToolResult


def tool(
    name: str,
    description: str,
    parameters: Dict[str, Dict[str, Any]],
    required: List[str],
) -> Callable:
    """定义 OpenAI 工具装饰器，用于将一个函数/方法添加上对应的工具声明"""
    
    def decorator(func):
        """装饰器函数，用于将 name/description/parameters/required 转换成对应的属性"""
        # 1. 创建工具声明数据结构
        tool_schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required,
                }
            }
        }

        # 2. 将对应属性绑定到 func 上
        func._tool_name = name
        func._tool_description = description
        func._tool_schema = tool_schema
        return func
    
    return decorator

class BaseTool:
    """基础工具类，管理统一的工具集"""
    name: str = "" # 工具集名字

    def __init__(self) -> None:
        """构造函数，完成缓存初始化"""
        self._tools_cache = None

    @classmethod
    def _filter_parameter(cls, method: Callable, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """过滤无用参数"""
        filtered_kwargs = {}

        sign = inspect.signature(method)
        for key, value in kwargs.items():
            if key in sign.parameters:
                filtered_kwargs[key] = value
        
        return filtered_kwargs

    def get_tools(self) -> List[Dict[str, Any]]:
        """获取所有以注册的工具列表 schema 信息，用于 LLM 绑定工具"""
        if self._tools_cache is not None:
            return self._tools_cache

        tools = []
        for _, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "_tool_schema"):
                tools.append(getattr(method, "_tool_schema"))

        self._tools_cache = tools
        return tools

    def has_tool(self, tool_name: str) -> bool:
        """判断是否存在指定的工具"""
        for _, method in inspect.inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "_tool_name") and getattr(method, "_tool_name") == tool_name:
                return True
        return False


    async def invoke(self, tool_name: str, **kwargs) -> ToolResult:
        """调用指定工具并获取结果"""
        # 1. 循环遍历工具集的所有方法
        for _, method in inspect.getmembers(self, inspect.ismethod):
            # 2. 判断对应是否存在 _tool_name 属性
            if hasattr(method, "_tool_name") and getattr(method, "_tool_name") == tool_name:
                # 3. 筛选传递的 kwargs 参数，保留 method 对应的参数，其余的剔除
                filtered_kwargs = self._filter_parameter(method, kwargs)
                # 4. 调用方法获取工具结果
                return await method(**filtered_kwargs)
        
        # 5. 没找到对应工具
        return ValueError(f"工具[{tool_name}]未找到")

    