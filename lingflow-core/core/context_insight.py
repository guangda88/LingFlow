"""
LingFlow Context Insight

提供上下文状态分析和洞察
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .token_estimator import TokenEstimator, get_token_estimator
from .message_scorer import MessageScorer, get_message_scorer
from .compression_strategy import TieredCompressionStrategy, get_compression_strategy

# SQLite 上下文管理器
try:
    from .sqlite_context_manager import (
        SQLiteContextManager,
        get_context_manager,
        Message,
        Conversation
    )
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    SQLiteContextManager = None
    get_context_manager = None
    Message = None
    Conversation = None

logger = logging.getLogger(__name__)


@dataclass
class ContextInsight:
    """上下文洞察结果"""
    total_tokens: int
    message_count: int
    important_messages: int
    can_compress: bool
    compression_recommendation: Optional[Dict[str, Any]]
    recommendations: List[str]
    health_status: str  # "healthy", "warning", "critical"
    details: Dict[str, Any]


class ContextInsightProvider:
    """上下文洞察提供者"""

    def __init__(
        self,
        token_estimator: Optional[TokenEstimator] = None,
        message_scorer: Optional[MessageScorer] = None,
        compression_strategy: Optional[TieredCompressionStrategy] = None,
        use_sqlite: bool = True,
        db_path: str = ":memory:"
    ):
        """
        初始化上下文洞察提供者

        Args:
            token_estimator: Token 估算器
            message_scorer: 消息评分器
            compression_strategy: 压缩策略
            use_sqlite: 是否使用 SQLite 存储
            db_path: 数据库路径
        """
        self.token_estimator = token_estimator or get_token_estimator()
        self.message_scorer = message_scorer or get_message_scorer()
        self.compression_strategy = compression_strategy or get_compression_strategy()

        self.use_sqlite = use_sqlite and SQLITE_AVAILABLE
        if self.use_sqlite:
            self.context_manager = get_context_manager(db_path)
            self.context_manager.initialize_database()  # 初始化数据库
            logger.info(f"ContextInsightProvider initialized with SQLite at {db_path}")
        else:
            self.context_manager = None
            logger.info("ContextInsightProvider initialized without SQLite")

    def analyze(
        self,
        messages: List[Dict],
        threshold: int = 150000
    ) -> ContextInsight:
        """
        分析上下文状态

        Args:
            messages: 消息列表
            threshold: token 阈值

        Returns:
            上下文洞察结果
        """
        # 计算 token 数量
        token_estimate = self.token_estimator.estimate_messages(messages)

        # 评分消息
        scores = self.message_scorer.batch_score(messages)
        important_count = sum(1 for s in scores if s.importance_score > 0.7)

        # 判断是否可以压缩
        can_compress = token_estimate.token_count > threshold

        # 获取压缩建议
        compression_rec = None
        if can_compress:
            compression_rec = self.compression_strategy.get_compression_recommendation(
                messages,
                threshold
            )

        # 生成建议
        recommendations = self._generate_recommendations(
            messages,
            token_estimate.token_count,
            threshold,
            scores,
            compression_rec
        )

        # 计算健康状态
        health_status = self._calculate_health_status(
            token_estimate.token_count,
            threshold
        )

        # 收集详细信息
        details = self._collect_details(messages, scores, token_estimate)

        return ContextInsight(
            total_tokens=token_estimate.token_count,
            message_count=len(messages),
            important_messages=important_count,
            can_compress=can_compress,
            compression_recommendation=compression_rec,
            recommendations=recommendations,
            health_status=health_status,
            details=details
        )

    def _generate_recommendations(
        self,
        messages: List[Dict],
        token_count: int,
        threshold: int,
        scores: List,
        compression_rec: Optional[Dict]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        # Token 使用建议
        if token_count > threshold:
            recommendations.append(
                f"⚠️  Token count ({token_count:,}) exceeds threshold ({threshold:,})"
            )
        elif token_count > threshold * 0.8:
            recommendations.append(
                f"⚡ Token count ({token_count:,}) approaching threshold ({threshold:,})"
            )
        else:
            recommendations.append(
                f"✅ Token count ({token_count:,}) within safe limits"
            )

        # 压缩建议
        if compression_rec and compression_rec.get("should_compress"):
            strategy = compression_rec.get("recommended_strategy")
            recommendations.append(
                f"🗜️  Consider compression using '{strategy}' strategy"
            )

        # 消息质量建议
        low_quality = sum(1 for s in scores if s.importance_score < 0.3)
        if low_quality > 5:
            recommendations.append(
                f"🧹 {low_quality} low-importance messages could be removed"
            )

        # 会话长度建议
        if len(messages) > 100:
            recommendations.append(
                f"📝 Consider summarizing older messages ({len(messages)} total)"
            )

        return recommendations

    def _calculate_health_status(self, token_count: int, threshold: int) -> str:
        """计算健康状态"""
        ratio = token_count / threshold

        if ratio < 0.7:
            return "healthy"
        elif ratio < 0.9:
            return "warning"
        else:
            return "critical"

    def _collect_details(
        self,
        messages: List[Dict],
        scores: List,
        token_estimate
    ) -> Dict[str, Any]:
        """收集详细信息"""
        # 消息类型分布
        role_counts = {}
        for msg in messages:
            role = msg.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        # 重要性分布
        importance_dist = {
            "high": sum(1 for s in scores if s.importance_score > 0.7),
            "medium": sum(1 for s in scores if 0.4 <= s.importance_score <= 0.7),
            "low": sum(1 for s in scores if s.importance_score < 0.4)
        }

        # 平均评分
        avg_importance = sum(s.importance_score for s in scores) / len(scores) if scores else 0

        return {
            "role_distribution": role_counts,
            "importance_distribution": importance_dist,
            "average_importance": round(avg_importance, 3),
            "encoding": token_estimate.encoding,
            "model": token_estimate.model
        }

    def save_to_sqlite(
        self,
        session_id: str,
        messages: List[Dict],
        metadata: Optional[Dict] = None
    ) -> Optional[Conversation]:
        """
        保存会话到 SQLite

        Args:
            session_id: 会话 ID
            messages: 消息列表
            metadata: 元数据

        Returns:
            会话对象（如果 SQLite 可用）
        """
        if not self.use_sqlite or not self.context_manager:
            logger.warning("SQLite not available, skipping save")
            return None

        try:
            # 创建会话
            conv = self.context_manager.create_conversation(session_id, metadata)

            # 添加消息
            for msg_dict in messages:
                # 评分消息
                score = self.message_scorer.score(
                    msg_dict.get("content", ""),
                    msg_dict.get("role", "user")
                )

                # 创建消息对象
                msg = Message(
                    role=msg_dict.get("role", "user"),
                    content=msg_dict.get("content", ""),
                    token_count=self.token_estimator.estimate(
                        msg_dict.get("content", "")
                    ).token_count,
                    importance_score=score.importance_score,
                    metadata={
                        "relevance_score": score.relevance_score,
                        "time_score": score.time_score,
                        "quality_score": score.quality_score,
                        "reasoning": score.reasoning
                    }
                )

                self.context_manager.add_message(conv.id, msg)

            return conv

        except Exception as e:
            logger.error(f"Failed to save to SQLite: {e}")
            return None

    def get_sqlite_statistics(self, session_id: str) -> Optional[Dict]:
        """
        获取 SQLite 统计信息

        Args:
            session_id: 会话 ID

        Returns:
            统计信息（如果 SQLite 可用）
        """
        if not self.use_sqlite or not self.context_manager:
            return None

        try:
            conv = self.context_manager.get_conversation_by_session(session_id)
            if not conv:
                return None

            return self.context_manager.get_statistics(conv.id)

        except Exception as e:
            logger.error(f"Failed to get SQLite statistics: {e}")
            return None

    def compress_from_sqlite(
        self,
        session_id: str,
        target_tokens: int,
        strategy: str = "auto"
    ) -> Optional[Dict]:
        """
        从 SQLite 压缩会话

        Args:
            session_id: 会话 ID
            target_tokens: 目标 token 数量
            strategy: 压缩策略

        Returns:
            压缩结果（如果 SQLite 可用）
        """
        if not self.use_sqlite or not self.context_manager:
            return None

        try:
            conv = self.context_manager.get_conversation_by_session(session_id)
            if not conv:
                return None

            # 获取上下文状态
            state = self.context_manager.get_context_state(conv.id)
            if not state:
                return None

            # 获取低重要性消息
            low_importance_msgs = self.context_manager.get_low_importance_messages(
                conv.id,
                limit=50
            )

            if not low_importance_msgs:
                return {"message": "No messages to compress"}

            # 执行压缩
            removed_tokens = sum(msg.token_count for msg in low_importance_msgs)
            after_tokens = state['current_tokens'] - removed_tokens

            # 记录压缩
            self.context_manager.record_compression(
                conv.id,
                state['current_tokens'],
                after_tokens,
                len(low_importance_msgs),
                strategy,
                {"messages": [msg.id for msg in low_importance_msgs]}
            )

            # 标记为已压缩
            self.context_manager.mark_messages_compressed(
                [msg.id for msg in low_importance_msgs]
            )

            return {
                "before_tokens": state['current_tokens'],
                "after_tokens": after_tokens,
                "reduction_ratio": removed_tokens / state['current_tokens'],
                "messages_removed": len(low_importance_msgs)
            }

        except Exception as e:
            logger.error(f"Failed to compress from SQLite: {e}")
            return None


# 全局实例
_insight_provider: Optional[ContextInsightProvider] = None


def get_context_insight_provider(
    token_estimator: Optional[TokenEstimator] = None,
    message_scorer: Optional[MessageScorer] = None,
    compression_strategy: Optional[TieredCompressionStrategy] = None,
    use_sqlite: bool = True,
    db_path: str = ":memory:"
) -> ContextInsightProvider:
    """
    获取上下文洞察提供者实例（单例模式）

    Args:
        token_estimator: Token 估算器
        message_scorer: 消息评分器
        compression_strategy: 压缩策略
        use_sqlite: 是否使用 SQLite
        db_path: 数据库路径

    Returns:
        上下文洞察提供者实例
    """
    global _insight_provider
    if _insight_provider is None:
        _insight_provider = ContextInsightProvider(
            token_estimator,
            message_scorer,
            compression_strategy,
            use_sqlite,
            db_path
        )
    return _insight_provider


__all__ = [
    "ContextInsightProvider",
    "ContextInsight",
    "get_context_insight_provider",
    "SQLITE_AVAILABLE"
]
