import pytest

from lingflow.utils.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    SmartRetry,
    ConcurrencyController,
    APIClient,
)


class TestRateLimiterAsync:
    @pytest.mark.asyncio
    async def test_acquire_async(self):
        config = RateLimitConfig(requests_per_second=100.0)
        limiter = RateLimiter(config)
        await limiter.acquire_async()
        assert len(limiter.request_times) == 1

    @pytest.mark.asyncio
    async def test_acquire_async_rate_limited(self):
        config = RateLimitConfig(requests_per_second=2.0)
        limiter = RateLimiter(config)
        limiter.request_times = [0.0, 0.0]
        await limiter.acquire_async()
        assert len(limiter.request_times) == 1


class TestSmartRetryAsync:
    @pytest.mark.asyncio
    async def test_execute_async_success(self):
        config = RateLimitConfig(max_retries=3)
        retry = SmartRetry(config)

        async def good_func():
            return "ok"

        result = await retry.execute_async(good_func)
        assert result == "ok"
        assert retry.success_count == 1

    @pytest.mark.asyncio
    async def test_execute_async_retry(self):
        config = RateLimitConfig(max_retries=3, base_delay=0.01)
        retry = SmartRetry(config)
        call_count = [0]

        async def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("429 rate limit")
            return "recovered"

        result = await retry.execute_async(flaky)
        assert result == "recovered"
        assert retry.error_count == 2

    @pytest.mark.asyncio
    async def test_execute_async_all_fail(self):
        config = RateLimitConfig(max_retries=2, base_delay=0.01)
        retry = SmartRetry(config)

        async def always_fail():
            raise Exception("500 server error")

        with pytest.raises(Exception, match="500 server error"):
            await retry.execute_async(always_fail)

    @pytest.mark.asyncio
    async def test_execute_async_non_retryable(self):
        config = RateLimitConfig(max_retries=3, base_delay=0.01)
        retry = SmartRetry(config)

        async def non_retryable():
            raise ValueError("bad input")

        with pytest.raises(ValueError, match="bad input"):
            await retry.execute_async(non_retryable)

    @pytest.mark.asyncio
    async def test_execute_async_with_callback(self):
        config = RateLimitConfig(max_retries=3, base_delay=0.01)
        retry = SmartRetry(config)
        callback_calls = []

        call_count = [0]

        async def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("connection timeout")
            return "ok"

        def on_retry(attempt, error, delay):
            callback_calls.append((attempt, str(error)))

        result = await retry.execute_async(flaky, on_retry=on_retry)
        assert result == "ok"
        assert len(callback_calls) == 1


class TestConcurrencyController:
    def test_acquire_release(self):
        c = ConcurrencyController(max_concurrent=2)
        c.acquire()
        assert c.get_active_count() == 1
        c.acquire()
        assert c.get_active_count() == 2
        c.release()
        assert c.get_active_count() == 1
        c.release()
        assert c.get_active_count() == 0


class TestAPIClientSync:
    def test_request_success(self):
        config = RateLimitConfig(requests_per_second=100.0)
        client = APIClient(config, max_concurrent=5)

        def api_call(x):
            return x * 2

        result = client.request(api_call, 5)
        assert result == 10

    def test_request_with_retry(self):
        config = RateLimitConfig(
            requests_per_second=100.0,
            max_retries=3,
            base_delay=0.01,
        )
        client = APIClient(config)
        call_count = [0]

        def flaky_api():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("429 rate limit")
            return "ok"

        result = client.request(flaky_api)
        assert result == "ok"

    def test_get_stats(self):
        config = RateLimitConfig()
        client = APIClient(config, max_concurrent=3)
        stats = client.get_stats()
        assert "error_count" in stats
        assert "active_requests" in stats
        assert stats["max_concurrent"] == 3


class TestAPIClientAsync:
    @pytest.mark.asyncio
    async def test_request_async_success(self):
        config = RateLimitConfig(requests_per_second=100.0, base_delay=0.01)
        client = APIClient(config, max_concurrent=5)

        async def async_api(x):
            return x * 3

        result = await client.request_async(async_api, 4)
        assert result == 12

    @pytest.mark.asyncio
    async def test_request_async_with_retry(self):
        config = RateLimitConfig(
            requests_per_second=100.0,
            max_retries=3,
            base_delay=0.01,
        )
        client = APIClient(config)
        call_count = [0]

        async def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("503 service unavailable")
            return "recovered"

        result = await client.request_async(flaky)
        assert result == "recovered"
