"""影响力分析器

评估每个提及的影响力。
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

from .base import BaseAnalyzer, AnalyzerConfig, calculate_percentile
from ..models.common import MentionData, InfluenceScore, Platform
from ..constants import (
    PlatformWeights,
    ScoreWeights,
    InfluenceThresholds,
    AuthorTiers,
    RecencyDecay,
)

logger = logging.getLogger(__name__)


@dataclass
class InfluenceConfig(AnalyzerConfig):
    """影响力分析器配置"""
    # 平台权重 (使用常量类)
    platform_weights: Dict[Platform, float] = None

    # 指标权重 (使用常量类)
    engagement_weight: float = ScoreWeights.ENGAGEMENT
    author_weight: float = ScoreWeights.AUTHOR
    content_weight: float = ScoreWeights.CONTENT
    recency_weight: float = ScoreWeights.RECENCY

    def __post_init__(self):
        if self.platform_weights is None:
            # 使用常量类初始化
            self.platform_weights = {
                Platform.HACKERNEWS: PlatformWeights.HACKERNEWS,
                Platform.GITHUB: PlatformWeights.GITHUB,
                Platform.REDDIT: PlatformWeights.REDDIT,
                Platform.JUEJIN: PlatformWeights.JUEJIN,
                Platform.ZHIHU: PlatformWeights.ZHIHU,
                Platform.V2EX: PlatformWeights.V2EX,
            }


class InfluenceAnalyzer(BaseAnalyzer):
    """影响力分析器

    综合评估每个提及的影响力。
    """

    NAME = "influence"
    DESCRIPTION = "影响力分析器"

    # 作者活跃度分级 (使用常量类)
    AUTHOR_TIERS = {
        "high": AuthorTiers.HIGH,
        "medium": AuthorTiers.MEDIUM,
        "low": AuthorTiers.LOW,
        "unknown": AuthorTiers.UNKNOWN,
    }

    def __init__(self, config: Optional[InfluenceConfig] = None):
        """初始化分析器"""
        super().__init__(config)
        self.config: InfluenceConfig = config or InfluenceConfig()

    def analyze(
        self,
        mentions: List[MentionData],
        calculate_percentiles: bool = True
    ) -> Dict[str, Any]:
        """分析所有提及的影响力

        Args:
            mentions: 提及数据列表
            calculate_percentiles: 是否计算百分位

        Returns:
            分析结果
        """
        if not mentions:
            return {
                'total': 0,
                'scores': [],
                'summary': {},
            }

        scores = []
        for mention in mentions:
            score = self.calculate_score(mention)
            scores.append(score)

        # 计算汇总统计
        score_values = [s.score for s in scores]

        result = {
            'total': len(scores),
            'scores': [s.to_dict() for s in scores],
            'summary': {
                'avg_score': sum(score_values) / len(score_values) if score_values else 0,
                'max_score': max(score_values) if score_values else 0,
                'min_score': min(score_values) if score_values else 0,
                'high_influence': sum(1 for s in scores if s.level == 'high'),
                'medium_influence': sum(1 for s in scores if s.level == 'medium'),
                'low_influence': sum(1 for s in scores if s.level == 'low'),
            },
        }

        if calculate_percentiles:
            result['summary']['percentiles'] = {
                'p50': calculate_percentile(score_values, 50),
                'p75': calculate_percentile(score_values, 75),
                'p90': calculate_percentile(score_values, 90),
                'p95': calculate_percentile(score_values, 95),
            }

        return result

    def calculate_score(self, mention: MentionData) -> InfluenceScore:
        """计算单个提及的影响力

        考虑因素:
        - 平台权重
        - 互动指标 (stars/comments/upvotes)
        - 作者活跃度
        - 内容质量 (情感/长度)
        - 时效性

        Args:
            mention: 提及数据

        Returns:
            影响力分数
        """
        components = {}

        # 1. 平台权重 (0-100)
        platform = mention.platform
        if isinstance(platform, str):
            try:
                platform = Platform(platform)
            except ValueError:
                platform = Platform.GITHUB
        platform_weight = self.config.platform_weights.get(
            platform,
            0.5
        )
        components['platform'] = platform_weight * 100

        # 2. 互动指标 (0-100)
        engagement_score = self._calculate_engagement(mention)
        components['engagement'] = engagement_score

        # 3. 作者评分 (0-100)
        author_score = self._assess_author(mention.author)
        components['author'] = author_score

        # 4. 内容质量 (0-100)
        content_score = self._assess_content(mention)
        components['content'] = content_score

        # 5. 时效性 (0-100)
        recency_score = self._assess_recency(mention.published_at)
        components['recency'] = recency_score

        # 综合评分
        total_score = (
            components['engagement'] * self.config.engagement_weight +
            components['author'] * self.config.author_weight +
            components['content'] * self.config.content_weight +
            components['recency'] * self.config.recency_weight
        ) * platform_weight

        # 确保在0-100范围内
        total_score = max(0, min(100, total_score))

        # 确定等级 (使用常量类)
        level = InfluenceThresholds.get_level(total_score)

        return InfluenceScore(
            mention_id=mention.source_id,
            platform=mention.platform,
            score=round(total_score, 1),
            level=level,
            components=components,
        )

    def _calculate_engagement(self, mention: MentionData) -> float:
        """计算互动指标分数

        Args:
            mention: 提及数据

        Returns:
            分数 (0-100)
        """
        # 根据平台获取不同的互动指标
        if mention.platform == Platform.REDDIT:
            raw_score = mention.score + mention.comments * 2
        elif mention.platform == Platform.HACKERNEWS:
            raw_score = mention.points + mention.comments * 2
        elif mention.platform == Platform.GITHUB:
            # GitHub: reactions + comments
            reactions = sum(
                mention.reactions.values()) if isinstance(
                mention.reactions, dict) else 0
            raw_score = reactions + mention.comments * 3
        else:
            raw_score = mention.comments

        # 转换为对数刻度 (避免少数极端值主导)
        import math
        if raw_score <= 0:
            return 0.0

        # 使用对数函数，1000互动≈80分
        score = min(100, 20 * math.log10(raw_score + 1))
        return score

    def _assess_author(self, author: str) -> float:
        """评估作者分数

        Args:
            author: 作者名

        Returns:
            分数 (0-100)
        """
        # 简化版: 检查是否是已知活跃用户
        # 实际应用中可以从数据库查询历史贡献

        # 这里使用简单的启发式规则
        known_authors = {
            'guangda88': 100,  # 项目作者
            # 可以添加其他核心贡献者
        }

        return known_authors.get(author, self.AUTHOR_TIERS['medium'])

    def _assess_content(self, mention: MentionData) -> float:
        """评估内容质量

        Args:
            mention: 提及数据

        Returns:
            分数 (0-100)
        """
        content_length = len(mention.content)

        # 长度评分 (适中最好)
        if content_length == 0:
            length_score = 20
        elif content_length < 50:
            length_score = 40
        elif content_length < 200:
            length_score = 80
        elif content_length < 1000:
            length_score = 100
        else:
            length_score = 90  # 太长可能冗余

        # 标题加分
        title_score = 30 if mention.title else 0

        return (length_score + title_score) / 2

    def _assess_recency(self, published_at: str) -> float:
        """评估时效性

        Args:
            published_at: 发布时间

        Returns:
            分数 (0-100)
        """
        from datetime import datetime, timedelta

        try:
            if 'T' in published_at:
                dt = datetime.fromisoformat(
                    published_at.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(published_at)
        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to parse publish date: {e}")
            return 50.0

        age_hours = (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600

        # 使用常量类进行指数衰减
        if age_hours < RecencyDecay.FRESH_HOURS:
            return RecencyDecay.FRESH_SCORE
        elif age_hours < RecencyDecay.DAY_HOURS:
            return RecencyDecay.DAY_SCORE
        elif age_hours < RecencyDecay.WEEK_HOURS:
            return RecencyDecay.WEEK_SCORE
        elif age_hours < RecencyDecay.MONTH_HOURS:
            return RecencyDecay.MONTH_SCORE
        else:
            return RecencyDecay.OLD_SCORE

    def get_top_influential(
        self,
        mentions: List[MentionData],
        limit: int = 10
    ) -> List[InfluenceScore]:
        """获取最有影响力的提及

        Args:
            mentions: 提及数据列表
            limit: 返回数量

        Returns:
            影响力分数列表（降序）
        """
        scores = [self.calculate_score(m) for m in mentions]
        scores.sort(key=lambda s: s.score, reverse=True)
        return scores[:limit]


def main():
    """主函数 - 测试分析器"""
    print("=" * 60)
    print("📊 影响力分析器测试")
    print("=" * 60)
    print()

    from ..models.common import Platform, SourceType

    # 创建测试数据
    test_mentions = [
        MentionData(
            platform=Platform.HACKERNEWS,
            source_type=SourceType.POST,
            source_id="1",
            author="famous_user",
            content="This is a great tool for automation!",
            url="https://example.com/1",
            published_at="2026-04-03T10:00:00",
            title="LingFlow: Amazing AI Tool",
            points=150,
            comments=45,
        ),
        MentionData(
            platform=Platform.REDDIT,
            source_type=SourceType.POST,
            source_id="2",
            author="regular_user",
            content="Just discovered LingFlow, pretty cool.",
            url="https://example.com/2",
            published_at="2026-04-02T15:00:00",
            title="Found a useful tool",
            score=25,
            upvote_ratio=0.9,
            comments=8,
        ),
        MentionData(
            platform=Platform.GITHUB,
            source_type=SourceType.ISSUE,
            source_id="3",
            author="newbie",
            content="Help with installation?",
            url="https://example.com/3",
            published_at="2026-04-01T08:00:00",
            title="Installation issue",
            comments=2,
        ),
    ]

    analyzer = InfluenceAnalyzer()

    # 分析
    result = analyzer.analyze(test_mentions)

    print("📈 分析结果:")
    print(f"  总数: {result['total']}")
    print(f"  平均分: {result['summary']['avg_score']:.1f}")
    print(f"  最高分: {result['summary']['max_score']:.1f}")
    print(f"  最低分: {result['summary']['min_score']:.1f}")
    print(f"  高影响力: {result['summary']['high_influence']}")
    print(f"  中影响力: {result['summary']['medium_influence']}")
    print(f"  低影响力: {result['summary']['low_influence']}")

    print()
    print("🔝 TOP影响力:")
    top = analyzer.get_top_influential(test_mentions, limit=5)
    for i, score in enumerate(top, 1):
        print(f"  [{i}] {score.mention_id}: {score.score} ({score.level})")

    print()
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
