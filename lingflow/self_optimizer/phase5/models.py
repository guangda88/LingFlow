"""
lingflow Phase 5: 核心数据模型定义

包含AI反馈、规则、模式等核心数据类。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class FeedbackSource(Enum):
    """AI反馈来源"""

    SEMGREP = "semgrep"
    RUFF = "ruff"
    PYLINT = "pylint"
    SONARQUBE = "sonarqube"
    CODEQL = "codeql"
    ESLINT = "eslint"
    CUSTOM = "custom"


class ToolType(Enum):
    """工具类型（用于学习引擎）"""

    STATIC_ANALYZER = "static_analyzer"
    CODE_REVIEW = "code_review"
    SECURITY_SCANNER = "security_scanner"
    LINTING = "linting"


class FeedbackSeverity(Enum):
    """反馈严重程度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# 兼容性别名
SeverityLevel = FeedbackSeverity


class FeedbackCategory(Enum):
    """反馈分类"""

    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICE = "best_practice"
    BUG_RISK = "bug_risk"
    ARCHITECTURE = "architecture"


class PatternType(Enum):
    """代码模式类型"""

    ANTI_PATTERN = "anti_pattern"  # 反模式
    BEST_PRACTICE = "best_practice"  # 最佳实践


@dataclass
class AIFeedback:
    """AI工具反馈数据模型

    表示从外部AI代码分析工具收集到的一条反馈。
    """

    id: str  # 唯一标识
    source: FeedbackSource  # 来源工具
    category: FeedbackCategory  # 问题类别
    severity: FeedbackSeverity  # 严重程度
    rule_id: Optional[str] = None  # 规则ID
    message: str = ""  # 反馈消息
    file_path: str = ""  # 文件路径
    line_no: int = 0  # 行号
    column_no: Optional[int] = None  # 列号
    end_line_no: Optional[int] = None  # 结束行号
    end_column_no: Optional[int] = None  # 结束列号
    code_snippet: Optional[str] = None  # 代码片段
    suggestion: Optional[str] = None  # 修复建议
    fix_available: bool = False  # 是否有自动修复
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    verified: bool = False  # 是否已验证
    applied: bool = False  # 是否已应用

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source": self.source.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "rule_id": self.rule_id,
            "message": self.message,
            "file_path": self.file_path,
            "line_no": self.line_no,
            "column_no": self.column_no,
            "suggestion": self.suggestion,
            "fix_available": self.fix_available,
            "verified": self.verified,
            "applied": self.applied,
        }

    def get_location_str(self) -> str:
        """获取位置字符串"""
        location = f"{self.file_path}:{self.line_no}"
        if self.column_no:
            location += f":{self.column_no}"
        return location

    def is_security_issue(self) -> bool:
        """是否是安全问题"""
        return self.category == FeedbackCategory.SECURITY

    def can_auto_fix(self) -> bool:
        """是否可以自动修复"""
        return self.fix_available and self.suggestion is not None


@dataclass
class ExtractedRule:
    """从AI反馈中提取的规则

    表示从多次反馈中提取出的可重用规则。
    """

    id: str  # 规则ID
    name: str  # 规则名称
    category: FeedbackCategory  # 规则类别
    description: str  # 描述
    pattern: str  # 代码模式（AST或正则）
    severity: FeedbackSeverity  # 默认严重程度
    suggestion_template: str  # 建议模板
    confidence: float  # 置信度 (0-1)
    source_feedback_ids: List[str] = field(default_factory=list)  # 来源反馈ID
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    verified: bool = False  # 是否已验证
    enabled: bool = True  # 是否启用
    application_count: int = 0  # 应用次数
    success_count: int = 0  # 成功次数

    def to_lingflow_rule(self) -> Dict[str, Any]:
        """转换为lingflow代码审查规则"""
        return {
            "rule_id": self.id,
            "name": self.name,
            "category": self.category.value,
            "severity": self.severity.value,
            "pattern": self.pattern,
            "suggestion": self.suggestion_template,
            "confidence": self.confidence,
            "enabled": self.enabled,
        }

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.application_count == 0:
            return 0.0
        return self.success_count / self.application_count

    def is_high_confidence(self) -> bool:
        """是否是高置信度规则"""
        return self.confidence >= 0.8 and self.application_count >= 5


