#!/usr/bin/env python3
"""lingflow 优化趋势分析工具"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_reports():
    """加载所有优化报告"""
    reports_dir = Path(".lingflow/reports")
    reports = []

    for report_file in sorted(reports_dir.glob("autonomous_optimization_*.json")):
        try:
            with open(report_file) as f:
                data = json.load(f)
                data['file'] = str(report_file)
                reports.append(data)
        except Exception as e:
            print(f"⚠️  无法读取 {report_file}: {e}")

    return reports

def print_summary(reports):
    """打印优化摘要"""
    print("\n" + "=" * 70)
    print("📊 lingflow 优化历史摘要")
    print("=" * 70)

    if not reports:
        print("❌ 没有找到优化报告")
        return

    print(f"\n总优化次数: {len(reports)}")
    print(f"时间范围: {reports[0]['timestamp']} 到 {reports[-1]['timestamp']}")

    # 统计信息
    violations = [r.get('violations', 0) for r in reports if r.get('violations', 0) > 0]
    if violations:
        print(f"\n违规数统计:")
        print(f"  最小: {min(violations)}")
        print(f"  最大: {max(violations)}")
        print(f"  平均: {sum(violations)/len(violations):.1f}")
        print(f"  最新: {violations[-1]}")

    # 实验次数
    experiments = [r.get('experiments', 0) for r in reports if r.get('experiments')]
    if experiments:
        print(f"\n实验次数: 每次平均 {sum(experiments)/len(experiments):.0f} 次")

    # 耗时
    durations = [r.get('duration', 0) for r in reports if r.get('duration')]
    if durations:
        print(f"优化耗时: 平均 {sum(durations)/len(durations):.2f} 秒")

def print_history(reports, limit=10):
    """打印优化历史"""
    print("\n" + "=" * 70)
    print(f"📜 最近{min(limit, len(reports))}次优化")
    print("=" * 70)

    for i, report in enumerate(reports[-limit:], 1):
        timestamp = report.get('timestamp', 'N/A')
        violations = report.get('violations', 'N/A')
        experiments = report.get('experiments', 'N/A')
        duration = report.get('duration', 'N/A')
        status = report.get('status', 'N/A')

        # 格式化时间
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            time_str = timestamp

        # 状态图标
        if status == 'success':
            status_icon = "✅"
        elif status == 'error':
            status_icon = "❌"
        else:
            status_icon = "ℹ️ "

        print(f"\n{status_icon} 优化 #{i}")
        print(f"   时间: {time_str}")
        print(f"   违规数: {violations}")
        print(f"   实验次数: {experiments}")
        print(f"   耗时: {duration}秒" if duration != 'N/A' else f"   耗时: {duration}")

def print_trend(reports):
    """打印趋势分析"""
    print("\n" + "=" * 70)
    print("📈 趋势分析")
    print("=" * 70)

    # 提取有效的违规数数据
    valid_reports = [r for r in reports if r.get('violations', 0) > 0]

    if len(valid_reports) < 2:
        print("⚠️  数据不足，无法分析趋势")
        return

    first = valid_reports[0]['violations']
    last = valid_reports[-1]['violations']

    print(f"\n首次优化违规数: {first}")
    print(f"最新优化违规数: {last}")

    if last < first:
        improvement = (first - last) / first * 100
        print(f"✅ 改进: {improvement:.1f}% (↓ {first - last:.0f} 个违规)")
    elif last > first:
        regression = (last - first) / first * 100
        print(f"⚠️  回退: {regression:.1f}% (↑ {last - first:.0f} 个违规)")
    else:
        print(f"➡️  保持不变")

    # 最近趋势
    if len(valid_reports) >= 3:
        recent = valid_reports[-3:]
        recent_violations = [r['violations'] for r in recent]
        avg_recent = sum(recent_violations) / len(recent_violations)

        print(f"\n最近3次平均: {avg_recent:.1f}")

        if avg_recent < last:
            print(f"📉 趋势: 向下（良好）")
        elif avg_recent > last:
            print(f"📈 趋势: 向上（需关注）")
        else:
            print(f"➡️  趋势: 稳定")

def print_best_params(reports):
    """打印最佳参数"""
    print("\n" + "=" * 70)
    print("⚙️  最佳参数配置")
    print("=" * 70)

    # 获取最新的有效报告
    for report in reversed(reports):
        if 'best_params' in report and report.get('violations', 0) > 0:
            params = report['best_params']
            print(f"\n来自优化: {report['timestamp']}")
            print(f"违规数: {report['violations']}")
            print("\n参数配置:")
            for key, value in params.items():
                print(f"  {key}: {value}")
            break

def generate_recommendations(reports):
    """生成改进建议"""
    print("\n" + "=" * 70)
    print("💡 改进建议")
    print("=" * 70)

    valid_reports = [r for r in reports if r.get('violations', 0) > 0]

    if not valid_reports:
        print("⚠️  数据不足，无法生成建议")
        return

    latest = valid_reports[-1]['violations']

    # 基于违规数的建议
    if latest <= 5:
        print("✅ 代码质量优秀！")
        print("   建议: 继续保持当前开发规范")
    elif latest <= 10:
        print("✅ 代码质量良好")
        print("   建议: 定期重构小问题，保持当前水平")
    elif latest <= 20:
        print("⚠️  代码质量一般")
        print("   建议: 关注违规最多的模块，逐步重构")
    else:
        print("❌ 代码质量需要改进")
        print("   建议: 优先处理违规最多的问题，考虑专项优化")

    # 趋势建议
    if len(valid_reports) >= 3:
        recent = valid_reports[-3:]
        recent_violations = [r['violations'] for r in recent]

        if recent_violations[-1] > recent_violations[0]:
            print("\n⚠️  最近违规数有上升趋势")
            print("   建议: 检查最近代码变更，加强代码审查")

def main():
    """主函数"""
    print("=" * 70)
    print("🔍 lingflow 优化趋势分析")
    print("=" * 70)

    # 加载报告
    reports = load_reports()

    if not reports:
        print("\n❌ 没有找到优化报告")
        print("\n提示: 运行优化以生成报告")
        print("  /home/ai/lingflow/scripts/run_optimization_simple.sh")
        return

    # 打印摘要
    print_summary(reports)

    # 打印历史
    print_history(reports, limit=10)

    # 打印趋势
    print_trend(reports)

    # 打印最佳参数
    print_best_params(reports)

    # 生成建议
    generate_recommendations(reports)

    # 文件位置
    print("\n" + "=" * 70)
    print("📁 报告文件位置")
    print("=" * 70)
    print("\n最新报告:")
    latest = reports[-1]['file']
    print(f"  {latest}")
    print(f"\n查看详情:")
    print(f"  cat {latest} | jq '.'")

    print("\n" + "=" * 70)
    print("✅ 分析完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
