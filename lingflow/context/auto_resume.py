#!/usr/bin/env python3
"""自动会话恢复模块

在 LingFlow 导入时自动显示上次会话摘要（如果存在）。
"""

import sys
from pathlib import Path


SESSION_FILE = Path("/home/ai/.claude/projects/-home-ai-LingFlow/context/SESSION.md")
LAST_SHOWN_FILE = Path("/home/ai/.claude/projects/-home-ai-LingFlow/context/.last_shown")


def auto_resume() -> str:
    """自动恢复上次会话

    Returns:
        会话恢复文本，如果没有则返回空字符串
    """
    if not SESSION_FILE.exists():
        return ""

    content = SESSION_FILE.read_text(encoding="utf-8")

    # 检查是否已显示过
    if LAST_SHOWN_FILE.exists():
        last_content = LAST_SHOWN_FILE.read_text(encoding="utf-8")
        if last_content in content:
            # 已经显示过，返回简化版本
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "任务:" in line:
                    return "\n".join(lines[:i+1])
            return ""

    # 标记为已显示
    LAST_SHOWN_FILE.write_text(content[:100], encoding="utf-8")

    return f"""

╔══════════════════════════════════════════════════════════════╗
║                   🔙 上次会话恢复                              ║
╚══════════════════════════════════════════════════════════════╝

{content}

─────────────────────────────────────────────────────────────────
输入 'lingflow resume' 查看详情，或继续新任务
─────────────────────────────────────────────────────────────────"""


def save_resume_markdown(tasks: list, next_steps: list = None, summary: str = ""):
    """保存会话恢复信息（Markdown 格式）

    Args:
        tasks: 任务列表 [{"name": "...", "done": bool}, ...]
        next_steps: 下一步计划
        summary: 摘要
    """
    lines = []

    if summary:
        lines.append(f"📋 {summary}\n")

    if tasks:
        done_count = sum(1 for t in tasks if t.get("done"))
        total_count = len(tasks)
        lines.append(f"📊 任务进度: {done_count}/{total_count}\n")

        lines.append("任务:")
        for task in tasks:
            status = "✅" if task.get("done") else "◻"
            name = task.get("name", task.get("task", ""))
            lines.append(f"  {status} {name}")
        lines.append("")

    if next_steps:
        lines.append("下一步:")
        for i, step in enumerate(next_steps, 1):
            lines.append(f"  {i}. {step}")
        lines.append("")

    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text("\n".join(lines), encoding="utf-8")

    # 清除已显示标记
    if LAST_SHOWN_FILE.exists():
        LAST_SHOWN_FILE.unlink()


# 模块导入时尝试自动恢复
if __name__ != "__main__":
    resume_text = auto_resume()
    if resume_text:
        print(resume_text, file=sys.stderr)
