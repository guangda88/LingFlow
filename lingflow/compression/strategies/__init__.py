"""压缩策略模块

提供不同的压缩策略实现。
"""

from .base import CompressionPlan, CompressionStrategy, CompressionTier, TieredCompressionStrategy

__all__ = [
    "CompressionStrategy",
    "TieredCompressionStrategy",
    "CompressionTier",
    "CompressionPlan",
]
