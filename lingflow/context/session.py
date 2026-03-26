#!/usr/bin/env python3
"""LingFlow 会话恢复工具

在对话因 token 限制中断后，用于在新会话中快速恢复上下文。
"""

import json
from pathlib import Path
from datetime import datetime


SESSION_FILE = Path("/home/ai/.claude/projects/-home-ai-LingFlow/context/session.json")


def save_context(summary: str, tasks: list = None, next_steps: list = None):
    """保存当前会话上下文

    Args:
        summary: 会话摘要
        tasks: 任务列表 [{"task": "...", "done": bool}, ...]
        next_steps: 下一步计划
    """
    data = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "tasks": tasks or [],
        "next_steps": next_steps or []
    }
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_context() -> dict:
    """加载上次会话上下文"""
    if SESSION_FILE.exists():
        return json.loads(SESSION_FILE.read_text())
    return None


def print_recovery():
    """打印恢复信息"""
    data = load_context()
    if not data:
        print("没有找到上次的会话上下文")
        return

    print(f"\n{'='*50}")
    print(f"上次会话: {data['timestamp']}")
    print(f"{'='*50}\n")

    if data.get('summary'):
        print("摘要:")
        print(data['summary'])
        print()

    if data.get('tasks'):
        print("任务:")
        for t in data['tasks']:
            status = "✅" if t.get('done') else "◻"
            # 兼容 'name' 和 'task' 两种键名
            task_name = t.get('name') or t.get('task', '未命名任务')
            print(f"  {status} {task_name}")
        print()

    if data.get('next_steps'):
        print("下一步:")
        for i, step in enumerate(data['next_steps'], 1):
            print(f"  {i}. {step}")
        print()


if __name__ == "__main__":
    print_recovery()
