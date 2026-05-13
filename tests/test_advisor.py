"""Tests for lingflow.self_optimizer.advisor"""

import os
import tempfile
from pathlib import Path

import pytest

from lingflow.self_optimizer.advisor import OptimizationAdvisor
from lingflow.self_optimizer.optimizer import OptimizationResult


@pytest.fixture
def advisor():
    return OptimizationAdvisor()


@pytest.fixture
def sample_result():
    return OptimizationResult(
        success=True,
        best_params={
            "max_class_size": 200,
            "max_complexity": 10,
            "max_method_count": 15,
        },
        best_score=5.0,
        experiments=20,
        duration=45.2,
    )


@pytest.fixture
def sample_result_with_history():
    return OptimizationResult(
        success=True,
        best_params={"max_class_size": 150},
        best_score=6.0,
        experiments=15,
        duration=30.0,
        history=[
            {"experiment_id": 1, "params": {"max_class_size": 200}, "score": 4.0},
            {"experiment_id": 2, "params": {"max_class_size": 150}, "score": 6.0},
            {"experiment_id": 3, "params": {"max_class_size": 100, "extra": "x", "more": "y", "last": "z"}, "score": 5.5},
        ]
        + [{"experiment_id": i, "params": {"k": i}, "score": float(i)} for i in range(4, 14)],
    )


class TestOptimizationAdvisorInit:
    def test_goal_names(self, advisor):
        assert advisor.goal_names["structure"] == "结构优化"
        assert advisor.goal_names["performance"] == "性能优化"
        assert advisor.goal_names["simplicity"] == "简洁优化"


class TestGenerateReportStructure:
    def test_report_header(self, advisor, sample_result):
        metrics = {"review_score": 75, "structure_violations": 5}
        report = advisor.generate_report("structure", "/path", metrics, sample_result)
        assert "# lingflow 自优化建议报告" in report
        assert "结构优化" in report

    def test_structure_metrics(self, advisor, sample_result):
        metrics = {
            "review_score": 75,
            "structure_violations": 3,
            "avg_class_size": 120.5,
            "avg_method_count": 8.3,
            "avg_complexity": 6.2,
            "large_classes_count": 2,
        }
        report = advisor.generate_report("structure", "/path", metrics, sample_result)
        assert "结构违规: 3处" in report
        assert "120行" in report
        assert "8.3个" in report
        assert "6.2" in report
        assert "2" in report

    def test_structure_issues(self, advisor, sample_result):
        metrics = {
            "large_classes_count": 3,
            "complex_methods_count": 5,
            "structure_violations": 2,
        }
        report = advisor.generate_report("structure", "/path", metrics, sample_result)
        assert "3 个大型类" in report
        assert "5 个复杂方法" in report
        assert "2 处" in report

    def test_no_issues(self, advisor, sample_result):
        report = advisor.generate_report("structure", "/path", {}, sample_result)
        assert "未发现严重问题" in report


class TestGenerateReportPerformance:
    def test_performance_metrics(self, advisor, sample_result):
        metrics = {
            "execution_time": 2.5,
            "memory_usage_mb": 150.0,
            "response_time_ms": 300,
        }
        report = advisor.generate_report("performance", "/path", metrics, sample_result)
        assert "2.50秒" in report
        assert "150.0MB" in report
        assert "300ms" in report

    def test_performance_issues(self, advisor, sample_result):
        metrics = {
            "execution_time": 3.0,
            "memory_usage_mb": 200,
        }
        report = advisor.generate_report("performance", "/path", metrics, sample_result)
        assert "执行时间过长" in report
        assert "内存占用较高" in report


class TestGenerateReportSimplicity:
    def test_simplicity_metrics(self, advisor, sample_result):
        metrics = {
            "total_lines": 5000,
            "duplication_rate": 0.12,
            "avg_line_length": 45,
        }
        report = advisor.generate_report("simplicity", "/path", metrics, sample_result)
        assert "5000" in report
        assert "12.0%" in report
        assert "45" in report

    def test_simplicity_issues(self, advisor, sample_result):
        metrics = {
            "duplication_rate": 0.08,
            "avg_complexity": 15,
        }
        report = advisor.generate_report("simplicity", "/path", metrics, sample_result)
        assert "8.0%" in report
        assert "15.0" in report


