"""消息评分模块

提供消息重要性评分功能。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class MessageScore:
    """消息评分结果

    Attributes:
        score: 重要性分数 (0-1)
        factors: 影响评分的因素
        timestamp: 评分时间
    """
    score: float
    factors: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"MessageScore(score={self.score:.2f}, factors={self.factors})"


class MessageScorer:
    """消息重要性评分器

    多维度评分系统：
    1. 角色权重 - system/user/assistant 消息重要性不同
    2. 时间衰减 - 最近的对话更重要
    3. 长度权重 - 较长的消息可能包含更多信息
    4. 关键词匹配 - 包含重要关键词的消息
    5. 交互质量 - 问答配对的重要性
    """

    # 角色默认权重
    ROLE_WEIGHTS = {
        MessageRole.SYSTEM: 1.0,      # 系统提示最重要
        MessageRole.USER: 0.8,         # 用户提问重要
        MessageRole.ASSISTANT: 0.6,    # 助手回复相对次要
        MessageRole.FUNCTION: 0.4,     # 函数调用最次要
    }

    # 关键词及其权重
    KEYWORD_WEIGHTS = {
        # 错误相关
        "error": 1.5,
        "exception": 1.5,
        "bug": 1.4,
        "fail": 1.3,

        # 重要指令
        "必须": 1.3,
        "require": 1.3,
        "critical": 1.4,
        "important": 1.2,

        # 代码相关
        "code": 1.1,
        "function": 1.0,
        "class": 1.0,
        "implement": 1.2,

        # 问题相关
        "问题": 1.2,
        "question": 1.1,
        "how": 1.1,
        "为什么": 1.2,
    }

    def __init__(
        self,
        role_weights: Optional[Dict[MessageRole, float]] = None,
        keyword_weights: Optional[Dict[str, float]] = None,
        time_half_life: float = 3600.0  # 1小时半衰期
    ):
        """初始化消息评分器

        Args:
            role_weights: 角色权重配置
            keyword_weights: 关键词权重配置
            time_half_life: 时间衰减半衰期（秒）
        """
        self.role_weights = role_weights or self.ROLE_WEIGHTS
        self.keyword_weights = keyword_weights or self.KEYWORD_WEIGHTS
        self.time_half_life = time_half_life

    def score_message(
        self,
        message: Dict,
        context: Optional[Dict] = None
    ) -> MessageScore:
        """对单条消息评分

        Args:
            message: 消息对象
            context: 上下文信息（如对话历史）

        Returns:
            消息评分结果
        """
        factors = {}

        # 1. 角色评分
        role_score = self._score_role(message)
        factors["role"] = role_score

        # 2. 时间衰减评分
        time_score = self._score_time(message)
        factors["time"] = time_score

        # 3. 长度评分
        length_score = self._score_length(message)
        factors["length"] = length_score

        # 4. 关键词评分
        keyword_score = self._score_keywords(message)
        factors["keywords"] = keyword_score

        # 5. 交互质量评分
        interaction_score = self._score_interaction(message, context)
        factors["interaction"] = interaction_score

        # 计算加权总分
        total_score = (
            role_score * 0.3 +
            time_score * 0.2 +
            length_score * 0.15 +
            keyword_score * 0.2 +
            interaction_score * 0.15
        )

        # 归一化到 0-1
        total_score = min(max(total_score, 0.0), 1.0)

        return MessageScore(score=total_score, factors=factors)

    def score_messages(
        self,
        messages: List[Dict],
        context: Optional[Dict] = None
    ) -> List[MessageScore]:
        """对消息列表评分

        Args:
            messages: 消息列表
            context: 上下文信息

        Returns:
            评分结果列表
        """
        return [
            self.score_message(msg, context)
            for msg in messages
        ]

    def _score_role(self, message: Dict) -> float:
        """评分：消息角色

        Args:
            message: 消息对象

        Returns:
            角色评分 (0-1)
        """
        role_str = message.get("role", "user")
        try:
            role = MessageRole(role_str)
        except ValueError:
            role = MessageRole.USER

        return self.role_weights.get(role, 0.5)

    def _score_time(self, message: Dict) -> float:
        """评分：时间衰减

        Args:
            message: 消息对象

        Returns:
            时间评分 (0-1)
        """
        # 没有时间戳，给予中性评分
        if "timestamp" not in message:
            return 0.5

        try:
            timestamp_str = message["timestamp"]
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = timestamp_str

            # 计算时间差
            age = (datetime.now() - timestamp).total_seconds()

            # 指数衰减
            decay = 2.0 ** (-age / self.time_half_life)
            return float(decay)

        except Exception as e:
            logger.debug(f"时间评分失败: {e}")
            return 0.5

    def _score_length(self, message: Dict) -> float:
        """评分：消息长度

        Args:
            message: 消息对象

        Returns:
            长度评分 (0-1)
        """
        content = message.get("content", "")
        length = len(content)

        # 使用对数刻度，避免过长消息权重过高
        if length == 0:
            return 0.0

        # 归一化：0-2000字符映射到0-1
        import math
        normalized = min(math.log1p(length) / math.log1p(2000), 1.0)
        return float(normalized)

    def _score_keywords(self, message: Dict) -> float:
        """评分：关键词匹配

        Args:
            message: 消息对象

        Returns:
            关键词评分 (0-1)
        """
        content = message.get("content", "").lower()

        if not content:
            return 0.0

        # 计算关键词得分
        total_weight = 0.0
        matched_keywords = 0

        for keyword, weight in self.keyword_weights.items():
            if keyword.lower() in content:
                total_weight += weight
                matched_keywords += 1

        # 归一化
        if matched_keywords == 0:
            return 0.0

        # 基础分 + 关键词加成
        base_score = min(matched_keywords * 0.1, 0.5)
        weight_score = min(total_weight * 0.1, 0.5)

        return base_score + weight_score

    def _score_interaction(
        self,
        message: Dict,
        context: Optional[Dict] = None
    ) -> float:
        """评分：交互质量

        检查是否形成良好的问答配对。

        Args:
            message: 消息对象
            context: 上下文信息

        Returns:
            交互评分 (0-1)
        """
        if not context:
            return 0.5

        # 检查是否是好的回答
        if message.get("role") == "assistant":
            content = message.get("content", "")
            # 好的回答应该有实质内容
            if len(content) > 50:
                return 0.8
            elif len(content) > 20:
                return 0.6
            else:
                return 0.3

        # 用户消息检查是否有明确问题
        if message.get("role") == "user":
            content = message.get("content", "")
            question_indicators = ["?", "？", "如何", "怎么", "what", "how", "why"]
            if any(indicator in content for indicator in question_indicators):
                return 0.8
            else:
                return 0.5

        return 0.5
