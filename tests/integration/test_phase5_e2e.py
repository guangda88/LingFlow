"""
Phase 5 端到端集成测试

测试AI工具学习系统的完整工作流，包括：
- AI工具适配器
- 规则提取
- 模式识别
- 知识库
"""

from datetime import datetime
from typing import Any, Dict, List

import pytest

from lingflow.self_optimizer.phase5.adapters import AIToolAdapter, RuffAdapter, SemgrepAdapter
from lingflow.self_optimizer.phase5.knowledge import InMemoryKnowledgeBase, KnowledgeBase
from lingflow.self_optimizer.phase5.learning import RuleDeduplicator, RuleExtractor, RuleValidator, SecurityRuleExtractor
from lingflow.self_optimizer.phase5.models import FeedbackCategory, FeedbackItem, LearnedRule, Pattern, SeverityLevel, ToolType
from lingflow.self_optimizer.phase5.patterns import HardcodedSecretDetector, LongMethodDetector, PatternRecognizer


@pytest.mark.phase5
class TestToolAdapters:
    """测试工具适配器"""

    def test_semgrep_adapter(self, temp_project):
        """测试Semgrep适配器"""
        adapter = SemgrepAdapter()

        results = adapter.run_scan(temp_project)

        assert isinstance(results, list)
        # Mock结果可能是空的，但要验证返回类型
        assert all(isinstance(r, dict) for r in results)

    def test_ruff_adapter(self, temp_project):
        """测试Ruff适配器"""
        from lingflow.self_optimizer.phase5.models import AIFeedback

        adapter = RuffAdapter()

        results = adapter.run_scan(temp_project)

        assert isinstance(results, list)
        assert all(isinstance(r, AIFeedback) for r in results)

    def test_adapter_result_normalization(self, mock_feedback_data):
        """测试结果标准化"""
        from lingflow.self_optimizer.phase5.models import AIFeedback

        adapter = SemgrepAdapter()

        normalized = adapter.normalize_results(mock_feedback_data)

        assert isinstance(normalized, list)
        for item in normalized:
            assert isinstance(item, AIFeedback)
            assert hasattr(item, "source")
            assert hasattr(item, "category")
            assert hasattr(item, "severity")
            assert hasattr(item, "rule_id")
            assert hasattr(item, "message")


@pytest.mark.phase5
class TestRuleExtraction:
    """测试规则提取"""

    def test_basic_rule_extraction(self, mock_feedback_data):
        """测试基本规则提取"""
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.7)

        # 转换为FeedbackItem
        feedback_items = [FeedbackItem(**item) for item in mock_feedback_data]

        rules = extractor.extract_rules(feedback_items)

        assert isinstance(rules, list)
        assert all(isinstance(rule, LearnedRule) for rule in rules)

    def test_security_rule_extraction(self, mock_feedback_data):
        """测试安全规则提取"""
        extractor = SecurityRuleExtractor(min_frequency=1, min_confidence=0.7)

        feedback_items = [FeedbackItem(**item) for item in mock_feedback_data if item.get("category") == "security"]

        rules = extractor.extract_rules(feedback_items)

        assert all(rule.category == FeedbackCategory.SECURITY for rule in rules)

    def test_rule_filtering_by_category(self, mock_feedback_data):
        """测试按类别过滤规则"""
        extractor = RuleExtractor()

        feedback_items = [FeedbackItem(**item) for item in mock_feedback_data]

        security_rules = extractor.extract_rules(feedback_items, category=FeedbackCategory.SECURITY)

        assert all(rule.category == FeedbackCategory.SECURITY for rule in security_rules)

    def test_rule_quality_scoring(self, mock_feedback_data):
        """测试规则质量评分"""
        extractor = RuleExtractor(min_frequency=1)

        feedback_items = [FeedbackItem(**item) for item in mock_feedback_data]
        rules = extractor.extract_rules(feedback_items)

        for rule in rules:
            assert hasattr(rule, "quality_score")
            assert 0 <= rule.quality_score <= 1