@dataclass
class CodePattern:
    """代码模式

    表示识别到的代码反模式或最佳实践。
    """

    id: str  # 模式ID
    name: str  # 模式名称
    type: PatternType  # 模式类型
    category: str  # 分类
    description: str  # 描述
    file_path: str  # 文件路径
    locations: List[Dict[str, int]]  # 位置列表
    severity: FeedbackSeverity  # 严重程度
    suggestion: str  # 建议
    confidence: float  # 置信度
    detected_at: datetime = field(default_factory=datetime.now)  # 检测时间
    verified: bool = False  # 是否已验证

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "category": self.category,
            "description": self.description,
            "file_path": self.file_path,
            "locations": self.locations,
            "severity": self.severity.value,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
        }

    def is_anti_pattern(self) -> bool:
        """是否是反模式"""
        return self.type == PatternType.ANTI_PATTERN

    def get_occurrence_count(self) -> int:
        """获取出现次数"""
        return len(self.locations)


@dataclass
class LearningResult:
    """学习结果

    表示一次学习会话的结果。
    """

    feedback_count: int  # 收集的反馈数量
    rules_learned: int  # 学习的规则数量
    patterns_recognized: int  # 识别的模式数量
    suggestions_generated: int  # 生成的建议数量
    suggestions: List["Suggestion"] = field(default_factory=list)  # 建议列表
    errors: List[str] = field(default_factory=list)  # 错误列表
    duration: float = 0.0  # 耗时（秒）
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳

    def get_summary(self) -> str:
        """获取摘要"""
        return f"""
学习结果摘要:
  收集反馈: {self.feedback_count}
  学习规则: {self.rules_learned}
  识别模式: {self.patterns_recognized}
  生成建议: {self.suggestions_generated}
  错误: {len(self.errors)}
  耗时: {self.duration:.2f}秒
        """.strip()


@dataclass
class Suggestion:
    """改进建议

    表示一个具体的代码改进建议。
    """

    id: str  # 建议ID
    rule_id: Optional[str]  # 关联规则ID
    pattern_id: Optional[str]  # 关联模式ID
    feedback_id: Optional[str]  # 来源反馈ID
    title: str  # 标题
    description: str  # 描述
    file_path: str  # 文件路径
    locations: List[Dict[str, int]]  # 位置列表
    current_code: str  # 当前代码
    suggested_code: str  # 建议代码
    severity: FeedbackSeverity  # 严重程度
    category: FeedbackCategory  # 类别
    auto_applicable: bool = False  # 是否可自动应用
    confidence: float = 1.0  # 置信度
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    applied: bool = False  # 是否已应用
    approved: bool = False  # 是否已批准

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "severity": self.severity.value,
            "category": self.category.value,
            "auto_applicable": self.auto_applicable,
            "confidence": self.confidence,
        }


@dataclass
class ApplyResult:
    """应用结果

    表示应用建议的结果。
    """

    applied: List["SingleApplyResult"] = field(default_factory=list)  # 成功应用
    failed: List["SingleApplyResult"] = field(default_factory=list)  # 失败
    skipped: List[Dict[str, Any]] = field(default_factory=list)  # 跳过
    rolled_back: bool = False  # 是否回滚
    error: Optional[str] = None  # 错误
    duration: float = 0.0  # 耗时

    def get_summary(self) -> str:
        """获取摘要"""
        return f"""
应用结果:
  成功: {len(self.applied)}
  失败: {len(self.failed)}
  跳过: {len(self.skipped)}
  回滚: {'是' if self.rolled_back else '否'}
  耗时: {self.duration:.2f}秒
        """.strip()

    def get_success_rate(self) -> float:
        """获取成功率"""
        total = len(self.applied) + len(self.failed)
        if total == 0:
            return 0.0
        return len(self.applied) / total


