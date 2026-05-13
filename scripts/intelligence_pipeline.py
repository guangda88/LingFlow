#!/usr/bin/env python3
"""lingflow 情报系统统一运行脚本

执行完整的情报采集、分析、报告流程。
"""

from lingflow.intelligence.models.common import MentionData, Platform
from lingflow.intelligence.reporters import DailyReporter, DailyReportConfig
from lingflow.intelligence.analyzers import (
    SentimentAnalyzer,
    InfluenceAnalyzer,
    AnalyzerPipeline,
)
from lingflow.intelligence.collectors import (
    lingflowMonitor,
    StarTracker,
    RedditCollector,
    HNCollector,
    CollectorManager,
    CollectorConfig,
)
import argparse
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def collect_all(
    enable_github: bool = True,
    enable_reddit: bool = True,
    enable_hn: bool = True,
    days: int = 1,
) -> list[MentionData]:
    """采集所有平台数据

    Args:
        enable_github: 启用GitHub采集
        enable_reddit: 启用Reddit采集
        enable_hn: 启用HN采集
        days: 采集天数

    Returns:
        所有提及数据
    """
    print("=" * 60)
    print("🔍 情报采集阶段")
    print("=" * 60)
    print()

    all_mentions = []

    # GitHub 采集
    if enable_github:
        print("📋 GitHub 采集...")
        try:
            monitor = lingflowMonitor()

            issues = monitor.collect_issues(state="open", days=days)
            all_mentions.extend(issues)

            discussions = monitor.collect_discussions(days=days)
            all_mentions.extend(discussions)

            releases = monitor.collect_releases()
            all_mentions.extend(releases)

            # 保存GitHub数据
            if all_mentions:
                monitor.save_data(all_mentions)

        except Exception as e:
            print(f"  ❌ GitHub采集失败: {e}")

        print()

    # Reddit 采集
    if enable_reddit:
        print("🔍 Reddit 采集...")
        try:
            reddit = RedditCollector()
            mentions = reddit.search_mentions(
                keywords=["lingflow", "lingflow-core"],
                limit=100,
                days=days
            )
            all_mentions.extend(mentions)

            # 保存Reddit数据
            if mentions:
                reddit.save_data(mentions)

        except Exception as e:
            print(f"  ❌ Reddit采集失败: {e}")

        print()

    # HN 采集
    if enable_hn:
        print("🔍 Hacker News 采集...")
        try:
            hn = HNCollector()
            mentions = hn.search_mentions(
                keywords=["lingflow", "lingflow-core"],
                limit=100,
                days=days
            )
            all_mentions.extend(mentions)

            # 保存HN数据
            if mentions:
                hn.save_data(mentions)

        except Exception as e:
            print(f"  ❌ HN采集失败: {e}")

        print()

    print(f"✅ 采集完成，共获得 {len(all_mentions)} 条数据")
    print()

    return all_mentions


def analyze_all(mentions: list[MentionData]) -> dict:
    """分析所有数据

    Args:
        mentions: 提及数据列表

    Returns:
        分析结果字典
    """
    print("=" * 60)
    print("📊 情报分析阶段")
    print("=" * 60)
    print()

    if not mentions:
        print("  ⚠️ 没有数据可供分析")
        return {}

    # 创建分析流水线
    pipeline = AnalyzerPipeline([
        SentimentAnalyzer(),
        InfluenceAnalyzer(),
    ])

    results = pipeline.run(mentions)

    print("  情感分析: 完成")
    if 'sentiment' in results and results['sentiment']:
        sentiment = results['sentiment']
        print(f"    正面: {sentiment.get('positive', 0)}, "
              f"中性: {sentiment.get('neutral', 0)}, "
              f"负面: {sentiment.get('negative', 0)}")

    print("  影响力分析: 完成")
    if 'influence' in results and results['influence']:
        influence = results['influence']
        summary = influence.get('summary', {})
        print(f"    平均分: {summary.get('avg_score', 0):.1f}, "
              f"高影响力: {summary.get('high_influence', 0)}")

    print()
    print("✅ 分析完成")
    print()

    return results


