"""Tests for lingflow/utils/rate_limiter.py"""

import time
import threading

import pytest

from lingflow.utils.rate_limiter import (
    APIClient,
    ConcurrencyController,
    RateLimitConfig,
    RateLimiter,
    SmartRetry,
)


class TestRateLimitConfig:
    def test_defaults(self):
        cfg = RateLimitConfig()
        assert cfg.requests_per_second == 2.0
        assert cfg.requests_per_minute == 100.0
        assert cfg.max_retries == 3
        assert cfg.base_delay == 1.0
        assert cfg.max_delay == 60.0
        assert cfg.jitter is True
        assert cfg.exponential_backoff is True

    def test_custom(self):
        cfg = RateLimitConfig(
            requests_per_second=5.0,
            max_retries=5,
            jitter=False,
        )
        assert cfg.requests_per_second == 5.0
        assert cfg.max_retries == 5
        assert cfg.jitter is False


class TestRateLimiter:
    def test_acquire_below_limit(self):
        limiter = RateLimiter(RateLimitConfig(requests_per_second=10.0))
        for _ in range(5):
            limiter.acquire()
        assert len(limiter.request_times) == 5

    def test_acquire_at_limit_waits(self):
        limiter = RateLimiter(RateLimitConfig(requests_per_second=3.0))
        start = time.time()
        for _ in range(5):
            limiter.acquire()
        elapsed = time.time() - start
        assert len(limiter.request_times) == 5
        assert elapsed < 5.0

    def test_memory_leak_prevention(self):
        limiter = RateLimiter(RateLimitConfig(requests_per_second=1000.0))
        limiter.request_times = [time.time() - i for i in range(1100)]
        limiter.acquire()
        assert len(limiter.request_times) <= limiter.MAX_HISTORY_SIZE + 1

    @pytest.mark.asyncio
    async def test_acquire_async(self):
        limiter = RateLimiter(RateLimitConfig(requests_per_second=10.0))
        for _ in range(3):
            await limiter.acquire_async()
        assert len(limiter.request_times) == 3


