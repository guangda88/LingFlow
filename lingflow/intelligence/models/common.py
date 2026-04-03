"""情报系统通用数据模型

定义所有采集、分析、报告共用的数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class Platform(Enum):
    """平台枚举"""
    GITHUB = "github"
    REDDIT = "reddit"
    HACKERNEWS = "hackernews"
    JUEJIN = "juejin"
    ZHIHU = "zhihu"
    V2EX = "v2ex"


class SourceType(Enum):
    """来源类型枚举"""
    ISSUE = "issue"
    DISCUSSION = "discussion"
    PULL_REQUEST = "pull_request"
    RELEASE = "release"
    POST = "post"
    COMMENT = "comment"


class SentimentLabel(Enum):
    """情感标签"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class TrendDirection(Enum):
    """趋势方向"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    UNKNOWN = "unknown"


@dataclass
class MentionData:
    """提及数据模型 - 统一各平台采集的数据格式"""
    platform: Platform
    source_type: SourceType
    source_id: str
    author: str
    content: str
    url: str
    published_at: str
    collected_at: str = field(
        default_factory=lambda: datetime.now().isoformat())
    metrics: Dict[str, Any] = field(default_factory=dict)

    # 可选字段
    title: str = ""
    state: str = ""
    labels: List[str] = field(default_factory=list)
    reactions: Dict[str, Any] = field(default_factory=dict)
    comments: int = 0

    # 平台特有字段
    subreddit: str = ""  # Reddit
    score: int = 0  # Reddit/HN
    upvote_ratio: float = 0.0  # Reddit
    points: int = 0  # HN
    rank: int = 0  # HN

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "platform": self.platform.value if isinstance(self.platform, Platform) else self.platform,
            "source_type": self.source_type.value if isinstance(self.source_type, SourceType) else self.source_type,
            "source_id": self.source_id,
            "author": self.author,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "url": self.url,
            "published_at": self.published_at,
            "collected_at": self.collected_at,
            "metrics": self.metrics,
            "title": self.title,
            "state": self.state,
            "labels": self.labels,
            "reactions": self.reactions,
            "comments": self.comments,
            "subreddit": self.subreddit,
            "score": self.score,
            "upvote_ratio": self.upvote_ratio,
            "points": self.points,
            "rank": self.rank,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MentionData':
        """从字典创建实例"""
        # 处理枚举类型
        platform = data.get('platform', 'unknown')
        if isinstance(platform, str):
            try:
                platform = Platform(platform)
            except ValueError:
                pass

        source_type = data.get('source_type', 'unknown')
        if isinstance(source_type, str):
            try:
                source_type = SourceType(source_type)
            except ValueError:
                pass

        return cls(
            platform=platform,
            source_type=source_type,
            source_id=data['source_id'],
            author=data['author'],
            content=data['content'],
            url=data['url'],
            published_at=data['published_at'],
            collected_at=data.get('collected_at', datetime.now().isoformat()),
            metrics=data.get('metrics', {}),
            title=data.get('title', ''),
            state=data.get('state', ''),
            labels=data.get('labels', []),
            reactions=data.get('reactions', {}),
            comments=data.get('comments', 0),
            subreddit=data.get('subreddit', ''),
            score=data.get('score', 0),
            upvote_ratio=data.get('upvote_ratio', 0.0),
            points=data.get('points', 0),
            rank=data.get('rank', 0),
        )


@dataclass
class SentimentResult:
    """情感分析结果"""
    text: str
    score: float  # -1 到 1
    label: SentimentLabel
    confidence: float  # 0 到 1
    key_words: List[str] = field(default_factory=list)
    analyzed_at: str = field(
        default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        # 截断长文本，超过100字符时截断并添加省略号
        truncated = self.text[:100] + \
            "..." if len(self.text) > 100 else self.text
        return {
            "text": truncated,
            "score": self.score,
            "label": self.label.value if isinstance(self.label, SentimentLabel) else self.label,
            "confidence": self.confidence,
            "key_words": self.key_words,
            "analyzed_at": self.analyzed_at,
        }


@dataclass
class InfluenceScore:
    """影响力分数"""
    mention_id: str
    platform: Platform
    score: float  # 0 到 100
    level: str  # high/medium/low
    components: Dict[str, float] = field(default_factory=dict)
    calculated_at: str = field(
        default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mention_id": self.mention_id,
            "platform": self.platform.value if isinstance(self.platform, Platform) else self.platform,
            "score": self.score,
            "level": self.level,
            "components": self.components,
            "calculated_at": self.calculated_at,
        }


@dataclass
class TrendMetrics:
    """趋势指标"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: TrendDirection
    forecast: Optional[float] = None
    period_start: str = ""
    period_end: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_percent": self.change_percent,
            "trend_direction": self.trend_direction.value if isinstance(self.trend_direction, TrendDirection) else self.trend_direction,
            "forecast": self.forecast,
            "period_start": self.period_start,
            "period_end": self.period_end,
        }


