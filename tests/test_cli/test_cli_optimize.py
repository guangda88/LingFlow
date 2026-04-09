"""Tests for lingflow.cli.optimize module"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lingflow.cli.optimize import (
    apply_optimization,
    cancel,
    check_trigger,
    generate_config,
    optimize,
    run,
    status,
    wait_completion,
)


class TestOptimizeCommand:
    """Test optimize CLI command group"""

    def test_optimize_group_exists(self):
        """Test that optimize command group exists"""
        runner = CliRunner()
        result = runner.invoke(optimize, ["--help"])
        assert result.exit_code == 0
        assert "自优化系统" in result.output


class TestRunCommand:
    """Test run command"""

    def test_run_help(self):
        """Test run command help text"""
        runner = CliRunner()
        result = runner.invoke(run, ["--help"])
        assert result.exit_code == 0
        assert "--target" in result.output
        assert "--async" in result.output
        assert "--experiments" in result.output
        assert "--report" in result.output
        assert "GOAL" in result.output

    def test_run_invalid_goal(self):
        """Test run with invalid goal choice"""
        runner = CliRunner()
        result = runner.invoke(run, ["invalid_goal"])
        assert result.exit_code != 0
        assert "Invalid value for 'goal'" in result.output

    @patch("lingflow.self_optimizer.quick_optimize")
    @patch("lingflow.self_optimizer.evaluator.StructureEvaluator")
    @patch("lingflow.self_optimizer.config.get_global_config")
    def test_run_structure_goal(self, mock_config, mock_evaluator_class, mock_quick_optimize):
        """Test run with structure goal"""
        mock_config_obj = MagicMock()
        mock_config_obj.get.return_value = None
        mock_config.return_value = mock_config_obj

        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "structure_violations": 5,
            "avg_class_size": 150,
            "avg_complexity": 8.5,
            "large_classes_count": 3,
            "long_methods_count": 4,
        }
        mock_evaluator_class.return_value = mock_evaluator

        mock_result = MagicMock()
        mock_result.success = True
        mock_quick_optimize.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run, ["structure"])

        assert result.exit_code == 0
        assert "结构违规: 5" in result.output

    @patch("lingflow.self_optimizer.quick_optimize")
    @patch("lingflow.self_optimizer.config.get_global_config")
    def test_run_async_mode(self, mock_config, mock_quick_optimize):
        """Test run with async mode"""
        mock_config_obj = MagicMock()
        mock_config_obj.get.return_value = None
        mock_config.return_value = mock_config_obj

        mock_quick_optimize.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run, ["structure", "--async"])

        assert result.exit_code == 0
        assert "优化已启动（后台运行）" in result.output

    @patch("lingflow.cli.optimize.quick_optimize")
    @patch("lingflow.self_optimizer.config.get_global_config")
    def test_run_with_custom_experiments(self, mock_config, mock_quick_optimize):
        """Test run with custom experiments count"""
        mock_config_obj = MagicMock()
        mock_config.return_value = mock_config_obj

        mock_result = MagicMock()
        mock_result.success = True
        mock_quick_optimize.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run, ["structure", "--experiments", "50"])

        assert result.exit_code == 0
        mock_config_obj.set.assert_called()
        call_args = mock_config_obj.set.call_args
        assert "optimization.max_experiments" in str(call_args)

    @patch("lingflow.cli.optimize.quick_optimize")
    @patch("lingflow.self_optimizer.config.get_global_config")
    def test_run_failure(self, mock_config, mock_quick_optimize):
        """Test run when optimization fails"""
        mock_config_obj = MagicMock()
        mock_config_obj.get.return_value = None
        mock_config.return_value = mock_config_obj

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Test error"
        mock_quick_optimize.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run, ["structure"])

        assert result.exit_code == 1
        assert "优化失败" in result.output


class TestStatusCommand:
    """Test status command"""

    @patch("lingflow.hooks.get_global_hook")
    def test_status_no_optimization_running(self, mock_get_hook):
        """Test status when no optimization is running"""
        mock_hook = MagicMock()
        mock_hook.is_optimization_running.return_value = False
        mock_get_hook.return_value = mock_hook

        runner = CliRunner()
        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "没有运行中的优化" in result.output

    @patch("lingflow.hooks.get_global_hook")
    def test_status_optimization_running(self, mock_get_hook):
        """Test status when optimization is running"""
        mock_hook = MagicMock()
        mock_hook.is_optimization_running.return_value = True
        mock_optimizer = MagicMock()
        mock_optimizer.get_progress.return_value = {"pid": 12345}
        mock_hook.optimizer = mock_optimizer
        mock_get_hook.return_value = mock_hook

        runner = CliRunner()
        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "优化运行中" in result.output
        assert "12345" in result.output


class TestWaitCommand:
    """Test wait command"""

    def test_wait_help(self):
        """Test wait command help text"""
        runner = CliRunner()
        result = runner.invoke(wait_completion, ["--help"])
        assert result.exit_code == 0
        assert "--timeout" in result.output

    @patch("lingflow.hooks.get_global_hook")
    def test_wait_no_optimization_running(self, mock_get_hook):
        """Test wait when no optimization is running"""
        mock_hook = MagicMock()
        mock_hook.is_optimization_running.return_value = False
        mock_get_hook.return_value = mock_hook

        runner = CliRunner()
        result = runner.invoke(wait_completion)

        assert result.exit_code == 0
        assert "没有运行中的优化" in result.output


class TestCancelCommand:
    """Test cancel command"""

    @patch("lingflow.hooks.get_global_hook")
    def test_cancel_no_optimization_running(self, mock_get_hook):
        """Test cancel when no optimization is running"""
        mock_hook = MagicMock()
        mock_hook.is_optimization_running.return_value = False
        mock_get_hook.return_value = mock_hook

        runner = CliRunner()
        result = runner.invoke(cancel)

        assert result.exit_code == 0
        assert "没有运行中的优化" in result.output

    @patch("lingflow.hooks.get_global_hook")
    def test_cancel_success(self, mock_get_hook):
        """Test successful cancel"""
        mock_hook = MagicMock()
        mock_hook.is_optimization_running.return_value = True
        mock_get_hook.return_value = mock_hook

        runner = CliRunner()
        result = runner.invoke(cancel)

        assert result.exit_code == 0
        assert "优化已取消" in result.output
        mock_hook.cancel_optimization.assert_called_once()


class TestApplyOptimization:
    """Test apply_optimization command"""

    def test_apply_help(self):
        """Test apply command help text"""
        runner = CliRunner()
        result = runner.invoke(apply_optimization, ["--help"])
        assert result.exit_code == 0
        assert "--report" in result.output

    def test_apply_report_not_found(self):
        """Test apply with non-existent report"""
        runner = CliRunner()
        result = runner.invoke(apply_optimization, ["--report", "nonexistent.md"])
        assert result.exit_code == 1
        assert "报告文件不存在" in result.output

    def test_apply_valid_report(self, tmp_path):
        """Test apply with valid report"""
        report_path = tmp_path / "report.md"
        report_path.write_text(
            """
