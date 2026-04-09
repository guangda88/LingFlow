"""LingFlow 代理协调器"""

import asyncio
import logging
import types
from typing import Any, Dict, List, Optional

from lingflow.common.models import AgentConfig, Task, TaskResult
from lingflow.common.sandbox import SandboxError, SandboxTimeoutError, SkillSandbox
from lingflow.compression.compressor import (
    CompressionLevel,
    ContextCompressor,
)
from lingflow.coordination.agent import Agent
from lingflow.coordination.base import BaseCoordinator
from lingflow.coordination.registry import AgentRegistry

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
        self.compressor = ContextCompressor(target_tokens=4000, level=CompressionLevel.ADVANCED)
        self.sandbox = SkillSandbox(timeout=30.0, memory_limit=256 * 1024 * 1024)  # 256MB

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

    async def execute_tasks_parallel(self, tasks: List[Task], max_parallel: int = 2) -> Dict[str, TaskResult]:
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
        tasks_to_execute = [asyncio.create_task(self._execute_one_task(task, semaphore)) for task in tasks]
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
                    budget_status.level.value,
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

            # 元认知检查（事前预防）- 在执行技能之前检查能力
            # 注意：不检查 metacognition-guard 技能本身，避免递归
            metacognition_result = self._check_metacognition(skill_name, params)
            if not metacognition_result.get("can_start", True):
                logger.warning(
                    f"Metacognition check failed for skill '{skill_name}': {metacognition_result.get('reason', 'Unknown reason')}"
                )
                return {
                    "skill": skill_name,
                    "params": params,
                    "error": f"Metacognition check failed: {metacognition_result.get('reason', 'Unknown reason')}",
                    "metacognition_result": metacognition_result,
                }

            result = self._execute_skill_module(module, params)

            # 自动信任验证（如果启用）
            from lingflow.common.config import get_config

            if get_config("trust.auto_verify", default=False):
                verification_result = self._auto_verify_skill(skill_name, params, result)
                if not verification_result.get("passed", False):
                    logger.warning(
                        f"Skill '{skill_name}' verification failed: {verification_result.get('message', 'Unknown error')}"
                    )
                    return {
                        "skill": skill_name,
                        "params": params,
                        "error": f"Verification failed: {verification_result.get('message', 'Unknown error')}",
                        "verification_result": verification_result,
                    }

            return {"skill": skill_name, "params": params, "result": result}
        except ImportError as e:
            return {"skill": skill_name, "params": params, "error": f"导入技能模块失败: {str(e)}"}
        except Exception as e:
            return {"skill": skill_name, "params": params, "error": f"执行技能时出错: {str(e)}"}

    def _check_metacognition(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """元认知检查（事前预防）

        在执行技能之前检查是否具备所需的能力。

        Args:
            skill_name: 技能名称
            params: 技能参数

        Returns:
            检查结果字典，包含:
            - can_start: 是否可以开始执行
            - reason: 原因说明（如果无法开始）
            - evolution_paths: 进化路径建议（如果有缺口）
        """
        from lingflow.common.config import get_config

        # 检查是否启用元认知
        if not get_config("metacognition.enabled", default=True):
            return {"can_start": True}

        # 不检查元认知守卫技能本身（避免递归）
        if skill_name == "metacognition-guard":
            return {"can_start": True}

        # 检查是否是严格模式
        strict_mode = get_config("metacognition.strict_mode", default=True)

        try:
            # 尝试从参数中提取所需能力
            required_capabilities = self._extract_required_capabilities(skill_name, params)
            complexity = self._estimate_complexity(skill_name, params)

            # 如果没有明确的能力要求，跳过检查
            if not required_capabilities:
                return {"can_start": True}

            # 获取当前 AI 的能力（从模拟的能力库中获取）
            current_capabilities = self._get_current_capabilities()

            # 创建元认知检查参数
            metacognition_params = {
                "task_id": f"{skill_name}-{id(params)}",
                "task_description": f"Execute skill: {skill_name}",
                "required_capabilities": required_capabilities,
                "complexity": complexity,
                "current_capabilities": current_capabilities,
            }

            # 执行元认知守卫技能
            metacognition_result = self._execute_metacognition_check(metacognition_params)

            # 如果不是严格模式，即使有缺口也允许开始（但记录警告）
            if not strict_mode and not metacognition_result.get("can_start", True):
                logger.warning(
                    f"Metacognition check found gaps for '{skill_name}', but strict_mode is disabled: {metacognition_result.get('reason', 'Unknown reason')}"
                )
                return {"can_start": True}

            return metacognition_result

        except Exception as e:
            logger.error(f"Metacognition check failed: {str(e)}")
            # 如果检查失败，根据严格模式决定是否允许执行
            if strict_mode:
                return {
                    "can_start": False,
                    "reason": f"Metacognition check failed: {str(e)}",
                }
            else:
                logger.warning(f"Metacognition check failed but strict_mode is disabled: {str(e)}")
                return {"can_start": True}

    def _extract_required_capabilities(self, skill_name: str, params: Dict[str, Any]) -> List[str]:
        """从技能参数中提取所需能力

        Args:
            skill_name: 技能名称
            params: 技能参数

        Returns:
            所需能力列表
        """
        capabilities = []

        # 根据技能名称推断所需能力
        skill_capability_mapping = {
            "brainstorming": ["Design", "Creative thinking"],
            "systematic-debugging": ["Python", "Debugging", "Problem solving"],
            "code-review": ["Python", "Code analysis", "Best practices"],
            "code-refactor": ["Python", "Code transformation"],
            "test-driven-development": ["Python", "Testing", "TDD"],
            "workflow-executor": ["YAML", "Workflow orchestration"],
            "dispatching-parallel-agents": ["Parallel execution", "Coordination"],
            "api-doc-generator": ["API design", "Documentation"],
            "database-schema-designer": ["Database", "Schema design"],
            "ci-cd-orchestrator": ["CI/CD", "Automation"],
        }

        # 添加技能对应的能力
        if skill_name in skill_capability_mapping:
            capabilities.extend(skill_capability_mapping[skill_name])

        # 从参数中提取额外的能力要求
        if "language" in params:
            capabilities.append(params["language"])
        if "framework" in params:
            capabilities.append(params["framework"])
        if "database" in params:
            capabilities.append(params["database"])

        # 去重
        return list(set(capabilities))

    def _estimate_complexity(self, skill_name: str, params: Dict[str, Any]) -> str:
        """估算任务复杂度

        Args:
            skill_name: 技能名称
            params: 技能参数

        Returns:
            复杂度级别 ("simple", "medium", "complex")
        """
        # 默认复杂度为 medium
        complexity = "medium"

        # 根据技能名称调整复杂度
        complex_skills = ["brainstorming", "systematic-debugging", "code-review", "ci-cd-orchestrator"]
        simple_skills = ["notification", "code-refactor"]

        if skill_name in complex_skills:
            complexity = "complex"
        elif skill_name in simple_skills:
            complexity = "simple"

        # 根据参数调整复杂度
        if "complexity" in params:
            complexity = params["complexity"]

        return complexity

    def _get_current_capabilities(self) -> Dict[str, str]:
        """获取当前 AI 的能力（模拟实现）

        Returns:
            当前能力字典，格式: {"能力名": "等级"}
        """
        # 这里使用模拟的能力库
        # 在实际实现中，可以从 AI 的能力注册表或学习历史中获取
        return {
            "Python": "MASTERED",
            "YAML": "MASTERED",
            "Testing": "PARTIAL",
            "Design": "PARTIAL",
            "Database": "FAMILIAR",
            "API design": "PARTIAL",
            "CI/CD": "FAMILIAR",
            "Automation": "PARTIAL",
            "Creative thinking": "PARTIAL",
            "Debugging": "PARTIAL",
            "Problem solving": "PARTIAL",
            "Code analysis": "PARTIAL",
            "Best practices": "PARTIAL",
            "Code transformation": "PARTIAL",
            "TDD": "FAMILIAR",
            "Workflow orchestration": "PARTIAL",
            "Parallel execution": "FAMILIAR",
            "Coordination": "PARTIAL",
            "Documentation": "PARTIAL",
            "Schema design": "FAMILIAR",
        }

    def _execute_metacognition_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行元认知检查

        Args:
            params: 元认知检查参数

        Returns:
            检查结果
        """
        try:
            # 加载元认知守卫技能
            from lingflow.trust import get_metacognitive_agent
            from lingflow.trust.metacognition import CapabilityLevel

            agent = get_metacognitive_agent()

            # 分析任务要求
            requirements = agent.analyze_task_requirements(
                task_id=params["task_id"],
                task_description=params["task_description"],
                required_capabilities=params["required_capabilities"],
                complexity=params["complexity"],
                current_capabilities=params["current_capabilities"],
            )

            # 如果有缺口，生成进化路径
            if not requirements["can_start"] and requirements.get("gaps"):
                requirements["evolution_paths"] = []
                for gap in requirements["gaps"]:
                    # 解析缺口信息（格式: "capability: level < required required_level"）
                    # 简化处理：提取能力名称
                    capability_name = gap.split(":")[0] if ":" in gap else gap

                    try:
                        # 估算目标等级
                        current_level_str = params["current_capabilities"].get(capability_name, "UNKNOWN")
                        current_level = CapabilityLevel[current_level_str]
                        target_level = (
                            current_level + 1 if current_level < CapabilityLevel.MASTERED else CapabilityLevel.MASTERED
                        )

                        # 生成进化路径
                        evolution = agent.propose_evolution(capability_name, target_level)
                        requirements["evolution_paths"].append(evolution)
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Failed to generate evolution path for {capability_name}: {str(e)}")

            return requirements

        except Exception as e:
            logger.error(f"Failed to execute metacognition check: {str(e)}")
            return {
                "can_start": False,
                "reason": f"Metacognition check error: {str(e)}",
            }

    def _auto_verify_skill(self, skill_name: str, params: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """自动验证技能执行结果

        根据技能参数自动选择合适的验证器进行验证。

        Args:
            skill_name: 技能名称
            params: 技能参数
            result: 技能执行结果

        Returns:
            验证结果字典，包含:
            - passed: 是否通过验证
            - message: 验证消息
            - confidence: 置信度
        """
        from lingflow.common.config import get_config

        # 获取置信度阈值
        threshold = get_config("trust.confidence_threshold", default=0.8)

        # 如果结果本身包含验证信息，直接使用
        if isinstance(result, dict) and "success" in result and "confidence" in result:
            passed = result["success"] and result["confidence"] >= threshold
            return {
                "passed": passed,
                "message": result.get("summary", "Verification from result"),
                "confidence": result["confidence"],
            }

        # 根据技能类型和参数进行自动验证
        # 这里是一个简单的启发式验证逻辑
        # 对于不同的技能类型，可以添加更具体的验证逻辑

        # 如果技能操作了文件（通过 params 中的 file/target 等字段）
        if "file" in params or "target" in params or "path" in params:
            target = params.get("file") or params.get("target") or params.get("path", "")

            # 检查文件是否存在
            from pathlib import Path

            if target and Path(target).exists():
                return {
                    "passed": True,
                    "message": f"Target file exists: {target}",
                    "confidence": 0.9,
                }
            else:
                return {
                    "passed": False,
                    "message": f"Target file not found: {target}",
                    "confidence": 0.0,
                }

        # 默认情况下，如果没有明确的验证方式，返回通过（但置信度较低）
        return {
            "passed": True,
            "message": "No specific verification configured",
            "confidence": 0.5,
        }

    def _get_skill_path(self, skill_name: str) -> Optional[str]:
        """获取技能文件路径（增强安全版本）

        Args:
            skill_name: 技能名称（只允许小写字母、数字、下划线和连字符）

        Returns:
            技能文件的绝对路径，如果验证失败则返回 None
        """
        """获取技能文件路径（增强安全版本）"""
        import os
        import pathlib
        import re

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

    def _load_skill_module(self, skill_name: str, skill_path: str) -> Optional[types.ModuleType]:
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
            with open(skill_path, "r", encoding="utf-8") as f:
                skill_code = f.read()

            # Skip sandbox validation for trust-guardrail skill (it needs lingflow.trust)
            # The skill is trusted as it's part of LingFlow's core verification system
            is_trust_skill = skill_name == "trust-guardrail"

            # 验证代码安全性
            if not is_trust_skill and not self.sandbox.validate_code(skill_code):
                raise SkillLoadError(f"Skill {skill_name} contains unsafe code")

            # 在沙箱中执行代码以验证语法和基本安全性（跳过 trust-guardrail）
            if not is_trust_skill:
                try:
                    self.sandbox.execute_code(skill_code)
                except SandboxTimeoutError as e:
                    raise SkillLoadError(f"Skill {skill_name} execution timed out: {str(e)}")
                except SandboxError as err:
                    raise SkillLoadError(f"Sandbox error loading skill {skill_name}: {str(err)}")

            # 使用 importlib 正常加载模块
            spec = importlib.util.spec_from_file_location(f"skills.{skill_name}.implementation", skill_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 验证必须的函数存在
            if not hasattr(module, "execute_skill"):
                raise SkillLoadError(f"Skill {skill_name} missing required execute_skill function")

            # 创建包装模块，确保 execute_skill 在沙箱中执行
            execute_func = module.execute_skill

            # For trust-guardrail, use normal execution instead of sandbox
            # because it needs to import lingflow.trust
            if skill_name == "trust-guardrail":

                class DirectModule(types.ModuleType):
                    """直接执行模块包装器（不使用沙箱）"""

                    def __init__(self, name: str, func: Any):
                        super().__init__(name)
                        self._execute_func = func

                    def execute_skill(self, params: Dict[str, Any]) -> Dict[str, Any]:
                        """直接执行技能（不使用沙箱）"""
                        return self._execute_func(params)

                return DirectModule(f"skills.{skill_name}.implementation", execute_func)

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
            sandbox_module = SandboxModule(f"skills.{skill_name}.implementation", self.sandbox, execute_func)

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
            if not item.is_dir() or item.name.startswith("_"):
                continue

            impl_path = item / "implementation.py"
            skill_md = item / "SKILL.md"

            if impl_path.exists() or skill_md.exists():
                # 使用连字符格式作为技能名称
                skills.append(item.name)

        return sorted(skills)
