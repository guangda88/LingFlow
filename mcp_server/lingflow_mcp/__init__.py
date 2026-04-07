"""LingFlow MCP Server

将 LingFlow 的工程流能力封装为 MCP (Model Context Protocol) 工具，
使 AI 助手（Claude Desktop、Cursor 等）可直接调用 LingFlow 功能。

作者: LingFlow Team
版本: 1.1.0
协议: MCP (Model Context Protocol)
"""

__version__ = "1.3.0"

from lingflow_mcp.server import LingFlowMCPServer, MCPServerConfig
from lingflow_mcp.tools import ToolRegistry
from lingflow_mcp.config import ServerConfig
from lingflow_mcp.external_router import (
    ExternalMCPRouter,
    ExternalServerConfig,
    load_external_servers_from_config,
    create_default_config,
)

__all__ = [
    "LingFlowMCPServer",
    "MCPServerConfig",
    "ToolRegistry",
    "ServerConfig",
    "ExternalMCPRouter",
    "ExternalServerConfig",
    "create_server",
    "create_default_config",
    "load_external_servers_from_config",
    "__version__",
]


def create_server(
    config: MCPServerConfig = None,
    server_config: ServerConfig = None
) -> LingFlowMCPServer:
    """创建 LingFlow MCP 服务器实例

    Args:
        config: MCP 服务器配置
        server_config: LingFlow 服务器配置

    Returns:
        LingFlowMCPServer 实例
    """
    return LingFlowMCPServer(config, server_config)
