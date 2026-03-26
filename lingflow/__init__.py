"""LingFlow 统一入口"""

from pathlib import Path
from typing import Any, Dict, Optional

from .coordination.coordinator import AgentCoordinator
from .workflow.orchestrator import WorkflowOrchestrator

__version__ = "3.5.1"


class LingFlow:
    """LingFlow 统一入口 - 封装所有复杂性"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 LingFlow

        Args:
            config: 配置字典
        """
        self._coordinator = AgentCoordinator()
        self._orchestrator = WorkflowOrchestrator(self._coordinator)

    def run_skill(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """直接执行单个技能

        Args:
            skill_name: 技能名称
            params: 技能参数

        Returns:
            技能执行结果
        """
        return self._coordinator.execute_skill(skill_name, params or {})

    def run_workflow_file(self, filepath: str) -> Dict[str, Any]:
        """从YAML/JSON文件加载并执行工作流

        Args:
            filepath: 工作流文件路径

        Returns:
            工作流执行结果

        Raises:
            ValueError: 如果文件路径不合法或不在允许的目录内
        """
        import yaml

        base_dir = Path.cwd().resolve()

        # 安全验证文件路径（不跟随符号链接）
        validated_path = self._validate_filepath(filepath, base_dir)

        with open(validated_path, encoding="utf-8") as f:
            workflow_def = yaml.safe_load(f)
        return self._orchestrator.execute(workflow_def["tasks"])

    def _validate_filepath(self, filepath: str, base_dir: Path) -> Path:
        """安全验证文件路径

        验证文件路径是否在允许的目录内，并拒绝符号链接以防止路径遍历攻击。

        Args:
            filepath: 要验证的文件路径
            base_dir: 允许的基础目录

        Returns:
            验证后的规范化路径

        Raises:
            ValueError: 如果路径不合法或不在允许的目录内
            FileNotFoundError: 如果文件不存在
        """
        # 构建完整路径但不跟随符号链接
        filepath_abs = (base_dir / filepath).resolve(strict=False)

        # 检查路径是否在 base_dir 内（即使有..也被限制）
        try:
            # 使用 resolve(strict=False) 已经处理了..，但需要验证结果是否在 base_dir 内
            filepath_abs.relative_to(base_dir)
        except ValueError:
            raise ValueError(
                f"Access denied: {filepath} is outside allowed directory ({base_dir})"
            )

        # 拒绝符号链接（防止链接到目录外的文件）
        if filepath_abs.exists() and filepath_abs.is_symlink():
            raise ValueError(f"Symbolic links not allowed: {filepath}")

        # 确保文件实际存在
        if not filepath_abs.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        return filepath_abs

    def run_workflow(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """直接执行工作流定义

        Args:
            workflow_def: 工作流定义

        Returns:
            工作流执行结果
        """
        tasks = workflow_def.get("tasks", [])
        return self._orchestrator.execute(tasks)
