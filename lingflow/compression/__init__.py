"""LingFlow Compression模块

导出:
- ContextCompressor: 主压缩器 (兼容层)
- AdvancedContextCompressor: 高级压缩器
- CompressionLevel: 压缩级别枚举
- CompressionStrategy: 压缩策略枚举
- CompressionResult: 压缩结果数据类
"""

from .compressor import (
    ContextCompressor,
    AdvancedContextCompressor,
    CompressionLevel,
    CompressionStrategy,
    CompressionResult,
    _BasicCompressor
)

__all__ = [
    "ContextCompressor",
    "AdvancedContextCompressor",
    "CompressionLevel",
    "CompressionStrategy",
    "CompressionResult"
]
