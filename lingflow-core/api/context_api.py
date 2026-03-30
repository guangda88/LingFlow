"""
LingFlow Context API - 统一的上下文管理 API
"""

import logging
from typing import Dict, List, Optional, Any

from core.token_estimator import get_token_estimator
from core.message_scorer import get_message_scorer
from core.compression_strategy import get_compression_strategy
from core.context_insight import get_context_insight_provider

logger = logging.getLogger(__name__)


class ContextAPI:
    """统一的上下文管理 API"""

    def __init__(self, model: str = "claude-opus-4"):
        """
        初始化上下文 API

        Args:
            model: 默认使用的 LLM 模型
        """
        self.model = model
        self.token_estimator = get_token_estimator(model)
        self.message_scorer = get_message_scorer()
        self.compression_strategy = get_compression_strategy(
            self.token_estimator,
            self.message_scorer
        )
        self.insight_provider = get_context_insight_provider(
            self.token_estimator,
            self.message_scorer,
            self.compression_strategy
        )
        logger.info(f"ContextAPI initialized for model {model}")

    def estimate_tokens(
        self,
        text: Optional[str] = None,
        messages: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        估算 token 数量

        Args:
            text: 单个文本
            messages: 消息列表

        Returns:
            Token 估算结果
        """
        try:
            if text:
                estimate = self.token_estimator.estimate(text)
                return {
                    "token_count": estimate.token_count,
                    "model": estimate.model,
                    "encoding": estimate.encoding,
                    "estimated": estimate.estimated
                }
            elif messages:
                estimate = self.token_estimator.estimate_messages(messages)
                return {
                    "token_count": estimate.token_count,
                    "model": estimate.model,
                    "encoding": estimate.encoding,
                    "message_count": len(messages)
                }
            else:
                return {"error": "Either text or messages must be provided"}
        except Exception as e:
            logger.error(f"Error estimating tokens: {e}")
            return {"error": str(e)}

    def score_messages(
        self,
        messages: List[Dict],
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        评分消息列表

        Args:
            messages: 消息列表
            context: 上下文信息

        Returns:
            评分结果列表
        """
        try:
            scores = self.message_scorer.batch_score(messages, context)

            return [
                {
                    "role": msg.get("role"),
                    "content_preview": msg.get("content", "")[:100] + "...",
                    "importance_score": score.importance_score,
                    "relevance_score": score.relevance_score,
                    "time_score": score.time_score,
                    "quality_score": score.quality_score,
                    "reasoning": score.reasoning
                }
                for msg, score in zip(messages, scores)
            ]
        except Exception as e:
            logger.error(f"Error scoring messages: {e}")
            return [{"error": str(e)}]

    def compress_context(
        self,
        messages: List[Dict],
        target_tokens: int,
        strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        压缩上下文

        Args:
            messages: 消息列表
            target_tokens: 目标 token 数量
            strategy: 压缩策略

        Returns:
            压缩结果
        """
        try:
            result = self.compression_strategy.compress(
                messages,
                target_tokens,
                strategy
            )

            return {
                "original_tokens": result.original_tokens,
                "compressed_tokens": result.compressed_tokens,
                "reduction_ratio": round(result.reduction_ratio * 100, 2),
                "messages_removed": result.messages_removed,
                "compression_level": result.compression_level.value,
                "strategy": result.strategy,
                "compressed_messages": result.compressed_messages,
                "details": result.details
            }
        except Exception as e:
            logger.error(f"Error compressing context: {e}")
            return {"error": str(e)}

    def get_context_insight(
        self,
        messages: List[Dict],
        threshold: int = 150000
    ) -> Dict[str, Any]:
        """
        获取上下文洞察

        Args:
            messages: 消息列表
            threshold: token 阈值

        Returns:
            上下文洞察
        """
        try:
            insight = self.insight_provider.analyze(messages, threshold)

            return {
                "total_tokens": insight.total_tokens,
                "message_count": insight.message_count,
                "important_messages": insight.important_messages,
                "can_compress": insight.can_compress,
                "health_status": insight.health_status,
                "recommendations": insight.recommendations,
                "compression_recommendation": insight.compression_recommendation,
                "details": insight.details
            }
        except Exception as e:
            logger.error(f"Error getting context insight: {e}")
            return {"error": str(e)}

    def should_compress(
        self,
        messages: List[Dict],
        threshold: int = 150000
    ) -> Dict[str, Any]:
        """
        判断是否应该压缩

        Args:
            messages: 消息列表
            threshold: token 阈值

        Returns:
            压缩建议
        """
        try:
            recommendation = self.compression_strategy.get_compression_recommendation(
                messages,
                threshold
            )

            return {
                "should_compress": recommendation["should_compress"],
                "reason": recommendation["reason"],
                "current_tokens": recommendation["current_tokens"],
                "target_tokens": recommendation["target_tokens"],
                "excess_tokens": recommendation["excess_tokens"],
                "excess_ratio": recommendation["excess_ratio"],
                "recommended_strategy": recommendation["recommended_strategy"]
            }
        except Exception as e:
            logger.error(f"Error checking compression: {e}")
            return {"error": str(e)}

    def analyze_session(
        self,
        session_id: str,
        messages: List[Dict],
        threshold: int = 150000
    ) -> Dict[str, Any]:
        """
        完整分析会话

        Args:
            session_id: 会话 ID
            messages: 消息列表
            threshold: token 阈值

        Returns:
            完整的会话分析
        """
        try:
            # Token 估算
            token_info = self.estimate_tokens(messages=messages)

            # 消息评分
            scores = self.score_messages(messages)

            # 上下文洞察
            insight = self.get_context_insight(messages, threshold)

            # 压缩建议
            compression_rec = self.should_compress(messages, threshold)

            # 保存到 SQLite（如果可用）
            saved = False
            if self.insight_provider.use_sqlite:
                conv = self.insight_provider.save_to_sqlite(
                    session_id,
                    messages
                )
                saved = conv is not None

            return {
                "session_id": session_id,
                "tokens": token_info,
                "scores": scores,
                "insight": insight,
                "compression": compression_rec,
                "saved_to_sqlite": saved,
                "summary": {
                    "total_messages": len(messages),
                    "total_tokens": token_info.get("token_count", 0),
                    "health_status": insight.get("health_status", "unknown"),
                    "needs_compression": compression_rec.get("should_compress", False)
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing session: {e}")
            return {"error": str(e)}


# 全局实例
_api_instances: Dict[str, ContextAPI] = {}


def get_context_api(model: str = "claude-opus-4") -> ContextAPI:
    """
    获取上下文 API 实例（单例模式）

    Args:
        model: 模型名称

    Returns:
        上下文 API 实例
    """
    if model not in _api_instances:
        _api_instances[model] = ContextAPI(model)
    return _api_instances[model]


__all__ = [
    "ContextAPI",
    "get_context_api"
]
