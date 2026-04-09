"""情报采集器测试

测试RedditCollector、HNCollector等采集器。
"""

from unittest.mock import MagicMock, Mock, patch

import pytest  # noqa

from lingflow.intelligence.collectors.base import CollectorConfig, CollectorManager
from lingflow.intelligence.collectors.hackernews import HNCollector
from lingflow.intelligence.collectors.reddit import RedditCollector
from lingflow.intelligence.models.common import Platform, SourceType


class TestRedditCollector:
    """RedditCollector测试"""

    def test_initialization(self):
        """测试初始化"""
        collector = RedditCollector()

        assert collector.PLATFORM == Platform.REDDIT
        assert collector.NAME == "reddit"
        assert len(collector.subreddits) > 0
        assert len(collector.keywords) > 0

    def test_search_mentions_with_cache(self):
        """测试缓存功能"""
        collector = RedditCollector()

        # Mock缓存
        with patch.object(collector, "load_cache", return_value=[]):
            result = collector.search_mentions(use_cache=True)

        # 应该调用load_cache
        assert isinstance(result, list)

    def test_parse_post(self):
        """测试帖子解析"""
        collector = RedditCollector()

        # 模拟Reddit API返回数据
        post_data = {
            "id": "test123",
            "author": "test_user",
            "title": "Test Post",
            "selftext": "Test content about LingFlow",
            "permalink": "/r/test/comments/test123/",
            "created_utc": 1712236800,  # 2024-04-04
            "score": 100,
            "upvote_ratio": 0.9,
            "num_comments": 50,
            "subreddit": "Python",
        }

        mention = collector._parse_post(post_data)

        assert mention.platform == Platform.REDDIT
        assert mention.source_type == SourceType.POST
        assert mention.author == "test_user"
        assert mention.title == "Test Post"
        assert mention.subreddit == "Python"
        assert mention.score == 100


class TestHNCollector:
    """HNCollector测试"""

    def test_initialization(self):
        """测试初始化"""
        collector = HNCollector()

        assert collector.PLATFORM == Platform.HACKERNEWS
        assert collector.NAME == "hackernews"
        assert len(collector.keywords) > 0

    def test_parse_hit(self):
        """测试结果解析"""
        collector = HNCollector()

        # 模拟HN API返回数据
        hit_data = {
            "objectID": "12345",
            "author": "hn_user",
            "title": "LingFlow Discussion",
            "url": "https://example.com",
            "created_at": "2026-04-04T10:00:00.000Z",
            "points": 80,
            "children": 20,
            "num_comments": 20,
            "rank": 5,
            "type": "story",
        }

        mention = collector._parse_hit(hit_data)

        assert mention.platform == Platform.HACKERNEWS
        assert mention.source_type == SourceType.POST
        assert mention.author == "hn_user"
        assert mention.points == 80
        assert mention.rank == 5


class TestCollectorManager:
    """CollectorManager测试"""

    def test_initialization(self):
        """测试初始化"""
        manager = CollectorManager()

        assert isinstance(manager.collectors, dict)
        assert manager.list_collectors() == []

    def test_register_and_get(self):
        """测试注册和获取采集器"""
        manager = CollectorManager()
        collector = RedditCollector()

        manager.register("reddit", collector)

        assert "reddit" in manager.list_collectors()
        assert manager.get("reddit") is collector
        assert manager.get("nonexistent") is None

    def test_remove(self):
        """测试移除采集器"""
        manager = CollectorManager()
        collector = RedditCollector()

        manager.register("reddit", collector)
        assert "reddit" in manager.list_collectors()

        result = manager.remove("reddit")
        assert result is True
        assert "reddit" not in manager.list_collectors()

    def test_get_summary(self):
        """测试获取汇总"""
        manager = CollectorManager()

        config = CollectorConfig()
        collector = RedditCollector(config)
        manager.register("reddit", collector)

        summary = manager.get_summary()

        assert summary["total_collectors"] == 1
        assert summary["enabled_collectors"] == 1
        assert "reddit" in summary["collectors"]


class TestCollectorConfig:
    """CollectorConfig测试"""

    def test_defaults(self):
        """测试默认值"""
        config = CollectorConfig()

        assert config.enabled is True
        assert config.rate_limit == 100
        assert config.cache_ttl == 3600
        assert config.max_results == 1000
