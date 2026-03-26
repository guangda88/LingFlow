"""LingFlow Compression模块

提供智能上下文压缩功能，防止因 token 限制导致会话中断。

导出:
- SmartContextCompressor: 智能压缩器 (推荐)
- TokenEstimator: 精确 Token 计数器
- MessageScorer: 消息重要性评分器
- ConversationSummarizer: 对话摘要生成器
- ContextCompressor: 主压缩器 (兼容层)
- AdvancedContextCompressor: 高级压缩器
- CompressionLevel: 压缩级别枚举
- CompressionStrategy: 压缩策略枚举
- CompressionConfig: 压缩配置
- ConversationCompressor: 对话压缩器
- enable_smart_compression: 启用智能压缩
- compress_if_needed: 按需压缩上下文
- compress_messages: 压缩消息历史
"""

# 智能压缩模块 (推荐使用)
from .smart_compressor import (
    SmartContextCompressor,
    TokenEstimator,
    MessageScorer,
    ConversationSummarizer,
    CompressionTier,
    CompressionPlan,
    MessageScore,
    get_smart_compressor,
    compress_messages as smart_compress_messages,
    estimate_tokens,
)

# 兼容层
from .compressor import (
    ContextCompressor,
    AdvancedContextCompressor,
    CompressionLevel,
    CompressionStrategy,
    CompressionResult as OldCompressionResult,
    _BasicCompressor
)
from .config import (
    CompressionConfig,
    ConversationCompressor,
    enable_auto_compression,
    compress_if_needed,
    compress_messages as old_compress_messages,
    get_conversation_compressor,
)

__all__ = [
    # 智能压缩 (推荐)
    "SmartContextCompressor",
    "TokenEstimator",
    "MessageScorer",
    "ConversationSummarizer",
    "CompressionTier",
    "CompressionPlan",
    "MessageScore",
    "get_smart_compressor",
    "smart_compress_messages",
    "estimate_tokens",
    "enable_smart_compression",
    # 兼容层
    "ContextCompressor",
    "AdvancedContextCompressor",
    "CompressionLevel",
    "CompressionStrategy",
    "CompressionConfig",
    "ConversationCompressor",
    "enable_auto_compression",
    "compress_if_needed",
    "old_compress_messages",
    "get_conversation_compressor",
]

# ============================================================================
# 智能压缩管理
# ============================================================================

_smart_compressor_instance = None


def enable_smart_compression(
    max_tokens: int = 180000,
    warning_threshold: float = 0.75,
    compress_threshold: float = 0.85
) -> SmartContextCompressor:
    """启用智能上下文压缩

    这是推荐的启用方式，提供更精确的 token 计数和智能压缩策略。

    Args:
        max_tokens: 最大 token 数量 (默认 180k for Claude)
        warning_threshold: 警告阈值 (默认 75%)
        compress_threshold: 压缩阈值 (默认 85%)

    Returns:
        智能压缩器实例

    Example:
        from lingflow.compression import enable_smart_compression, estimate_tokens

        # 启用智能压缩
        compressor = enable_smart_compression()

        # 估算当前 token 数量
        messages = [{"role": "user", "content": "Hello"}]
        token_count = estimate_tokens(messages)
        print(f"当前 tokens: {token_count}")
    """
    global _smart_compressor_instance

    config = {
        "warning_threshold": warning_threshold,
        "compress_threshold": compress_threshold,
        "target_ratio": 0.5
    }

    _smart_compressor_instance = SmartContextCompressor(
        max_tokens=max_tokens,
        config=config
    )

    return _smart_compressor_instance


def get_current_compressor() -> SmartContextCompressor:
    """获取当前智能压缩器实例"""
    global _smart_compressor_instance
    if _smart_compressor_instance is None:
        _smart_compressor_instance = enable_smart_compression()
    return _smart_compressor_instance


# 导出便利函数
def estimate_current_tokens(messages: list) -> int:
    """估算消息列表的 token 数量

    Args:
        messages: 消息列表

    Returns:
        token 数量
    """
    compressor = get_current_compressor()
    return compressor.token_estimator.count_messages(messages)


def check_and_compress(messages: list) -> tuple:
    """检查并按需压缩消息

    Args:
        messages: 消息列表

    Returns:
        (是否压缩, 压缩后的消息列表)
    """
    compressor = get_current_compressor()
    did_compress, result = compressor.check_and_compress(messages)

    if did_compress and result:
        return True, result.compressed_messages
    return False, messages


# 模块导入时启用智能压缩 (默认配置)
enable_smart_compression()
