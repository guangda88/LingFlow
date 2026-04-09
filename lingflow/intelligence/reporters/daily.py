"""每日情报简报生成器

生成每日情报简报，支持多种输出格式。
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..analyzers.influence import InfluenceAnalyzer
from ..analyzers.sentiment import SentimentAnalyzer
from ..models.common import (
    DailyReport,
    MentionData,
)


@dataclass
class DailyReportConfig:
    """每日报告配置"""

    output_dir: Path = Path(".lingflow/intelligence/reports/daily")
    include_charts: bool = False
    max_highlights: int = 5
    max_concerns: int = 3
    max_topics: int = 10


class DailyReporter:
    """每日情报简报生成器

    从采集的数据生成每日情报简报。
    """

    def __init__(self, config: Optional[DailyReportConfig] = None):
        """初始化报告器

        Args:
            config: 报告器配置
        """
        self.config = config or DailyReportConfig()
        self.output_dir = self.config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 分析器
        self.sentiment_analyzer = SentimentAnalyzer()
        self.influence_analyzer = InfluenceAnalyzer()

    def generate(
        self, mentions: List[MentionData], date: Optional[datetime] = None, star_growth: int = 0, star_count: int = 0
    ) -> DailyReport:
        """生成每日报告

        Args:
            mentions: 提及数据列表
            date: 报告日期
            star_growth: Star增长数
            star_count: 当前Star数

        Returns:
            DailyReport
        """
        date = date or datetime.now()
        date_str = date.strftime("%Y-%m-%d")

        print(f"  📊 生成每日报告 ({date_str})...")

        # 1. 基础统计
        metrics = self._calculate_metrics(mentions, star_growth, star_count)

        # 2. 情感分析
        sentiment_summary = self._analyze_sentiment(mentions)

        # 3. 提取亮点和关注点
        highlights, concerns = self._extract_highlights_concerns(mentions, sentiment_summary)

        # 4. 提取热门话题
        top_topics = self._extract_topics(mentions)

        # 5. 生成可行动洞察
        actionable_insights = self._generate_insights(mentions, sentiment_summary, metrics)

        # 6. 生成摘要
        summary = self._generate_summary(metrics, sentiment_summary, star_growth)

        return DailyReport(
            date=date_str,
            summary=summary,
            metrics=metrics,
            highlights=highlights,
            concerns=concerns,
            sentiment_summary=sentiment_summary,
            top_topics=top_topics,
            actionable_insights=actionable_insights,
        )

    def _calculate_metrics(self, mentions: List[MentionData], star_growth: int, star_count: int) -> Dict[str, Any]:
        """计算基础指标"""
        # 按平台统计
        by_platform: Dict[str, int] = {}
        for m in mentions:
            platform = m.platform.value if hasattr(m.platform, "value") else str(m.platform)
            by_platform[platform] = by_platform.get(platform, 0) + 1

        # 按类型统计
        by_type: Dict[str, int] = {}
        for m in mentions:
            source_type = m.source_type.value if hasattr(m.source_type, "value") else str(m.source_type)
            by_type[source_type] = by_type.get(source_type, 0) + 1

        # 计算互动
        total_comments = sum(m.comments for m in mentions)
        total_score = sum((m.points or m.score or 0) for m in mentions)

        return {
            "total_mentions": len(mentions),
            "by_platform": by_platform,
            "by_type": by_type,
            "total_comments": total_comments,
            "total_score": total_score,
            "star_growth": star_growth,
            "star_count": star_count,
            "star_growth_rate": round((star_growth / star_count * 100) if star_count > 0 else 0, 1),
        }

    def _analyze_sentiment(self, mentions: List[MentionData]) -> Dict[str, Any]:
        """分析情感"""
        texts = [f"{m.title}\n{m.content}" for m in mentions if m.content or m.title]

        if not texts:
            return {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "avg_score": 0.0,
            }

        result = self.sentiment_analyzer.analyze_batch(texts)

        return {
            "positive": result["positive"],
            "neutral": result["neutral"],
            "negative": result["negative"],
            "avg_score": result["avg_score"],
            "total": result["total"],
        }

    def _extract_highlights_concerns(
        self, mentions: List[MentionData], sentiment_summary: Dict
    ) -> tuple[List[str], List[str]]:
        """提取亮点和关注点"""
        highlights = []
        concerns = []

        # 计算影响力
        influence_result = self.influence_analyzer.analyze(mentions)
        high_influence = [s for s in influence_result.get("scores", []) if s.get("level") == "high"]

        # 找出对应的提及
        high_mentions = []
        for score_data in high_influence[:5]:
            mention_id = score_data["mention_id"]
            for m in mentions:
                if m.source_id == mention_id:
                    high_mentions.append(m)
                    break

        # 提取亮点
        for m in high_mentions[: self.config.max_highlights]:
            if m.title:
                highlights.append(f'"{m.title[:50]}" ({m.score or m.points or 0}👍)')

        # 检查负面情感
        if sentiment_summary.get("negative", 0) > 0:
            concerns.append(f"发现 {sentiment_summary['negative']} 条负面评价需要关注")

        # 检查未回复的讨论
        open_discussions = [m for m in mentions if m.state == "open" and m.comments == 0]
        if len(open_discussions) > 3:
            concerns.append(f"{len(open_discussions)} 条讨论尚未得到回复")

        # 检查高关注度问题
        high_comment_issues = [m for m in mentions if m.comments > 10 and m.source_type.value == "issue"]
        for m in high_comment_issues[: self.config.max_concerns]:
            concerns.append(f"Issue: {m.title[:40]} ({m.comments}条评论)")

        return highlights, concerns

    def _extract_topics(self, mentions: List[MentionData]) -> List[str]:
        """提取热门话题"""
        # 简单的关键词提取
        import re
        from collections import Counter

        words = []
        for m in mentions:
            # 从标题和内容提取
            text = f"{m.title} {m.content}".lower()
            # 提取有意义的词
            tokens = re.findall(r"\b[a-z]{3,}\b", text)
            words.extend(tokens)

        # 过滤常见词
        stop_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "has",
            "have",
            "been",
            "this",
            "that",
            "with",
            "they",
            "from",
            "what",
            "when",
            "which",
            "their",
            "will",
            "would",
            "there",
            "could",
            "more",
            "about",
            "into",
            "than",
        }

        filtered = [w for w in words if w not in stop_words]

        # 统计频率
        counter = Counter(filtered)

        return [word for word, _ in counter.most_common(self.config.max_topics)]

    def _generate_insights(self, mentions: List[MentionData], sentiment_summary: Dict, metrics: Dict) -> List[str]:
        """生成可行动洞察"""
        insights = []

        # Star增长洞察
        star_growth = metrics.get("star_growth", 0)
        if star_growth > 10:
            insights.append(f"Star增长强劲 (+{star_growth})，保持当前推广策略")
        elif star_growth > 0:
            insights.append(f"Star稳步增长 (+{star_growth})")
        elif star_growth < -5:
            insights.append(f"⚠️ Star出现负增长 ({star_growth})，需要关注")

        # 情感洞察
        avg_score = sentiment_summary.get("avg_score", 0)
        if avg_score > 0.3:
            insights.append("社区情感积极，用户反馈良好")
        elif avg_score < -0.2:
            insights.append("⚠️ 社区情感偏负面，需要改进用户体验")

        # 平台洞察
        by_platform = metrics.get("by_platform", {})
        if by_platform:
            top_platform = max(by_platform.items(), key=lambda x: x[1])
            insights.append(f"最活跃平台: {top_platform[0]} ({top_platform[1]}条讨论)")

        # 活跃作者
        authors = {}
        for m in mentions:
            authors[m.author] = authors.get(m.author, 0) + 1

        if authors:
            top_author = max(authors.items(), key=lambda x: x[1])
            if top_author[1] > 2:
                insights.append(f"活跃用户 @{top_author[0]} 发起 {top_author[1]} 条讨论")

        return insights[:5]

    def _generate_summary(self, metrics: Dict, sentiment_summary: Dict, star_growth: int) -> str:
        """生成摘要文本"""
        total = metrics.get("total_mentions", 0)
        star = metrics.get("star_growth", 0)
        sentiment = sentiment_summary.get("avg_score", 0)

        parts = []

        if total > 0:
            parts.append(f"今日共收录 {total} 条讨论")

        if star > 0:
            parts.append(f"Star增长 +{star}")

        if sentiment > 0.2:
            parts.append("社区情感积极")
        elif sentiment < -0.2:
            parts.append("社区情感偏负面")
        else:
            parts.append("社区情感中性")

        return "，".join(parts) + "。"

    def save(self, report: DailyReport, format: str = "json") -> Path:
        """保存报告

        Args:
            report: 报告数据
            format: 输出格式 (json/markdown/txt)

        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"daily_report_{timestamp}.{format}"
        filepath = self.output_dir / filename

        if format == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        elif format == "markdown":
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self._format_markdown(report))

        elif format == "txt":
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report.format_terminal())

        return filepath

    def _format_markdown(self, report: DailyReport) -> str:
        """格式化为Markdown"""
        lines = [
            f"# 📊 LingFlow 情报简报 - {report.date}",
            "",
            "## 📋 摘要",
            f"{report.summary}",
            "",
            "## 📈 今日统计",
            f"- 总提及: **{report.metrics.get('total_mentions', 0)}** 条",
        ]

        # 平台分布
        by_platform = report.metrics.get("by_platform", {})
        if by_platform:
            lines.append("- 平台分布:")
            for platform, count in by_platform.items():
                lines.append(f"  - {platform}: {count}")

        # Star数据
        star_growth = report.metrics.get("star_growth", 0)
        if star_growth > 0:
            lines.append(f"- Star增长: **+{star_growth}**")

        lines.extend(
            [
                "",
                "## 💬 情感分析",
            ]
        )

        sentiment = report.sentiment_summary
        total = sentiment.get("total", 1)
        lines.extend(
            [
                f"- 积极: {sentiment.get('positive', 0)}" f" ({sentiment.get('positive', 0) / total * 100:.0f}%)",
                f"- 中性: {sentiment.get('neutral', 0)}" f" ({sentiment.get('neutral', 0) / total * 100:.0f}%)",
                f"- 消极: {sentiment.get('negative', 0)}" f" ({sentiment.get('negative', 0) / total * 100:.0f}%)",
                "",
                "## 🔥 热门话题",
            ]
        )

        for i, topic in enumerate(report.top_topics[:10], 1):
            lines.append(f"{i}. {topic}")

        if report.highlights:
            lines.extend(
                [
                    "",
                    "## ✅ 亮点",
                ]
            )
            for highlight in report.highlights:
                lines.append(f"- {highlight}")

        if report.concerns:
            lines.extend(
                [
                    "",
                    "## ⚠️ 需要关注",
                ]
            )
            for concern in report.concerns:
                lines.append(f"- {concern}")

        if report.actionable_insights:
            lines.extend(
                [
                    "",
                    "## 💡 洞察",
                ]
            )
            for insight in report.actionable_insights:
                lines.append(f"- {insight}")

        lines.extend(
            [
                "",
                f"*生成时间: {report.generated_at}*",
            ]
        )

        return "\n".join(lines)


