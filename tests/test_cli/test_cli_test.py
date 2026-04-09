"""Tests for lingflow.cli.test module"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lingflow.cli.test import (
    run_e2e_test,
    run_test,
    test,
)


class TestCommand:
    """Test CLI command group"""

    def test_test_group_exists(self):
        """Test that test command group exists"""
        runner = CliRunner()
        result = runner.invoke(test, ["--help"])
        assert result.exit_code == 0
        assert "测试系统" in result.output


class TestRunTest:
    """Test run_test command"""

    def test_run_test_help(self):
        """Test run_test command help text"""
        runner = CliRunner()
        result = runner.invoke(run_test, ["--help"])
        assert result.exit_code == 0
        assert "--coverage" in result.output
        assert "--verbose" in result.output
        assert "--parallel" in result.output
        assert "--target" in result.output

    @patch("lingflow.cli.test.subprocess.run")
    def test_run_test_default(self, mock_run):
        """Test run_test with default parameters"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_test)

        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "python" in call_args
        assert "-m" in call_args
        assert "pytest" in call_args

    @patch("lingflow.cli.test.subprocess.run")
    def test_run_test_with_coverage(self, mock_run):
        """Test run_test with coverage flag"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_test, ["--coverage"])

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "--cov=lingflow" in call_args
        assert "--cov-report=term-missing" in call_args

    @patch("lingflow.cli.test.subprocess.run")
    def test_run_test_verbose(self, mock_run):
        """Test run_test with verbose flag"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_test, ["--verbose"])

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "-v" in call_args

    @patch("lingflow.cli.test.subprocess.run")
    def test_run_test_quiet_mode(self, mock_run):
        """Test run_test without verbose (quiet mode)"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_test)

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "-q" in call_args

    @patch("lingflow.cli.test.subprocess.run")
    def test_run_test_with_parallel(self, mock_run):
        """Test run_test with parallel flag"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_test, ["--parallel"])

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "-n" in call_args
        assert "auto" in call_args

    @patch("lingflow.cli.test.subprocess.run")
    def test_run_test_with_target(self, mock_run):
        """Test run_test with specific target"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_test, ["--target", "tests/test_core/"])

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "tests/test_core/" in call_args

    @patch("lingflow.cli.test.subprocess.run")
    def test_run_test_failure(self, mock_run):
        """Test run_test when tests fail"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_test)

        assert result.exit_code == 1

    @patch("lingflow.cli.test.subprocess.run")
    def test_run_test_combined_options(self, mock_run):
        """Test run_test with multiple options"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_test, ["--coverage", "--verbose", "--parallel", "--target", "tests/test_utils/"])

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "--cov=lingflow" in call_args
        assert "-v" in call_args
        assert "-n" in call_args
        assert "tests/test_utils/" in call_args


class TestRunE2ETest:
    """Test run_e2e_test command"""

    def test_e2e_help(self):
        """Test e2e command help text"""
        runner = CliRunner()
        result = runner.invoke(run_e2e_test, ["--help"])
        assert result.exit_code == 0
        assert "--scenario" in result.output
        assert "--verbose" in result.output

    def test_e2e_no_integration_directory(self):
        """Test e2e when integration directory doesn't exist"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(run_e2e_test)

        assert result.exit_code == 0
        assert "E2E测试目录不存在" in result.output

    def test_e2e_no_test_files(self, tmp_path):
        """Test e2e when no E2E test files found"""
        integration_dir = tmp_path / "tests" / "integration"
        integration_dir.mkdir(parents=True)

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create integration dir but no e2e files
            (Path("tests") / "integration").mkdir(parents=True, exist_ok=True)
            result = runner.invoke(run_e2e_test)

        assert result.exit_code == 0
        assert "未找到E2E测试文件" in result.output

    def test_e2e_with_test_files(self, tmp_path):
        """Test e2e with test files present"""
        integration_dir = tmp_path / "tests" / "integration"
        integration_dir.mkdir(parents=True)

        # Create a dummy e2e test file
        (integration_dir / "test_e2e_demo.py").write_text("def test_e2e(): pass")

        runner = CliRunner()
        with runner.isolated_filesystem():
            import shutil

            shutil.copytree(integration_dir.parent.parent, "tests", dirs_exist_ok=True)
            result = runner.invoke(run_e2e_test)

        # Should attempt to run tests
        assert "找到" in result.output or "E2E测试" in result.output

    @patch("lingflow.cli.test.subprocess.run")
    def test_e2e_with_scenario(self, mock_run):
        """Test e2e with specific scenario"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create integration directory with e2e test
            (Path("tests") / "integration").mkdir(parents=True, exist_ok=True)
            (Path("tests") / "integration" / "test_e2e_scenario.py").write_text("def test_scenario(): pass")

            result = runner.invoke(run_e2e_test, ["--scenario", "user_login"])

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "-k" in call_args
        assert "user_login" in call_args

    @patch("lingflow.cli.test.subprocess.run")
    def test_e2e_verbose_mode(self, mock_run):
        """Test e2e with verbose mode"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create integration directory with e2e test
            (Path("tests") / "integration").mkdir(parents=True, exist_ok=True)
            (Path("tests") / "integration" / "test_e2e_demo.py").write_text("def test_e2e(): pass")

            result = runner.invoke(run_e2e_test, ["--verbose"])

        assert result.exit_code == 0
        call_args = mock_run.call_args[0][0]
        assert "-v" in call_args
