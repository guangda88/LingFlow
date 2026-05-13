"""lingflow 智能压缩模块

提供上下文压缩和 token 管理功能。
"""

from .smart_compressor import (
    CompressionConfig,
    SmartContextCompressor,
    compress_messages,
    get_default_compressor,
)
from .result import CompressionResult
from .scoring import MessageScore, MessageScorer
from .strategies.base import CompressionPlan, CompressionStrategy, CompressionTier, TieredCompressionStrategy
from .summarizer import ConversationSummarizer
from .token_estimator import TokenEstimator

_default_compressor: SmartContextCompressor | None = None


def enable_smart_compression(
    max_tokens: int = 180000,
    warning_threshold: float = 0.75,
    compress_threshold: float = 0.85,
) -> SmartContextCompressor:
    """初始化并返回全局 SmartContextCompressor 实例

    Args:
        max_tokens: 最大 token 限制
        warning_threshold: 预警阈值（比例）
        compress_threshold: 压缩阈值（比例）

    Returns:
        配置好的 SmartContextCompressor 实例
    """
    global _default_compressor
    config = CompressionConfig(
        max_tokens=max_tokens,
        warning_threshold=warning_threshold,
    )
    _default_compressor = SmartContextCompressor(config=config)
    return _default_compressor


__all__ = [
    "SmartContextCompressor",
    "CompressionConfig",
    "get_default_compressor",
    "compress_messages",
    "enable_smart_compression",
    "TokenEstimator",
    "MessageScorer",
    "MessageScore",
    "ConversationSummarizer",
    "CompressionStrategy",
    "TieredCompressionStrategy",
    "CompressionTier",
    "CompressionPlan",
    "CompressionResult",
]
