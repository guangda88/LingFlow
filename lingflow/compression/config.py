"""LingFlow 上下文压缩配置

此模块配置对话上下文的自动压缩功能，防止对话因 token 限制而中断。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from lingflow.compression.compressor import (
    AdvancedContextCompressor,
    CompressionStrategy,
)
from lingflow.compression.token_estimator import TokenEstimator


class CompressionConfig:
    """上下文压缩配置"""

    # 默认配置
    DEFAULT_CONFIG = {
        "enabled": True,
        "target_ratio": 0.4,  # 目标压缩比例 (保留 40%)
        "threshold_tokens": 50000,  # 触发压缩的 token 阈值
        "preserve_keywords": True,
        "strategies": ["density", "semantic", "list"],
        "custom_keywords": [
            # 关键操作词
            "must", "should", "require", "ensure",
            "critical", "important", "essential",
            "verify", "validate", "confirm",
            "fix", "bug", "error", "warning",
            "todo", "note", "remember",
            # 技术术语
            "api", "function", "class", "method",
            "import", "export", "return", "param"
        ]
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """初始化压缩配置

        Args:
            config: 自定义配置，覆盖默认值
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

    @property
    def enabled(self) -> bool:
        return self.config.get("enabled", True)

    @property
    def target_ratio(self) -> float:
        return self.config.get("target_ratio", 0.4)

    @property
    def threshold_tokens(self) -> int:
        return self.config.get("threshold_tokens", 50000)

    def create_compressor(self) -> AdvancedContextCompressor:
        """根据配置创建压缩器实例

        Returns:
            配置好的压缩器
        """
        strategies = [
            CompressionStrategy(s)
            for s in self.config.get("strategies", ["density", "semantic", "list"])
        ]

        return AdvancedContextCompressor(
            target_ratio=self.target_ratio,
            preserve_keywords=self.config.get("preserve_keywords", True),
            custom_keywords=self.config.get("custom_keywords"),
            strategies=strategies
        )


class ConversationCompressor:
    """对话上下文压缩器

    自动监控对话长度，在超过阈值时压缩上下文。
    """

    # 估算 token 的比率 (约 4 字符 = 1 token) — 保留向后兼容
    CHAR_TO_TOKEN_RATIO = 0.25

    def __init__(self, config: Optional[CompressionConfig] = None) -> None:
        """初始化对话压缩器

        Args:
            config: 压缩配置
        """
        self.config = config or CompressionConfig()
        self.compressor = self.config.create_compressor()
        self._token_estimator = TokenEstimator()
        self._compression_count = 0
        self._total_saved_tokens = 0

    def estimate_tokens(self, text: str) -> int:
        """估算文本的 token 数量

        Args:
            text: 输入文本

        Returns:
            估算的 token 数量
        """
        return self._token_estimator.count_tokens(text)

    def should_compress(self, context: Dict[str, Any]) -> bool:
        """检查是否需要压缩

        Args:
            context: 当前上下文

        Returns:
            是否需要压缩
        """
        if not self.config.enabled:
            return False

        # 估算总 token 数
        total_tokens = 0
        for value in context.values():
            if isinstance(value, str):
                total_tokens += self.estimate_tokens(value)
            elif isinstance(value, list):
                for item in value:
                    total_tokens += self.estimate_tokens(str(item))
            elif isinstance(value, dict):
                total_tokens += self.estimate_tokens(json.dumps(value))

        return total_tokens > self.config.threshold_tokens

    def compress_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """压缩对话上下文

        Args:
            context: 原始上下文

        Returns:
            压缩后的上下文
        """
        if not self.should_compress(context):
            return context

        original_size = len(json.dumps(context))

        # 使用压缩器压缩
        compressed = self.compressor.compress(context)

        compressed_size = len(json.dumps(compressed))
        original_tokens = self._token_estimator.count_tokens(json.dumps(context))
        compressed_tokens = self._token_estimator.count_tokens(
            json.dumps(compressed),
        )
        saved_tokens = original_tokens - compressed_tokens

        self._compression_count += 1
        self._total_saved_tokens += saved_tokens

        return compressed

    def compress_conversation_history(
        self,
        messages: List[Dict[str, str]],
        keep_recent: int = 10
    ) -> List[Dict[str, str]]:
        """压缩对话历史

        保留最近 N 条消息，使用 ConversationSummarizer 生成旧消息摘要。

        Args:
            messages: 消息列表
            keep_recent: 保留的最近消息数量

        Returns:
            压缩后的消息列表
        """
        if len(messages) <= keep_recent:
            return messages

        recent = messages[-keep_recent:]
        old_messages = messages[:-keep_recent]

        if old_messages:
            from lingflow.compression.summarizer import ConversationSummarizer
            summarizer = ConversationSummarizer()
            summary_msg = summarizer.create_summary_message(old_messages)
            return [summary_msg] + recent

        return recent

    def get_stats(self) -> Dict[str, Any]:
        """获取压缩统计信息

        Returns:
            统计信息字典
        """
        return {
            "compression_count": self._compression_count,
            "total_saved_tokens": self._total_saved_tokens,
            "config": {
                "enabled": self.config.enabled,
                "target_ratio": self.config.target_ratio,
                "threshold_tokens": self.config.threshold_tokens,
            }
        }


# 全局单例
_conversation_compressor: Optional[ConversationCompressor] = None


def get_conversation_compressor(
    config: Optional[CompressionConfig] = None
) -> ConversationCompressor:
    """获取全局对话压缩器实例

    Args:
        config: 自定义配置

    Returns:
        对话压缩器实例
    """
    global _conversation_compressor
    if _conversation_compressor is None:
        _conversation_compressor = ConversationCompressor(config)
    return _conversation_compressor


def compress_if_needed(context: Dict[str, Any]) -> Dict[str, Any]:
    """根据需要压缩上下文（便捷函数）

    Args:
        context: 原始上下文

    Returns:
        压缩后的上下文（如果需要）
    """
    compressor = get_conversation_compressor()
    return compressor.compress_context(context)


def compress_messages(
    messages: List[Dict[str, str]],
    keep_recent: int = 10
) -> List[Dict[str, str]]:
    """压缩消息历史（便捷函数）

    Args:
        messages: 消息列表
        keep_recent: 保留的最近消息数量

    Returns:
        压缩后的消息列表
    """
    compressor = get_conversation_compressor()
    return compressor.compress_conversation_history(messages, keep_recent)


# 导出模块初始化时自动启用
def enable_auto_compression(threshold_tokens: int = 50000):
    """启用自动压缩

    Args:
        threshold_tokens: 触发压缩的 token 阈值
    """
    global _conversation_compressor

    config = CompressionConfig({
        "enabled": True,
        "threshold_tokens": threshold_tokens,
        "target_ratio": 0.4
    })

    _conversation_compressor = ConversationCompressor(config)
