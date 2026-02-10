import asyncio
from tabnanny import check
from typing import List

from app.domain.external.health_checker import HealthChecker
from app.domain.models.health_status import HealthStatus


class StatusService:
    """系统服务状态服务"""

    def __init__(self, checkers: List[HealthChecker]) -> None:
        self._checkers = checkers

    async def check_all(self) -> List[HealthStatus]:
        results = await asyncio.gather(
            *(checker.check() for checker in self._checkers),
            return_exceptions=True, # 捕获异常而不是让 gather 失效
        )

        processed_results = []
        for res in results:
            if isinstance(res, Exception):
                processed_results.append(HealthStatus(
                    service="未知服务",
                    status="error",
                    details=f"未知检查器发生错误: {str(res)}"
                ))
            else:
                processed_results.append(res)
        
        return processed_results