"""情报系统常量测试

测试constants.py中定义的常量类。
"""

import pytest  # noqa

from lingflow.intelligence.constants import (
    APILimits,
    AuthorTiers,
    DataRetention,
    InfluenceThresholds,
    PlatformWeights,
    RecencyDecay,
    ReportLimits,
    ScoreWeights,
    SentimentThresholds,
)
from lingflow.intelligence.models.common import Platform


class TestPlatformWeights:
    """PlatformWeights测试"""

    def test_weights_exist(self):
        """测试权重常量存在"""
        assert hasattr(PlatformWeights, "GITHUB")
        assert hasattr(PlatformWeights, "HACKERNEWS")
        assert hasattr(PlatformWeights, "REDDIT")

    def test_weight_values(self):
        """测试权重值在合理范围"""
        assert 0.0 <= PlatformWeights.HACKERNEWS <= 1.0
        assert 0.0 <= PlatformWeights.GITHUB <= 1.0
        assert 0.0 <= PlatformWeights.REDDIT <= 1.0

    def test_get_weight(self):
        """测试获取权重方法"""
        # 测试已知平台
        assert PlatformWeights.get_weight(Platform.HACKERNEWS) == 1.0
        assert PlatformWeights.get_weight(Platform.GITHUB) == 0.9
        assert PlatformWeights.get_weight(Platform.REDDIT) == 0.6

        # 测试未知平台，应返回默认值
        assert PlatformWeights.get_weight(None) == 0.5


class TestAPILimits:
    """APILimits测试"""

    def test_limits_exist(self):
        """测试限制常量存在"""
        assert hasattr(APILimits, "MAX_PAGES")
        assert hasattr(APILimits, "REQUEST_TIMEOUT")
        assert hasattr(APILimits, "CACHE_TTL")

    def test_reasonable_values(self):
        """测试值在合理范围"""
        assert APILimits.MAX_PAGES > 0
        assert APILimits.REQUEST_TIMEOUT > 0
        assert APILimits.CACHE_TTL > 0


class TestInfluenceThresholds:
    """InfluenceThresholds测试"""

    def test_thresholds_exist(self):
        """测试阈值常量存在"""
        assert hasattr(InfluenceThresholds, "HIGH")
        assert hasattr(InfluenceThresholds, "MEDIUM")
        assert hasattr(InfluenceThresholds, "LOW")

    def test_threshold_order(self):
        """测试阈值顺序正确"""
        assert InfluenceThresholds.HIGH > InfluenceThresholds.MEDIUM
        assert InfluenceThresholds.MEDIUM > InfluenceThresholds.LOW

    def test_get_level(self):
        """测试获取等级方法"""
        assert InfluenceThresholds.get_level(80) == "high"
        assert InfluenceThresholds.get_level(50) == "medium"
        assert InfluenceThresholds.get_level(20) == "low"
        assert InfluenceThresholds.get_level(70) == "high"  # 边界值
        assert InfluenceThresholds.get_level(40) == "medium"  # 边界值


class TestSentimentThresholds:
    """SentimentThresholds测试"""

    def test_thresholds_exist(self):
        """测试阈值常量存在"""
        assert hasattr(SentimentThresholds, "POSITIVE")
        assert hasattr(SentimentThresholds, "NEGATIVE")

    def test_get_label(self):
        """测试获取标签方法"""
        assert SentimentThresholds.get_label(0.5) == "positive"
        assert SentimentThresholds.get_label(-0.5) == "negative"
        assert SentimentThresholds.get_label(0.0) == "neutral"
        assert SentimentThresholds.get_label(0.1) == "positive"  # 边界值
        assert SentimentThresholds.get_label(-0.1) == "negative"  # 边界值


class TestDataRetention:
    """DataRetention测试"""

    def test_policies_exist(self):
        """测试策略常量存在"""
        assert hasattr(DataRetention, "RAW_DATA")
        assert hasattr(DataRetention, "ANALYZED_DATA")
        assert hasattr(DataRetention, "REPORTS")

    def test_reasonable_values(self):
        """测试值合理"""
        assert DataRetention.RAW_DATA > 0
        assert DataRetention.ANALYZED_DATA > DataRetention.RAW_DATA
        assert DataRetention.REPORTS > DataRetention.ANALYZED_DATA


class TestReportLimits:
    """ReportLimits测试"""

    def test_limits_exist(self):
        """测试限制常量存在"""
        assert hasattr(ReportLimits, "MAX_HIGHLIGHTS")
        assert hasattr(ReportLimits, "MAX_CONCERNS")
        assert hasattr(ReportLimits, "MAX_TOPICS")

    def test_positive_values(self):
        """测试值为正"""
        assert ReportLimits.MAX_HIGHLIGHTS > 0
        assert ReportLimits.MAX_CONCERNS > 0
        assert ReportLimits.MAX_TOPICS > 0


class TestScoreWeights:
    """ScoreWeights测试"""

    def test_weights_exist(self):
        """测试权重常量存在"""
        assert hasattr(ScoreWeights, "ENGAGEMENT")
        assert hasattr(ScoreWeights, "AUTHOR")
        assert hasattr(ScoreWeights, "CONTENT")
        assert hasattr(ScoreWeights, "RECENCY")

    def test_weights_sum_to_one(self):
        """测试权重和为1"""
        total = ScoreWeights.ENGAGEMENT + ScoreWeights.AUTHOR + ScoreWeights.CONTENT + ScoreWeights.RECENCY
        assert abs(total - 1.0) < 0.01  # 允许浮点误差


class TestAuthorTiers:
    """AuthorTiers测试"""

    def test_tiers_exist(self):
        """测试层级常量存在"""
        assert hasattr(AuthorTiers, "HIGH")
        assert hasattr(AuthorTiers, "MEDIUM")
        assert hasattr(AuthorTiers, "LOW")

    def test_tier_order(self):
        """测试层级顺序"""
        assert AuthorTiers.HIGH > AuthorTiers.MEDIUM
        assert AuthorTiers.MEDIUM > AuthorTiers.LOW


class TestRecencyDecay:
    """RecencyDecay测试"""

    def test_decay_params_exist(self):
        """测试衰减参数存在"""
        assert hasattr(RecencyDecay, "FRESH_HOURS")
        assert hasattr(RecencyDecay, "FRESH_SCORE")
        assert hasattr(RecencyDecay, "DAY_HOURS")
        assert hasattr(RecencyDecay, "DAY_SCORE")

    def test_score_decay(self):
        """测试分数递减"""
        assert RecencyDecay.FRESH_SCORE >= RecencyDecay.DAY_SCORE
        assert RecencyDecay.DAY_SCORE >= RecencyDecay.WEEK_SCORE
        assert RecencyDecay.WEEK_SCORE >= RecencyDecay.MONTH_SCORE
        assert RecencyDecay.MONTH_SCORE >= RecencyDecay.OLD_SCORE
