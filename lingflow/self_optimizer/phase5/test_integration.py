"""
Self-Learning 闭环集成测试

测试完整的自学习闭环：扫描 → 学习 → 应用 → 反馈
"""

import os
import tempfile
from datetime import datetime

import pytest

from lingflow.self_optimizer.phase5 import (
    FeedbackCategory,
    FeedbackCollector,
    FeedbackItem,
    FeedbackLoop,
    FeedbackSeverity,
    KnowledgeBase,
    LearnedRule,
    Pattern,
    PreCommitHookGenerator,
    RuleApplier,
    RuleExtractor,
    ToolType,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_kb():
    """临时知识库"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    kb = KnowledgeBase(db_path=db_path)
    yield kb

    kb.close()
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture
def sample_rules(temp_kb):
    """添加示例规则到知识库"""
    rules = [
        LearnedRule(
            id="rule-001",
            name="Unused Import",
            description="Imported but unused symbol",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=Pattern(
                file_patterns=["*.py"],
                code_patterns=[r"^import \w+", r"^from .* import"],
                context_keywords=["import", "unused"],
                severity_distribution={"LOW": 10},
                tool_support=["ruff"],
            ),
            tools=["ruff"],
            frequency=5,
            confidence=0.85,
            quality_score=0.9,
            status="approved",
            created_at=datetime.now(),
        ),
        LearnedRule(
            id="rule-002",
            name="Line Too Long",
            description="Line exceeds maximum length",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=Pattern(
                file_patterns=["*.py"],
                code_patterns=[r".{100,}"],  # 超过100字符的行
                context_keywords=["line", "length"],
                severity_distribution={"MEDIUM": 5},
                tool_support=["pylint"],
            ),
            tools=["pylint"],
            frequency=3,
            confidence=0.7,
            quality_score=0.75,
            status="approved",
            created_at=datetime.now(),
        ),
    ]

    for rule in rules:
        temp_kb.add_rule(rule)

    return rules


@pytest.fixture
def sample_code_file(tmp_path):
    """创建包含问题的示例代码文件"""
    code = '''# This file has some issues

import os
import sys
import json  # unused import

def very_long_function_that_does_many_things_and_should_be_refactored():
    """This function is way too long and does too many things."""
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    # ... more code ...
    return x + y + z + a + b + c + d + e

def another_function():
    unused_var = 999
    return 42
'''

    file_path = tmp_path / "sample.py"
    file_path.write_text(code)

    return str(file_path)


# ============================================================================
# RuleApplier 测试
# ============================================================================


class TestRuleApplier:
    """测试规则应用器"""

    def test_check_code_with_rules(self, temp_kb, sample_rules):
        """测试使用规则检查代码"""
        applier = RuleApplier(temp_kb)

        code = """
import os
import sys
import json  # unused

def test():
    return 1
"""

        issues = applier.check_code(code, "test.py")

        # 应该检测到unused import模式
        assert len(issues) > 0

    def test_check_file(self, temp_kb, sample_rules, sample_code_file):
        """测试检查文件"""
        applier = RuleApplier(temp_kb)

        issues = applier.check_file(sample_code_file)

        assert isinstance(issues, list)
        # 可能检测到未使用变量或导入

    def test_check_directory(self, temp_kb, sample_rules, tmp_path):
        """测试检查目录"""
        applier = RuleApplier(temp_kb)

        # 创建多个测试文件
        for i in range(3):
            file_path = tmp_path / f"test_{i}.py"
            file_path.write_text(f"import unused_{i}\nprint({i})\n")

        results = applier.check_directory(str(tmp_path))

        assert isinstance(results, dict)

    def test_category_filter(self, temp_kb, sample_rules):
        """测试类别过滤"""
        applier = RuleApplier(temp_kb)

        code = "import os\nprint('hello')\n"

        # 只检查CODE_QUALITY类别
        issues = applier.check_code(code, "test.py", category=FeedbackCategory.CODE_QUALITY)

        assert isinstance(issues, list)

    def test_statistics(self, temp_kb, sample_rules):
        """测试统计功能"""
        applier = RuleApplier(temp_kb)

        stats = applier.get_statistics()
        assert "applied_count" in stats
        assert stats["applied_count"] == 0


# ============================================================================
# FeedbackCollector 测试
# ============================================================================


class TestFeedbackCollector:
    """测试反馈收集器"""

    @pytest.fixture
    def collector(self, tmp_path):
        """创建临时收集器"""
        storage_path = tmp_path / "feedback.json"
        return FeedbackCollector(str(storage_path))

    def test_record_rule_application(self, collector):
        """测试记录规则应用反馈"""
        collector.record_rule_application(
            rule_id="rule-001", file_path="test.py", line=10, accepted=True, user_feedback="Good suggestion"
        )

        # 获取规则效果
        effectiveness = collector.get_rule_effectiveness("rule-001")

        assert effectiveness["rule_id"] == "rule-001"
        assert effectiveness["total_applications"] == 1
        assert effectiveness["acceptance_rate"] == 1.0

    def test_record_application_stats(self, collector):
        """测试记录应用统计"""
        collector.record_application_stats(
            scan_id="scan-001", total_files=10, total_issues=50, fixed_issues=25, duration_seconds=5.5
        )

        feedback = collector.get_all_feedback()

        assert feedback["total_application_feedback"] == 1

    def test_get_all_feedback(self, collector):
        """测试获取所有反馈"""
        # 添加一些反馈数据
        for i in range(5):
            collector.record_rule_application(f"rule-{i}", "test.py", i, i % 2 == 0)  # 交替接受/拒绝

        feedback = collector.get_all_feedback(days=30)

        assert feedback["total_rule_feedback"] == 5
        assert "top_rules" in feedback


# ============================================================================
# FeedbackLoop 测试
# ============================================================================


class TestFeedbackLoop:
    """测试反馈循环"""

    @pytest.fixture
    def feedback_loop(self, temp_kb, tmp_path):
        """创建反馈循环实例"""
        storage_path = tmp_path / "feedback.json"
        FeedbackCollector(str(storage_path))
        return FeedbackLoop(temp_kb)

    def test_run_cycle(self, feedback_loop, sample_rules):
        """测试运行完整循环"""
        # 模拟扫描结果
        scan_results = {"test.py": [{"rule_id": "rule-001", "line": 10, "message": "Issue here"}]}

        result = feedback_loop.run_cycle(scan_id="test-scan", scan_results=scan_results, duration_seconds=1.5)

        assert result["scan_id"] == "test-scan"
        assert "application_stats" in result
        assert "quality_adjustments" in result
        assert "feedback_summary" in result

    def test_get_improvement_suggestions(self, feedback_loop):
        """测试获取改进建议"""
        suggestions = feedback_loop.get_improvement_suggestions()

        assert isinstance(suggestions, list)


# ============================================================================
# 端到端集成测试
# ============================================================================


class TestSelfLearningE2E:
    """测试自学习端到端流程"""

    def test_full_loop(self, tmp_path):
        """测试完整的学习-应用-反馈循环"""
        # 1. 创建知识库
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            kb = KnowledgeBase(db_path=db_path)

            # 2. 创建反馈数据
            feedback_items = [
                FeedbackItem(
                    tool_name="ruff",
                    tool_type=ToolType.STATIC_ANALYZER,
                    rule_id="F401",
                    rule_name="unused-import",
                    category=FeedbackCategory.CODE_QUALITY,
                    severity=FeedbackSeverity.LOW,
                    message="Unused import",
                    file_path="test.py",
                    line=1,
                    snippet="import os",
                    suggestion="Remove unused import",
                    confidence=0.9,
                )
                for _ in range(5)  # 相同规则，达到频率要求
            ]

            # 3. 提取规则
            extractor = RuleExtractor(min_frequency=3, min_confidence=0.7)
            rules = extractor.extract_rules(feedback_items)

            assert len(rules) >= 1

            # 4. 添加到知识库
            for rule in rules:
                rule.status = "approved"
                kb.add_rule(rule)

            # 5. 应用规则检查代码
            applier = RuleApplier(kb)
            code = "import os\nimport sys\nprint('hello')\n"
            issues = applier.check_code(code, "test.py")

            # 6. 创建反馈循环
            storage_path = tmp_path / "feedback.json"
            collector = FeedbackCollector(str(storage_path))

            # 记录反馈
            for issue in issues:
                collector.record_rule_application(
                    rule_id=issue["rule_id"], file_path=issue["file_path"], line=issue["line"], accepted=True
                )

            # 验证完整流程
            assert len(rules) > 0
            assert isinstance(issues, list)

            kb.close()

        finally:
            try:
                os.unlink(db_path)
            except Exception:
                pass

    def test_closed_loop_statistics(self, temp_kb):
        """测试闭环统计"""
        # 添加一些已批准的规则
        rule = LearnedRule(
            id="test-rule",
            name="Test Rule",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=Pattern(
                file_patterns=["*.py"],
                code_patterns=["test"],
                context_keywords=["test"],
                severity_distribution={},
                tool_support=["ruff"],
            ),
            tools=["ruff"],
            frequency=1,
            confidence=0.8,
            quality_score=0.8,
            status="approved",
            created_at=datetime.now(),
        )
        temp_kb.add_rule(rule)

        # 应用规则
        applier = RuleApplier(temp_kb)
        code = "test pattern here\n"
        issues = applier.check_code(code, "test.py")

        # 验证统计
        stats = applier.get_statistics()
        assert stats["applied_count"] == len(issues)


# ============================================================================
# PreCommitHookGenerator 测试
# ============================================================================


class TestPreCommitHookGenerator:
    """测试Pre-commit钩子生成器"""

    def test_generate_hook(self, temp_kb, tmp_path):
        """测试生成pre-commit钩子"""
        output_path = tmp_path / "pre-commit-hook"

        PreCommitHookGenerator.generate_hook(temp_kb, output_path=str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "LingFlow" in content
        assert "Self-Learning" in content

    def test_generate_config(self, temp_kb, tmp_path):
        """测试生成配置文件"""
        output_path = tmp_path / "config.yaml"

        PreCommitHookGenerator.generate_config(temp_kb, output_path=str(output_path))

        assert output_path.exists()
