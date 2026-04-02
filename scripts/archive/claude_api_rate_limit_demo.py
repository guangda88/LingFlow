#!/usr/bin/env python3
"""
实际案例：解决Claude API速率限制问题

展示如何在真实项目中使用速率限制控制
"""

import time
from typing import List, Dict


def example_claude_api_with_rate_limit():
    """示例：带速率限制的Claude API调用"""
    print("\n=== Claude API速率限制示例 ===\n")

    from lingflow.utils.rate_limiter import APIClient, RateLimitConfig

    # 配置：Claude API建议保守设置
    config = RateLimitConfig(
        requests_per_second=0.5,  # 每2秒1个请求（保守）
        max_retries=5,              # 最多重试5次
        base_delay=2.0,             # 基础延迟2秒
        max_delay=60.0,             # 最大延迟60秒
        exponential_backoff=True,   # 指数退避
        jitter=True,                # 随机抖动
    )

    client = APIClient(
        rate_limit_config=config,
        max_concurrent=2            # 最多2个并发（非常保守）
    )

    # 模拟Claude API调用
    call_count = [0]

    def mock_claude_api(prompt: str) -> str:
        """模拟Claude API调用"""
        call_count[0] += 1

        # 模拟API延迟
        time.sleep(0.5)

        # 模拟偶尔的429错误（前3次调用）
        if call_count[0] <= 3:
            raise Exception("429 Rate Limit Error - 您的账户已达到速率限制")

        return f"Claude响应: {prompt[:20]}..."

    # 批量处理提示词
    prompts = [
        "Hello Claude, how are you?",
        "Explain quantum computing",
        "Write a Python function",
        "What is machine learning?",
        "Generate a story",
    ]

    print(f"📝 处理 {len(prompts)} 个提示词...\n")

    results = []

    def process_prompt(idx: int, prompt: str):
        try:
            result = client.request(mock_claude_api, prompt)
            results.append((idx, result))
            print(f"✓ [{idx}] {prompt[:30]}")
        except Exception as e:
            print(f"✗ [{idx}] 失败: {e}")

    # 串行处理（保守）
    for i, prompt in enumerate(prompts):
        process_prompt(i, prompt)

    print(f"\n📊 结果统计:")
    print(f"  成功: {len(results)}/{len(prompts)}")
    print(f"  总调用次数: {call_count[0]}")

    # 显示统计
    stats = client.get_stats()
    print(f"\n📈 详细统计:")
    print(f"  成功次数: {stats['success_count']}")
    print(f"  失败次数: {stats['error_count']}")
    print(f"  错误率: {stats['error_rate']:.1%}")


