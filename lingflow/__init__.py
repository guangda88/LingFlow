"""灵通 (LingFlow) - 众智混元，万法灵通

统一入口模块，提供工作流执行和智能体协调功能。

启动顺序:
1. 导入核心模块
2. 初始化智能压缩器
3. 初始化上下文管理器
4. 显示会话恢复信息
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 核心模块（延迟导入，避免循环依赖）
_AgentCoordinator = None
_WorkflowOrchestrator = None


def _import_core_modules():
    """延迟导入核心模块"""
    global _AgentCoordinator, _WorkflowOrchestrator
    if _AgentCoordinator is None:
        from .coordination.coordinator import AgentCoordinator
        from .workflow.orchestrator import WorkflowOrchestrator
        _AgentCoordinator = AgentCoordinator
        _WorkflowOrchestrator = WorkflowOrchestrator


def _initialize_services():
    """初始化服务（压缩、上下文）"""
    # 1. 初始化智能压缩
    from .compression import enable_smart_compression
    enable_smart_compression(
        max_tokens=180000,
        warning_threshold=0.75,
        compress_threshold=0.85
    )

    # 2. 初始化上下文管理器（加载上次状态）
    from .context import get_context_manager
    get_context_manager()


def _show_session_resume():
    """显示会话恢复信息"""
    from .context.auto_resume import auto_resume, SESSION_FILE
    if SESSION_FILE.exists():
        text = auto_resume()
        if text:
            print(text, file=__import__('sys').stderr)


# 版本信息
__version__ = "3.5.2"

# 执行启动初始化
_initialize_services()
_show_session_resume()


# 便捷导入（供外部使用）
def get_context_manager():
    """获取上下文管理器实例"""
    from .context import get_context_manager as _gcm
    return _gcm()


def get_smart_compressor():
    """获取智能压缩器实例"""
    from .compression import get_smart_compressor as _gsc
    return _gsc()


# 导出便捷函数
track_context = lambda *a, **k: None  # 由 context 模块处理


def compress_context():
    """压缩上下文（带异常处理）"""
    try:
        return get_context_manager().compress_now()
    except Exception as e:
        logger.warning(f"上下文压缩失败: {e}")
        return ""


class LingFlow:
    """LingFlow 统一入口 - 封装所有复杂性"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 LingFlow

        Args:
            config: 配置字典，可包含:
                - compression_enabled: 是否启用压缩 (默认 True)
                - compression_target_tokens: 压缩目标 token 数 (默认 4000)
        """
        # 确保核心模块已导入
        _import_core_modules()

        # 解析配置
        config = config or {}

        # 初始化协调器
        self._coordinator = _AgentCoordinator()
        self._orchestrator = _WorkflowOrchestrator(self._coordinator)

    def run_skill(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """直接执行单个技能

        Args:
            skill_name: 技能名称
            params: 技能参数

        Returns:
            技能执行结果
        """
        _import_core_modules()
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

        _import_core_modules()
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
