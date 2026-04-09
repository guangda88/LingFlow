"""
基类审查器单元测试

测试 BaseCodeReviewer 类的功能
"""

import ast
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from lingflow.code_review.core.base_reviewer import BaseCodeReviewer
from lingflow.code_review.core.severity import Severity


class MockCodeReviewer(BaseCodeReviewer):
    """用于测试的审查器实现"""

    def review(self, file_path: str, **kwargs):
        """实现抽象方法"""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"文件不存在: {file_path}"}

        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            issues = self.rule_engine.run_rules(content, tree, path)

            result = {
                "file": str(path),
                "dimensions": {
                    "security": {"issues": [], "suggestions": [], "score": 5.0},
                    "performance": {"issues": [], "suggestions": [], "score": 5.0},
                    "code_quality": {"issues": [], "suggestions": [], "score": 5.0},
                },
                "overall_score": 5.0,
            }

            for issue in issues:
                category = self._map_category_to_dimension(issue["category"])
                if category in result["dimensions"]:
                    result["dimensions"][category]["issues"].append(issue)
                    result["dimensions"][category]["score"] -= 1

            return result

        except Exception as e:
            return {"error": str(e)}


class TestBaseCodeReviewer:
    """BaseCodeReviewer 类测试"""

    def test_initialization_default_config(self):
        """测试使用默认配置初始化"""
        reviewer = MockCodeReviewer()
        assert reviewer.config is not None
        assert "complexity_threshold" in reviewer.config
        assert "max_file_lines" in reviewer.config

    def test_initialization_custom_config(self):
        """测试使用自定义配置初始化"""
        custom_config = {
            "complexity_threshold": 20,
            "max_file_lines": 500,
        }
        reviewer = MockCodeReviewer(config=custom_config)
        assert reviewer.config["complexity_threshold"] == 20
        assert reviewer.config["max_file_lines"] == 500

    def test_rule_engine_initialized(self):
        """测试规则引擎已初始化"""
        reviewer = MockCodeReviewer()
        assert reviewer.rule_engine is not None
        assert reviewer.scorer is not None

    def test_get_rule_engine(self):
        """测试获取规则引擎"""
        reviewer = MockCodeReviewer()
        engine = reviewer.get_rule_engine()
        assert engine is not None
        assert hasattr(engine, "rules")

    def test_enable_rule(self):
        """测试启用规则"""
        reviewer = MockCodeReviewer()
        reviewer.enable_rule("SEC001")
        assert reviewer.rule_engine.rules["SEC001"].enabled is True

    def test_disable_rule(self):
        """测试禁用规则"""
        reviewer = MockCodeReviewer()
        reviewer.disable_rule("SEC001")
        assert reviewer.rule_engine.rules["SEC001"].enabled is False


class TestReviewFile:
    """review_file 方法测试"""

    def setup_method(self):
        """设置测试环境"""
        self.reviewer = MockCodeReviewer()

    def test_review_file_success(self, tmp_path):
        """测试成功审查文件"""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): pass")

        result = self.reviewer.review_file(test_file)
        # 结果包含各个维度的键（在顶层）
        assert "security" in result
        assert "performance" in result

    def test_review_file_syntax_error(self, tmp_path):
        """测试审查有语法错误的文件"""
        test_file = tmp_path / "bad_syntax.py"
        test_file.write_text("def foo(\n")  # 不完整的代码

        result = self.reviewer.review_file(test_file)
        assert "code_quality" in result
        # 应该有语法错误问题
        issues = result.get("code_quality", {}).get("issues", [])
        assert any("语法" in str(issue.get("issue", "")) for issue in issues)

    def test_review_nonexistent_file(self, tmp_path):
        """测试审查不存在的文件"""
        result = self.reviewer.review_file(tmp_path / "nonexistent.py")
        assert "error" in result


