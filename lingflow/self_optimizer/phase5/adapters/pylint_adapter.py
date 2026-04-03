"""
LingFlow Phase 5: Pylint适配器

Pylint是一个Python代码分析工具，查找编程错误、代码异味和不符合规范的地方。
"""

import json
import subprocess
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from lingflow.self_optimizer.phase5.models import (
    AIFeedback,
    FeedbackSource,
    FeedbackSeverity,
)
from lingflow.self_optimizer.phase5.adapters.base_adapter import AIToolAdapter

logger = logging.getLogger(__name__)


class PylintAdapter(AIToolAdapter):
    """Pylint适配器

    Pylint是一个Python代码分析工具，查找编程错误、代码异味和不符合规范的地方。
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.tool_name = "pylint"
        self.load_plugins = self.config.get("load_plugins", [])
        self.disable = self.config.get("disable", [])

    def check_available(self) -> bool:
        """检查Pylint是否可用"""
        try:
            result = self._run_command(["pylint", "--version"], timeout=10)
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_version(self) -> Optional[str]:
        """获取Pylint版本"""
        try:
            result = self._run_command(["pylint", "--version"], timeout=10)
            if result.returncode == 0:
                # 解析版本: "pylint 2.17.0"
                match = re.search(r"pylint (\d+\.\d+\.\d+)", result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def _run_scan_impl(self, target_path: str, **kwargs) -> List[AIFeedback]:
        """运行Pylint扫描"""
        cmd = [
            "pylint",
            "--output-format=json",
            "--recursive=y",
        ]

        # 添加禁用的检查
        if self.disable:
            cmd.extend(["--disable", ",".join(self.disable)])

        # 添加插件
        for plugin in self.load_plugins:
            cmd.extend(["--load-plugins", plugin])

        # 添加目标路径
        target = Path(target_path)
        if target.is_file():
            cmd.append(str(target))
        else:
            cmd.append(str(target / "*.py"))

        try:
            result = self._run_command(cmd)
            return self._parse_pylint_output(result.stdout, target_path)
        except Exception as e:
            logger.error(f"Pylint scan failed: {e}")
            return []

    def _parse_pylint_output(self, output: str, target_path: str) -> List[AIFeedback]:
        """解析Pylint输出

        Args:
            output: Pylint JSON输出
            target_path: 目标路径

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
                    feedback = AIFeedback(
                        id=self._generate_feedback_id(),
                        source=FeedbackSource.PYLINT,
                        rule_id=result.get("message-id", ""),
                        message=result.get("msg", ""),
                        category=self._parse_category(result.get("message-id", ""), result.get("msg", ""), {}),
                        severity=self._parse_pylint_severity(result),
                        file_path=result.get("path", ""),
                        line_no=result.get("line", 0),
                        end_line_no=result.get("endLine", result.get("line", 0)),
                        column_no=result.get("column", 0),
                        code_snippet="",  # Pylint JSON不包含代码片段
                        suggestion=None,  # Pylint消息本身即是建议
                        metadata={
                            "symbol": result.get("symbol", ""),
                            "module": result.get("module", ""),
                            "obj": result.get("obj", ""),
                            "category": result.get("category", ""),
                        },
                    )
                    feedback_list.append(feedback)
                except Exception as e:
                    logger.warning(f"Failed to parse Pylint result: {e}")
                    continue

            return feedback_list
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Pylint JSON output: {e}")
            return []

    def _parse_pylint_severity(self, result: Any, msg_id: str = None) -> FeedbackSeverity:
        """解析Pylint严重程度

        Args:
            result: Pylint结果（可以是字典或类型字符串）
            msg_id: 消息ID（可选，用于兼容旧测试）

        Returns:
            FeedbackSeverity枚举
        """
        # 支持直接传入类型字符串（用于测试）
        if isinstance(result, str):
            msg_type = result
        else:
            msg_type = result.get("type", "")

        severity_map = {
            "error": FeedbackSeverity.HIGH,
            "warning": FeedbackSeverity.MEDIUM,
            "convention": FeedbackSeverity.LOW,
            "refactor": FeedbackSeverity.LOW,
            "info": FeedbackSeverity.INFO,
            "fatal": FeedbackSeverity.CRITICAL,
        }
        return severity_map.get(msg_type.lower(), FeedbackSeverity.MEDIUM)
