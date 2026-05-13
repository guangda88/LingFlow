"""
lingflow Phase 5: AI工具适配器基类

定义所有适配器的通用接口和基础功能。
"""

import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from lingflow.self_optimizer.phase5.models import (
    AIFeedback,
    FeedbackCategory,
    FeedbackSeverity,
)

logger = logging.getLogger(__name__)


class AIToolAdapter:
    """AI工具适配器基类

    定义所有适配器的通用接口和基础功能。
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化适配器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.enabled = self.config.get("enabled", True)
        self.timeout = self.config.get("timeout", 300)
        self.max_issues = self.config.get("max_issues", 1000)

    def check_available(self) -> bool:
        """检查工具是否可用

        Returns:
            工具是否安装并可用
        """
        raise NotImplementedError

    def get_version(self) -> Optional[str]:
        """获取工具版本

        Returns:
            版本字符串，如果无法获取则返回None
        """
        return None

    def run_scan(self, target_path: str, **kwargs) -> List[AIFeedback]:
        """运行扫描

        Args:
            target_path: 目标路径
            **kwargs: 额外参数

        Returns:
            反馈列表
        """
        if not self.enabled:
            logger.debug(f"{self.name} is disabled, skipping scan")
            return []

        if not self.check_available():
            logger.warning(f"{self.name} is not available")
            return []

        logger.info(f"Running {self.name} scan on {target_path}")
        start_time = datetime.now()

        try:
            result = self._run_scan_impl(target_path, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"{self.name} scan completed in {duration:.2f}s, " f"found {len(result)} issues")
            return result[: self.max_issues]
        except Exception as e:
            logger.error(f"{self.name} scan failed: {e}")
            return []

    def _run_scan_impl(self, target_path: str, **kwargs) -> List[AIFeedback]:
        """实际扫描实现（子类实现）

        Args:
            target_path: 目标路径
            **kwargs: 额外参数

        Returns:
            反馈列表
        """
        raise NotImplementedError

    def _run_command(
        self, command: List[str], cwd: Optional[str] = None, timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        """运行命令

        Args:
            command: 命令列表
            cwd: 工作目录
            timeout: 超时时间

        Returns:
            命令执行结果
        """
        timeout = timeout or self.timeout
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return result

    def _generate_feedback_id(self) -> str:
        """生成反馈ID

        Returns:
            唯一ID
        """
        return f"{self.name.lower()}_{datetime.now().timestamp()}"

    def _parse_severity(self, severity_str) -> FeedbackSeverity:
        """解析严重程度字符串

        Args:
            severity_str: 严重程度字符串或枚举

        Returns:
            FeedbackSeverity枚举
        """
        # 如果已经是枚举，直接返回
        if isinstance(severity_str, FeedbackSeverity):
            return severity_str

        severity_map = {
            "error": FeedbackSeverity.HIGH,
            "warning": FeedbackSeverity.MEDIUM,
            "info": FeedbackSeverity.INFO,
            "critical": FeedbackSeverity.CRITICAL,
            "major": FeedbackSeverity.HIGH,
            "minor": FeedbackSeverity.LOW,
            "blocker": FeedbackSeverity.CRITICAL,
        }
        severity_lower = severity_str.lower()
        return severity_map.get(severity_lower, FeedbackSeverity.MEDIUM)

    def _parse_category(self, rule_id: str, message: str, metadata: Dict[str, Any]) -> FeedbackCategory:
        """解析反馈类别

        Args:
            rule_id: 规则ID
            message: 消息
            metadata: 元数据

        Returns:
            FeedbackCategory枚举
        """
        # 基于规则ID和消息推断类别
        rule_lower = rule_id.lower() if rule_id else ""
        msg_lower = message.lower()

        # 安全相关
        security_keywords = [
            "security",
            "injection",
            "xss",
            "csrf",
            "sql",
            "auth",
            "crypto",
            "cipher",
            "hash",
            "password",
            "token",
            "session",
            "eval",
            "exec",
            "shell",
        ]
        if any(kw in rule_lower or kw in msg_lower for kw in security_keywords):
            return FeedbackCategory.SECURITY

        # 性能相关
        perf_keywords = ["performance", "slow", "optimize", "inefficient"]
        if any(kw in rule_lower or kw in msg_lower for kw in perf_keywords):
            return FeedbackCategory.PERFORMANCE

        # 最佳实践
        best_practice_keywords = ["style", "convention", "pep", "lint"]
        if any(kw in rule_lower or kw in msg_lower for kw in best_practice_keywords):
            return FeedbackCategory.BEST_PRACTICE

        # Bug风险
        bug_keywords = ["bug", "error", "exception", "null", "undefined"]
        if any(kw in rule_lower or kw in msg_lower for kw in bug_keywords):
            return FeedbackCategory.BUG_RISK

        # 默认代码质量
        return FeedbackCategory.CODE_QUALITY

    def normalize_results(self, results: Union[List[Any], Dict[str, Any]]) -> List[AIFeedback]:
        """规范化不同工具的结果格式到统一的AIFeedback列表

        Args:
            results: 工具扫描结果，可以是AIFeedback列表或字典格式

        Returns:
            统一格式的AIFeedback列表
        """
        # 如果是空列表，返回空列表
        if isinstance(results, list) and not results:
            return []

        # 如果已经是AIFeedback列表，直接返回
        if isinstance(results, list) and hasattr(results[0], "rule_id"):
            return results

        # 如果是字典格式，转换为AIFeedback
        if isinstance(results, dict):
            return self._convert_dict_to_feedback(results)

        # 尝试逐个转换
        normalized = []
        for item in results if isinstance(results, list) else [results]:
            if hasattr(item, "rule_id"):  # 已经是AIFeedback类型
                normalized.append(item)
            elif isinstance(item, dict):
                normalized.append(self._convert_dict_item_to_feedback(item))
        return normalized

    def _convert_dict_to_feedback(self, result_dict: Dict[str, Any]) -> List[AIFeedback]:
        """将字典结果转换为AIFeedback列表"""

        feedback_list = []

        # 处理常见格式
        if "results" in result_dict:
            items = result_dict["results"]
        elif "issues" in result_dict:
            items = result_dict["issues"]
        elif "findings" in result_dict:
            items = result_dict["findings"]
        else:
            items = [result_dict]

        for item in items:
            if isinstance(item, dict):
                feedback_list.append(self._convert_dict_item_to_feedback(item))

        return feedback_list

    def _convert_dict_item_to_feedback(self, item: Dict[str, Any]) -> AIFeedback:
        """将单个字典项转换为AIFeedback"""
        from lingflow.self_optimizer.phase5.models import AIFeedback, FeedbackSource

        # 处理category：如果是枚举直接使用，否则解析
        category = item.get("category")
        if not isinstance(category, FeedbackCategory):
            category = self._parse_category(item.get("rule_id", ""), item.get("message", ""), item.get("metadata", {}))

        # 处理severity：如果是枚举直接使用，否则解析
        severity = item.get("severity")
        if not isinstance(severity, FeedbackSeverity):
            severity = self._parse_severity(severity or "medium")

        return AIFeedback(
            id=item.get("id", self._generate_feedback_id()),
            source=FeedbackSource.SEMGREP if "semgrep" in self.name.lower() else FeedbackSource.RUFF,
            category=category,
            severity=severity,
            rule_id=item.get("rule_id", item.get("check_id", "unknown")),
            message=item.get("message", item.get("description", "")),
            file_path=item.get("file_path", item.get("path", "")),
            line_no=item.get("line_no", item.get("line_number", item.get("line", 0))),
            column_no=item.get("column_no", item.get("column_number", item.get("col", 0))),
            end_line_no=item.get("end_line_no", item.get("end_line_number", item.get("end_line", 0))),
            end_column_no=item.get("end_column_no", item.get("end_column_number", item.get("end_col", 0))),
            code_snippet=item.get("code_snippet", item.get("snippet", None)),
            suggestion=item.get("suggestion", None),
            metadata=item.get("metadata", {}),
        )
