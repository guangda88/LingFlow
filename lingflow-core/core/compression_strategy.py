"""
LingFlow Compression Strategy

分层压缩策略，智能管理上下文
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .token_estimator import TokenEstimator, get_token_estimator
from .message_scorer import MessageScorer, get_message_scorer, MessageScore

logger = logging.getLogger(__name__)


class CompressionLevel(Enum):
    """压缩级别"""
    NONE = 0
    LIGHT = 1      # 轻度压缩：移除低重要性消息
    MEDIUM = 2     # 中度压缩：压缩中等重要性消息
    AGGRESSIVE = 3 # 激进压缩：只保留高重要性消息
    EXTREME = 4    # 极限压缩：只保留关键消息


@dataclass
class CompressionResult:
    """压缩结果"""
    original_messages: List[Dict]
    compressed_messages: List[Dict]
    original_tokens: int
    compressed_tokens: int
    reduction_ratio: float
    messages_removed: int
    compression_level: CompressionLevel
    strategy: str
    details: Dict


class TieredCompressionStrategy:
    """分层压缩策略"""

    def __init__(
        self,
        token_estimator: Optional[TokenEstimator] = None,
        message_scorer: Optional[MessageScorer] = None
    ):
        """
        初始化压缩策略

        Args:
            token_estimator: Token 估算器
            message_scorer: 消息评分器
        """
        self.token_estimator = token_estimator or get_token_estimator()
        self.message_scorer = message_scorer or get_message_scorer()
        logger.info("TieredCompressionStrategy initialized")

    def compress(
        self,
        messages: List[Dict],
        target_tokens: int,
        strategy: str = "auto"
    ) -> CompressionResult:
        """
        压缩消息列表

        Args:
            messages: 消息列表
            target_tokens: 目标 token 数量
            strategy: 压缩策略 ("auto", "tiered", "aggressive")

        Returns:
            压缩结果
        """
        if not messages:
            return CompressionResult(
                original_messages=[],
                compressed_messages=[],
                original_tokens=0,
                compressed_tokens=0,
                reduction_ratio=0.0,
                messages_removed=0,
                compression_level=CompressionLevel.NONE,
                strategy=strategy,
                details={}
            )

        # 计算原始 token 数
        original_tokens = self.token_estimator.estimate_messages(messages).token_count

        # 如果已经低于目标，不需要压缩
        if original_tokens <= target_tokens:
            return CompressionResult(
                original_messages=messages,
                compressed_messages=messages,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                reduction_ratio=0.0,
                messages_removed=0,
                compression_level=CompressionLevel.NONE,
                strategy=strategy,
                details={"reason": "Already under target"}
            )

        # 根据策略选择压缩方法
        if strategy == "auto":
            return self._auto_compress(messages, target_tokens, original_tokens)
        elif strategy == "tiered":
            return self._tiered_compress(messages, target_tokens, original_tokens)
        elif strategy == "aggressive":
            return self._aggressive_compress(messages, target_tokens, original_tokens)
        else:
            logger.warning(f"Unknown strategy: {strategy}, using auto")
            return self._auto_compress(messages, target_tokens, original_tokens)

    def _auto_compress(
        self,
        messages: List[Dict],
        target_tokens: int,
        original_tokens: int
    ) -> CompressionResult:
        """
        自动压缩策略

        根据超出的程度自动选择压缩级别
        """
        excess_ratio = original_tokens / target_tokens

        if excess_ratio < 1.2:
            # 超出不到 20%，轻度压缩
            return self._light_compress(messages, target_tokens, original_tokens)
        elif excess_ratio < 1.5:
            # 超出 20-50%，中度压缩
            return self._medium_compress(messages, target_tokens, original_tokens)
        elif excess_ratio < 2.0:
            # 超出 50-100%，激进压缩
            return self._aggressive_compress(messages, target_tokens, original_tokens)
        else:
            # 超出超过 100%，极限压缩
            return self._extreme_compress(messages, target_tokens, original_tokens)

    def _tiered_compress(
        self,
        messages: List[Dict],
        target_tokens: int,
        original_tokens: int
    ) -> CompressionResult:
        """
        分层压缩策略

        逐层尝试压缩，直到达到目标
        """
        # 先尝试轻度压缩
        result = self._light_compress(messages, target_tokens, original_tokens)
        if result.compressed_tokens <= target_tokens:
            return result

        # 再尝试中度压缩
        result = self._medium_compress(messages, target_tokens, original_tokens)
        if result.compressed_tokens <= target_tokens:
            return result

        # 再尝试激进压缩
        result = self._aggressive_compress(messages, target_tokens, original_tokens)
        if result.compressed_tokens <= target_tokens:
            return result

        # 最后尝试极限压缩
        return self._extreme_compress(messages, target_tokens, original_tokens)

    def _light_compress(
        self,
        messages: List[Dict],
        target_tokens: int,
        original_tokens: int
    ) -> CompressionResult:
        """
        轻度压缩：移除低重要性消息
        """
        # 评分所有消息
        scores = self.message_scorer.batch_score(messages)

        # 移除低重要性消息（importance < 0.3）
        filtered = [
            msg for msg, score in zip(messages, scores)
            if score.importance_score >= 0.3
        ]

        compressed_tokens = self.token_estimator.estimate_messages(filtered).token_count

        return CompressionResult(
            original_messages=messages,
            compressed_messages=filtered,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_ratio=(original_tokens - compressed_tokens) / original_tokens,
            messages_removed=len(messages) - len(filtered),
            compression_level=CompressionLevel.LIGHT,
            strategy="light",
            details={
                "threshold": 0.3,
                "reason": "Removed low importance messages"
            }
        )

    def _medium_compress(
        self,
        messages: List[Dict],
        target_tokens: int,
        original_tokens: int
    ) -> CompressionResult:
        """
        中度压缩：移除低和中等重要性消息
        """
        # 评分所有消息
        scores = self.message_scorer.batch_score(messages)

        # 移除低和中低重要性消息（importance < 0.5）
        filtered = [
            msg for msg, score in zip(messages, scores)
            if score.importance_score >= 0.5
        ]

        # 压缩中等重要性消息的内容
        compressed = []
        for msg, score in zip(messages, scores):
            if score.importance_score >= 0.5:
                compressed.append(msg)
            elif score.importance_score >= 0.3:
                # 简化内容
                compressed_msg = self._simplify_message(msg)
                compressed.append(compressed_msg)

        compressed_tokens = self.token_estimator.estimate_messages(compressed).token_count

        return CompressionResult(
            original_messages=messages,
            compressed_messages=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_ratio=(original_tokens - compressed_tokens) / original_tokens,
            messages_removed=len(messages) - len(compressed),
            compression_level=CompressionLevel.MEDIUM,
            strategy="medium",
            details={
                "threshold": 0.5,
                "simplified": sum(1 for s in scores if 0.3 <= s.importance_score < 0.5),
                "reason": "Removed medium-low importance and simplified some"
            }
        )

    def _aggressive_compress(
        self,
        messages: List[Dict],
        target_tokens: int,
        original_tokens: int
    ) -> CompressionResult:
        """
        激进压缩：只保留高重要性消息
        """
        # 评分所有消息
        scores = self.message_scorer.batch_score(messages)

        # 只保留高重要性消息（importance >= 0.7）
        filtered = [
            msg for msg, score in zip(messages, scores)
            if score.importance_score >= 0.7
        ]

        compressed_tokens = self.token_estimator.estimate_messages(filtered).token_count

        return CompressionResult(
            original_messages=messages,
            compressed_messages=filtered,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_ratio=(original_tokens - compressed_tokens) / original_tokens,
            messages_removed=len(messages) - len(filtered),
            compression_level=CompressionLevel.AGGRESSIVE,
            strategy="aggressive",
            details={
                "threshold": 0.7,
                "reason": "Kept only high importance messages"
            }
        )

    def _extreme_compress(
        self,
        messages: List[Dict],
        target_tokens: int,
        original_tokens: int
    ) -> CompressionResult:
        """
        极限压缩：只保留最关键的消息
        """
        # 评分所有消息
        scores = self.message_scorer.batch_score(messages)

        # 只保留最关键的消息（importance >= 0.85）
        filtered = [
            msg for msg, score in zip(messages, scores)
            if score.importance_score >= 0.85
        ]

        # 如果还是太多，保留最重要的 N 条
        if len(filtered) > 20:
            # 按重要性排序，保留前 20 条
            scored_msgs = list(zip(messages, scores))
            scored_msgs.sort(key=lambda x: x[1].importance_score, reverse=True)
            filtered = [msg for msg, _ in scored_msgs[:20]]

        compressed_tokens = self.token_estimator.estimate_messages(filtered).token_count

        return CompressionResult(
            original_messages=messages,
            compressed_messages=filtered,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_ratio=(original_tokens - compressed_tokens) / original_tokens,
            messages_removed=len(messages) - len(filtered),
            compression_level=CompressionLevel.EXTREME,
            strategy="extreme",
            details={
                "threshold": 0.85,
                "max_messages": 20,
                "reason": "Kept only critical messages"
            }
        )

    def _simplify_message(self, message: Dict) -> Dict:
        """
        简化消息内容

        Args:
            message: 原始消息

        Returns:
            简化后的消息
        """
        content = message.get("content", "")

        # 简化策略：
        # 1. 移除代码块（保留摘要）
        # 2. 截断长文本
        # 3. 保留关键信息

        # 如果是代码，保留签名
        if "```" in content:
            lines = content.split("\n")
            simplified_lines = []
            in_code_block = False

            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    if not in_code_block:
                        simplified_lines.append("... [code block]")
                    continue

                if not in_code_block:
                    simplified_lines.append(line)
                elif in_code_block and not simplified_lines[-1].endswith("[code block]"):
                    # 保留代码的第一行（通常是函数/类定义）
                    simplified_lines.append(line)

            content = "\n".join(simplified_lines)

        # 截断长文本
        if len(content) > 500:
            content = content[:500] + "\n... [content truncated]"

        return {
            "role": message.get("role", "user"),
            "content": content,
            "simplified": True
        }

    def should_compress(
        self,
        messages: List[Dict],
        threshold: int = 150000
    ) -> bool:
        """
        判断是否需要压缩

        Args:
            messages: 消息列表
            threshold: token 阈值

        Returns:
            是否需要压缩
        """
        token_count = self.token_estimator.estimate_messages(messages).token_count
        return token_count >= threshold

    def get_compression_recommendation(
        self,
        messages: List[Dict],
        target_tokens: int
    ) -> Dict[str, any]:
        """
        获取压缩建议

        Args:
            messages: 消息列表
            target_tokens: 目标 token 数量

        Returns:
            压缩建议
        """
        current_tokens = self.token_estimator.estimate_messages(messages).token_count

        if current_tokens <= target_tokens:
            return {
                "should_compress": False,
                "reason": "Current tokens under target",
                "current_tokens": current_tokens,
                "target_tokens": target_tokens,
                "excess_tokens": 0,
                "recommended_strategy": "none"
            }

        excess = current_tokens - target_tokens
        excess_ratio = current_tokens / target_tokens

        # 根据超出程度推荐策略
        if excess_ratio < 1.2:
            strategy = "light"
            level = CompressionLevel.LIGHT
        elif excess_ratio < 1.5:
            strategy = "medium"
            level = CompressionLevel.MEDIUM
        elif excess_ratio < 2.0:
            strategy = "aggressive"
            level = CompressionLevel.AGGRESSIVE
        else:
            strategy = "extreme"
            level = CompressionLevel.EXTREME

        return {
            "should_compress": True,
            "reason": f"Tokens exceed target by {excess_ratio:.1%}",
            "current_tokens": current_tokens,
            "target_tokens": target_tokens,
            "excess_tokens": excess,
            "excess_ratio": round(excess_ratio, 2),
            "recommended_strategy": strategy,
            "recommended_level": level.value
        }


# 全局实例
_strategy: Optional[TieredCompressionStrategy] = None


def get_compression_strategy(
    token_estimator: Optional[TokenEstimator] = None,
    message_scorer: Optional[MessageScorer] = None
) -> TieredCompressionStrategy:
    """
    获取压缩策略实例（单例模式）

    Args:
        token_estimator: Token 估算器
        message_scorer: 消息评分器

    Returns:
        压缩策略实例
    """
    global _strategy
    if _strategy is None:
        _strategy = TieredCompressionStrategy(token_estimator, message_scorer)
    return _strategy


__all__ = [
    "TieredCompressionStrategy",
    "CompressionResult",
    "CompressionLevel",
    "get_compression_strategy"
]
