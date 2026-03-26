"""LingFlow 对话上下文管理模块

自动跟踪对话进度，在 token 限制时压缩上下文到持久化存储。
"""

from .manager import (
    ContextManager,
    ContextSnapshot,
    get_context_manager,
    track_context,
    compress_context,
    get_recovery_context,
    add_task,
    complete_task,
)

__all__ = [
    "ContextManager",
    "ContextSnapshot",
    "get_context_manager",
    "track_context",
    "compress_context",
    "get_recovery_context",
    "add_task",
    "complete_task",
]

# 自动初始化上下文管理器
_get_cm = get_context_manager