def example_batch_requests():
    """示例：批量API请求处理"""
    print("\n=== 批量API请求示例 ===\n")

    from lingflow.utils.rate_limiter import APIClient, RateLimitConfig
    import threading

    # 配置：中等激进
    config = RateLimitConfig(
        requests_per_second=5.0,  # 每秒5个请求
        max_retries=3,
        base_delay=0.5,
    )

    client = APIClient(
        rate_limit_config=config,
        max_concurrent=10
    )

    # 模拟API端点
    endpoints = [
        "https://api.example.com/users",
        "https://api.example.com/posts",
        "https://api.example.com/comments",
        "https://api.example.com/likes",
        "https://api.example.com/shares",
    ]

    print(f"🌐 并发访问 {len(endpoints)} 个端点...\n")

    def fetch_endpoint(endpoint: str):
        """获取端点数据"""
        time.sleep(0.3)  # 模拟网络延迟

        # 模拟部分429错误
        if "posts" in endpoint or "comments" in endpoint:
            raise Exception("429 Rate Limit Error")

        return f"数据来自 {endpoint}"

    # 并发处理
    threads = []
    results = {}

    def worker(endpoint: str):
        try:
            result = client.request(fetch_endpoint, endpoint)
            results[endpoint] = result
            print(f"✓ {endpoint}")
        except Exception as e:
            print(f"✗ {endpoint}: {e}")

    start_time = time.time()

    for endpoint in endpoints:
        t = threading.Thread(target=worker, args=(endpoint,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    print(f"\n⏱️  总耗时: {elapsed:.1f}秒")
    print(f"✓ 成功: {len(results)}/{len(endpoints)}")


def example_progressive_backoff():
    """示例：渐进式退避策略"""
    print("\n=== 渐进式退避策略示例 ===\n")

    from lingflow.utils.rate_limiter import SmartRetry, RateLimitConfig

    # 配置：激进退避
    config = RateLimitConfig(
        max_retries=5,
        base_delay=1.0,
        max_delay=30.0,
        exponential_backoff=True,
        jitter=True,
    )

    retry_handler = SmartRetry(config)

    call_count = [0]

    def failing_api():
        """模拟失败的API"""
        call_count[0] += 1
        print(f"  🔴 API调用 #{call_count[0]}")

        # 前3次失败
        if call_count[0] <= 3:
            raise Exception("429 Rate Limit Error")

        return "成功!"

    print("尝试调用失败的API...\n")

    try:
        result = retry_handler.execute(
            failing_api,
            on_retry=lambda attempt, error, delay:
                print(f"    ⏳ {delay:.1f}秒后重试 (尝试 {attempt + 1}/{retry_handler.config.max_retries})")
        )
        print(f"\n✓ {result}")
        print(f"  总尝试次数: {call_count[0]}")

    except Exception as e:
        print(f"\n✗ 所有重试失败: {e}")


def example_adaptive_rate_limiting():
    """示例：自适应速率限制"""
    print("\n=== 自适应速率限制示例 ===\n")

    from lingflow.utils.rate_limiter import APIClient, RateLimitConfig

    # 根据错误率动态调整
    error_rate_threshold = 0.1  # 10%错误率

    # 初始配置：激进
    config = RateLimitConfig(
        requests_per_second=10.0,
        max_retries=3,
    )

    client = APIClient(config, max_concurrent=5)

    call_count = [0]
    error_count = [0]

    def adaptive_api_call():
        """模拟可能失败的API"""
        call_count[0] += 1

        # 模拟30%的失败率
        if call_count[0] % 10 in [1, 4, 7]:
            error_count[0] += 1
            raise Exception("429 Rate Limit Error")

        time.sleep(0.1)
        return f"响应 #{call_count[0]}"

    print("📊 发送50个请求（自适应速率限制）...\n")

    results = []

    for i in range(50):
        try:
            result = client.request(adaptive_api_call)
            results.append(result)

            # 每10个请求检查一次错误率
            if (i + 1) % 10 == 0:
                stats = client.get_stats()
                error_rate = stats['error_rate']

                print(f"  进度: {i+1}/50, 错误率: {error_rate:.1%}")

                # 如果错误率过高，降低速率
                if error_rate > error_rate_threshold:
                    print(f"    ⚠️  错误率过高，降低速率")
                    # 这里可以动态调整配置
                    # client.rate_limiter.config.requests_per_second /= 2

        except Exception as e:
            pass

    print(f"\n📈 最终统计:")
    stats = client.get_stats()
    print(f"  成功: {stats['success_count']}")
    print(f"  失败: {stats['error_count']}")
    print(f"  错误率: {stats['error_rate']:.1%}")


def example_real_world_scenario():
    """示例：真实世界场景"""
    print("\n=== 真实场景：批量文档处理 ===\n")

    from lingflow.utils.rate_limiter import APIClient, RateLimitConfig

    # 真实配置（Claude API推荐）
    config = RateLimitConfig(
        requests_per_second=0.5,  # 每2秒1个请求
        max_retries=5,
        base_delay=2.0,
        max_delay=120.0,
    )

    client = APIClient(config, max_concurrent=1)

    # 模拟文档
    documents = [
        "文档1：LingFlow使用指南",
        "文档2：API参考手册",
        "文档3：最佳实践",
        "文档4：故障排除",
        "文档5：性能优化",
    ]

    print(f"📄 处理 {len(documents)} 个文档（使用Claude API）...\n")

    def process_with_claude(doc: str) -> str:
        """使用Claude处理文档"""
        print(f"  📝 处理: {doc}")

        # 模拟Claude API调用
        time.sleep(1.5)  # Claude API较慢

        # 20%的请求被限流
        import random
        if random.random() < 0.2:
            raise Exception("429 Rate Limit Error")

        return f"已处理: {doc}"

    results = []
    total_time = 0

    for doc in documents:
        start = time.time()

        try:
            result = client.request(process_with_claude, doc)
            results.append(result)
            elapsed = time.time() - start
            total_time += elapsed
            print(f"    ✓ 完成 (耗时: {elapsed:.1f}秒)\n")
        except Exception as e:
            print(f"    ✗ 失败: {e}\n")

    print(f"📊 处理结果:")
    print(f"  成功: {len(results)}/{len(documents)}")
    print(f"  总耗时: {total_time:.1f}秒")
    print(f"  平均耗时: {total_time/len(documents):.1f}秒/文档")


def main():
    """主函数"""
    print("=" * 70)
    print(" API速率限制控制 - 实际案例演示 ".center(70))
    print("=" * 70)

    try:
        example_claude_api_with_rate_limit()
        time.sleep(1)

        example_batch_requests()
        time.sleep(1)

        example_progressive_backoff()
        time.sleep(1)

        example_adaptive_rate_limiting()
        time.sleep(1)

        example_real_world_scenario()

        print("\n" + "=" * 70)
        print(" ✅ 所有案例演示完成 ".center(70))
        print("=" * 70 + "\n")

        print("💡 提示:")
        print("  1. 根据您的API选择合适的配置")
        print("  2. 保守设置适合生产环境")
        print("  3. 激进设置仅用于测试")
        print("  4. 监控错误率并动态调整\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  演示被中断")
    except Exception as e:
        print(f"\n\n✗ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
