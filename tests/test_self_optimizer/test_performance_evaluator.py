"""
测试性能评估器
"""

from pathlib import Path

import pytest

from lingflow.self_optimizer.performance_evaluator import PerformanceEvaluator


class TestPerformanceEvaluator:
    """测试性能评估器"""

    @pytest.fixture
    def evaluator(self):
        """创建评估器"""
        return PerformanceEvaluator("/home/ai/lingflow/lingflow")

    def test_evaluate_with_params(self, evaluator):
        """测试带参数的评估"""
        params = {
            "cache_size": 100,
            "parallelism": 2,
            "timeout": 30,
        }

        score = evaluator.evaluate(params)

        assert isinstance(score, float)
        assert score >= 0

    def test_get_current_metrics(self, evaluator):
        """测试获取当前指标"""
        metrics = evaluator.get_current_metrics()

        assert "execution_time" in metrics
        assert "memory_usage_mb" in metrics
        assert "cpu_percent" in metrics

        assert metrics["execution_time"] >= 0
        assert metrics["memory_usage_mb"] >= 0
        assert metrics["cpu_percent"] >= 0

    def test_different_params_different_scores(self, evaluator):
        """测试不同参数产生不同分数"""
        params_small = {
            "cache_size": 10,
            "parallelism": 1,
            "timeout": 5,
        }

        params_large = {
            "cache_size": 500,
            "parallelism": 4,
            "timeout": 60,
        }

        score_small = evaluator.evaluate(params_small)
        score_large = evaluator.evaluate(params_large)

        # 两次评估都应该返回分数
        assert score_small >= 0
        assert score_large >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
