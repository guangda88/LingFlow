"""LingFlow 用户反馈模块

提供用户反馈收集、管理和报告功能。
"""

from lingflow.feedback.collector import (
    Feedback,
    FeedbackCategory,
    FeedbackCollector,
    FeedbackSeverity,
    get_feedback_collector,
    submit_bug,
    list_feedbacks,
)

__all__ = [
    "Feedback",
    "FeedbackCategory",
    "FeedbackCollector",
    "FeedbackSeverity",
    "get_feedback_collector",
    "submit_bug",
    "list_feedbacks",
]
