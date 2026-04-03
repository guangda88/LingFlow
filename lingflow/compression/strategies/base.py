"""压缩策略基类和实现

定义不同的压缩策略。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CompressionTier(Enum):
    """压缩层级

    定义不同的压缩强度。
    """

    NONE = "none"  # 不压缩
    LIGHT = "light"  # 轻度压缩 (保留 80%)
    MEDIUM = "medium"  # 中度压缩 (保留 50%)
    AGGRESSIVE = "aggressive"  # 激进压缩 (保留 30%)
    EXTREME = "extreme"  # 极限压缩 (保留 10%)


@dataclass
class CompressionPlan:
    """压缩计划

    定义如何压缩消息列表。
    """

    target_tokens: int
    current_tokens: int
    tier: CompressionTier
    remove_system: bool = False
    keep_first_n: int = 0
    keep_last_n: int = 0
    score_threshold: float = 0.0

    @property
    def compression_ratio(self) -> float:
        """压缩比例"""
        if self.current_tokens == 0:
            return 0.0
        return 1.0 - (self.target_tokens / self.current_tokens)

    def __str__(self) -> str:
        return f"CompressionPlan(target={self.target_tokens}, " f"current={self.current_tokens}, tier={self.tier.value})"


class CompressionStrategy(ABC):
    """压缩策略基类"""

    @abstractmethod
    def create_plan(
        self, messages: List[Dict], current_tokens: int, target_tokens: int, scores: Optional[List] = None
    ) -> CompressionPlan:
        """创建压缩计划

        Args:
            messages: 消息列表
            current_tokens: 当前 token 数
            target_tokens: 目标 token 数
            scores: 消息评分列表

        Returns:
            压缩计划
        """

    @abstractmethod
    def execute_plan(self, messages: List[Dict], plan: CompressionPlan, scores: Optional[List] = None) -> List[Dict]:
        """执行压缩计划

        Args:
            messages: 原始消息列表
            plan: 压缩计划
            scores: 消息评分列表

        Returns:
            压缩后的消息列表
        """


class TieredCompressionStrategy(CompressionStrategy):
    """分层压缩策略

    根据压缩强度选择不同的策略：
    1. 保留 system 消息
    2. 保留高分消息
    3. 保留首尾消息
    4. 移除低分消息
    """

    # 不同层级的配置
    TIER_CONFIGS = {
        CompressionTier.NONE: {
            "keep_first_n": 0,
            "keep_last_n": 0,
            "score_threshold": 0.0,
            "remove_system": False,
        },
        CompressionTier.LIGHT: {
            "keep_first_n": 5,
            "keep_last_n": 5,
            "score_threshold": 0.3,
            "remove_system": False,
        },
        CompressionTier.MEDIUM: {
            "keep_first_n": 3,
            "keep_last_n": 3,
            "score_threshold": 0.5,
            "remove_system": False,
        },
        CompressionTier.AGGRESSIVE: {
            "keep_first_n": 2,
            "keep_last_n": 2,
            "score_threshold": 0.7,
            "remove_system": False,
        },
        CompressionTier.EXTREME: {
            "keep_first_n": 1,
            "keep_last_n": 1,
            "score_threshold": 0.9,
            "remove_system": False,
        },
    }

    def __init__(self, custom_configs: Optional[Dict] = None):
        """初始化分层压缩策略

        Args:
            custom_configs: 自定义层级配置
        """
        self.configs = custom_configs or self.TIER_CONFIGS

    def create_plan(
        self, messages: List[Dict], current_tokens: int, target_tokens: int, scores: Optional[List] = None
    ) -> CompressionPlan:
        """创建压缩计划

        Args:
            messages: 消息列表
            current_tokens: 当前 token 数
            target_tokens: 目标 token 数
            scores: 消息评分列表

        Returns:
            压缩计划
        """
        # 根据压缩比例选择层级
        ratio = 1.0 - (target_tokens / current_tokens) if current_tokens > 0 else 0.0

        if ratio <= 0.0:
            tier = CompressionTier.NONE
        elif ratio <= 0.2:
            tier = CompressionTier.LIGHT
        elif ratio <= 0.5:
            tier = CompressionTier.MEDIUM
        elif ratio <= 0.7:
            tier = CompressionTier.AGGRESSIVE
        else:
            tier = CompressionTier.EXTREME

        config = self.configs[tier]

        return CompressionPlan(
            target_tokens=target_tokens,
            current_tokens=current_tokens,
            tier=tier,
            remove_system=config["remove_system"],
            keep_first_n=config["keep_first_n"],
            keep_last_n=config["keep_last_n"],
            score_threshold=config["score_threshold"],
        )

    def execute_plan(self, messages: List[Dict], plan: CompressionPlan, scores: Optional[List] = None) -> List[Dict]:
        """执行压缩计划

        Args:
            messages: 原始消息列表
            plan: 压缩计划
            scores: 消息评分列表

        Returns:
            压缩后的消息列表
        """
        if not messages:
            return []

        # 分离 system 消息
        system_messages = [m for m in messages if m.get("role") == "system"]
        other_messages = [m for m in messages if m.get("role") != "system"]

        # 如果需要移除 system 消息
        if plan.remove_system:
            system_messages = []

        # 保留首尾消息
        if len(other_messages) <= plan.keep_first_n + plan.keep_last_n:
            keep_first = other_messages
            keep_last = []
            middle_messages = []
        else:
            keep_first = other_messages[: plan.keep_first_n]
            keep_last = other_messages[-plan.keep_last_n :] if plan.keep_last_n > 0 else []
            middle_messages = other_messages[plan.keep_first_n :] if plan.keep_first_n < len(other_messages) else []
            if plan.keep_last_n > 0 and len(middle_messages) > plan.keep_last_n:
                middle_messages = middle_messages[: -plan.keep_last_n]

        # 根据评分过滤中间消息
        if scores and plan.score_threshold > 0:
            # 假设 scores 和 messages 对应
            middle_scores = (
                scores[len(system_messages) + plan.keep_first_n : len(scores) - plan.keep_last_n]
                if plan.keep_last_n > 0
                else scores[len(system_messages) + plan.keep_first_n :]
            )

            filtered_middle = []
            for msg, score in zip(middle_messages, middle_scores):
                score_value = score.score if hasattr(score, "score") else score
                if score_value >= plan.score_threshold:
                    filtered_middle.append(msg)
            middle_messages = filtered_middle

        # 组合结果
        result = system_messages + keep_first + middle_messages + keep_last

        logger.info(f"压缩完成: {len(messages)} -> {len(result)} 条消息 " f"({plan.tier.value} 压缩)")

        return result
