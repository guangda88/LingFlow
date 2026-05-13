"""
测试优化器
"""

import time

import pytest

from lingflow.self_optimizer.optimizer import OptimizationRequest, SynchronousOptimizer


class TestSynchronousOptimizer:
    """测试同步优化器"""

    @pytest.fixture
    def optimizer(self):
        """创建优化器"""
        return SynchronousOptimizer()

    @pytest.fixture
    def opt_request(self):
        """创建优化请求"""
        return OptimizationRequest(
            target="/home/ai/lingflow/lingflow",
            goal="structure",
            params={},
            config={
                "max_experiments": 3,  # 只运行3次实验（测试用）
                "time_budget": 60,
            },
        )

    def test_optimize(self, optimizer, opt_request):
        """测试优化"""
        result = optimizer.optimize(opt_request)

        assert result.success is True
        assert result.best_params is not None
        assert len(result.best_params) > 0
        assert result.best_score >= 0
        assert result.experiments > 0
        assert result.duration >= 0

    def test_best_params_structure(self, optimizer, opt_request):
        """测试最佳参数结构"""
        result = optimizer.optimize(opt_request)

        # 检查必需的参数
        expected_keys = [
            "max_class_size",
            "max_method_count",
            "max_complexity",
        ]

        for key in expected_keys:
            assert key in result.best_params
            assert isinstance(result.best_params[key], (int, float))


class TestOptimizationRequest:
    """测试优化请求"""

    def test_create_request(self):
        """测试创建请求"""
        request = OptimizationRequest(target=".", goal="structure", params={}, config={})

        assert request.target == "."
        assert request.goal == "structure"
        assert isinstance(request.params, dict)
        assert isinstance(request.config, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
