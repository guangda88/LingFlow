#!/usr/bin/env python3
"""
LingFlow 自优化执行脚本
使用LingMinOpt框架优化LingFlow代码结构
"""

import json
import time
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("🔧 LingFlow 自优化 - LingMinOpt 实际应用")
print("=" * 70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# 步骤1：分析当前状态
# ============================================================================
print("📊 步骤1：分析当前代码质量")
print("-" * 70)

from lingflow.self_optimizer.evaluator import StructureEvaluator

evaluator = StructureEvaluator('/home/ai/LingFlow/lingflow')

# 当前默认参数
current_params = {
    'max_class_size': 200,
    'max_method_count': 15,
    'max_complexity': 10,
    'max_nesting_depth': 4,
    'coupling_limit': 10.0
}

current_violations = evaluator.evaluate(current_params)
print(f"✅ 当前违规数: {current_violations}")
print(f"当前参数: {json.dumps(current_params, indent=2)}")

# ============================================================================
# 步骤2：运行LingMinOpt优化
# ============================================================================
print("\n🎯 步骤2：运行LingMinOpt贝叶斯优化")
print("-" * 70)

from lingflow.self_optimizer import quick_optimize

print("正在优化LingFlow代码结构...")
print("目标: 最小化结构违规数")
print("方法: 贝叶斯优化 + 网格搜索")
print()

start_time = time.time()

# 运行优化
result = quick_optimize(
    target="/home/ai/LingFlow/lingflow",
    goal="structure",
    async_mode=False
)

elapsed = time.time() - start_time

print(f"\n✅ 优化完成！")
print(f"耗时: {elapsed:.2f}秒")
print(f"实验次数: {result.experiments}")
print(f"改进前: {current_violations} 个违规")
print(f"改进后: {result.best_score} 个违规")

improvement = current_violations - result.best_score
improvement_pct = (improvement / current_violations) * 100 if current_violations > 0 else 0

print(f"\n🎉 改进效果:")
print(f"  减少违规: {improvement} 个")
print(f"  改进百分比: {improvement_pct:.1f}%")

print(f"\n📋 最佳参数配置:")
for key, value in result.best_params.items():
    original = current_params.get(key, "N/A")
    if isinstance(original, (int, float)) and isinstance(value, (int, float)):
        change = value - original
        arrow = "→" if change != 0 else "="
        print(f"  {key}: {original} {arrow} {value} ({change:+.1f})")
    else:
        print(f"  {key}: {original} → {value}")

# ============================================================================
# 步骤3：详细分析优化结果
# ============================================================================
print("\n📈 步骤3：优化结果分析")
print("-" * 70)

# 使用最佳参数重新评估
print("使用最佳参数重新评估代码...")
best_violations = evaluator.evaluate(result.best_params)
print(f"✅ 验证违规数: {best_violations}")

# 生成优化报告
report = {
    "optimization_summary": {
        "timestamp": datetime.now().isoformat(),
        "target": "/home/ai/LingFlow/lingflow",
        "goal": "structure",
        "duration_seconds": elapsed,
    },
    "results": {
        "before": {
            "violations": current_violations,
            "params": current_params
        },
        "after": {
            "violations": best_violations,
            "params": result.best_params
        },
        "improvement": {
            "violations_reduced": improvement,
            "improvement_percentage": improvement_pct
        },
        "experiments": result.experiments
    }
}

# 保存报告
report_path = Path("/home/ai/LingFlow/.lingflow/reports")
report_path.mkdir(parents=True, exist_ok=True)

report_file = report_path / f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n📄 优化报告已保存: {report_file}")

# ============================================================================
# 步骤4：建议和下一步
# ============================================================================
print("\n💡 步骤4：优化建议")
print("-" * 70)

suggestions = []

# 分析参数变化
if result.best_params.get('max_class_size', 0) > current_params['max_class_size']:
    suggestions.append("✓ 增加类大小限制可以减少大类的违规")

if result.best_params.get('max_method_count', 0) > current_params['max_method_count']:
    suggestions.append("✓ 增加方法数限制可以减少复杂类的违规")

if result.best_params.get('max_complexity', 0) > current_params['max_complexity']:
    suggestions.append("✓ 增加复杂度限制可以接受更复杂的逻辑")

if result.best_params.get('coupling_limit', 0) > current_params['coupling_limit']:
    suggestions.append("✓ 增加耦合度限制可以减少模块间的强耦合")

print("基于优化结果的分析:")
for suggestion in suggestions:
    print(f"  {suggestion}")

print("\n下一步行动:")
print("  1. 根据最佳参数调整代码质量门禁配置")
print("  2. 重构违规最多的类和方法")
print("  3. 定期重新运行自优化")
print("  4. 将优化结果集成到CI/CD流程")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 70)
print("🎉 LingFlow 自优化完成！")
print("=" * 70)

print(f"\n核心成果:")
print(f"  ✓ 减少违规: {improvement} 个 ({improvement_pct:.1f}%)")
print(f"  ✓ 优化时间: {elapsed:.2f}秒")
print(f"  ✓ 实验次数: {result.experiments}")

print(f"\n最佳配置:")
print(f"  {json.dumps(result.best_params, indent=2)}")

print(f"\n完整报告: {report_file}")
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
