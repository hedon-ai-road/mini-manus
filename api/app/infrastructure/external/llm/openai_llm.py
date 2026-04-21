import logging
import json
import re
import uuid
from typing import Any, AsyncGenerator, List, Dict, Optional, Tuple

from app.domain.external.llm import LLM
from app.domain.models.app_config import LLMConfig
from app.application.errors.exceptions import ServerError

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
#  DSML 格式工具调用解析
#  DeepSeek 在 API 过载/降级时有时会把工具调用输出为 DSML 文本而非
#  结构化 tool_calls，格式示例：
#    <|DSML|function_calls>
#      <|DSML|invoke name="func_name">
#        <|DSML|parameter name="param" string="true">value</|DSML|parameter>
#      </|DSML|invoke>
#    </|DSML|function_calls>
# ──────────────────────────────────────────────────────────────
_DSML_FC_RE = re.compile(
    r'<\|DSML\|function_calls>(.*?)</\|DSML\|function_calls>',
    re.DOTALL | re.IGNORECASE,
)
_DSML_INVOKE_RE = re.compile(
    r'<\|DSML\|invoke\s+name="([^"]+)">(.*?)</\|DSML\|invoke>',
    re.DOTALL | re.IGNORECASE,
)
_DSML_PARAM_RE = re.compile(
    r'<\|DSML\|parameter\s+name="([^"]+)"[^>]*>(.*?)</\|DSML\|parameter>',
    re.DOTALL | re.IGNORECASE,
)

def _parse_dsml_tool_calls(content: str) -> Tuple[str, Optional[List[Dict]]]:
    """检测并解析 content 中的 DSML 格式工具调用。

    Returns:
        (cleaned_content, tool_calls)
        - cleaned_content: 去掉 DSML 块后的正文（可能为空）
        - tool_calls: 解析出的 OpenAI 风格 tool_calls 列表；未检测到时为 None
    """
    fc_match = _DSML_FC_RE.search(content)
    if not fc_match:
        return content, None

    tool_calls = []
    for invoke_match in _DSML_INVOKE_RE.finditer(fc_match.group(1)):
        func_name = invoke_match.group(1).strip()
        params: Dict[str, str] = {}
        for param_match in _DSML_PARAM_RE.finditer(invoke_match.group(2)):
            params[param_match.group(1).strip()] = param_match.group(2).strip()
        tool_calls.append({
            "id": str(uuid.uuid4()),
            "type": "function",
            "function": {
                "name": func_name,
                "arguments": json.dumps(params, ensure_ascii=False),
            },
        })

    cleaned = _DSML_FC_RE.sub("", content).strip()
    logger.info(f"检测到 DSML 格式工具调用，已解析 {len(tool_calls)} 个: {[tc['function']['name'] for tc in tool_calls]}")
    return cleaned, tool_calls if tool_calls else None

