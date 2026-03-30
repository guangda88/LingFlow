"""
LingFlow Smart Compression Strategy - 智能压缩策略

结合依赖分析的智能压缩
"""

import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from .compression_strategy import (
    TieredCompressionStrategy,
    CompressionResult,
    CompressionLevel
)
from .dependency_analyzer import DependencyAnalyzer
from .token_estimator import TokenEstimator
from .message_scorer import MessageScorer

logger = logging.getLogger(__name__)


@dataclass
class SmartCompressionResult(CompressionResult):
    """智能压缩结果"""
    preserved_critical: bool  # 是否保留了关键消息
    dependency_impact: float   # 依赖影响分数 (0-1)
    critical_indices: Set[int]  # 关键消息索引


class SmartCompressionStrategy(TieredCompressionStrategy):
    """智能压缩策略（考虑依赖关系）"""

    def __init__(
        self,
        token_estimator: Optional[TokenEstimator] = None,
        message_scorer: Optional[MessageScorer] = None
    ):
        super().__init__(token_estimator, message_scorer)
        self.dependency_analyzer = DependencyAnalyzer()
        logger.info("SmartCompressionStrategy initialized")

    def compress_smart(
        self,
        messages: List[Dict],
        target_tokens: int,
        preserve_dependencies: bool = True
    ) -> SmartCompressionResult:
        """
        智能压缩（考虑依赖关系）

        Args:
            messages: 消息列表
            target_tokens: 目标 token 数量
            preserve_dependencies: 是否保留依赖关系

        Returns:
            智能压缩结果
        """
        if not messages:
            return SmartCompressionResult(
                original_messages=[],
                compressed_messages=[],
                original_tokens=0,
                compressed_tokens=0,
                reduction_ratio=0.0,
                messages_removed=0,
                compression_level=CompressionLevel.NONE,
                strategy="smart",
                details={},
                preserved_critical=True,
                dependency_impact=0.0,
                critical_indices=set()
            )

        # 计算原始 tokens
        original_tokens = self.token_estimator.estimate_messages(messages).token_count

        # 如果已经低于目标，不需要压缩
        if original_tokens <= target_tokens:
            return SmartCompressionResult(
                original_messages=messages,
                compressed_messages=messages,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                reduction_ratio=0.0,
                messages_removed=0,
                compression_level=CompressionLevel.NONE,
                strategy="smart",
                details={"reason": "Already under target"},
                preserved_critical=True,
                dependency_impact=0.0,
                critical_indices=set()
            )

        # 分析依赖关系
        dependency_graph = self.dependency_analyzer.analyze_dependencies(messages)
        critical_indices = self.dependency_analyzer.get_critical_messages(
            messages,
            dependency_graph
        )

        # 评分所有消息
        scores = self.message_scorer.batch_score(messages)

        # 标记消息：关键 + 重要性
        message_status = []
        for i, (msg, score) in enumerate(zip(messages, scores)):
            is_critical = i in critical_indices
            importance = score.importance_score
            message_status.append({
                "index": i,
                "critical": is_critical,
                "importance": importance,
                "tokens": self.token_estimator.estimate(msg.get("content", "")).token_count
            })

        # 按优先级排序：关键 > 高重要性 > 低重要性
        # 不可删除：critical = True
        # 可删除但优先保留：importance > 0.7
        # 可删除：importance <= 0.7

        # 分离可删除的消息
        removable = []
        must_keep = []

        for status in message_status:
            if status["critical"]:
                must_keep.append(status["index"])
            elif status["importance"] > 0.7:
                must_keep.append(status["index"])
            else:
                removable.append(status)

        # 按重要性排序可删除消息（从低到高）
        removable.sort(key=lambda x: x["importance"])

        # 尝试压缩
        compressed_messages = []
        removed_tokens = 0
        removed_count = 0

        # 首先保留必须保留的消息
        for idx in must_keep:
            compressed_messages.append(messages[idx])

        # 然后逐步添加可删除消息，直到达到目标
        for status in removable:
            current_tokens = self.token_estimator.estimate_messages(compressed_messages).token_count

            if current_tokens >= target_tokens:
                # 已经达到目标，不添加这条消息
                removed_tokens += status["tokens"]
                removed_count += 1
            else:
                # 还可以添加
                compressed_messages.append(messages[status["index"]])

        # 确保至少保留最关键的消息
        if not compressed_messages:
            # 保留最关键的前3条
            must_keep_sorted = sorted(must_keep, key=lambda i: scores[i].importance_score, reverse=True)
            for idx in must_keep_sorted[:3]:
                compressed_messages.append(messages[idx])

        # 计算结果
        compressed_tokens = self.token_estimator.estimate_messages(compressed_messages).token_count
        reduction_ratio = (original_tokens - compressed_tokens) / original_tokens if original_tokens > 0 else 0

        # 验证关键消息是否保留
        preserved_critical = all(idx in range(len(compressed_messages)) for idx in critical_indices)

        # 计算依赖影响
        kept_indices = set(range(len(compressed_messages)))
        removed_indices = set(range(len(messages))) - kept_indices

        impact = self.dependency_analyzer.calculate_removal_impact(messages, removed_indices)
        dependency_impact = impact["impact_score"] / (len(messages) * 2)  # 归一化

        # 确定压缩级别
        if removed_count == 0:
            level = CompressionLevel.NONE
        elif removed_count < len(messages) * 0.2:
            level = CompressionLevel.LIGHT
        elif removed_count < len(messages) * 0.5:
            level = CompressionLevel.MEDIUM
        elif removed_count < len(messages) * 0.7:
            level = CompressionLevel.AGGRESSIVE
        else:
            level = CompressionLevel.EXTREME

        return SmartCompressionResult(
            original_messages=messages,
            compressed_messages=compressed_messages,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_ratio=reduction_ratio,
            messages_removed=removed_count,
            compression_level=level,
            strategy="smart",
            details={
                "preserved_critical": preserved_critical,
                "critical_count": len(critical_indices),
                "dependency_impact": dependency_impact,
                "removed_indices": list(removed_indices),
                "kept_indices": list(kept_indices)
            },
            preserved_critical=preserved_critical,
            dependency_impact=dependency_impact,
            critical_indices=critical_indices
        )

    def should_compress_smart(
        self,
        messages: List[Dict],
        threshold: int = 150000
    ) -> Dict[str, any]:
        """
        智能判断是否应该压缩

        Args:
            messages: 消息列表
            threshold: token 阈值

        Returns:
            压缩建议
        """
        token_count = self.token_estimator.estimate_messages(messages).token_count

        # 基础检查
        if token_count < threshold:
            return {
                "should_compress": False,
                "reason": "Token count under threshold",
                "current_tokens": token_count,
                "threshold": threshold,
                "recommendation": "No compression needed"
            }

        # 分析依赖复杂度
        dependency_graph = self.dependency_analyzer.analyze_dependencies(messages)
        critical_count = len(self.dependency_analyzer.get_critical_messages(messages, dependency_graph))

        # 计算压缩空间
        non_critical_count = len(messages) - critical_count

        # 如果非关键消息很少，压缩效果有限
        if non_critical_count < 5:
            return {
                "should_compress": False,
                "reason": "Too few non-critical messages",
                "current_tokens": token_count,
                "threshold": threshold,
                "critical_messages": critical_count,
                "non_critical_messages": non_critical_count,
                "recommendation": "Consider manual cleanup instead"
            }

        # 计算预期压缩效果
        # 假设可以删除 50% 的非关键消息
        estimated_removable = int(non_critical_count * 0.5)
        estimated_reduction = estimated_removable / len(messages)

        return {
            "should_compress": True,
            "reason": f"Token count ({token_count}) exceeds threshold ({threshold})",
            "current_tokens": token_count,
            "threshold": threshold,
            "excess_tokens": token_count - threshold,
            "critical_messages": critical_count,
            "non_critical_messages": non_critical_count,
            "estimated_removable": estimated_removable,
            "estimated_reduction": f"{estimated_reduction*100:.1f}%",
            "recommendation": "Use smart compression to preserve dependencies"
        }
