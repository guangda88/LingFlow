#!/usr/bin/env python3
"""LingFlow QueryEngine - 使用示例和测试"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lingflow.core.query_engine import (
    QueryEngine,
    QueryEngineConfig,
    StopReason,
    create_default_engine,
    create_budget_conscious_engine,
    create_long_conversation_engine
)

print("=" * 70)
print("🔧 LingFlow QueryEngine - 使用示例")
print("=" * 70)
print()

# ============================================================================
# 示例1: 基本使用
# ============================================================================

print("📱 示例1: 基本使用")
print("-" * 70)

# 创建引擎
engine = create_default_engine()

# 模拟工具和Agent
tools = ["code_analyzer", "file_reader", "test_runner"]
agents = ["code_reviewer", "optimizer", "documenter"]

# 提交查询
result1 = engine.submit(
    "请帮我分析这段代码的性能",
    tools=tools,
    agents=agents
)

print(f"  提示词: {result1.prompt[:50]}...")
print(f"  输出: {result1.output[:100]}...")
print(f"  输入Tokens: {result1.input_tokens}")
print(f"  输出Tokens: {result1.output_tokens}")
print(f"  匹配工具: {result1.matched_tools}")
print(f"  匹配Agent: {result1.matched_agents}")
print(f"  停止原因: {result1.stop_reason.value}")

print()

# ============================================================================
# 示例2: 多轮对话
# ============================================================================

print("💬 示例2: 多轮对话")
print("-" * 70)

queries = [
    "如何优化Python代码？",
    "请使用code_analyzer工具",
    "生成单元测试"
]

for i, query in enumerate(queries, 1):
    print(f"\n  第{i}轮:")
    result = engine.submit(query, tools=tools, agents=agents)
    print(f"    提示: {query}")
    print(f"    输出: {result.output[:80]}...")

# 查看统计
stats = engine.get_stats()
print(f"\n  📊 对话统计:")
print(f"    总轮数: {stats['turn_count']}")
print(f"    总消息数: {stats['message_count']}")
print(f"    输入Tokens: {stats['usage']['total_input_tokens']}")
print(f"    输出Tokens: {stats['usage']['total_output_tokens']}")
print(f"    总Tokens: {stats['usage']['total_tokens']}")

print()

# ============================================================================
# 示例3: Token预算控制
# ============================================================================

print("💰 示例3: Token预算控制")
print("-" * 70)

# 创建小预算引擎
budget_engine = create_budget_conscious_engine(budget=100)

print(f"  预算设置: {budget_engine.config.max_budget_tokens} tokens")

# 模拟多次查询
for i in range(5):
    result = budget_engine.submit(f"查询 {i+1}")
    usage = budget_engine.usage_summary

    print(f"  查询 {i+1}: "
          f"+{result.input_tokens} +{result.output_tokens} = "
          f"{usage.total_tokens}/{budget_engine.config.max_budget_tokens} tokens")

    if result.stop_reason == StopReason.MAX_BUDGET_REACHED:
        print(f"  ⚠️  已达到预算限制！")
        break

print()

# ============================================================================
# 示例4: 自动紧凑化
# ============================================================================

print("🗜️  示例4: 自动紧凑化")
print("-" * 70)

# 创建长对话引擎
long_engine = create_long_conversation_engine()

print(f"  配置: 最多{long_engine.config.max_turns}轮")
print(f"  紧凑化触发: {long_engine.config.compact_after_turns}轮后")

# 模拟长对话
for i in range(20):
    result = long_engine.submit(f"这是第{i+1}条消息")

    if i % 5 == 0:
        stats = long_engine.get_stats()
        print(f"  第{i+1}轮: 消息数={stats['message_count']}, "
              f"Tokens={stats['usage']['total_tokens']}")

    if result.stop_reason != StopReason.COMPLETED:
        print(f"  停止: {result.stop_reason.value}")
        break

# 查看紧凑化摘要
summary = long_engine.get_compact_summary()
print(f"\n  紧凑化摘要: {summary}")

print()

# ============================================================================
# 示例5: 状态保存和加载
# ============================================================================

print("💾 示例5: 状态保存和加载")
print("-" * 70)

# 创建引擎并添加一些查询
engine = create_default_engine()
engine.submit("第一条查询")
engine.submit("第二条查询")
engine.submit("第三条查询")

# 保存状态
state_path = engine.save_state()
print(f"  ✅ 状态已保存: {state_path}")

# 加载状态
loaded_engine = QueryEngine.load_state(state_path)
stats = loaded_engine.get_stats()
print(f"  ✅ 状态已加载")
print(f"     轮数: {stats['turn_count']}")
print(f"     消息数: {stats['message_count']}")

print()

# ============================================================================
# 示例6: 自定义处理函数
# ============================================================================

print("⚙️  示例6: 自定义处理函数")
print("-" * 70)

def custom_processor(prompt: str) -> str:
    """自定义处理函数"""
    return f"自定义处理: {prompt.upper()}"

engine = create_default_engine()
result = engine.submit(
    "使用自定义处理器",
    process_func=custom_processor
)

print(f"  输入: {result.prompt}")
print(f"  输出: {result.output}")

print()

# ============================================================================
# 示例7: 错误处理
# ============================================================================

print("⚠️  示例7: 错误处理")
print("-" * 70)

# 创建限制严格的引擎
strict_engine = QueryEngine(
    QueryEngineConfig(max_turns=2, max_budget_tokens=50)
)

# 尝试超过限制
results = []
for i in range(5):
    result = strict_engine.submit(f"查询 {i+1}")
    results.append(result)

    if result.error:
        print(f"  查询 {i+1}: ⚠️  {result.error}")
    else:
        print(f"  查询 {i+1}: ✅ 正常")

print()

# ============================================================================
# 总结
# ============================================================================

print("=" * 70)
print("✅ 所有示例运行完成！")
print("=" * 70)

print("""
🎯 QueryEngine 功能特性:

1. 多轮对话管理
   • 自动跟踪对话轮数
   • 维护完整消息历史
   • 智能停止控制

2. Token预算控制
   • 输入/输出Token统计
   • 总预算限制
   • 自动停止机制

3. 自动紧凑化
   • 达到阈值后自动触发
   • 保留最近的重要消息
   • 生成紧凑化摘要

4. 工具和Agent匹配
   • 基于关键词的智能匹配
   • 返回匹配的工具和Agent
   • 支持自定义匹配逻辑

5. 状态持久化
   • 保存完整引擎状态
   • 支持状态恢复
   • JSON格式存储

6. 自定义处理
   • 支持自定义处理函数
   • 灵活的输出格式
   • 可扩展的处理逻辑

💡 使用场景:

✅ 多轮对话系统
✅ API调用管理
✅ Token预算控制
✅ 长对话紧凑化
✅ 工具调度系统
✅ Agent协调

📚 相关文档:
  • CLAUDE_CODE_PRACTICAL_LEARNING_PLAN.md
  • lingflow/core/query_engine.py

🎯 开始在您的项目中使用QueryEngine吧！
""")

print("=" * 70)
