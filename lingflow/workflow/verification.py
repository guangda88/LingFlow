"""验证命令 + 自动重试框架

参考 GSD 的 verification pattern:
- 每个 task 的 must_haves 定义验证标准
- 支持运行 shell 命令验证（pytest, ruff check, build 等）
- 验证失败时自动重试，最多 N 次
- 重试时注入失败上下文（哪些检查没过、错误输出）
"""

import logging
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """验证结果

    Attributes:
        task_id: Task ID
        passed: 是否通过
        command: 执行的命令
        exit_code: 退出码
        stdout: 标准输出
        stderr: 标准错误
        execution_time: 执行时间（秒）
        check_name: 检查名称（如 "pytest", "ruff"）
    """

    task_id: str
    passed: bool
    command: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    check_name: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "task_id": self.task_id,
            "passed": self.passed,
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout[:500],
            "stderr": self.stderr[:500],
            "execution_time": self.execution_time,
            "check_name": self.check_name,
        }


@dataclass
class VerificationCheck:
    """单个验证检查

    Attributes:
        name: 检查名称
        command: Shell 命令
        timeout: 超时（秒）
        working_dir: 工作目录（None = 继承当前目录）
    """

    name: str
    command: str
    timeout: int = 120
    working_dir: Optional[str] = None


@dataclass
class RetryContext:
    """重试上下文

    Attributes:
        attempt: 当前尝试次数
        max_retries: 最大重试次数
        previous_results: 之前的验证结果
        failure_summary: 失败摘要
    """

    attempt: int
    max_retries: int
    previous_results: List[VerificationResult] = field(default_factory=list)
    failure_summary: str = ""

    @property
    def has_retries_left(self) -> bool:
        return self.attempt < self.max_retries

    def format_for_injection(self) -> str:
        """格式化为可注入到 task params 的上下文"""
        if not self.previous_results:
            return ""

        lines = [
            f"## Retry Context (attempt {self.attempt}/{self.max_retries})",
            "",
            self.failure_summary,
            "",
            "### Previous Verification Results",
            "",
        ]

        for result in self.previous_results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"- **{result.check_name}**: {status} (exit code {result.exit_code})")
            if not result.passed and result.stderr:
                lines.append(f"  - Error: {result.stderr[:200]}")

        lines.append("")
        lines.append("Fix the issues above and try again.")
        return "\n".join(lines)


