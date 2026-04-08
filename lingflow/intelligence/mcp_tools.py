"""灵议 MCP 工具

为灵议 (Council) 提供 MCP (Model Context Protocol) 工具接口。
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from .collectors.lingflow_monitor import LingFlowMonitor
from .logging_config import get_logger

logger = get_logger(__name__)


def _score_issue(mention, index: int) -> float:
    """为单个 issue 计算简化的影响力分数

    LingFlowMonitor 返回自己的 MentionData（非 models.common.MentionData），
    因此使用独立的评分逻辑而非 InfluenceAnalyzer。

    Args:
        mention: LingFlowMonitor.MentionData 实例
        index: 在列表中的位置（越新越高）

    Returns:
        影响力分数 (0-100)
    """
    score = 0.0

    reactions = sum(mention.reactions.values()) if isinstance(mention.reactions, dict) else 0
    score += min(30, reactions * 0.5)
    score += min(30, mention.comments * 3)

    title_bonus = 10 if mention.title else 0
    score += title_bonus

    content_len = len(mention.content) if mention.content else 0
    if content_len > 200:
        score += 15
    elif content_len > 50:
        score += 10

    label_keywords = {"bug", "enhancement", "feature", "help wanted", "good first issue"}
    for label in mention.labels:
        if label.lower() in label_keywords:
            score += 5

    score = min(100.0, score)
    return round(score, 1)


def get_top_issues(
    repo: str = "guangda88/LingFlow",
    token: Optional[str] = None,
    state: str = "open",
    days: int = 30,
    top_n: int = 10,
) -> Dict[str, Any]:
    """获取按影响力排名的 Top Issues

    Args:
        repo: GitHub 仓库 (格式: owner/repo)
        token: GitHub Personal Access Token
        state: issue 状态 (open, closed, all)
        days: 只获取最近 N 天的问题
        top_n: 返回前 N 个

    Returns:
        包含 top issues 和摘要的字典
    """
    monitor = LingFlowMonitor(repo=repo, token=token)
    mentions = monitor.collect_issues(state=state, days=days)

    if not mentions:
        return {
            "total": 0,
            "top_issues": [],
            "summary": "No issues found in the specified time range.",
        }

    scored = [(m, _score_issue(m, i)) for i, m in enumerate(mentions)]
    scored.sort(key=lambda x: x[1], reverse=True)

    top_issues = []
    for mention, score_val in scored[:top_n]:
        issue = {
            "title": mention.title,
            "url": mention.url,
            "author": mention.author,
            "state": mention.state,
            "labels": mention.labels,
            "comments": mention.comments,
            "influence_score": score_val,
            "published_at": mention.published_at,
        }
        if mention.reactions:
            issue["reactions"] = mention.reactions
        top_issues.append(issue)

    summary = {
        "repo": repo,
        "state": state,
        "days": days,
        "total_issues": len(mentions),
        "returned": len(top_issues),
        "generated_at": datetime.now().isoformat(),
    }

    return {
        "total": len(mentions),
        "top_issues": top_issues,
        "summary": summary,
    }


def get_issue_trends(
    repo: str = "guangda88/LingFlow",
    token: Optional[str] = None,
    days: int = 90,
) -> Dict[str, Any]:
    """获取 Issue 趋势分析

    Args:
        repo: GitHub 仓库
        token: GitHub Token
        days: 分析最近 N 天

    Returns:
        趋势分析结果
    """
    monitor = LingFlowMonitor(repo=repo, token=token)

    open_issues = monitor.collect_issues(state="open", days=days)
    closed_issues = monitor.collect_issues(state="closed", days=days)

    all_issues = open_issues + closed_issues

    if not all_issues:
        return {
            "total_open": 0,
            "total_closed": 0,
            "trends": {},
        }

    labels_counter: Dict[str, int] = {}
    authors_counter: Dict[str, int] = {}
    for issue in all_issues:
        for label in issue.labels:
            labels_counter[label] = labels_counter.get(label, 0) + 1
        authors_counter[issue.author] = authors_counter.get(issue.author, 0) + 1

    top_labels = sorted(labels_counter.items(), key=lambda x: x[1], reverse=True)[:10]
    top_authors = sorted(authors_counter.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_open": len(open_issues),
        "total_closed": len(closed_issues),
        "open_ratio": round(len(open_issues) / max(len(all_issues), 1), 2),
        "top_labels": [{"label": label, "count": c} for label, c in top_labels],
        "top_authors": [{"author": a, "count": c} for a, c in top_authors],
        "period_days": days,
        "generated_at": datetime.now().isoformat(),
    }


def main() -> None:
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(description="灵议 MCP 工具")
    parser.add_argument("command", choices=["top-issues", "trends"], help="命令")
    parser.add_argument("--repo", default="guangda88/LingFlow", help="GitHub 仓库")
    parser.add_argument("--days", type=int, default=30, help="最近 N 天")
    parser.add_argument("--top-n", type=int, default=10, help="返回前 N 个")
    parser.add_argument("--state", default="open", help="Issue 状态")
    args = parser.parse_args()

    if args.command == "top-issues":
        result = get_top_issues(
            repo=args.repo,
            state=args.state,
            days=args.days,
            top_n=args.top_n,
        )
    elif args.command == "trends":
        result = get_issue_trends(
            repo=args.repo,
            days=args.days,
        )
    else:
        result = {"error": f"Unknown command: {args.command}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