@dataclass
class ReputationMetrics:
    """声誉指标模型"""
    period: str  # daily/weekly/monthly
    start_date: str
    end_date: str

    # 提及统计
    total_mentions: int
    mentions_by_platform: Dict[str, int]
    mentions_by_type: Dict[str, int]

    # 情感统计
    sentiment_score: float  # -1 到 1
    sentiment_distribution: Dict[str, int]  # positive/neutral/negative

    # 增长统计
    star_growth: int
    star_growth_rate: float  # 百分比

    # 影响力统计
    influence_score: float  # 0 到 100
    high_influence_mentions: int

    # 趋势
    trend: TrendDirection

    # 热门话题
    top_topics: List[str]

    generated_at: str = field(
        default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_mentions": self.total_mentions,
            "mentions_by_platform": self.mentions_by_platform,
            "mentions_by_type": self.mentions_by_type,
            "sentiment_score": self.sentiment_score,
            "sentiment_distribution": self.sentiment_distribution,
            "star_growth": self.star_growth,
            "star_growth_rate": self.star_growth_rate,
            "influence_score": self.influence_score,
            "high_influence_mentions": self.high_influence_mentions,
            "trend": self.trend.value if isinstance(self.trend, TrendDirection) else self.trend,
            "top_topics": self.top_topics,
            "generated_at": self.generated_at,
        }


@dataclass
class StargazerData:
    """Star用户数据模型"""
    user: str = ""
    starred_at: str = ""
    collected_at: str = field(
        default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, str]:
        return {
            "user": self.user,
            "starred_at": self.starred_at,
            "collected_at": self.collected_at,
        }


@dataclass
class TopicCluster:
    """话题聚类结果"""
    topic_id: str
    topic_name: str
    keywords: List[str]
    mention_count: int
    sample_mentions: List[str]  # source_id列表
    avg_sentiment: float
    first_seen: str
    last_seen: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "keywords": self.keywords,
            "mention_count": self.mention_count,
            "sample_mentions": self.sample_mentions,
            "avg_sentiment": self.avg_sentiment,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


@dataclass
class DailyReport:
    """每日报告模型"""
    date: str
    summary: str
    metrics: Dict[str, Any]
    highlights: List[str]
    concerns: List[str]
    sentiment_summary: Dict[str, Any]
    top_topics: List[str]
    actionable_insights: List[str]
    trend_metrics: List[TrendMetrics] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "summary": self.summary,
            "metrics": self.metrics,
            "highlights": self.highlights,
            "concerns": self.concerns,
            "sentiment_summary": self.sentiment_summary,
            "top_topics": self.top_topics,
            "actionable_insights": self.actionable_insights,
            "trend_metrics": [t.to_dict() for t in self.trend_metrics],
            "generated_at": self.generated_at,
        }

    def format_terminal(self) -> str:
        """格式化为终端输出"""
        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            f"║        📊 LingFlow 情报简报 - {self.date}                   ║",
            "╠════════════════════════════════════════════════════════════╣",
            "║                                                            ║",
            "║  📋 摘要                                                  ║",
        ]

        for line in self.summary.split('\n'):
            lines.append(f"║    {line:54} ║")

        lines.extend([
            "║                                                            ║",
            "║  📈 今日统计                                               ║",
        ])

        for key, value in self.metrics.items():
            lines.append(
                f"║    • {key}: {value}                                         ║")

        lines.extend([
            "║                                                            ║",
            "║  💬 情感分析                                               ║",
            f"║    积极: {
                self.sentiment_summary.get(
                    'positive',
                    0):.0%}                                    ║",
            f"║    中性: {
                self.sentiment_summary.get(
                    'neutral',
                    0):.0%}                                    ║",
            f"║    消极: {
                self.sentiment_summary.get(
                    'negative',
                    0):.0%}                                    ║",
            "║                                                            ║",
            "║  🔥 热门议题                                               ║",
        ])

        for i, topic in enumerate(self.top_topics[:5], 1):
            lines.append(f"║    {i}. {topic:50} ║")

        lines.extend([
            "║                                                            ║",
            "║  ✅ 亮点                                                  ║",
        ])

        for highlight in self.highlights[:3]:
            lines.append(f"║    • {highlight:50} ║")

        if self.concerns:
            lines.extend([
                "║                                                            ║",
                "║  ⚠️  需要关注                                              ║",
            ])
            for concern in self.concerns[:3]:
                lines.append(f"║    • {concern:50} ║")

        lines.extend([
            "║                                                            ║",
            "╚════════════════════════════════════════════════════════════╝",
        ])

        return '\n'.join(lines)