class TestReviewDirectory:
    """review_directory 方法测试"""

    def setup_method(self):
        """设置测试环境"""
        self.reviewer = MockCodeReviewer()

    def test_review_directory_success(self, tmp_path):
        """测试成功审查目录"""
        # 创建测试文件
        (tmp_path / "test1.py").write_text("def foo(): pass")
        (tmp_path / "test2.py").write_text("x = 1")
        (tmp_path / "readme.md").write_text("# README")

        result = self.reviewer.review_directory(str(tmp_path))
        assert "reviewed_files" in result
        assert len(result["reviewed_files"]) == 2  # 只审查 .py 文件

    def test_review_nonexistent_directory(self):
        """测试审查不存在的目录"""
        result = self.reviewer.review_directory("/nonexistent/directory")
        assert "error" in result

    def test_review_directory_empty(self, tmp_path):
        """测试审查空目录"""
        result = self.reviewer.review_directory(str(tmp_path))
        assert "reviewed_files" in result
        assert len(result["reviewed_files"]) == 0


class TestCategoryMapping:
    """_map_category_to_dimension 方法测试"""

    def setup_method(self):
        """设置测试环境"""
        self.reviewer = MockCodeReviewer()

    def test_map_security(self):
        """测试映射 security 类别"""
        dimension = self.reviewer._map_category_to_dimension("security")
        assert dimension == "security"

    def test_map_performance(self):
        """测试映射 performance 类别"""
        dimension = self.reviewer._map_category_to_dimension("performance")
        assert dimension == "performance"

    def test_map_unknown(self):
        """测试映射未知类别"""
        dimension = self.reviewer._map_category_to_dimension("unknown")
        assert dimension == "best_practices"


class TestOrganizeResults:
    """_organize_results 方法测试"""

    def setup_method(self):
        """设置测试环境"""
        self.reviewer = MockCodeReviewer()

    def test_organize_empty_issues(self, tmp_path):
        """测试组织空问题列表"""
        result = self.reviewer._organize_results([], tmp_path / "test.py")
        # 检查各个维度的issues都是空的（跳过'file'键）
        for key in result:
            if key != "file":
                assert len(result[key]["issues"]) == 0

    def test_organize_with_issues(self, tmp_path):
        """测试组织有问题的结果"""
        issues = [
            {
                "category": "security",
                "issue": "Test security issue",
                "severity": "high",
                "line": 10,
                "rule_id": "SEC001",
            }
        ]

        result = self.reviewer._organize_results(issues, tmp_path / "test.py")
        assert len(result["security"]["issues"]) == 1
        assert result["security"]["issues"][0]["issue"] == "Test security issue"


class TestMergeResults:
    """_merge_results 方法测试"""

    def setup_method(self):
        """设置测试环境"""
        self.reviewer = MockCodeReviewer()

    def test_merge_results(self):
        """测试合并结果"""
        target = {
            "dimensions": {
                "security": {"issues": [], "suggestions": []},
                "performance": {"issues": [], "suggestions": []},
                "code_quality": {"issues": [], "suggestions": []},
            }
        }

        source = {
            "security": {
                "issues": [{"issue": "Security issue"}],
                "suggestions": [],
            },
            "performance": {
                "issues": [],
                "suggestions": [],
            },
        }

        self.reviewer._merge_results(target, source)
        assert len(target["dimensions"]["security"]["issues"]) == 1


class TestGenerateSummary:
    """_generate_summary 方法测试"""

    def setup_method(self):
        """设置测试环境"""
        self.reviewer = MockCodeReviewer()

    def test_generate_summary(self):
        """测试生成摘要"""
        result = {
            "overall_score": 4.5,
            "dimensions": {
                "security": {"issues": [], "suggestions": []},
                "performance": {"issues": [], "suggestions": []},
            },
        }

        summary = self.reviewer._generate_summary(result, 5)
        assert "5" in summary
        assert "4.5" in summary


class TestAddCustomRule:
    """add_custom_rule 方法测试"""

    def setup_method(self):
        """设置测试环境"""
        self.reviewer = MockCodeReviewer()

    def test_add_custom_rule(self):
        """测试添加自定义规则"""

        def custom_check(content, tree, path):
            return "Custom issue"

        self.reviewer.add_custom_rule(
            rule_id="CUSTOM001",
            name="custom_rule",
            category="test",
            check_func=custom_check,
            severity=Severity.MEDIUM,
            suggestion_template="Custom suggestion",
        )

        assert "CUSTOM001" in self.reviewer.rule_engine.rules