class TestGenerateReportRecommendations:
    def test_best_params_yaml(self, advisor, sample_result):
        report = advisor.generate_report("structure", "/path", {}, sample_result)
        assert "max_class_size" in report
        assert "max_complexity" in report

    def test_structure_improvement(self, advisor, sample_result):
        metrics = {"structure_violations": 10, "avg_class_size": 300}
        report = advisor.generate_report("structure", "/path", metrics, sample_result)
        assert "10" in report

    def test_performance_improvement(self, advisor, sample_result):
        metrics = {"execution_time": 5.0}
        report = advisor.generate_report("performance", "/path", metrics, sample_result)
        assert "3.50s" in report
        assert "30% 改进" in report

    def test_experiment_stats(self, advisor, sample_result):
        report = advisor.generate_report("structure", "/path", {}, sample_result)
        assert "20 次实验" in report
        assert "45.2 秒" in report


class TestGenerateReportComparison:
    def test_comparison_table(self, advisor, sample_result):
        metrics = {
            "current_params": {
                "max_class_size": 300,
                "max_complexity": 15,
            }
        }
        report = advisor.generate_report("structure", "/path", metrics, sample_result)
        assert "| 参数 | 当前值 | 建议值 | 说明 |" in report
        assert "建议↓" in report

    def test_comparison_keep(self, advisor, sample_result):
        metrics = {
            "current_params": {
                "max_class_size": 200,
                "max_complexity": 10,
                "max_method_count": 15,
            }
        }
        report = advisor.generate_report("structure", "/path", metrics, sample_result)
        assert "保持" in report


class TestGenerateReportImplementation:
    def test_implementation_steps(self, advisor, sample_result):
        report = advisor.generate_report("structure", "/path", {}, sample_result)
        assert "## 实施步骤" in report
        assert "自动应用" in report
        assert "手动应用" in report
        assert "配置文件" in report


class TestGenerateReportHistory:
    def test_with_history(self, advisor, sample_result_with_history):
        report = advisor.generate_report("structure", "/path", {}, sample_result_with_history)
        assert "## 优化历史" in report
        assert "| 实验 | 参数 | 分数 |" in report

    def test_without_history(self, advisor, sample_result):
        sample_result.history = None
        report = advisor.generate_report("structure", "/path", {}, sample_result)
        assert "## 优化历史" not in report

    def test_long_history_truncated(self, advisor):
        result = OptimizationResult(
            success=True,
            best_params={"k": 1},
            best_score=8.0,
            experiments=15,
            duration=20.0,
            history=[{"experiment_id": i, "params": {"k": i}, "score": float(i)} for i in range(15)],
        )
        report = advisor.generate_report("structure", "/path", {}, result)
        assert "15 次实验" in report


class TestSaveReport:
    def test_save_to_specified_path(self, advisor):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.md")
            result = advisor.save_report("# Test Report", path)
            assert result == path
            assert Path(path).read_text() == "# Test Report"

    def test_save_auto_path(self, advisor):
        result = advisor.save_report("# Test Report")
        assert result.startswith("LINGFLOW_OPTIMIZATION_REPORT_")
        assert result.endswith(".md")
        Path(result).unlink(missing_ok=True)


class TestPrintSummary:
    def test_print_summary(self, advisor, sample_result, capsys):
        metrics = {"structure_violations": 10}
        advisor.print_summary(sample_result, metrics)
        captured = capsys.readouterr()
        assert "20" in captured.out
        assert "5.00" in captured.out

    def test_print_summary_no_violations(self, advisor, sample_result, capsys):
        advisor.print_summary(sample_result, {})
        captured = capsys.readouterr()
        assert "预期改进" not in captured.out


class TestGoalNameFallback:
    def test_unknown_goal(self, advisor, sample_result):
        report = advisor.generate_report("custom_goal", "/path", {}, sample_result)
        assert "custom_goal" in report
