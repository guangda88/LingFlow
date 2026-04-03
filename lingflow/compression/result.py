"""压缩结果数据类

定义压缩操作的结果数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class CompressionResult:
    """压缩结果

    记录压缩操作的详细结果。

    Attributes:
        original_messages: 原始消息列表
        compressed_messages: 压缩后的消息列表
        original_tokens: 原始 token 数
        compressed_tokens: 压缩后 token 数
        strategy: 使用的压缩策略
        tier: 压缩层级
        timestamp: 压缩时间
        metadata: 额外的元数据
    """

    original_messages: List[Dict]
    compressed_messages: List[Dict]
    original_tokens: int
    compressed_tokens: int
    strategy: str = "tiered"
    tier: str = "medium"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def compression_ratio(self) -> float:
        """压缩比例"""
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.compressed_tokens / self.original_tokens)

    @property
    def tokens_saved(self) -> int:
        """节省的 token 数"""
        return self.original_tokens - self.compressed_tokens

    @property
    def message_count_ratio(self) -> float:
        """消息数量比例"""
        if not self.original_messages:
            return 0.0
        return len(self.compressed_messages) / len(self.original_messages)

    def to_dict(self) -> Dict:
        """转换为字典

        Returns:
            结果字典
        """
        return {
            "original_count": len(self.original_messages),
            "compressed_count": len(self.compressed_messages),
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": self.compression_ratio,
            "tokens_saved": self.tokens_saved,
            "strategy": self.strategy,
            "tier": self.tier,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        return (
            f"CompressionResult("
            f"{len(self.original_messages)} -> {len(self.compressed_messages)} msgs, "
            f"{self.original_tokens} -> {self.compressed_tokens} tokens, "
            f"{self.compression_ratio:.1%} reduction)"
        )