def generate_report(
    mentions: list[MentionData],
    analysis_results: dict,
    star_growth: int = 0,
    star_count: int = 0,
) -> None:
    """生成报告

    Args:
        mentions: 提及数据
        analysis_results: 分析结果
        star_growth: Star增长数
        star_count: 当前Star数
    """
    print("=" * 60)
    print("📝 报告生成阶段")
    print("=" * 60)
    print()

    if not mentions:
        print("  ⚠️ 没有数据可生成报告")
        return

    reporter = DailyReporter()

    # 生成报告
    report = reporter.generate(
        mentions=mentions,
        star_growth=star_growth,
        star_count=star_count
    )

    # 输出到终端
    print(report.format_terminal())
    print()

    # 保存报告
    for fmt in ["txt", "json", "markdown"]:
        try:
            filepath = reporter.save(report, format=fmt)
            print(f"💾 {fmt:8} -> {filepath}")
        except Exception as e:
            print(f"  ❌ 保存{fmt}失败: {e}")

    print()


def track_stars() -> tuple[int, int]:
    """追踪Star增长

    Returns:
        (star_count, star_growth)
    """
    print("=" * 60)
    print("⭐ Star 追踪")
    print("=" * 60)
    print()

    try:
        tracker = StarTracker()
        result = tracker.collect(max_users=300)

        star_count = result.get('star_count', 0)
        star_growth = result.get('growth', 0)

        print(f"  当前Stars: {star_count}")
        print(f"  增长: +{star_growth}")
        print()

        return star_count, star_growth

    except Exception as e:
        print(f"  ❌ Star追踪失败: {e}")
        print()
        return 0, 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="lingflow 情报系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行完整流程
  python scripts/intelligence_pipeline.py

  # 只采集数据
  python scripts/intelligence_pipeline.py --collect-only

  # 采集最近3天数据
  python scripts/intelligence_pipeline.py --days 3

  # 禁用Reddit采集
  python scripts/intelligence_pipeline.py --no-reddit
        """
    )

    parser.add_argument(
        '--collect-only',
        action='store_true',
        help='只采集数据，不分析和报告'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='采集天数 (默认: 1)'
    )
    parser.add_argument(
        '--no-github',
        action='store_true',
        help='禁用GitHub采集'
    )
    parser.add_argument(
        '--no-reddit',
        action='store_true',
        help='禁用Reddit采集'
    )
    parser.add_argument(
        '--no-hn',
        action='store_true',
        help='禁用Hacker News采集'
    )
    parser.add_argument(
        '--no-stars',
        action='store_true',
        help='禁用Star追踪'
    )

    args = parser.parse_args()

    # 开始时间
    start_time = datetime.now()
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         🕊️  lingflow 情报系统 v2.0                        ║")
    print(
        f"║         启动时间: {
            start_time.strftime('%Y-%m-%d %H:%M:%S')}               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # 1. Star追踪
    star_count, star_growth = 0, 0
    if not args.no_stars:
        star_count, star_growth = track_stars()

    # 2. 数据采集
    mentions = collect_all(
        enable_github=not args.no_github,
        enable_reddit=not args.no_reddit,
        enable_hn=not args.no_hn,
        days=args.days,
    )

    if args.collect_only:
        print("✅ 采集完成，跳过分析和报告")
        return

    # 3. 数据分析
    analysis_results = analyze_all(mentions)

    # 4. 报告生成
    generate_report(
        mentions=mentions,
        analysis_results=analysis_results,
        star_growth=star_growth,
        star_count=star_count,
    )

    # 完成时间
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         ✅ 情报系统运行完成                                ║")
    print(f"║         运行时长: {duration:.1f} 秒                              ║")
    print(
        f"║         结束时间: {
            end_time.strftime('%Y-%m-%d %H:%M:%S')}               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
