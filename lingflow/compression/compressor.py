"""LingFlow 上下文压缩器

支持多种压缩策略：
- basic: 基础截断策略（向后兼容）
- advanced: 高级压缩策略（信息密度、语义压缩、列表压缩）
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class CompressionLevel(Enum):
    """压缩级别"""
    BASIC = "basic"      # 基础截断（向后兼容）
    ADVANCED = "advanced"  # 高级压缩


class CompressionStrategy(Enum):
    """压缩策略"""
    DENSITY = "density"      # 信息密度排名
    SEMANTIC = "semantic"    # 语义压缩
    LIST = "list"           # 列表压缩


@dataclass
class CompressionResult:
    """压缩结果"""
    original_length: int
    compressed_length: int
    reduction_ratio: float
    strategy: str
    preserved_keywords: List[str] = field(default_factory=list)


class AdvancedContextCompressor:
    """高级上下文压缩器

    实现文档中描述的压缩策略：
    - 信息密度排名
    - 语义压缩
    - 列表压缩
    - 关键词保留
    """

    # 默认保留关键词
    DEFAULT_KEYWORDS = [
        "must", "should", "require", "ensure",
        "critical", "important", "essential",
        "verify", "validate", "confirm",
        "security", "authentication", "authorization"
    ]

    def __init__(
        self,
        target_ratio: float = 0.5,
        preserve_keywords: bool = True,
        custom_keywords: Optional[List[str]] = None,
        strategies: Optional[List[CompressionStrategy]] = None
    ):
        """初始化压缩器

        Args:
            target_ratio: 目标压缩比例 (0.5 = 保留50%)
            preserve_keywords: 是否保留关键词
            custom_keywords: 自定义关键词
            strategies: 使用的压缩策略
        """
        self.target_ratio = target_ratio
        self.preserve_keywords = preserve_keywords
        self.keywords = set(DEFAULT_KEYWORDS + (custom_keywords or []))
        self.strategies = strategies or [
            CompressionStrategy.DENSITY,
            CompressionStrategy.SEMANTIC,
            CompressionStrategy.LIST
        ]
        self.compressions_count = 0
        self.tokens_saved = 0

    def compress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """压缩上下文

        Args:
            context: 上下文字典

        Returns:
            压缩后的上下文字典
        """
        if not context:
            return context

        self.compressions_count += 1
        original_tokens = self._estimate_tokens(context)

        compressed = {}
        priority_keys = ["requirements", "specification", "description", "constraints"]

        # 压缩优先级字段
        for key in priority_keys:
            if key in context:
                value = str(context[key])
                if len(value) > 1000:
                    compressed[key] = self._compress_text(value, key)
                else:
                    compressed[key] = value

        # 压缩其他字段
        for key, value in context.items():
            if key not in compressed:
                if isinstance(value, list):
                    compressed[key] = self._compress_list(value)
                else:
                    str_value = str(value)
                    if len(str_value) > 500:
                        compressed[key] = self._compress_text(str_value, key, max_length=500)
                    else:
                        compressed[key] = str_value

        saved_tokens = original_tokens - self._estimate_tokens(compressed)
        self.tokens_saved += saved_tokens

        return compressed

    def compress_with_stats(self, text: str) -> CompressionResult:
        """压缩文本并返回统计信息

        Args:
            text: 要压缩的文本

        Returns:
            CompressionResult 包含压缩统计
        """
        original_length = len(text)
        compressed = self._compress_text(text, "general")
        compressed_length = len(compressed)

        return CompressionResult(
            original_length=original_length,
            compressed_length=compressed_length,
            reduction_ratio=1.0 - (compressed_length / original_length) if original_length > 0 else 0,
            strategy="advanced",
            preserved_keywords=self._extract_preserved_keywords(text)
        )

    def calculate_density(self, text: str) -> float:
        """计算信息密度

        密度 = 唯一词数 / 总词数

        Args:
            text: 输入文本

        Returns:
            信息密度 (0.0 - 1.0)
        """
        words = text.lower().split()
        if not words:
            return 0.0
        unique_words = set(words)
        return len(unique_words) / len(words)

    def semantic_compress(self, text: str) -> str:
        """语义压缩

        保留：
        - 前 20%（引言、概述）
        - 中间的关键句
        - 后 20%（结论、总结）

        Args:
            text: 输入文本

        Returns:
            压缩后的文本
        """
        sentences = self._split_sentences(text)
        if len(sentences) <= 3:
            return text

        n = len(sentences)
        first_end = max(1, int(n * 0.2))
        last_start = max(first_end, int(n * 0.8))

        # 保留首尾
        kept = sentences[:first_end] + sentences[last_start:]

        # 从中间提取关键句
        middle = sentences[first_end:last_start]
        key_sentences = self._extract_key_sentences(middle)
        kept.extend(key_sentences)

        return ". ".join(kept)

    def compress_list(self, items: List[str]) -> List[str]:
        """压缩列表

        保留：
        - 前 2 个
        - 后 2 个
        - 包含关键词的项

        Args:
            items: 列表项

        Returns:
            压缩后的列表
        """
        if len(items) <= 4:
            return items

        kept = items[:2] + items[-2:]

        # 添加包含关键词的中间项
        keywords_lower = [kw.lower() for kw in self.keywords]
        for item in items[2:-2]:
            item_lower = str(item).lower()
            if any(kw in item_lower for kw in keywords_lower):
                if item not in kept:
                    kept.append(item)

        return kept

    def _compress_text(self, text: str, field_name: str, max_length: int = 1000) -> str:
        """压缩文本

        根据配置的策略压缩文本
        """
        if len(text) <= max_length:
            return text

        # 使用语义压缩
        if CompressionStrategy.SEMANTIC in self.strategies:
            compressed = self.semantic_compress(text)
            if len(compressed) <= max_length:
                return compressed
            text = compressed

        # 截断到目标长度
        return text[:max_length] + "... [truncated]"

    def _compress_list(self, items: List[Any]) -> List[Any]:
        """压缩列表"""
        if not items or len(items) <= 3:
            return items

        # 转换为字符串列表
        str_items = [str(item) for item in items]

        if CompressionStrategy.LIST in self.strategies:
            compressed = self.compress_list(str_items)
            return compressed

        # 默认：保留首尾
        return str_items[:2] + str_items[-2:]

    def _split_sentences(self, text: str) -> List[str]:
        """分割文本为句子"""
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[.!?]+\s*', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_key_sentences(self, sentences: List[str]) -> List[str]:
        """提取关键句

        包含关键词的句子被认为是关键的
        """
        keywords_lower = [kw.lower() for kw in self.keywords]
        key_sentences = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(kw in sentence_lower for kw in keywords_lower):
                key_sentences.append(sentence)

        return key_sentences[:3]  # 最多保留 3 个关键句

    def _extract_preserved_keywords(self, text: str) -> List[str]:
        """提取文本中存在的保留关键词"""
        found = []
        text_lower = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)
        return found

    def _estimate_tokens(self, data: Any) -> int:
        """估算 token 数量"""
        text = str(data)
        return len(text) // 4  # 简单估算：4 字符/token

    def get_stats(self) -> Dict[str, Any]:
        """获取压缩统计"""
        return {
            "total_compressions": self.compressions_count,
            "tokens_saved": self.tokens_saved,
            "strategies": [s.value for s in self.strategies],
            "target_ratio": self.target_ratio
        }


class ContextCompressor:
    """上下文压缩器（兼容层）

    默认使用基础压缩策略（向后兼容），
    可通过设置切换到高级策略。
    """

    def __init__(self, target_tokens: int = 4000, level: CompressionLevel = CompressionLevel.BASIC):
        """初始化压缩器

        Args:
            target_tokens: 目标 token 数量
            level: 压缩级别 (basic 或 advanced)
        """
        self._target_tokens = target_tokens
        self.level = level

        # 根据级别选择底层实现
        if level == CompressionLevel.ADVANCED:
            self._compressor = AdvancedContextCompressor(target_ratio=0.5)
        else:
            self._compressor = _BasicCompressor(target_tokens)

    def compress(self, context: Dict[str, Any], max_tokens: int = 4000) -> Dict[str, Any]:
        """压缩上下文

        Args:
            context: 上下文字典
            max_tokens: 最大 token 数量

        Returns:
            压缩后的上下文字典
        """
        return self._compressor.compress(context, max_tokens)

    def get_stats(self) -> Dict[str, int]:
        """获取压缩统计"""
        return self._compressor.get_stats()

    @property
    def compressions_count(self) -> int:
        """获取压缩次数（向后兼容）"""
        return self._compressor.compressions_count

    @property
    def tokens_saved(self) -> int:
        """获取节省的 token 数（向后兼容）"""
        return self._compressor.tokens_saved

    @property
    def target_tokens(self) -> int:
        """获取目标 token 数"""
        return self._target_tokens

    def _estimate_tokens(self, data: Any) -> int:
        """估算 token 数量（向后兼容）"""
        return self._compressor._estimate_tokens(data)


class _BasicCompressor:
    """基础压缩器（原实现）

    保持向后兼容性。
    """

    def __init__(self, target_tokens: int = 4000):
        self.target_tokens = target_tokens
        self.compressions_count = 0
        self.tokens_saved = 0

    def compress(self, context: Dict[str, Any], max_tokens: int = 4000) -> Dict[str, Any]:
        """压缩上下文（基础策略）

        Priority fields (requirements, specification, description) are preserved
        with a 1000 character limit. Other fields are limited to 3 items with
        a 500 character limit each.
        """
        if not context:
            return context

        self.compressions_count += 1
        original_tokens = self._estimate_tokens(context)

        # 简化策略：保留关键字段，截断长文本
        compressed = {}
        priority_keys = ["requirements", "specification", "description"]

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
        return len(text) // 4

    def get_stats(self) -> Dict[str, int]:
        """获取压缩统计"""
        return {
            "total_compressions": self.compressions_count,
            "tokens_saved": self.tokens_saved
        }
