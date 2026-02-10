import logging
from typing import Any, List, Dict

from app.domain.external.llm import LLM
from app.domain.models.app_config import LLMConfig
from app.application.errors.exceptions import ServerError

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class OpenAILLM(LLM):
    """基于 OpenAI SDK/兼容 OpenAI 格式的 LLM 调用类"""

    def __init__(self, llm_config: LLMConfig) -> None:
        """构造函数，完成异步 OpenAI 客户端的创建和参数初始化"""
        self._client = AsyncOpenAI(
            base_url=str(llm_config.base_url),
            api_key=llm_config.api_key,
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
            raise ServerError("调用 OpenAI 客户端向 LLM 发起请求出错")


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