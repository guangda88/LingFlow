"""Hacker News 采集器

采集Hacker News上关于LingFlow的讨论。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from ..models.common import MentionData, Platform, SourceType
from .base import BaseCollector, CollectorConfig


class HNCollector(BaseCollector):
    """Hacker News 采集器

    使用 Algolia HN Search API
    API文档: https://hn.algolia.com/api
    """

    PLATFORM = Platform.HACKERNEWS
    NAME = "hackernews"
    DESCRIPTION = "Hacker News 采集器"

    # API配置
    API_BASE = "http://hn.algolia.com/api/v1"

    # 搜索关键词
    SEARCH_KEYWORDS = ["LingFlow", "lingflow-core", "lingflow.ai", "灵通工程流"]

    def __init__(self, config: Optional[CollectorConfig] = None):
        """初始化采集器"""
        super().__init__(config)
        self.keywords = self.SEARCH_KEYWORDS

    def collect(self, **kwargs) -> List[MentionData]:
        return self.search_mentions(**kwargs)

    def search_mentions(
        self, keywords: Optional[List[str]] = None, limit: int = 100, days: int = 7, use_cache: bool = True
    ) -> List[MentionData]:
        """搜索提及

        Args:
            keywords: 搜索关键词
            limit: 最大结果数
            days: 最近N天
            use_cache: 是否使用缓存

        Returns:
            MentionData列表
        """
        keywords = keywords or self.keywords

        print("  🔍 Hacker News搜索...")
        print(f"    关键词: {', '.join(keywords)}")

        # 检查缓存
        cache_key = self.get_cache_key(keywords=",".join(keywords), limit=limit)
        if use_cache:
            cached = self.load_cache(cache_key)
            if cached:
                print(f"    使用缓存: {len(cached)}条")
                return cached

        all_mentions = []
        cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())

        for keyword in keywords:
            mentions = self._search_keyword(keyword, cutoff_timestamp, limit)
            all_mentions.extend(mentions)

        # 去重
        seen_ids = set()
        unique_mentions = []
        for m in all_mentions:
            if m.source_id not in seen_ids:
                seen_ids.add(m.source_id)
                unique_mentions.append(m)

        print(f"    找到: {len(unique_mentions)}条")

        # 保存缓存
        if use_cache:
            self.save_cache(cache_key, unique_mentions)

        return unique_mentions[:limit]

    def _search_keyword(self, keyword: str, cutoff_timestamp: int, limit: int) -> List[MentionData]:
        """搜索单个关键词

        Args:
            keyword: 关键词
            cutoff_timestamp: 截止时间戳
            limit: 结果数限制

        Returns:
            MentionData列表
        """
        mentions = []

        try:
            # 搜索参数
            params = {
                "query": keyword,
                "tags": "story,comment",  # 搜索故事和评论
                "numericFilters": f"created_at_i>{cutoff_timestamp}",
                "hitsPerPage": min(200, limit),
            }

            url = f"{self.API_BASE}/search"
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", [])

                for hit in hits:
                    mention = self._parse_hit(hit)
                    if mention:
                        mentions.append(mention)

        except Exception as e:
            print(f"    搜索失败 ({keyword}): {e}")

        return mentions

    def _parse_hit(self, hit: Dict) -> Optional[MentionData]:
        """解析搜索结果

        Args:
            hit: Algolia API返回的结果

        Returns:
            MentionData或None
        """
        try:
            # 确定类型
            hit_type = hit.get("type", "story")
            if hit_type == "story":
                source_type = SourceType.POST
            elif hit_type == "comment":
                source_type = SourceType.COMMENT
            else:
                source_type = SourceType.POST

            # 解析时间
            created_at = hit.get("created_at", "")
            try:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                dt = datetime.fromtimestamp(hit.get("created_at_i", 0))

            # 获取作者
            author = hit.get("author", "") or hit.get("username", "")

            # 获取内容
            text = hit.get("text", "") or hit.get("title", "") or ""

            # 获取URL
            url = hit.get("url", "")
            if not url:
                object_id = hit.get("objectID", "")
                url = f"https://news.ycombinator.com/item?id={object_id}"

            return MentionData(
                platform=Platform.HACKERNEWS,
                source_type=source_type,
                source_id=str(hit.get("objectID", "")),
                author=author,
                content=text[:2000],
                url=url,
                published_at=dt.isoformat(),
                title=hit.get("title", ""),
                points=hit.get("points", 0),
                comments=hit.get("children", 0) or hit.get("num_comments", 0),
                rank=hit.get("rank", 0),
                metrics={
                    "points": hit.get("points", 0),
                    "num_comments": hit.get("children", 0) or hit.get("num_comments", 0),
                    "rank": hit.get("rank", 0),
                    "object_id": hit.get("objectID", ""),
                },
            )
        except Exception as e:
            print(f"      解析失败: {e}")
            return None

    def get_front_page(self, limit: int = 30) -> List[MentionData]:
        """获取首页热门

        Args:
            limit: 获取数量

        Returns:
            MentionData列表
        """
        print("  📰 获取HN首页...")

        mentions = []

        try:
            # 获取首页故事
            url = f"{self.API_BASE}/search"
            params = {
                "tags": "front_page",
                "hitsPerPage": limit,
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", [])

                for hit in hits:
                    mention = self._parse_hit(hit)
                    if mention:
                        mentions.append(mention)

        except Exception as e:
            print(f"    获取失败: {e}")

        print(f"    找到: {len(mentions)}条")
        return mentions

    def get_trending(self, limit: int = 30) -> List[MentionData]:
        """获取当前热门

        Args:
            limit: 获取数量

        Returns:
            MentionData列表
        """
        print("  🔥 获取HN热门...")

        mentions = []

        try:
            # 获取最近24小时的热门
            url = f"{self.API_BASE}/search_by_date"
            params = {
                "tags": "story",
                "numericFilters": "created_at_i>86400",
                "hitsPerPage": limit,
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", [])

                for hit in hits:
                    mention = self._parse_hit(hit)
                    if mention:
                        mentions.append(mention)

        except Exception as e:
            print(f"    获取失败: {e}")

        print(f"    找到: {len(mentions)}条")
        return mentions


def main():
    """主函数 - 测试采集器"""
    print("=" * 60)
    print("🔍 Hacker News 采集器测试")
    print("=" * 60)
    print()

    collector = HNCollector()

    # 搜索提及
    mentions = collector.search_mentions(keywords=["LingFlow", "Claude Code"], limit=50, days=30)

    print()
    print("📊 采集结果:")
    print(f"  总数: {len(mentions)}")

    if mentions:
        # 生成汇总
        summary = collector.generate_summary(mentions)
        print(f"  平台: {summary['platform']}")
        print(f"  独立作者: {summary['unique_authors']}")
        print(f"  总评论: {summary['total_comments']}")

        # 显示前几条
        print()
        print("🔝 热门讨论:")
        sorted_mentions = sorted(mentions, key=lambda m: m.points, reverse=True)[:5]

        for i, m in enumerate(sorted_mentions, 1):
            print(f"  [{i}] {m.title[:50]}... ({m.points}👍)")
            print(f"      {m.author} | {m.comments}💬")

        # 保存数据
        filepath = collector.save_data(mentions)
        print()
        print(f"💾 数据已保存: {filepath}")

    print()
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