@dataclass
class SingleApplyResult:
    """单个建议应用结果"""

    success: bool  # 是否成功
    suggestion: Suggestion  # 建议对象
    modified_files: List[str] = field(default_factory=list)  # 修改的文件
    error: Optional[str] = None  # 错误信息
    duration: float = 0.0  # 耗时


@dataclass
class SafetyCheckResult:
    """安全检查结果"""

    is_safe: bool  # 是否安全
    reason: Optional[str] = None  # 不安全的原因
    details: List[Any] = field(default_factory=list)  # 详细信息
    score: float = 1.0  # 安全评分 (0-1)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_safe": self.is_safe,
            "reason": self.reason,
            "score": self.score,
        }


@dataclass
class Checkpoint:
    """回滚检查点"""

    id: str  # 检查点ID
    path: Path  # 检查点路径
    metadata: Dict[str, Any]  # 元数据
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间

    def get_age_seconds(self) -> int:
        """获取检查点年龄（秒）"""
        return int((datetime.now() - self.created_at).total_seconds())

    def get_file_count(self) -> int:
        """获取备份文件数量"""
        return len(self.metadata.get("files", {}))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "file_count": self.get_file_count(),
            "age_seconds": self.get_age_seconds(),
        }


@dataclass
class KnowledgeBaseStats:
    """知识库统计"""

    total_rules: int  # 总规则数
    enabled_rules: int  # 启用规则数
    total_patterns: int  # 总模式数
    verified_rules: int  # 已验证规则数
    high_confidence_rules: int  # 高置信度规则数
    total_suggestions: int  # 总建议数
    applied_suggestions: int  # 已应用建议数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_rules": self.total_rules,
            "enabled_rules": self.enabled_rules,
            "total_patterns": self.total_patterns,
            "verified_rules": self.verified_rules,
            "high_confidence_rules": self.high_confidence_rules,
            "total_suggestions": self.total_suggestions,
            "applied_suggestions": self.applied_suggestions,
        }


@dataclass
class ToolCapability:
    """工具能力描述"""

    name: str  # 工具名称
    source: FeedbackSource  # 来源
    version: Optional[str]  # 版本
    available: bool  # 是否可用
    capabilities: List[str]  # 能力列表
    scan_speed: str  # 扫描速度
    false_positive_rate: str  # 误报率
    custom_rules: bool  # 支持自定义规则

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "source": self.source.value,
            "version": self.version,
            "available": self.available,
            "capabilities": self.capabilities,
        }


# 兼容性别名 - 用于学习引擎
# 注意：SeverityLevel在上面已经定义为FeedbackSeverity的子类


@dataclass
class FeedbackItem:
    """反馈项（兼容性别名）"""

    tool_name: str
    tool_type: ToolType
    rule_id: str
    rule_name: str
    category: FeedbackCategory
    severity: SeverityLevel
    message: str
    file_path: str
    line: int
    snippet: Optional[str] = None
    suggestion: Optional[str] = None
    confidence: float = 0.8


@dataclass
class Pattern:
    """规则模式"""

    file_patterns: List[str] = field(default_factory=list)
    code_patterns: List[str] = field(default_factory=list)
    context_keywords: List[str] = field(default_factory=list)
    severity_distribution: Dict[str, int] = field(default_factory=dict)
    tool_support: List[str] = field(default_factory=list)


@dataclass
class LearnedRule:
    """学习到的规则"""

    id: str
    name: str
    description: str
    category: FeedbackCategory
    pattern: Pattern
    tools: List[str]
    frequency: int
    confidence: float
    quality_score: float = 0.0
    status: str = "draft"
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
