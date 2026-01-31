import logging
from functools import lru_cache
from typing import Optional

import alibabacloud_oss_v2 as oss
import alibabacloud_oss_v2.aio as oss_aio

from core.config import Settings, get_settings


logger = logging.getLogger(__name__)

class OSS:
    """阿里云 OSS 对象存储"""

    def __init__(self):
        self._settings: Settings = get_settings()
        self._client: Optional[oss_aio.AsyncClient] = None

    async def init(self) -> None:
        """初始化 OSS 客户端"""
        if self._client is not None:
            logger.warning("OSS 客户端已初始化，无需重复操作")
            return
        
        try:
            logger.info("正在初始化 OSS 客户端...")
            
            # 1. 创建静态凭证提供者
            credentials_provider = oss.credentials.StaticCredentialsProvider(
                access_key_id=self._settings.oss_access_key_id,
                access_key_secret=self._settings.oss_access_key_secret,
            )
            
            # 2. 创建 OSS 配置
            config = oss.config.load_default()
            config.credentials_provider = credentials_provider
            config.region = self._settings.oss_region_id
            
            # 3. 创建异步 OSS 客户端
            self._client = oss_aio.AsyncClient(config)
            
            logger.info(f"OSS 客户端初始化成功，区域：{self._settings.oss_region_id}")
            
        except Exception as e:
            logger.error(f"初始化 OSS 客户端失败：{str(e)}")
            raise
    
    async def shutdown(self) -> None:
        """关闭 OSS 客户端"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("OSS 客户端已关闭")
        
        get_oss.cache_clear()
    
    @property
    def client(self) -> oss_aio.AsyncClient:
        """获取 OSS 客户端实例"""
        if self._client is None:
            raise RuntimeError("OSS 客户端未初始化，请先调用 init() 方法")
        return self._client
    
    @property
    def bucket(self) -> str:
        """获取 Bucket 名称"""
        return self._settings.oss_bucket


@lru_cache
def get_oss() -> OSS:
    """获取 OSS 实例（单例模式）"""
    return OSS()