"""
API速率限制控制器
实现请求间隔、智能重试、并发控制
"""

import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    requests_per_second: float = 2.0  # 每秒请求数
    requests_per_minute: float = 100.0  # 每分钟请求数
    max_retries: int = 3  # 最大重试次数
    base_delay: float = 1.0  # 基础延迟（秒）
    max_delay: float = 60.0  # 最大延迟（秒）
    jitter: bool = True  # 是否添加随机抖动
    exponential_backoff: bool = True  # 是否使用指数退避


class RateLimiter:
    """速率限制器 - 控制请求频率"""

    # 最大历史记录数，防止内存泄漏
    MAX_HISTORY_SIZE = 1000

    def __init__(self, config: RateLimitConfig = None):
        """
        Args:
            config: 速率限制配置
        """
        self.config = config or RateLimitConfig()

        # 请求时间记录
        self.request_times = []
        self.lock = threading.Lock()

        # 计算最小间隔
        self.min_interval = 1.0 / self.config.requests_per_second

    def acquire(self):
        """获取请求许可（阻塞直到可以请求）"""
        with self.lock:
            now = time.time()

            # 清理旧记录（超过1秒的）
            self.request_times = [t for t in self.request_times if now - t < 1.0]

            # 防止内存泄漏 - 限制历史记录大小
            if len(self.request_times) > self.MAX_HISTORY_SIZE:
                self.request_times = self.request_times[-self.MAX_HISTORY_SIZE :]

            # 如果达到速率限制，等待
            if len(self.request_times) >= self.config.requests_per_second:
                sleep_time = self.min_interval - (now - self.request_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            # 记录本次请求时间
            self.request_times.append(time.time())

    async def acquire_async(self):
        """异步获取请求许可"""
        import asyncio

        with self.lock:
            now = time.time()
            self.request_times = [t for t in self.request_times if now - t < 1.0]

            # 防止内存泄漏 - 限制历史记录大小
            if len(self.request_times) > self.MAX_HISTORY_SIZE:
                self.request_times = self.request_times[-self.MAX_HISTORY_SIZE :]

            if len(self.request_times) >= self.config.requests_per_second:
                sleep_time = self.min_interval - (now - self.request_times[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            self.request_times.append(time.time())


class SmartRetry:
    """智能重试器 - 处理API错误和重试"""

    def __init__(self, config: RateLimitConfig = None):
        """
        Args:
            config: 重试配置
        """
        self.config = config or RateLimitConfig()

        # 错误统计
        self.error_count = 0
        self.success_count = 0
        self.last_error_time = None

    def execute(self, func: Callable, *args, on_retry: Optional[Callable] = None, **kwargs) -> Any:
        """执行函数，支持智能重试

        Args:
            func: 要执行的函数
            *args: 函数参数
            on_retry: 重试时的回调函数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 所有重试失败后的异常
        """
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                result = func(*args, **kwargs)

                # 成功，记录统计
                self.success_count += 1
                return result

            except Exception as e:
                last_exception = e
                self.error_count += 1
                self.last_error_time = datetime.now()

                # 检查是否应该重试
                if not self._should_retry(e, attempt):
                    raise

                # 计算延迟时间
                delay = self._calculate_delay(attempt)

                # 调用回调
                if on_retry:
                    on_retry(attempt, e, delay)

                # 等待后重试
                time.sleep(delay)

        # 所有重试都失败
        raise last_exception

    async def execute_async(self, func: Callable, *args, on_retry: Optional[Callable] = None, **kwargs) -> Any:
        """异步执行函数，支持智能重试"""
        import asyncio

        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                result = await func(*args, **kwargs)
                self.success_count += 1
                return result

            except Exception as e:
                last_exception = e
                self.error_count += 1
                self.last_error_time = datetime.now()

                if not self._should_retry(e, attempt):
                    raise

                delay = self._calculate_delay(attempt)

                if on_retry:
                    on_retry(attempt, e, delay)

                await asyncio.sleep(delay)

        raise last_exception

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        # 达到最大重试次数
        if attempt >= self.config.max_retries - 1:
            return False

        # 检查错误类型
        error_str = str(error).lower()

        # 速率限制错误（429）
        if "429" in error_str or "rate limit" in error_str:
            return True

        # 服务器错误（5xx）
        if "500" in error_str or "502" in error_str or "503" in error_str:
            return True

        # 网络错误
        if "connection" in error_str or "timeout" in error_str:
            return True

        return False

    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        if self.config.exponential_backoff:
            # 指数退避
            delay = self.config.base_delay * (2**attempt)
        else:
            # 固定延迟
            delay = self.config.base_delay

        # 限制最大延迟
        delay = min(delay, self.config.max_delay)

        # 添加随机抖动（避免雷群效应）
        if self.config.jitter:
            jitter = random.uniform(0.5, 1.5)
            delay *= jitter

        return delay

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "error_count": self.error_count,
            "success_count": self.success_count,
            "error_rate": self.error_count / max(1, self.error_count + self.success_count),
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class ConcurrencyController:
    """并发控制器 - 限制同时运行的请求数"""

    def __init__(self, max_concurrent: int = 5):
        """
        Args:
            max_concurrent: 最大并发数
        """
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(max_concurrent)
        self.active_count = 0
        self.lock = threading.Lock()

    def acquire(self):
        """获取并发许可"""
        self.semaphore.acquire()
        with self.lock:
            self.active_count += 1

    def release(self):
        """释放并发许可"""
        with self.lock:
            self.active_count -= 1
        self.semaphore.release()

    def get_active_count(self) -> int:
        """获取当前活跃请求数"""
        return self.active_count


class APIClient:
    """整合的API客户端 - 同时控制速率、重试、并发"""

    def __init__(self, rate_limit_config: RateLimitConfig = None, max_concurrent: int = 5):
        """
        Args:
            rate_limit_config: 速率限制配置
            max_concurrent: 最大并发数
        """
        self.rate_limiter = RateLimiter(rate_limit_config)
        self.retry_handler = SmartRetry(rate_limit_config)
        self.concurrency_controller = ConcurrencyController(max_concurrent)

    def request(self, func: Callable, *args, **kwargs) -> Any:
        """执行API请求（整合所有控制）"""
        # 1. 获取并发许可
        self.concurrency_controller.acquire()

        try:
            # 2. 获取速率许可
            self.rate_limiter.acquire()

            # 3. 执行请求（带智能重试）
            def retry_callback(attempt, error, delay):
                print(f"⚠️  第 {attempt + 1} 次重试，错误: {error}，等待 {delay:.1f}秒...")

            result = self.retry_handler.execute(func, *args, on_retry=retry_callback, **kwargs)

            return result

        finally:
            # 4. 释放并发许可
            self.concurrency_controller.release()

    async def request_async(self, func: Callable, *args, **kwargs) -> Any:
        """异步执行API请求"""
        self.concurrency_controller.acquire()

        try:
            await self.rate_limiter.acquire_async()

            async def retry_callback(attempt, error, delay):
                print(f"⚠️  第 {attempt + 1} 次重试，错误: {error}，等待 {delay:.1f}秒...")

            result = await self.retry_handler.execute_async(func, *args, on_retry=retry_callback, **kwargs)

            return result

        finally:
            self.concurrency_controller.release()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.retry_handler.get_stats(),
            "active_requests": self.concurrency_controller.get_active_count(),
            "max_concurrent": self.concurrency_controller.max_concurrent,
        }


# ============== 使用示例 ==============


def example_rate_limiter():  # pragma: no cover
    """速率限制器示例"""
    print("\n=== 速率限制器示例 ===\n")

    config = RateLimitConfig(requests_per_second=2.0)
    limiter = RateLimiter(config)

    def make_request(request_id):
        limiter.acquire()
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{now}] 请求 {request_id}")

    # 发送5个请求
    for i in range(5):
        make_request(i)


def example_smart_retry():  # pragma: no cover
    """智能重试示例"""
    print("\n=== 智能重试示例 ===\n")

    config = RateLimitConfig(max_retries=3, base_delay=0.5, exponential_backoff=True)
    retry_handler = SmartRetry(config)

    # 模拟可能失败的API调用
    call_count = [0]

    def unreliable_api_call():
        call_count[0] += 1
        print(f"  API调用 #{call_count[0]}")

        if call_count[0] < 3:
            raise Exception("429 Rate Limit Error")

        return "成功!"

    try:
        result = retry_handler.execute(
            unreliable_api_call, on_retry=lambda attempt, error, delay: print(f"    重试 #{attempt + 1}，延迟 {delay:.1f}秒")
        )
        print(f"\n✓ 最终结果: {result}")
    except Exception as e:
        print(f"\n✗ 所有重试失败: {e}")


def example_concurrency_control():  # pragma: no cover
    """并发控制示例"""
    print("\n=== 并发控制示例 ===\n")

    import threading

    controller = ConcurrencyController(max_concurrent=2)

    def worker(worker_id):
        controller.acquire()
        print(f"Worker {worker_id} 开始工作 (活跃: {controller.get_active_count()})")
        time.sleep(1)
        print(f"Worker {worker_id} 完成")
        controller.release()

    # 启动5个worker
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(0.2)  # 错开启动时间

    for t in threads:
        t.join()


def example_integrated_client():  # pragma: no cover
    """整合的API客户端示例"""
    print("\n=== 整合API客户端示例 ===\n")

    config = RateLimitConfig(requests_per_second=2.0, max_retries=3, base_delay=0.5)

    client = APIClient(config, max_concurrent=3)

    # 模拟API调用
    call_count = [0]

    def api_call(request_id):
        call_count[0] += 1
        print(f"📡 请求 {request_id}")

        # 模拟偶尔的速率限制
        if call_count[0] in [2, 5]:
            raise Exception("429 Rate Limit Error")

        time.sleep(0.5)  # 模拟网络延迟
        return f"响应 {request_id}"

    # 发送多个请求
    import threading

    def worker(request_id):
        try:
            result = client.request(api_call, request_id)
            print(f"✓ {result}")
        except Exception as e:
            print(f"✗ 请求 {request_id} 失败: {e}")

    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 显示统计
    stats = client.get_stats()
    print("\n📊 统计:")
    print(f"  成功: {stats['success_count']}")
    print(f"  失败: {stats['error_count']}")
    print(f"  错误率: {stats['error_rate']:.1%}")


if __name__ == "__main__":  # pragma: no cover
    print("API速率限制控制演示")
    print("=" * 50)

    example_rate_limiter()
    time.sleep(1)

    example_smart_retry()
    time.sleep(1)

    example_concurrency_control()
    time.sleep(1)

    example_integrated_client()

    print("\n✅ 演示完成！")
