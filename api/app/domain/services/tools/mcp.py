"""
MCP客户端管理器的开发思路:
1.在Agent执行的过程中，有可能需要调用多次工具,
    但是因为MCP工具的每次获取都需要调用客户端会话的list_tools()方法,
    非常耗时, 所以需要我们缓存工具的参数信息, 只有在初始化的时候才调用一次,
    并且在销毁MCP客户端管理器的时候一并清除;
2.在前端UI交互中, 无论MCP服务是否启动, 都会显示工具列表信息,
    但是在Agent执行的过程中, 我们只会传递已启动的MCP服务,
    所以对于MCP客户端管理器来说, 可以根据接收的MCP配置的差异加载不同的服务器,
    而不是仅从配置文件中读取数据;
3.MCP客户端管理器会同时管理多个MCP服务, 有可能有stdio、sse、streamable_http等传输协议.
    需要根据传输协议的不同来创建客户端会话(ClientSession), 同时缓存会话;
4.另外有可能有一些环境变量是存储在我们整个系统中的, 在初始化MCP服务的时候，需要将传递进来的
    环境变量与系统的环境变量进行合并后传递给MCP服务;
5.使用AsyncExitStack异步上下文管理器来管理上下文，避免使用with多层嵌套;
6.MCPClientManager的初始化非常耗时, 所以需要有机制可以判断避免重复初始化;
7.由于config.yaml是直接暴露在项目中的, 所以在使用config.yaml进行初始化的时候必须二次校验;
8.同时缓存ClientSession+Tool-Schema, 一个是客户端会话, 一个是工具参数声明;
9.MCP客户端管理器在清除/停止使用的时候, 必须关闭异步上下文管理器、清除资源(ClientSession、Tool-Schema)、
    初始化标识等, 从而避免资源泄露;
"""

from contextlib import AbstractAsyncContextManager, AsyncExitStack
import logging
import os
from typing import Any, Dict, List, Optional
import httpx
from mcp import ClientSession, StdioServerParameters, Tool, stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client

from .base import BaseTool
from app.domain.models.app_config import MCPConfig, MCPServerConfig, MCPTransport
from app.domain.models.tool_result import ToolResult
from app.application.errors.exceptions import NotFoundError

logger = logging.getLogger(__name__)

