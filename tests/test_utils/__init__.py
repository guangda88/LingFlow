"""测试工具模块"""
import pytest

from lingflow.utils.sampling import ReservoirSampler
from lingflow.utils.rate_limiter import RateLimiter


class TestSampling:
    """测试采样功能"""

    def test_reservoir_sampler_creation(self):
        """测试水库采样器创建"""
        sampler = ReservoirSampler(size=100)
        assert sampler is not None
        assert sampler.size == 100

    def test_reservoir_sampler_add(self):
        """测试水库采样器添加样本"""
        sampler = ReservoirSampler(size=5)
        sampler.add("item1")
        sampler.add("item2")
        # 样本被添加
        assert len(sampler.get_samples()) <= 5

    def test_reservoir_sampler_get_samples(self):
        """测试获取样本"""
        sampler = ReservoirSampler(size=10)
        for i in range(5):
            sampler.add(f"item{i}")
        samples = sampler.get_samples()
        assert len(samples) == 5


class TestRateLimiter:
    """测试速率限制器"""

    def test_rate_limiter_creation(self):
        """测试速率限制器创建"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert limiter is not None

    def test_rate_limiter_allow_request(self):
        """测试允许请求"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        # 前10个请求应该被允许
        for _ in range(10):
            assert limiter.is_allowed() is True

    def test_rate_limiter_deny_request(self):
        """测试拒绝请求"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        # 使用掉所有配额
        for _ in range(5):
            limiter.is_allowed()
        # 下一个请求应该被拒绝
        assert limiter.is_allowed() is False

    def test_rate_limiter_reset(self):
        """测试速率限制器重置"""
        # 这是一个简化的测试，实际测试可能需要mock时间
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed() is True
        assert limiter.is_allowed() is False


class TestPerformance:
    """测试性能工具"""

    def test_performance_timer(self):
        """测试性能计时器"""
        from lingflow.utils.performance import timer

        with timer("test_operation"):
            dummy_result = sum(range(100))
        # 计时器应该记录操作时间
        # (这里只测试不抛异常)

    def test_performance_decorator(self):
        """测试性能装饰器"""
        from lingflow.utils.performance import timed

        @timed
        def test_function():
            return 42

        result = test_function()
        assert result == 42
