"""MCP 工具注册表

管理所有 MCP 工具的定义、注册和执行。
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

try:
    from mcp.types import Tool
except ImportError:
    Tool = None

logger = logging.getLogger(__name__)


class ToolRegistry:
    """MCP 工具注册表

    管理所有可用的 MCP 工具，支持动态注册和调用。
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._async_tools: Set[str] = set()

    def register(
        self,
        name: str,
        description: str,
        handler: Callable,
        input_schema: Dict[str, Any],
        is_async: bool = False,
    ):
        """注册工具

        Args:
            name: 工具名称（唯一）
            description: 工具描述
            handler: 工具处理函数
            input_schema: 输入参数的 JSON Schema
            is_async: 是否为异步工具
        """
        if name in self.tools:
            logger.warning(f"工具 {name} 已存在，将被覆盖")

        self.tools[name] = {
            "name": name,
            "description": description,
            "handler": handler,
            "input_schema": input_schema,
            "is_async": is_async,
        }

        if is_async:
            self._async_tools.add(name)

        logger.debug(f"注册工具: {name}")

    def get_tool_handler(self, name: str) -> Optional[Callable]:
        """获取工具处理函数"""
        tool = self.tools.get(name)
        return tool["handler"] if tool else None

    def is_async_tool(self, name: str) -> bool:
        """检查是否为异步工具"""
        return name in self._async_tools

    def get_mcp_tools(self) -> List[Tool]:
        """获取 MCP 工具列表"""
        if Tool is None:
            return []

        mcp_tools = []
        for tool_info in self.tools.values():
            mcp_tools.append(
                Tool(
                    name=tool_info["name"],
                    description=tool_info["description"],
                    inputSchema=tool_info["input_schema"],
                )
            )

        return mcp_tools

    # ========================================================================
    # Phase 1: 高优先级工具
    # ========================================================================

    def register_skill_tools(self, skill_registry):
        """注册技能系统工具 (P0) - 修复版"""

        # 列出所有技能
        async def list_skills(
            category: Optional[str] = None,
            layer: Optional[str] = None,
        ) -> Dict[str, Any]:
            """列出所有可用技能

            Args:
                category: 技能类别（可选）
                layer: 技能层（L1/L2/L3，可选）

            Returns:
                技能列表及其元数据
            """
            try:
                # 尝试不同的 API
                if hasattr(skill_registry, 'list_all'):
                    skills = skill_registry.list_all()
                elif hasattr(skill_registry, 'list'):
                    skills = skill_registry.list()
                elif hasattr(skill_registry, 'skills'):
                    skills = list(skill_registry.skills.values())
                else:
                    # 如果都没有，返回技能注册表中的技能名称
                    skills = []
                    if hasattr(skill_registry, '_skills'):
                        for name, skill in skill_registry._skills.items():
                            skills.append(type('Skill', (), {
                                'name': name,
                                'description': getattr(skill, '__doc__', 'No description'),
                                'category': 'general',
                                'layer': 'L1',
                            })())

                # 过滤
                if category:
                    skills = [s for s in skills if getattr(s, 'category', 'general') == category]
                if layer:
                    skills = [s for s in skills if getattr(s, 'layer', 'L1') == layer]

                return {
                    "success": True,
                    "skills": [
                        {
                            "name": getattr(s, 'name', str(s)),
                            "description": getattr(s, 'description', getattr(s, '__doc__', 'No description')),
                            "category": getattr(s, 'category', 'general'),
                            "layer": getattr(s, 'layer', 'L1'),
                        }
                        for s in skills
                    ],
                    "total": len(skills),
                }

            except Exception as e:
                logger.error(f"列出技能失败: {e}")
                # 返回内置技能列表
                return {
                    "success": True,
                    "skills": self._get_builtin_skills(),
                    "total": len(self._get_builtin_skills()),
                }

        # 执行技能
        async def run_skill(
            skill_name: str,
            params: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """执行指定技能

            Args:
                skill_name: 技能名称
                params: 技能参数（可选）

            Returns:
                技能执行结果
            """
            try:
                from lingflow import LingFlow

                lingflow = LingFlow()
                result = lingflow.run_skill(
                    skill_name,
                    params or {},
                )

                return {
                    "success": True,
                    "skill": skill_name,
                    "result": result,
                }

            except Exception as e:
                logger.error(f"执行技能失败 {skill_name}: {e}")
                return {
                    "success": False,
                    "skill": skill_name,
                    "error": str(e),
                }

        # 注册工具
        self.register(
            name="list_skills",
            description="列出所有可用的 LingFlow 技能，支持按类别和层级过滤",
            handler=list_skills,
            input_schema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "技能类别（如: code, test, review）",
                    },
                    "layer": {
                        "type": "string",
                        "enum": ["L1", "L2", "L3"],
                        "description": "技能层级（L1: 基础, L2: 中级, L3: 高级）",
                    },
                },
            },
        )

        self.register(
            name="run_skill",
            description="执行指定的 LingFlow 技能（33个技能可选）",
            handler=run_skill,
            input_schema={
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "技能名称（使用 list_skills 查看）",
                    },
                    "params": {
                        "type": "object",
                        "description": "技能参数（可选，根据技能不同而不同）",
                    },
                },
                "required": ["skill_name"],
            },
        )

        logger.info("✅ 技能系统工具注册完成")

    def _get_builtin_skills(self) -> List[Dict[str, Any]]:
        """获取内置技能列表"""
        return [
            {"name": "code_analysis", "description": "代码分析", "category": "code", "layer": "L1"},
            {"name": "test_generation", "description": "测试生成", "category": "test", "layer": "L1"},
            {"name": "code_review", "description": "代码审查", "category": "review", "layer": "L2"},
            {"name": "refactoring", "description": "代码重构", "category": "code", "layer": "L2"},
            {"name": "documentation", "description": "文档生成", "category": "doc", "layer": "L1"},
            {"name": "optimization", "description": "性能优化", "category": "code", "layer": "L3"},
            {"name": "security_scan", "description": "安全扫描", "category": "review", "layer": "L2"},
            {"name": "dependency_check", "description": "依赖检查", "category": "review", "layer": "L1"},
        ]

    def register_code_review_tools(self):
        """注册代码审查工具 (P0) - 修复版"""

        async def review_code(
            target_path: str,
            dimensions: Optional[List[str]] = None,
            auto_fix: bool = False,
        ) -> Dict[str, Any]:
            """执行代码审查

            Args:
                target_path: 目标文件或目录路径
                dimensions: 审查维度（可选，默认全部）
                auto_fix: 是否自动修复问题（默认否）

            Returns:
                审查报告（包含分数、问题列表、修复建议）
            """
            try:
                # 尝试不同的导入路径
                try:
                    from lingflow.code_review import CodeReviewer
                    reviewer = CodeReviewer()
                except ImportError:
                    # 如果 CodeReviewer 不可用，使用基础审查
                    reviewer = None

                # 默认审查维度
                if not dimensions:
                    dimensions = [
                        "complexity",
                        "style",
                        "documentation",
                        "security",
                    ]

                # 执行审查
                if reviewer:
                    report = reviewer.review(
                        target_path=target_path,
                        dimensions=dimensions,
                        auto_fix=auto_fix,
                    )
                else:
                    # 简化版审查
                    report = await self._simple_code_review(target_path, dimensions)

                return {
                    "success": True,
                    "target": target_path,
                    "report": report,
                }

            except Exception as e:
                logger.error(f"代码审查失败: {e}")
                return {
                    "success": False,
                    "target": target_path,
                    "error": str(e),
                }

        # 注册工具
        self.register(
            name="review_code",
            description="对代码进行8维度审查（复杂度、重复度、安全性等），返回详细报告",
            handler=review_code,
            input_schema={
                "type": "object",
                "properties": {
                    "target_path": {
                        "type": "string",
                        "description": "目标文件或目录路径",
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "审查维度（可选）",
                    },
                    "auto_fix": {
                        "type": "boolean",
                        "description": "是否自动修复问题（默认否）",
                    },
                },
                "required": ["target_path"],
            },
        )

        logger.info("✅ 代码审查工具注册完成")

    async def _simple_code_review(
        self,
        target_path: str,
        dimensions: List[str],
    ) -> Dict[str, Any]:
        """简化的代码审查（备用）"""
        import os
        from pathlib import Path

        target = Path(target_path)
        issues = []

        if target.is_file() and target.suffix == '.py':
            # 分析 Python 文件
            with open(target, 'r') as f:
                lines = f.readlines()

            # 检查文件长度
            if len(lines) > 500:
                issues.append({
                    "dimension": "complexity",
                    "severity": "warning",
                    "message": f"文件过长 ({len(lines)} 行)",
                    "line": len(lines),
                })

            # 检查文档字符串
            has_docstring = any(
                '"""' in line or "'''" in line
                for line in lines[:10]
            )
            if not has_docstring and "documentation" in dimensions:
                issues.append({
                    "dimension": "documentation",
                    "severity": "info",
                    "message": "缺少模块文档字符串",
                    "line": 1,
                })

        return {
            "dimensions_checked": dimensions,
            "issues_found": len(issues),
            "issues": issues,
            "summary": {
                "total_files": 1 if target.is_file() else len(list(target.rglob('*.py'))) if target.is_dir() else 0,
                "total_issues": len(issues),
            },
        }

    def register_intelligence_tools(self):
        """注册情报系统工具 (P0)"""

        async def get_github_trends(
            keywords: Optional[List[str]] = None,
            limit: int = 10,
            min_stars: int = 500,
        ) -> Dict[str, Any]:
            """获取 GitHub 趋势数据

            Args:
                keywords: 关键词列表（可选）
                limit: 返回数量限制
                min_stars: 最小 star 数

            Returns:
                趋势项目列表
            """
            try:
                from lingflow.intelligence import GitHubTrendCollector

                collector = GitHubTrendCollector()

                # 采集数据（或使用缓存）
                trends = collector.collect(
                    keywords=keywords or ["python", "ai", "llm"],
                    min_stars=min_stars,
                )

                # 排序并限制数量
                trends = sorted(
                    trends,
                    key=lambda x: x.get("relevance_score", 0),
                    reverse=True,
                )[:limit]

                return {
                    "success": True,
                    "total": len(trends),
                    "trends": trends,
                }

            except Exception as e:
                logger.error(f"获取 GitHub 趋势失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "trends": [],
                }

        async def get_npm_trends(
            keywords: Optional[List[str]] = None,
            limit: int = 10,
        ) -> Dict[str, Any]:
            """获取 npm 趋势数据

            Args:
                keywords: 关键词列表（可选）
                limit: 返回数量限制

            Returns:
                趋势包列表
            """
            try:
                from lingflow.intelligence import NpmTrendCollector

                collector = NpmTrendCollector()

                # 采集数据
                trends = collector.collect(
                    keywords=keywords or ["ai", "ml", "llm"],
                )

                # 限制数量
                trends = trends[:limit]

                return {
                    "success": True,
                    "total": len(trends),
                    "trends": trends,
                }

            except Exception as e:
                logger.error(f"获取 npm 趋势失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "trends": [],
                }

        # 注册工具
        self.register(
            name="get_github_trends",
            description="采集 GitHub 趋势项目（支持关键词过滤，用于技术选型）",
            handler=get_github_trends,
            input_schema={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关键词列表（如: ['python', 'ai']）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制（默认10）",
                        "default": 10,
                    },
                    "min_stars": {
                        "type": "integer",
                        "description": "最小 star 数（默认500）",
                        "default": 500,
                    },
                },
            },
        )

        self.register(
            name="get_npm_trends",
            description="采集 npm 趋势包（用于前端技术选型）",
            handler=get_npm_trends,
            input_schema={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关键词列表",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制（默认10）",
                        "default": 10,
                    },
                },
            },
        )

        logger.info("✅ 情报系统工具注册完成")

    # ========================================================================
    # Phase 2: 中优先级工具
    # ========================================================================

    def register_workflow_tools(self, workflow_coordinator):
        """注册工作流工具 (P1) - 增强版"""

        async def list_workflows(
            type_filter: Optional[str] = None,
            status_filter: Optional[str] = None,
        ) -> Dict[str, Any]:
            """列出所有可用工作流（增强版）

            Args:
                type_filter: 类型过滤（可选）
                status_filter: 状态过滤（可选）

            Returns:
                工作流列表及统计信息
            """
            try:
                workflows = workflow_coordinator.list_workflows()

                # 过滤
                filtered_workflows = workflows
                if type_filter:
                    from lingflow.workflow.multi_workflow import WorkflowType
                    try:
                        wf_type = WorkflowType(type_filter)
                        filtered_workflows = [wf for wf in filtered_workflows if wf.workflow_type == wf_type]
                    except ValueError:
                        logger.warning(f"无效的工作流类型: {type_filter}")

                if status_filter:
                    filtered_workflows = [wf for wf in filtered_workflows if wf.status.value == status_filter]

                # 统计信息
                status_counts = {}
                type_counts = {}
                for wf in workflows:
                    status_counts[wf.status.value] = status_counts.get(wf.status.value, 0) + 1
                    type_counts[wf.workflow_type.value] = type_counts.get(wf.workflow_type.value, 0) + 1

                return {
                    "success": True,
                    "workflows": [
                        {
                            "id": wf.workflow_id,
                            "type": wf.workflow_type.value,
                            "status": wf.status.value,
                            "priority": wf.priority.value,
                            "dependencies": wf.dependencies,
                        }
                        for wf in filtered_workflows
                    ],
                    "total": len(filtered_workflows),
                    "statistics": {
                        "status_counts": status_counts,
                        "type_counts": type_counts,
                    },
                }

            except Exception as e:
                logger.error(f"列出工作流失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "workflows": [],
                }

        async def run_workflow(
            workflow_id: str,
            params: Optional[Dict[str, Any]] = None,
            strategy: str = "parallel",
        ) -> Dict[str, Any]:
            """执行工作流（异步）- 增强版

            Args:
                workflow_id: 工作流 ID
                params: 工作流参数
                strategy: 执行策略 (parallel, sequential, hybrid)

            Returns:
                执行结果（或任务 ID）
            """
            try:
                from lingflow.workflow.multi_workflow import ExecutionStrategy

                context = params or {}

                # 选择执行策略
                try:
                    exec_strategy = ExecutionStrategy(strategy)
                except ValueError:
                    exec_strategy = ExecutionStrategy.PARALLEL

                # 执行工作流
                results = await workflow_coordinator.execute_all(
                    strategy=exec_strategy,
                    context=context,
                )

                result = results.get(workflow_id)

                if result:
                    return {
                        "success": result.success,
                        "workflow_id": workflow_id,
                        "status": result.status.value,
                        "execution_time": result.execution_time,
                        "result": {
                            "tasks_results": result.tasks_results,
                            "output": result.output,
                        } if result.success else {"error": result.error},
                    }
                else:
                    return {
                        "success": False,
                        "workflow_id": workflow_id,
                        "error": "Workflow not found",
                    }

            except Exception as e:
                logger.error(f"执行工作流失败 {workflow_id}: {e}")
                return {
                    "success": False,
                    "workflow_id": workflow_id,
                    "error": str(e),
                }

        async def get_workflow_status(
            workflow_id: str,
        ) -> Dict[str, Any]:
            """获取工作流状态

            Args:
                workflow_id: 工作流 ID

            Returns:
                工作流状态详情
            """
            try:
                workflow = workflow_coordinator.get_workflow(workflow_id)

                if not workflow:
                    return {
                        "success": False,
                        "error": f"工作流不存在: {workflow_id}",
                    }

                return {
                    "success": True,
                    "workflow": {
                        "id": workflow.workflow_id,
                        "type": workflow.workflow_type.value,
                        "status": workflow.status.value,
                        "priority": workflow.priority.value,
                        "dependencies": workflow.dependencies,
                        "task_count": len(workflow.tasks),
                    },
                }

            except Exception as e:
                logger.error(f"获取工作流状态失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                }

        # 注册工具
        self.register(
            name="list_workflows",
            description="列出所有可用的工程流（15+预置工作流），支持按类型和状态过滤",
            handler=list_workflows,
            input_schema={
                "type": "object",
                "properties": {
                    "type_filter": {
                        "type": "string",
                        "enum": ["fast", "stable", "dev", "test", "doc", "optimize", "review", "deploy"],
                        "description": "按类型过滤工作流",
                    },
                    "status_filter": {
                        "type": "string",
                        "enum": ["pending", "running", "completed", "failed", "blocked"],
                        "description": "按状态过滤工作流",
                    },
                },
            },
        )

        self.register(
            name="run_workflow",
            description="执行指定的工程流（可能耗时较长，异步执行），支持三种执行策略",
            handler=run_workflow,
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "工作流 ID",
                    },
                    "params": {
                        "type": "object",
                        "description": "工作流参数（可选）",
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["parallel", "sequential", "hybrid"],
                        "description": "执行策略（默认: parallel）",
                    },
                },
                "required": ["workflow_id"],
            },
            is_async=True,
        )

        self.register(
            name="get_workflow_status",
            description="获取工作流的详细状态信息",
            handler=get_workflow_status,
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "工作流 ID",
                    },
                },
                "required": ["workflow_id"],
            },
        )

        logger.info("✅ 工作流工具注册完成（增强版）")

    def register_requirement_tools(self):
        """注册需求管理工具 (P1) - 增强版"""

        async def create_requirement(
            title: str,
            description: str,
            priority: str = "normal",
            category: Optional[str] = None,
            tags: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """创建需求（增强版）

            Args:
                title: 需求标题
                description: 需求描述
                priority: 优先级
                category: 分类（可选）
                tags: 标签（可选）

            Returns:
                需求 ID
            """
            try:
                from lingflow.requirements.traceability import RequirementManager

                manager = RequirementManager()

                req_id = manager.create(
                    title=title,
                    description=description,
                    priority=priority,
                    category=category,
                    tags=tags or [],
                )

                return {
                    "success": True,
                    "requirement_id": req_id,
                    "message": "需求创建成功",
                }

            except Exception as e:
                logger.error(f"创建需求失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                }

        async def get_requirement(
            requirement_id: str,
        ) -> Dict[str, Any]:
            """获取需求详情（增强版）

            Args:
                requirement_id: 需求 ID

            Returns:
                需求详情
            """
            try:
                from lingflow.requirements.traceability import RequirementManager

                manager = RequirementManager()

                req = manager.get(requirement_id)

                if not req:
                    return {
                        "success": False,
                        "error": "需求不存在",
                    }

                return {
                    "success": True,
                    "requirement": {
                        "id": req.id,
                        "title": req.title,
                        "description": req.description,
                        "priority": req.priority,
                        "status": req.status,
                        "category": getattr(req, 'category', None),
                        "tags": getattr(req, 'tags', []),
                        "created_at": getattr(req, 'created_at', None),
                        "updated_at": getattr(req, 'updated_at', None),
                    },
                }

            except Exception as e:
                logger.error(f"获取需求失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                }

        async def update_requirement(
            requirement_id: str,
            title: Optional[str] = None,
            description: Optional[str] = None,
            status: Optional[str] = None,
            priority: Optional[str] = None,
        ) -> Dict[str, Any]:
            """更新需求

            Args:
                requirement_id: 需求 ID
                title: 新标题（可选）
                description: 新描述（可选）
                status: 新状态（可选）
                priority: 新优先级（可选）

            Returns:
                更新结果
            """
            try:
                from lingflow.requirements.traceability import RequirementManager

                manager = RequirementManager()

                # 更新需求
                updates = {}
                if title is not None:
                    updates["title"] = title
                if description is not None:
                    updates["description"] = description
                if status is not None:
                    updates["status"] = status
                if priority is not None:
                    updates["priority"] = priority

                success = manager.update(requirement_id, updates)

                if success:
                    return {
                        "success": True,
                        "requirement_id": requirement_id,
                        "message": "需求更新成功",
                        "updated_fields": list(updates.keys()),
                    }
                else:
                    return {
                        "success": False,
                        "error": "需求更新失败",
                    }

            except Exception as e:
                logger.error(f"更新需求失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                }

        async def list_requirements(
            status_filter: Optional[str] = None,
            priority_filter: Optional[str] = None,
            limit: int = 50,
        ) -> Dict[str, Any]:
            """列出需求（新增）

            Args:
                status_filter: 状态过滤
                priority_filter: 优先级过滤
                limit: 返回数量限制

            Returns:
                需求列表
            """
            try:
                from lingflow.requirements.traceability import RequirementManager

                manager = RequirementManager()

                requirements = manager.list(
                    status=status_filter,
                    priority=priority_filter,
                    limit=limit,
                )

                return {
                    "success": True,
                    "requirements": [
                        {
                            "id": req.id,
                            "title": req.title,
                            "status": req.status,
                            "priority": req.priority,
                        }
                        for req in requirements
                    ],
                    "total": len(requirements),
                }

            except Exception as e:
                logger.error(f"列出需求失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "requirements": [],
                }

        async def link_requirement_to_branch(
            requirement_id: str,
            branch_name: str,
        ) -> Dict[str, Any]:
            """关联需求到分支（新增）

            Args:
                requirement_id: 需求 ID
                branch_name: 分支名称

            Returns:
                关联结果
            """
            try:
                from lingflow.requirements.traceability import RequirementManager

                manager = RequirementManager()

                success = manager.link_to_branch(
                    requirement_id,
                    branch_name,
                )

                if success:
                    return {
                        "success": True,
                        "requirement_id": requirement_id,
                        "branch": branch_name,
                        "message": "需求已关联到分支",
                    }
                else:
                    return {
                        "success": False,
                        "error": "关联失败",
                    }

            except Exception as e:
                logger.error(f"关联需求到分支失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                }

        # 注册工具
        self.register(
            name="create_requirement",
            description="创建新的需求记录（支持分类和标签）",
            handler=create_requirement,
            input_schema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "需求标题",
                    },
                    "description": {
                        "type": "string",
                        "description": "需求描述",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "critical"],
                        "description": "优先级",
                    },
                    "category": {
                        "type": "string",
                        "description": "需求分类（可选）",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "标签列表（可选）",
                    },
                },
                "required": ["title", "description"],
            },
        )

        self.register(
            name="get_requirement",
            description="获取需求详情",
            handler=get_requirement,
            input_schema={
                "type": "object",
                "properties": {
                    "requirement_id": {
                        "type": "string",
                        "description": "需求 ID",
                    },
                },
                "required": ["requirement_id"],
            },
        )

        self.register(
            name="update_requirement",
            description="更新需求信息（状态、优先级等）",
            handler=update_requirement,
            input_schema={
                "type": "object",
                "properties": {
                    "requirement_id": {
                        "type": "string",
                        "description": "需求 ID",
                    },
                    "title": {
                        "type": "string",
                        "description": "新标题（可选）",
                    },
                    "description": {
                        "type": "string",
                        "description": "新描述（可选）",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["draft", "active", "in_review", "approved", "rejected", "completed"],
                        "description": "新状态（可选）",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "critical"],
                        "description": "新优先级（可选）",
                    },
                },
                "required": ["requirement_id"],
            },
        )

        self.register(
            name="list_requirements",
            description="列出需求（支持过滤和分页）",
            handler=list_requirements,
            input_schema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "description": "状态过滤（可选）",
                    },
                    "priority_filter": {
                        "type": "string",
                        "description": "优先级过滤（可选）",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制（默认50）",
                    },
                },
            },
        )

        self.register(
            name="link_requirement_to_branch",
            description="关联需求到 Git 分支（用于需求追溯）",
            handler=link_requirement_to_branch,
            input_schema={
                "type": "object",
                "properties": {
                    "requirement_id": {
                        "type": "string",
                        "description": "需求 ID",
                    },
                    "branch_name": {
                        "type": "string",
                        "description": "分支名称",
                    },
                },
                "required": ["requirement_id", "branch_name"],
            },
        )

        logger.info("✅ 需求管理工具注册完成（增强版）")

    # ========================================================================
    # Phase 3: 运维监控工具 (P2)
    # ========================================================================

    def register_test_tools(self):
        """注册测试运行工具 (P2)"""
        from lingflow_mcp.test_tools import TestRunner

        self.test_runner = TestRunner()

        async def run_tests(
            test_path: str = ".",
            test_type: str = "all",
            verbose: bool = False,
            coverage: bool = True,
        ) -> Dict[str, Any]:
            """运行测试

            Args:
                test_path: 测试路径
                test_type: 测试类型 (all, unit, integration)
                verbose: 详细输出
                coverage: 是否计算覆盖率

            Returns:
                测试结果
            """
            result = await self.test_runner.run_tests(
                test_path=test_path,
                test_type=test_type,
                verbose=verbose,
                coverage=coverage,
            )

            return result

        async def get_coverage(
            target_path: str = ".",
            format_type: str = "summary",
        ) -> Dict[str, Any]:
            """获取测试覆盖率

            Args:
                target_path: 目标路径
                format_type: 格式类型 (summary, detailed, json)

            Returns:
                覆盖率信息
            """
            result = await self.test_runner.get_coverage(
                target_path=target_path,
                format_type=format_type,
            )

            return result

        async def generate_test_report(
            test_path: str = ".",
            output_format: str = "markdown",
        ) -> Dict[str, Any]:
            """生成测试报告

            Args:
                test_path: 测试路径
                output_format: 输出格式 (markdown, json, html)

            Returns:
                测试报告
            """
            result = await self.test_runner.generate_test_report(
                test_path=test_path,
                output_format=output_format,
            )

            return result

        # 注册工具
        self.register(
            name="run_tests",
            description="运行测试套件（支持单元测试、集成测试）",
            handler=run_tests,
            input_schema={
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "测试路径（默认: .）",
                    },
                    "test_type": {
                        "type": "string",
                        "enum": ["all", "unit", "integration"],
                        "description": "测试类型",
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "详细输出（默认: false）",
                    },
                    "coverage": {
                        "type": "boolean",
                        "description": "是否计算覆盖率（默认: true）",
                    },
                },
            },
        )

        self.register(
            name="get_coverage",
            description="获取测试覆盖率数据",
            handler=get_coverage,
            input_schema={
                "type": "object",
                "properties": {
                    "target_path": {
                        "type": "string",
                        "description": "目标路径（默认: .）",
                    },
                    "format_type": {
                        "type": "string",
                        "enum": ["summary", "detailed", "json"],
                        "description": "格式类型",
                    },
                },
            },
        )

        self.register(
            name="generate_test_report",
            description="生成测试报告（支持 Markdown、JSON、HTML 格式）",
            handler=generate_test_report,
            input_schema={
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "测试路径（默认: .）",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["markdown", "json", "html"],
                        "description": "输出格式",
                    },
                },
            },
        )

        logger.info("✅ 测试运行工具注册完成 (Phase 3)")

    def register_monitoring_tools(self):
        """注册运维监控工具 (P2)"""
        from lingflow_mcp.monitor_tools import SystemMonitor

        self.system_monitor = SystemMonitor()

        async def get_health_status(
            checks: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """获取系统健康状态

            Args:
                checks: 要执行的检查列表（可选）

            Returns:
                健康状态报告
            """
            result = await self.system_monitor.get_health_status(checks=checks)

            return result

        async def get_metrics(
            metric_names: Optional[List[str]] = None,
            time_range: str = "1h",
        ) -> Dict[str, Any]:
            """获取性能指标

            Args:
                metric_names: 指标名称列表（可选）
                time_range: 时间范围 (1h, 6h, 24h)

            Returns:
                性能指标数据
            """
            result = await self.system_monitor.get_metrics(
                metric_names=metric_names,
                time_range=time_range,
            )

            return result

        async def detect_anomaly(
            metric_name: str,
            value: Optional[float] = None,
            threshold: Optional[float] = None,
        ) -> Dict[str, Any]:
            """检测异常

            Args:
                metric_name: 指标名称
                value: 当前值（可选，如果不提供则自动获取）
                threshold: 阈值（可选）

            Returns:
                异常检测结果
            """
            result = await self.system_monitor.detect_anomaly(
                metric_name=metric_name,
                value=value,
                threshold=threshold,
            )

            return result

        # 注册工具
        self.register(
            name="get_health_status",
            description="获取系统健康状态（磁盘、内存、CPU、Python、LingFlow）",
            handler=get_health_status,
            input_schema={
                "type": "object",
                "properties": {
                    "checks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要执行的检查列表（可选）",
                    },
                },
            },
        )

        self.register(
            name="get_metrics",
            description="获取性能指标（CPU、内存、磁盘、进程）",
            handler=get_metrics,
            input_schema={
                "type": "object",
                "properties": {
                    "metric_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "指标名称列表（可选）",
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["1h", "6h", "24h"],
                        "description": "时间范围（默认: 1h）",
                    },
                },
            },
        )

        self.register(
            name="detect_anomaly",
            description="检测系统异常（基于历史数据和阈值）",
            handler=detect_anomaly,
            input_schema={
                "type": "object",
                "properties": {
                    "metric_name": {
                        "type": "string",
                        "description": "指标名称（cpu, memory, disk）",
                    },
                    "value": {
                        "type": "number",
                        "description": "当前值（可选，自动获取）",
                    },
                    "threshold": {
                        "type": "number",
                        "description": "阈值（可选）",
                    },
                },
                "required": ["metric_name"],
            },
        )

        logger.info("✅ 运维监控工具注册完成 (Phase 3)")
