"""Carbonyl E2E 测试运行器 (已弃用)

.. deprecated::
    推荐直接使用 Chrome DevTools MCP 服务器，无需 Python 包装。

    在 Claude Code 中直接调用 MCP 工具即可，无需额外代码。

保留此文件仅作为架构参考。
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class CarbonylTestConfig:
    """Carbonyl 测试配置"""

    carbonyl_path: str = "carbonyl"
    use_docker: bool = False
    default_timeout: int = 30
    screenshot_dir: str = "/tmp/carbonyl_screenshots"
    headless: bool = True


@dataclass
class TestResult:
    """测试结果"""

    name: str
    passed: bool
    duration: float
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CarbonylRunner:
    """Carbonyl 浏览器运行器

    提供在终端中运行 Chromium 浏览器的能力，用于 E2E 测试。
    """

    def __init__(self, config: Optional[CarbonylTestConfig] = None):
        """初始化运行器

        Args:
            config: 测试配置
        """
        self.config = config or CarbonylTestConfig()
        self._ensure_carbonyl()

    def _ensure_carbonyl(self) -> bool:
        """确保 Carbonyl 可用"""
        if self._find_carbonyl():
            return True

        # 尝试使用 Docker
        try:
            subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
            self.config.use_docker = True
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _find_carbonyl(self) -> bool:
        """查找 Carbonyl 二进制"""
        candidates = [
            self.config.carbonyl_path,
            "/usr/local/bin/carbonyl",
            os.path.expanduser("~/.local/bin/carbonyl"),
        ]

        for candidate in candidates:
            try:
                result = subprocess.run(["which", candidate], capture_output=True, timeout=5)
                if result.returncode == 0:
                    self.config.carbonyl_path = candidate
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        return False

    def run_carbonyl(
        self, url: str, args: Optional[List[str]] = None, capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """运行 Carbonyl

        Args:
            url: 要访问的 URL
            args: 额外参数
            capture_output: 是否捕获输出

        Returns:
            子进程结果
        """
        if self.config.use_docker:
            cmd = ["docker", "run", "--rm", "-v", f"{os.getcwd()}:/app:ro", "fathyb/carbonyl", url]
        else:
            cmd = [self.config.carbonyl_path, url]

        if args:
            cmd.extend(args)

        return subprocess.run(cmd, capture_output=capture_output, timeout=self.config.default_timeout)

    def take_screenshot(self, url: str, output_path: Optional[str] = None) -> TestResult:
        """截图

        Args:
            url: 要截图的 URL
            output_path: 输出文件路径

        Returns:
            测试结果
        """
        if not output_path:
            Path(self.config.screenshot_dir).mkdir(parents=True, exist_ok=True)
            output_path = str(Path(self.config.screenshot_dir) / f"{self._sanitize_url(url)}.png")

        start_time = time.time()

        try:
            result = self.run_carbonyl(url, capture_output=True)
            duration = time.time() - start_time

            # 检查是否成功
            success = result.returncode == 0

            return TestResult(
                name="screenshot",
                passed=success,
                duration=duration,
                screenshot_path=output_path if success else None,
                error=result.stderr.decode() if result.stderr else None,
            )
        except subprocess.TimeoutExpired:
            return TestResult(name="screenshot", passed=False, duration=time.time() - start_time, error="超时")
        except Exception as e:
            return TestResult(name="screenshot", passed=False, duration=0, error=str(e))

    def verify_page_load(self, url: str) -> TestResult:
        """验证页面加载

        Args:
            url: 要验证的 URL

        Returns:
            测试结果
        """
        start_time = time.time()

        try:
            result = self.run_carbonyl(url, capture_output=True)
            duration = time.time() - start_time

            success = result.returncode == 0
            has_errors = False

            # 检查输出中的错误
            if result.stderr:
                stderr = result.stderr.decode()
                has_errors = "ERROR" in stderr or "FAIL" in stderr

            return TestResult(
                name="page_load",
                passed=success and not has_errors,
                duration=duration,
                error=result.stderr.decode() if result.stderr else None,
                metadata={"url": url, "has_stderr_errors": has_errors},
            )
        except subprocess.TimeoutExpired:
            return TestResult(name="page_load", passed=False, duration=time.time() - start_time, error="超时")

    def check_console_errors(self, url: str) -> TestResult:
        """检查控制台错误

        Args:
            url: 要检查的 URL

        Returns:
            测试结果
        """
        start_time = time.time()

        try:
            result = self.run_carbonyl(url, capture_output=True)
            duration = time.time() - start_time

            errors = []
            if result.stderr:
                stderr = result.stderr.decode()
                for line in stderr.split("\n"):
                    if "ERROR" in line or "WARN" in line:
                        errors.append(line.strip())

            return TestResult(
                name="console_check",
                passed=len(errors) == 0,
                duration=duration,
                metadata={"error_count": len(errors), "errors": errors[:10]},  # 只保存前10个错误
            )
        except subprocess.TimeoutExpired:
            return TestResult(name="console_check", passed=False, duration=time.time() - start_time, error="超时")

    def run_web_test(self, url: str, tests: List[str] = None) -> List[TestResult]:
        """运行 Web 测试套件

        Args:
            url: 要测试的 URL
            tests: 要运行的测试列表

        Returns:
            测试结果列表
        """
        if tests is None:
            tests = ["screenshot", "page_load", "console_check"]

        results = []

        for test_name in tests:
            if test_name == "screenshot":
                results.append(self.take_screenshot(url))
            elif test_name == "page_load":
                results.append(self.verify_page_load(url))
            elif test_name == "console_check":
                results.append(self.check_console_errors(url))

        return results

    @staticmethod
    def _sanitize_url(url: str) -> str:
        """将 URL 转换为安全的文件名"""
        import re

        # 移除协议
        url = url.replace("https://", "").replace("http://", "")
        # 替换特殊字符
        url = re.sub(r"[^\w\-_.]", "_", url)
        # 限制长度
        return url[:50]

    def get_status(self) -> Dict[str, Any]:
        """获取运行器状态"""
        return {
            "carbonyl_found": self._find_carbonyl(),
            "using_docker": self.config.use_docker,
            "carbonyl_path": self.config.carbonyl_path,
            "screenshot_dir": self.config.screenshot_dir,
            "default_timeout": self.config.default_timeout,
        }


# 便捷函数
def get_carbonyl_runner() -> CarbonylRunner:
    """获取 Carbonyl 运行器单例"""
    return CarbonylRunner()


def run_carbonyl_test(url: str, test: str = "verify") -> TestResult:
    """快速运行 Carbonyl 测试

    Args:
        url: 要测试的 URL
        test: 测试类型

    Returns:
        测试结果
    """
    runner = get_carbonyl_runner()

    if test == "screenshot":
        return runner.take_screenshot(url)
    elif test == "verify":
        return runner.verify_page_load(url)
    elif test == "console":
        return runner.check_console_errors(url)
    else:
        return TestResult(name="unknown", passed=False, duration=0, error=f"未知测试类型: {test}")
