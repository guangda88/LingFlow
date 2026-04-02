"""Rate limiter tests"""

import time
import threading
import pytest

from lingflow.utils.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    SmartRetry,
    ConcurrencyController,
    APIClient,
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


class TestRateLimiter:
    def test_acquire_basic(self):
        limiter = RateLimiter(RateLimitConfig(requests_per_second=10.0))
        limiter.acquire()
        assert len(limiter.request_times) >= 1

    def test_acquire_respects_rate(self):
        cfg = RateLimitConfig(requests_per_second=2.0)
        limiter = RateLimiter(cfg)
        start = time.time()
        for _ in range(4):
            limiter.acquire()
        elapsed = time.time() - start
        assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_acquire_async(self):
        limiter = RateLimiter(RateLimitConfig(requests_per_second=10.0))
        await limiter.acquire_async()
        assert len(limiter.request_times) >= 1


class TestSmartRetry:
    def test_success_no_retry(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3, base_delay=0.01, jitter=False))
        result = retry.execute(lambda: 42)
        assert result == 42
        assert retry.success_count == 1
        assert retry.error_count == 0

    def test_retry_then_success(self):
        retry = SmartRetry(RateLimitConfig(max_retries=5, base_delay=0.01, jitter=False))
        call_count = [0]

        def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("429 Rate Limit")
            return "ok"

        result = retry.execute(flaky)
        assert result == "ok"
        assert retry.success_count == 1
        assert retry.error_count == 2

    def test_all_retries_fail(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3, base_delay=0.01, jitter=False))

        def always_fail():
            raise Exception("429 Rate Limit")

        with pytest.raises(Exception, match="429"):
            retry.execute(always_fail)

    def test_non_retryable_error(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3, base_delay=0.01))
        call_count = [0]

        def bad():
            call_count[0] += 1
            raise ValueError("bad input")

        with pytest.raises(ValueError, match="bad input"):
            retry.execute(bad)
        assert call_count[0] == 1

    def test_on_retry_callback(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3, base_delay=0.01, jitter=False))
        call_count = [0]
        callback_calls = []

        def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("500 Server Error")
            return "ok"

        def on_retry(attempt, error, delay):
            callback_calls.append((attempt, str(error), delay))

        result = retry.execute(flaky, on_retry=on_retry)
        assert result == "ok"
        assert len(callback_calls) == 1
        assert callback_calls[0][0] == 0

    def test_get_stats(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3, base_delay=0.01))
        retry.execute(lambda: 1)
        stats = retry.get_stats()
        assert stats["success_count"] == 1
        assert stats["error_count"] == 0
        assert stats["error_rate"] == 0.0
        assert stats["last_error_time"] is None

    def test_exponential_backoff(self):
        cfg = RateLimitConfig(max_retries=4, base_delay=0.01, jitter=False, exponential_backoff=True)
        retry = SmartRetry(cfg)
        delay0 = retry._calculate_delay(0)
        delay1 = retry._calculate_delay(1)
        assert delay1 > delay0

    def test_fixed_delay(self):
        cfg = RateLimitConfig(base_delay=0.5, jitter=False, exponential_backoff=False)
        retry = SmartRetry(cfg)
        d0 = retry._calculate_delay(0)
        d1 = retry._calculate_delay(1)
        assert d0 == d1 == 0.5

    def test_max_delay_cap(self):
        cfg = RateLimitConfig(base_delay=100.0, max_delay=1.0, jitter=False, exponential_backoff=True)
        retry = SmartRetry(cfg)
        d = retry._calculate_delay(10)
        assert d <= 1.0

    @pytest.mark.asyncio
    async def test_execute_async_success(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3, base_delay=0.01, jitter=False))

        async def ok():
            return "async_ok"

        result = await retry.execute_async(ok)
        assert result == "async_ok"

    @pytest.mark.asyncio
    async def test_execute_async_retry(self):
        retry = SmartRetry(RateLimitConfig(max_retries=4, base_delay=0.01, jitter=False))
        call_count = [0]

        async def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("connection timeout")
            return "ok"

        result = await retry.execute_async(flaky)
        assert result == "ok"

    def test_should_retry_network_error(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3))
        assert retry._should_retry(Exception("connection refused"), 0) is True

    def test_should_retry_timeout(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3))
        assert retry._should_retry(Exception("timeout"), 0) is True

    def test_should_not_retry_at_limit(self):
        retry = SmartRetry(RateLimitConfig(max_retries=3))
        assert retry._should_retry(Exception("429"), 2) is False


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

    def test_threaded(self):
        ctrl = ConcurrencyController(max_concurrent=3)
        results = []

        def worker():
            ctrl.acquire()
            results.append(ctrl.get_active_count())
            ctrl.release()

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 5


class TestAPIClient:
    def test_request_success(self):
        cfg = RateLimitConfig(requests_per_second=100.0, max_retries=1, base_delay=0.01)
        client = APIClient(cfg, max_concurrent=2)
        result = client.request(lambda: "response")
        assert result == "response"

    def test_request_with_retry(self):
        cfg = RateLimitConfig(requests_per_second=100.0, max_retries=3, base_delay=0.01, jitter=False)
        client = APIClient(cfg, max_concurrent=2)
        call_count = [0]

        def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("502 Bad Gateway")
            return "ok"

        result = client.request(flaky)
        assert result == "ok"

    def test_get_stats(self):
        cfg = RateLimitConfig(requests_per_second=100.0, max_retries=1, base_delay=0.01)
        client = APIClient(cfg)
        client.request(lambda: 1)
        stats = client.get_stats()
        assert stats["success_count"] == 1
        assert stats["active_requests"] == 0
