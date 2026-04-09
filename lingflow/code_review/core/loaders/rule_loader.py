"""规则加载器模块

提供规则的加载、注册和管理功能。
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..rules.models import Rule, RuleValidationError
from ..rules.severity import Severity

logger = logging.getLogger(__name__)


class RuleLoader:
    """规则加载器

    从文件系统或代码中加载规则。
    """

    def __init__(self):
        """初始化规则加载器"""
        self._rules: Dict[str, Rule] = {}

    def load_from_file(self, file_path: Path) -> List[Rule]:
        """从文件加载规则

        Args:
            file_path: 规则文件路径（JSON格式）

        Returns:
            规则列表

        Raises:
            FileNotFoundError: 文件不存在
            RuleValidationError: 规则验证失败
        """
        if not file_path.exists():
            raise FileNotFoundError(f"规则文件不存在: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise RuleValidationError(f"规则文件格式错误: {e}")

        rules = []
        for rule_data in data.get("rules", []):
            rule = self._parse_rule(rule_data)
            if rule:
                rules.append(rule)

        return rules

    def load_from_directory(self, directory: Path) -> List[Rule]:
        """从目录加载所有规则文件

        Args:
            directory: 规则目录

        Returns:
            规则列表
        """
        rules: list[Rule] = []

        if not directory.exists():
            logger.warning(f"规则目录不存在: {directory}")
            return rules

        for file_path in directory.glob("*.json"):
            try:
                file_rules = self.load_from_file(file_path)
                rules.extend(file_rules)
            except Exception as e:
                logger.error(f"加载规则文件失败 {file_path}: {e}")

        return rules

    def register_rule(self, rule: Rule) -> None:
        """注册规则

        Args:
            rule: 规则对象

        Raises:
            RuleValidationError: 规则无效
        """
        if not rule.validate():
            raise RuleValidationError(f"规则验证失败: {rule.id}")

        self._rules[rule.id] = rule
        logger.debug(f"注册规则: {rule.id}")

    def register_rules(self, rules: List[Rule]) -> None:
        """批量注册规则

        Args:
            rules: 规则列表
        """
        for rule in rules:
            try:
                self.register_rule(rule)
            except RuleValidationError as e:
                logger.error(f"规则注册失败: {e}")

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取规则

        Args:
            rule_id: 规则ID

        Returns:
            规则对象，不存在返回None
        """
        return self._rules.get(rule_id)

    def get_all_rules(self) -> Dict[str, Rule]:
        """获取所有规则

        Returns:
            规则字典
        """
        return self._rules.copy()

    def get_rules_by_category(self, category: str) -> List[Rule]:
        """按类别获取规则

        Args:
            category: 规则类别

        Returns:
            规则列表
        """
        return [rule for rule in self._rules.values() if rule.category == category and rule.enabled]

    def enable_rule(self, rule_id: str) -> bool:
        """启用规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功
        """
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功
        """
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = False
            return True
        return False

    def _parse_rule(self, data: Dict[str, Any]) -> Optional[Rule]:
        """解析规则数据

        Args:
            data: 规则数据字典

        Returns:
            规则对象
        """
        try:
            # 创建检查函数（简化版本）
            check_func = self._create_check_func(data)

            rule = Rule(
                id=data["id"],
                name=data["name"],
                category=data.get("category", "general"),
                check_func=check_func,
                severity=Severity(data.get("severity", "medium")),
                suggestion_template=data.get("suggestion", ""),
                enabled=data.get("enabled", True),
                metadata=data.get("metadata", {}),
            )

            return rule

        except Exception as e:
            logger.error(f"解析规则失败: {e}")
            return None

    def _create_check_func(self, data: Dict[str, Any]) -> Callable:
        """创建检查函数

        Args:
            data: 规则数据

        Returns:
            检查函数
        """
        # 简化版本：基于模式匹配
        pattern = data.get("pattern")

        if pattern:
            import re

            compiled_pattern = re.compile(pattern)

            def check_func(content, tree, file_path):
                if compiled_pattern.search(content):
                    return data.get("message", "匹配到模式")
                return None

            return check_func

        # 默认函数
        def default_check(content, tree, file_path):
            return None

        return default_check


class RuleRegistry:
    """规则注册表

    全局单例，管理所有规则。
    """

    _instance: Optional["RuleRegistry"] = None
    _loader: Optional[RuleLoader] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loader = RuleLoader()
        return cls._instance

    @property
    def loader(self) -> RuleLoader:
        """获取规则加载器"""
        return self._loader


def get_registry() -> RuleRegistry:
    """获取全局规则注册表"""
    return RuleRegistry()
