"""LingFlow 智能压缩模块

提供上下文压缩和 token 管理功能。
"""

try:
    from .smart_compressor_new import (
        CompressionConfig,
        SmartContextCompressor,
        compress_messages,
        enable_smart_compression,
        get_default_compressor,
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


from .result import CompressionResult
from .scoring import MessageScore, MessageScorer
from .strategies.base import CompressionPlan, CompressionStrategy, CompressionTier, TieredCompressionStrategy
from .summarizer import ConversationSummarizer
from .token_estimator import TokenEstimator

__all__ = [
    # 主要接口
    "SmartContextCompressor",
    "CompressionConfig",
    "get_default_compressor",
    "compress_messages",
    "enable_smart_compression",
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
