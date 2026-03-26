"""LingFlow Compression模块

导出:
- ContextCompressor: 主压缩器 (兼容层)
- AdvancedContextCompressor: 高级压缩器
- CompressionLevel: 压缩级别枚举
- CompressionStrategy: 压缩策略枚举
- CompressionResult: 压缩结果数据类
- CompressionConfig: 压缩配置
- ConversationCompressor: 对话压缩器
- enable_auto_compression: 启用自动压缩
- compress_if_needed: 按需压缩上下文
- compress_messages: 压缩消息历史
"""

from .compressor import (
    ContextCompressor,
    AdvancedContextCompressor,
    CompressionLevel,
    CompressionStrategy,
    CompressionResult,
    _BasicCompressor
)
from .config import (
    CompressionConfig,
    ConversationCompressor,
    enable_auto_compression,
    compress_if_needed,
    compress_messages,
    get_conversation_compressor,
)

__all__ = [
    "ContextCompressor",
    "AdvancedContextCompressor",
    "CompressionLevel",
    "CompressionStrategy",
    "CompressionResult",
    "CompressionConfig",
    "ConversationCompressor",
    "enable_auto_compression",
    "compress_if_needed",
    "compress_messages",
    "get_conversation_compressor",
]
