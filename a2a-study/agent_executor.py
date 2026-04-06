import dotenv
import os

from openai import AsyncOpenAI
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.utils import new_agent_text_message
from a2a.server.events.event_queue import EventQueue

dotenv.load_dotenv()

class DeepseekAgent:

    @classmethod
    async def invoke(cls, query: str) -> str:
        client = AsyncOpenAI(
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
            api_key=os.getenv("DEEPSEEK_API_KEY")
        )
        response = await client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": query}]
        )
        return f"推理内容: {response.choices[0].message.reasoning_content}\n\n答案: {response.choices[0].message.content}"


class DeepseekAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agent = DeepseekAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.message.parts[0].root.text
        result = await DeepseekAgent.invoke(query)
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("暂不支持取消")