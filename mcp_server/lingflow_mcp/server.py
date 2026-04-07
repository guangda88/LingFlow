"""LingFlow MCP Server 主服务器

实现 MCP 协议的服务器，暴露 LingFlow 的核心功能为工具。
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None
    Tool = None
    TextContent = None

from lingflow_mcp.tools import ToolRegistry
from lingflow_mcp.config import ServerConfig
from lingflow_mcp.external_router import (
    ExternalMCPRouter,
    load_external_servers_from_config,
)

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP 服务器配置"""
    name: str = "lingflow-mcp-server"
    version: str = "1.0.0"
    lingflow_path: Optional[Path] = None
    max_workers: int = 3
    enable_async_tasks: bool = True
    external_servers_path: Optional[str] = None
    enable_external_servers: bool = True


class LingFlowMCPServer:
    """LingFlow MCP 服务器

    将 LingFlow 功能暴露为 MCP 工具，支持 AI 助手直接调用。
    """

    def __init__(
        self,
        config: Optional[MCPServerConfig] = None,
        server_config: Optional[ServerConfig] = None
    ):
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP SDK 未安装。请运行: pip install mcp"
            )

        self.config = config or MCPServerConfig()
        self.server_config = server_config or ServerConfig()

        # 初始化 LingFlow 核心
        self._init_lingflow()

        # 创建 MCP 服务器实例
        self.server = Server(self.config.name)

        # 工具注册表
        self.tool_registry = ToolRegistry()

        # 异步任务存储
        self._async_tasks: Dict[str, Dict[str, Any]] = {}

        # 注册所有工具
        self._register_tools()

        # 注册 Phase 3 工具
        self._register_phase3_tools()

        # 外部 MCP 服务器路由
        self.external_router: Optional[ExternalMCPRouter] = None

        # 注册处理器
        self._register_handlers()

        logger.info(
            f"LingFlow MCP Server 初始化完成: {self.config.name} "
            f"v{self.config.version}"
        )

    def _init_lingflow(self):
        """初始化 LingFlow 核心"""
        try:
            # 导入 LingFlow
            from lingflow import LingFlow
            from lingflow.workflow.multi_workflow import (
                MultiWorkflowCoordinator,
                WorkflowType,  # noqa: F401
            )
            from lingflow.core.skill import SkillRegistry

            # 初始化 LingFlow 实例
            self.lingflow = LingFlow()

            # 工作流协调器
            self.workflow_coordinator = MultiWorkflowCoordinator()

            # 技能注册表
            self.skill_registry = SkillRegistry()

            logger.info("LingFlow 核心初始化成功")

        except ImportError as e:
            logger.error(f"LingFlow 导入失败: {e}")
            raise

    def _register_tools(self):
        """注册所有工具"""
        # Phase 1: 高优先级工具
        self.tool_registry.register_skill_tools(self.skill_registry)
        self.tool_registry.register_intelligence_tools()
        self.tool_registry.register_code_review_tools()

        # Phase 2: 中优先级工具
        self.tool_registry.register_workflow_tools(self.workflow_coordinator)
        self.tool_registry.register_requirement_tools()

        # Phase 4: 文件操作与开发工具
        self.tool_registry.register_filesystem_and_dev_tools()

        logger.info(
            f"工具注册完成，共 {len(self.tool_registry.tools)} 个工具"
        )

    def _register_handlers(self):
        """注册 MCP 处理器"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """列出所有可用工具"""
            return self.tool_registry.get_mcp_tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """调用工具"""
            try:
                # 检查是否为异步任务查询
                if name == "get_task_status":
                    return await self._handle_async_task_status(arguments)

                # 执行工具
                result = await self._execute_tool(name, arguments)

                # 返回结果
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2)
                    )
                ]

            except Exception as e:
                logger.error(f"工具执行失败 {name}: {e}")
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, ensure_ascii=False)
                    )
                ]

        # 注册 get_task_status 工具
        self.tool_register_task_status_tools()

    async def _execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行工具

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            执行结果
        """
        tool_func = self.tool_registry.get_tool_handler(name)
        if not tool_func:
            raise ValueError(f"未知工具: {name}")

        # 检查是否为异步工具
        if self.tool_registry.is_async_tool(name):
            # 创建异步任务
            task_id = self._create_async_task(name, arguments)
            return {
                "success": True,
                "task_id": task_id,
                "status": "pending",
                "message": "任务已创建，请使用 get_task_status 查询状态"
            }

        # 同步执行
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**arguments)
        else:
            result = tool_func(**arguments)

        return result

    def _create_async_task(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> str:
        """创建异步任务

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            任务 ID
        """
        import uuid

        task_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"

        self._async_tasks[task_id] = {
            "tool_name": tool_name,
            "arguments": arguments,
            "status": "pending",
            "result": None,
            "error": None,
        }

        # 在后台执行任务
        asyncio.create_task(self._run_async_task(task_id))

        return task_id

    async def _run_async_task(self, task_id: str):
        """在后台运行异步任务"""
        task_info = self._async_tasks.get(task_id)
        if not task_info:
            return

        try:
            task_info["status"] = "running"

            tool_func = self.tool_registry.get_tool_handler(
                task_info["tool_name"]
            )

            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**task_info["arguments"])
            else:
                result = tool_func(**task_info["arguments"])

            task_info["status"] = "completed"
            task_info["result"] = result

        except Exception as e:
            task_info["status"] = "failed"
            task_info["error"] = str(e)
            logger.error(f"异步任务失败 {task_id}: {e}")

    async def _handle_async_task_status(
        self,
        arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """处理异步任务状态查询"""
        task_id = arguments.get("task_id")

        if not task_id:
            raise ValueError("缺少 task_id 参数")

        task_info = self._async_tasks.get(task_id)

        if not task_info:
            raise ValueError(f"任务不存在: {task_id}")

        # 返回任务状态
        result = {
            "task_id": task_id,
            "status": task_info["status"],
            "result": task_info.get("result"),
            "error": task_info.get("error"),
        }

        # 清理已完成的旧任务
        if task_info["status"] in ["completed", "failed"]:
            # 保留最近 100 个任务
            if len(self._async_tasks) > 100:
                self._cleanup_old_tasks()

        return [
            TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )
        ]

    def _cleanup_old_tasks(self):
        """清理旧任务"""
        # 保留最近 100 个任务
        sorted_tasks = sorted(
            self._async_tasks.items(),
            key=lambda x: x[0],
            reverse=True
        )

        self._async_tasks = dict(sorted_tasks[:100])

    def _register_phase3_tools(self):
        """注册 Phase 3 工具"""
        # 测试运行工具
        self.tool_registry.register_test_tools()

        # 运维监控工具
        self.tool_registry.register_monitoring_tools()

        logger.info("✅ Phase 3 工具注册完成")

    async def initialize_external_servers(self) -> int:
        """初始化外部 MCP 服务器连接并注册代理工具

        Returns:
            注册的外部工具数量
        """
        if not self.config.enable_external_servers:
            logger.info("外部 MCP 服务器已禁用")
            return 0

        self.external_router = ExternalMCPRouter()

        server_configs = load_external_servers_from_config(
            self.config.external_servers_path
        )

        for cfg in server_configs:
            self.external_router.add_server(cfg)

        if not self.external_router.get_servers():
            logger.info("未配置外部 MCP 服务器")
            return 0

        discovered = await self.external_router.discover_tools()

        for prefixed_name, tool_meta in discovered.items():
            self._register_proxy_tool(prefixed_name, tool_meta)

        count = len(discovered)
        if count > 0:
            logger.info(f"✅ 注册 {count} 个外部 MCP 工具")
        return count

    def _register_proxy_tool(
        self, prefixed_name: str, tool_meta: Dict[str, Any]
    ):
        """注册一个外部工具的代理 handler"""
        router = self.external_router

        async def proxy_handler(**kwargs) -> Dict[str, Any]:
            return await router.call_tool(prefixed_name, kwargs)

        proxy_handler.__name__ = f"proxy_{prefixed_name}"
        proxy_handler.__doc__ = (
            f"[External: {tool_meta.get('server_name', '?')}] "
            f"{tool_meta.get('description', '')}"
        )

        self.tool_registry.register(
            name=prefixed_name,
            description=proxy_handler.__doc__,
            handler=proxy_handler,
            input_schema=tool_meta.get(
                "input_schema", {"type": "object", "properties": {}}
            ),
        )

    def tool_register_task_status_tools(self):
        """注册异步任务状态查询工具"""

        async def get_task_status(
            task_id: str,
        ) -> Dict[str, Any]:
            """获取异步任务状态

            Args:
                task_id: 任务 ID

            Returns:
                任务状态信息
            """
            task_info = self._async_tasks.get(task_id)

            if not task_info:
                return {
                    "success": False,
                    "error": f"任务不存在: {task_id}",
                }

            return {
                "success": True,
                "task_id": task_id,
                "status": task_info["status"],
                "result": task_info.get("result"),
                "error": task_info.get("error"),
                "tool_name": task_info.get("tool_name"),
            }

        async def list_tasks(
            status_filter: Optional[str] = None,
        ) -> Dict[str, Any]:
            """列出所有异步任务

            Args:
                status_filter: 状态过滤（可选）

            Returns:
                任务列表
            """
            tasks = list(self._async_tasks.values())

            if status_filter:
                tasks = [t for t in tasks if t["status"] == status_filter]

            return {
                "success": True,
                "tasks": [
                    {
                        "task_id": task_id,
                        "tool_name": t["tool_name"],
                        "status": t["status"],
                    }
                    for task_id, t in self._async_tasks.items()
                    if not status_filter or t["status"] == status_filter
                ],
                "total": len(tasks),
            }

        self.tool_registry.register(
            name="get_task_status",
            description="查询异步任务的执行状态",
            handler=get_task_status,
            input_schema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID",
                    },
                },
                "required": ["task_id"],
            },
        )

        self.tool_registry.register(
            name="list_tasks",
            description="列出所有异步任务（支持状态过滤）",
            handler=list_tasks,
            input_schema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": ["pending", "running", "completed", "failed"],
                        "description": "状态过滤（可选）",
                    },
                },
            },
        )

    async def run(self, host: str = "localhost", port: int = 8000):
        """启动 MCP 服务器

        Args:
            host: 监听地址
            port: 监听端口
        """
        logger.info(f"启动 MCP 服务器: {host}:{port}")

        # 使用 stdio 传输（MCP 标准）
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def create_server(
    config: Optional[MCPServerConfig] = None,
    server_config: Optional[ServerConfig] = None
) -> LingFlowMCPServer:
    """创建 LingFlow MCP 服务器实例

    Args:
        config: MCP 服务器配置
        server_config: LingFlow 服务器配置

    Returns:
        LingFlowMCPServer 实例
    """
    return LingFlowMCPServer(config, server_config)
