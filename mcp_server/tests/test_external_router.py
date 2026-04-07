"""Tests for ExternalMCPRouter and external server integration"""

import json
import pytest
from pathlib import Path

from lingflow_mcp.external_router import (
    ExternalMCPRouter,
    ExternalServerConfig,
    load_external_servers_from_config,
    create_default_config,
)


class TestExternalServerConfig:
    """Test ExternalServerConfig dataclass"""

    def test_stdio_config(self):
        cfg = ExternalServerConfig(
            name="fetch",
            transport="stdio",
            command="uvx",
            args=["mcp-server-fetch"],
        )
        assert cfg.name == "fetch"
        assert cfg.transport == "stdio"
        assert cfg.command == "uvx"
        assert cfg.args == ["mcp-server-fetch"]
        assert cfg.enabled is True
        assert cfg.tool_prefix == "fetch"

    def test_sse_config(self):
        cfg = ExternalServerConfig(
            name="remote",
            transport="sse",
            url="http://localhost:8080/sse",
        )
        assert cfg.url == "http://localhost:8080/sse"
        assert cfg.tool_prefix == "remote"

    def test_streamable_http_config(self):
        cfg = ExternalServerConfig(
            name="streamable",
            transport="streamable_http",
            url="http://localhost:8080/mcp",
        )
        assert cfg.transport == "streamable_http"
        assert cfg.url == "http://localhost:8080/mcp"
        assert cfg.tool_prefix == "streamable"

    def test_custom_prefix(self):
        cfg = ExternalServerConfig(
            name="my-server",
            tool_prefix="ms",
        )
        assert cfg.tool_prefix == "ms"

    def test_invalid_transport_raises(self):
        with pytest.raises(ValueError, match="Unsupported transport"):
            ExternalServerConfig(name="bad", transport="grpc")

    def test_defaults(self):
        cfg = ExternalServerConfig(name="test")
        assert cfg.args == []
        assert cfg.env is None
        assert cfg.enabled is True


class TestExternalMCPRouter:
    """Test ExternalMCPRouter core logic"""

    def test_add_server(self):
        router = ExternalMCPRouter()
        cfg = ExternalServerConfig(name="test", transport="stdio", command="echo")
        router.add_server(cfg)
        assert "test" in router.get_servers()

    def test_remove_server(self):
        router = ExternalMCPRouter()
        cfg = ExternalServerConfig(name="test", transport="stdio", command="echo")
        router.add_server(cfg)
        router.remove_server("test")
        assert "test" not in router.get_servers()

    def test_remove_server_cleans_tools(self):
        router = ExternalMCPRouter()
        cfg = ExternalServerConfig(name="srv", transport="stdio", command="echo")
        router.add_server(cfg)
        router._tool_to_server["srv__tool1"] = "srv"
        router._discovered_tools["srv__tool1"] = {"name": "tool1"}
        router.remove_server("srv")
        assert "srv__tool1" not in router._tool_to_server
        assert "srv__tool1" not in router._discovered_tools

    def test_is_external_tool(self):
        router = ExternalMCPRouter()
        router._tool_to_server["ext__fetch"] = "ext"
        assert router.is_external_tool("ext__fetch") is True
        assert router.is_external_tool("list_skills") is False

    def test_get_tool_count(self):
        router = ExternalMCPRouter()
        assert router.get_tool_count() == 0
        router._discovered_tools["a__x"] = {"name": "x"}
        router._discovered_tools["a__y"] = {"name": "y"}
        assert router.get_tool_count() == 2

    def test_get_proxy_tools(self):
        router = ExternalMCPRouter()
        router._discovered_tools["srv__tool1"] = {"name": "tool1", "server_name": "srv"}
        proxy_tools = router.get_proxy_tools()
        assert "srv__tool1" in proxy_tools
        assert proxy_tools["srv__tool1"]["server_name"] == "srv"

    def test_get_connected_servers(self):
        router = ExternalMCPRouter()
        assert router.get_connected_servers() == set()
        router._connected.add("srv1")
        router._connected.add("srv2")
        assert router.get_connected_servers() == {"srv1", "srv2"}

    @pytest.mark.asyncio
    async def test_discover_tools_handles_failure(self):
        """discover_tools should handle connection failures gracefully"""
        router = ExternalMCPRouter()
        cfg = ExternalServerConfig(
            name="bad",
            transport="stdio",
            command="nonexistent_command_xyz",
            enabled=True,
        )
        router.add_server(cfg)
        result = await router.discover_tools()
        assert isinstance(result, dict)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_discover_tools_skips_disabled(self):
        """Disabled servers should be skipped"""
        router = ExternalMCPRouter()
        cfg = ExternalServerConfig(
            name="disabled",
            transport="stdio",
            command="echo",
            enabled=False,
        )
        router.add_server(cfg)
        result = await router.discover_tools()
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self):
        """Unknown tool should return error"""
        router = ExternalMCPRouter()
        result = await router.call_tool("nonexistent__tool", {})
        assert result["success"] is False
        assert "Unknown external tool" in result["error"]

    @pytest.mark.asyncio
    async def test_call_tool_server_not_configured(self):
        """Tool mapped to missing server should return error"""
        router = ExternalMCPRouter()
        router._tool_to_server["x__y"] = "missing_server"
        result = await router.call_tool("x__y", {})
        assert result["success"] is False
        assert "Server not configured" in result["error"]


