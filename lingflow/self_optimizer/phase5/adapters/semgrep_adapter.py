"""
LingFlow Phase 5: Semgrep适配器

Semgrep是一个快速的静态分析工具，支持多种语言和自定义规则。
"""

import json
import logging
import re
import subprocess
from typing import Any, Dict, List, Optional

from lingflow.self_optimizer.phase5.adapters.base_adapter import AIToolAdapter
from lingflow.self_optimizer.phase5.models import (
    AIFeedback,
    FeedbackSource,
)

logger = logging.getLogger(__name__)


class SemgrepAdapter(AIToolAdapter):
    """Semgrep适配器

    Semgrep是一个快速的静态分析工具，支持多种语言和自定义规则。
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.tool_name = "semgrep"
        self.rules = self.config.get("rules", ["auto"])
        self.config_file = self.config.get("config_file")

    def check_available(self) -> bool:
        """检查Semgrep是否可用"""
        try:
            result = self._run_command(["semgrep", "--version"], timeout=10)
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_version(self) -> Optional[str]:
        """获取Semgrep版本"""
        try:
            result = self._run_command(["semgrep", "--version"], timeout=10)
            if result.returncode == 0:
                # 解析版本: "semgrep version: 1.0.0"
                match = re.search(r"version:\s*(\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def _run_scan_impl(self, target_path: str, **kwargs) -> List[AIFeedback]:
        """运行Semgrep扫描"""
        cmd = ["semgrep", "--json", "--no-git-ignore", "--verbose"]

        # 添加配置
        if self.config_file:
            cmd.extend(["--config", self.config_file])
        elif self.rules:
            for rule in self.rules:
                cmd.extend(["--config", rule])

        # 添加目标路径
        cmd.append(str(target_path))

        try:
            result = self._run_command(cmd)
            return self._parse_semgrep_output(result.stdout, target_path)
        except Exception as e:
            logger.error(f"Semgrep scan failed: {e}")
            return []

    def _parse_semgrep_output(self, output: str, target_path: str) -> List[AIFeedback]:
        """解析Semgrep输出

        Args:
            output: Semgrep JSON输出
            target_path: 目标路径

        Returns:
            反馈列表
        """
        try:
            data = json.loads(output)
            results = data.get("results", [])

            feedback_list = []
            for result in results:
                try:
                    feedback = AIFeedback(
                        id=self._generate_feedback_id(),
                        source=FeedbackSource.SEMGREP,
                        rule_id=result.get("check_id", ""),
                        message=result.get("message", ""),
                        category=self._parse_category(
                            result.get("check_id", ""), result.get("message", ""), result.get("extra", {})
                        ),
                        severity=self._parse_severity(result.get("extra", {}).get("severity", "warning")),
                        file_path=result.get("path", ""),
                        line_no=result.get("start", {}).get("line", 0),
                        end_line_no=result.get("end", {}).get("line", 0),
                        column_no=result.get("start", {}).get("col", 0),
                        end_column_no=result.get("end", {}).get("col", 0),
                        code_snippet=self._extract_snippet(result),
                        suggestion=self._extract_suggestion(result),
                        metadata={
                            "cwe": result.get("extra", {}).get("metadata", {}).get("cwe"),
                            "owasp": result.get("extra", {}).get("metadata", {}).get("owasp"),
                            "references": result.get("extra", {}).get("metadata", {}).get("references", []),
                        },
                    )
                    feedback_list.append(feedback)
                except Exception as e:
                    logger.warning(f"Failed to parse Semgrep result: {e}")
                    continue

            return feedback_list
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Semgrep JSON output: {e}")
            return []

    def _extract_snippet(self, result: Dict[str, Any]) -> str:
        """提取代码片段

        Args:
            result: 单个Semgrep结果

        Returns:
            代码片段
        """
        lines = result.get("extra", {}).get("lines", "")
        if lines:
            return lines.strip()
        return ""

    def _extract_suggestion(self, result: Dict[str, Any]) -> Optional[str]:
        """提取修复建议

        Args:
            result: 单个Semgrep结果

        Returns:
            修复建议，如果没有则返回None
        """
        fix = result.get("fix", "")
        if fix:
            return fix
        return None
