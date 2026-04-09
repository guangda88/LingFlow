"""
测试结构评估器
"""

from pathlib import Path

import pytest

from lingflow.self_optimizer.evaluator import StructureEvaluator


class TestStructureEvaluator:
    """测试结构评估器"""

    @pytest.fixture
    def evaluator(self):
        """创建评估器"""
        return StructureEvaluator("/home/ai/LingFlow/lingflow")

    def test_evaluate_with_params(self, evaluator):
        """测试带参数的评估"""
        params = {
            "max_class_size": 200,
            "max_method_count": 15,
            "max_complexity": 10,
        }

        score = evaluator.evaluate(params)

        assert isinstance(score, float)
        assert score >= 0

    def test_get_current_metrics(self, evaluator):
        """测试获取当前指标"""
        metrics = evaluator.get_current_metrics()

        assert "structure_violations" in metrics
        assert "avg_complexity" in metrics
        assert "avg_class_size" in metrics

        assert metrics["structure_violations"] >= 0
        assert metrics["avg_complexity"] >= 0
        assert metrics["avg_class_size"] >= 0

    def test_different_params_different_scores(self, evaluator):
        """测试不同参数产生不同分数"""
        strict_params = {
            "max_class_size": 100,
            "max_complexity": 5,
        }

        loose_params = {
            "max_class_size": 500,
            "max_complexity": 20,
        }

        score_strict = evaluator.evaluate(strict_params)
        score_loose = evaluator.evaluate(loose_params)

        # 严格参数应该产生更高的违规分数
        assert score_strict >= score_loose


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
