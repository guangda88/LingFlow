"""EVOLUTION_LOG 解析和导入到记忆引擎

将 EVOLUTION_LOG.md 中的教训结构化导入 LingMemory：
- 每个 #xxx 条目作为一个 Episode
- 事件描述作为 body
- 根因分析作为 facets
- 硬化措施作为 facet points
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_EVOLUTION_LOG_PATH = Path("/home/ai/lingflow/EVOLUTION_LOG.md")
_LING_CLAUDE_PATH = Path.home() / "lingclaude"


def _ensure_memory_engine() -> Optional["LingMemory"]:
    """懒加载并返回记忆引擎实例"""
    try:
        if str(_LING_CLAUDE_PATH) not in sys.path:
            sys.path.insert(0, str(_LING_CLAUDE_PATH))
        from lingclaude.core.memory_engine import LingMemory
        return LingMemory()
    except ImportError as e:
        logger.warning("记忆引擎导入失败: %s", e)
        return None


def parse_evolution_log(log_path: Path = _EVOLUTION_LOG_PATH) -> List[Dict]:
    """解析 EVOLUTION_LOG.md

    返回格式:
    [{
        "id": "#001",
        "title": "失忆与编造 — 面对知识空白时的回避模式",
        "date": "2026-04-27",
        "body": "事件描述...",
        "root_cause": "根因...",
        "lessons": ["教训1", "教训2"],
        "measures": ["硬化措施1", "硬化措施2"],
        "tags": ["标签1", "标签2"],
    }]
    """
    if not log_path.exists():
        logger.warning("EVOLUTION_LOG.md 不存在: %s", log_path)
        return []

    content = log_path.read_text(encoding="utf-8")

    # 分割每个 #xxx 条目
    entries = []
    entry_pattern = re.compile(r"^##\s+(#\d+)\s+(.+)$", re.MULTILINE)
    matches = list(entry_pattern.finditer(content))

    for i, match in enumerate(matches):
        entry_id = match.group(1)
        title = match.group(2)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        entry_content = content[start:end]

        # 提取日期
        date_match = re.search(r"\*\*日期\*\*:\s*(20\d\d-\d\d-\d\d)", entry_content)
        date = date_match.group(1) if date_match else ""

        # 提取事件 (### 事件 到 下一个 ###)
        event_match = re.search(r"###\s*事件\s*\n(.+?)(?=\n###\s|\n##\s|\Z)", entry_content, re.DOTALL)
        event_body = event_match.group(1).strip() if event_match else ""

        # 提取根因 (可能是 "### 根因" 或 "### 根因分析")
        root_cause_match = re.search(r"###\s*(?:根因|根因分析)\s*\n(.+?)(?=\n###\s|\n##\s|\Z)", entry_content, re.DOTALL)
        root_cause = root_cause_match.group(1).strip() if root_cause_match else ""

        # 提取教训 (### 教训 或 ### 教训总结)
        lessons_match = re.search(r"###\s*(?:教训|教训总结)\s*\n(.+?)(?=\n###\s|\n##\s|\Z)", entry_content, re.DOTALL)
        lessons_text = lessons_match.group(1) if lessons_match else ""
        lessons = [l.strip() for l in re.findall(r"^\d+\.\s+(.+)$", lessons_text, re.MULTILINE)]
        if not lessons:
            bullet_lessons = [l.strip() for l in re.findall(r"^[-*]\s+(.+)$", lessons_text, re.MULTILINE)]
            lessons = bullet_lessons if bullet_lessons else [lessons_text.strip()] if lessons_text.strip() else []

        # 提取硬化措施
        measures_match = re.search(r"###\s*(?:硬化措施|改进措施)\s*\n(.+?)(?=\n###\s|\n##\s|\Z)", entry_content, re.DOTALL)
        measures_text = measures_match.group(1) if measures_match else ""
        measures = [m.strip() for m in re.findall(r"^\d+\.\s+(.+)$", measures_text, re.MULTILINE)]
        if not measures:
            bullet_measures = [m.strip() for m in re.findall(r"^[-*]\s+(.+)$", measures_text, re.MULTILINE)]
            measures = bullet_measures if bullet_measures else [measures_text.strip()] if measures_text.strip() else []

        # 提取标签（从标题和内容中推断）
        tags = []
        tag_keywords = {
            "元认知": ["元认知", "metacognition", "记忆", "失忆", "编造"],
            "编码": ["死代码", "basename", "编码", "验证"],
            "思考回路": ["思考回路", "thinking", "回避"],
            "进程": ["进程", "process", "kill", "wrapper"],
            "发布": ["发布", "publish", "发布编排", "灵扬"],
            "RAG": ["RAG", "检索", "知识库", "embedding"],
            "灵族": ["灵族", "成员重组", "共享服务"],
            "错误": ["错误", "bug", "修复"],
            "安全": ["安全", "凭据", "硬编码"],
            "工作流": ["workflow", "编排", "skill"],
        }
        for tag, keywords in tag_keywords.items():
            if any(k.lower() in (title + " " + event_body + " " + root_cause).lower() for k in keywords):
                tags.append(tag)

        entries.append({
            "id": entry_id,
            "title": title,
            "date": date,
            "body": event_body,
            "root_cause": root_cause,
            "lessons": lessons,
            "measures": measures,
            "tags": tags,
        })

    logger.info("解析到 %d 个 EVOLUTION_LOG 条目", len(entries))
    return entries


def import_to_memory(entries: List[Dict], force: bool = False) -> Dict:
    """将解析后的条目导入记忆引擎

    Args:
        entries: parse_evolution_log() 返回的条目列表
        force: 是否强制覆盖已有条目

    Returns:
        统计字典: {imported, skipped, errors}
    """
    mem = _ensure_memory_engine()
    if mem is None:
        return {"imported": 0, "skipped": 0, "errors": -1}

    stats = {"imported": 0, "skipped": 0, "errors": 0}

    for entry in entries:
        try:
            # 检查是否已存在（通过标签搜索近似匹配）
            existing = mem.store.search_episodes_by_tag([entry["id"]], limit=1)
            if existing and not force:
                stats["skipped"] += 1
                continue

            # 组合 body: 事件 + 根因
            body_parts = []
            if entry["body"]:
                body_parts.append(entry["body"])
            if entry["root_cause"]:
                body_parts.append(f"\n根因: {entry['root_cause']}")
            body = "\n".join(body_parts)

            # 创建 facets: 教训和硬化措施
            # ingest_incident 的 points 期望 list[str]（纯 claim 文本）
            facets = []
            if entry["lessons"]:
                facets.append({
                    "name": "教训",
                    "body": "从事件中吸取的关键教训",
                    "points": entry["lessons"],
                    "tags": ["教训"],
                })
            if entry["measures"]:
                facets.append({
                    "name": "硬化措施",
                    "body": "为防止重复发生而采取的具体措施",
                    "points": entry["measures"],
                    "tags": ["硬化措施", "改进"],
                })

            # 准备 tags: ID + 推断的标签
            tags = [entry["id"]] + entry["tags"]

            # 导入为 INCIDENT 类型的 Episode
            ep_id = mem.ingester.ingest_incident(
                title=f"{entry['id']} {entry['title']}",
                body=body,
                tags=tags,
                facets=facets,
                source="EVOLUTION_LOG.md",
            )

            if ep_id:
                stats["imported"] += 1
            else:
                stats["errors"] += 1

        except Exception as e:
            logger.warning("导入条目 %s 失败: %s", entry["id"], e)
            stats["errors"] += 1

    logger.info("导入完成: %d 新增, %d 跳过, %d 错误", stats["imported"], stats["skipped"], stats["errors"])
    return stats


def import_evolution_log(force: bool = False) -> Dict:
    """一键导入 EVOLUTION_LOG.md 到记忆引擎

    Args:
        force: 是否强制覆盖已有条目

    Returns:
        统计字典: {imported, skipped, errors, total_in_memory}
    """
    entries = parse_evolution_log()
    stats = import_to_memory(entries, force=force)

    mem = _ensure_memory_engine()
    if mem:
        mem_stats = mem.stats()
        stats["total_in_memory"] = mem_stats.get("episodes", 0)
    else:
        stats["total_in_memory"] = 0

    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser(description="导入 EVOLUTION_LOG.md 到记忆引擎")
    parser.add_argument("--force", action="store_true", help="强制覆盖已有条目")
    parser.add_argument("--list", action="store_true", help="只列出解析的条目，不导入")
    args = parser.parse_args()

    if args.list:
        entries = parse_evolution_log()
        for e in entries:
            print(f"\n{e['id']}: {e['title']}")
            print(f"  日期: {e['date']}")
            print(f"  教训数: {len(e['lessons'])}")
            print(f"  措施数: {len(e['measures'])}")
            print(f"  标签: {e['tags']}")
        print(f"\n总计: {len(entries)} 个条目")
    else:
        stats = import_evolution_log(force=args.force)
        print(f"导入统计:")
        print(f"  新增: {stats['imported']}")
        print(f"  跳过: {stats['skipped']}")
        print(f"  错误: {stats['errors']}")
        print(f"  记忆库中总计: {stats['total_in_memory']} 个 episode")
