"""
LingFlow Phase 5: Ruff适配器

Ruff是一个极速的Python linter，用Rust编写。
"""

import json
import subprocess
import re
from typing import List, Dict, Any, Optional
import logging

from lingflow.self_optimizer.phase5.models import (
    AIFeedback,
    FeedbackSource,
    FeedbackSeverity,
    FeedbackCategory,
)
from lingflow.self_optimizer.phase5.adapters.base_adapter import AIToolAdapter


logger = logging.getLogger(__name__)


class RuffAdapter(AIToolAdapter):
    """Ruff适配器

    Ruff是一个极速的Python linter，用Rust编写。
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.tool_name = "ruff"
        self.select = self.config.get("select", ["F", "E", "W"])
        self.ignore = self.config.get("ignore", [])
        self.fix = self.config.get("fix", False)

    def check_available(self) -> bool:
        """检查Ruff是否可用"""
        try:
            result = self._run_command(["ruff", "--version"], timeout=10)
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_version(self) -> Optional[str]:
        """获取Ruff版本"""
        try:
            result = self._run_command(["ruff", "--version"], timeout=10)
            if result.returncode == 0:
                # 解析版本: "ruff 0.1.0"
                match = re.search(r"ruff (\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def _run_scan_impl(self, target_path: str, **kwargs) -> List[AIFeedback]:
        """运行Ruff扫描"""
        cmd = [
            "ruff",
            "check",
            "--output-format=json",
            "--no-fix",
            target_path
        ]

        # 添加select选项
        if self.select:
            cmd.extend(["--select", ",".join(self.select)])

        # 添加ignore选项
        if self.ignore:
            cmd.extend(["--ignore", ",".join(self.ignore)])

        try:
            result = self._run_command(cmd)
            return self._parse_ruff_output(result.stdout, target_path)
        except Exception as e:
            logger.error(f"Ruff scan failed: {e}")
            return []

    def _parse_ruff_output(self, output: str, target_path: str = None) -> List[AIFeedback]:
        """解析Ruff输出

        Args:
            output: Ruff JSON输出
            target_path: 目标路径（可选）

        Returns:
            反馈列表
        """
        try:
            data = json.loads(output)
            if not isinstance(data, list):
                return []

            feedback_list = []
            for result in data:
                try:
                    # Ruff的location对象
                    location = result.get("location", {})

                    feedback = AIFeedback(
                        id=self._generate_feedback_id(),
                        source=FeedbackSource.RUFF,
                        rule_id=result.get("code", ""),
                        message=self._format_ruff_message(result),
                        category=self._parse_category(
                            result.get("code", ""),
                            result.get("message", ""),
                            {}
                        ),
                        severity=self._parse_ruff_severity(result),
                        file_path=location.get("path", ""),
                        line_no=location.get("row", 0),
                        end_line_no=location.get("end_row", 0),
                        column_no=location.get("column", 0),
                        end_column_no=location.get("end_column", 0),
                        code_snippet=self._extract_ruff_snippet(result),
                        suggestion=self._extract_ruff_fix(result),
                        metadata={
                            "tags": result.get("tags", []),
                            "url": result.get("url", None)
                        }
                    )
                    feedback_list.append(feedback)
                except Exception as e:
                    logger.warning(f"Failed to parse Ruff result: {e}")
                    continue

            return feedback_list
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ruff JSON output: {e}")
            return []

    def _format_ruff_message(self, result: Dict[str, Any]) -> str:
        """格式化Ruff消息

        Args:
            result: Ruff结果

        Returns:
            格式化的消息
        """
        message = result.get("message", "")
        code = result.get("code", "")
        if code:
            return f"[{code}] {message}"
        return message

    def _parse_ruff_severity(self, result: Any) -> FeedbackSeverity:
        """解析Ruff严重程度

        Args:
            result: Ruff结果（可以是字典或错误码字符串）

        Returns:
            FeedbackSeverity枚举
        """
        # 支持直接传入错误码字符串（用于测试）
        if isinstance(result, str):
            code = result
        else:
            code = result.get("code", "")

        # Ruff使用错误码前缀来判断严重性
        # E9开头的是严重错误
        # S开头的是安全相关的，也是高严重性
        # E, W, F开头的是普通警告或错误，中等严重性
        if code.startswith("E9") or code.startswith("S"):
            return FeedbackSeverity.HIGH
        elif code.startswith("E") or code.startswith("W") or code.startswith("F"):
            return FeedbackSeverity.MEDIUM
        else:
            return FeedbackSeverity.LOW

    def _extract_ruff_snippet(self, result: Dict[str, Any]) -> str:
        """提取Ruff代码片段

        Args:
            result: Ruff结果

        Returns:
            代码片段
        """
        # Ruff JSON输出不包含代码片段
        return ""

    def _extract_ruff_fix(self, result: Dict[str, Any]) -> Optional[str]:
        """提取Ruff修复建议

        Args:
            result: Ruff结果

        Returns:
            修复建议，如果没有则返回None
        """
        # Ruff的自动修复需要单独运行ruff --fix
        return None
