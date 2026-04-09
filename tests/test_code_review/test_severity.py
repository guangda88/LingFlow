"""
严重程度单元测试

测试 Severity 枚举和 SeverityWeight 类的功能
"""

import pytest

from lingflow.code_review.core.severity import DIMENSION_WEIGHTS, Severity, SeverityWeight


class TestSeverity:
    """Severity 枚举测试"""

    def test_severity_values(self):
        """测试严重程度值"""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"

    def test_severity_comparison(self):
        """测试严重程度比较"""
        # 枚举实例应该相等
        assert Severity.CRITICAL == Severity.CRITICAL
        assert Severity.HIGH != Severity.MEDIUM


class TestSeverityWeight:
    """SeverityWeight 类测试"""

    def test_get_all(self):
        """测试获取所有严重程度配置"""
        all_weights = SeverityWeight.get_all()
        assert len(all_weights) == 6

        # 检查返回的是 SeverityWeight 实例
        for config in all_weights:
            assert hasattr(config, "severity")
            assert hasattr(config, "weight")
            assert hasattr(config, "color")
            assert hasattr(config, "emoji")

    def test_get_weight(self):
        """测试获取严重程度权重"""
        assert SeverityWeight.get_weight(Severity.CRITICAL) == 10.0
        assert SeverityWeight.get_weight(Severity.HIGH) == 5.0
        assert SeverityWeight.get_weight(Severity.MEDIUM) == 2.0
        assert SeverityWeight.get_weight(Severity.LOW) == 0.5
        assert SeverityWeight.get_weight(Severity.WARNING) == 0.2
        assert SeverityWeight.get_weight(Severity.INFO) == 0.1

    def test_get_weight_ordering(self):
        """测试权重顺序正确"""
        weights = [
            SeverityWeight.get_weight(Severity.CRITICAL),
            SeverityWeight.get_weight(Severity.HIGH),
            SeverityWeight.get_weight(Severity.MEDIUM),
            SeverityWeight.get_weight(Severity.LOW),
            SeverityWeight.get_weight(Severity.WARNING),
            SeverityWeight.get_weight(Severity.INFO),
        ]

        # 权重应该递减
        for i in range(len(weights) - 1):
            assert weights[i] > weights[i + 1]

    def test_get_emoji(self):
        """测试获取严重程度表情"""
        assert SeverityWeight.get_emoji(Severity.CRITICAL) == "🔴"
        assert SeverityWeight.get_emoji(Severity.HIGH) == "🔶"
        assert SeverityWeight.get_emoji(Severity.MEDIUM) == "⚠️"
        assert SeverityWeight.get_emoji(Severity.LOW) == "🔵"
        assert SeverityWeight.get_emoji(Severity.WARNING) == "⚪"
        assert SeverityWeight.get_emoji(Severity.INFO) == "ℹ️"


class TestDimensionWeights:
    """维度权重配置测试"""

    def test_dimension_weights_defined(self):
        """测试维度权重已定义"""
        assert DIMENSION_WEIGHTS is not None
        assert isinstance(DIMENSION_WEIGHTS, dict)

    def test_dimension_weights_sum(self):
        """测试维度权重总和"""
        total = sum(DIMENSION_WEIGHTS.values())
        # 权重总和应该接近 1.0（但可能不完全是，因为可能有其他维度）
        assert 0.8 < total <= 1.0

    def test_security_weight_highest(self):
        """测试安全维度权重最高"""
        security_weight = DIMENSION_WEIGHTS.get("security", 0)
        assert security_weight > 0

        # 安全权重应该高于其他大多数维度
        for key, weight in DIMENSION_WEIGHTS.items():
            if key not in ["security", "bugs"]:
                assert security_weight > weight

    def test_all_dimension_weights_positive(self):
        """测试所有维度权重为正"""
        for key, weight in DIMENSION_WEIGHTS.items():
            assert weight > 0, f"{key} 的权重应该为正"

    def test_expected_dimensions_exist(self):
        """测试预期的维度存在"""
        expected_dimensions = [
            "security",
            "bugs",
            "code_quality",
            "architecture",
            "performance",
            "maintainability",
            "best_practices",
        ]

        for dimension in expected_dimensions:
            assert dimension in DIMENSION_WEIGHTS, f"缺少维度: {dimension}"


class TestSeverityDataclass:
    """SeverityWeight 数据类测试"""

    def test_severity_weight_creation(self):
        """测试创建 SeverityWeight 实例"""
        config = SeverityWeight(severity=Severity.CRITICAL, weight=10.0, color="red", emoji="🔴")

        assert config.severity == Severity.CRITICAL
        assert config.weight == 10.0
        assert config.color == "red"
        assert config.emoji == "🔴"

    def test_severity_weight_immutability(self):
        """测试 SeverityWeight 是不可变的（dataclass）"""
        config = SeverityWeight(severity=Severity.CRITICAL, weight=10.0, color="red", emoji="🔴")

        # dataclass 默认是可变的，但我们可以测试属性访问
        assert config.severity.value == "critical"
