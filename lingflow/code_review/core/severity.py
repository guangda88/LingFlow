"""
严重程度定义和权重配置

该模块定义了问题严重程度的枚举、权重配置和维度权重。
用于代码审查中的问题严重程度评估和评分计算。
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict


class Severity(Enum):
    """
    问题严重程度枚举

    该枚举定义了代码审查中发现问题的严重程度级别。

    Attributes:
        CRITICAL: 严重问题，必须立即修复（如安全漏洞）
        HIGH: 高优先级问题，应尽快修复
        MEDIUM: 中等问题，建议修复
        LOW: 低优先级问题，可以稍后修复
        WARNING: 警告信息，不是错误
        INFO: 信息提示，仅供参考

    Examples:
        >>> severity = Severity.CRITICAL
        >>> assert severity.value == "critical"
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"
    INFO = "info"

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """
        从字符串创建 Severity 实例

        Args:
            value: 严重程度字符串值

        Returns:
            Severity: 对应的严重程度枚举

        Raises:
            ValueError: 如果字符串值无效
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid_values = [s.value for s in cls]
            raise ValueError(f"无效的严重程度: '{value}'. " f"有效值为: {', '.join(valid_values)}")

    def is_critical(self) -> bool:
        """检查是否为严重级别"""
        return self == Severity.CRITICAL

    def is_high_or_higher(self) -> bool:
        """检查是否为高优先级或更高级别"""
        return self in (Severity.CRITICAL, Severity.HIGH)


@dataclass(frozen=True)
class SeverityWeight:
    """
    严重程度权重配置

    该类定义了不同严重程度的权重值、颜色和emoji表示。

    Attributes:
        severity: 严重程度枚举
        weight: 权重值，用于计算扣分
        color: 显示颜色名称
        emoji: 对应的emoji符号

    Examples:
        >>> config = SeverityWeight.get_all()
        >>> critical_weight = next(c for c in config if c.severity == Severity.CRITICAL)
        >>> assert critical_weight.weight == 10.0
    """

    severity: Severity
    weight: float
    color: str
    emoji: str

    @classmethod
    def get_all(cls) -> List["SeverityWeight"]:
        """
        获取所有严重程度配置

        Returns:
            List[SeverityWeight]: 所有严重程度配置列表，按严重程度降序排列
        """
        return [
            cls(Severity.CRITICAL, 10.0, "red", "🔴"),
            cls(Severity.HIGH, 5.0, "orange", "🔶"),
            cls(Severity.MEDIUM, 2.0, "yellow", "⚠️"),
            cls(Severity.LOW, 0.5, "blue", "🔵"),
            cls(Severity.WARNING, 0.2, "gray", "⚪"),
            cls(Severity.INFO, 0.1, "gray", "ℹ️"),
        ]

    @classmethod
    def get_weight(cls, severity: Severity) -> float:
        """
        获取严重程度权重

        Args:
            severity: 严重程度枚举

        Returns:
            float: 对应的权重值

        Examples:
            >>> assert SeverityWeight.get_weight(Severity.CRITICAL) == 10.0
        """
        for config in cls.get_all():
            if config.severity == severity:
                return config.weight
        return 1.0  # 默认权重

    @classmethod
    def get_emoji(cls, severity: Severity) -> str:
        """
        获取严重程度对应的 emoji

        Args:
            severity: 严重程度枚举

        Returns:
            str: 对应的 emoji 符号

        Examples:
            >>> assert SeverityWeight.get_emoji(Severity.CRITICAL) == "🔴"
        """
        for config in cls.get_all():
            if config.severity == severity:
                return config.emoji
        return "📝"  # 默认emoji

    @classmethod
    def get_color(cls, severity: Severity) -> str:
        """
        获取严重程度对应的颜色

        Args:
            severity: 严重程度枚举

        Returns:
            str: 对应的颜色名称
        """
        for config in cls.get_all():
            if config.severity == severity:
                return config.color
        return "gray"  # 默认颜色


# 维度权重配置
# 这些权重用于计算各维度在总体评分中的重要性
# 总和约等于1.0，但不严格要求完全等于1.0
DIMENSION_WEIGHTS: Dict[str, float] = {
    # 安全性 - 最高权重
    "security": 0.30,
    # 潜在错误 - 高权重
    "bugs": 0.25,
    # 代码质量
    "code_quality": 0.20,
    # 架构设计
    "architecture": 0.10,
    # 性能问题
    "performance": 0.05,
    # 可维护性
    "maintainability": 0.05,
    # 最佳实践
    "best_practices": 0.03,
    # 一致性检查
    "autoresearch_consistency": 0.02,
}


def get_dimension_weight(dimension: str) -> float:
    """
    获取指定维度的权重

    Args:
        dimension: 维度名称

    Returns:
        float: 权重值，如果维度不存在则返回0
    """
    return DIMENSION_WEIGHTS.get(dimension, 0.0)


def get_all_dimensions() -> List[str]:
    """
    获取所有维度名称

    Returns:
        List[str]: 维度名称列表，按权重降序排列
    """
    return sorted(DIMENSION_WEIGHTS.keys(), key=lambda x: DIMENSION_WEIGHTS[x], reverse=True)


def get_critical_dimensions() -> List[str]:
    """
    获取关键维度列表（权重 >= 0.1）

    Returns:
        List[str]: 关键维度名称列表
    """
    return [d for d, w in DIMENSION_WEIGHTS.items() if w >= 0.1]
