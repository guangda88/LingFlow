"""
LingFlow 钩子系统
在特定事件触发时执行自定义操作
"""

from lingflow.hooks.auto_optimize_hook import AutoOptimizeHook, get_global_hook
from lingflow.hooks.conclusion_verification_hook import ConclusionVerificationHook, get_conclusion_hook
from lingflow.hooks.metacognition_hook import MetacognitionHook, get_metacognition_hook

__all__ = [
    "AutoOptimizeHook",
    "get_global_hook",
    "ConclusionVerificationHook",
    "get_conclusion_hook",
    "MetacognitionHook",
    "get_metacognition_hook",
]
