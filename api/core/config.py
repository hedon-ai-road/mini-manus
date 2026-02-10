from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """后端中控配置信息，从 .env 或环境变量中加载"""

    # 项目基础配置
    env: str = "development"
    log_level: str = "INFO"
    app_config_file_path: str = "config.yaml"

    # 数据库相关配置
    sqlalchemy_database_uri: str = "postgresql+asyncpg://admin:admin123@localhost:5433/mini_manus"

    # Redis 相关配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = ""

    # 对象存储相关配置
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_region_id: str = "cn-beijing"
    oss_endpoint: str = "oss-cn-beijing.aliyuncs.com"
    oss_bucket: str = "mini-manus"

    # 使用 pydantic v2 的写法来完成环境变量信息的告知
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    """获取当前项目的配置信息，并对内容进行缓存，避免重复读取"""
    settings = Settings()
    return settings