class TestSmartRetry:
    def test_success_no_retry(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3, base_delay=0.01))
        result = retry.execute(lambda: 42)
        assert result == 42
        assert retry.success_count == 1
        assert retry.error_count == 0

    def test_retry_then_succeed(self):
        calls = [0]

        def flaky():
            calls[0] += 1
            if calls[0] < 3:
                raise Exception("429 Rate Limit")
            return "ok"

        retry = SmartRetry(RateLimitConfig(
            max_retries=4,
            base_delay=0.01,
            exponential_backoff=False,
            jitter=False,
        ))
        result = retry.execute(flaky)
        assert result == "ok"
        assert retry.success_count == 1
        assert retry.error_count == 2

    def test_all_retries_fail(self):
        def always_fail():
            raise Exception("500 Internal Server Error")

        retry = SmartRetry(RateLimitConfig(
            max_retries=2,
            base_delay=0.01,
            exponential_backoff=False,
            jitter=False,
        ))
        with pytest.raises(Exception, match="500"):
            retry.execute(always_fail)
        assert retry.error_count == 2

    def test_non_retryable_error(self):
        def raise_value_error():
            raise ValueError("bad input")

        retry = SmartRetry(RateLimitConfig(max_retries=3, base_delay=0.01))
        with pytest.raises(ValueError):
            retry.execute(raise_value_error)

    def test_on_retry_callback(self):
        callbacks = []
        calls = [0]

        def flaky():
            calls[0] += 1
            if calls[0] < 2:
                raise Exception("429 Rate Limit")
            return "ok"

        def cb(attempt, error, delay):
            callbacks.append((attempt, str(error)))

        retry = SmartRetry(RateLimitConfig(
            max_retries=3,
            base_delay=0.01,
            exponential_backoff=False,
            jitter=False,
        ))
        retry.execute(flaky, on_retry=cb)
        assert len(callbacks) == 1
        assert callbacks[0][0] == 0

    def test_exponential_backoff_delay(self):
        retry = SmartRetry(RateLimitConfig(
            base_delay=1.0,
            max_delay=100.0,
            exponential_backoff=True,
            jitter=False,
        ))
        assert retry._calculate_delay(0) == 1.0
        assert retry._calculate_delay(1) == 2.0
        assert retry._calculate_delay(3) == 8.0

    def test_fixed_delay(self):
        retry = SmartRetry(RateLimitConfig(
            base_delay=0.5,
            exponential_backoff=False,
            jitter=False,
        ))
        assert retry._calculate_delay(0) == 0.5
        assert retry._calculate_delay(5) == 0.5

    def test_max_delay_cap(self):
        retry = SmartRetry(RateLimitConfig(
            base_delay=10.0,
            max_delay=30.0,
            exponential_backoff=True,
            jitter=False,
        ))
        assert retry._calculate_delay(5) == 30.0

    def test_jitter_adds_randomness(self):
        retry = SmartRetry(RateLimitConfig(
            base_delay=1.0,
            jitter=True,
            exponential_backoff=False,
        ))
        delays = [retry._calculate_delay(0) for _ in range(50)]
        assert min(delays) < 1.0
        assert max(delays) > 1.0

    def test_should_retry_rate_limit(self):
        retry = SmartRetry()
        assert retry._should_retry(Exception("429 Too Many Requests"), 0) is True

    def test_should_retry_server_error(self):
        retry = SmartRetry()
        assert retry._should_retry(Exception("503 Service Unavailable"), 0) is True

    def test_should_retry_connection_error(self):
        retry = SmartRetry()
        assert retry._should_retry(Exception("Connection timeout"), 0) is True

    def test_should_not_retry_at_max(self):
        retry = SmartRetry(RateLimitConfig(max_retries=2))
        assert retry._should_retry(Exception("429"), 1) is False

    def test_should_not_retry_other_errors(self):
        retry = SmartRetry()
        assert retry._should_retry(Exception("unknown problem"), 0) is False

    def test_get_stats(self):
        retry = SmartRetry()
        retry.success_count = 5
        retry.error_count = 2
        stats = retry.get_stats()
        assert stats["success_count"] == 5
        assert stats["error_count"] == 2
        assert stats["error_rate"] == pytest.approx(2 / 7, abs=0.01)
        assert stats["last_error_time"] is None

    @pytest.mark.asyncio
    async def test_execute_async_success(self):
        retry = SmartRetry(RateLimitConfig(max_retries=2, base_delay=0.01))

        async def coro_fn():
            return 99

        result = await retry.execute_async(coro_fn)
        assert result == 99

    @pytest.mark.asyncio
    async def test_execute_async_retry(self):
        calls = [0]

        async def flaky():
            calls[0] += 1
            if calls[0] < 2:
                raise Exception("429 rate limit")
            return "async_ok"

        retry = SmartRetry(RateLimitConfig(
            max_retries=3,
            base_delay=0.01,
            exponential_backoff=False,
            jitter=False,
        ))
        result = await retry.execute_async(flaky)
        assert result == "async_ok"


class TestConcurrencyController:
    def test_acquire_release(self):
        ctrl = ConcurrencyController(max_concurrent=2)
        ctrl.acquire()
        assert ctrl.get_active_count() == 1
        ctrl.acquire()
        assert ctrl.get_active_count() == 2
        ctrl.release()
        assert ctrl.get_active_count() == 1
        ctrl.release()
        assert ctrl.get_active_count() == 0

    def test_max_concurrent(self):
        ctrl = ConcurrencyController(max_concurrent=1)
        results = []

        def worker(wid):
            ctrl.acquire()
            results.append(f"start-{wid}")
            time.sleep(0.05)
            results.append(f"end-{wid}")
            ctrl.release()

        t1 = threading.Thread(target=worker, args=(1,))
        t2 = threading.Thread(target=worker, args=(2,))
        t1.start()
        time.sleep(0.02)
        t2.start()
        t1.join()
        t2.join()
        assert "start-1" in results
        assert "start-2" in results


class TestAPIClient:
    def test_request_success(self):
        client = APIClient(
            RateLimitConfig(requests_per_second=100.0, max_retries=1),
            max_concurrent=2,
        )
        result = client.request(lambda x: x * 2, 21)
        assert result == 42

    def test_request_with_retry(self):
        calls = [0]

        def flaky(x):
            calls[0] += 1
            if calls[0] < 2:
                raise Exception("429 rate limit")
            return x * 3

        client = APIClient(
            RateLimitConfig(requests_per_second=100.0, max_retries=3, base_delay=0.01),
            max_concurrent=2,
        )
        result = client.request(flaky, 7)
        assert result == 21

    def test_get_stats(self):
        client = APIClient(max_concurrent=3)
        stats = client.get_stats()
        assert "active_requests" in stats
        assert "max_concurrent" in stats
        assert stats["max_concurrent"] == 3
        assert stats["error_count"] == 0
