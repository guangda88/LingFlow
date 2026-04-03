"""情报系统数据模型测试

测试MentionData、SentimentResult等数据类。
"""

import pytest  # noqa

from lingflow.intelligence.models.common import (
    MentionData,
    Platform,
    SourceType,
    SentimentLabel,
    TrendDirection,
    SentimentResult,
    InfluenceScore,
    TrendMetrics,
    DailyReport,
)


class TestMentionData:
    """MentionData测试"""

    def test_creation(self):
        """测试创建MentionData"""
        mention = MentionData(
            platform=Platform.GITHUB,
            source_type=SourceType.ISSUE,
            source_id="test-1",
            author="test_user",
            content="Test content",
            url="https://example.com/1",
            published_at="2026-04-04T10:00:00",
        )

        assert mention.platform == Platform.GITHUB
        assert mention.source_type == SourceType.ISSUE
        assert mention.author == "test_user"
        assert mention.content == "Test content"

    def test_to_dict(self):
        """测试转换为字典"""
        mention = MentionData(
            platform=Platform.REDDIT,
            source_type=SourceType.POST,
            source_id="reddit-1",
            author="redditor",
            content="Reddit post content",
            url="https://reddit.com/r/test/1",
            published_at="2026-04-04T10:00:00",
            subreddit="Python",
            score=100,
            upvote_ratio=0.9,
        )

        data = mention.to_dict()

        assert data["platform"] == "reddit"
        assert data["source_type"] == "post"
        assert data["subreddit"] == "Python"
        assert data["score"] == 100

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "platform": "hackernews",
            "source_type": "post",
            "source_id": "hn-1",
            "author": "hn_user",
            "content": "HN post",
            "url": "https://news.ycombinator.com/item?id=1",
            "published_at": "2026-04-04T10:00:00",
            "points": 50,
            "rank": 5,
        }

        mention = MentionData.from_dict(data)

        assert mention.platform == Platform.HACKERNEWS
        assert mention.source_type == SourceType.POST
        assert mention.points == 50


class TestSentimentResult:
    """SentimentResult测试"""

    def test_creation(self):
        """测试创建SentimentResult"""
        result = SentimentResult(
            text="Great tool!",
            score=0.8,
            label=SentimentLabel.POSITIVE,
            confidence=0.9,
            key_words=["great"],
        )

        assert result.label == SentimentLabel.POSITIVE
        assert result.score == 0.8
        assert result.confidence == 0.9

    def test_to_dict(self):
        """测试转换为字典"""
        # 使用超过100字符的文本
        long_text = (
            "This is a very long text that should be truncated when "
            "converted to dictionary and it contains even more characters "
            "to ensure it exceeds one hundred characters limit"
        )
        result = SentimentResult(
            text=long_text,
            score=0.5,
            label=SentimentLabel.NEUTRAL,
            confidence=0.7,
            key_words=["long", "text"],
        )

        data = result.to_dict()

        assert len(data["text"]) <= 103  # 100 + "..."
        assert "..." in data["text"]


class TestInfluenceScore:
    """InfluenceScore测试"""

    def test_creation(self):
        """测试创建InfluenceScore"""
        score = InfluenceScore(
            mention_id="test-1",
            platform=Platform.GITHUB,
            score=85.5,
            level="high",
            components={"engagement": 90, "author": 80},
        )

        assert score.score == 85.5
        assert score.level == "high"
        assert score.components["engagement"] == 90


class TestTrendMetrics:
    """TrendMetrics测试"""

    def test_creation(self):
        """测试创建TrendMetrics"""
        metrics = TrendMetrics(
            metric_name="star_count",
            current_value=100.0,
            previous_value=80.0,
            change_percent=25.0,
            trend_direction=TrendDirection.UP,
        )

        assert metrics.metric_name == "star_count"
        assert metrics.change_percent == 25.0
        assert metrics.trend_direction == TrendDirection.UP


class TestDailyReport:
    """DailyReport测试"""

    def test_creation(self):
        """测试创建DailyReport"""
        report = DailyReport(
            date="2026-04-04",
            summary="Test summary",
            metrics={"total": 10},
            highlights=["Highlight 1"],
            concerns=[],
            sentiment_summary={"positive": 5, "neutral": 3, "negative": 2},
            top_topics=["topic1", "topic2"],
            actionable_insights=["Insight 1"],
        )

        assert report.date == "2026-04-04"
        assert len(report.highlights) == 1
        assert report.sentiment_summary["positive"] == 5

    def test_format_terminal(self):
        """测试终端格式化"""
        report = DailyReport(
            date="2026-04-04",
            summary="今日共收录 10 条讨论",
            metrics={"total_mentions": 10},
            highlights=["Great feedback!"],
            concerns=[],
            sentiment_summary={
                "positive": 7,
                "neutral": 2,
                "negative": 1,
                "total": 10},
            top_topics=["automation", "ai"],
            actionable_insights=["Keep improving"],
        )

        output = report.format_terminal()

        assert "2026-04-04" in output
        assert "10 条讨论" in output
        assert "Great feedback!" in output
        assert "automation" in output
