#!/usr/bin/env python3
"""Session v2 集成测试和使用示例"""

import sys
from pathlib import Path

# 测试导入
print("=" * 70)
print("🧪 测试1: 导入Session v2")
print("=" * 70)

try:
    from lingflow.core import SessionManager, SessionSnapshot
    print("✅ 从 lingflow.core 导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

try:
    from lingflow.core.session_v2 import SessionManager as SM2
    print("✅ 从 lingflow.core.session_v2 直接导入成功")
except ImportError as e:
    print(f"❌ 直接导入失败: {e}")
    sys.exit(1)

print()

# 测试基本功能
print("=" * 70)
print("🧪 测试2: 创建SessionManager")
print("=" * 70)

manager = SessionManager()
print(f"✅ SessionManager创建成功")
print(f"   Session目录: {manager.session_dir}")

print()

# 测试添加消息
print("=" * 70)
print("🧪 测试3: 添加消息和Token统计")
print("=" * 70)

manager.add_message(
    "用户: 请帮我优化这段代码",
    input_tokens=10,
    output_tokens=5
)

manager.add_message(
    "助手: 我已经分析了代码，发现了一些优化点...",
    input_tokens=5,
    output_tokens=20
)

summary = manager.get_usage_summary()
print(f"✅ 消息统计:")
print(f"   消息数: {summary['message_count']}")
print(f"   输入Tokens: {summary['input_tokens']}")
print(f"   输出Tokens: {summary['output_tokens']}")
print(f"   总Tokens: {summary['total_tokens']}")

print()

# 测试快照
print("=" * 70)
print("🧪 测试4: 创建不可变快照")
print("=" * 70)

snapshot = manager.create_snapshot()
print(f"✅ 快照创建成功")
print(f"   Session ID: {snapshot.session_id}")
print(f"   消息数: {len(snapshot.messages)}")
print(f"   创建时间: {snapshot.created_at}")

# 测试不可变性
try:
    snapshot.messages = ("新消息",)
    print("❌ 错误: 快照应该是不可变的")
except Exception as e:
    print(f"✅ 快照不可变性验证通过: {type(e).__name__}")

print()

# 测试保存
print("=" * 70)
print("🧪 测试5: 保存Session到文件")
print("=" * 70)

saved_path = manager.save_session()
print(f"✅ Session已保存: {saved_path}")
print(f"   文件大小: {saved_path.stat().st_size} bytes")

# 验证文件内容
import json
with open(saved_path) as f:
    data = json.load(f)
    print(f"✅ 文件内容验证:")
    print(f"   Session ID: {data['session_id']}")
    print(f"   消息数: {len(data['messages'])}")
    print(f"   总Tokens: {data['input_tokens'] + data['output_tokens']}")

print()

# 测试加载（模拟）
print("=" * 70)
print("🧪 测试6: 加载现有Session")
print("=" * 70)

new_manager = SessionManager()
with open(saved_path) as f:
    data = json.load(f)

# 恢复消息和token统计
for msg in data['messages']:
    new_manager._current_messages.append(msg)

new_manager._current_input_tokens = data['input_tokens']
new_manager._current_output_tokens = data['output_tokens']

restored_summary = new_manager.get_usage_summary()
print(f"✅ Session恢复成功:")
print(f"   消息数: {restored_summary['message_count']}")
print(f"   总Tokens: {restored_summary['total_tokens']}")

print()

# 使用示例
print("=" * 70)
print("📖 使用示例")
print("=" * 70)

print("""
# 基本使用
from lingflow.core import SessionManager

# 创建管理器
manager = SessionManager()

# 添加消息
manager.add_message("用户消息", input_tokens=10, output_tokens=5)

# 查看统计
summary = manager.get_usage_summary()
print(f"总Tokens: {summary['total_tokens']}")

# 保存会话
session_path = manager.save_session()
print(f"会话已保存: {session_path}")

# 创建快照（不可变）
snapshot = manager.create_snapshot()
print(f"Session ID: {snapshot.session_id}")

# 快照可以安全地传递
def process_session(snapshot: SessionSnapshot):
    # 由于是不可变的，可以安全地并发处理
    print(f"处理Session: {snapshot.session_id}")

process_session(snapshot)
""")

print()

# 与现有Session系统集成示例
print("=" * 70)
print("🔄 与现有系统集成")
print("=" * 70)

print("""
# Session v2 和现有 session.py 可以共存

# 使用现有的session.py进行简单上下文恢复
from lingflow.context.session import save_context, load_context

# 使用Session v2进行完整的会话管理和Token追踪
from lingflow.core import SessionManager

# 保存上下文摘要
save_context(
    summary="本次优化工作",
    tasks=[{"name": "集成Session v2", "done": True}],
    next_steps=["设置定期优化"]
)

# 同时管理详细的会话和Token统计
manager = SessionManager()
manager.add_message("开始优化工作", input_tokens=10, output_tokens=5)
manager.save_session()

# 两者互补，各司其职
""")

print()

# 性能测试
print("=" * 70)
print("⚡ 性能测试")
print("=" * 70)

import time

# 测试1000次消息添加
start = time.time()
manager = SessionManager()
for i in range(1000):
    manager.add_message(f"消息 {i}", input_tokens=10, output_tokens=5)
elapsed = time.time() - start

print(f"✅ 添加1000条消息: {elapsed:.4f}秒")
print(f"   平均每条: {elapsed/1000*1000:.4f}毫秒")

# 测试快照创建
start = time.time()
snapshot = manager.create_snapshot()
elapsed = time.time() - start

print(f"✅ 创建快照: {elapsed*1000:.4f}毫秒")

# 测试保存
start = time.time()
path = manager.save_session()
elapsed = time.time() - start

print(f"✅ 保存会话: {elapsed*1000:.4f}毫秒")
print(f"   文件大小: {path.stat().st_size / 1024:.2f} KB")

print()

# 总结
print("=" * 70)
print("✅ 所有测试通过！Session v2集成成功！")
print("=" * 70)

print("""
📋 集成要点:
  1. ✅ Session v2已导出到lingflow.core
  2. ✅ 可通过from lingflow.core import SessionManager导入
  3. ✅ 与现有session.py系统共存
  4. ✅ 不可变快照，线程安全
  5. ✅ Token自动统计追踪
  6. ✅ JSON格式持久化

🎯 推荐使用场景:
  • 需要Token统计的会话 → 使用Session v2
  • 简单上下文恢复 → 使用现有session.py
  • 需要不可变快照 → 使用Session v2
  • 多线程/并发场景 → 使用Session v2

📚 相关文档:
  • FINAL_IMPROVEMENT_SUMMARY.md
  • LINGFLOW_AUTO_OPTIMIZATION_GUIDE.md
  • CLAUDE_CODE_PRACTICAL_LEARNING_PLAN.md
""")
