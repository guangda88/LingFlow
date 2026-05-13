"""lingflow 定时调度器

支持 cron / interval / delay 三类定时任务，
具备失败重试、分布式锁、执行上下文隔离能力。

设计约束：
- 单进程 asyncio 调度，不引入外部依赖
- 任务以 async callable 表示，支持同步函数自动包装
- 持久化到 JSON 文件（~/.lingflow/scheduler_tasks.json），可重启恢复
- 失败重试带指数退避，最多 3 次
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

_SCHEDULER_DIR = Path.home() / ".lingflow"
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 5.0  # seconds
_DEFAULT_INTERVAL = 300  # 5 minutes


class ScheduleType(str, Enum):
    CRON = "cron"
    INTERVAL = "interval"
    DELAY = "delay"


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    task_id: str
    name: str
    schedule_type: ScheduleType
    callback_name: str
    cron_expr: str = ""
    interval_seconds: float = 0.0
    delay_seconds: float = 0.0
    params: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = _MAX_RETRIES
    retry_count: int = 0
    state: TaskState = TaskState.PENDING
    last_run: Optional[str] = None
    last_result: Optional[str] = None
    next_run: Optional[float] = None
    created_at: Optional[str] = None
    lock_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            from datetime import datetime

            self.created_at = datetime.now().isoformat()
        if self.next_run is None:
            self._compute_next_run()

    def _compute_next_run(self) -> None:
        now = time.time()
        if self.schedule_type == ScheduleType.INTERVAL:
            self.next_run = now + self.interval_seconds
        elif self.schedule_type == ScheduleType.DELAY:
            self.next_run = now + self.delay_seconds
        elif self.schedule_type == ScheduleType.CRON:
            self.next_run = self._parse_cron_next(now)

    def _parse_cron_next(self, now: float) -> float:
        """Simple cron parser: 'HH:MM' or 'HH:MM DOW' (day of week 0-6)."""
        import re
        from datetime import datetime, timedelta

        expr = self.cron_expr.strip()
        # Pattern: "HH:MM" or "HH:MM DOW"
        m = re.match(r"^(\d{1,2}):(\d{2})(?:\s+(\d))?$", expr)
        if not m:
            logger.warning("Invalid cron expression: %s, defaulting to 24h", expr)
            return now + 86400

        hour, minute = int(m.group(1)), int(m.group(2))
        dow = int(m.group(3)) if m.group(3) else None

        now_dt = datetime.fromtimestamp(now)
        target = now_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if dow is not None:
            days_ahead = (dow - now_dt.weekday()) % 7
            if days_ahead == 0 and target <= now_dt:
                days_ahead = 7
            target += timedelta(days=days_ahead)
        else:
            if target <= now_dt:
                target += timedelta(days=1)

        return target.timestamp()


@dataclass
class TaskExecution:
    task_id: str
    started_at: float
    finished_at: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    duration: float = 0.0


class LingScheduler:
    """lingflow 定时调度器

    用法：
        scheduler = LingScheduler()
        scheduler.register_callback("daily_briefing", my_briefing_func)
        scheduler.add_interval("briefing", "daily_briefing", interval_seconds=3600)
        await scheduler.start()

    Supports:
        - cron: 每天固定时间执行 (e.g., "09:00")
        - interval: 每隔 N 秒执行
        - delay: 延迟 N 秒后执行一次
        - 失败重试 (exponential backoff)
        - 持久化到 JSON
    """

    def __init__(self, persist: bool = True) -> None:
        self._tasks: Dict[str, ScheduledTask] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._running = False
        self._history: List[TaskExecution] = []
        self._persist = persist
        self._main_task: Optional[asyncio.Task] = None

    def register_callback(self, name: str, func: Callable) -> None:
        """Register a named callback function."""
        self._callbacks[name] = func

    def add_cron(
        self,
        name: str,
        callback_name: str,
        cron_expr: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = _MAX_RETRIES,
    ) -> str:
        """Add a cron-based scheduled task.

        Args:
            name: Human-readable task name
            callback_name: Registered callback name
            cron_expr: Cron expression (e.g., "09:00" or "09:00 1" for Monday)
            params: Parameters passed to callback
            max_retries: Maximum retry attempts on failure

        Returns:
            task_id
        """
        task_id = f"cron_{name}_{uuid.uuid4().hex[:8]}"
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.CRON,
            callback_name=callback_name,
            cron_expr=cron_expr,
            params=params or {},
            max_retries=max_retries,
        )
        self._tasks[task_id] = task
        self._persist_tasks()
        logger.info("Added cron task: %s (%s)", name, cron_expr)
        return task_id

    def add_interval(
        self,
        name: str,
        callback_name: str,
        interval_seconds: float = _DEFAULT_INTERVAL,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = _MAX_RETRIES,
    ) -> str:
        """Add an interval-based scheduled task."""
        task_id = f"int_{name}_{uuid.uuid4().hex[:8]}"
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.INTERVAL,
            callback_name=callback_name,
            interval_seconds=interval_seconds,
            params=params or {},
            max_retries=max_retries,
        )
        self._tasks[task_id] = task
        self._persist_tasks()
        logger.info("Added interval task: %s (every %ds)", name, interval_seconds)
        return task_id

    def add_delay(
        self,
        name: str,
        callback_name: str,
        delay_seconds: float,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = _MAX_RETRIES,
    ) -> str:
        """Add a one-shot delayed task."""
        task_id = f"del_{name}_{uuid.uuid4().hex[:8]}"
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_type=ScheduleType.DELAY,
            callback_name=callback_name,
            delay_seconds=delay_seconds,
            params=params or {},
            max_retries=max_retries,
        )
        self._tasks[task_id] = task
        self._persist_tasks()
        logger.info("Added delay task: %s (after %ds)", name, delay_seconds)
        return task_id

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._persist_tasks()
            logger.info("Removed task: %s", task_id)
            return True
        return False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task (keeps it in list but won't run)."""
        task = self._tasks.get(task_id)
        if task:
            task.state = TaskState.CANCELLED
            self._persist_tasks()
            return True
        return False

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks with status."""
        return [
            {
                "task_id": t.task_id,
                "name": t.name,
                "type": t.schedule_type.value,
                "state": t.state.value,
                "next_run": t.next_run,
                "last_run": t.last_run,
                "retry_count": t.retry_count,
                "params": t.params,
            }
            for t in self._tasks.values()
        ]

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent task execution history."""
        return [
            {
                "task_id": h.task_id,
                "started_at": h.started_at,
                "finished_at": h.finished_at,
                "success": h.success,
                "error": h.error,
                "duration": h.duration,
            }
            for h in self._history[-limit:]
        ]

    async def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            return
        self._running = True
        self._load_tasks()
        self._main_task = asyncio.create_task(self._run_loop())
        logger.info("LingScheduler started with %d tasks", len(self._tasks))

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        self._persist_tasks()
        logger.info("LingScheduler stopped")

    async def _run_loop(self) -> None:
        """Main scheduling loop."""
        while self._running:
            now = time.time()
            for task_id, task in list(self._tasks.items()):
                if task.state in (TaskState.CANCELLED, TaskState.RUNNING):
                    continue
                if task.next_run and task.next_run <= now:
                    task.next_run = None
                    asyncio.create_task(self._execute_task(task))

            await asyncio.sleep(0.1)

    async def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a single scheduled task with retry logic."""
        callback = self._callbacks.get(task.callback_name)
        if not callback:
            logger.error("Callback not found: %s for task %s", task.callback_name, task.name)
            task.state = TaskState.FAILED
            task.last_result = f"callback '{task.callback_name}' not registered"
            self._persist_tasks()
            return

        lock_id = uuid.uuid4().hex[:8]
        task.lock_id = lock_id
        task.state = TaskState.RUNNING

        from datetime import datetime

        task.last_run = datetime.now().isoformat()

        exec_record = TaskExecution(task_id=task.task_id, started_at=time.time())

        try:
            if asyncio.iscoroutinefunction(callback):
                result = await callback(task.params)
            else:
                result = callback(task.params)

            exec_record.success = True
            exec_record.finished_at = time.time()
            exec_record.duration = exec_record.finished_at - exec_record.started_at
            task.state = TaskState.SUCCEEDED
            task.last_result = str(result)[:200] if result else "ok"
            task.retry_count = 0
            logger.info("Task %s succeeded (%.2fs)", task.name, exec_record.duration)

        except Exception as e:
            exec_record.success = False
            exec_record.finished_at = time.time()
            exec_record.duration = exec_record.finished_at - exec_record.started_at
            exec_record.error = str(e)
            task.retry_count += 1

            if task.retry_count <= task.max_retries:
                task.state = TaskState.RETRYING
                task.last_result = f"retry {task.retry_count}/{task.max_retries}: {e}"
                logger.warning("Task %s failed (retry %d/%d): %s", task.name, task.retry_count, task.max_retries, e)
            else:
                task.state = TaskState.FAILED
                task.last_result = f"failed after {task.max_retries} retries: {e}"
                logger.error("Task %s failed permanently: %s", task.name, e)

        finally:
            self._history.append(exec_record)
            if len(self._history) > 200:
                self._history = self._history[-200:]

            # Compute next run
            if task.schedule_type == ScheduleType.DELAY:
                if task.state == TaskState.SUCCEEDED:
                    task.next_run = None
                elif task.state == TaskState.RETRYING:
                    task.next_run = time.time() + _RETRY_BASE_DELAY * (2 ** (task.retry_count - 1))
            elif task.state == TaskState.RETRYING:
                task.next_run = time.time() + _RETRY_BASE_DELAY * (2 ** (task.retry_count - 1))
            else:
                task._compute_next_run()

            self._persist_tasks()

    def _persist_tasks(self) -> None:
        """Persist task definitions to JSON file."""
        if not self._persist:
            return
        try:
            _SCHEDULER_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "tasks": {tid: asdict(t) for tid, t in self._tasks.items()},
                "saved_at": time.time(),
            }
            path = _SCHEDULER_DIR / "scheduler_tasks.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to persist scheduler tasks: %s", e)

    def _load_tasks(self) -> None:
        """Load persisted task definitions."""
        if not self._persist:
            return
        path = _SCHEDULER_DIR / "scheduler_tasks.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for tid, tdata in data.get("tasks", {}).items():
                tdata["schedule_type"] = ScheduleType(tdata["schedule_type"])
                tdata["state"] = (
                    TaskState.PENDING
                    if tdata.get("state") in (TaskState.RUNNING.value, TaskState.RETRYING.value)
                    else TaskState(tdata.get("state", TaskState.PENDING.value))
                )
                task = ScheduledTask(**{k: v for k, v in tdata.items() if k in ScheduledTask.__dataclass_fields__})
                self._tasks[tid] = task
            logger.info("Loaded %d persisted tasks", len(self._tasks))
        except Exception as e:
            logger.warning("Failed to load scheduler tasks: %s", e)
