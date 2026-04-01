#!/usr/bin/env python3
"""LingFlow PromptRouter - 使用示例和测试"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lingflow.core.prompt_router import (
    PromptRouter,
    RouteRule,
    RouteTarget,
    RouteStrategy,
    create_default_router,
    create_code_focused_router
)

print("=" * 70)
print("🔀 LingFlow PromptRouter - 使用示例")
print("=" * 70)
print()

# ============================================================================
# 示例1: 基本使用
# ============================================================================

print("📱 示例1: 基本使用")
print("-" * 70)

# 创建默认路由器
router = create_default_router()

# 路由不同的prompt
prompts = [
    "请帮我优化这段Python代码",
    "写一个单元测试",
    "解释什么是机器学习",
    "创建API文档"
]

for prompt in prompts:
    result = router.route(prompt)
    best = result.best_match

    print(f"\n  提示: {prompt}")
    print(f"  匹配规则: {best[0] if best else '无'} (分数: {best[1]:.2f})" if best else "  匹配规则: 无")
    print(f"  选择目标: {result.selected_target.name if result.selected_target else '无'}")
    print(f"  置信度: {result.confidence:.2f}")

print()

# ============================================================================
# 示例2: 自定义路由器
# ============================================================================

print("⚙️  示例2: 自定义路由器")
print("-" * 70)

# 创建自定义路由器
custom_router = PromptRouter()

# 添加目标
targets = [
    RouteTarget(
        name="calculator",
        agent_type="CalculatorAgent",
        description="数学计算"
    ),
    RouteTarget(
        name="translator",
        agent_type="TranslatorAgent",
        description="语言翻译"
    )
]

for target in targets:
    custom_router.add_target(target)

# 添加规则
rules = [
    RouteRule(
        name="calculation",
        keywords=["计算", "加", "减", "乘", "除"],
        metadata={"target_name": "calculator"}
    ),
    RouteRule(
        name="translation",
        keywords=["翻译", "英文", "中文", "翻译成"],
        metadata={"target_name": "translator"}
    )
]

for rule in rules:
    custom_router.add_rule(rule)

# 设置默认目标
custom_router.set_default_target(targets[0])

# 测试路由
test_prompts = [
    "帮我计算 1 + 1",
    "把这句话翻译成英文",
    "未知的请求"
]

for prompt in test_prompts:
    result = custom_router.route(prompt)
    print(f"  {prompt} -> {result.selected_target.name if result.selected_target else '无目标'} "
          f"(置信度: {result.confidence:.2f})")

print()

# ============================================================================
# 示例3: 模式匹配
# ============================================================================

print("🔍 示例3: 模式匹配")
print("-" * 70)

# 创建支持模式匹配的路由器
pattern_router = PromptRouter()

# 添加目标
pattern_router.add_target(
    RouteTarget(
        name="email_handler",
        agent_type="EmailAgent",
        description="邮件处理"
    )
)

# 添加正则表达式规则
email_rule = RouteRule(
    name="email_pattern",
    patterns=[
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\bsend\s+email\b',
        r'\b发送\s+邮件\b'
    ],
    strategy=RouteStrategy.PATTERN_MATCH,
    metadata={"target_name": "email_handler"}
)
pattern_router.add_rule(email_rule)

# 测试模式匹配
pattern_tests = [
    "请发送邮件到 user@example.com",
    "联系 support@company.com",
    "帮我写代码"
]

for test in pattern_tests:
    result = pattern_router.route(test)
    print(f"  {test}")
    print(f"    匹配: {result.best_match[0] if result.best_match else '无'} "
          f"(分数: {result.best_match[1]:.2f})" if result.best_match else "    匹配: 无")

print()

# ============================================================================
# 示例4: 统计分析
# ============================================================================

print("📊 示例4: 统计分析")
print("-" * 70)

router = create_default_router()

# 生成大量路由请求
test_prompts = [
    "优化代码",
    "写单元测试",
    "优化代码",
    "解释API",
    "写文档",
    "优化代码",
    "写单元测试",
    "创建测试",
    "解释概念"
]

for prompt in test_prompts:
    router.route(prompt)

# 获取统计
stats = router.get_statistics()

print(f"  总路由数: {stats['total_routes']}")
print(f"  平均置信度: {stats['avg_confidence']:.2f}")
print(f"\n  最常用目标:")
for target_name, count in stats['most_used_targets']:
    print(f"    {target_name}: {count}次")

print(f"\n  最常匹配规则:")
for rule_name, count in stats['most_matched_rules']:
    print(f"    {rule_name}: {count}次")

print()

# ============================================================================
# 示例5: 配置保存和加载
# ============================================================================

print("💾 示例5: 配置保存和加载")
print("-" * 70)

# 创建路由器
router = create_default_router()

# 保存配置
config_path = router.save_config()
print(f"  ✅ 配置已保存: {config_path}")

# 加载配置
loaded_router = PromptRouter.load_config(config_path)
print(f"  ✅ 配置已加载")

# 验证加载
result = loaded_router.route("优化Python代码")
print(f"  测试路由: {result.selected_target.name if result.selected_target else '无'}")

print()

# ============================================================================
# 示例6: Top-K匹配
# ============================================================================

print("🏆 示例6: Top-K匹配")
print("-" * 70)

router = create_default_router()

# 创建可能匹配多个规则的提示词
prompt = "请帮我优化代码并编写单元测试"
result = router.route(prompt, top_k=5)

print(f"  提示词: {prompt}")
print(f"\n  Top-{len(result.matched_rules)} 匹配:")
for i, (rule_name, score) in enumerate(result.matched_rules, 1):
    print(f"    {i}. {rule_name}: {score:.2f}")

print()

# ============================================================================
# 示例7: 优先级系统
# ============================================================================

print("⭐ 示例7: 优先级系统")
print("-" * 70)

router = PromptRouter()

# 添加目标
router.add_target(
    RouteTarget(
        name="general_agent",
        agent_type="GeneralAgent",
        description="通用助手"
    )
)

# 添加不同优先级的规则
rules = [
    RouteRule(
        name="low_priority",
        keywords=["帮助", "助手"],
        priority=0,
        metadata={"target_name": "general_agent"}
    ),
    RouteRule(
        name="high_priority",
        keywords=["紧急", "重要", "优先"],
        priority=5,
        metadata={"target_name": "general_agent"}
    )
]

for rule in rules:
    router.add_rule(rule)

# 测试优先级
test = "这是一个紧急的请求，需要帮助"
result = router.route(test)

print(f"  提示词: {test}")
print(f"\n  匹配规则:")
for rule_name, score in result.matched_rules:
    print(f"    {rule_name}: {score:.2f}")

print()

# ============================================================================
# 总结
# ============================================================================

print("=" * 70)
print("✅ 所有示例运行完成！")
print("=" * 70)

print("""
🎯 PromptRouter 功能特性:

1. 智能匹配
   • 基于关键词的匹配
   • 正则表达式模式匹配
   • 可扩展的自定义匹配策略

2. 评分系统
   • 匹配度评分
   • 优先级权重
   • 置信度计算

3. 多目标路由
   • 支持多个路由目标
   • 智能选择最佳目标
   • 默认目标兜底

4. Top-K匹配
   • 返回前K个匹配
   • 多候选结果
   • 灵活的排序策略

5. 统计分析
   • 路由历史记录
   • 使用统计
   • 热门目标和规则

6. 配置管理
   • 保存/加载配置
   • JSON格式存储
   • 易于部署

💡 使用场景:

✅ 多Agent系统路由
✅ 智能客服系统
✅ 任务分发系统
✅ 内容分类路由
✅ 自动化工作流

📚 相关文档:
  • CLAUDE_CODE_PRACTICAL_LEARNING_PLAN.md
  • lingflow/core/prompt_router.py

🎯 开始在您的项目中使用PromptRouter吧！
""")

print("=" * 70)
