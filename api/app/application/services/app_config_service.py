from app.domain.models.app_config import AgentConfig, AppConfig, LLMConfig
from app.domain.repositories.app_config_repository import AppConfigRepository


class AppConfigService:
    """应用配置服务"""

    def __init__(self, app_config_repository: AppConfigRepository) -> None:
        """构造函数，完成应用配置服务的初始化"""
        self.app_config_repository = app_config_repository

    def _load_app_config(self) -> AppConfig:
        """加载所有应用配置信息"""
        return self.app_config_repository.load()

    def get_llm_config(self) -> LLMConfig:
        """获取 LLM 提供商配置"""
        return self._load_app_config().llm_config

    def update_llm_config(self, llm_config: LLMConfig) -> LLMConfig:
        """根据传递的 llm_config 更新语言模型提供商配置"""
        app_config = self._load_app_config()
        if not llm_config.api_key.strip():
            llm_config.api_key = app_config.llm_config.api_key
        
        app_config.llm_config = llm_config
        self.app_config_repository.save(app_config)
        return app_config.llm_config

    def get_agent_config(self) -> AgentConfig:
        """获取 Agent 配置"""
        return self._load_app_config().agent_config

    def update_agent_config(self, agent_config: AgentConfig) -> AgentConfig:
        """根据传递的 agent_config 更新 Agent 配置"""
        app_config = self._load_app_config()
        app_config.agent_config = agent_config
        self.app_config_repository.save(app_config)
        return app_config.agent_config