class VerificationRunner:
    """验证运行器

    运行验证命令检查 task 是否真正完成。
    支持 must_haves 中定义的检查项。

    Usage:
        runner = VerificationRunner(workdir="/path/to/project")

        # 定义检查
        checks = [
            VerificationCheck(name="pytest", command="python -m pytest tests/ -x"),
            VerificationCheck(name="ruff", command="ruff check src/"),
        ]

        # 运行验证
        result = runner.run_checks("T01", checks)

        # 带自动重试的验证
        success, all_results, retry_ctx = runner.verify_with_retry(
            task_id="T01",
            checks=checks,
            execute_fn=my_execute_function,
            max_retries=3,
        )
    """

    def __init__(self, workdir: str):
        """初始化验证运行器

        Args:
            workdir: 工作目录
        """
        self.workdir = Path(workdir)

    def run_check(self, task_id: str, check: VerificationCheck) -> VerificationResult:
        """运行单个验证检查

        Args:
            task_id: Task ID
            check: 验证检查定义

        Returns:
            验证结果
        """
        working_dir = check.working_dir or str(self.workdir)
        logger.info(f"Running verification '{check.name}' for {task_id}: {check.command}")

        start_time = time.time()
        try:
            proc = subprocess.run(
                shlex.split(check.command),
                shell=False,
                capture_output=True,
                text=True,
                timeout=check.timeout,
                cwd=working_dir,
            )
            elapsed = time.time() - start_time

            passed = proc.returncode == 0
            result = VerificationResult(
                task_id=task_id,
                passed=passed,
                command=check.command,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                execution_time=elapsed,
                check_name=check.name,
            )

            if passed:
                logger.info(f"Verification '{check.name}' PASSED ({elapsed:.2f}s)")
            else:
                logger.warning(f"Verification '{check.name}' FAILED (exit {proc.returncode})")
                if proc.stderr:
                    logger.debug(f"stderr: {proc.stderr[:200]}")

            return result

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            logger.error(f"Verification '{check.name}' TIMED OUT after {check.timeout}s")
            return VerificationResult(
                task_id=task_id,
                passed=False,
                command=check.command,
                exit_code=-1,
                stdout="",
                stderr=f"Timeout after {check.timeout}s",
                execution_time=elapsed,
                check_name=check.name,
            )
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Verification '{check.name}' ERROR: {e}")
            return VerificationResult(
                task_id=task_id,
                passed=False,
                command=check.command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=elapsed,
                check_name=check.name,
            )

    def run_checks(self, task_id: str, checks: List[VerificationCheck]) -> List[VerificationResult]:
        """运行多个验证检查

        Args:
            task_id: Task ID
            checks: 验证检查列表

        Returns:
            验证结果列表
        """
        results = []
        for check in checks:
            result = self.run_check(task_id, check)
            results.append(result)
        return results

    def verify_with_retry(
        self,
        task_id: str,
        checks: List[VerificationCheck],
        execute_fn: object,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> Tuple[bool, List[VerificationResult], RetryContext]:
        """带自动重试的验证

        验证失败时调用 execute_fn 重新执行 task，然后再次验证。
        每次重试都会将失败上下文注入到执行参数中。

        Args:
            task_id: Task ID
            checks: 验证检查列表
            execute_fn: 重试时的执行函数，签名: (task_id: str, retry_context: RetryContext) -> bool
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）

        Returns:
            (是否通过, 所有验证结果, 重试上下文)
        """
        retry_ctx = RetryContext(attempt=0, max_retries=max_retries)
        all_results: List[VerificationResult] = []

        while True:
            retry_ctx.attempt += 1
            logger.info(f"Verification attempt {retry_ctx.attempt}/{max_retries} for {task_id}")

            results = self.run_checks(task_id, checks)
            all_results.extend(results)

            passed = all(r.passed for r in results)
            if passed:
                logger.info(f"All verifications passed for {task_id} on attempt {retry_ctx.attempt}")
                return True, all_results, retry_ctx

            failed_checks = [r for r in results if not r.passed]
            retry_ctx.previous_results = failed_checks
            retry_ctx.failure_summary = self._build_failure_summary(failed_checks)

            logger.warning(
                f"Verification failed for {task_id}: "
                f"{len(failed_checks)}/{len(results)} checks failed "
                f"(attempt {retry_ctx.attempt}/{max_retries})"
            )

            if not retry_ctx.has_retries_left:
                logger.error(f"Max retries ({max_retries}) exceeded for {task_id}")
                return False, all_results, retry_ctx

            if retry_delay > 0:
                logger.info(f"Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)

            try:
                retry_success = execute_fn(task_id, retry_ctx)
                if not retry_success:
                    logger.warning(f"Retry execute_fn returned False for {task_id}")
            except Exception as e:
                logger.error(f"Retry execute_fn failed for {task_id}: {e}")

    def parse_must_haves(self, must_haves: List[str]) -> List[VerificationCheck]:
        """从 must_haves 列表解析验证检查

        支持格式:
        - "pytest" → 默认 pytest 命令
        - "ruff check" → 默认 ruff 命令
        - "run:pytest tests/ -x" → 自定义命令
        - "command:make test" → 自定义命令

        Args:
            must_haves: Must-have 列表

        Returns:
            验证检查列表
        """
        checks = []
        for item in must_haves:
            item_lower = item.strip().lower()

            if item_lower.startswith("run:"):
                cmd = item.strip()[4:].strip()
                checks.append(VerificationCheck(
                    name=f"custom-{len(checks) + 1}",
                    command=cmd,
                ))
            elif item_lower.startswith("command:"):
                cmd = item.strip()[8:].strip()
                checks.append(VerificationCheck(
                    name=f"custom-{len(checks) + 1}",
                    command=cmd,
                ))
            elif item_lower in ("pytest", "test", "tests"):
                checks.append(VerificationCheck(
                    name="pytest",
                    command="python -m pytest -x",
                    timeout=300,
                ))
            elif item_lower in ("ruff", "ruff check", "lint"):
                checks.append(VerificationCheck(
                    name="ruff",
                    command="ruff check .",
                    timeout=60,
                ))
            elif item_lower in ("mypy", "type check", "typecheck"):
                checks.append(VerificationCheck(
                    name="mypy",
                    command="python -m mypy . --ignore-missing-imports",
                    timeout=120,
                ))
            elif item_lower in ("build", "make"):
                checks.append(VerificationCheck(
                    name="build",
                    command="python -m build",
                    timeout=300,
                ))

        return checks

    def _build_failure_summary(self, failed_results: List[VerificationResult]) -> str:
        """构建失败摘要

        Args:
            failed_results: 失败的验证结果

        Returns:
            失败摘要文本
        """
        if not failed_results:
            return ""

        lines = ["The following verification checks FAILED:", ""]
        for result in failed_results:
            lines.append(f"### {result.check_name} (exit code {result.exit_code})")
            if result.stderr:
                lines.append(f"```\n{result.stderr[:1000]}\n```")
            if result.stdout:
                lines.append(f"Output:\n```\n{result.stdout[:500]}\n```")
            lines.append("")

        return "\n".join(lines)

    def write_verification_report(
        self, task_id: str, results: List[VerificationResult], retry_ctx: Optional[RetryContext] = None
    ) -> Path:
        """写入验证报告文件

        Args:
            task_id: Task ID
            results: 验证结果列表
            retry_ctx: 重试上下文

        Returns:
            报告文件路径
        """
        report_file = self.workdir / ".lingflow" / f"{task_id}-VERIFY.md"

        lines = [
            f"# Verification Report: {task_id}",
            "",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        if retry_ctx:
            lines.append(f"Attempts: {retry_ctx.attempt}/{retry_ctx.max_retries}")
            lines.append("")

        all_passed = all(r.passed for r in results)
        lines.append(f"## Overall: {'PASS' if all_passed else 'FAIL'}")
        lines.append("")

        lines.append("## Checks")
        lines.append("")
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"### {result.check_name}: {status}")
            lines.append(f"- Command: `{result.command}`")
            lines.append(f"- Exit code: {result.exit_code}")
            lines.append(f"- Time: {result.execution_time:.2f}s")
            if result.stdout:
                lines.append(f"- Stdout:\n```\n{result.stdout[:500]}\n```")
            if result.stderr:
                lines.append(f"- Stderr:\n```\n{result.stderr[:500]}\n```")
            lines.append("")

        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Verification report written: {report_file}")
        return report_file