# Optimization Report

```yaml
max_complexity: 10
max_class_size: 200
```
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Copy report to current dir
            import shutil

            shutil.copy(report_path, "report.md")

            # Use non-interactive flag
            result = runner.invoke(apply_optimization, ["--report", "report.md"])

        # Command should run but fail without confirmation in test
        # The actual test is that it doesn't crash


class TestGenerateConfig:
    """Test generate_config command"""

    def test_generate_config_help(self):
        """Test generate_config help text"""
        runner = CliRunner()
        result = runner.invoke(generate_config, ["--help"])
        assert result.exit_code == 0
        assert "--report" in result.output
        assert "--output" in result.output

    def test_generate_config_report_not_found(self):
        """Test generate_config with non-existent report"""
        runner = CliRunner()
        result = runner.invoke(generate_config, ["--report", "nonexistent.md"])
        assert result.exit_code == 1
        assert "报告文件不存在" in result.output

    def test_generate_config_success(self, tmp_path):
        """Test successful config generation"""
        report_path = tmp_path / "report.md"
        report_path.write_text(
            """
# Report

```yaml
param1: value1
param2: 100
```
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            import shutil

            shutil.copy(report_path, "report.md")

            output_file = "config_optimized.yaml"
            result = runner.invoke(generate_config, ["--report", "report.md", "--output", output_file])

        assert result.exit_code == 0
        assert "配置文件已生成" in result.output
        assert Path(output_file).exists()


class TestCheckTrigger:
    """Test check_trigger command"""

    def test_check_help(self):
        """Test check command help text"""
        runner = CliRunner()
        result = runner.invoke(check_trigger, ["--help"])
        assert result.exit_code == 0
        assert "--target" in result.output

    @patch("lingflow.self_optimizer.evaluator.StructureEvaluator")
    @patch("lingflow.self_optimizer.trigger.OptimizationTrigger")
    def test_check_no_trigger_needed(self, mock_trigger_class, mock_evaluator_class):
        """Test check when no trigger is needed"""
        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "avg_complexity": 2.0,
            "large_classes_count": 0,
            "structure_violations": 1,
        }
        mock_evaluator_class.return_value = mock_evaluator

        mock_trigger = MagicMock()
        mock_trigger.check_all_conditions.return_value = (False, MagicMock())
        mock_trigger_class.return_value = mock_trigger

        runner = CliRunner()
        result = runner.invoke(check_trigger)

        assert result.exit_code == 0
        assert "暂时不需要优化" in result.output

    @patch("lingflow.self_optimizer.evaluator.StructureEvaluator")
    @patch("lingflow.self_optimizer.trigger.OptimizationTrigger")
    def test_check_trigger_needed(self, mock_trigger_class, mock_evaluator_class):
        """Test check when trigger is needed"""
        mock_evaluator = MagicMock()
        mock_evaluator.get_current_metrics.return_value = {
            "avg_complexity": 15.0,
            "large_classes_count": 10,
            "structure_violations": 50,
        }
        mock_evaluator_class.return_value = mock_evaluator

        mock_info = MagicMock()
        mock_info.reason = "High complexity"
        mock_info.priority = "high"

        mock_trigger = MagicMock()
        mock_trigger.check_all_conditions.return_value = (True, mock_info)
        mock_trigger_class.return_value = mock_trigger

        runner = CliRunner()
        result = runner.invoke(check_trigger)

        assert result.exit_code == 0
        assert "需要优化" in result.output
        assert "High complexity" in result.output
