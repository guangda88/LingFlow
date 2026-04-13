"""Tests for verification runner + auto-retry framework"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from lingflow.workflow.verification import (
    RetryContext,
    VerificationCheck,
    VerificationResult,
    VerificationRunner,
)


class TestVerificationResult:
    """VerificationResult dataclass tests"""

    def test_create_passed_result(self):
        result = VerificationResult(
            task_id="T01",
            passed=True,
            command="pytest",
            exit_code=0,
            stdout="3 passed",
            stderr="",
            execution_time=1.5,
            check_name="pytest",
        )
        assert result.passed is True
        assert result.exit_code == 0
        assert result.check_name == "pytest"

    def test_create_failed_result(self):
        result = VerificationResult(
            task_id="T01",
            passed=False,
            command="ruff check .",
            exit_code=1,
            stdout="",
            stderr="error: syntax error",
            execution_time=0.3,
            check_name="ruff",
        )
        assert result.passed is False
        assert result.exit_code == 1

    def test_to_dict(self):
        result = VerificationResult(
            task_id="T01",
            passed=True,
            command="pytest",
            exit_code=0,
            stdout="x" * 1000,
            stderr="y" * 1000,
            execution_time=1.0,
            check_name="pytest",
        )
        d = result.to_dict()
        assert d["passed"] is True
        assert len(d["stdout"]) <= 500
        assert len(d["stderr"]) <= 500


class TestVerificationCheck:
    """VerificationCheck dataclass tests"""

    def test_create_check(self):
        check = VerificationCheck(name="pytest", command="python -m pytest")
        assert check.name == "pytest"
        assert check.timeout == 120
        assert check.working_dir is None

    def test_create_check_custom(self):
        check = VerificationCheck(
            name="custom",
            command="make test",
            timeout=300,
            working_dir="/tmp",
        )
        assert check.timeout == 300
        assert check.working_dir == "/tmp"


class TestRetryContext:
    """RetryContext tests"""

    def test_has_retries_left(self):
        ctx = RetryContext(attempt=1, max_retries=3)
        assert ctx.has_retries_left is True

    def test_no_retries_left(self):
        ctx = RetryContext(attempt=3, max_retries=3)
        assert ctx.has_retries_left is False

    def test_format_for_injection_empty(self):
        ctx = RetryContext(attempt=1, max_retries=3)
        assert ctx.format_for_injection() == ""

    def test_format_for_injection_with_results(self):
        ctx = RetryContext(
            attempt=2,
            max_retries=3,
            previous_results=[
                VerificationResult(
                    task_id="T01",
                    passed=False,
                    command="pytest",
                    exit_code=1,
                    stdout="",
                    stderr="1 failed",
                    execution_time=1.0,
                    check_name="pytest",
                ),
            ],
            failure_summary="pytest failed",
        )
        text = ctx.format_for_injection()
        assert "attempt 2/3" in text
        assert "pytest" in text
        assert "FAIL" in text
        assert "1 failed" in text


class TestVerificationRunner:
    """VerificationRunner tests"""

    @pytest.fixture
    def runner(self, tmp_path):
        return VerificationRunner(str(tmp_path))

    def test_init(self, tmp_path):
        runner = VerificationRunner(str(tmp_path))
        assert runner.workdir == tmp_path

    @patch("lingflow.workflow.verification.subprocess.run")
    def test_run_check_pass(self, mock_run, runner):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="3 passed",
            stderr="",
        )
        check = VerificationCheck(name="pytest", command="python -m pytest")
        result = runner.run_check("T01", check)

        assert result.passed is True
        assert result.exit_code == 0
        assert result.stdout == "3 passed"
        assert result.check_name == "pytest"
        mock_run.assert_called_once()

    @patch("lingflow.workflow.verification.subprocess.run")
    def test_run_check_fail(self, mock_run, runner):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="1 failed",
            stderr="AssertionError",
        )
        check = VerificationCheck(name="pytest", command="python -m pytest")
        result = runner.run_check("T01", check)

        assert result.passed is False
        assert result.exit_code == 1

    @patch("lingflow.workflow.verification.subprocess.run")
    def test_run_check_timeout(self, mock_run, runner):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=30)
        check = VerificationCheck(name="pytest", command="python -m pytest", timeout=30)
        result = runner.run_check("T01", check)

        assert result.passed is False
        assert "Timeout" in result.stderr
        assert result.exit_code == -1

    @patch("lingflow.workflow.verification.subprocess.run")
    def test_run_check_exception(self, mock_run, runner):
        mock_run.side_effect = OSError("command not found")
        check = VerificationCheck(name="pytest", command="python -m pytest")
        result = runner.run_check("T01", check)

        assert result.passed is False
        assert "command not found" in result.stderr

    @patch("lingflow.workflow.verification.subprocess.run")
    def test_run_checks_multiple(self, mock_run, runner):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="3 passed", stderr=""),
            MagicMock(returncode=0, stdout="All good", stderr=""),
        ]
        checks = [
            VerificationCheck(name="pytest", command="python -m pytest"),
            VerificationCheck(name="ruff", command="ruff check ."),
        ]
        results = runner.run_checks("T01", checks)

        assert len(results) == 2
        assert all(r.passed for r in results)

    @patch("lingflow.workflow.verification.subprocess.run")
    def test_run_checks_partial_failure(self, mock_run, runner):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="3 passed", stderr=""),
            MagicMock(returncode=1, stdout="", stderr="syntax error"),
        ]
        checks = [
            VerificationCheck(name="pytest", command="python -m pytest"),
            VerificationCheck(name="ruff", command="ruff check ."),
        ]
        results = runner.run_checks("T01", checks)

        assert results[0].passed is True
        assert results[1].passed is False

    @patch("lingflow.workflow.verification.time.sleep")
    @patch("lingflow.workflow.verification.subprocess.run")
    def test_verify_with_retry_pass_first_try(self, mock_run, mock_sleep, runner):
        mock_run.return_value = MagicMock(returncode=0, stdout="3 passed", stderr="")
        checks = [VerificationCheck(name="pytest", command="python -m pytest")]
        execute_fn = MagicMock()

        success, results, ctx = runner.verify_with_retry(
            task_id="T01",
            checks=checks,
            execute_fn=execute_fn,
            max_retries=3,
        )

        assert success is True
        assert ctx.attempt == 1
        assert len(results) == 1
        execute_fn.assert_not_called()

    @patch("lingflow.workflow.verification.time.sleep")
    @patch("lingflow.workflow.verification.subprocess.run")
    def test_verify_with_retry_pass_after_retry(self, mock_run, mock_sleep, runner):
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="1 failed", stderr="error"),
            MagicMock(returncode=0, stdout="3 passed", stderr=""),
        ]
        checks = [VerificationCheck(name="pytest", command="python -m pytest")]
        execute_fn = MagicMock(return_value=True)

        success, results, ctx = runner.verify_with_retry(
            task_id="T01",
            checks=checks,
            execute_fn=execute_fn,
            max_retries=3,
        )

        assert success is True
        assert ctx.attempt == 2
        assert len(results) == 2
        execute_fn.assert_called_once()

    @patch("lingflow.workflow.verification.time.sleep")
    @patch("lingflow.workflow.verification.subprocess.run")
    def test_verify_with_retry_all_fail(self, mock_run, mock_sleep, runner):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        checks = [VerificationCheck(name="pytest", command="python -m pytest")]
        execute_fn = MagicMock(return_value=True)

        success, results, ctx = runner.verify_with_retry(
            task_id="T01",
            checks=checks,
            execute_fn=execute_fn,
            max_retries=2,
        )

        assert success is False
        assert ctx.attempt == 2
        assert len(results) == 2

    @patch("lingflow.workflow.verification.time.sleep")
    @patch("lingflow.workflow.verification.subprocess.run")
    def test_verify_with_retry_execute_fn_exception(self, mock_run, mock_sleep, runner):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        checks = [VerificationCheck(name="pytest", command="python -m pytest")]
        execute_fn = MagicMock(side_effect=RuntimeError("boom"))

        success, results, ctx = runner.verify_with_retry(
            task_id="T01",
            checks=checks,
            execute_fn=execute_fn,
            max_retries=2,
        )

        assert success is False
        execute_fn.assert_called_once()

    @patch("lingflow.workflow.verification.time.sleep")
    @patch("lingflow.workflow.verification.subprocess.run")
    def test_verify_with_retry_no_delay(self, mock_run, mock_sleep, runner):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        checks = [VerificationCheck(name="pytest", command="python -m pytest")]
        execute_fn = MagicMock(return_value=True)

        runner.verify_with_retry(
            task_id="T01",
            checks=checks,
            execute_fn=execute_fn,
            max_retries=1,
            retry_delay=0,
        )

        mock_sleep.assert_not_called()


class TestParseMustHaves:
    """parse_must_haves tests"""

    @pytest.fixture
    def runner(self, tmp_path):
        return VerificationRunner(str(tmp_path))

    def test_parse_pytest(self, runner):
        checks = runner.parse_must_haves(["pytest"])
        assert len(checks) == 1
        assert checks[0].name == "pytest"
        assert "pytest" in checks[0].command

    def test_parse_test_alias(self, runner):
        checks = runner.parse_must_haves(["test"])
        assert len(checks) == 1
        assert checks[0].name == "pytest"

    def test_parse_ruff(self, runner):
        checks = runner.parse_must_haves(["ruff"])
        assert len(checks) == 1
        assert checks[0].name == "ruff"

    def test_parse_mypy(self, runner):
        checks = runner.parse_must_haves(["mypy"])
        assert len(checks) == 1
        assert checks[0].name == "mypy"

    def test_parse_build(self, runner):
        checks = runner.parse_must_haves(["build"])
        assert len(checks) == 1
        assert checks[0].name == "build"

    def test_parse_run_prefix(self, runner):
        checks = runner.parse_must_haves(["run:make test"])
        assert len(checks) == 1
        assert checks[0].command == "make test"

    def test_parse_command_prefix(self, runner):
        checks = runner.parse_must_haves(["command:npm test"])
        assert len(checks) == 1
        assert checks[0].command == "npm test"

    def test_parse_multiple(self, runner):
        checks = runner.parse_must_haves(["pytest", "ruff", "mypy"])
        assert len(checks) == 3
        assert checks[0].name == "pytest"
        assert checks[1].name == "ruff"
        assert checks[2].name == "mypy"

    def test_parse_empty(self, runner):
        checks = runner.parse_must_haves([])
        assert len(checks) == 0

    def test_parse_unknown_ignored(self, runner):
        checks = runner.parse_must_haves(["unknown-check", "pytest"])
        assert len(checks) == 1
        assert checks[0].name == "pytest"

    def test_parse_case_insensitive(self, runner):
        checks = runner.parse_must_haves(["PyTest", "RUFF CHECK"])
        assert len(checks) == 2


class TestBuildFailureSummary:
    """_build_failure_summary tests"""

    @pytest.fixture
    def runner(self, tmp_path):
        return VerificationRunner(str(tmp_path))

    def test_empty_results(self, runner):
        assert runner._build_failure_summary([]) == ""

    def test_single_failure(self, runner):
        results = [
            VerificationResult(
                task_id="T01",
                passed=False,
                command="pytest",
                exit_code=1,
                stdout="1 failed",
                stderr="AssertionError",
                execution_time=1.0,
                check_name="pytest",
            )
        ]
        summary = runner._build_failure_summary(results)
        assert "pytest" in summary
        assert "FAIL" in summary
        assert "AssertionError" in summary


class TestWriteVerificationReport:
    """write_verification_report tests"""

    @pytest.fixture
    def runner(self, tmp_path):
        return VerificationRunner(str(tmp_path))

    def test_write_pass_report(self, runner, tmp_path):
        results = [
            VerificationResult(
                task_id="T01",
                passed=True,
                command="pytest",
                exit_code=0,
                stdout="3 passed",
                stderr="",
                execution_time=1.5,
                check_name="pytest",
            )
        ]
        report_path = runner.write_verification_report("T01", results)
        assert report_path.exists()
        content = report_path.read_text()
        assert "PASS" in content
        assert "pytest" in content

    def test_write_fail_report(self, runner):
        results = [
            VerificationResult(
                task_id="T01",
                passed=False,
                command="pytest",
                exit_code=1,
                stdout="1 failed",
                stderr="error",
                execution_time=1.0,
                check_name="pytest",
            )
        ]
        report_path = runner.write_verification_report("T01", results)
        content = report_path.read_text()
        assert "FAIL" in content

    def test_write_report_with_retry_context(self, runner):
        results = [
            VerificationResult(
                task_id="T01",
                passed=True,
                command="pytest",
                exit_code=0,
                stdout="ok",
                stderr="",
                execution_time=1.0,
                check_name="pytest",
            )
        ]
        retry_ctx = RetryContext(attempt=2, max_retries=3)
        report_path = runner.write_verification_report("T01", results, retry_ctx)
        content = report_path.read_text()
        assert "2/3" in content

    def test_report_creates_directory(self, runner, tmp_path):
        lingflow_dir = tmp_path / ".lingflow"
        assert not lingflow_dir.exists()
        results = [
            VerificationResult(
                task_id="T01",
                passed=True,
                command="pytest",
                exit_code=0,
                stdout="",
                stderr="",
                execution_time=1.0,
                check_name="pytest",
            )
        ]
        report_path = runner.write_verification_report("T01", results)
        assert lingflow_dir.exists()
        assert report_path.exists()


class TestIntegration:
    """Integration tests for verification flow"""

    @pytest.fixture
    def runner(self, tmp_path):
        return VerificationRunner(str(tmp_path))

    def test_full_verify_flow(self, runner):
        must_haves = ["pytest", "ruff check"]
        checks = runner.parse_must_haves(must_haves)
        assert len(checks) == 2
        assert checks[0].name == "pytest"
        assert checks[1].name == "ruff"

    def test_must_haves_to_report_flow(self, runner):
        must_haves = ["pytest", "run:make lint"]
        checks = runner.parse_must_haves(must_haves)

        results = [
            VerificationResult(
                task_id="T01",
                passed=True,
                command=checks[0].command,
                exit_code=0,
                stdout="3 passed",
                stderr="",
                execution_time=1.0,
                check_name=checks[0].name,
            ),
            VerificationResult(
                task_id="T01",
                passed=False,
                command=checks[1].command,
                exit_code=1,
                stdout="",
                stderr="lint error",
                execution_time=0.5,
                check_name=checks[1].name,
            ),
        ]

        report_path = runner.write_verification_report("T01", results)
        content = report_path.read_text()
        assert "PASS" in content
        assert "FAIL" in content
        assert "pytest" in content
        assert "custom-2" in content
