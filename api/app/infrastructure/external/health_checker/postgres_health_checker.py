from app.domain.models.health_status import HealthStatus
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.domain.external.health_checker import HealthChecker


logger = logging.getLogger(__name__)

class PostgresHealthChecker(HealthChecker):
    """Postgres 健康检查器"""

    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def check(self) -> HealthChecker:
        try:
            await self._db_session.execute(text("SELECT 1;"))
            return HealthStatus(service="postgres", status="ok")
        except Exception as e:
            logger.error(f"Postgres 健康检查失败: {str(e)}")
            return HealthStatus(
                service="postgres",
                status="error",
                details=f"{str(e)}"
            )