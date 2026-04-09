"""LingFlow 智能上下文压缩器

提供智能化的上下文压缩功能，防止因 token 限制导致会话中断。

核心功能:
1. 精确 Token 计数 - 支持多种模型的 token 计算
2. 消息重要性评分 - 多维度评分系统
3. 分层压缩策略 - 保留关键信息
4. 对话摘要生成 - 智能摘要
5. 主动预警机制 - 接近限制时提醒

使用示例:
    from lingflow.compression import SmartContextCompressor

    compressor = SmartContextCompressor()
    result = compressor.compress(messages, target_tokens=4000)
"""

import logging
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from lingflow.compression.result import CompressionResult
from lingflow.compression.scoring import MessageScorer
from lingflow.compression.strategies.base import (
    CompressionStrategy,
    TieredCompressionStrategy,
)
from lingflow.compression.summarizer import ConversationSummarizer
from lingflow.compression.token_estimator import TokenEstimator

logger = logging.getLogger(__name__)


@dataclass
class CompressionConfig:
    """压缩配置

    Attributes:
        max_tokens: 最大 token 限制
        warning_threshold: 预警阈值（比例）
        default_strategy: 默认压缩策略
        enable_summarization: 是否启用摘要
        score_messages: 是否对消息评分
    """

    max_tokens: int = 8000
    warning_threshold: float = 0.8  # 80% 时预警
    default_strategy: str = "tiered"
    enable_summarization: bool = True
    score_messages: bool = True


class SmartContextCompressor:
    """智能上下文压缩器

    主要功能：
    1. Token 计数和预警
    2. 消息重要性评分
    3. 智能压缩
    4. 对话摘要
    """

    def __init__(self, config: Optional[CompressionConfig] = None, model: str = "claude-3"):
        """初始化压缩器

        Args:
            config: 压缩配置
            model: 模型名称（用于 token 计算）
        """
        self.config = config or CompressionConfig()
        self.model = model

        # 初始化组件
        self.token_estimator = TokenEstimator(model=model)
        self.message_scorer = MessageScorer() if self.config.score_messages else None
        self.compression_strategy = TieredCompressionStrategy()
        self.summarizer = ConversationSummarizer() if self.config.enable_summarization else None

        # 线程安全锁
        self._lock = threading.Lock()

        # 预警回调
        self._warning_callbacks: List[callable] = []

    def count_tokens(self, messages: List[Dict]) -> int:
        """计算消息列表的 token 数

        Args:
            messages: 消息列表

        Returns:
            token 数量
        """
        return self.token_estimator.count_messages_tokens(messages)

    def check_warning(self, messages: List[Dict]) -> bool:
        """检查是否需要预警

        Args:
            messages: 消息列表

        Returns:
            是否需要预警
        """
        current_tokens = self.count_tokens(messages)
        threshold = self.config.max_tokens * self.config.warning_threshold

        if current_tokens >= threshold:
            # 触发预警回调
            for callback in self._warning_callbacks:
                try:
                    callback(current_tokens, self.config.max_tokens)
                except Exception as e:
                    logger.error(f"预警回调失败: {e}")

            return True

        return False

    def compress(
        self,
        messages: List[Dict],
        target_tokens: Optional[int] = None,
        strategy: Optional[CompressionStrategy] = None,
    ) -> CompressionResult:
        """压缩消息列表

        Args:
            messages: 原始消息列表
            target_tokens: 目标 token 数，默认使用配置的最大值
            strategy: 压缩策略，默认使用分层策略

        Returns:
            压缩结果
        """
        with self._lock:
            # 计算当前 token 数
            current_tokens = self.count_tokens(messages)
            target_tokens = target_tokens or self.config.max_tokens

            # 如果不需要压缩
            if current_tokens <= target_tokens:
                return CompressionResult(
                    original_messages=messages,
                    compressed_messages=messages,
                    original_tokens=current_tokens,
                    compressed_tokens=current_tokens,
                    strategy="none",
                    tier="none",
                )

            # 对消息评分
            scores = None
            if self.message_scorer:
                scores = self.message_scorer.score_messages(messages)

            # 创建压缩计划
            strategy = strategy or self.compression_strategy
            plan = strategy.create_plan(
                messages=messages,
                current_tokens=current_tokens,
                target_tokens=target_tokens,
                scores=scores,
            )

            # 执行压缩
            compressed = strategy.execute_plan(messages, plan, scores)

            if self.summarizer and len(compressed) < len(messages) and len(compressed) > 0:

                removed = [m for m in messages if m not in compressed]
                if removed:
                    summary_msg = self.summarizer.create_summary_message(removed)
                    candidate = [summary_msg] + compressed
                    candidate_tokens = self.count_tokens(candidate)
                    if candidate_tokens < current_tokens:
                        compressed = candidate

            # 计算最终 token 数
            final_tokens = self.count_tokens(compressed)

            return CompressionResult(
                original_messages=messages,
                compressed_messages=compressed,
                original_tokens=current_tokens,
                compressed_tokens=final_tokens,
                strategy=strategy.__class__.__name__,
                tier=plan.tier.value,
                metadata={"plan": str(plan), "score_threshold": plan.score_threshold},
            )

    def compress_if_needed(self, messages: List[Dict], target_tokens: Optional[int] = None) -> List[Dict]:
        """按需压缩消息

        只在超出限制时才压缩。

        Args:
            messages: 消息列表
            target_tokens: 目标 token 数

        Returns:
            压缩后的消息列表（如果需要）
        """
        current_tokens = self.count_tokens(messages)
        target_tokens = target_tokens or self.config.max_tokens

        if current_tokens <= target_tokens:
            return messages

        result = self.compress(messages, target_tokens)
        return result.compressed_messages

    def add_warning_callback(self, callback: callable):
        """添加预警回调

        Args:
            callback: 回调函数，接收 (current_tokens, max_tokens)
        """
        self._warning_callbacks.append(callback)

    def get_stats(self, messages: List[Dict]) -> Dict[str, Any]:
        """获取统计信息

        Args:
            messages: 消息列表

        Returns:
            统计信息字典
        """
        token_count = self.count_tokens(messages)

        return {
            "message_count": len(messages),
            "token_count": token_count,
            "max_tokens": self.config.max_tokens,
            "usage_ratio": token_count / self.config.max_tokens,
            "warning_threshold": self.config.warning_threshold,
            "needs_compression": token_count > self.config.max_tokens,
            "needs_warning": token_count > (self.config.max_tokens * self.config.warning_threshold),
        }


# 默认实例
_default_compressor: Optional[SmartContextCompressor] = None


def get_default_compressor() -> SmartContextCompressor:
    """获取默认压缩器实例"""
    global _default_compressor
    if _default_compressor is None:
        _default_compressor = SmartContextCompressor()
    return _default_compressor


def compress_messages(messages: List[Dict], target_tokens: Optional[int] = None) -> List[Dict]:
    """便捷函数：压缩消息

    Args:
        messages: 消息列表
        target_tokens: 目标 token 数

    Returns:
        压缩后的消息列表
    """
    compressor = get_default_compressor()
    return compressor.compress_if_needed(messages, target_tokens)
