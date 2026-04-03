"""Targeted tests for rate_limiter APIClient and remaining uncovered code."""

import pytest
import asyncio
import threading
from unittest.mock import patch, MagicMock

from lingflow.utils.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    SmartRetry,
    ConcurrencyController,
    APIClient,
)


class TestAPIClient:
    def test_request_success(self):
        config = RateLimitConfig(requests_per_second=100.0, max_retries=1)
        client = APIClient(config, max_concurrent=2)
        result = client.request(lambda: "ok")
        assert result == "ok"

    def test_request_with_retry(self):
        config = RateLimitConfig(
            requests_per_second=100.0, max_retries=3, base_delay=0.01, jitter=False
        )
        client = APIClient(config, max_concurrent=2)
        call_count = [0]

        def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("429 Rate Limit Error")
            return "recovered"

        result = client.request(flaky)
        assert result == "recovered"

    def test_request_all_retries_fail(self):
        config = RateLimitConfig(
            requests_per_second=100.0, max_retries=2, base_delay=0.01, jitter=False
        )
        client = APIClient(config, max_concurrent=2)

        with pytest.raises(Exception, match="always fails"):
            client.request(lambda: (_ for _ in ()).throw(Exception("always fails")))

    def test_get_stats(self):
        config = RateLimitConfig(requests_per_second=100.0, max_retries=1)
        client = APIClient(config, max_concurrent=3)
        stats = client.get_stats()
        assert "active_requests" in stats
        assert "max_concurrent" in stats
        assert "success_count" in stats

    @pytest.mark.asyncio
    async def test_request_async_success(self):
        config = RateLimitConfig(requests_per_second=100.0, max_retries=1)
        client = APIClient(config, max_concurrent=2)

        async def async_func():
            return "async_ok"

        result = await client.request_async(async_func)
        assert result == "async_ok"


class TestRateLimiterAsync:
    @pytest.mark.asyncio
    async def test_acquire_async_basic(self):
        config = RateLimitConfig(requests_per_second=100.0)
        limiter = RateLimiter(config)
        await limiter.acquire_async()
        assert len(limiter.request_times) == 1

    @pytest.mark.asyncio
    async def test_acquire_async_waits(self):
        config = RateLimitConfig(requests_per_second=2.0)
        limiter = RateLimiter(config)
        await limiter.acquire_async()
        await limiter.acquire_async()
        assert len(limiter.request_times) == 2


class TestSmartRetryAsync:
    @pytest.mark.asyncio
    async def test_execute_async_success(self):
        config = RateLimitConfig(max_retries=3, base_delay=0.01, jitter=False)
        retry = SmartRetry(config)

        async def func():
            return "async_result"

        result = await retry.execute_async(func)
        assert result == "async_result"
        assert retry.success_count == 1

    @pytest.mark.asyncio
    async def test_execute_async_with_retry(self):
        config = RateLimitConfig(max_retries=3, base_delay=0.01, jitter=False)
        retry = SmartRetry(config)
        call_count = [0]

        async def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("429 Rate Limit Error")
            return "recovered"

        result = await retry.execute_async(flaky)
        assert result == "recovered"
        assert retry.error_count == 1

    @pytest.mark.asyncio
    async def test_execute_async_all_fail(self):
        config = RateLimitConfig(max_retries=2, base_delay=0.01, jitter=False)
        retry = SmartRetry(config)

        async def always_fail():
            raise Exception("502 Bad Gateway")

        with pytest.raises(Exception, match="502 Bad Gateway"):
            await retry.execute_async(always_fail)

    @pytest.mark.asyncio
    async def test_execute_async_with_callback(self):
        config = RateLimitConfig(max_retries=3, base_delay=0.01, jitter=False)
        retry = SmartRetry(config)
        call_count = [0]
        retry_log = []

        def on_retry(attempt, error, delay):
            retry_log.append((attempt, str(error)))

        async def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception(f"503 Service Unavailable-{call_count[0]}")
            return "ok"

        result = await retry.execute_async(flaky, on_retry=on_retry)
        assert result == "ok"
        assert len(retry_log) == 2


class TestConcurrencyControllerEdge:
    def test_concurrent_access(self):
        controller = ConcurrencyController(max_concurrent=3)
        results = []
        barrier = threading.Barrier(3)

        def worker(idx):
            controller.acquire()
            barrier.wait(timeout=5)
            results.append(idx)
            controller.release()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 3
        assert controller.get_active_count() == 0
