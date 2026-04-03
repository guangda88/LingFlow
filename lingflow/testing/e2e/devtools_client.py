"""Chrome DevTools MCP 客户端

轻量级包装器，用于调用 Chrome DevTools MCP 服务器。

使用示例:
    >>> from lingflow.testing.e2e import DevToolsClient
    >>> client = DevToolsClient()
    >>> await client.start()
    >>> result = await client.navigate("https://example.com")
"""

import subprocess
import asyncio
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class MCPResult:
    """MCP 调用结果"""

    success: bool
    data: Any = None
    error: Optional[str] = None


class DevToolsClient:
    """Chrome DevTools MCP 客户端

    通过 MCP 协议调用 chrome-devtools 服务器。

    注意: 需要先安装并启动 chrome-devtools MCP 服务器
    https://github.com/ModelContextProtocol/servers
    """

    def __init__(self, server_name: str = "chrome-devtools"):
        """初始化客户端

        Args:
            server_name: MCP 服务器名称
        """
        self.server_name = server_name
        self._process: Optional[subprocess.Popen] = None

    async def start(self) -> MCPResult:
        """启动浏览器（通过 MCP）

        Returns:
            启动结果
        """
        # 调用 MCP 服务器启动浏览器
        return await self._call_mcp("create_browser", {"headless": True})

    async def navigate(self, url: str) -> MCPResult:
        """导航到 URL

        Args:
            url: 目标 URL

        Returns:
            导航结果
        """
        return await self._call_mcp("navigate_to_url", {"url": url})

    async def screenshot(self, path: str = "/tmp/screenshot.png") -> MCPResult:
        """截图

        Args:
            path: 保存路径

        Returns:
            截图结果
        """
        return await self._call_mcp("capture_screenshot", {"path": path})

    async def get_console(self) -> MCPResult:
        """获取控制台消息

        Returns:
            控制台消息
        """
        return await self._call_mcp("get_console_messages")

    async def get_network(self) -> MCPResult:
        """获取网络日志

        Returns:
            网络日志
        """
        return await self._call_mcp("get_network_log")

    async def get_performance(self) -> MCPResult:
        """获取性能指标

        Returns:
            性能指标
        """
        return await self._call_mcp("get_performance_metrics")

    async def evaluate_js(self, script: str) -> MCPResult:
        """执行 JavaScript

        Args:
            script: JavaScript 代码

        Returns:
            执行结果
        """
        return await self._call_mcp("evaluate_js", {"expression": script})

    async def close(self) -> None:
        """关闭浏览器"""
        await self._call_mcp("close_browser")

    async def _call_mcp(self, tool: str, args: Optional[Dict[str, Any]] = None) -> MCPResult:
        """调用 MCP 工具

        Args:
            tool: 工具名称
            args: 参数

        Returns:
            调用结果
        """
        try:
            # 尝试使用 MCP SDK 调用
            # 检查是否安装了 mcp 包
            try:
                from mcp import Client
                from mcp.client.stdio import stdio_client

                # 使用 stdio 连接到 MCP 服务器
                async with stdio_client() as (read_stream, write_stream):
                    async with Client(read_stream, write_stream) as client:
                        # 调用工具
                        result = await client.call_tool(tool, args or {})

                        return MCPResult(success=True, data=result.content if hasattr(result, "content") else result)
            except ImportError:
                # MCP SDK 未安装，使用 subprocess 调用 MCP CLI
                return await self._call_mcp_via_cli(tool, args)

        except Exception as e:
            # MCP 调用失败，返回错误结果
            return MCPResult(success=False, error=str(e), data=None)

    async def _call_mcp_via_cli(self, tool: str, args: Optional[Dict[str, Any]] = None) -> MCPResult:
        """通过 CLI 调用 MCP 工具（后备方法）

        Args:
            tool: 工具名称
            args: 参数

        Returns:
            调用结果
        """
        try:
            # 构建 MCP CLI 命令
            import json

            cmd = ["mcp", "call", self.server_name, tool, json.dumps(args or {})]

            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return MCPResult(success=True, data=json.loads(stdout.decode()) if stdout else {})
            else:
                return MCPResult(success=False, error=stderr.decode(), data=None)

        except FileNotFoundError:
            # MCP CLI 不可用，返回错误
            return MCPResult(success=False, error="MCP CLI 不可用，请安装 Model Context Protocol CLI", data=None)
        except Exception as e:
            return MCPResult(success=False, error=str(e), data=None)


# 便捷函数
async def quick_test(url: str) -> Dict[str, Any]:
    """快速测试 URL

    Args:
        url: 测试 URL

    Returns:
        测试结果
    """
    client = DevToolsClient()
    await client.start()

    results = {}

    # 导航
    nav = await client.navigate(url)
    results["navigation"] = nav.success

    # 截图
    shot = await client.screenshot()
    results["screenshot"] = shot.success

    # 控制台
    console = await client.get_console()
    results["console"] = console.data

    # 性能
    perf = await client.get_performance()
    results["performance"] = perf.data

    await client.close()
    return results