class MCPClientManager:
    """MCP 客户端管理器"""

    def __init__(self, mcp_config: Optional[MCPConfig] = None) -> None:
        self._mcp_config: MCPConfig = mcp_config # mcp 配置信息
        self._exit_stack: AsyncExitStack = AsyncExitStack() # 异步上下文管理器
        self._clients: Dict[str, ClientSession] = {} # 缓存的客户端会话
        self._tools: Dict[str, List[Tool]] = {} # 缓存的 MCP 工具参数声明
        self._initialized: bool = False # 是否已经初始化

    @property
    def tools(self) -> Dict[str, List[Tool]]:
        return self._tools

    async def initilize(self) -> None:
        """真正的初始化，连接所有配置的 MCP 服务器"""
        if self._initialized:
            return

        try:
            logger.info(f"从 config.yaml 中加载了 {len(self._mcp_config.mcpServers)} 个 MCP 服务器")
            await self._connect_mcp_servers()
            self._initialized = True
            logging.info("MCP 客户端管理器加载成功")
        except Exception as e:
            logger.error(f"MCP 客户端管理器加载失败: {str(e)}")
            raise

    async def _connect_mcp_servers(self) -> None:
        """连接所有的 MCP 服务器"""
        for server_name, server_config in self._mcp_config.mcpServers.items():
            try:
                await self._connect_mcp_server(server_name, server_config)
            except Exception as e:
                logger.error(f"连接 MCP 服务器 [{server_name}] 出错: {str(e)}")
                continue

    async def _connect_mcp_server(self, server_name: str, server_config: MCPServerConfig) -> None:
        """连接单个 MCP 服务器"""
        try:
            transport = server_config.transport
            if transport == MCPTransport.STDIO:
                await self._connect_stdio_server(server_name, server_config)
            elif transport == MCPTransport.SSE:
                await self._connect_sse_server(server_name, server_config)
            elif transport == MCPTransport.STREAMABLE_HTTP:
                await self._connect_streamable_http_server(server_name, server_config)
            else:
                raise ValueError(f"MCP 服务 [{server_name}] 使用了不支持的传输协议: {transport}")
        except Exception as e:
            logger.error(f"连接 MCP 服务器 [{server_name}] 出错: {str(e)}")
            raise

    async def _connect_stdio_server(self, server_name: str, server_config: MCPServerConfig) -> None:
        command = server_config.command
        args = server_config.args
        env = server_config.env

        if not command:
            raise ValueError(f"连接 stdio-mcp 服务器需要配置 command 命令")
        
        server_parameters = StdioServerParameters(
            command=command,
            args=args,
            env={**os.environ, **env}
        )

        try:
            cm = AbstractAsyncContextManager(ClientSession(server_parameters))
            session = await self._new_session(server_name, cm)
            await self._cache_mcp_server_tools(server_name, session)
            
            logger.info(f"连接 stdio_mcp 服务成功: {server_name}")
        except Exception as e:
            logger.error(f"连接 stdio-mcp 服务器失败: {str(e)}")
            raise

    async def _connect_sse_server(self, server_name: str, server_config: MCPServerConfig) -> None:
        url = server_config.url
        if not url:
            raise ValueError(f"连接 sse-mcp 服务器需要配置 url")

        try:
            cm = sse_client(url=url, headers=server_config.headers)
            session = await self._new_session(server_name, cm)
            await self._cache_mcp_server_tools(server_name, session)
            
            logger.info(f"连接 sse-mcp 服务成功: {server_name}")
        except Exception as e:
            logger.error(f"连接 sse-mcp 服务器失败: {str(e)}")
            raise

    async def _connect_streamable_http_server(self, server_name: str, server_config: MCPServerConfig) -> None:
        url = server_config.url
        if not url:
            raise ValueError(f"连接 streamable-htt-mcp 服务器需要配置 url")

        try:
            cm = streamable_http_client(
                url=url,
                http_client=httpx.AsyncClient(headers=server_config.headers)
            )
            session = await self._new_session(server_name, cm)
            await self._cache_mcp_server_tools(server_name, session)
            
            logger.info(f"连接 streamable-htt-mcp 服务成功: {server_name}")
        except Exception as e:
            logger.error(f"连接 streamable-htt-mcp 服务器失败: {str(e)}")
            raise

    async def _new_session(self, server_name: str, cm: AbstractAsyncContextManager) -> ClientSession:
        # 使用异步上下文管理器创建传输协议
        read_stream, write_stream = None, None

        transport = await self._exit_stack.enter_async_context(cm=cm)
        if len(transport) == 3:
            read_stream, write_stream, _ = transport
        else:
            read_stream, write_stream = transport

        # 根据读取与写入流构建会话
        session: ClientSession = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream),
        )

        # 初始化 MCP 服务会话
        await session.initialize()
        
        # 缓存对应的 mcp 客户端
        self._clients[server_name] = session
        return session
    
    async def _cache_mcp_server_tools(self, server_name: str, session: ClientSession) -> None:
        try:
            tools_response = await session.list_tools()
            tools = tools_response.tools if tools_response else []
            self._tools[server_name] = tools
            logger.info(f"MCP 服务器 [{server_name}] 提供了 {len(tools)} 个工具")
        except Exception as e:
            logger.error(f"获取 MCP 服务器 [{server_name}] 工具列表失败: {str(e)}")
            self._tools[server_name] = []

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """获取所有 MCP 工具列表，返回 LLM 可以使用的工具参数声明并处理 MCP 的名字"""
        all_tools = []
        for server_name, tools in self._tools.items():
            for tool in tools:
                if server_name.startswith("mcp_"):
                    tool_name = f"{server_name}_{tool.name}"
                else:
                    tool_name = f"mcp_{server_name}_{tool.name}"
                tool_schema = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": f"[{server_name}] {tool.description or tool.name}",
                        "parameters": tool.inputSchema,
                    }
                }
                all_tools.append(tool_schema)

        return all_tools
    
    async def invoke(self, tool_name: str, arguments: Dict[str, Dict[str, Any]]) -> ToolResult:
        """调用指定的工具"""
        try:
            original_server_name = None
            original_tool_name = None

            for server_name in self._mcp_config.mcpServers.keys():
                expected_prefix = server_name if server_name.startswith("mcp_") else f"mcp_{server_name}"
                if tool_name.startswith(f"{expected_prefix}_"):
                    original_server_name = server_name
                    original_tool_name = tool_name[len(expected_prefix)+1:]
                    break
            
            if not original_server_name or not original_tool_name:
                raise NotFoundError(f"服务器解析 MCP 工具不存在: {tool_name}")
            
            session = self._clients.get(original_server_name)
            if not session:
                return ToolResult(success=False, message=f"MCP 服务器 [{original_server_name}] 未连接")
            
            result = await session.call_tool(original_tool_name, arguments)
            if result:
                content = []
                if hasattr(result, "content") and result.content:
                    for item in result.content:
                        if hasattr(item, "text"):
                            content.append(item.text)
                        else:
                            content.append(str(item))
                
                return ToolResult(success=True, message="工具执行成功", data="\n".join(content) if content else "工具执行成功")
            else:
                return ToolResult(success=True, message="工具执行成功")

        except Exception as e:
            logger.error(f"调用 MCP 工具 [{tool_name}] 失败: {str(e)}")
            return ToolResult(
                success=False,
                message=f"调用 MCP 工具 [{tool_name}] 失败: {str(e)}"
            )

    async def cleanup(self) -> None:
        """当退出 MCP 服务时，清除对应资源"""
        if not self._initialized:
            return

        try:
            await self._exit_stack.aclose()
            logger.info(f"清除 MCP 上下文管理器成功")
        except RuntimeError as e:
            if "Attempted to exit cancel scope in a different task" in str(e):
                logger.warning(f"清理MCP客户端管理器时遇到任务上下文切换警告（可忽略）: {str(e)}")
            else:
                logger.error(f"清理MCP客户端管理器失败: {str(e)}")
        except Exception as e:
            logger.error(f"清理 MCP 客户端管理器失败: {str(e)}")
        finally:
            self._clients.clear()
            self._tools.clear()
            self._initialized = False
            logger.info(f"清除 MCP 客户端管理器成功")

class MCPTool(BaseTool):
    """MCP 工具包，包含所有已配置 + 已启动的 MCP 工具"""
    name: str = "mcp"

    def __init__(self) -> None:
        """构造函数，完成 MCP 工具包的初始化"""
        super().__init__()
        self._initialized: bool = False
        self._tools =[]
        self._manager: MCPClientManager = None
    
    async def initialize(self, mcp_config: Optional[MCPConfig] = None) -> None:
        """初始化"""
        if self._initialized:
            return
        
        self._manager = MCPClientManager(mcp_config=mcp_config)
        await self._manager.initilize()
        self._tools = await self._manager.get_all_tools()
        self._initialized = True

    def get_tools(self) -> List[Dict[str, Any]]:
        return self._tools
    
    def has_tool(self, tool_name: str) -> bool:
        for tool in self._tools:
            if tool["function"]["name"] == tool_name:
                return True
        return False
    
    async def invoke(self, tool_name: str, **kwargs) -> ToolResult:
        return await self._manager.invoke(tool_name, kwargs)
    
    async def cleanup(self) -> None:
        if self._manager:
            await self._manager.cleanup()
