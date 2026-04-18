#!/usr/bin/env python3
"""数据导入调度器

监控批量导入进度，支持:
- 断点续传（基于检查点文件）
- 限速控制
- 定时报告
- 失败重试
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/ai/LingFlow/scripts/scheduler.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("import_scheduler")

CHECKPOINT = Path("/home/ai/LingFlow/scripts/import_checkpoint.json")
TEXTBOOK_DIR = Path("/home/ai/zhineng-knowledge-system/data/textbooks/txt格式")
REPORT_INTERVAL = 300
DEFAULT_BATCH_SIZE = 5
MAX_RETRIES = 2
RATE_LIMIT_DELAY = 60


@dataclass
class RetryEntry:
    filename: str
    attempt: int
    last_error: str
    next_retry: float


@dataclass
class SchedulerState:
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_chunks: int = 0
    total_embedded: int = 0
    retries: List[Dict] = field(default_factory=list)
    started_at: str = ""


def load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    return {}


def count_pending_files() -> int:
    cp = load_checkpoint()
    completed = set(cp.get("completed_files", {}).keys())
    all_files = list(TEXTBOOK_DIR.glob("*.txt"))
    return sum(1 for f in all_files if f.name not in completed)


def print_status():
    cp = load_checkpoint()
    completed = cp.get("completed_files", {})
    total = len(list(TEXTBOOK_DIR.glob("*.txt")))
    done = len(completed)
    chunks = cp.get("total_chunks", 0)
    embedded = cp.get("total_embedded", 0)
    last = cp.get("last_file", "无")
    updated = cp.get("updated_at", "无")

    success = sum(1 for v in completed.values() if v == "success")
    errors = sum(1 for v in completed.values() if v == "error")

    print(f"\n{'=' * 50}")
    print("批量导入状态报告")
    print(f"{'=' * 50}")
    print(f"总文件数:     {total}")
    print(f"已完成:       {done} (成功: {success}, 失败: {errors})")
    print(f"待处理:       {total - done}")
    print(f"总块数:       {chunks}")
    print(f"总嵌入数:     {embedded}")
    print(f"最后处理:     {last}")
    print(f"更新时间:     {updated}")
    print(f"{'=' * 50}\n")


async def run_scheduled_import(batch_size: int = DEFAULT_BATCH_SIZE, continuous: bool = False):
    from batch_textbook_import import run_batch_import

    iteration = 0
    while True:
        iteration += 1
        pending = count_pending_files()
        if pending == 0:
            log.info("所有文件已处理完成")
            break

        log.info(f"[轮次 {iteration}] 剩余 {pending} 个文件, 本次处理 {min(batch_size, pending)} 个")
        await run_batch_import(limit=batch_size)
        print_status()

        if not continuous:
            break

        pending = count_pending_files()
        if pending == 0:
            log.info("所有文件已处理完成")
            break

        log.info(f"等待 {RATE_LIMIT_DELAY}s 后继续...")
        await asyncio.sleep(RATE_LIMIT_DELAY)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="数据导入调度器")
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH_SIZE, help="每批处理文件数")
    parser.add_argument("--continuous", action="store_true", help="持续运行直到完成")
    parser.add_argument("--status", action="store_true", help="仅显示当前状态")
    parser.add_argument("--reset-failed", action="store_true", help="重置失败文件以便重试")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.reset_failed:
        cp = load_checkpoint()
        completed = cp.get("completed_files", {})
        failed = {k: v for k, v in completed.items() if v == "error"}
        for k in failed:
            del completed[k]
        cp["completed_files"] = completed
        CHECKPOINT.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已重置 {len(failed)} 个失败文件: {list(failed.keys())}")
        return

    sys.path.insert(0, str(Path(__file__).parent))
    asyncio.run(run_scheduled_import(batch_size=args.batch, continuous=args.continuous))


if __name__ == "__main__":
    main()
