"""LingScheduler tests."""

import asyncio
import pytest

from lingflow.scheduler import LingScheduler


@pytest.mark.unit
class TestLingScheduler:
    def setup_method(self) -> None:
        self.results: list = []
        self.scheduler = LingScheduler(persist=False)
        self.scheduler.register_callback("collect", self._collect)
        self.scheduler.register_callback("fail_once", self._fail_once)

    async def _collect(self, params: dict) -> str:
        self.results.append(params.get("val", "default"))
        return "ok"

    async def _fail_once(self, params: dict) -> str:
        call_count = params.setdefault("_call_count", 0)
        params["_call_count"] = call_count + 1
        if params["_call_count"] < 2:
            raise RuntimeError("not yet")
        self.results.append("recovered")
        return "recovered"

    @pytest.mark.asyncio
    async def test_delay_task(self) -> None:
        self.scheduler.add_delay("test", "collect", delay_seconds=0.1, params={"val": "hello"})
        await self.scheduler.start()
        await asyncio.sleep(0.5)
        await self.scheduler.stop()
        assert "hello" in self.results

    @pytest.mark.asyncio
    async def test_interval_task(self) -> None:
        self.scheduler.add_interval("test", "collect", interval_seconds=0.1, params={"val": "tick"})
        await self.scheduler.start()
        await asyncio.sleep(0.5)
        await self.scheduler.stop()
        assert self.results.count("tick") >= 3

    @pytest.mark.asyncio
    async def test_cancel_task(self) -> None:
        tid = self.scheduler.add_interval("test", "collect", interval_seconds=0.1, params={"val": "nope"})
        self.scheduler.cancel_task(tid)
        await self.scheduler.start()
        await asyncio.sleep(0.3)
        await self.scheduler.stop()
        assert "nope" not in self.results

    @pytest.mark.asyncio
    async def test_list_tasks(self) -> None:
        self.scheduler.add_delay("t1", "collect", delay_seconds=10)
        self.scheduler.add_interval("t2", "collect", interval_seconds=60)
        tasks = self.scheduler.list_tasks()
        assert len(tasks) == 2
        types = {t["type"] for t in tasks}
        assert "delay" in types
        assert "interval" in types

    @pytest.mark.asyncio
    async def test_retry_on_failure(self) -> None:
        self.scheduler.add_delay("retry_test", "fail_once", delay_seconds=0.1,
                                 params={"val": "x"}, max_retries=3)
        await self.scheduler.start()
        await asyncio.sleep(8.0)
        await self.scheduler.stop()
        assert "recovered" in self.results

    def test_add_and_remove(self) -> None:
        tid = self.scheduler.add_delay("x", "collect", delay_seconds=10)
        assert len(self.scheduler.list_tasks()) == 1
        assert self.scheduler.remove_task(tid) is True
        assert len(self.scheduler.list_tasks()) == 0
        assert self.scheduler.remove_task("nonexistent") is False
