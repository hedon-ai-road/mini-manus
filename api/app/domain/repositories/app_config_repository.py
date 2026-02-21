from typing import Optional, Protocol

from app.domain.models.app_config import AppConfig

class AppConfigRepository(Protocol):
    """应用配置仓库接口"""

    async def load(self) -> Optional[AppConfig]:
        """加载获取应用配置"""
        ...
    
    async def save(self, app_config: AppConfig) -> None:
        """存储更新的应用配置"""
        ...