@pytest.mark.phase5
class TestRuleDeduplication:
    """测试规则去重"""

    def test_basic_deduplication(self, mock_feedback_data):
        """测试基本去重"""
        extractor = RuleExtractor(min_frequency=1)
        deduplicator = RuleDeduplicator()

        feedback_items = [FeedbackItem(**item) for item in mock_feedback_data]
        rules = extractor.extract_rules(feedback_items)

        unique_rules = deduplicator.deduplicate(rules)

        assert len(unique_rules) <= len(rules)

    def test_similarity_detection(self):
        """测试相似度检测"""
        deduplicator = RuleDeduplicator()

        # 创建相似规则
        pattern1 = Pattern(file_patterns=["*.py"], code_patterns=["import os"], context_keywords=["import", "unused"])

        pattern2 = Pattern(file_patterns=["*.py"], code_patterns=["import os"], context_keywords=["import", "unused"])

        hash1 = deduplicator._compute_rule_hash(
            LearnedRule(
                id="rule1",
                name="Rule 1",
                description="Test",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=pattern1,
                tools=["Ruff"],
                frequency=1,
                confidence=0.8,
            )
        )

        hash2 = deduplicator._compute_rule_hash(
            LearnedRule(
                id="rule2",
                name="Rule 2",
                description="Test",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=pattern2,
                tools=["Ruff"],
                frequency=1,
                confidence=0.8,
            )
        )

        # 相似规则应该被检测到
        assert deduplicator._are_similar(hash1, hash2)


@pytest.mark.phase5
class TestRuleValidation:
    """测试规则验证"""

    def test_valid_rule_validation(self):
        """测试有效规则验证"""
        validator = RuleValidator()

        pattern = Pattern(file_patterns=["*.py"])
        rule = LearnedRule(
            id="test_rule",
            name="Test Rule",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Ruff"],
            frequency=5,
            confidence=0.8,
        )
        rule.quality_score = 0.7

        assert validator.validate(rule) is True

    def test_invalid_rule_validation(self):
        """测试无效规则验证"""
        validator = RuleValidator(min_quality_score=0.5)

        pattern = Pattern(file_patterns=["*.py"])
        rule = LearnedRule(
            id="test_rule",
            name="Test Rule",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=[],  # 无工具支持
            frequency=1,
            confidence=0.3,
        )
        rule.quality_score = 0.2  # 低质量

        assert validator.validate(rule) is False

    def test_batch_validation(self):
        """测试批量验证"""
        validator = RuleValidator(min_quality_score=0.3)

        pattern = Pattern(file_patterns=["*.py"])

        rules = [
            LearnedRule(
                id=f"rule_{i}",
                name=f"Rule {i}",
                description="Test",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=pattern,
                tools=["Ruff"],
                frequency=i + 1,
                confidence=0.5 + (i * 0.1),
            )
            for i in range(5)
        ]

        # 设置质量分数
        for i, rule in enumerate(rules):
            rule.quality_score = 0.3 + (i * 0.15)

        valid_rules = validator.validate_batch(rules)

        assert len(valid_rules) <= len(rules)


@pytest.mark.phase5
class TestPatternRecognition:
    """测试模式识别"""

    def test_long_method_detection(self):
        """测试长方法检测"""
        detector = LongMethodDetector(threshold=50)

        long_method = "def " + "x\n" * 60 + "return x"

        patterns = detector.detect(long_method, "test.py")

        assert len(patterns) > 0
        assert patterns[0]["name"] == "Long Method"

    def test_hardcoded_secret_detection(self):
        """测试硬编码密钥检测"""
        detector = HardcodedSecretDetector()

        code = """
        password = "admin123"
        api_key = "sk-1234567890abcdef"
        secret = 'my_secret_key_12345'
        """

        patterns = detector.detect(code, "test.py")

        assert len(patterns) >= 2
        assert all(p["name"] == "Hardcoded Secret" for p in patterns)

    def test_pattern_recognizer_integration(self, sample_code):
        """测试模式识别器集成"""
        recognizer = PatternRecognizer()

        patterns = recognizer.recognize_patterns(sample_code, "test.py")

        assert isinstance(patterns, list)

    def test_multiple_pattern_detection(self):
        """测试多模式检测"""
        code = (
            '''
        def very_long_function():
            """A very long function with many lines"""
            x = 1
            '''
            + "\n".join([f"    var_{i} = {i}" for i in range(50)])
            + """
            password = "secret123"
            return x
        """
        )

        recognizer = PatternRecognizer()
        patterns = recognizer.recognize_patterns(code, "test.py")

        # 应该检测到多个模式
        pattern_names = [p["name"] for p in patterns]
        assert "Long Method" in pattern_names or "Hardcoded Secret" in pattern_names


