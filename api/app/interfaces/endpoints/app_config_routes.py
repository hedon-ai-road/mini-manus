import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends

from app.application.services.app_config_service import AppConfigService
from app.interfaces.service_dependencies import get_app_config_service
from app.interfaces.schemas.base import Response
from app.domain.models.app_config import AgentConfig, LLMConfig, MCPConfig

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

@router.get(
    path="/mcp-servers",
    response_model=Response,
    summary="获取 MCP 服务器工具列表",
    description="获取当前系统的 MCP 服务器列表，包含 MCP 服务名字、工具列表、启用状态等。"
)
async def get_mcp_servers(
    app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[Any]:
    """获取当前系统的 MCP 服务器工具列表"""
    pass

@router.post(
    path="/mcp-servers",
    response_model=Response[Optional[Dict]],
    summary="新增 MCP 服务配置，支持传递一个或多个配置",
    description="传递 MCP 配置信息为系统新增 MCP 工具"
)
async def create_mcp_server(
    mcp_config: MCPConfig,
    app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[Optional[Dict]]:
    await app_config_service.update_and_create_mcp_servers(mcp_config)
    return Response.success(msg="新增 MCP 服务配置成功")

@router.post(
    path="/mcp-servers/{server_name}/delete",
    response_model=Response[Optional[Dict]],
    summary="删除 MCP 服务配置",
    description="根据传递的 MCP 服务名字删除指定的 MCP 服务"
)
async def delete_mcp_server(
    server_name: str,
    app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[Optional[Dict]]:
    await app_config_service.delete_mcp_server(server_name)
    return Response.success(msg="删除 MCP 服务配置成功")

@router.post(
    path="/mcp-servers/{server_name}/enabled",
    response_model=Response[Optional[Dict]],
    summary="更新 MCP 服务的启用状态",
    description="根据传递的 MCP 服务名字 + enbaled 更新启用状态"
)
async def set_mcp_server_enabled(
    server_name: str,
    enbaled: bool = Body(...),
    app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[Optional[Dict]]:
    await app_config_service.set_mcp_server_enabled(server_name, enbaled)
    return Response.success(msg="更新 MCP 服务启用状态成功")