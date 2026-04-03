"""
LingFlow Phase 5: AI工具适配器

提供与各种AI代码分析工具（Semgrep、Ruff、Pylint等）的集成适配器。
"""

from typing import Dict, Any, Optional, List

from lingflow.self_optimizer.phase5.models import FeedbackSource
from lingflow.self_optimizer.phase5.adapters.base_adapter import AIToolAdapter
from lingflow.self_optimizer.phase5.adapters.semgrep_adapter import SemgrepAdapter
from lingflow.self_optimizer.phase5.adapters.ruff_adapter import RuffAdapter
from lingflow.self_optimizer.phase5.adapters.pylint_adapter import PylintAdapter

__all__ = [
    "AIToolAdapter",
    "SemgrepAdapter",
    "RuffAdapter",
    "PylintAdapter",
    "get_adapter",
    "get_available_adapters",
]


def get_adapter(source: FeedbackSource, config: Dict[str, Any] = None) -> Optional[AIToolAdapter]:
    """获取适配器实例

    Args:
        source: 反馈源类型
        config: 配置字典

    Returns:
        适配器实例，如果不支持则返回None
    """
    adapter_map = {
        FeedbackSource.SEMGREP: SemgrepAdapter,
        FeedbackSource.RUFF: RuffAdapter,
        FeedbackSource.PYLINT: PylintAdapter,
    }

    adapter_class = adapter_map.get(source)
    if adapter_class:
        return adapter_class(config)

    return None


def get_available_adapters(configs: Dict[FeedbackSource, Dict[str, Any]] = None) -> List[AIToolAdapter]:
    """获取所有可用的适配器

    Args:
        configs: 配置字典，键为反馈源，值为配置

    Returns:
        可用的适配器实例列表
    """

    configs = configs or {}
    adapters = []

    for source in FeedbackSource:
        if source == FeedbackSource.CUSTOM:
            continue

        config = configs.get(source, {})
        adapter = get_adapter(source, config)

        if adapter and adapter.check_available():
            adapters.append(adapter)

    return adapters
