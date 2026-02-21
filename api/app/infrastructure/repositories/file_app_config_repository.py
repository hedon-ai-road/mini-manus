import logging
from pathlib import Path
from typing import Optional
import yaml

from fastapi import logger
from app.domain.models.app_config import AgentConfig, AppConfig, LLMConfig, MCPConfig
from app.domain.repositories.app_config_repository import AppConfigRepository
from app.application.errors.exceptions import ServerError
from filelock import FileLock

logger = logging.getLogger(__name__)

class FileAppConfigRepository(AppConfigRepository):
    """基于本地文件的 App 配置数据仓库"""

    def __init__(self, config_path: str) -> None:
        """构造函数，完成文件配置仓库的相关信息初始化"""

        # 1. 获取当前项目的根目录
        root_dir = Path.cwd()

        # 2. 拼接配置文件路径并校验基础信息
        self._config_path = root_dir.joinpath(config_path)
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = self._config_path.with_suffix(".lock") # 文件锁
    
    def _create_default_app_config_if_not_exists(self):
        if not self._config_path.exists():
            default_app_config = AppConfig(
                llm_config=LLMConfig(),
                agent_config=AgentConfig(),
                mcp_config=MCPConfig()
            )
            self.save(default_app_config)

    def load(self) -> Optional[AppConfig]:
        """从本地 yaml 文件中加载应用配置"""
        self._create_default_app_config_if_not_exists()

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return AppConfig.model_validate(data) if data else None
        except Exception as e:
            logger.error(f"读取应用配置失败：{str(e)}")
            raise ServerError("读取应用配置失败，请稍后重试")

    def save(self, app_config: AppConfig) -> None:
        """将 app_config 存储到本地 yaml 配置"""
        lock = FileLock(self._lock_file, timeout=5)

        try:
            with lock:
                data_to_dump = app_config.model_dump(mode="json")
                with open(self._config_path, "w", encoding="utf-8") as f:
                    yaml.dump(data_to_dump, f, allow_unicode=True, sort_keys=False)
        except TimeoutError:
            logger.error("无法获取配置文件")
            raise ServerError("写入配置文件失败，请稍后重试")