def main():
    """主函数 - 测试报告器"""
    print("=" * 60)
    print("📊 每日简报生成器测试")
    print("=" * 60)
    print()

    from ..models.common import Platform, SourceType

    # 创建测试数据
    test_mentions = [
        MentionData(
            platform=Platform.HACKERNEWS,
            source_type=SourceType.POST,
            source_id="1",
            author="user1",
            content="LingFlow is amazing! Best automation tool I've used.",
            url="https://example.com/1",
            published_at="2026 - 04 - 03T10:00:00",
            title="LingFlow: The Future of Automation",
            points=150,
            comments=45,
        ),
        MentionData(
            platform=Platform.REDDIT,
            source_type=SourceType.POST,
            source_id="2",
            author="user2",
            content="Just started using LingFlow, pretty good so far.",
            url="https://example.com/2",
            published_at="2026 - 04 - 03T12:00:00",
            title="First impressions of LingFlow",
            score=25,
            upvote_ratio=0.9,
            comments=8,
        ),
        MentionData(
            platform=Platform.GITHUB,
            source_type=SourceType.ISSUE,
            source_id="3",
            author="user3",
            content="Having trouble with the installation process.",
            url="https://example.com/3",
            published_at="2026 - 04 - 03T14:00:00",
            title="Installation issue on Windows",
            comments=12,
            state="open",
        ),
    ]

    reporter = DailyReporter()

    # 生成报告
    report = reporter.generate(mentions=test_mentions, star_growth=15, star_count=245)

    print()
    print(report.format_terminal())

    print()
    print("💾 保存报告...")

    # 保存多种格式
    for fmt in ["txt", "json", "markdown"]:
        filepath = reporter.save(report, format=fmt)
        print(f"  {fmt}: {filepath}")

    print()
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
