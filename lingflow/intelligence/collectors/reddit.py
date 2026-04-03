"""Reddit讨论采集器

采集Reddit上关于LingFlow的讨论。
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests

from .base import BaseCollector, CollectorConfig
from ..models.common import MentionData, Platform, SourceType


class RedditCollector(BaseCollector):
    """Reddit讨论采集器

    使用Reddit API (无需认证的只读模式)
    或使用rss2json作为备选方案
    """

    PLATFORM = Platform.REDDIT
    NAME = "reddit"
    DESCRIPTION = "Reddit讨论采集器"

    # 默认搜索的子版块
    DEFAULT_SUBREDDITS = [
        "Python",
        "LocalLLaMA",
        "learnprogramming",
        "LanguageTechnology",
        "MachineLearning",
        "linux",
        "opensource",
    ]

    # 搜索关键词
    SEARCH_KEYWORDS = ["LingFlow", "lingflow-core", "lingflow.ai"]

    def __init__(self, config: Optional[CollectorConfig] = None):
        """初始化采集器"""
        super().__init__(config)
        self.subreddits = self.DEFAULT_SUBREDDITS
        self.keywords = self.SEARCH_KEYWORDS

        # Reddit API配置
        self.api_base = "https://www.reddit.com"
        self.user_agent = "LingFlow-Intelligence/1.0"

        # 备选: 使用rss2json
        self.rss2json_api = "https://api.rss2json.com/v1/api.json"

    def search_mentions(
        self,
        keywords: Optional[List[str]] = None,
        subreddits: Optional[List[str]] = None,
        limit: int = 100,
        days: int = 7,
        use_cache: bool = True
    ) -> List[MentionData]:
        """搜索提及

        Args:
            keywords: 搜索关键词
            subreddits: 子版块列表
            limit: 最大结果数
            days: 最近N天
            use_cache: 是否使用缓存

        Returns:
            MentionData列表
        """
        keywords = keywords or self.keywords
        subreddits = subreddits or self.subreddits

        print("  🔍 Reddit搜索...")
        print(f"    关键词: {', '.join(keywords)}")
        print(f"    子版块: {', '.join(subreddits)}")

        # 检查缓存
        cache_key = self.get_cache_key(
            keywords=','.join(keywords),
            subreddits=','.join(subreddits),
            limit=limit
        )
        if use_cache:
            cached = self.load_cache(cache_key)
            if cached:
                print(f"    使用缓存: {len(cached)}条")
                return cached

        all_mentions = []
        cutoff = datetime.now() - timedelta(days=days)

        # 方案1: 使用Reddit搜索API (无需认证)
        all_mentions.extend(self._search_via_reddit_api(
            keywords, limit, days, cutoff
        ))

        # 方案2: 如果API结果不足，使用rss2json
        if len(all_mentions) < 10:
            all_mentions.extend(self._search_via_rss(
                subreddits, keywords, limit
            ))

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

    def _search_via_reddit_api(
        self,
        keywords: List[str],
        limit: int,
        days: int,
        cutoff: datetime
    ) -> List[MentionData]:
        """使用Reddit搜索API"""
        mentions = []

        for keyword in keywords:
            try:
                # Reddit搜索URL
                url = f"{self.api_base}/search.json"
                params = {
                    'q': keyword,
                    'restrict_sr': 'false',  # 搜索整个Reddit
                    'sort': 'new',
                    'limit': min(100, limit),
                }

                headers = {'User-Agent': self.user_agent}

                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])

                    for post_data in posts:
                        post = post_data.get('data', {})
                        mention = self._parse_post(post, cutoff)
                        if mention:
                            mentions.append(mention)

            except Exception as e:
                print(f"    Reddit API搜索失败 ({keyword}): {e}")

        return mentions

    def _search_via_rss(
        self,
        subreddits: List[str],
        keywords: List[str],
        limit: int
    ) -> List[MentionData]:
        """使用rss2json获取子版块内容"""
        mentions = []

        for subreddit in subreddits[:5]:  # 限制子版块数量
            try:
                rss_url = f"{self.api_base}/r/{subreddit}/hot.json"
                params = {'limit': 50}
                headers = {'User-Agent': self.user_agent}

                response = requests.get(
                    rss_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])

                    for post_data in posts:
                        post = post_data.get('data', {})

                        # 检查是否包含关键词
                        title = post.get('title', '').lower()
                        text = post.get('selftext', '').lower()
                        combined = f"{title} {text}"

                        if any(k.lower() in combined for k in keywords):
                            mention = self._parse_post(post)
                            if mention:
                                mentions.append(mention)

            except Exception as e:
                print(f"    RSS获取失败 (r/{subreddit}): {e}")

        return mentions

    def _parse_post(self, post: Dict,
                    cutoff: Optional[datetime] = None) -> Optional[MentionData]:
        """解析Reddit帖子数据

        Args:
            post: Reddit API返回的帖子数据
            cutoff: 截止时间

        Returns:
            MentionData或None
        """
        try:
            # 解析时间
            created_utc = post.get('created_utc', 0)
            created_at = datetime.fromtimestamp(created_utc)

            if cutoff and created_at < cutoff:
                return None

            return MentionData(
                platform=Platform.REDDIT,
                source_type=SourceType.POST,
                source_id=str(post.get('id', '')),
                author=post.get('author', '[unknown]'),
                content=post.get('selftext', '')[:2000],
                url=f"https://reddit.com{post.get('permalink', '')}",
                published_at=created_at.isoformat(),
                title=post.get('title', ''),
                subreddit=post.get('subreddit', ''),
                score=post.get('score', 0),
                upvote_ratio=post.get('upvote_ratio', 0.0),
                comments=post.get('num_comments', 0),
                metrics={
                    'score': post.get('score', 0),
                    'upvote_ratio': post.get('upvote_ratio', 0.0),
                    'num_comments': post.get('num_comments', 0),
                    'total_awards': post.get('total_awards_received', 0),
                }
            )
        except Exception as e:
            print(f"      解析失败: {e}")
            return None

    def get_subreddit_info(self, subreddit: str) -> Optional[Dict]:
        """获取子版块信息

        Args:
            subreddit: 子版块名称

        Returns:
            子版块信息字典
        """
        try:
            url = f"{self.api_base}/r/{subreddit}/about.json"
            headers = {'User-Agent': self.user_agent}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'name': data.get('display_name'),
                    'subscribers': data.get('subscribers', 0),
                    'active_users': data.get('active_user_count', 0),
                    'description': data.get('public_description', ''),
                }
        except Exception as e:
            print(f"    获取子版块信息失败: {e}")

        return None


def main():
    """主函数 - 测试采集器"""
    print("=" * 60)
    print("🔍 Reddit 采集器测试")
    print("=" * 60)
    print()

    collector = RedditCollector()

    # 搜索提及
    mentions = collector.search_mentions(
        keywords=["LingFlow", "Claude"],
        limit=50,
        days=7
    )

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
        print("🔝 热门帖子:")
        sorted_mentions = sorted(
            mentions,
            key=lambda m: m.score,
            reverse=True
        )[:5]

        for i, m in enumerate(sorted_mentions, 1):
            print(f"  [{i}] {m.title[:50]}... ({m.score}👍)")
            if m.subreddit:
                print(f"      r/{m.subreddit} | {m.author}")

        # 保存数据
        filepath = collector.save_data(mentions)
        print()
        print(f"💾 数据已保存: {filepath}")

    print()
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
