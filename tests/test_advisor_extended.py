"""Extended tests for lingflow.self_optimizer.advisor - additional coverage"""

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
def perf_result():
    return OptimizationResult(
        success=True,
        best_params={"timeout": 30.0, "max_retries": 3},
        best_score=7.5,
        experiments=10,
        duration=20.0,
    )


@pytest.fixture
def simple_result():
    return OptimizationResult(
        success=True,
        best_params={"max_complexity": 10},
        best_score=4.0,
        experiments=5,
        duration=10.0,
    )


class TestGoalNameResolution:
    def test_structure(self, advisor):
        assert advisor._goal_name("structure") == "结构优化"

    def test_performance(self, advisor):
        assert advisor._goal_name("performance") == "性能优化"

    def test_simplicity(self, advisor):
        assert advisor._goal_name("simplicity") == "简洁优化"

    def test_unknown_falls_back(self, advisor):
        assert advisor._goal_name("unknown") == "unknown"


class TestFormatCurrentMetricsStructure:
    def test_all_structure_metrics(self, advisor, simple_result):
        metrics = {
            "review_score": 80,
            "structure_violations": 5,
            "avg_class_size": 150.0,
            "avg_method_count": 12.0,
            "avg_complexity": 8.5,
            "large_classes_count": 3,
        }
        report = advisor.generate_report("structure", "/path", metrics, simple_result)
        assert "80/100" in report
        assert "5处" in report
        assert "150行" in report
        assert "12.0个" in report
        assert "8.5" in report
        assert "3" in report

    def test_no_review_score(self, advisor, simple_result):
        report = advisor.generate_report("structure", "/path", {}, simple_result)
        assert "整体得分" not in report


class TestFormatCurrentMetricsPerformance:
    def test_all_performance_metrics(self, advisor, perf_result):
        metrics = {
            "execution_time": 3.5,
            "memory_usage_mb": 200.0,
            "response_time_ms": 500,
        }
        report = advisor.generate_report("performance", "/path", metrics, perf_result)
        assert "3.50秒" in report
        assert "200.0MB" in report
        assert "500ms" in report

    def test_performance_no_issues(self, advisor, perf_result):
        metrics = {"execution_time": 0.5, "memory_usage_mb": 50}
        report = advisor.generate_report("performance", "/path", metrics, perf_result)
        assert "执行时间过长" not in report
        assert "内存占用较高" not in report


class TestFormatCurrentMetricsSimplicity:
    def test_all_simplicity_metrics(self, advisor):
        result = OptimizationResult(
            success=True, best_params={"k": 1},
            best_score=5.0, experiments=5, duration=10.0
        )
        metrics = {
            "total_lines": 10000,
            "duplication_rate": 0.15,
            "avg_line_length": 60,
        }
        report = advisor.generate_report("simplicity", "/path", metrics, result)
        assert "10000" in report
        assert "15.0%" in report
        assert "60" in report


class TestFormatIssues:
    def test_structure_no_issues(self, advisor, simple_result):
        report = advisor.generate_report("structure", "/path", {}, simple_result)
        assert "未发现严重问题" in report

    def test_performance_no_issues(self, advisor, perf_result):
        report = advisor.generate_report("performance", "/path", {}, perf_result)
        assert "未发现严重问题" in report

    def test_simplicity_no_issues(self, advisor):
        result = OptimizationResult(
            success=True, best_params={"k": 1},
            best_score=5.0, experiments=5, duration=10.0
        )
        report = advisor.generate_report("simplicity", "/path", {}, result)
        assert "未发现严重问题" in report


class TestFormatRecommendationsParams:
    def test_float_params(self, advisor):
        result = OptimizationResult(
            success=True, best_params={"ratio": 0.75},
            best_score=5.0, experiments=5, duration=10.0
        )
        report = advisor.generate_report("structure", "/path", {}, result)
        assert "0.75" in report

    def test_int_params(self, advisor):
        result = OptimizationResult(
            success=True, best_params={"count": 10},
            best_score=5.0, experiments=5, duration=10.0
        )
        report = advisor.generate_report("structure", "/path", {}, result)
        assert "count" in report


class TestFormatComparisonValues:
    def test_float_current_vs_recommended(self, advisor, simple_result):
        metrics = {"current_params": {"max_complexity": 15.0}}
        report = advisor.generate_report("structure", "/path", metrics, simple_result)
        assert "15.00" in report

    def test_default_current(self, advisor, simple_result):
        report = advisor.generate_report("structure", "/path", {}, simple_result)
        assert "默认" in report

    def test_increase_indicator(self, advisor):
        result = OptimizationResult(
            success=True, best_params={"timeout": 60},
            best_score=5.0, experiments=5, duration=10.0
        )
        metrics = {"current_params": {"timeout": 30}}
        report = advisor.generate_report("structure", "/path", metrics, result)
        assert "建议↑" in report


class TestFormatImplementationSteps:
    def test_all_options_present(self, advisor, simple_result):
        report = advisor.generate_report("structure", "/path", {}, simple_result)
        assert "选项 1: 自动应用" in report
        assert "选项 2: 手动应用" in report
        assert "选项 3: 生成配置文件" in report


class TestSaveReport:
    def test_save_to_file(self, advisor):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.md")
            result = advisor.save_report("# Report", path)
            assert Path(path).read_text() == "# Report"
            assert result == path


class TestPrintSummaryExtended:
    def test_print_with_float_params(self, advisor, capsys):
        result = OptimizationResult(
            success=True,
            best_params={"ratio": 0.75, "count": 10},
            best_score=8.0,
            experiments=5,
            duration=10.0,
        )
        advisor.print_summary(result, {})
        out = capsys.readouterr().out
        assert "0.75" in out
        assert "10" in out

    def test_print_with_violations(self, advisor, capsys):
        result = OptimizationResult(
            success=True, best_params={"k": 1},
            best_score=5.0, experiments=5, duration=10.0
        )
        advisor.print_summary(result, {"structure_violations": 5})
        out = capsys.readouterr().out
        assert "预期改进" in out
        assert "5" in out
