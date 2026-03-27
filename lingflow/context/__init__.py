"""LingFlow 对话上下文管理模块

自动跟踪对话进度，在 token 限制时压缩上下文到持久化存储。

注意: 此模块不自动初始化，由 lingflow.__init__ 统一管理启动顺序。
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

# 导出 auto_resume 模块的接口（但不自动触发）
def show_resume():
    """显示会话恢复信息（手动调用）"""
    from .auto_resume import auto_resume
    text = auto_resume()
    if text:
        print(text, file=__import__('sys').stderr)
