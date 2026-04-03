"""Extended tests for rate_limiter covering remaining gaps."""
import asyncio
import threading
import time
from datetime import datetime
from unittest.mock import patch

import pytest

from lingflow.utils.rate_limiter import (
    APIClient,
    ConcurrencyController,
    RateLimitConfig,
    RateLimiter,
    SmartRetry,
)


class TestSmartRetryLastErrorTime:
    def test_last_error_time_set_after_error(self):
        config = RateLimitConfig(max_retries=1, base_delay=0.01)
        retry = SmartRetry(config)
        with pytest.raises(Exception, match="timeout"):
            retry.execute(lambda: (_ for _ in ()).throw(Exception("timeout error")))
        stats = retry.get_stats()
        assert stats["last_error_time"] is not None
        parsed = datetime.fromisoformat(stats["last_error_time"])
        assert isinstance(parsed, datetime)

    def test_error_rate_after_mixed_results(self):
        config = RateLimitConfig(max_retries=1, base_delay=0.01)
        retry = SmartRetry(config)
        retry.success_count = 3
        retry.error_count = 1
        stats = retry.get_stats()
        assert stats["error_rate"] == pytest.approx(0.25)

    def test_execute_with_args_kwargs_through_retry(self):
        call_log = []
        config = RateLimitConfig(max_retries=3, base_delay=0.01, exponential_backoff=False, jitter=False)

        def func(a, b, c=0):
            call_log.append((a, b, c))
            if len(call_log) < 2:
                raise Exception("500 error")
            return a + b + c

        retry = SmartRetry(config)
        result = retry.execute(func, 1, 2, c=3)
        assert result == 6
        assert len(call_log) == 2
        assert call_log[0] == (1, 2, 3)
        assert call_log[1] == (1, 2, 3)


class TestSmartRetryAsyncArgsKwargs:
    @pytest.mark.asyncio
    async def test_execute_async_with_args_kwargs(self):
        config = RateLimitConfig(max_retries=1, base_delay=0.01)
        retry = SmartRetry(config)

        async def func(a, b, c=0):
            return a + b + c

        result = await retry.execute_async(func, 1, 2, c=10)
        assert result == 13

    @pytest.mark.asyncio
    async def test_execute_async_args_through_retry(self):
        call_log = []
        config = RateLimitConfig(max_retries=3, base_delay=0.01, exponential_backoff=False, jitter=False)

        async def func(x, y=0):
            call_log.append((x, y))
            if len(call_log) < 2:
                raise Exception("connection refused")
            return x * y

        retry = SmartRetry(config)
        result = await retry.execute_async(func, 5, y=3)
        assert result == 15
        assert len(call_log) == 2


class TestAPIClientConcurrencyCleanup:
    def test_concurrency_released_on_exception(self):
        config = RateLimitConfig(max_retries=1, base_delay=0.01)
        client = APIClient(config, max_concurrent=1)

        def failing_func():
            raise RuntimeError("test failure")

        with pytest.raises(RuntimeError):
            client.request(failing_func)

        assert client.concurrency_controller.get_active_count() == 0

    @pytest.mark.asyncio
    async def test_async_concurrency_released_on_exception(self):
        config = RateLimitConfig(max_retries=1, base_delay=0.01)
        client = APIClient(config, max_concurrent=1)

        async def failing_func():
            raise RuntimeError("async failure")

        with pytest.raises(RuntimeError):
            await client.request_async(failing_func)

        assert client.concurrency_controller.get_active_count() == 0


class TestAPIClientDefaultConstructor:
    def test_default_config(self):
        client = APIClient()
        assert client.rate_limiter is not None
        assert client.retry_handler is not None
        assert client.concurrency_controller is not None
        stats = client.get_stats()
        assert stats["active_requests"] == 0
        assert stats["max_concurrent"] == 5


class TestAPIClientGetStats:
    def test_stats_after_async_request(self):
        config = RateLimitConfig(max_retries=1, base_delay=0.01)
        client = APIClient(config, max_concurrent=2)

        async def run():
            async def func():
                return "ok"
            await client.request_async(func)

        asyncio.run(run())
        stats = client.get_stats()
        assert stats["success_count"] == 1


class TestConcurrencyControllerEdgeCases:
    def test_release_without_acquire(self):
        cc = ConcurrencyController(max_concurrent=2)
        cc.release()
        assert cc.get_active_count() == -1

    def test_blocking_at_max_concurrent(self):
        cc = ConcurrencyController(max_concurrent=1)
        results = []
        cc.acquire()
        assert cc.get_active_count() == 1

        def try_acquire():
            cc.acquire()
            results.append("acquired")
            cc.release()

        t = threading.Thread(target=try_acquire)
        t.start()
        time.sleep(0.1)
        assert len(results) == 0

        cc.release()
        t.join(timeout=1.0)
        assert len(results) == 1


class TestRateLimiterMultithread:
    def test_concurrent_acquire(self):
        config = RateLimitConfig(requests_per_second=100)
        limiter = RateLimiter(config)
        results = []
        barrier = threading.Barrier(5)

        def worker():
            barrier.wait()
            limiter.acquire()
            results.append(time.time())

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        assert len(results) == 5


class TestSmartRetryNonRetryable:
    def test_non_retryable_raises_immediately(self):
        config = RateLimitConfig(max_retries=3, base_delay=0.01, exponential_backoff=False, jitter=False)
        retry = SmartRetry(config)
        retry_attempts = []

        def func():
            retry_attempts.append(1)
            raise ValueError("unknown error")

        with pytest.raises(ValueError):
            retry.execute(func)

        assert len(retry_attempts) == 1
        assert retry.error_count == 1
        assert retry.get_stats()["last_error_time"] is not None


class TestSmartRetryCallback:
    def test_on_retry_callback_with_async(self):
        config = RateLimitConfig(max_retries=3, base_delay=0.01, exponential_backoff=False, jitter=False)
        retry = SmartRetry(config)
        callback_log = []
        call_count = [0]

        async def func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("502 bad gateway")
            return "ok"

        async def run():
            return await retry.execute_async(
                func,
                on_retry=lambda attempt, error, delay: callback_log.append((attempt, str(error), delay))
            )

        result = asyncio.run(run())
        assert result == "ok"
        assert len(callback_log) == 2
        assert "502" in callback_log[0][1]
