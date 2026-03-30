"""
LingFlow Message Scorer

多维度评分系统，评估消息的重要性
"""

import re
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MessageScore:
    """消息评分结果"""
    importance_score: float  # 总体重要性评分 (0-1)
    relevance_score: float   # 相关性评分 (0-1)
    time_score: float        # 时效性评分 (0-1)
    quality_score: float     # 质量评分 (0-1)
    reasoning: str           # 评分理由


class MessageScorer:
    """消息评分器"""

    # 关键词权重
    IMPORTANCE_KEYWORDS = {
        "high": [
            "error", "bug", "fix", "critical", "urgent", "important",
            "错误", "修复", "关键", "紧急", "重要", "失败"
        ],
        "medium": [
            "question", "help", "how", "what", "why", "问题",
            "帮助", "如何", "什么", "为什么"
        ],
        "low": [
            "ok", "yes", "no", "thanks", "good", "好的",
            "谢谢", "可以", "确定"
        ]
    }

    # 代码相关权重
    CODE_PATTERNS = [
        r"```[\s\S]*?```",  # 代码块
        r"`[^`]+`",          # 行内代码
        r"def\s+\w+\s*\(",  # 函数定义
        r"class\s+\w+",      # 类定义
        r"import\s+\w+",     # 导入语句
    ]

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化消息评分器

        Args:
            weights: 评分权重，默认为均衡权重
        """
        self.weights = weights or {
            "relevance": 0.4,
            "time": 0.2,
            "quality": 0.3,
            "keywords": 0.1
        }
        logger.info(f"MessageScorer initialized with weights: {self.weights}")

    def score(
        self,
        content: str,
        role: str = "user",
        context: Optional[Dict] = None
    ) -> MessageScore:
        """
        评估消息的重要性

        Args:
            content: 消息内容
            role: 消息角色 (user, assistant, system, tool)
            context: 上下文信息

        Returns:
            消息评分结果
        """
        if not content:
            return MessageScore(
                importance_score=0.0,
                relevance_score=0.0,
                time_score=0.0,
                quality_score=0.0,
                reasoning="Empty message"
            )

        # 计算各维度评分
        relevance = self._score_relevance(content, role, context)
        time_score = self._score_time(content, context)
        quality = self._score_quality(content, role)
        keywords = self._score_keywords(content)

        # 计算总体重要性评分
        importance = (
            relevance * self.weights["relevance"] +
            time_score * self.weights["time"] +
            quality * self.weights["quality"] +
            keywords * self.weights["keywords"]
        )

        # 生成评分理由
        reasoning = self._generate_reasoning(
            relevance, time_score, quality, keywords, content
        )

        return MessageScore(
            importance_score=round(importance, 3),
            relevance_score=round(relevance, 3),
            time_score=round(time_score, 3),
            quality_score=round(quality, 3),
            reasoning=reasoning
        )

    def _score_relevance(
        self,
        content: str,
        role: str,
        context: Optional[Dict]
    ) -> float:
        """
        评估消息相关性

        Args:
            content: 消息内容
            role: 消息角色
            context: 上下文信息

        Returns:
            相关性评分 (0-1)
        """
        score = 0.5  # 基础分

        # 角色权重
        if role == "user":
            score += 0.3  # 用户消息更重要
        elif role == "system":
            score += 0.2  # 系统消息次之
        elif role == "tool":
            score += 0.1  # 工具消息较低
        # assistant 消息保持基础分

        # 内容长度（太短或太长都可能降低相关性）
        length = len(content)
        if 50 <= length <= 1000:
            score += 0.1  # 适中长度加分
        elif length > 2000:
            score -= 0.1  # 过长可能冗余

        # 代码内容加分
        if self._contains_code(content):
            score += 0.1

        # 上下文相关性
        if context:
            # 如果有对话历史，检查是否与前文相关
            if "previous_messages" in context:
                prev_msgs = context["previous_messages"]
                if prev_msgs and self._is_contextual(content, prev_msgs):
                    score += 0.1

        return min(max(score, 0.0), 1.0)

    def _score_time(self, content: str, context: Optional[Dict]) -> float:
        """
        评估消息时效性

        Args:
            content: 消息内容
            context: 上下文信息（应包含时间戳）

        Returns:
            时效性评分 (0-1)
        """
        # 默认为较新的消息
        score = 0.7

        if context and "timestamp" in context:
            timestamp = context["timestamp"]
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except:
                    timestamp = datetime.now()

            # 计算消息年龄
            age = datetime.now() - timestamp

            # 新鲜度评分（越新越高）
            if age < timedelta(minutes=5):
                score = 1.0
            elif age < timedelta(minutes=15):
                score = 0.8
            elif age < timedelta(hours=1):
                score = 0.6
            elif age < timedelta(hours=6):
                score = 0.4
            else:
                score = 0.2

        return score

    def _score_quality(self, content: str, role: str) -> float:
        """
        评估消息质量

        Args:
            content: 消息内容
            role: 消息角色

        Returns:
            质量评分 (0-1)
        """
        score = 0.5

        # 内容质量指标
        if content:
            # 避免简单的确认语
            simple_responses = ["ok", "yes", "no", "好的", "可以", "确定"]
            if content.lower().strip() in simple_responses:
                score -= 0.3

            # 避免过短的消息
            if len(content) < 10:
                score -= 0.2
            elif len(content) > 50:
                score += 0.2

            # 结构化内容加分
            if self._has_structure(content):
                score += 0.2

            # 专业性加分
            if self._is_professional(content):
                score += 0.1

        return min(max(score, 0.0), 1.0)

    def _score_keywords(self, content: str) -> float:
        """
        基于关键词评分

        Args:
            content: 消息内容

        Returns:
            关键词评分 (0-1)
        """
        score = 0.5
        content_lower = content.lower()

        # 高重要性关键词
        high_count = sum(
            1 for keyword in self.IMPORTANCE_KEYWORDS["high"]
            if keyword in content_lower
        )
        if high_count > 0:
            score += min(high_count * 0.2, 0.4)

        # 中等重要性关键词
        medium_count = sum(
            1 for keyword in self.IMPORTANCE_KEYWORDS["medium"]
            if keyword in content_lower
        )
        if medium_count > 0:
            score += min(medium_count * 0.1, 0.2)

        # 低重要性关键词
        low_count = sum(
            1 for keyword in self.IMPORTANCE_KEYWORDS["low"]
            if keyword in content_lower
        )
        if low_count > 0:
            score -= min(low_count * 0.1, 0.2)

        return min(max(score, 0.0), 1.0)

    def _contains_code(self, content: str) -> bool:
        """检查内容是否包含代码"""
        return any(re.search(pattern, content) for pattern in self.CODE_PATTERNS)

    def _has_structure(self, content: str) -> bool:
        """检查内容是否有结构"""
        # 检查是否有列表、编号、标题等
        patterns = [
            r"^\s*[-*+]\s+",  # 列表
            r"^\s*\d+\.\s+",  # 编号列表
            r"^#+\s+",        # 标题
            r"```\s*\w*",     # 代码块
        ]
        return any(re.search(pattern, content, re.MULTILINE) for pattern in patterns)

    def _is_professional(self, content: str) -> bool:
        """检查内容是否专业"""
        # 检查是否包含专业术语或详细解释
        professional_indicators = [
            "because", "therefore", "however", "thus",
            "因为", "所以", "但是", "因此"
        ]
        return any(indicator in content.lower() for indicator in professional_indicators)

    def _is_contextual(self, content: str, previous_messages: List[Dict]) -> bool:
        """检查是否与上下文相关"""
        if not previous_messages:
            return False

        # 简单的词汇重叠检查
        content_words = set(content.lower().split())
        for msg in previous_messages[-3:]:  # 检查最近3条消息
            msg_words = set(msg.get("content", "").lower().split())
            overlap = content_words & msg_words
            if len(overlap) > 2:  # 有2个以上词汇重叠
                return True

        return False

    def _generate_reasoning(
        self,
        relevance: float,
        time_score: float,
        quality: float,
        keywords: float,
        content: str
    ) -> str:
        """生成评分理由"""
        reasons = []

        if relevance > 0.7:
            reasons.append("highly relevant")
        elif relevance < 0.4:
            reasons.append("less relevant")

        if time_score > 0.8:
            reasons.append("recent")
        elif time_score < 0.4:
            reasons.append("old")

        if quality > 0.7:
            reasons.append("high quality")
        elif quality < 0.4:
            reasons.append("low quality")

        if keywords > 0.7:
            reasons.append("contains important keywords")
        elif keywords < 0.4:
            reasons.append("routine message")

        # 添加特殊原因
        if self._contains_code(content):
            reasons.append("contains code")

        if len(content) > 1000:
            reasons.append("detailed")
        elif len(content) < 20:
            reasons.append("brief")

        return ", ".join(reasons) if reasons else "standard message"

    def batch_score(
        self,
        messages: List[Dict],
        context: Optional[Dict] = None
    ) -> List[MessageScore]:
        """
        批量评分消息

        Args:
            messages: 消息列表
            context: 上下文信息

        Returns:
            评分结果列表
        """
        return [
            self.score(
                msg.get("content", ""),
                msg.get("role", "user"),
                context
            )
            for msg in messages
        ]

    def get_importance_summary(
        self,
        scores: List[MessageScore]
    ) -> Dict[str, any]:
        """
        获取重要性摘要

        Args:
            scores: 评分列表

        Returns:
            摘要统计
        """
        if not scores:
            return {
                "total": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "avg_importance": 0.0
            }

        high_count = sum(1 for s in scores if s.importance_score > 0.7)
        medium_count = sum(1 for s in scores if 0.4 <= s.importance_score <= 0.7)
        low_count = sum(1 for s in scores if s.importance_score < 0.4)
        avg_importance = sum(s.importance_score for s in scores) / len(scores)

        return {
            "total": len(scores),
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
            "avg_importance": round(avg_importance, 3)
        }


# 全局实例
_scorer: Optional[MessageScorer] = None


def get_message_scorer(weights: Optional[Dict[str, float]] = None) -> MessageScorer:
    """
    获取消息评分器实例（单例模式）

    Args:
        weights: 评分权重

    Returns:
        消息评分器实例
    """
    global _scorer
    if _scorer is None or weights is not None:
        _scorer = MessageScorer(weights)
    return _scorer


__all__ = [
    "MessageScorer",
    "MessageScore",
    "get_message_scorer"
]
