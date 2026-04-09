"""Tests for lingflow.cli.analyze module"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lingflow.cli.analyze import (
    _generate_analysis_report,
    analyze,
    analyze_complexity,
    analyze_duplication,
    run_analyze,
)


class TestAnalyzeCommand:
    """Test analyze CLI command group"""

    def test_analyze_group_exists(self):
        """Test that analyze command group exists"""
        runner = CliRunner()
        result = runner.invoke(analyze, ["--help"])
        assert result.exit_code == 0
        assert "代码分析系统" in result.output


class TestRunAnalyze:
    """Test run_analyze command"""

    def test_run_analyze_help(self):
        """Test run_analyze help text"""
        runner = CliRunner()
        result = runner.invoke(run_analyze, ["--help"])
        assert result.exit_code == 0
        assert "--target" in result.output
        assert "--metrics" in result.output
        assert "--output" in result.output
        assert "--format" in result.output

    @patch("lingflow.self_optimizer.evaluator.StructureEvaluator")
    def test_run_analyze_default(self, mock_evaluator_class):
        """Test run_analyze with defaults"""
        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "structure_violations": 5,
            "avg_class_size": 100,
            "avg_complexity": 3.5,
            "large_classes_count": 2,
            "long_methods_count": 3,
        }
        mock_evaluator_class.return_value = mock_evaluator

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_analyze)

        assert result.exit_code == 0
        assert "结构违规: 5" in result.output
        assert "平均类大小: 100" in result.output
        assert "分析指标:" in result.output

    @patch("lingflow.cli.analyze.StructureEvaluator")
    def test_run_analyze_with_custom_metrics(self, mock_evaluator_class):
        """Test run_analyze with custom metrics"""
        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "structure_violations": 1,
            "avg_class_size": 50,
            "avg_complexity": 2.0,
            "large_classes_count": 0,
            "long_methods_count": 0,
        }
        mock_evaluator_class.return_value = mock_evaluator

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_analyze, ["--metrics", "complexity,security"])

        assert result.exit_code == 0
        assert "complexity, security" in result.output

    @patch("lingflow.cli.analyze.StructureEvaluator")
    def test_run_analyze_saves_report(self, mock_evaluator_class):
        """Test run_analyze saves report"""
        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "structure_violations": 0,
            "avg_class_size": 80,
            "avg_complexity": 2.5,
            "large_classes_count": 1,
            "long_methods_count": 2,
        }
        mock_evaluator_class.return_value = mock_evaluator

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "test_report.md"
            result = runner.invoke(run_analyze, ["--output", output_file])

        assert result.exit_code == 0
        assert "报告已保存" in result.output
        assert Path(output_file).exists()

    @patch("lingflow.cli.analyze.StructureEvaluator")
    def test_run_analyze_json_format(self, mock_evaluator_class):
        """Test run_analyze with JSON format"""
        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "structure_violations": 3,
            "avg_class_size": 120,
            "avg_complexity": 5.0,
            "large_classes_count": 2,
            "long_methods_count": 5,
        }
        mock_evaluator_class.return_value = mock_evaluator

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "test_report.json"
            result = runner.invoke(run_analyze, ["--output", output_file, "--format", "json"])

        assert result.exit_code == 0
        assert Path(output_file).exists()

        with open(output_file) as f:
            data = json.load(f)
        assert "metrics" in data
        assert "results" in data
        assert data["results"]["structure_violations"] == 3

    @patch("lingflow.cli.analyze.StructureEvaluator")
    def test_run_analyze_verbose(self, mock_evaluator_class):
        """Test run_analyze with verbose output"""
        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "structure_violations": 2,
            "avg_class_size": 90,
            "avg_complexity": 3.0,
            "large_classes_count": 1,
            "long_methods_count": 1,
        }
        mock_evaluator_class.return_value = mock_evaluator

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_analyze, ["--verbose"])

        assert result.exit_code == 0


class TestAnalyzeComplexity:
    """Test analyze_complexity command"""

    def test_analyze_complexity_help(self):
        """Test analyze_complexity help text"""
        runner = CliRunner()
        result = runner.invoke(analyze_complexity, ["--help"])
        assert result.exit_code == 0
        assert "--target" in result.output
        assert "--threshold" in result.output
        assert "--verbose" in result.output

    @patch("lingflow.cli.analyze.StructureEvaluator")
    def test_analyze_complexity_default_threshold(self, mock_evaluator_class):
        """Test analyze_complexity with default threshold"""
        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "avg_complexity": 5.5,
            "max_complexity": 15,
            "high_complexity_count": 3,
        }
        mock_evaluator_class.return_value = mock_evaluator

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(analyze_complexity, [])

        assert result.exit_code == 0
        assert "平均复杂度: 5.5" in result.output
        assert "最大复杂度: 15" in result.output
        assert "高复杂度函数: 3" in result.output

    @patch("lingflow.cli.analyze.StructureEvaluator")
    def test_analyze_complexity_custom_threshold(self, mock_evaluator_class):
        """Test analyze_complexity with custom threshold"""
        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "avg_complexity": 8.0,
            "max_complexity": 25,
            "high_complexity_count": 5,
        }
        mock_evaluator_class.return_value = mock_evaluator

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(analyze_complexity, ["--threshold", "20"])

        assert result.exit_code == 0
        assert "阈值: 20" in result.output


class TestAnalyzeDuplication:
    """Test analyze_duplication command"""

    def test_analyze_duplication_help(self):
        """Test analyze_duplication help text"""
        runner = CliRunner()
        result = runner.invoke(analyze_duplication, ["--help"])
        assert result.exit_code == 0
        assert "--target" in result.output
        assert "--min-lines" in result.output

    def test_analyze_duplication_default(self):
        """Test analyze_duplication with defaults"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create some test Python files
            (Path("test1.py")).write_text(
                """
def func1():
    return 1

def func2():
    return 1
""",
                encoding="utf-8",
            )

            result = runner.invoke(analyze_duplication, [])

        assert result.exit_code == 0
        assert "分析代码重复" in result.output
        assert "最小重复行数: 10" in result.output

    def test_analyze_duplication_custom_min_lines(self):
        """Test analyze_duplication with custom min_lines"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(analyze_duplication, ["--min-lines", "5"])

        assert result.exit_code == 0
        assert "最小重复行数: 5" in result.output


class TestGenerateAnalysisReport:
    """Test _generate_analysis_report function"""

    def test_generate_markdown_report(self, tmp_path):
        """Test generating markdown report"""
        report_path = tmp_path / "report.md"
        metrics = ["complexity", "duplication"]
        results = {
            "structure_violations": 2,
            "avg_class_size": 100,
            "avg_complexity": 4.5,
            "large_classes_count": 1,
            "long_methods_count": 2,
        }

        _generate_analysis_report(report_path, metrics, results, "markdown")

        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "# 代码分析报告" in content
        assert "complexity, duplication" in content
        # The format uses ** for bold markdown
        assert "**结构违规**: 2" in content
        assert "**平均类大小**: 100" in content

    def test_generate_json_report(self, tmp_path):
        """Test generating JSON report"""
        report_path = tmp_path / "report.json"
        metrics = ["security"]
        results = {"structure_violations": 0}

        _generate_analysis_report(report_path, metrics, results, "json")

        assert report_path.exists()
        with open(report_path) as f:
            data = json.load(f)
        assert data["metrics"] == ["security"]
        assert data["results"]["structure_violations"] == 0
        assert "timestamp" in data