@pytest.mark.phase5
class TestKnowledgeBase:
    """测试知识库"""

    def test_add_rule(self):
        """测试添加规则"""
        kb = InMemoryKnowledgeBase()

        pattern = Pattern(file_patterns=["*.py"])
        rule = LearnedRule(
            id="test_rule",
            name="Test Rule",
            description="Test description",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Ruff"],
            frequency=5,
            confidence=0.85,
        )

        assert kb.add_rule(rule) is True

    def test_get_rule(self):
        """测试获取规则"""
        kb = InMemoryKnowledgeBase()

        pattern = Pattern(file_patterns=["*.py"])
        rule = LearnedRule(
            id="get_test",
            name="Test",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Ruff"],
            frequency=1,
            confidence=0.8,
        )

        kb.add_rule(rule)
        retrieved = kb.get_rule("get_test")

        assert retrieved is not None
        assert retrieved.id == "get_test"

    def test_get_all_rules(self):
        """测试获取所有规则"""
        kb = InMemoryKnowledgeBase()

        for i in range(3):
            pattern = Pattern(file_patterns=["*.py"])
            rule = LearnedRule(
                id=f"rule_{i}",
                name=f"Rule {i}",
                description="Test",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=pattern,
                tools=["Ruff"],
                frequency=1,
                confidence=0.8,
            )
            kb.add_rule(rule)

        all_rules = kb.get_all_rules()
        assert len(all_rules) == 3

    def test_search_rules(self):
        """测试搜索规则"""
        kb = InMemoryKnowledgeBase()

        pattern = Pattern(file_patterns=["*.py"])
        rule = LearnedRule(
            id="search_test",
            name="Security Rule for Password",
            description="Detects hardcoded passwords",
            category=FeedbackCategory.SECURITY,
            pattern=pattern,
            tools=["Semgrep"],
            frequency=10,
            confidence=0.9,
        )

        kb.add_rule(rule)

        results = kb.search_rules("password")
        assert len(results) > 0

    def test_update_rule_status(self):
        """测试更新规则状态"""
        kb = InMemoryKnowledgeBase()

        pattern = Pattern(file_patterns=["*.py"])
        rule = LearnedRule(
            id="status_test",
            name="Test",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Ruff"],
            frequency=1,
            confidence=0.8,
            status="draft",
        )

        kb.add_rule(rule)
        kb.update_rule_status("status_test", "approved")

        updated = kb.get_rule("status_test")
        assert updated.status == "approved"

    def test_delete_rule(self):
        """测试删除规则"""
        kb = InMemoryKnowledgeBase()

        pattern = Pattern(file_patterns=["*.py"])
        rule = LearnedRule(
            id="delete_test",
            name="Test",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Ruff"],
            frequency=1,
            confidence=0.8,
        )

        kb.add_rule(rule)
        assert kb.get_rule("delete_test") is not None

        kb.delete_rule("delete_test")
        assert kb.get_rule("delete_test") is None

    def test_get_statistics(self):
        """测试获取统计信息"""
        kb = InMemoryKnowledgeBase()

        for i in range(5):
            pattern = Pattern(file_patterns=["*.py"])
            rule = LearnedRule(
                id=f"stat_{i}",
                name=f"Rule {i}",
                description="Test",
                category=FeedbackCategory.CODE_QUALITY if i % 2 == 0 else FeedbackCategory.SECURITY,
                pattern=pattern,
                tools=["Ruff"],
                frequency=1,
                confidence=0.8,
            )
            kb.add_rule(rule)

        stats = kb.get_statistics()

        assert stats["total_rules"] == 5
        assert "by_category" in stats
        assert "by_status" in stats

    def test_batch_add_rules(self):
        """测试批量添加规则"""
        kb = InMemoryKnowledgeBase()

        rules = []
        for i in range(3):
            pattern = Pattern(file_patterns=["*.py"])
            rule = LearnedRule(
                id=f"batch_{i}",
                name=f"Batch Rule {i}",
                description="Test",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=pattern,
                tools=["Ruff"],
                frequency=1,
                confidence=0.8,
            )
            rules.append(rule)

        count = kb.add_rules_batch(rules)
        assert count == 3
        assert len(kb.get_all_rules()) == 3


