"""规则定义模块

定义规则引擎的核心数据模型。
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional
from .severity import Severity


@dataclass
class Rule:
    """审查规则定义

    Attributes:
        id: 规则唯一标识符 (如 "SEC001")
        name: 规则名称
        category: 规则类别 (security, performance, code_quality等)
        check_func: 检查函数，签名为 (content, tree, file_path) -> Optional[str]
        severity: 问题严重程度
        suggestion_template: 修复建议模板
        enabled: 是否启用该规则
        metadata: 额外的元数据

    Examples:
        >>> def check_eval(content, tree, path):
        ...     return "发现eval使用" if "eval(" in content else None
        >>> rule = Rule(
        ...     id="CUSTOM001",
        ...     name="custom_eval_check",
        ...     category="security",
        ...     check_func=check_eval,
        ...     severity=Severity.CRITICAL,
        ...     suggestion_template="避免使用eval"
        ... )
    """

    id: str
    name: str
    category: str
    check_func: Callable
    severity: Severity
    suggestion_template: str
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理，确保类别不为None"""
        if not self.category:
            self.category = "general"
        if not self.id:
            raise ValueError("规则ID不能为空")

    def validate(self) -> bool:
        """验证规则配置是否有效

        Returns:
            bool: 规则是否有效
        """
        return bool(self.id and self.name and self.check_func)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            规则字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "severity": self.severity.value,
            "suggestion_template": self.suggestion_template,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }


@dataclass
class RuleResult:
    """规则检查结果

    Attributes:
        rule_id: 触发的规则ID
        rule_name: 规则名称
        severity: 问题严重程度
        message: 问题描述
        suggestion: 修复建议
        file_path: 文件路径
        line: 行号
        column: 列号
        end_line: 结束行号
        end_column: 结束列号
    """

    rule_id: str
    rule_name: str
    severity: Severity
    message: str
    suggestion: str
    file_path: str
    line: int
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            结果字典
        """
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "file_path": str(self.file_path),
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
        }

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line} [{self.severity.value}] {self.message}"


class RuleEngineError(Exception):
    """规则引擎异常基类"""


class RuleNotFoundError(RuleEngineError):
    """规则未找到异常"""


class RuleValidationError(RuleEngineError):
    """规则验证异常"""
