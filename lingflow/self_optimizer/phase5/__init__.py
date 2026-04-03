"""
LingFlow Phase 5: AI工具学习系统

从外部AI代码分析工具（SonarQube、CodeQL、Semgrep等）中学习，
提取规则和模式，自动集成到LingFlow的代码审查和优化流程中。

核心功能：
- AI工具适配器（Semgrep、Ruff、Pylint等）
- 反馈收集与标准化
- 规则提取与模式识别
- 安全的自动应用系统
- 完整的回滚机制

使用示例:
    from lingflow.self_optimizer.phase5 import AIToolLearningSystem

    system = AIToolLearningSystem(config={})
    result = system.learn_from_tools("./my_project")

    print(f"收集反馈: {result.feedback_count}")
    print(f"提取规则: {result.rules_learned}")

    # 应用建议（带确认）
    apply_result = system.apply_learned_improvements(auto_apply=False)
"""

# 版本信息 (与主项目版本保持一致)
__version__ = "3.8.0"
__author__ = "LingFlow Team"

# 核心类导出（待实现）
# from lingflow.self_optimizer.phase5.core import (
#     AIToolLearningSystem,
#     LearningResult,
# )

# 数据模型导出
from lingflow.self_optimizer.phase5.models import (
    FeedbackItem,
    ToolType,
    FeedbackCategory,
    SeverityLevel,
    LearnedRule,
    Pattern,
)

# 学习引擎导出
from lingflow.self_optimizer.phase5.learning import (
    RuleExtractor,
    SecurityRuleExtractor,
    RuleDeduplicator,
    RuleValidator,
)

# 模式识别导出
from lingflow.self_optimizer.phase5.patterns import (
    PatternRecognizer,
    PatternDetector,
    LongMethodDetector,
    UnusedVariableDetector,
    HardcodedSecretDetector,
    DuplicateCodeDetector,
    EmptyBlockDetector,
    ComplexityDetector,
)

# 知识库导出
from lingflow.self_optimizer.phase5.knowledge import (
    KnowledgeBase,
    InMemoryKnowledgeBase,
)

# 便捷函数（待core模块实现后启用）
# def quick_learn(
#     target: str = ".",
#     tools: list = None,
#     auto_apply: bool = False
# ):
#     """快速学习（便捷函数）"""
#     from lingflow.self_optimizer.phase5.core import AIToolLearningSystem
#     system = AIToolLearningSystem(config={})
#     result = system.learn_from_tools(target, tools)
#     if auto_apply and result.suggestions:
#         system.apply_learned_improvements(auto_apply=True)
#     return result
#
#
# def get_learned_rules(category: str = None) -> list:
#     """获取学习到的规则（便捷函数）"""
#     from lingflow.self_optimizer.phase5.core import AIToolLearningSystem
#     system = AIToolLearningSystem(config={})
#     rules = system.get_learned_rules()
#     if category:
#         rules = [r for r in rules if r.category.value == category]
#     return rules
#
#
# def get_recognized_patterns(pattern_type: str = None) -> list:
#     """获取识别到的模式（便捷函数）"""
#     from lingflow.self_optimizer.phase5.core import AIToolLearningSystem
#     system = AIToolLearningSystem(config={})
#     patterns = system.get_recognized_patterns()
#     if pattern_type:
#         patterns = [p for p in patterns if p.type == pattern_type]
#     return patterns


__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    # 数据模型
    "FeedbackItem",
    "ToolType",
    "FeedbackCategory",
    "SeverityLevel",
    "LearnedRule",
    "Pattern",
    # 学习引擎
    "RuleExtractor",
    "SecurityRuleExtractor",
    "RuleDeduplicator",
    "RuleValidator",
    # 模式识别
    "PatternRecognizer",
    "PatternDetector",
    "LongMethodDetector",
    "UnusedVariableDetector",
    "HardcodedSecretDetector",
    "DuplicateCodeDetector",
    "EmptyBlockDetector",
    "ComplexityDetector",
    # 知识库
    "KnowledgeBase",
    "InMemoryKnowledgeBase",
]