class TestLoadExternalServersConfig:
    """Test config file loading"""

    def test_load_nonexistent_file(self, tmp_path):
        configs = load_external_servers_from_config(str(tmp_path / "nosuch.json"))
        assert configs == []

    def test_load_valid_config(self, tmp_path):
        config_file = tmp_path / "servers.json"
        config_file.write_text(json.dumps({
            "servers": [
                {
                    "name": "fetch",
                    "transport": "stdio",
                    "command": "uvx",
                    "args": ["mcp-server-fetch"],
                },
                {
                    "name": "remote",
                    "transport": "sse",
                    "url": "http://localhost:9000/sse",
                },
            ]
        }))
        configs = load_external_servers_from_config(str(config_file))
        assert len(configs) == 2
        assert configs[0].name == "fetch"
        assert configs[1].name == "remote"

    def test_load_invalid_entry_skipped(self, tmp_path):
        config_file = tmp_path / "servers.json"
        config_file.write_text(json.dumps({
            "servers": [
                {"name": "good", "transport": "stdio", "command": "echo"},
                {"bad_entry": True},
            ]
        }))
        configs = load_external_servers_from_config(str(config_file))
        assert len(configs) == 1
        assert configs[0].name == "good"

    def test_load_invalid_json(self, tmp_path):
        config_file = tmp_path / "servers.json"
        config_file.write_text("not valid json{{{")
        configs = load_external_servers_from_config(str(config_file))
        assert configs == []


class TestCreateDefaultConfig:
    """Test default config creation"""

    def test_creates_file(self, tmp_path):
        path = str(tmp_path / "ext_servers.json")
        result = create_default_config(path)
        assert Path(result).exists()
        data = json.loads(Path(result).read_text())
        assert "servers" in data
        assert len(data["servers"]) == 3

    def test_default_has_fetch_example(self, tmp_path):
        path = str(tmp_path / "ext_servers.json")
        create_default_config(path)
        data = json.loads(Path(path).read_text())
        names = [s["name"] for s in data["servers"]]
        assert "fetch" in names
        assert "filesystem" in names
        assert "remote-mcp" in names

    def test_default_includes_streamable_http(self, tmp_path):
        path = str(tmp_path / "ext_servers.json")
        create_default_config(path)
        data = json.loads(Path(path).read_text())
        transports = [s["transport"] for s in data["servers"]]
        assert "streamable_http" in transports

    def test_default_examples_disabled(self, tmp_path):
        path = str(tmp_path / "ext_servers.json")
        create_default_config(path)
        data = json.loads(Path(path).read_text())
        for server in data["servers"]:
            assert server["enabled"] is False


class TestServerIntegration:
    """Test external router integration with LingFlowMCPServer"""

    def test_server_has_external_router(self):
        from lingflow_mcp import create_server

        srv = create_server()
        assert hasattr(srv, "external_router")
        assert srv.external_router is None

    @pytest.mark.asyncio
    async def test_initialize_external_servers_no_config(self):
        from lingflow_mcp import create_server

        srv = create_server()
        count = await srv.initialize_external_servers()
        assert count == 0
        assert srv.external_router is not None

    @pytest.mark.asyncio
    async def test_initialize_external_servers_disabled(self):
        from lingflow_mcp import create_server, MCPServerConfig

        cfg = MCPServerConfig(enable_external_servers=False)
        srv = create_server(config=cfg)
        count = await srv.initialize_external_servers()
        assert count == 0
        assert srv.external_router is None

    @pytest.mark.asyncio
    async def test_initialize_with_config_file(self, tmp_path):
        from lingflow_mcp import create_server, MCPServerConfig

        config_file = tmp_path / "servers.json"
        config_file.write_text(json.dumps({
            "servers": [
                {
                    "name": "fetch",
                    "transport": "stdio",
                    "command": "nonexistent_cmd",
                    "enabled": True,
                },
            ]
        }))

        cfg = MCPServerConfig(
            external_servers_path=str(config_file),
        )
        srv = create_server(config=cfg)
        count = await srv.initialize_external_servers()
        assert count == 0  # Command doesn't exist, so discovery fails

    def test_config_has_external_fields(self):
        from lingflow_mcp import MCPServerConfig

        cfg = MCPServerConfig()
        assert hasattr(cfg, "external_servers_path")
        assert hasattr(cfg, "enable_external_servers")
        assert cfg.enable_external_servers is True
        assert cfg.external_servers_path is None
