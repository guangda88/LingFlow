"""情报系统常量定义

集中管理所有魔法数字，提高可维护性。
"""

from .models.common import Platform


class PlatformWeights:
    """平台权重常量

    用于影响力分析中各平台的权重分配。
    权重范围: 0.0 - 1.0
    """
    HACKERNEWS = 1.0
    GITHUB = 0.9
    REDDIT = 0.6
    JUEJIN = 0.5
    ZHIHU = 0.5
    V2EX = 0.4

    @classmethod
    def get_weight(cls, platform: Platform) -> float:
        """获取平台权重

        Args:
            platform: 平台枚举

        Returns:
            权重值，未知平台返回0.5
        """
        weights = {
            Platform.HACKERNEWS: cls.HACKERNEWS,
            Platform.GITHUB: cls.GITHUB,
            Platform.REDDIT: cls.REDDIT,
            Platform.JUEJIN: cls.JUEJIN,
            Platform.ZHIHU: cls.ZHIHU,
            Platform.V2EX: cls.V2EX,
        }
        return weights.get(platform, 0.5)


class APILimits:
    """API限制常量

    各平台的API调用限制。
    """
    # 分页限制
    MAX_PAGES = 100
    DEFAULT_PAGE_SIZE = 30
    MAX_RESULTS = 1000

    # 超时设置 (秒)
    REQUEST_TIMEOUT = 30
    CONNECT_TIMEOUT = 10

    # 缓存设置 (秒)
    CACHE_TTL = 3600  # 1小时
    CACHE_TTL_SHORT = 300  # 5分钟
    CACHE_TTL_LONG = 86400  # 24小时


class InfluenceThresholds:
    """影响力评分阈值

    用于确定影响力等级。
    """
    HIGH = 70
    MEDIUM = 40
    LOW = 0

    @classmethod
    def get_level(cls, score: float) -> str:
        """根据分数获取等级

        Args:
            score: 影响力分数 (0-100)

        Returns:
            等级字符串: high/medium/low
        """
        if score >= cls.HIGH:
            return "high"
        elif score >= cls.MEDIUM:
            return "medium"
        else:
            return "low"


class SentimentThresholds:
    """情感分析阈值

    用于确定情感标签。
    """
    POSITIVE = 0.1
    NEGATIVE = -0.1

    @classmethod
    def get_label(cls, score: float) -> str:
        """根据分数获取情感标签

        Args:
            score: 情感分数 (-1 到 1)

        Returns:
            标签字符串: positive/neutral/negative
        """
        if score >= cls.POSITIVE:
            return "positive"
        elif score <= cls.NEGATIVE:
            return "negative"
        else:
            return "neutral"


class DataRetention:
    """数据保留策略

    定义各类数据的保留时间 (天)。
    """
    RAW_DATA = 30
    ANALYZED_DATA = 90
    REPORTS = 365
    CACHE = 7


class ReportLimits:
    """报告生成限制

    报告中各类内容的数量限制。
    """
    MAX_HIGHLIGHTS = 5
    MAX_CONCERNS = 3
    MAX_TOPICS = 10
    MAX_INSIGHTS = 5
    MAX_TOP_AUTHORS = 5


class ScoreWeights:
    """影响力评分权重

    各维度在影响力计算中的权重。
    """
    ENGAGEMENT = 0.4
    AUTHOR = 0.3
    CONTENT = 0.2
    RECENCY = 0.1

    # 验证权重和为1.0
    TOTAL = ENGAGEMENT + AUTHOR + CONTENT + RECENCY


class AuthorTiers:
    """作者活跃度分级

    不同贡献等级的基础分数。
    """
    HIGH = 100
    MEDIUM = 50
    LOW = 10
    UNKNOWN = 0


class RecencyDecay:
    """时效性衰减参数

    根据内容年龄计算时效分数。
    """
    FRESH_HOURS = 1
    FRESH_SCORE = 100

    DAY_HOURS = 24
    DAY_SCORE = 90

    WEEK_HOURS = 168
    WEEK_SCORE = 70

    MONTH_HOURS = 720
    MONTH_SCORE = 50

    OLD_SCORE = 30
