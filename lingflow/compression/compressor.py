"""LingFlow 上下文压缩器"""

from typing import Dict, Any


class ContextCompressor:
    """简化的上下文压缩器"""

    def __init__(self, target_tokens: int = 4000):
        self.target_tokens = target_tokens
        self.compressions_count = 0
        self.tokens_saved = 0

    def compress(self, context: Dict[str, Any], max_tokens: int = 4000) -> Dict[str, Any]:
        """压缩上下文"""
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
        """获取统计信息"""
        return {
            'total_compressions': self.compressions_count,
            'tokens_saved': self.tokens_saved
        }
