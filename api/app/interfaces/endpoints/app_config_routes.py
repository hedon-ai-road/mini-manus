import logging
from typing import Dict, Optional

from fastapi import APIRouter, Body, Depends

from app.application.services.app_config_service import AppConfigService
from app.interfaces.schemas.app_config import ListMCPServerResponse, ListA2AServerResponse
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
    response_model=Response[ListMCPServerResponse],
    summary="获取 MCP 服务器工具列表",
    description="获取当前系统的 MCP 服务器列表，包含 MCP 服务名字、工具列表、启用状态等。"
)
async def get_mcp_servers(
    app_config_service: AppConfigService = Depends(get_app_config_service)
) -> Response[ListMCPServerResponse]:
    """获取当前系统的 MCP 服务器工具列表"""
    mcp_servers = await app_config_service.get_mcp_servers()
    return Response.success(
        msg="获取 MCP 服务器列表成功",
        data=ListMCPServerResponse(mcp_servers=mcp_servers)
    )

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

@router.get(
    path="/a2a-servers",
    response_model=Response[ListA2AServerResponse],
    summary="获取a2a服务器列表",
    description="获取MoocManus项目中的所有已配置的a2a服务列表",
)
async def get_a2a_servers(
        app_config_service: AppConfigService = Depends(get_app_config_service),
) -> Response[ListA2AServerResponse]:
    """获取a2a服务列表"""
    a2a_servers = await app_config_service.get_a2a_servers()
    return Response.success(
        msg="获取a2a服务列表成功",
        data=ListA2AServerResponse(a2a_servers=a2a_servers)
    )


@router.post(
    path="/a2a-servers",
    response_model=Response[Optional[Dict]],
    summary="新增a2a服务器",
    description="为MoocManus项目新增a2a服务器",
)
async def create_a2a_server(
        base_url: str = Body(..., embed=True),
        app_config_service: AppConfigService = Depends(get_app_config_service),
) -> Response[Optional[Dict]]:
    """新增a2a服务器"""
    await app_config_service.create_a2a_server(base_url)
    return Response.success(msg="新增A2A服务配置成功")


@router.post(
    path="/a2a-servers/{a2a_id}/delete",
    response_model=Response[Optional[Dict]],
    summary="删除a2a服务器",
    description="根据A2A服务id标识删除指定的A2A服务"
)
async def delete_a2a_server(
        a2a_id: str,
        app_config_service: AppConfigService = Depends(get_app_config_service),
) -> Response[Optional[Dict]]:
    """删除a2a服务器"""
    await app_config_service.delete_a2a_server(a2a_id)
    return Response.success(msg="删除a2a服务器成功")


@router.post(
    path="/a2a-servers/{a2a_id}/enabled",
    response_model=Response[Optional[Dict]],
    summary="更新A2A服务的启用状态",
    description="启动or禁用A2A服务的状态",
)
async def set_a2a_server_enabled(
        a2a_id: str,
        enabled: bool = Body(..., embed=True),
        app_config_service: AppConfigService = Depends(get_app_config_service),
) -> Response[Optional[Dict]]:
    """更新A2A服务的启用状态"""
    await app_config_service.set_a2a_server_enabled(a2a_id, enabled)
    return Response.success(msg="更新a2a服务器启用状态成功")
