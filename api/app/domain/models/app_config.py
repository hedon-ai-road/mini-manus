from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

class LLMConfig(BaseModel):
    """语言模型配置"""
    base_url: HttpUrl = "https://api.deepseek.com" # 基础 URL 地址
    api_key: str = ""  # API 密钥
    model_name: str = "deepseek-reasoner" # 推理模型如果传递了 tools 底层会自动切换为 chat 模型
    temperature: float = Field(default=0.7)  # 温度
    max_tokens: int = Field(default=8192, ge=0) # 最大输出 token 数

class AgentConfig(BaseModel):
    """Agent 通用配置"""
    max_iterations: int = Field(default=100, gt=0, lt=100) # 最大迭代次数
    max_retries: int = Field(default=3, gt=1, lt=10) # LLM/工具的最大重试次数
    max_search_results: int = Field(default=10, gt=1, lt=30) # 最大搜索结果数

class MCPTransport(str, Enum):
    """MCP 传输类型枚举"""
    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"

class MCPServerConfig(BaseModel):
    """单个 MCP 服务配置"""
    # 通用字段配置
    transport: MCPTransport = MCPTransport.STREAMABLE_HTTP # 传输协议
    enabled: bool = True # 是否开启
    description: Optional[str] = None # 描述
    env: Optional[Dict[str, Any]] = None # 环境变量

    # stdio 配置
    command: Optional[str] = None # 启动命令
    args: Optional[List[str]] = None # 启动命令参数

    # streamable_http 与 sse 配置
    url: Optional[str] = None # MCP 服务 url 地址
    headers: Optional[Dict[str, Any]] = None # headers 请求头信息

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_mcp_server_config(self):
        if self.transport in [MCPTransport.SSE, MCPTransport.STREAMABLE_HTTP]:
            if not self.url:
                raise ValueError("在 sse 或 streamable_http 传输协议中必须传递 url")
        if self.transport == MCPTransport.STDIO:
            if not self.command:
                raise ValueError("在 stdio 传输协议中必须传递 command")
        
        return self

class MCPConfig(BaseModel):
    """MCP 配置"""
    mcpServers: Dict[str, MCPServerConfig] = Field(default_factory=dict) # mcp 服务
    
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

class AppConfig(BaseModel):
    """应用配置信息，包含 Agent 配置、LLM 提供商、A2A 网络、MCP 服务配置等"""
    llm_config: LLMConfig
    agent_config: AgentConfig
    mcp_config: MCPConfig

    # Pydantic 配置，允许传递额外的字段初始化
    model_config = ConfigDict(extra="allow")
