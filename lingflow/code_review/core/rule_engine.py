"""规则引擎 - 可配置的代码检查规则

该模块提供了可扩展的规则引擎，用于静态代码分析。
支持自定义规则注册、规则启用/禁用等功能。
"""

import ast
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from .loaders.rule_loader import RuleLoader, get_registry
from .rules.models import Rule, RuleResult, RuleNotFoundError

logger = logging.getLogger(__name__)


class RuleEngine:
    """可配置的代码审查规则引擎

    该类管理所有代码审查规则，提供规则注册、启用/禁用、执行等功能。

    Attributes:
        rules: 已注册的规则字典，键为规则ID

    Examples:
        >>> engine = RuleEngine()
        >>> result = engine.run_rules(code, tree, Path("test.py"))
        >>> engine.disable_rule("SEC001")
    """

    def __init__(self):
        """初始化规则引擎"""
        self.loader = get_registry().loader

    def register_rule(self, rule: Rule) -> None:
        """注册新规则

        Args:
            rule: 规则对象

        Raises:
            RuleValidationError: 规则验证失败
        """
        self.loader.register_rule(rule)

    def unregister_rule(self, rule_id: str) -> bool:
        """注销规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功注销
        """
        return self.loader.disable_rule(rule_id)

    def enable_rule(self, rule_id: str) -> bool:
        """启用指定规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功启用
        """
        return self.loader.enable_rule(rule_id)

    def disable_rule(self, rule_id: str) -> bool:
        """禁用指定规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功禁用
        """
        return self.loader.disable_rule(rule_id)

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取指定规则

        Args:
            rule_id: 规则ID

        Returns:
            规则对象，不存在返回None
        """
        return self.loader.get_rule(rule_id)

    def list_rules(self, category: Optional[str] = None) -> List[Rule]:
        """列出规则

        Args:
            category: 可选的类别过滤

        Returns:
            规则列表
        """
        if category:
            return self.loader.get_rules_by_category(category)

        return list(self.loader.get_all_rules().values())

    def run_rules(
        self,
        content: str,
        tree: ast.AST,
        file_path: Path
    ) -> List[RuleResult]:
        """对所有启用的规则运行检查

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            检查结果列表
        """
        results = []
        rules = self.loader.get_all_rules()

        for rule in rules.values():
            if not rule.enabled:
                continue

            try:
                result = self._run_single_rule(rule, content, tree, file_path)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"规则执行失败 {rule.id}: {e}")

        return results

    def run_rule(
        self,
        rule_id: str,
        content: str,
        tree: ast.AST,
        file_path: Path
    ) -> Optional[RuleResult]:
        """运行单个规则

        Args:
            rule_id: 规则ID
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            检查结果，如果规则未触发返回None

        Raises:
            RuleNotFoundError: 规则不存在
        """
        rule = self.loader.get_rule(rule_id)
        if not rule:
            raise RuleNotFoundError(f"规则不存在: {rule_id}")

        if not rule.enabled:
            return None

        return self._run_single_rule(rule, content, tree, file_path)

    def _run_single_rule(
        self,
        rule: Rule,
        content: str,
        tree: ast.AST,
        file_path: Path
    ) -> Optional[RuleResult]:
        """运行单个规则

        Args:
            rule: 规则对象
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            检查结果
        """
        # 执行检查函数
        message = rule.check_func(content, tree, file_path)

        if message is None:
            return None

        # 查找问题位置（简化版本）
        line, column = self._find_issue_location(content, message)

        return RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            message=message,
            suggestion=rule.suggestion_template,
            file_path=str(file_path),
            line=line,
            column=column
        )

    def _find_issue_location(
        self,
        content: str,
        message: str
    ) -> tuple[int, int]:
        """查找问题位置

        Args:
            content: 文件内容
            message: 错误消息

        Returns:
            (行号, 列号)
        """
        lines = content.split('\n')

        # 尝试从消息中提取行号
        import re
        line_match = re.search(r'line[:\s]+(\d+)', message, re.IGNORECASE)
        if line_match:
            line = int(line_match.group(1))
            return (line, 0)

        # 默认第一行
        return (1, 0)

    def load_rules_from_file(self, file_path: Path) -> int:
        """从文件加载规则

        Args:
            file_path: 规则文件路径

        Returns:
            加载的规则数量
        """
        rules = self.loader.load_from_file(file_path)
        self.loader.register_rules(rules)
        return len(rules)

    def load_rules_from_directory(self, directory: Path) -> int:
        """从目录加载规则

        Args:
            directory: 规则目录

        Returns:
            加载的规则数量
        """
        rules = self.loader.load_from_directory(directory)
        self.loader.register_rules(rules)
        return len(rules)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        rules = self.loader.get_all_rules()

        category_count = {}
        enabled_count = 0
        disabled_count = 0

        for rule in rules.values():
            category_count[rule.category] = category_count.get(rule.category, 0) + 1
            if rule.enabled:
                enabled_count += 1
            else:
                disabled_count += 1

        return {
            "total_rules": len(rules),
            "enabled_rules": enabled_count,
            "disabled_rules": disabled_count,
            "categories": category_count
        }
