import logging

from app.infrastructure.storage.redis import RedisClient
from app.domain.models.health_status import HealthStatus
from app.domain.external.health_checker import HealthChecker

logger = logging.getLogger(__name__)

class RedisHealthChecker(HealthChecker):
    """Redis 健康检查器"""

    def __init__(self, redis_client: RedisClient) -> None:
        self._redis_client = redis_client

    async def check(self) -> HealthChecker:
        try:
            if await self._redis_client.client.ping():
                return HealthStatus(service="redis", status="ok")
            else:
                return HealthStatus(service="redis", status="error", details="Redis 服务 Ping 失败")
        except Exception as e:
            logger.error(f"Redis 健康检查失败: {str(e)}")
            return HealthStatus(
                service="redis",
                status="error",
                details=f"{str(e)}"
            )