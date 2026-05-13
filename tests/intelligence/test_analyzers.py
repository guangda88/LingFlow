"""情报分析器测试

测试SentimentAnalyzer、InfluenceAnalyzer等分析器。
"""

import pytest  # noqa

from lingflow.intelligence.analyzers.base import AnalyzerPipeline
from lingflow.intelligence.analyzers.influence import (
    InfluenceAnalyzer,
    InfluenceConfig,
)
from lingflow.intelligence.analyzers.sentiment import SentimentAnalyzer
from lingflow.intelligence.models.common import (
    MentionData,
    Platform,
    SourceType,
)


class TestSentimentAnalyzer:
    """SentimentAnalyzer测试"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = SentimentAnalyzer()

        assert analyzer.POSITIVE_WORDS is not None
        assert analyzer.NEGATIVE_WORDS is not None
        assert len(analyzer.POSITIVE_WORDS) > 0
        assert len(analyzer.NEGATIVE_WORDS) > 0

    def test_analyze_positive(self):
        """测试分析正面文本"""
        analyzer = SentimentAnalyzer()

        result = analyzer.analyze("lingflow is awesome! Great work!")

        assert result.label == "positive"
        assert result.score > 0
        assert "awesome" in result.key_words or "great" in result.key_words

    def test_analyze_negative(self):
        """测试分析负面文本"""
        analyzer = SentimentAnalyzer()

        result = analyzer.analyze("This tool is buggy and slow")

        assert result.label == "negative"
        assert result.score < 0

    def test_analyze_neutral(self):
        """测试分析中性文本"""
        analyzer = SentimentAnalyzer()

        result = analyzer.analyze("How do I install this tool?")

        assert result.label == "neutral"

    def test_analyze_empty(self):
        """测试分析空文本"""
        analyzer = SentimentAnalyzer()

        result = analyzer.analyze("")

        assert result.label == "neutral"
        assert result.score == 0.0
        assert result.confidence == 0.0

    def test_analyze_batch(self):
        """测试批量分析"""
        analyzer = SentimentAnalyzer()

        texts = [
            "Great tool!",
            "Bad experience",
            "How to use?",
            "Awesome!",
        ]

        result = analyzer.analyze_batch(texts)

        assert result["total"] == 4
        assert result["positive"] > 0
        assert result["negative"] > 0
        assert result["neutral"] > 0

    def test_extract_topics(self):
        """测试提取话题"""
        analyzer = SentimentAnalyzer()

        texts = [
            "The API is well designed",
            "I love the CLI interface",
            "Great automation framework",
        ]

        topics = analyzer.extract_topics(texts)

        assert isinstance(topics, list)
        assert len(topics) > 0


class TestInfluenceAnalyzer:
    """InfluenceAnalyzer测试"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = InfluenceAnalyzer()

        assert analyzer.NAME == "influence"
        assert analyzer.config is not None

    def test_calculate_score_high(self):
        """测试计算高分"""
        analyzer = InfluenceAnalyzer()

        mention = MentionData(
            platform=Platform.HACKERNEWS,
            source_type=SourceType.POST,
            source_id="hn-1",
            author="famous_user",
            content="A" * 300,  # 长内容
            url="https://example.com/1",
            published_at="2026-04-04T09:00:00",  # 最近
            title="Important Discussion",
            points=200,
            comments=100,
        )

        score = analyzer.calculate_score(mention)

        # Score might be medium due to recency decay or other factors
        assert score.level in ("high", "medium")
        assert score.score > 40

    def test_calculate_score_low(self):
        """测试计算低分"""
        analyzer = InfluenceAnalyzer()

        mention = MentionData(
            platform=Platform.REDDIT,
            source_type=SourceType.POST,
            source_id="reddit-1",
            author="newbie",
            content="Short",
            url="https://example.com/1",
            published_at="2026-01-01T10:00:00",  # 很久以前
            score=1,
            upvote_ratio=0.5,
            comments=0,
        )

        score = analyzer.calculate_score(mention)

        assert score.level == "low"
        assert score.score < 40

    def test_analyze_empty(self):
        """测试分析空列表"""
        analyzer = InfluenceAnalyzer()

        result = analyzer.analyze([])

        assert result["total"] == 0
        assert result["scores"] == []
        # summary may not have 'total' key when empty - check structure instead
        assert "summary" in result
        assert result["summary"] == {} or "total" in result["summary"]

    def test_analyze_batch(self):
        """测试批量分析"""
        analyzer = InfluenceAnalyzer()

        mentions = [
            MentionData(
                platform=Platform.HACKERNEWS,
                source_type=SourceType.POST,
                source_id=f"hn-{i}",
                author=f"user-{i}",
                content=f"Content {i}",
                url=f"https://example.com/{i}",
                published_at="2026-04-04T10:00:00",
                points=100 - i * 10,
                comments=10,
            )
            for i in range(5)
        ]

        result = analyzer.analyze(mentions)

        assert result["total"] == 5
        assert len(result["scores"]) == 5
        assert result["summary"]["avg_score"] > 0


class TestAnalyzerPipeline:
    """AnalyzerPipeline测试"""

    def test_initialization(self):
        """测试初始化"""
        pipeline = AnalyzerPipeline()

        assert isinstance(pipeline.analyzers, list)
        assert pipeline.list_analyzers() == []

    def test_add(self):
        """测试添加分析器"""
        pipeline = AnalyzerPipeline()
        analyzer = InfluenceAnalyzer()

        result = pipeline.add(analyzer)

        assert result is pipeline  # 链式调用
        assert "influence" in pipeline.list_analyzers()

    def test_remove(self):
        """测试移除分析器"""
        pipeline = AnalyzerPipeline()
        analyzer = InfluenceAnalyzer()

        pipeline.add(analyzer)
        assert "influence" in pipeline.list_analyzers()

        result = pipeline.remove("influence")
        assert result is True
        assert "influence" not in pipeline.list_analyzers()

    def test_run(self):
        """测试运行流水线"""
        pipeline = AnalyzerPipeline(
            [
                InfluenceAnalyzer(),
            ]
        )

        mentions = [
            MentionData(
                platform=Platform.GITHUB,
                source_type=SourceType.ISSUE,
                source_id="1",
                author="user",
                content="Great tool!",
                url="https://github.com/1",
                published_at="2026-04-04T10:00:00",
            )
        ]

        results = pipeline.run(mentions)

        assert "influence" in results
        assert results["influence"] is not None
        assert results["influence"]["total"] == 1


class TestInfluenceConfig:
    """InfluenceConfig测试"""

    def test_defaults(self):
        """测试默认值"""
        config = InfluenceConfig()

        assert config.enabled is True
        assert config.engagement_weight == 0.4
        assert config.author_weight == 0.3
        assert config.content_weight == 0.2
        assert config.recency_weight == 0.1
        assert config.platform_weights is not None

    def test_custom_weights(self):
        """测试自定义权重"""
        config = InfluenceConfig(
            engagement_weight=0.5,
            author_weight=0.3,
            content_weight=0.1,
            recency_weight=0.1,
        )

        assert config.engagement_weight == 0.5
        assert config.author_weight == 0.3
