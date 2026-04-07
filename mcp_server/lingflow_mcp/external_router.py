"""External MCP Server Router

Manages connections to external MCP servers and proxies their tools
into the LingFlow MCP server's tool registry.

Supports three transport types:
- stdio: Launch local MCP server processes (e.g., npx packages)
- sse: Connect to remote MCP servers via Server-Sent Events
- streamable_http: Connect via HTTP Streamable transport (MCP spec)
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ExternalServerConfig:
    """Configuration for a single external MCP server

    Args:
        name: Unique identifier for the server
        transport: Transport type - "stdio", "sse", or "streamable_http"
        command: Command to launch (stdio only), e.g. "npx" or "uvx"
        args: Command arguments (stdio only), e.g. ["-y", "@anthropic/mcp-server-fetch"]
        url: Server URL (sse/streamable_http), e.g. "http://localhost:8080/sse"
        env: Additional environment variables
        enabled: Whether this server is active
        tool_prefix: Prefix prepended to imported tool names (default: server name)
    """

    name: str
    transport: str = "stdio"
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    enabled: bool = True
    tool_prefix: Optional[str] = None

    def __post_init__(self):
        if self.tool_prefix is None:
            self.tool_prefix = self.name
        if self.args is None:
            self.args = []
        if self.transport not in ("stdio", "sse", "streamable_http"):
            raise ValueError(f"Unsupported transport: {self.transport}")


class ExternalMCPRouter:
    """Routes tool calls to external MCP servers

    Manages client sessions to external MCP servers, discovers their tools,
    and provides proxy handlers that forward calls to the appropriate server.
    """

    def __init__(self):
        self._servers: Dict[str, ExternalServerConfig] = {}
        self._sessions: Dict[str, Any] = {}
        self._tool_to_server: Dict[str, str] = {}
        self._discovered_tools: Dict[str, Dict[str, Any]] = {}
        self._connected: Set[str] = set()

    def add_server(self, config: ExternalServerConfig):
        """Register an external server configuration"""
        self._servers[config.name] = config
        logger.info(f"Registered external MCP server: {config.name} ({config.transport})")

    def remove_server(self, name: str):
        """Remove a server and disconnect"""
        if name in self._servers:
            del self._servers[name]
            self._connected.discard(name)
            tools_to_remove = [t for t, s in self._tool_to_server.items() if s == name]
            for t in tools_to_remove:
                del self._tool_to_server[t]
                self._discovered_tools.pop(t, None)
            logger.info(f"Removed external MCP server: {name}")

    def get_servers(self) -> Dict[str, ExternalServerConfig]:
        """Return all registered server configs"""
        return dict(self._servers)

    async def discover_tools(self) -> Dict[str, Dict[str, Any]]:
        """Connect to all enabled servers and discover their tools

        Returns:
            Dict mapping prefixed tool names to their tool metadata
        """
        for name, config in self._servers.items():
            if not config.enabled:
                continue
            try:
                tools = await self._discover_server_tools(name, config)
                for tool_info in tools:
                    original_name = tool_info["name"]
                    prefixed_name = f"{config.tool_prefix}__{original_name}"
                    self._tool_to_server[prefixed_name] = name
                    self._discovered_tools[prefixed_name] = {
                        **tool_info,
                        "original_name": original_name,
                        "server_name": name,
                        "prefixed_name": prefixed_name,
                    }
                logger.info(
                    f"Discovered {len(tools)} tools from external server '{name}'"
                )
            except Exception as e:
                logger.warning(f"Failed to discover tools from '{name}': {e}")

        return dict(self._discovered_tools)

    async def _discover_server_tools(
        self, server_name: str, config: ExternalServerConfig
    ) -> List[Dict[str, Any]]:
        """Connect to a single server and list its tools"""
        async with self._connect(config) as (read_stream, write_stream):
            from mcp.client.session import ClientSession

            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                self._connected.add(server_name)
                return [
                    {
                        "name": t.name,
                        "description": t.description or "",
                        "input_schema": (
                            t.inputSchema
                            if hasattr(t, "inputSchema") and t.inputSchema
                            else {"type": "object", "properties": {}}
                        ),
                    }
                    for t in result.tools
                ]

    async def _connect(self, config: ExternalServerConfig) -> AsyncIterator[Tuple[Any, Any]]:
        """Create a connection context manager yielding (read_stream, write_stream)

        Normalizes the transport differences so callers always receive a
        consistent 2-tuple regardless of transport type.
        """
        if config.transport == "stdio":
            from mcp.client.stdio import stdio_client, StdioServerParameters

            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env,
            )
            async with stdio_client(server_params) as streams:
                yield streams[0], streams[1]
        elif config.transport == "sse":
            from mcp.client.sse import sse_client

            async with sse_client(url=config.url, headers=config.env) as (read_stream, write_stream):
                yield read_stream, write_stream
        elif config.transport == "streamable_http":
            from mcp.client.streamable_http import streamable_http_client

            async with streamable_http_client(url=config.url) as (
                read_stream,
                write_stream,
                _session_id_fn,
            ):
                yield read_stream, write_stream
        else:
            raise ValueError(f"Unsupported transport: {config.transport}")

    async def call_tool(
        self, prefixed_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Forward a tool call to the appropriate external server

        Args:
            prefixed_name: The prefixed tool name (server_prefix__original_name)
            arguments: Tool arguments

        Returns:
            Tool execution result as a dict
        """
        server_name = self._tool_to_server.get(prefixed_name)
        if not server_name:
            return {"success": False, "error": f"Unknown external tool: {prefixed_name}"}

        config = self._servers.get(server_name)
        if not config:
            return {"success": False, "error": f"Server not configured: {server_name}"}

        tool_meta = self._discovered_tools.get(prefixed_name, {})
        original_name = tool_meta.get("original_name", prefixed_name)

        try:
            async with self._connect(config) as (read_stream, write_stream):
                from mcp.client.session import ClientSession

                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(original_name, arguments)

                    text_parts = []
                    for content in result.content:
                        if hasattr(content, "text"):
                            text_parts.append(content.text)

                    raw = "\n".join(text_parts) if text_parts else ""

                    try:
                        parsed = json.loads(raw)
                        if isinstance(parsed, dict):
                            return parsed
                    except (json.JSONDecodeError, TypeError):
                        pass

                    return {
                        "success": True,
                        "server": server_name,
                        "tool": original_name,
                        "result": raw,
                    }

        except Exception as e:
            logger.error(f"External tool call failed [{prefixed_name}]: {e}")
            return {"success": False, "error": str(e), "tool": prefixed_name}

    def get_proxy_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return metadata for all discovered external tools

        Returns:
            Dict mapping prefixed tool names to their full metadata
        """
        return dict(self._discovered_tools)

    def is_external_tool(self, name: str) -> bool:
        """Check if a tool name belongs to an external server"""
        return name in self._tool_to_server

    def get_connected_servers(self) -> Set[str]:
        """Return names of servers that have been successfully connected"""
        return set(self._connected)

    def get_tool_count(self) -> int:
        """Return total number of discovered external tools"""
        return len(self._discovered_tools)


def load_external_servers_from_config(
    config_path: Optional[str] = None,
) -> List[ExternalServerConfig]:
    """Load external server configurations from a JSON file

    Args:
        config_path: Path to JSON config file. Defaults to
            LINGFLOW_EXTERNAL_SERVERS env var or
            ~/.lingflow/external_servers.json

    Returns:
        List of ExternalServerConfig instances
    """
    if config_path is None:
        config_path = os.getenv(
            "LINGFLOW_EXTERNAL_SERVERS",
            str(Path.home() / ".lingflow" / "external_servers.json"),
        )

    config_file = Path(config_path)
    if not config_file.exists():
        logger.debug(f"No external servers config at {config_path}")
        return []

    try:
        with open(config_file, "r") as f:
            data = json.load(f)

        servers = data.get("servers", [])
        configs = []
        for entry in servers:
            try:
                configs.append(ExternalServerConfig(**entry))
            except (TypeError, ValueError) as e:
                logger.warning(f"Invalid server config entry: {entry} - {e}")

        logger.info(f"Loaded {len(configs)} external server configs from {config_path}")
        return configs

    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load external servers config: {e}")
        return []


def create_default_config(config_path: Optional[str] = None) -> str:
    """Create a default external servers config file with examples

    Args:
        config_path: Path to write config. Defaults to
            ~/.lingflow/external_servers.json

    Returns:
        Path to the created config file
    """
    if config_path is None:
        config_dir = Path.home() / ".lingflow"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = str(config_dir / "external_servers.json")

    default_config = {
        "servers": [
            {
                "name": "fetch",
                "transport": "stdio",
                "command": "uvx",
                "args": ["mcp-server-fetch"],
                "enabled": False,
            },
            {
                "name": "filesystem",
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@anthropic/mcp-server-filesystem", "/tmp"],
                "enabled": False,
            },
            {
                "name": "remote-mcp",
                "transport": "streamable_http",
                "url": "http://localhost:8080/mcp",
                "enabled": False,
            },
        ]
    }

    with open(config_path, "w") as f:
        json.dump(default_config, f, indent=2)

    logger.info(f"Created default external servers config at {config_path}")
    return config_path
