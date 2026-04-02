"""上下文预算管理器

基于长上下文退化研究，主动管理 token 预算，防止 LLM 性能衰减。

核心设计依据:
- arXiv 2601.15300: 在 128K 上下文中，43.2% 处出现性能断崖
- 39% 平均退化（15 个 SOTA 模型测试）
- 安全策略: 保持工作上下文在模型最大值的 40% 以下

五层防御:
1. 预防 — 主动预算分配
2. 监控 — 实时用量追踪
3. 压缩 — 超阈值时压缩
4. 恢复 — 会话交接
5. 架构 — 多 agent 隔离
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from lingflow.compression.token_estimator import TokenEstimator

logger = logging.getLogger(__name__)


class BudgetLevel(Enum):
    """预算级别"""
    SAFE = "safe"           # < 30% — 完全安全
    MODERATE = "moderate"    # 30-40% — 接近断崖点
    WARNING = "warning"      # 40-60% — 已过断崖点，需要压缩
    CRITICAL = "critical"    # 60-80% — 严重退化，立即行动
    EMERGENCY = "emergency"  # > 80% — 必须交接


@dataclass
class BudgetStatus:
    """预算状态"""
    level: BudgetLevel
    current_tokens: int
    max_tokens: int
    usage_ratio: float
    safety_ratio: float
    recommended_action: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "usage_ratio": f"{self.usage_ratio:.1%}",
            "safety_ratio": f"{self.safety_ratio:.1%}",
            "recommended_action": self.recommended_action,
            "details": self.details,
        }


class ContextBudgetManager:
    """上下文预算管理器

    主动管理 token 预算，防止长上下文退化。

    基于 40% 安全线:
    - 低于 40%: 安全工作区
    - 40-60%: 需要压缩
    - 60-80%: 严重退化，需要立即压缩
    - > 80%: 必须进行会话交接
    """

    DEFAULT_SAFETY_RATIO = 0.4
    WARNING_RATIO = 0.4
    CRITICAL_RATIO = 0.6
    EMERGENCY_RATIO = 0.8

    def __init__(
        self,
        max_tokens: int = 180000,
        safety_ratio: float = 0.4,
        agent_context_limit: Optional[int] = None,
    ):
        """初始化预算管理器

        Args:
            max_tokens: 模型最大 token 数
            safety_ratio: 安全使用比例（默认 0.4，基于退化研究）
            agent_context_limit: 单 agent 上下文限制（如 8000）
        """
        self.max_tokens = max_tokens
        self.safety_ratio = safety_ratio
        self.agent_context_limit = agent_context_limit
        self._token_estimator = TokenEstimator()

    @property
    def safe_budget(self) -> int:
        """安全预算（token 数）"""
        return int(self.max_tokens * self.safety_ratio)

    @property
    def warning_budget(self) -> int:
        """警告预算"""
        return int(self.max_tokens * self.WARNING_RATIO)

    @property
    def critical_budget(self) -> int:
        """临界预算"""
        return int(self.max_tokens * self.CRITICAL_RATIO)

    @property
    def emergency_budget(self) -> int:
        """紧急预算"""
        return int(self.max_tokens * self.EMERGENCY_RATIO)

    def check_budget(self, current_tokens: int) -> BudgetStatus:
        """检查当前预算状态

        Args:
            current_tokens: 当前使用的 token 数

        Returns:
            预算状态
        """
        ratio = current_tokens / self.max_tokens if self.max_tokens > 0 else 0.0

        if ratio >= self.EMERGENCY_RATIO:
            level = BudgetLevel.EMERGENCY
            action = "handoff"
            message = (
                f"Token 使用率 {ratio:.1%} 超过紧急阈值 {self.EMERGENCY_RATIO:.0%}，"
                "必须进行会话交接"
            )
        elif ratio >= self.CRITICAL_RATIO:
            level = BudgetLevel.CRITICAL
            action = "compress_aggressive"
            message = (
                f"Token 使用率 {ratio:.1%} 超过临界阈值 {self.CRITICAL_RATIO:.0%}，"
                "LLM 性能已严重退化，需要立即激进压缩"
            )
        elif ratio >= self.WARNING_RATIO:
            level = BudgetLevel.WARNING
            action = "compress"
            message = (
                f"Token 使用率 {ratio:.1%} 超过安全阈值 {self.WARNING_RATIO:.0%}，"
                "建议压缩以防止性能退化"
            )
        elif ratio >= self.safety_ratio * 0.75:
            level = BudgetLevel.MODERATE
            action = "monitor"
            message = (
                f"Token 使用率 {ratio:.1%}，接近安全阈值，持续监控"
            )
        else:
            level = BudgetLevel.SAFE
            action = "none"
            message = f"Token 使用率 {ratio:.1%}，在安全范围内"

        return BudgetStatus(
            level=level,
            current_tokens=current_tokens,
            max_tokens=self.max_tokens,
            usage_ratio=ratio,
            safety_ratio=self.safety_ratio,
            recommended_action=action,
            details={"message": message},
        )

    def should_compact(self, current_tokens: int) -> bool:
        """是否需要压缩

        Args:
            current_tokens: 当前 token 数

        Returns:
            是否需要压缩
        """
        ratio = current_tokens / self.max_tokens if self.max_tokens > 0 else 0.0
        return ratio >= self.WARNING_RATIO

    def should_handoff(self, current_tokens: int) -> bool:
        """是否需要进行会话交接

        Args:
            current_tokens: 当前 token 数

        Returns:
            是否需要交接
        """
        ratio = current_tokens / self.max_tokens if self.max_tokens > 0 else 0.0
        return ratio >= self.EMERGENCY_RATIO

    def get_target_tokens(self, current_tokens: int) -> int:
        """获取压缩目标 token 数

        Args:
            current_tokens: 当前 token 数

        Returns:
            压缩目标
        """
        ratio = current_tokens / self.max_tokens if self.max_tokens > 0 else 0.0
        if ratio >= self.CRITICAL_RATIO:
            return int(self.max_tokens * self.safety_ratio * 0.6)
        elif ratio >= self.WARNING_RATIO:
            return int(self.max_tokens * self.safety_ratio * 0.8)
        return current_tokens

    def allocate_agent_budget(
        self,
        agent_name: str,
        agent_context_limit: Optional[int] = None,
        priority: int = 2,
    ) -> int:
        """为 agent 分配上下文预算

        Args:
            agent_name: agent 名称
            agent_context_limit: 该 agent 的上下文限制
            priority: 任务优先级 (0=CRITICAL, 1=HIGH, 2=NORMAL, 3=LOW)

        Returns:
            分配的 token 预算
        """
        limit = agent_context_limit or self.agent_context_limit or 8000
        priority_multipliers = {0: 1.5, 1: 1.2, 2: 1.0, 3: 0.7}
        multiplier = priority_multipliers.get(priority, 1.0)
        allocated = int(limit * multiplier)
        cap = int(self.max_tokens * self.safety_ratio)
        return min(allocated, cap)

    def estimate_text_tokens(self, text: str) -> int:
        """估算文本 token 数

        Args:
            text: 输入文本

        Returns:
            token 数量
        """
        return self._token_estimator.count_tokens(text)

    def get_status(self, current_tokens: int) -> Dict[str, Any]:
        """获取预算管理器状态

        Args:
            current_tokens: 当前 token 使用量

        Returns:
            状态字典
        """
        budget_status = self.check_budget(current_tokens)
        return {
            "budget_status": budget_status.to_dict(),
            "safe_budget": self.safe_budget,
            "warning_budget": self.warning_budget,
            "critical_budget": self.critical_budget,
            "emergency_budget": self.emergency_budget,
        }
