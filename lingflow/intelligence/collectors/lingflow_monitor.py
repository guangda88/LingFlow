"""lingflow 项目监控器 - 监控GitHub上的Issues、Discussions和评价

收集网络世界对lingflow系统的讨论和评价。
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


@dataclass
class MentionData:
    """提及数据模型"""

    platform: str = "github"
    source_type: str = ""  # issue, discussion, post, comment
    source_id: str = ""
    author: str = ""
    content: str = ""
    url: str = ""
    published_at: str = ""
    collected_at: str = ""
    metrics: Dict = field(default_factory=dict)
    # GitHub 特有字段
    title: str = ""
    state: str = ""
    labels: List[str] = field(default_factory=list)
    reactions: Dict = field(default_factory=dict)
    comments: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "platform": self.platform,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "author": self.author,
            "content": self.content,
            "url": self.url,
            "published_at": self.published_at,
            "collected_at": self.collected_at,
            "metrics": self.metrics,
            "title": self.title,
            "state": self.state,
            "labels": self.labels,
            "reactions": self.reactions,
            "comments": self.comments,
        }


class lingflowMonitor:
    """lingflow项目监控器

    监控GitHub上关于lingflow的讨论和评价，包括Issues和Discussions。
    """

    # 搜索关键词 - 用于在第三方平台搜索
    SEARCH_KEYWORDS = ["lingflow", "lingflow-core", "lingflow.ai", "灵通工程流"]

    def __init__(self, repo: str = "guangda88/lingflow", token: Optional[str] = None):
        """初始化监控器

        Args:
            repo: GitHub仓库 (格式: owner/repo)
            token: GitHub Personal Access Token
        """
        self.repo = repo
        self.owner, self.repo_name = repo.split("/")
        self.token = token or os.getenv("GITHUB_TOKEN", "")

        # GitHub API配置
        self.api_base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

        # 数据存储路径
        self.data_dir = Path(".lingflow/intelligence/raw/github")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """发送GET请求到GitHub API"""
        url = f"{self.api_base}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            print(f"  ❌ API请求失败: {e}")
            return {}

    def _paginated_get(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """分页GET请求"""
        results = []
        page = 1

        while True:
            if params:
                params["page"] = page
            else:
                params = {"page": page}

            data = self._get(endpoint, params)
            if not data:
                break

            if isinstance(data, list):
                if not data:
                    break
                results.extend(data)
            elif isinstance(data, dict) and "items" in data:
                results.extend(data["items"])
                # 检查是否还有更多页
                if len(results) >= data.get("total_count", len(results)):
                    break
            else:
                break

            page += 1
            if page > 10:  # 安全限制
                break

        return results

    def collect_issues(self, state: str = "open", days: int = 7) -> List[MentionData]:
        """采集Issues

        Args:
            state: issue状态 (open, closed, all)
            days: 只获取最近N天的问题

        Returns:
            MentionData列表
        """
        print(f"  📋 采集Issues (state={state}, days={days})...")

        issues = self._paginated_get(
            f"repos/{self.repo}/issues", {"state": state, "sort": "created", "direction": "desc", "per_page": 30}
        )

        mentions = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for issue in issues:
            # 过滤Pull Requests
            if "pull_request" in issue:
                continue

            # 时间过滤
            created_at = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
            if created_at < cutoff_date:
                continue

            mention = MentionData(
                platform="github",
                source_type="issue",
                source_id=str(issue["id"]),
                author=issue["user"]["login"],
                content=issue["body"] or "",
                url=issue["html_url"],
                published_at=issue["created_at"],
                collected_at=datetime.now().isoformat(),
                title=issue["title"],
                state=issue["state"],
                labels=[label["name"] for label in issue.get("labels", [])],
                reactions=issue.get("reactions", {}),
                comments=issue.get("comments", 0),
                metrics={
                    "stars": sum(r.get("count", 0) for r in issue.get("reactions", [])),
                    "comments": issue.get("comments", 0),
                },
            )
            mentions.append(mention)

        print(f"    找到 {len(mentions)} 个Issues")
        return mentions

    def collect_discussions(self, days: int = 7) -> List[MentionData]:
        """采集Discussions

        Args:
            days: 只获取最近N天的讨论

        Returns:
            MentionData列表
        """
        print(f"  💬 采集Discussions (days={days})...")

        discussions = self._paginated_get(
            f"repos/{self.repo}/discussions", {"sort": "created", "direction": "desc", "per_page": 30}
        )

        mentions = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for discussion in discussions:
            # 时间过滤
            created_at = datetime.fromisoformat(discussion["created_at"].replace("Z", "+00:00"))
            if created_at < cutoff_date:
                continue

            mention = MentionData(
                platform="github",
                source_type="discussion",
                source_id=str(discussion["id"]),
                author=discussion["user"]["login"],
                content=discussion.get("body") or "",
                url=discussion["html_url"],
                published_at=discussion["created_at"],
                collected_at=datetime.now().isoformat(),
                title=discussion["title"],
                state="open",
                labels=[],
                reactions=discussion.get("reactions", {}),
                comments=discussion.get("comments", 0),
                metrics={
                    "stars": discussion.get("reaction_groups", {}),
                    "comments": discussion.get("comments", 0),
                    "replies": discussion.get("reply_count", 0),
                },
            )
            mentions.append(mention)

        print(f"    找到 {len(mentions)} 个Discussions")
        return mentions

    def collect_releases(self) -> List[MentionData]:
        """采集Releases（了解用户反馈）"""
        print("  📦 采集Releases...")

        # 获取最新release
        data = self._get(f"repos/{self.repo}/releases/latest")
        if not data:
            print("    未找到Releases")
            return []

        # 获取最近5个releases
        releases = self._paginated_get(f"repos/{self.repo}/releases", {"per_page": 5})

        mentions = []
        for release in releases:
            mention = MentionData(
                platform="github",
                source_type="release",
                source_id=str(release["id"]),
                author=release["author"]["login"],
                content=release.get("body") or "",
                url=release["html_url"],
                published_at=release["created_at"],
                collected_at=datetime.now().isoformat(),
                title=release["name"] or release["tag_name"],
                state="published",
                labels=[],
                reactions=release.get("reactions", {}),
                metrics={
                    "stars": release.get("reactions", {}).get("total_count", 0),
                    "downloads": 0,  # 暂不支持
                    "tag_name": release.get("tag_name"),
                },
            )
            mentions.append(mention)

        print(f"    找到 {len(mentions)} 个Releases")
        return mentions

    def save_data(self, mentions: List[MentionData]) -> Path:
        """保存采集的数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_file = self.data_dir / f"mentions_{timestamp}.json"

        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "repo": self.repo,
                    "count": len(mentions),
                    "mentions": [m.to_dict() for m in mentions],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"  💾 数据已保存: {data_file}")
        return data_file

    def generate_summary(self, mentions: List[MentionData]) -> Dict[str, Any]:
        """生成汇总统计"""
        summary = {
            "total": len(mentions),
            "by_type": {},
            "by_state": {},
            "total_comments": sum(m.comments for m in mentions),
            "top_authors": {},
        }

        # 按类型统计
        for m in mentions:
            summary["by_type"][m.source_type] = summary["by_type"].get(m.source_type, 0) + 1
            if m.state:
                summary["by_state"][m.state] = summary["by_state"].get(m.state, 0) + 1

        # 按作者统计
        authors: dict[str, int] = {}
        for m in mentions:
            authors[m.author] = authors.get(m.author, 0) + 1
        summary["top_authors"] = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]

        return summary


def main():
    """主函数 - 测试监控器"""
    print("=" * 60)
    print("🔍 lingflow 项目监控器")
    print("=" * 60)
    print()

    monitor = lingflowMonitor()

    # 采集最近7天的数据
    all_mentions = []

    all_mentions.extend(monitor.collect_issues(state="open", days=7))
    all_mentions.extend(monitor.collect_discussions(days=7))
    all_mentions.extend(monitor.collect_releases())

    if all_mentions:
        # 保存数据
        monitor.save_data(all_mentions)

        # 生成汇总
        summary = monitor.generate_summary(all_mentions)

        print()
        print("📊 采集汇总:")
        print(f"  总提及: {summary['total']} 条")
        print(f"  按类型: {summary['by_type']}")
        print(f"  按状态: {summary['by_state']}")
        print(f"  总评论: {summary['total_comments']}")
        top_authors_list = list(summary["top_authors"])[:3]
        print(f"  活跃作者: {dict(top_authors_list)}")
    else:
        print("  未采集到数据")

    print()
    print("✅ 监控完成")


if __name__ == "__main__":
    main()
