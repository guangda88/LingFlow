"""LingFlow 上下文压缩器"""

from typing import Dict, Any


class ContextCompressor:
    """Simplified context compressor for reducing token usage.

    This compressor reduces token usage by prioritizing important fields
    and truncating long text content.
    """

    def __init__(self, target_tokens: int = 4000) -> None:
        """Initialize the context compressor.

        Args:
            target_tokens: Target token count for compression
        """
        self.target_tokens: int = target_tokens
        self.compressions_count: int = 0
        self.tokens_saved: int = 0

    def compress(self, context: Dict[str, Any], max_tokens: int = 4000) -> Dict[str, Any]:
        """Compress the context to reduce token usage.

        Priority fields (requirements, specification, description) are preserved
        with a 1000 character limit. Other fields are limited to 3 items with
        a 500 character limit each.

        Args:
            context: The context dictionary to compress
            max_tokens: Maximum token count (not currently used)

        Returns:
            Compressed context dictionary
        """
        if not context:
            return context

        self.compressions_count += 1
        original_tokens = self._estimate_tokens(context)

        # 简化策略：保留关键字段，截断长文本
        compressed = {}
        priority_keys = ['requirements', 'specification', 'description']

        # 优先保留高优先级字段
        for key in priority_keys:
            if key in context:
                value = str(context[key])
                if len(value) > 1000:
                    value = value[:1000] + "... [truncated]"
                compressed[key] = value

        # 处理其他字段（限制数量）
        other_count = 0
        max_other = 3
        for key, value in context.items():
            if key not in compressed and other_count < max_other:
                compressed[key] = str(value)[:500]
                other_count += 1

        saved_tokens = original_tokens - self._estimate_tokens(compressed)
        self.tokens_saved += saved_tokens

        return compressed

    def _estimate_tokens(self, data: Any) -> int:
        """估算 token 数量"""
        text = str(data)
        return len(text) // 4  # 简单估算：4 字符/token

    def get_stats(self) -> Dict[str, int]:
        """Get compression statistics.

        Returns:
            Dictionary containing:
            - total_compressions: Total number of compressions performed
            - tokens_saved: Total number of tokens saved
        """
        return {
            'total_compressions': self.compressions_count,
            'tokens_saved': self.tokens_saved
        }
