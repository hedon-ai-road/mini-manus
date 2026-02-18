import logging

from fastapi import APIRouter, Depends

from app.application.services.app_config_service import AppConfigService
from app.interfaces.service_dependencies import get_app_config_service
from app.interfaces.schemas.base import Response
from app.domain.models.app_config import AgentConfig, LLMConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/app-config", tags=["设置模块"])

@router.get(
    path="/llm",
    response_model=None,
    summary="获取 LLM 配置信息",
    description="包含 LLM 提供商的 base_url、temperature、model_name、max_tokens"
)
async def get_llm_config(
    app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[LLMConfig]:
    llm_config = app_config_service.get_llm_config()
    return Response.success(data=llm_config.model_dump(exclude={"api_key"}))

@router.post(
    path="/llm",
    response_model=None,
    summary="更新 LLM 配置信息",
    description="更新 LLM 配置信息，当 api_key 为空的时候表示不更新该字段"
)
async def update_llm_config(
    new_llm_config: LLMConfig,
    app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[LLMConfig]:
    updated_llm_config = app_config_service.update_llm_config(new_llm_config)
    return Response.success(
        msg="更新 LLM 配置成功",
        data=updated_llm_config.model_dump(exclude={"api_key"})
    )

@router.get(
    path="/agent",
    response_model=None,
    summary="获取 Agent 配置信息",
    description="包含 Agent 的最大迭代次数、最大重试次数、最大搜索结果数"
)
async def get_agent_config(
    app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[AgentConfig]:
    agent_config = app_config_service.get_agent_config()
    return Response.success(data=agent_config.model_dump())

@router.post(
    path="/agent",
    response_model=None,
    summary="更新 Agent 配置信息",
    description="更新 Agent 配置信息"
)
async def update_agent_config(
    new_agent_config: AgentConfig,
    app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[AgentConfig]:
    updated_agent_config = app_config_service.update_agent_config(new_agent_config)
    return Response.success(
        msg="更新 Agent 配置成功",
        data=updated_agent_config.model_dump()
    )