@pytest.mark.phase5
class TestLearningPipeline:
    """测试学习流水线"""

    def test_end_to_end_learning(self, mock_feedback_data):
        """测试端到端学习流程"""
        # 1. 接收反馈
        feedback_items = [FeedbackItem(**item) for item in mock_feedback_data]

        # 2. 提取规则
        extractor = RuleExtractor(min_frequency=1, min_confidence=0.6)
        rules = extractor.extract_rules(feedback_items)

        # 3. 去重
        deduplicator = RuleDeduplicator()
        unique_rules = deduplicator.deduplicate(rules)

        # 4. 验证
        validator = RuleValidator(min_quality_score=0.3)
        valid_rules = validator.validate_batch(unique_rules)

        # 5. 存储到知识库
        kb = InMemoryKnowledgeBase()
        kb.add_rules_batch(valid_rules)

        # 6. 验证结果
        stats = kb.get_statistics()
        assert stats["total_rules"] > 0

    def test_continuous_learning_cycle(self, mock_feedback_data):
        """测试持续学习循环"""
        kb = InMemoryKnowledgeBase()
        extractor = RuleExtractor(min_frequency=1, min_confidence=0.6)

        # 第一轮学习
        feedback_items = [FeedbackItem(**item) for item in mock_feedback_data]
        rules = extractor.extract_rules(feedback_items)
        kb.add_rules_batch(rules)

        initial_count = kb.get_statistics()["total_rules"]

        # 第二轮学习（新反馈）
        new_feedback = [
            FeedbackItem(
                tool_name="Semgrep",
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id="new_rule",
                rule_name="New Issue",
                category=FeedbackCategory.SECURITY,
                severity=SeverityLevel.MEDIUM,
                message="New security issue",
                file_path="src/new.py",
                line=10,
                snippet="code",
                suggestion="Fix it",
                confidence=0.9,
            )
        ]

        new_rules = extractor.extract_rules(new_feedback)
        kb.add_rules_batch(new_rules)

        # 应该有更多规则
        final_count = kb.get_statistics()["total_rules"]
        assert final_count >= initial_count


@pytest.mark.phase5
@pytest.mark.slow
class TestPhase5Workflows:
    """测试Phase 5完整工作流"""

    def test_tool_integration_workflow(self, temp_project):
        """测试工具集成工作流"""
        # 1. 运行工具
        adapter = SemgrepAdapter()
        results = adapter.run_scan(temp_project)

        # 2. 标准化结果
        normalized = adapter.normalize_results(results)

        # 3. 提取规则
        if normalized:
            # 将AIFeedback转换为FeedbackItem
            from lingflow.self_optimizer.phase5.models import ToolType

            feedback_items = []
            for item in normalized:
                feedback_items.append(
                    FeedbackItem(
                        tool_name=item.source.value,
                        tool_type=ToolType.SECURITY_SCANNER,
                        rule_id=item.rule_id or "",
                        rule_name=item.rule_id or "",
                        category=item.category,
                        severity=item.severity,
                        message=item.message,
                        file_path=item.file_path,
                        line=item.line_no,
                        snippet=item.code_snippet,
                        suggestion=item.suggestion,
                        confidence=0.8,
                    )
                )
            extractor = RuleExtractor(min_frequency=1)
            rules = extractor.extract_rules(feedback_items)

            # 4. 验证流程
            assert isinstance(rules, list)

    def test_pattern_learning_workflow(self, sample_code):
        """测试模式学习工作流"""
        # 1. 识别模式
        recognizer = PatternRecognizer()
        patterns = recognizer.recognize_patterns(sample_code, "test.py")

        # 2. 创建规则
        if patterns:
            rule = LearnedRule(
                id="learned_from_pattern",
                name="Learned Pattern",
                description="Learned from code analysis",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=Pattern(file_patterns=["*.py"]),
                tools=["Analyzer"],
                frequency=1,
                confidence=0.7,
            )

            # 3. 存储规则
            kb = InMemoryKnowledgeBase()
            kb.add_rule(rule)

            assert kb.get_rule("learned_from_pattern") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
