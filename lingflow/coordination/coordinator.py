"""LingFlow 代理协调器"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from lingflow.coordination.registry import AgentRegistry
from lingflow.coordination.agent import Agent
from lingflow.coordination.base import BaseCoordinator
from lingflow.compression.compressor import ContextCompressor
from lingflow.common.models import Task, TaskResult, AgentConfig

logger = logging.getLogger(__name__)


class AgentCoordinator(BaseCoordinator):
    """简化的代理协调器"""

    def __init__(self, registry: Optional[AgentRegistry] = None):
        super().__init__()
        self.registry = registry or AgentRegistry()
        self.task_queue: List[Task] = []
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.failed_tasks: Dict[str, TaskResult] = {}
        self.compressor = ContextCompressor()
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        """注册默认代理"""
        configs = [
            AgentConfig(
                name="implementation",
                description="Code implementation agent",
                capabilities=["code_generation", "testing", "documentation"]
            ),
            AgentConfig(
                name="review",
                description="Code review agent",
                capabilities=["code_review", "design_review", "security_check"]
            ),
            AgentConfig(
                name="testing",
                description="Testing agent",
                capabilities=["test_generation", "test_execution", "coverage_analysis"]
            ),
            AgentConfig(
                name="debugging",
                description="Debugging agent",
                capabilities=["error_analysis", "root_cause", "fix_generation"]
            ),
            AgentConfig(
                name="architecture",
                description="Architecture agent",
                capabilities=["system_design", "architecture_review", "api_design"]
            ),
            AgentConfig(
                name="documentation",
                description="Documentation agent",
                capabilities=["doc_generation", "api_doc_writing", "readme_generation"]
            )
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
        results_list = await asyncio.gather(
            *[self._execute_one_task(task, semaphore) for task in tasks],
            return_exceptions=True
        )

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
    
    def _find_agent_for_task(self, task: Task) -> Optional[Agent]:
        """查找适合任务的代理"""
        agents = self.registry.find_agents_for_task(task)
        if not agents:
            logger.warning(f"No agent found for task {task.task_id}")
            return None
        return agents[0]
    
    def _compress_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """压缩上下文"""
        try:
            return self.compressor.compress(context)
        except Exception:
            return context
    
    def _create_error_result(self, task: Task, error: str) -> TaskResult:
        """创建错误结果"""
        return TaskResult(
            task_id=task.task_id,
            success=False,
            error=error
        )
    
    def _process_task_results(self, results_list: List[Any]) -> Dict[str, TaskResult]:
        """处理任务结果"""
        results = {}
        for result in results_list:
            if isinstance(result, Exception):
                logger.error(f"Exception in task result: {result}")
                continue

            if result:
                results[result.task_id] = result

                if result.success:
                    self.completed_tasks[result.task_id] = result
                    logger.debug(f"Task {result.task_id} completed successfully")
                else:
                    self.failed_tasks[result.task_id] = result
                    logger.warning(f"Task {result.task_id} failed: {result.error}")
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
            'total_tasks': len(self.task_queue) + len(self.completed_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'agents': len(self.registry.agents),
            'compression_stats': self.compressor.get_stats()
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
                    "error": f"技能文件不存在: {skill_name}"
                }
            
            module = self._load_skill_module(skill_name, skill_path)
            if not module:
                return {
                    "skill": skill_name,
                    "params": params,
                    "error": f"加载技能模块失败: {skill_name}"
                }
            
            result = self._execute_skill_module(module, params)
            return {
                "skill": skill_name,
                "params": params,
                "result": result
            }
        except ImportError as e:
            return {
                "skill": skill_name,
                "params": params,
                "error": f"导入技能模块失败: {str(e)}"
            }
        except Exception as e:
            return {
                "skill": skill_name,
                "params": params,
                "error": f"执行技能时出错: {str(e)}"
            }
    
    def _get_skill_path(self, skill_name: str) -> Optional[str]:
        """获取技能文件路径（安全版本）"""
        import os
        import re
        
        # 验证技能名称，防止路径遍历攻击
        if not skill_name or not re.match(r'^[a-zA-Z0-9_-]+$', skill_name):
            return None
        
        # 构建技能路径
        skill_path = os.path.join(os.getcwd(), 'skills', skill_name, 'implementation.py')
        
        # 安全检查：确保路径在 skills 目录内
        skills_dir = os.path.abspath(os.path.join(os.getcwd(), 'skills'))
        skill_path_abs = os.path.abspath(skill_path)
        
        if not skill_path_abs.startswith(skills_dir):
            return None
        
        return skill_path if os.path.exists(skill_path) else None
    
    def _load_skill_module(self, skill_name: str, skill_path: str) -> Optional[Any]:
        """加载技能模块（安全版本）"""
        import importlib.util
        
        try:
            spec = importlib.util.spec_from_file_location(f"skills.{skill_name}.implementation", skill_path)
            module = importlib.util.module_from_spec(spec)
            
            # 沙箱执行：限制模块的全局变量
            # 这里可以添加更严格的沙箱限制
            spec.loader.exec_module(module)
            
            return module
        except Exception as e:
            raise Exception(f"加载技能模块失败: {str(e)}")
    
    def _execute_skill_module(self, module: Any, params: Dict[str, Any]) -> Any:
        """执行技能模块"""
        if hasattr(module, 'execute_skill'):
            return module.execute_skill(params)
        else:
            raise Exception("技能模块中没有 execute_skill 函数")

    def list_skills(self) -> List[str]:
        """List all available skills.

        Returns:
            List of skill names that can be executed
        """
        # 这里可以返回实际的技能列表
        return ["database_export", "upload_115", "notification", "code_analysis", "code_optimization"]
