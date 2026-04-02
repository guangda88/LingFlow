"""LingFlow 代理协调器"""

import asyncio
import logging
import types
from typing import Any, Dict, List, Optional

from lingflow.common.models import AgentConfig, Task, TaskResult
from lingflow.compression.compressor import (
    ContextCompressor,
    CompressionLevel,
)
from lingflow.coordination.base import BaseCoordinator
from lingflow.coordination.registry import AgentRegistry
from lingflow.common.sandbox import SkillSandbox, SandboxError, SandboxTimeoutError
from lingflow.coordination.agent import Agent

logger = logging.getLogger(__name__)


class AgentCoordinator(BaseCoordinator):
    """简化的代理协调器"""

    def __init__(self, registry: Optional[AgentRegistry] = None):
        super().__init__()
        self.registry = registry or AgentRegistry()
        self.task_queue: List[Task] = []
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.failed_tasks: Dict[str, TaskResult] = {}
        # 启用高级上下文压缩功能
        self.compressor = ContextCompressor(
            target_tokens=4000,
            level=CompressionLevel.ADVANCED
        )
        self.sandbox = SkillSandbox(timeout=30.0, memory_limit=100 * 1024 * 1024)  # 100MB

        # 上下文预算管理（基于 40% 安全线防止长上下文退化）
        from lingflow.context.budget import ContextBudgetManager
        self._budget_manager = ContextBudgetManager(max_tokens=180000)

        self._register_default_agents()

    def _register_default_agents(self) -> None:
        """注册默认代理"""
        configs = [
            AgentConfig(
                name="implementation",
                description="Code implementation agent",
                capabilities=["code_generation", "testing", "documentation"],
            ),
            AgentConfig(
                name="review",
                description="Code review agent",
                capabilities=["code_review", "design_review", "security_check"],
            ),
            AgentConfig(
                name="testing",
                description="Testing agent",
                capabilities=["test_generation", "test_execution", "coverage_analysis"],
            ),
            AgentConfig(
                name="debugging",
                description="Debugging agent",
                capabilities=["error_analysis", "root_cause", "fix_generation"],
            ),
            AgentConfig(
                name="architecture",
                description="Architecture agent",
                capabilities=["system_design", "architecture_review", "api_design"],
            ),
            AgentConfig(
                name="documentation",
                description="Documentation agent",
                capabilities=["doc_generation", "api_doc_writing", "readme_generation"],
            ),
        ]

        for config in configs:
            self.registry.register_agent(Agent(config))

    def submit_task(self, task: Task) -> None:
        """Submit a task to the coordinator.

        Args:
            task: The task to submit
        """
        self.task_queue.append(task)

    async def execute_tasks_parallel(
        self, tasks: List[Task], max_parallel: int = 2
    ) -> Dict[str, TaskResult]:
        """Execute multiple tasks in parallel.

        Args:
            tasks: List of tasks to execute
            max_parallel: Maximum number of parallel executions

        Returns:
            Dictionary mapping task IDs to their results
        """
        results = {}
        semaphore = asyncio.Semaphore(max_parallel)

        # 并行执行所有任务
        tasks_to_execute = [
            asyncio.create_task(self._execute_one_task(task, semaphore))
            for task in tasks
        ]
        results_list = await asyncio.gather(*tasks_to_execute, return_exceptions=True)

        # 处理结果
        results = self._process_task_results(results_list)
        return results

    async def _execute_one_task(self, task: Task, semaphore: asyncio.Semaphore) -> TaskResult:
        """执行单个任务"""
        async with semaphore:
            # 查找代理
            agent = self._find_agent_for_task(task)
            if not agent:
                return self._create_error_result(task, "No suitable agent found")

            # 压缩上下文
            compressed_context = self._compress_context(task.context)

            # 执行任务
            result = await agent.execute_task(task, compressed_context)
            return result

    def _find_agent_for_task(self, task: Task) -> Optional["Agent"]:
        """查找适合任务的代理

        Args:
            task: 要执行的任务

        Returns:
            找到的代理，如果没有合适的则返回 None
        """
        """查找适合任务的代理"""
        agents = self.registry.find_agents_for_task(task)
        if not agents:
            logger.warning("No agent found for task %s", task.task_id)
            return None
        return agents[0]

    def _compress_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """压缩上下文 - 基于预算管理器的安全版本"""
        try:
            # 检查上下文预算
            import json
            context_str = json.dumps(context) if isinstance(context, dict) else str(context)
            context_tokens = self._budget_manager.estimate_text_tokens(context_str)
            budget_status = self._budget_manager.check_budget(context_tokens)

            if budget_status.level.value in ("critical", "emergency"):
                logger.warning(
                    "Context budget %.1f%% (%s), applying aggressive compression",
                    budget_status.usage_ratio * 100,
                    budget_status.level.value
                )

            return self.compressor.compress(context)
        except (ValueError, KeyError, TypeError) as e:
            logger.warning("Context compression failed: %s", e)
            return context
        except Exception as e:
            logger.error("Unexpected error during compression: %s", e)
            return context

    def _create_error_result(self, task: Task, error: str) -> TaskResult:
        """创建错误结果"""
        return TaskResult(task_id=task.task_id, success=False, error=error)

    def _process_task_results(self, results_list: List[TaskResult]) -> Dict[str, TaskResult]:
        """处理任务结果"""
        results = {}
        for result in results_list:
            if isinstance(result, Exception):
                logger.error("Exception in task result: %s", result)
                continue

            if result:
                results[result.task_id] = result

                if result.success:
                    self.completed_tasks[result.task_id] = result
                    logger.debug("Task %s completed successfully", result.task_id)
                else:
                    self.failed_tasks[result.task_id] = result
                    logger.warning("Task %s failed: %s", result.task_id, result.error)
        return results

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the coordinator.

        Returns:
            Dictionary containing status information including:
            - total_tasks: Total number of tasks
            - completed_tasks: Number of completed tasks
            - failed_tasks: Number of failed tasks
            - agents: Number of registered agents
            - compression_stats: Context compression statistics
        """
        return {
            "total_tasks": len(self.task_queue) + len(self.completed_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "agents": len(self.registry.agents),
            "compression_stats": self.compressor.get_stats(),
            "budget": self._budget_manager.get_status(0),
        }

    def reset(self) -> None:
        """Reset the coordinator state.

        Clears all task queues, completed tasks, and failed tasks.
        """
        self.task_queue.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()

    def execute_skill(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single skill with given parameters.

        Args:
            skill_name: Name of the skill to execute
            params: Parameters to pass to the skill

        Returns:
            Dictionary containing:
            - skill: Name of the executed skill
            - params: Parameters passed to the skill
            - result: Execution result (if successful)
            - error: Error message (if failed)
        """
        try:
            skill_path = self._get_skill_path(skill_name)
            if not skill_path:
                return {
                    "skill": skill_name,
                    "params": params,
                    "error": f"技能文件不存在: {skill_name}",
                }

            module = self._load_skill_module(skill_name, skill_path)
            if not module:
                return {
                    "skill": skill_name,
                    "params": params,
                    "error": f"加载技能模块失败: {skill_name}",
                }

            result = self._execute_skill_module(module, params)
            return {"skill": skill_name, "params": params, "result": result}
        except ImportError as e:
            return {"skill": skill_name, "params": params, "error": f"导入技能模块失败: {str(e)}"}
        except Exception as e:
            return {"skill": skill_name, "params": params, "error": f"执行技能时出错: {str(e)}"}

    def _get_skill_path(self, skill_name: str) -> Optional[str]:
        """获取技能文件路径（增强安全版本）

        Args:
            skill_name: 技能名称（只允许小写字母、数字、下划线和连字符）

        Returns:
            技能文件的绝对路径，如果验证失败则返回 None
        """
        """获取技能文件路径（增强安全版本）"""
        import os
        import re
        import pathlib

        # 严格验证技能名称
        if not skill_name:
            return None

        if not (3 <= len(skill_name) <= 50):
            logger.warning("Invalid skill name length: %s", skill_name)
            return None

        if not re.match(r"^[a-z0-9_-]+$", skill_name):
            logger.warning("Invalid skill name format: %s", skill_name)
            return None

        # 构建并验证路径
        skills_dir = pathlib.Path(os.getcwd()) / "skills"
        try:
            skills_dir = skills_dir.resolve()
        except Exception as e:
            logger.error("Failed to resolve skills directory: %s", e)
            return None

        skill_path = skills_dir / skill_name / "implementation.py"

        # 规范化路径并验证存在性
        try:
            skill_path = skill_path.resolve(strict=True)
        except FileNotFoundError:
            logger.warning("Skill file not found: %s", skill_path)
            return None
        except RuntimeError:
            logger.warning("Skill path resolution failed: %s", skill_path)
            return None

        # 确保路径在 skills 目录内（防止路径遍历攻击）
        try:
            skill_path.relative_to(skills_dir)
        except ValueError:
            logger.warning("Path traversal attempt detected: %s", skill_path)
            return None

        return str(skill_path)

    def _load_skill_module(
        self, skill_name: str, skill_path: str
    ) -> Optional[types.ModuleType]:
        """加载技能模块（使用沙箱安全验证）

        安全特性：
        - 使用进程隔离的沙箱环境验证技能代码
        - 限制技能代码的超时时间（默认30秒）
        - 限制技能代码的内存使用（默认100MB）
        - 模块白名单，只允许访问安全的模块
        - 验证技能代码不包含危险操作

        已实施的安全限制：
        - 进程隔离：技能代码验证在独立的进程中执行
        - 超时限制：防止无限循环和长时间运行
        - 内存限制：防止内存耗尽攻击
        - 代码验证：检查危险的导入和函数调用
        - 模块白名单：只允许访问 typing, dataclasses, datetime, math, time

        Args:
            skill_name: 技能名称
            skill_path: 技能文件路径

        Returns:
            加载的模块，失败时返回 None

        Raises:
            SkillLoadError: 加载失败时抛出
        """
        import importlib.util
        import types
        from lingflow.common.exceptions import SkillLoadError

        try:
            # 读取技能文件内容
            with open(skill_path, 'r', encoding='utf-8') as f:
                skill_code = f.read()

            # 验证代码安全性
            if not self.sandbox.validate_code(skill_code):
                raise SkillLoadError(f"Skill {skill_name} contains unsafe code")

            # 在沙箱中执行代码以验证语法和基本安全性
            try:
                self.sandbox.execute_code(skill_code)
            except SandboxTimeoutError as e:
                raise SkillLoadError(f"Skill {skill_name} execution timed out: {str(e)}")
            except SandboxError as err:
                raise SkillLoadError(f"Sandbox error loading skill {skill_name}: {str(err)}")

            # 使用 importlib 正常加载模块
            spec = importlib.util.spec_from_file_location(
                f"skills.{skill_name}.implementation", skill_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 验证必须的函数存在
            if not hasattr(module, "execute_skill"):
                raise SkillLoadError(f"Skill {skill_name} missing required execute_skill function")

            # 创建包装模块，确保 execute_skill 在沙箱中执行
            execute_func = module.execute_skill

            class SandboxModule(types.ModuleType):
                """沙箱模块包装器"""

                def __init__(self, name: str, sandbox: SkillSandbox, func: Any):
                    super().__init__(name)
                    self.sandbox = sandbox
                    self._execute_func = func

                def execute_skill(self, params: Dict[str, Any]) -> Dict[str, Any]:
                    """在沙箱中执行技能"""
                    return self.sandbox.execute(self._execute_func, params)

            # 创建并返回包装模块
            sandbox_module = SandboxModule(
                f"skills.{skill_name}.implementation",
                self.sandbox,
                execute_func
            )

            return sandbox_module

        except IOError as e:
            raise SkillLoadError(f"Failed to read skill file {skill_path}: {str(e)}")
        except SyntaxError as e:
            raise SkillLoadError(f"Syntax error in skill {skill_name}: {str(e)}")
        except Exception as e:
            raise SkillLoadError(f"Failed to load skill module {skill_name}: {str(e)}")

    def _execute_skill_module(self, module: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能模块"""
        if hasattr(module, "execute_skill"):
            return module.execute_skill(params)
        else:
            raise Exception("技能模块中没有 execute_skill 函数")

    def list_skills(self) -> List[str]:
        """List all available skills.

        Returns:
            List of skill names that can be executed
        """
        import os
        from pathlib import Path

        skills_dir = Path(os.getcwd()) / "skills"
        skills = []

        if not skills_dir.exists():
            return skills

        # 扫描所有包含 implementation.py 或 SKILL.md 的目录
        for item in skills_dir.iterdir():
            if not item.is_dir() or item.name.startswith('_'):
                continue

            impl_path = item / "implementation.py"
            skill_md = item / "SKILL.md"

            if impl_path.exists() or skill_md.exists():
                # 使用连字符格式作为技能名称
                skills.append(item.name)

        return sorted(skills)
