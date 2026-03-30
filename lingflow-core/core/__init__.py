"""
LingFlow Core - 核心模块
"""

from .token_estimator import TokenEstimator, TokenEstimate, get_token_estimator
from .message_scorer import MessageScorer, MessageScore, get_message_scorer
from .compression_strategy import (
    TieredCompressionStrategy,
    CompressionResult,
    CompressionLevel,
    get_compression_strategy
)
from .context_insight import (
    ContextInsightProvider,
    ContextInsight,
    get_context_insight_provider,
    SQLITE_AVAILABLE
)
from .sqlite_context_manager import (
    SQLiteContextManager,
    Message,
    Conversation,
    get_context_manager
)

__version__ = "0.1.0"
__all__ = [
    "TokenEstimator",
    "TokenEstimate",
    "get_token_estimator",
    "MessageScorer",
    "MessageScore",
    "get_message_scorer",
    "TieredCompressionStrategy",
    "CompressionResult",
    "CompressionLevel",
    "get_compression_strategy",
    "ContextInsightProvider",
    "ContextInsight",
    "get_context_insight_provider",
    "SQLITE_AVAILABLE",
    "SQLiteContextManager",
    "Message",
    "Conversation",
    "get_context_manager"
]
