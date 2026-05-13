#!/usr/bin/env python3
"""
lingflow 情报收集主脚本

整合所有情报收集节点，收集网络世界对lingflow的评价和讨论。

运行方式:
    python scripts/lingflow_monitor.py
    或
    HOOKS_FAST_ITERATION=1 python scripts/lingflow_monitor.py
"""

from lingflow.intelligence.analyzers.sentiment import SentimentAnalyzer
from lingflow.intelligence.collectors import lingflowMonitor, StarTracker
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """主函数"""
    print("=" * 70)
    print("🔍 lingflow 情报收集系统")
    print("=" * 70)
    print()
    print("📡 收集节点:")
    print("  • GitHub Issues/Discussions - 项目讨论")
    print("  • Star 增长追踪 - 用户增长趋势")
    print("  • 情感分析 - 社区态度倾向")
    print()
    print(f"⏰ 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 监控 GitHub 活动
    print("=" * 70)
    print("📋 节点 1: GitHub 监控")
    print("=" * 70)

    monitor = lingflowMonitor()

    # 采集最近7天的数据
    all_mentions = []
    all_mentions.extend(monitor.collect_issues(state="open", days=7))
    all_mentions.extend(monitor.collect_discussions(days=7))
    all_mentions.extend(monitor.collect_releases())

    # 保存数据
    if all_mentions:
        data_file = monitor.save_data(all_mentions)
        summary = monitor.generate_summary(all_mentions)

        print()
        print("📊 GitHub 活动汇总:")
        print(f"  总提及: {summary['total']} 条")
        print(f"  按类型: {summary['by_type']}")
        print(f"  总评论: {summary['total_comments']}")
        print(f"  活跃作者: {dict(summary['top_authors'][:3])}")

    # 2. 追踪 Star 增长
    print()
    print("=" * 70)
    print("⭐ 节点 2: Star 增长追踪")
    print("=" * 70)

    tracker = StarTracker()
    star_result = tracker.collect(max_users=300)

    print()
    print("📈 Star 趋势:")
    print(f"  当前Stars: {star_result['star_count']}")
    print(f"  增长: +{star_result['growth']}")
    print(f"  新增用户: {len(star_result['new_stargazers'])}")

    # 趋势报告
    trend = tracker.generate_trend_report(days=30)
    if 'error' not in trend:
        print(f"  月均增长: {trend['avg_daily_growth']}/天")
        print(f"  数据点: {trend['data_points']}个")

    # 3. 情感分析
    print()
    print("=" * 70)
    print("💭 节点 3: 情感分析")
    print("=" * 70)

    analyzer = SentimentAnalyzer()

    # 提取所有文本内容
    texts = []
    for mention in all_mentions:
        texts.append(mention.title)
        texts.append(mention.content[:500])  # 限制长度

    if texts:
        sentiment_summary = analyzer.analyze_batch(texts)

        print("📊 情感分析结果:")
        print(f"  分析样本: {sentiment_summary['total']} 条")
        print(
            f"  正面: {
                sentiment_summary['positive']} ({
                sentiment_summary['positive_ratio']})")
        print(
            f"  负面: {
                sentiment_summary['negative']} ({
                sentiment_summary['negative_ratio']})")
        print(f"  中性: {sentiment_summary['neutral']}")
        print(f"  综合评分: {sentiment_summary['avg_score']:+.2f}")

        # 提取话题
        topics = analyzer.extract_topics(texts)
        if topics:
            print()
            print("🔥 热门话题:")
            for i, topic in enumerate(topics[:5], 1):
                print(f"  {i}. {topic}")

    # 4. 生成综合报告
    print()
    print("=" * 70)
    print("📋 情报简报")
    print("=" * 70)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = Path(".lingflow/intelligence/reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"brief_{timestamp}.txt"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("lingflow 情报简报\n")
        f.write("=" * 70 + "\n")
        f.write(f"\n采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        f.write(f"\n📊 GitHub 活动:\n")
        f.write(f"  • Issues: {summary.get('total', 0)} 条\n")
        f.write(
            f"  • Discussions: {
                summary.get(
                    'by_type',
                    {}).get(
                    'discussion',
                    0)} 条\n")
        f.write(f"  • 总评论: {summary.get('total_comments', 0)} 条\n")

        f.write(f"\n⭐ Star 增长:\n")
        f.write(f"  • 当前Stars: {star_result['star_count']}\n")
        f.write(f"  • 新增: +{star_result['growth']}\n")
        f.write(f"  • 月均增长: {trend.get('avg_daily_growth', 0)}/天\n")

        f.write(f"\n💭 情感分析:\n")
        f.write(f"  • 正面: {sentiment_summary.get('positive_ratio', 'N/A')}\n")
        f.write(f"  • 负面: {sentiment_summary.get('negative_ratio', 'N/A')}\n")
        f.write(f"  • 综合评分: {sentiment_summary.get('avg_score', 'N/A')}\n")

        f.write(f"\n📁 详细数据:\n")
        f.write(f"  • 原始数据: {data_file if all_mentions else 'N/A'}\n")
        f.write(f"  • Star历史: {tracker.history_file}\n")

    print(f"\n💾 简报已保存: {report_file}")

    print()
    print("✅ 情报收集完成!")


if __name__ == "__main__":
    main()