class OpenAILLM(LLM):
    """基于 OpenAI SDK/兼容 OpenAI 格式的 LLM 调用类"""

    def __init__(self, llm_config: LLMConfig, **kwargs) -> None:
        """构造函数，完成异步 OpenAI 客户端的创建和参数初始化"""
        self._client = AsyncOpenAI(
            base_url=str(llm_config.base_url),
            api_key=llm_config.api_key,
            **kwargs,
        )
        self._model_name = llm_config.model_name
        self._temperature = llm_config.temperature
        self._max_tokens = llm_config.max_tokens
        self._timeout_sec = 3600

    @property
    def model_name(self) -> str:
        """返回 LLM 的名字"""
        return self._model_name

    @property
    def temperature(self) -> float:
        """返回 LLM 的温度"""
        return self._temperature

    @property
    def max_tokens(self) -> int:
        """返回 LLM 返回的最大 token 树"""
        return self._max_tokens


    async def invoke(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None,
        response_format: Dict[str, Any] = None,
        tool_choice: str = None,
    ) -> Dict[str, Any]:
        """调用 LLM 接口，该接口可转为流式

        Args:
            messages: 消息列表
            tools: 工具列表. Defaults to None.
            response_format: 响应格式. Defaults to None.
            tool_choice: 工具选择策略. Defaults to None.
        """
        try:
            if tools:
                logger.info(f"调用 OpenAI 客户端向 LLM 发起请求并携带工具信息：{self._model_name}")
                response = await self._client.chat.completions.create(
                    model=self._model_name,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    messages=messages,
                    response_format=response_format,
                    tools=tools,
                    tool_choice=tool_choice,
                    parallel_tool_calls=False, # 关闭并行工具调用(deepseek没有这个参数)
                    timeout=self._timeout_sec,
                )
            else:
                logger.info(f"调用 OpenAI 客户端向 LLM 发起请求并未携带工具信息：{self._model_name}")
                response = await self._client.chat.completions.create(
                    model=self._model_name,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    messages=messages,
                    response_format=response_format,
                    timeout=self._timeout_sec,
                )
            
            logger.info(f"OpenAI 客户端返回内容: {response.model_dump()}")
            return response.choices[0].message.model_dump()
        except Exception as e:
            logger.error(f"调用 OpenAI 客户端发生异常: {str(e)}")
            raise ServerError(f"LLM 调用失败: {type(e).__name__}: {str(e)}") from e

    async def invoke_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None,
        response_format: Dict[str, Any] = None,
        tool_choice: str = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用 LLM 接口，实时 yield 思考内容块，最终 yield 完整 message

        每次 yield 的 dict 格式为：
          - {"type": "thinking", "content": str}  —— 思考内容块（reasoning_content）
          - {"type": "result",   "message": Dict} —— 完整消息（role/content/tool_calls）

        Args:
            messages: 消息列表
            tools: 工具列表. Defaults to None.
            response_format: 响应格式. Defaults to None.
            tool_choice: 工具选择策略. Defaults to None.
        """
        try:
            params = dict(
                model=self._model_name,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                messages=messages,
                response_format=response_format,
                timeout=self._timeout_sec,
                stream=True,
            )
            if tools:
                logger.info(f"流式调用 OpenAI 客户端并携带工具信息：{self._model_name}")
                params["tools"] = tools
                params["tool_choice"] = tool_choice
                params["parallel_tool_calls"] = False
            else:
                logger.info(f"流式调用 OpenAI 客户端并未携带工具信息：{self._model_name}")

            content = ""
            tool_calls_map: Dict[int, Dict[str, Any]] = {}

            stream = await self._client.chat.completions.create(**params)
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # 实时 yield reasoning_content（思考内容）
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    yield {"type": "thinking", "content": reasoning}

                # 累积 content
                if delta.content:
                    content += delta.content

                # 累积 tool_calls
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {
                                "id": tc_delta.id or "",
                                "type": "function",
                                "function": {
                                    "name": (tc_delta.function.name or "") if tc_delta.function else "",
                                    "arguments": (tc_delta.function.arguments or "") if tc_delta.function else "",
                                },
                            }
                        else:
                            if tc_delta.id:
                                tool_calls_map[idx]["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    tool_calls_map[idx]["function"]["name"] += tc_delta.function.name
                                if tc_delta.function.arguments:
                                    tool_calls_map[idx]["function"]["arguments"] += tc_delta.function.arguments

            tool_calls = [tool_calls_map[k] for k in sorted(tool_calls_map.keys())] if tool_calls_map else None

            # 若 LLM 降级输出了 DSML 格式工具调用，解析并转换为标准 tool_calls
            if not tool_calls and content:
                content, dsml_tool_calls = _parse_dsml_tool_calls(content)
                if dsml_tool_calls:
                    tool_calls = dsml_tool_calls

            assembled: Dict[str, Any] = {
                "role": "assistant",
                "content": content or None,
                "tool_calls": tool_calls,
            }
            logger.info(f"流式调用 OpenAI 客户端完成，assembled message: {assembled}")
            yield {"type": "result", "message": assembled}
        except Exception as e:
            logger.error(f"流式调用 OpenAI 客户端发生异常: {str(e)}")
            raise ServerError(f"LLM 流式调用失败: {type(e).__name__}: {str(e)}") from e


if __name__ == "__main__":
    import dotenv
    import os
    import asyncio

    dotenv.load_dotenv()

    async def main():
        llm = OpenAILLM(LLMConfig(
            base_url="https://api.deepseek.com",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            model_name="deepseek-chat",
        ))

        response = await llm.invoke([{"role": "user", "content": "Hi"}])
        print(response)
    
    asyncio.run(main())