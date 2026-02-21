from app.application.errors.exceptions import NotFoundError
from app.domain.models.app_config import AgentConfig, AppConfig, LLMConfig, MCPConfig
from app.domain.repositories.app_config_repository import AppConfigRepository


class AppConfigService:
    """应用配置服务"""

    def __init__(self, app_config_repository: AppConfigRepository) -> None:
        """构造函数，完成应用配置服务的初始化"""
        self.app_config_repository = app_config_repository

    async def _load_app_config(self) -> AppConfig:
        """加载所有应用配置信息"""
        return await self.app_config_repository.load()

    async def get_llm_config(self) -> LLMConfig:
        """获取 LLM 提供商配置"""
        return await self._load_app_config().llm_config

    async def update_llm_config(self, llm_config: LLMConfig) -> LLMConfig:
        """根据传递的 llm_config 更新语言模型提供商配置"""
        app_config = await self._load_app_config()
        if not llm_config.api_key.strip():
            llm_config.api_key = app_config.llm_config.api_key
        
        app_config.llm_config = llm_config
        await self.app_config_repository.save(app_config)
        return app_config.llm_config

    async def get_agent_config(self) -> AgentConfig:
        """获取 Agent 配置"""
        return await self._load_app_config().agent_config

    async def update_agent_config(self, agent_config: AgentConfig) -> AgentConfig:
        """根据传递的 agent_config 更新 Agent 配置"""
        app_config = await self._load_app_config()
        app_config.agent_config = agent_config
        await self.app_config_repository.save(app_config)
        return app_config.agent_config

    async def update_and_create_mcp_servers(self, mcp_config: MCPConfig) -> MCPConfig:
        """根据传递的数据新增或更新 MCP 配置"""
        app_config = await self._load_app_config()
        app_config.mcp_config.mcpServers.update(mcp_config.mcpServers)
        await self.app_config_repository.save(app_config)
        return app_config.mcp_config

    async def delete_mcp_server(self, server_name: str) -> MCPConfig:
        """根据传递的服务名称删除 MCP 配置"""
        app_config = await self._load_app_config()
        if server_name not in app_config.mcp_config.mcpServers:
            raise NotFoundError(f"该 MCP 服务[{server_name}]不存在，请核实后重试")

        del app_config.mcp_config.mcpServers[server_name]
        await self.app_config_repository.save(app_config)
        return app_config.mcp_config

    async def set_mcp_server_enabled(self, server_name: str, enabled: bool):
        """更新 MCP 服务启用状态"""
        app_config = await self._load_app_config()
        if server_name not in app_config.mcp_config.mcpServers:
            raise NotFoundError(f"该 MCP 服务[{server_name}]不存在，请核实后重试")

        app_config.mcp_config.mcpServers[server_name].enabled = enabled
        await self.app_config_repository.save(app_config)