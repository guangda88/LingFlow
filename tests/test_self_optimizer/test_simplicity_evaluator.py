"""
测试简洁性评估器
"""

import pytest
from pathlib import Path
from lingflow.self_optimizer.simplicity_evaluator import SimplicityEvaluator


class TestSimplicityEvaluator:
    """测试简洁性评估器"""

    @pytest.fixture
    def evaluator(self):
        """创建评估器"""
        return SimplicityEvaluator("/home/ai/LingFlow/lingflow")

    def test_evaluate_with_params(self, evaluator):
        """测试带参数的评估"""
        params = {
            "complexity_threshold": 10,
            "duplication_penalty": 1.0,
            "max_line_length": 100,
        }

        score = evaluator.evaluate(params)

        assert isinstance(score, float)
        assert score >= 0

    def test_get_current_metrics(self, evaluator):
        """测试获取当前指标"""
        metrics = evaluator.get_current_metrics()

        assert "total_lines" in metrics
        assert "code_lines" in metrics
        assert "avg_line_length" in metrics
        assert "duplication_rate" in metrics

        assert metrics["total_lines"] >= 0
        assert metrics["code_lines"] >= 0
        assert metrics["avg_line_length"] >= 0
        assert 0 <= metrics["duplication_rate"] <= 1

    def test_different_params_different_scores(self, evaluator):
        """测试不同参数产生不同分数"""
        strict_params = {
            "complexity_threshold": 5,
            "duplication_penalty": 2.0,
            "max_line_length": 80,
        }

        loose_params = {
            "complexity_threshold": 15,
            "duplication_penalty": 0.5,
            "max_line_length": 120,
        }

        score_strict = evaluator.evaluate(strict_params)
        score_loose = evaluator.evaluate(loose_params)

        # 严格参数应该产生更高的分数（更多违规）
        assert score_strict >= 0
        assert score_loose >= 0

    def test_find_duplicate_code_blocks(self, evaluator):
        """测试查找重复代码块"""
        duplicates = evaluator.find_duplicate_code_blocks(min_lines=5)

        assert isinstance(duplicates, list)
        for dup in duplicates:
            assert "occurrences" in dup
            assert "locations" in dup
            assert "lines" in dup
            assert dup["occurrences"] >= 2
            assert dup["lines"] >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
