"""
AI学习引擎

从外部AI工具反馈中学习改进规则，自动提取、验证和应用最佳实践。
"""

from .feedback_interface import (
    ToolType,
    SeverityLevel,
    FeedbackCategory,
    FeedbackItem,
    ToolAdapter,
    SonarQubeAdapter,
    PylintAdapter,
    BanditAdapter,
    FeedbackProcessor,
    FeedbackPriorityCalculator
)

from .rule_learning_engine import (
    LearningStatus,
    Pattern,
    LearnedRule,
    RuleExtractor,
    RuleClassifier,
    RuleQualityScorer,
    ConflictDetector,
    RuleLearningEngine
)

__version__ = "1.0.0"
__author__ = "LingFlow Team"

__all__ = [
    # Types
    'ToolType',
    'SeverityLevel',
    'FeedbackCategory',
    'LearningStatus',

    # Data classes
    'FeedbackItem',
    'Pattern',
    'LearnedRule',

    # Adapters
    'ToolAdapter',
    'SonarQubeAdapter',
    'PylintAdapter',
    'BanditAdapter',

    # Processors
    'FeedbackProcessor',
    'FeedbackPriorityCalculator',

    # Engines
    'RuleExtractor',
    'RuleClassifier',
    'RuleQualityScorer',
    'ConflictDetector',
    'RuleLearningEngine'
]