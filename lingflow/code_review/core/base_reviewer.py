"""
代码审查器基类 - 统一的审查接口

该模块提供了代码审查器的抽象基类，定义了标准的审查接口。
子类需要实现 review 方法来提供具体的审查逻辑。
"""

import ast
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .rule_engine import RuleEngine
from .scorer import QualityScorer
from .severity import Severity

logger = logging.getLogger(__name__)


class ReviewerError(Exception):
    """审查器异常基类"""


class FileNotFoundError(ReviewerError):
    """文件未找到异常"""


class BaseCodeReviewer(ABC):
    """
    代码审查器基类

    该类定义了代码审查的标准接口和通用功能。
    子类需要实现 review 方法来提供具体的审查逻辑。

    默认配置:
        - complexity_threshold: 圈复杂度阈值 (默认: 15)
        - max_file_lines: 单文件最大行数 (默认: 300)
        - max_class_methods: 类最大方法数 (默认: 15)
        - max_imports: 最大导入数 (默认: 20)
        - nested_loop_threshold: 嵌套循环阈值 (默认: 3)

    Examples:
        >>> class MyReviewer(BaseCodeReviewer):
        ...     def review(self, file_path: str, **kwargs):
        ...         # 实现审查逻辑
        ...         return self.review_file(Path(file_path))
    """

    # 默认配置
    DEFAULT_CONFIG = {
        "complexity_threshold": 15,
        "max_file_lines": 300,
        "max_class_methods": 15,
        "max_imports": 20,
        "nested_loop_threshold": 3,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化审查器

        Args:
            config: 审查配置字典，会与默认配置合并

        Raises:
            ReviewerError: 如果初始化失败
        """
        self.config = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)

        try:
            self.rule_engine = RuleEngine()
            self.scorer = QualityScorer()
        except Exception as e:
            raise ReviewerError(f"审查器初始化失败: {e}") from e

        logger.debug(f"审查器初始化完成，配置: {self.config}")

    @abstractmethod
    def review(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        审查单个文件

        子类必须实现此方法来提供具体的审查逻辑。

        Args:
            file_path: 文件路径字符串
            **kwargs: 额外的审查参数

        Returns:
            Dict[str, Any]: 审查结果字典，至少包含:
                - file: 文件路径
                - dimensions: 各维度审查结果
                - overall_score: 总体评分
                或者:
                - error: 错误信息（如果审查失败）
        """

    def review_directory(self, dir_path: str, **kwargs) -> Dict[str, Any]:
        """
        审查整个目录

        遍历目录中的所有 .py 文件并进行审查。

        Args:
            dir_path: 目录路径字符串
            **kwargs: 额外的审查参数

        Returns:
            Dict[str, Any]: 审查结果字典，包含:
                - reviewed_files: 已审查的文件列表
                - dimensions: 各维度汇总结果
                - overall_score: 总体评分
                - summary: 审查摘要
                - review_time: 审查时间
                或者:
                - error: 错误信息（如果目录不存在）
        """
        dir_path_obj = Path(dir_path)

        if not dir_path_obj.exists():
            return {"error": f"目录不存在: {dir_path}", "reviewed_files": [], "overall_score": 0}

        if not dir_path_obj.is_dir():
            return {"error": f"路径不是目录: {dir_path}", "reviewed_files": [], "overall_score": 0}

        # 初始化结果结构
        result = {
            "reviewed_files": [],
            "dimensions": {
                "security": {"issues": [], "suggestions": [], "score": 0},
                "bugs": {"issues": [], "suggestions": [], "score": 0},
                "code_quality": {"issues": [], "suggestions": [], "score": 0},
                "architecture": {"issues": [], "suggestions": [], "score": 0},
                "performance": {"issues": [], "suggestions": [], "score": 0},
                "maintainability": {"issues": [], "suggestions": [], "score": 0},
                "best_practices": {"issues": [], "suggestions": [], "score": 0},
            },
            "summary": "",
            "overall_score": 0,
            "review_time": datetime.now().isoformat(),
        }

        # 审查目录中的所有 Python 文件
        file_count = 0
        for file_path in dir_path_obj.rglob("*.py"):
            try:
                file_result = self.review_file(file_path, **kwargs)
                result["reviewed_files"].append(str(file_path))
                self._merge_results(result, file_result)
                file_count += 1
            except Exception as e:
                logger.error(f"审查文件 {file_path} 时出错: {e}")

        # 计算得分
        result["overall_score"] = self.scorer.calculate_score(result)

        # 生成摘要
        result["summary"] = self._generate_summary(result, file_count)

        logger.info(f"目录审查完成: {file_count} 个文件，总分: {result['overall_score']:.2f}")

        # 结论验证 — 审查结论必须有可证伪证据
        if "conclusion" in result:
            from lingflow.hooks.conclusion_verification_hook import get_conclusion_hook

            check = get_conclusion_hook().verify(
                conclusion=result["conclusion"],
                disprove_evidence=result.get("disprove_evidence"),
            )
            if not check.passed:
                logger.warning(f"Code review conclusion unverified: {result['conclusion'][:100]}")

        return result

    def review_file(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """
        审查单个文件 - 内部实现

        该方法处理文件读取、AST解析和规则执行。

        Args:
            file_path: 文件路径对象
            **kwargs: 额外的审查参数

        Returns:
            Dict[str, Any]: 审查结果字典
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # 检查文件长度
            if len(lines) > self.config.get("max_file_lines", 300):
                logger.warning(f"文件过长: {file_path} ({len(lines)} 行)")

            # 解析 AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return self._create_syntax_error_result(file_path, e)

            # 运行规则引擎
            issues = self.rule_engine.run_rules(content, tree, file_path)

            # 组织结果
            result = self._organize_results(issues, file_path)

        except Exception as e:
            logger.error(f"审查文件 {file_path} 时出错: {e}")
            return self._create_error_result(file_path, str(e))

        return result

    def _create_syntax_error_result(self, file_path: Path, error: SyntaxError) -> Dict:
        """
        创建语法错误结果

        Args:
            file_path: 文件路径
            error: 语法错误异常

        Returns:
            Dict: 包含语法错误信息的结果字典
        """
        error_msg = f"语法错误: {error.msg} (行 {error.lineno})"
        if error.text:
            error_msg += f": {error.text.strip()}"

        return {
            "file": str(file_path),
            "code_quality": {
                "issues": [{"file": str(file_path), "issue": error_msg, "severity": "critical", "line": error.lineno or 0}],
                "suggestions": [],
                "score": 0,
            },
            "security": {"issues": [], "suggestions": [], "score": 0},
            "bugs": {"issues": [], "suggestions": [], "score": 0},
            "architecture": {"issues": [], "suggestions": [], "score": 0},
            "performance": {"issues": [], "suggestions": [], "score": 0},
            "maintainability": {"issues": [], "suggestions": [], "score": 0},
            "best_practices": {"issues": [], "suggestions": [], "score": 0},
        }

    def _create_error_result(self, file_path: Path, error: str) -> Dict:
        """
        创建错误结果

        Args:
            file_path: 文件路径
            error: 错误信息

        Returns:
            Dict: 包含错误信息的结果字典
        """
        return {
            "error": error,
            "file": str(file_path),
            "code_quality": {"issues": [], "suggestions": [], "score": 0},
            "security": {"issues": [], "suggestions": [], "score": 0},
            "bugs": {"issues": [], "suggestions": [], "score": 0},
            "architecture": {"issues": [], "suggestions": [], "score": 0},
            "performance": {"issues": [], "suggestions": [], "score": 0},
            "maintainability": {"issues": [], "suggestions": [], "score": 0},
            "best_practices": {"issues": [], "suggestions": [], "score": 0},
        }

    def _organize_results(self, issues: List[Dict], file_path: Path) -> Dict:
        """
        将规则引擎结果组织成维度格式

        Args:
            issues: 规则引擎返回的问题列表
            file_path: 文件路径

        Returns:
            Dict: 按维度组织的结果字典
        """
        result = {
            "file": str(file_path),
            "code_quality": {"issues": [], "suggestions": [], "score": 5.0},
            "security": {"issues": [], "suggestions": [], "score": 5.0},
            "bugs": {"issues": [], "suggestions": [], "score": 5.0},
            "architecture": {"issues": [], "suggestions": [], "score": 5.0},
            "performance": {"issues": [], "suggestions": [], "score": 5.0},
            "maintainability": {"issues": [], "suggestions": [], "score": 5.0},
            "best_practices": {"issues": [], "suggestions": [], "score": 5.0},
        }

        # 分类问题
        for issue in issues:
            category = self._map_category_to_dimension(issue.get("category", "general"))
            if category in result:
                result[category]["issues"].append(
                    {
                        "file": str(file_path),
                        "issue": issue["issue"],
                        "severity": issue["severity"],
                        "line": issue.get("line", 0),
                        "rule_id": issue.get("rule_id"),
                    }
                )

                # 添加建议
                if issue.get("suggestion"):
                    result[category]["suggestions"].append(
                        {
                            "file": str(file_path),
                            "suggestion": issue["suggestion"],
                            "priority": issue.get("severity", "low"),
                        }
                    )

        return result

    def _map_category_to_dimension(self, category: str) -> str:
        """
        将规则类别映射到审查维度

        Args:
            category: 规则类别名称

        Returns:
            str: 对应的维度名称
        """
        mapping = {
            "security": "security",
            "performance": "performance",
            "code_quality": "code_quality",
            "architecture": "architecture",
        }
        return mapping.get(category, "best_practices")

    def _merge_results(self, target: Dict, source: Dict) -> None:
        """
        合并审查结果

        将单个文件的审查结果合并到总体结果中。

        Args:
            target: 目标结果字典（包含dimensions键）
            source: 源结果字典（可能包含dimensions键或直接包含维度键）
        """
        # 检查source的结构
        source_dimensions = source.get("dimensions", source)

        for dimension in target["dimensions"]:
            if dimension in source_dimensions:
                target["dimensions"][dimension]["issues"].extend(source_dimensions[dimension].get("issues", []))
                target["dimensions"][dimension]["suggestions"].extend(source_dimensions[dimension].get("suggestions", []))

    def _generate_summary(self, result: Dict, file_count: int) -> str:
        """
        生成审查摘要

        Args:
            result: 审查结果字典
            file_count: 审查的文件数量

        Returns:
            str: 摘要文本
        """
        score = result.get("overall_score", 0)
        grade = self.scorer.get_score_grade(score)
        emoji = self.scorer.get_score_emoji(score)

        total_issues = sum(len(d.get("issues", [])) for d in result.get("dimensions", {}).values())

        return f"""审查了 {file_count} 个文件
总体评分: {score:.2f}/5.0 {emoji} ({grade}级)
发现问题: {total_issues} 个"""

    def get_rule_engine(self) -> RuleEngine:
        """
        获取规则引擎

        Returns:
            RuleEngine: 规则引擎实例
        """
        return self.rule_engine

    def add_custom_rule(
        self, rule_id: str, name: str, category: str, check_func: callable, severity: Severity, suggestion_template: str
    ) -> None:
        """
        添加自定义规则

        Args:
            rule_id: 规则唯一标识符
            name: 规则名称
            category: 规则类别
            check_func: 检查函数
            severity: 严重程度
            suggestion_template: 建议模板
        """
        from .rule_engine import Rule

        rule = Rule(
            id=rule_id,
            name=name,
            category=category,
            check_func=check_func,
            severity=severity,
            suggestion_template=suggestion_template,
        )
        self.rule_engine.register_rule(rule)
        logger.debug(f"已注册自定义规则: {rule_id}")

    def enable_rule(self, rule_id: str) -> None:
        """
        启用规则

        Args:
            rule_id: 规则ID
        """
        self.rule_engine.enable_rule(rule_id)

    def disable_rule(self, rule_id: str) -> None:
        """
        禁用规则

        Args:
            rule_id: 规则ID
        """
        self.rule_engine.disable_rule(rule_id)
