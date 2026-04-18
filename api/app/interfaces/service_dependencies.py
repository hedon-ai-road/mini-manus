from fastapi import Depends
import logging
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.file_service import FileService
from app.domain.repositories import file_repository
from app.domain.repositories.file_repository import FileRepository
from app.infrastructure.external.health_checker.redis_health_checker import RedisHealthChecker
from app.infrastructure.external.health_checker.postgres_health_checker import PostgresHealthChecker
from app.infrastructure.external.json_parser.repair_json_parser import RepairJsonParser
from app.infrastructure.external.llm.openai_llm import OpenAILLM
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.infrastructure.external.task.redis_stream_task import RedisStreamTask
from app.infrastructure.external.search.bing_search import BingSearchEngine
from app.infrastructure.repositories.db_file_repository import DBFileRepository
from app.infrastructure.storage.oss import OSS, get_oss
from app.infrastructure.external.file_storage.oss_file_storage import OSSFileStorage
from app.infrastructure.storage.redis import get_redis
from app.infrastructure.storage.redis import RedisClient
from app.infrastructure.storage.posgres import get_db_session
from app.application.services.session_service import SessionService
from app.application.services.status_service import StatusService
from app.application.services.app_config_service import AppConfigService
from app.infrastructure.repositories.file_app_config_repository import FileAppConfigRepository
from core.config import get_settings
from app.interfaces.repository_dependencies import get_db_session_repository
from app.domain.repositories.session_repository import SessionRepository
from app.application.services.agent_service import AgentService
from app.domain.external.json_parser import JsonParser
from app.domain.external.search import SearchEngine
from app.domain.external.llm import LLM
from app.domain.models.app_config import AgentConfig, MCPConfig, A2AConfig
from app.domain.external.sandbox import Sandbox
from app.domain.external.task import Task


logger = logging.getLogger(__name__)
settings = get_settings()

@lru_cache()
def get_app_config_service() -> AppConfigService:
    """获取应用配置服务"""

    # 1. 获取数据仓库并打印日志
    logger.info("加载获取 AppConfigService")
    file_app_config_repository = FileAppConfigRepository(settings.app_config_file_path)

    # 2. 实例化 AppConfigService
    return AppConfigService(app_config_repository=file_app_config_repository)

@lru_cache
def get_status_service(
    db_session: AsyncSession = Depends(get_db_session),
    redis_client: RedisClient = Depends(get_redis)
) -> StatusService:
    """获取状态服务"""

    postgres_checker = PostgresHealthChecker(db_session)
    redis_checker = RedisHealthChecker(redis_client)

    logger.info("加载获取 StatusService")

    return StatusService(checkers=[postgres_checker, redis_checker])


@lru_cache()
def get_file_service(
    oss: OSS = Depends(get_oss),
    db_session: AsyncSession = Depends(get_db_session)
) -> FileService:
    """获取文件服务"""

    file_repository = DBFileRepository(db_session=db_session)
    file_storage = OSSFileStorage(
        bucket=settings.oss_bucket,
        oss=oss,
        repository=file_repository,
    )

    return FileService(file_storage=file_storage, file_repository=file_repository)

@lru_cache()
def get_session_service(
    session_repository: SessionRepository = Depends(get_db_session_repository),
) -> SessionService:
    """获取会话服务"""
    return SessionService(session_repository=session_repository)

@lru_cache()
def get_agent_service(
    oss: OSS = Depends(get_oss),
    db_session: AsyncSession = Depends(get_db_session),
    session_repository: SessionRepository = Depends(get_db_session_repository),
) -> AgentService:
    """获取 Agent 服务"""
    app_config_repository = FileAppConfigRepository(settings.app_config_file_path)
    app_config = app_config_repository.load()
    file_repository = DBFileRepository(db_session=db_session)

    llm = OpenAILLM(llm_config=app_config.llm_config)
    file_storage = OSSFileStorage(
        bucket=settings.oss_bucket,
        oss=oss,
        repository=file_repository,
    )
    json_parser = RepairJsonParser()
    search_engine = BingSearchEngine()
    sandbox_cls = DockerSandbox
    task_cls = RedisStreamTask
    return AgentService(
        session_repository=session_repository,
        file_repository=file_repository,
        file_storage=file_storage,
        json_parser=json_parser,
        search_engine=search_engine,
        llm=llm,
        agent_config=app_config.agent_config,
        mcp_config=app_config.mcp_config,
        a2a_config=app_config.a2a_config,
        sandbox_cls=sandbox_cls,
        task_cls=task_cls,
    )