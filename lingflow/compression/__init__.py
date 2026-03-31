"""LingFlow 智能压缩模块

提供上下文压缩和 token 管理功能。
"""

try:
    from .smart_compressor_new import (
        SmartContextCompressor,
        CompressionConfig,
        get_default_compressor,
        compress_messages,
        enable_smart_compression
    )
except ImportError:
    from .compressor import ContextCompressor as SmartContextCompressor

    class CompressionConfig:
        pass

    def get_default_compressor():
        return SmartContextCompressor()

    def compress_messages(messages, target_tokens=4000):
        return SmartContextCompressor().compress(messages)

    def enable_smart_compression(**kwargs):
        """Enable smart compression"""
        return True
from .token_estimator import TokenEstimator
from .scoring import MessageScorer, MessageScore
from .strategies.base import (
    CompressionStrategy,
    TieredCompressionStrategy,
    CompressionTier,
    CompressionPlan
)
from .summarizer import ConversationSummarizer
from .result import CompressionResult

__all__ = [
    # 主要接口
    "SmartContextCompressor",
    "CompressionConfig",
    "get_default_compressor",
    "compress_messages",

    # 组件
    "TokenEstimator",
    "MessageScorer",
    "MessageScore",
    "ConversationSummarizer",

    # 策略
    "CompressionStrategy",
    "TieredCompressionStrategy",
    "CompressionTier",
    "CompressionPlan",

    # 结果
    "CompressionResult",
]
