from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication

import uvicorn

from agent_executor import DeepseekAgentExecutor

if __name__ == "__main__":
    # 1. 定义 Agent 技能
    skill = AgentSkill(
        id="calculator",
        name="计算器",
        description="支持计算各种复杂数学公式",
        tags=["计算器"],
        examples=["445*34", "123+456", "789-123", "123*456", "789/123+12"],
    )

    # 2. 定义 Agent 卡片
    agent_card = AgentCard(
        name="DeepSeek智能体",
        description="DeepSeek 是一个基于 DeepSeek 大模型的智能体，支持深度思考，在需要深度思考时可以使用",
        url="http://localhost:9999",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
        supports_authenticated_extended_card=False,
    )

    # 3. 使用 a2a 默认的请求处理器(jsonrpc)
    request_handler = DefaultRequestHandler(
        agent_executor=DeepseekAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # 4. 启动 a2a 服务器
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host="0.0.0.0", port=9999)
