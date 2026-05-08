"""LingFlow 情报系统统一管线

编排 Star 追踪 → 多平台采集 → 分析 → 报告生成全流程。
支持独立运行或注册到 LingScheduler 定时调度。
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from lingflow.intelligence.collectors import (
    HNCollector,
    LingFlowMonitor,
    RedditCollector,
    StarTracker,
)
from lingflow.intelligence.analyzers import (
    AnalyzerPipeline,
    InfluenceAnalyzer,
    SentimentAnalyzer,
)
from lingflow.intelligence.reporters import DailyReporter

log = logging.getLogger("intel-pipeline")


def _collect_github(days: int) -> list:
    all_mentions = []
    try:
        monitor = LingFlowMonitor()
        all_mentions.extend(monitor.collect_issues(state="open", days=days))
        all_mentions.extend(monitor.collect_discussions(days=days))
        all_mentions.extend(monitor.collect_releases())
        if all_mentions:
            monitor.save_data(all_mentions)
    except Exception as e:
        log.warning("GitHub采集失败: %s", e)
    return all_mentions


def _collect_reddit(days: int) -> list:
    mentions = []
    try:
        reddit = RedditCollector()
        mentions = reddit.search_mentions(
            keywords=["LingFlow", "lingflow-core"],
            limit=100,
            days=days,
        )
        if mentions:
            reddit.save_data(mentions)
    except Exception as e:
        log.warning("Reddit采集失败: %s", e)
    return mentions


def _collect_hn(days: int) -> list:
    mentions = []
    try:
        hn = HNCollector()
        mentions = hn.search_mentions(
            keywords=["LingFlow", "lingflow-core"],
            limit=100,
            days=days,
        )
        if mentions:
            hn.save_data(mentions)
    except Exception as e:
        log.warning("HN采集失败: %s", e)
    return mentions


def _track_stars() -> Dict[str, int]:
    try:
        tracker = StarTracker()
        result = tracker.collect(max_users=300)
        return {
            "star_count": result.get("star_count", 0),
            "star_growth": result.get("growth", 0),
        }
    except Exception as e:
        log.warning("Star追踪失败: %s", e)
        return {"star_count": 0, "star_growth": 0}


def _analyze(mentions: list) -> Dict[str, Any]:
    if not mentions:
        return {}
    pipeline = AnalyzerPipeline([SentimentAnalyzer(), InfluenceAnalyzer()])
    return pipeline.run(mentions)


def _generate_reports(
    mentions: list,
    analysis: dict,
    star_count: int,
    star_growth: int,
    formats: List[str],
) -> List[str]:
    paths = []
    if not mentions:
        return paths
    reporter = DailyReporter()
    report = reporter.generate(
        mentions=mentions,
        star_growth=star_growth,
        star_count=star_count,
    )
    for fmt in formats:
        try:
            filepath = reporter.save(report, format=fmt)
            paths.append(str(filepath))
        except Exception as e:
            log.warning("保存%s报告失败: %s", fmt, e)
    return paths


def execute_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    days = params.get("days", 1)
    enable_github = params.get("enable_github", True)
    enable_reddit = params.get("enable_reddit", True)
    enable_hn = params.get("enable_hn", True)
    enable_stars = params.get("enable_stars", True)
    collect_only = params.get("collect_only", False)
    dry_run = params.get("dry_run", False)
    schedule = params.get("schedule", "")
    report_formats = params.get("report_formats", ["txt", "json", "markdown"])

    start_time = time.time()
    result: Dict[str, Any] = {
        "phase": "dry_run",
        "mentions_count": 0,
        "star_count": 0,
        "star_growth": 0,
        "analysis": {},
        "reports": [],
        "elapsed_seconds": 0,
        "scheduler_task_id": None,
    }

    if dry_run:
        platforms = []
        if enable_github:
            platforms.append("github")
        if enable_reddit:
            platforms.append("reddit")
        if enable_hn:
            platforms.append("hackernews")
        result["platforms"] = platforms
        result["days"] = days
        result["collect_only"] = collect_only
        result["enable_stars"] = enable_stars
        result["status"] = "dry_run"
        result["elapsed_seconds"] = round(time.time() - start_time, 2)
        return result

    # 1. Star 追踪
    star_info = {"star_count": 0, "star_growth": 0}
    if enable_stars:
        star_info = _track_stars()
    result["star_count"] = star_info["star_count"]
    result["star_growth"] = star_info["star_growth"]

    # 2. 数据采集
    all_mentions: list = []
    if enable_github:
        all_mentions.extend(_collect_github(days))
    if enable_reddit:
        all_mentions.extend(_collect_reddit(days))
    if enable_hn:
        all_mentions.extend(_collect_hn(days))

    result["mentions_count"] = len(all_mentions)
    result["phase"] = "collected"

    if collect_only:
        result["status"] = "collect_only"
        result["elapsed_seconds"] = round(time.time() - start_time, 2)
        return result

    # 3. 分析
    analysis = _analyze(all_mentions)
    result["analysis"] = analysis
    result["phase"] = "analyzed"

    # 4. 报告
    report_paths = _generate_reports(
        all_mentions, analysis,
        star_info["star_count"], star_info["star_growth"],
        report_formats,
    )
    result["reports"] = report_paths
    result["phase"] = "complete"
    result["status"] = "complete"
    result["elapsed_seconds"] = round(time.time() - start_time, 2)

    # 5. 可选：注册定时调度
    if schedule:
        try:
            from lingflow.scheduler import LingScheduler

            scheduler = LingScheduler()
            scheduler.register_callback("intel_pipeline_run", _scheduler_callback)
            task_id = scheduler.add_cron(
                name="intel_daily",
                callback_name="intel_pipeline_run",
                cron_expr=schedule,
                params={
                    "days": days,
                    "enable_github": enable_github,
                    "enable_reddit": enable_reddit,
                    "enable_hn": enable_hn,
                    "enable_stars": enable_stars,
                    "collect_only": collect_only,
                    "report_formats": report_formats,
                },
            )
            result["scheduler_task_id"] = task_id
            log.info("已注册定时调度: %s (%s)", task_id, schedule)
        except Exception as e:
            log.warning("注册定时调度失败: %s", e)
            result["scheduler_error"] = str(e)

    return result


def _scheduler_callback(params: Dict[str, Any]) -> Dict[str, Any]:
    log.info("定时调度触发情报管线")
    return execute_skill(params)
