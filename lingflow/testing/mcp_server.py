#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 测试服务器
基于 Chrome DevTools MCP 的标准化接口模式
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

from .tool_definition import ToolDefinition, ToolRequest, ToolResponse, TestContext

logger = logging.getLogger(__name__)


class MCPServerStatus(str, Enum):
    """MCP 服务器状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    category: str
    read_only: bool


class MCPTestServer:
    """MCP 测试服务器 - 标准化测试接口

    基于 Chrome DevTools MCP 的服务器模式
    提供 Model Context Protocol 标准接口

    特性:
    - 标准化 MCP 协议
    - 工具注册和发现
    - 异步请求处理
    - 错误处理和恢复
    - 状态监控
    """

    def __init__(
        self,
        name: str = "LingFlow MCP Test Server",
        version: str = "1.0.0"
    ):
        """初始化 MCP 测试服务器

        Args:
            name: 服务器名称
            version: 服务器版本
        """
        self.name = name
        self.version = version
        self.status = MCPServerStatus.STOPPED
        self.tools: Dict[str, ToolDefinition] = {}
        self.handlers: Dict[str, Callable] = {}
        self.start_time: Optional[float] = None
        self.request_count = 0
        self.error_count = 0

        logger.info(f"🔌 MCPTestServer 初始化: {name} v{version}")

    def register_tool(
        self,
        tool: ToolDefinition,
        handler: Optional[Callable] = None
    ):
        """注册工具

        Args:
            tool: 工具定义
            handler: 自定义处理函数（可选）

        Example:
            >>> server = MCPTestServer()
            >>> server.register_tool(run_test_tool)
        """
        self.tools[tool.name] = tool
        self.handlers[tool.name] = handler or tool.handle

        logger.info(f"✓ 工具已注册: {tool.name}")

    def register_tools(
        self,
        tools: Dict[str, ToolDefinition]
    ):
        """批量注册工具

        Args:
            tools: 工具字典

        Example:
            >>> server = MCPTestServer()
            >>> server.register_tools(create_tool_registry())
        """
        for name, tool in tools.items():
            self.register_tool(tool)

        logger.info(f"✓ 已批量注册 {len(tools)} 个工具")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具

        Args:
            name: 工具名称

        Returns:
            工具定义，不存在返回 None
        """
        return self.tools.get(name)

    def list_tools(self) -> List[MCPTool]:
        """列出所有工具

        Returns:
            MCP 工具列表

        Example:
            >>> server = MCPTestServer()
            >>> server.register_tools(tool_registry)
            >>> tools = server.list_tools()
            >>> for tool in tools:
            ...     print(f"{tool.name}: {tool.description}")
        """
        mcp_tools = []

        for name, tool in self.tools.items():
            mcp_tool = MCPTool(
                name=tool.name,
                description=tool.description,
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "arguments": {"type": "object"}
                    }
                },
                category=tool.annotations.get("category", "general"),
                read_only=tool.annotations.get("read_only", True)
            )
            mcp_tools.append(mcp_tool)

        return mcp_tools

    async def start(self):
        """启动 MCP 服务器

        Example:
            >>> server = MCPTestServer()
            >>> await server.start()
        """
        if self.status == MCPServerStatus.RUNNING:
            logger.warning("服务器已在运行")
            return

        self.status = MCPServerStatus.STARTING
        logger.info(f"🚀 启动 MCP 服务器: {self.name}")

        # 模拟启动过程
        await asyncio.sleep(0.1)

        self.status = MCPServerStatus.RUNNING
        self.start_time = asyncio.get_event_loop().time()

        logger.info(f"✓ MCP 服务器已启动")

    async def stop(self):
        """停止 MCP 服务器

        Example:
            >>> server = MCPTestServer()
            >>> await server.stop()
        """
        if self.status != MCPServerStatus.RUNNING:
            logger.warning("服务器未运行")
            return

        self.status = MCPServerStatus.STOPPING
        logger.info(f"🛑 停止 MCP 服务器")

        # 模拟停止过程
        await asyncio.sleep(0.1)

        self.status = MCPServerStatus.STOPPED
        self.start_time = None

        logger.info(f"✓ MCP 服务器已停止")

    async def handle_tool_call(
        self,
        request: ToolRequest,
        context: Optional[TestContext] = None
    ) -> ToolResponse:
        """处理工具调用

        Args:
            request: 工具请求
            context: 测试上下文（可选）

        Returns:
            工具响应

        Example:
            >>> server = MCPTestServer()
            >>> await server.start()
            >>> request = ToolRequest(name="run_test", arguments={...})
            >>> response = await server.handle_tool_call(request)
            >>> print(response.success)
        """
        self.request_count += 1

        if self.status != MCPServerStatus.RUNNING:
            self.error_count += 1
            return ToolResponse(
                success=False,
                error="服务器未运行",
                execution_time=0.0
            )

        tool = self.get_tool(request.name)

        if not tool:
            self.error_count += 1
            return ToolResponse(
                success=False,
                error=f"工具不存在: {request.name}",
                execution_time=0.0
            )

        # 创建上下文
        if context is None:
            context = TestContext(
                test_name=f"mcp_call_{request.name}",
                test_id=f"req_{self.request_count}",
                temp_dir="/tmp/mcp",
                start_time=0.0
            )

        # 调用处理函数
        response = ToolResponse(success=False, execution_time=0.0)

        try:
            handler = self.handlers[request.name]
            await handler(request, response, context)
        except Exception as e:
            self.error_count += 1
            logger.error(f"工具调用错误: {request.name} - {e}")
            response.success = False
            response.error = str(e)

        return response

    async def handle_mcp_request(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理 MCP 协议请求

        Args:
            request: MCP 请求

        Returns:
            MCP 响应

        Example:
            >>> server = MCPTestServer()
            >>> await server.start()
            >>> request = {"method": "tools/list"}
            >>> response = await server.handle_mcp_request(request)
        """
        method = request.get("method", "")

        if method == "tools/list":
            tools = self.list_tools()
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "inputSchema": t.input_schema
                        }
                        for t in tools
                    ]
                }
            }

        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            tool_request = ToolRequest(
                name=tool_name,
                arguments=arguments
            )

            response = await self.handle_tool_call(tool_request)

            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "success": response.success,
                                "data": response.data,
                                "error": response.error,
                                "execution_time": response.execution_time
                            })
                        }
                    ]
                }
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"未知方法: {method}"
                }
            }

    def get_status(self) -> Dict[str, Any]:
        """获取服务器状态

        Returns:
            状态字典

        Example:
            >>> server = MCPTestServer()
            >>> status = server.get_status()
            >>> print(status["status"])
        """
        uptime = 0.0
        if self.start_time and self.status == MCPServerStatus.RUNNING:
            uptime = asyncio.get_event_loop().time() - self.start_time

        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "uptime": uptime,
            "tools_count": len(self.tools),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": (
                self.error_count / self.request_count
                if self.request_count > 0 else 0
            )
        }


# 示例使用

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from lingflow.testing.tool_definition import create_tool_registry

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("MCP 测试服务器示例")
    print("=" * 70)

    async def main():
        # 创建服务器
        server = MCPTestServer(
            name="LingFlow Test Server",
            version="1.0.0"
        )

        # 注册工具
        tools = create_tool_registry()
        server.register_tools(tools)

        print("\n" + "-" * 70)
        print("启动服务器:")
        print("-" * 70)

        await server.start()

        # 列出工具
        print("\n" + "-" * 70)
        print("可用工具:")
        print("-" * 70)

        mcp_tools = server.list_tools()
        for tool in mcp_tools:
            print(f"  - {tool.name}: {tool.description}")
            print(f"    类别: {tool.category}, 只读: {tool.read_only}")

        # 工具调用示例
        print("\n" + "-" * 70)
        print("工具调用示例:")
        print("-" * 70)

        # MCP 协议请求 - 列出工具
        request1 = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }

        response1 = await server.handle_mcp_request(request1)
        print(f"\n1. tools/list:")
        print(f"   工具数量: {len(response1['result']['tools'])}")

        # MCP 协议请求 - 调用工具
        request2 = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "analyze_code",
                "arguments": {
                    "code": "def foo(): pass"
                }
            }
        }

        response2 = await server.handle_mcp_request(request2)
        print(f"\n2. tools/call (analyze_code):")
        print(f"   成功: {response2['success']}")

        # 显示状态
        print("\n" + "-" * 70)
        print("服务器状态:")
        print("-" * 70)

        status = server.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")

        # 停止服务器
        print("\n" + "-" * 70)
        print("停止服务器:")
        print("-" * 70)

        await server.stop()

    asyncio.run(main())

    print("\n✅ MCP 测试服务器示例完成")
