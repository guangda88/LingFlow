"""
LingFlow Enhanced Message Scorer - 增强版消息评分器

使用更复杂的评分算法（TF-IDF）
"""

import re
import math
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter

from .message_scorer import MessageScorer, MessageScore

logger = logging.getLogger(__name__)


@dataclass
class MessageContext:
    """消息上下文"""
    previous_messages: List[Dict]
    next_messages: List[Dict]
    conversation_topic: Optional[str]
    user_intent: Optional[str]


class EnhancedMessageScorer(MessageScorer):
    """增强版消息评分器"""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        super().__init__(weights)

        # IDF 统计
        self._document_count = 0
        self._word_document_count = Counter()
        self._idf_cache = {}

    def train_idf(self, messages: List[Dict]):
        """
        训练 IDF 模型

        Args:
            messages: 训练消息列表
        """
        logger.info(f"Training IDF model with {len(messages)} messages")

        self._document_count = len(messages)
        word_counts = Counter()

        for msg in messages:
            content = msg.get("content", "")
            words = self._extract_words(content)
            unique_words = set(words)
            word_counts.update(unique_words)

        self._word_document_count = word_counts
        self._idf_cache.clear()

        logger.info(f"IDF training complete: {len(word_counts)} unique words")

    def _extract_words(self, content: str) -> List[str]:
        """
        提取词语

        Args:
            content: 文本内容

        Returns:
            词语列表
        """
        # 转换为小写
        content = content.lower()

        # 移除代码块
        content = re.sub(r'```[\s\S]*?```', '', content)

        # 分词（简单实现，按空格和标点分割）
        words = re.findall(r'\b\w+\b', content)

        # 过滤停用词
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }

        return [w for w in words if len(w) > 2 and w not in stopwords]

    def _calculate_tf(self, content: str) -> Dict[str, float]:
        """
        计算 TF (Term Frequency)

        Args:
            content: 文本内容

        Returns:
            词频字典
        """
        words = self._extract_words(content)
        word_count = len(words)

        if word_count == 0:
            return {}

        tf = Counter(words)
        # 归一化
        return {word: count / word_count for word, count in tf.items()}

    def _calculate_idf(self, word: str) -> float:
        """
        计算 IDF (Inverse Document Frequency)

        Args:
            word: 词语

        Returns:
            IDF 值
        """
        if word in self._idf_cache:
            return self._idf_cache[word]

        if self._document_count == 0:
            return 0.0

        doc_count = self._word_document_count.get(word, 0)
        if doc_count == 0:
            idf = 0.0
        else:
            idf = math.log(self._document_count / (1 + doc_count))

        self._idf_cache[word] = idf
        return idf

    def _calculate_tfidf(self, content: str) -> float:
        """
        计算 TF-IDF 得分

        Args:
            content: 文本内容

        Returns:
            TF-IDF 得分
        """
        tf = self._calculate_tf(content)

        if not tf:
            return 0.0

        # 计算 TF-IDF
        tfidf_sum = 0.0
        for word, tf_value in tf.items():
            idf = self._calculate_idf(word)
            tfidf_sum += tf_value * idf

        # 归一化
        return tfidf_sum / len(tf) if tf else 0.0

    def score_with_context(
        self,
        content: str,
        role: str = "user",
        context: Optional[MessageContext] = None
    ) -> MessageScore:
        """
        带上下文的消息评分

        Args:
            content: 消息内容
            role: 消息角色
            context: 消息上下文

        Returns:
            消息评分
        """
        # 基础评分
        base_score = super().score(content, role, context)

        # TF-IDF 评分
        tfidf_score = self._calculate_tfidf(content)

        # 归一化 TF-IDF 到 0-1
        normalized_tfidf = min(tfidf_score / 2.0, 1.0)

        # 上下文相关性
        context_score = 0.5
        if context and context.previous_messages:
            context_score = self._calculate_context_relevance(
                content,
                context.previous_messages
            )

        # 综合评分
        final_importance = (
            base_score.importance_score * 0.5 +
            normalized_tfidf * 0.3 +
            context_score * 0.2
        )

        # 生成推理
        reasoning_parts = base_score.reasoning.split(", ")
        if normalized_tfidf > 0.3:
            reasoning_parts.append(f"TF-IDF: {normalized_tfidf:.2f}")
        if context_score > 0.7:
            reasoning_parts.append("high context relevance")

        return MessageScore(
            importance_score=min(final_importance, 1.0),
            relevance_score=base_score.relevance_score,
            time_score=base_score.time_score,
            quality_score=base_score.quality_score,
            reasoning=", ".join(reasoning_parts)
        )

    def _calculate_context_relevance(
        self,
        content: str,
        previous_messages: List[Dict]
    ) -> float:
        """
        计算上下文相关性

        Args:
            content: 当前消息
            previous_messages: 之前的消息

        Returns:
            相关性得分 (0-1)
        """
        if not previous_messages:
            return 0.5

        # 提取当前消息的词语
        current_words = set(self._extract_words(content))

        if not current_words:
            return 0.5

        # 检查最近的消息
        recent_messages = previous_messages[-5:] if len(previous_messages) > 5 else previous_messages
        relevance_scores = []

        for prev_msg in recent_messages:
            prev_content = prev_msg.get("content", "")
            prev_words = set(self._extract_words(prev_content))

            # 计算词汇重叠
            if prev_words:
                overlap = current_words & prev_words
                union = current_words | prev_words
                jaccard = len(overlap) / len(union) if union else 0
                relevance_scores.append(jaccard)

        if relevance_scores:
            return max(relevance_scores)

        return 0.0

    def batch_score_with_context(
        self,
        messages: List[Dict],
        use_context: bool = True
    ) -> List[MessageScore]:
        """
        批量评分（带上下文）

        Args:
            messages: 消息列表
            use_context: 是否使用上下文

        Returns:
            评分列表
        """
        # 先训练 IDF（如果未训练）
        if self._document_count == 0:
            self.train_idf(messages)

        results = []

        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            role = msg.get("role", "user")

            # 构建上下文
            message_context = None
            if use_context:
                message_context = MessageContext(
                    previous_messages=messages[:i] if i > 0 else [],
                    next_messages=messages[i+1:] if i < len(messages) - 1 else [],
                    conversation_topic=None,
                    user_intent=None
                )

            # 评分
            score = self.score_with_context(content, role, message_context)
            results.append(score)

        return results

    def get_importance_breakdown(self, score: MessageScore) -> Dict[str, float]:
        """
        获取重要性评分的详细分解

        Args:
            score: 消息评分

        Returns:
            详细分解
        """
        return {
            "importance": score.importance_score,
            "relevance": score.relevance_score,
            "time": score.time_score,
            "quality": score.quality_score,
            "breakdown": score.reasoning
        }
