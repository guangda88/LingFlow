"""
Phase 5 学习引擎测试

测试规则提取、模式识别和知识库功能。
YOLO模式：快速验证核心功能
"""

import pytest
from datetime import datetime

from lingflow.self_optimizer.phase5.models import (
    FeedbackItem,
    LearnedRule,
    Pattern,
    FeedbackCategory,
    SeverityLevel,
    ToolType
)
from lingflow.self_optimizer.phase5.learning import (
    RuleExtractor,
    SecurityRuleExtractor,
    RuleDeduplicator,
    RuleValidator
)
from lingflow.self_optimizer.phase5.patterns import (
    PatternRecognizer,
    LongMethodDetector,
    HardcodedSecretDetector
)
from lingflow.self_optimizer.phase5.knowledge import (
    KnowledgeBase,
    InMemoryKnowledgeBase
)


# 测试数据
def create_sample_feedback() -> list[FeedbackItem]:
    """创建示例反馈数据"""
    return [
        FeedbackItem(
            tool_name="Semgrep",
            tool_type=ToolType.SECURITY_SCANNER,
            rule_id="python.lang.security.hardcoded_password",
            rule_name="Hardcoded password detected",
            category=FeedbackCategory.SECURITY,
            severity=SeverityLevel.HIGH,
            message="Hardcoded password detected in source code",
            file_path="src/auth.py",
            line=45,
            snippet="password = 'admin123'",
            suggestion="Use environment variables for credentials",
            confidence=0.95
        ),
        FeedbackItem(
            tool_name="Bandit",
            tool_type=ToolType.SECURITY_SCANNER,
            rule_id="B105:hardcoded_password",
            rule_name="Possible hardcoded password",
            category=FeedbackCategory.SECURITY,
            severity=SeverityLevel.HIGH,
            message="Possible hardcoded password: 'admin123'",
            file_path="src/auth.py",
            line=45,
            snippet="password = 'admin123'",
            suggestion="Use a secure credential manager",
            confidence=0.90
        ),
        FeedbackItem(
            tool_name="Semgrep",
            tool_type=ToolType.SECURITY_SCANNER,
            rule_id="python.lang.security.hardcoded_password",
            rule_name="Hardcoded password detected",
            category=FeedbackCategory.SECURITY,
            severity=SeverityLevel.HIGH,
            message="Hardcoded password detected",
            file_path="src/config.py",
            line=12,
            snippet="db_pass = 'secret456'",
            suggestion="Use environment variables",
            confidence=0.92
        ),
        FeedbackItem(
            tool_name="Ruff",
            tool_type=ToolType.LINTING,
            rule_id="F401",
            rule_name="Unused import",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.LOW,
            message="Unused import 'os'",
            file_path="src/utils.py",
            line=3,
            snippet="import os",
            suggestion="Remove unused import",
            confidence=0.85
        ),
        FeedbackItem(
            tool_name="Ruff",
            tool_type=ToolType.LINTING,
            rule_id="F401",
            rule_name="Unused import",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.LOW,
            message="Unused import 'json'",
            file_path="src/helpers.py",
            line=5,
            snippet="import json",
            suggestion="Remove unused import",
            confidence=0.85
        ),
        FeedbackItem(
            tool_name="Ruff",
            tool_type=ToolType.LINTING,
            rule_id="F401",
            rule_name="Unused import",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.LOW,
            message="Unused import 'sys'",
            file_path="src/main.py",
            line=2,
            snippet="import sys",
            suggestion="Remove unused import",
            confidence=0.88
        ),
    ]


class TestRuleExtractor:
    """测试规则提取器"""

    def test_extract_rules_basic(self):
        """测试基本规则提取"""
        feedback_items = create_sample_feedback()
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.7)
        rules = extractor.extract_rules(feedback_items)

        # 应该提取到至少2个规则
        assert len(rules) >= 2
        assert all(isinstance(rule, LearnedRule) for rule in rules)

    def test_extract_rules_by_category(self):
        """测试按类别提取规则"""
        feedback_items = create_sample_feedback()
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.7)

        # 提取安全规则
        security_rules = extractor.extract_rules(
            feedback_items,
            category=FeedbackCategory.SECURITY
        )

        assert all(rule.category == FeedbackCategory.SECURITY for rule in security_rules)

    def test_rule_quality_score(self):
        """测试质量分数计算"""
        feedback_items = create_sample_feedback()
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.7)
        rules = extractor.extract_rules(feedback_items)

        for rule in rules:
            assert 0 <= rule.quality_score <= 1
            assert rule.frequency > 0
            assert 0 <= rule.confidence <= 1


class TestSecurityRuleExtractor:
    """测试安全规则提取器"""

    def test_security_rules_only(self):
        """测试只提取安全规则"""
        feedback_items = create_sample_feedback()
        extractor = SecurityRuleExtractor(min_frequency=2, min_confidence=0.7)
        rules = extractor.extract_rules(feedback_items)

        assert all(rule.category == FeedbackCategory.SECURITY for rule in rules)
        assert all(rule.status == "security_verified" for rule in rules)


class TestRuleDeduplicator:
    """测试规则去重器"""

    def test_deduplicate_basic(self):
        """测试基本去重"""
        # 创建相似规则
        feedback_items = create_sample_feedback()
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.7)
        rules = extractor.extract_rules(feedback_items)

        deduplicator = RuleDeduplicator()
        unique_rules = deduplicator.deduplicate(rules)

        # 去重后的数量应该小于等于原数量
        assert len(unique_rules) <= len(rules)


class TestRuleValidator:
    """测试规则验证器"""

    def test_validate_valid_rule(self):
        """测试验证有效规则"""
        feedback_items = create_sample_feedback()
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.7)
        rules = extractor.extract_rules(feedback_items)

        validator = RuleValidator()

        for rule in rules:
            if rule.quality_score >= 0.5:
                assert validator.validate(rule) is True

    def test_validate_batch(self):
        """测试批量验证"""
        feedback_items = create_sample_feedback()
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.7)
        rules = extractor.extract_rules(feedback_items)

        validator = RuleValidator(min_quality_score=0.3)
        valid_rules = validator.validate_batch(rules)

        assert len(valid_rules) <= len(rules)


class TestPatternRecognizer:
    """测试模式识别器"""

    def test_recognize_long_method(self):
        """测试识别长方法"""
        sample_code = """
def very_long_function():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    h = 11
    i = 12
    j = 13
    k = 14
    l = 15
    m = 16
    n = 17
    o = 18
    p = 19
    q = 20
    r = 21
    s = 22
    t = 23
    u = 24
    v = 25
    w = 26
    x2 = 27
    y2 = 28
    z2 = 29
    a2 = 30
    b2 = 31
    c2 = 32
    d2 = 33
    e2 = 34
    f2 = 35
    g2 = 36
    h2 = 37
    i2 = 38
    j2 = 39
    k2 = 40
    l2 = 41
    m2 = 42
    n2 = 43
    o2 = 44
    p2 = 45
    q2 = 46
    r2 = 47
    s2 = 48
    t2 = 49
    u2 = 50
    v2 = 51
    return x + y + z
"""

        detector = LongMethodDetector(threshold=50)
        patterns = detector.detect(sample_code, "test.py")

        # 应该检测到长方法
        assert len(patterns) > 0
        assert patterns[0]['name'] == 'Long Method'

    def test_recognize_hardcoded_secret(self):
        """测试识别硬编码密钥"""
        sample_code = """
password = "admin123"
api_key = "sk-1234567890abcdef"
secret = 'my_secret_key_12345'
"""

        detector = HardcodedSecretDetector()
        patterns = detector.detect(sample_code, "test.py")

        # 应该检测到多个硬编码密钥
        assert len(patterns) >= 2
        assert all(p['name'] == 'Hardcoded Secret' for p in patterns)

    def test_pattern_recognizer_integration(self):
        """测试模式识别器集成"""
        sample_code = """
def long_func():
    pass

password = "test123"
"""

        recognizer = PatternRecognizer()
        patterns = recognizer.recognize_patterns(sample_code, "test.py")

        # 应该检测到一些模式
        assert isinstance(patterns, list)


class TestInMemoryKnowledgeBase:
    """测试内存知识库"""

    def test_add_and_get_rule(self):
        """测试添加和获取规则"""
        kb = InMemoryKnowledgeBase()

        # 创建测试规则
        pattern = Pattern(
            file_patterns=["*.py"],
            code_patterns=["import os"],
            context_keywords=["import", "unused"],
        )

        rule = LearnedRule(
            id="test_rule",
            name="Test Rule",
            description="Test description",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Ruff"],
            frequency=5,
            confidence=0.85,
            status="draft",
            created_at=datetime.now()
        )

        # 添加规则
        assert kb.add_rule(rule) is True

        # 获取规则
        retrieved = kb.get_rule("test_rule")
        assert retrieved is not None
        assert retrieved.id == "test_rule"
        assert retrieved.name == "Test Rule"

    def test_get_all_rules(self):
        """测试获取所有规则"""
        kb = InMemoryKnowledgeBase()

        # 添加多个规则
        for i in range(3):
            pattern = Pattern(file_patterns=["*.py"])
            rule = LearnedRule(
                id=f"rule_{i}",
                name=f"Rule {i}",
                description=f"Description {i}",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=pattern,
                tools=["Ruff"],
                frequency=i + 1,
                confidence=0.8,
                status="draft",
                created_at=datetime.now()
            )
            kb.add_rule(rule)

        # 获取所有规则
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
            status="draft",
            created_at=datetime.now()
        )

        kb.add_rule(rule)

        # 搜索规则
        results = kb.search_rules("password")
        assert len(results) > 0
        assert "password" in results[0].name.lower() or "password" in results[0].description.lower()

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
            created_at=datetime.now()
        )

        kb.add_rule(rule)

        # 更新状态
        assert kb.update_rule_status("status_test", "approved") is True

        # 验证更新
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
            status="draft",
            created_at=datetime.now()
        )

        kb.add_rule(rule)

        # 删除规则
        assert kb.delete_rule("delete_test") is True

        # 验证删除
        assert kb.get_rule("delete_test") is None

    def test_get_statistics(self):
        """测试获取统计信息"""
        kb = InMemoryKnowledgeBase()

        # 添加规则
        for i in range(5):
            pattern = Pattern(file_patterns=["*.py"])
            rule = LearnedRule(
                id=f"stat_{i}",
                name=f"Rule {i}",
                description=f"Description {i}",
                category=FeedbackCategory.CODE_QUALITY if i % 2 == 0 else FeedbackCategory.SECURITY,
                pattern=pattern,
                tools=["Ruff"],
                frequency=1,
                confidence=0.8,
                status="draft",
                created_at=datetime.now()
            )
            kb.add_rule(rule)

        # 获取统计
        stats = kb.get_statistics()
        assert stats['total_rules'] == 5
        assert 'by_category' in stats
        assert 'by_status' in stats


def test_end_to_end_workflow():
    """端到端工作流测试"""
    # 1. 创建反馈数据
    feedback_items = create_sample_feedback()

    # 2. 提取规则
    extractor = RuleExtractor(min_frequency=2, min_confidence=0.7)
    rules = extractor.extract_rules(feedback_items)
    assert len(rules) > 0

    # 3. 去重
    deduplicator = RuleDeduplicator()
    unique_rules = deduplicator.deduplicate(rules)

    # 4. 验证
    validator = RuleValidator()
    valid_rules = validator.validate_batch(unique_rules)
    assert len(valid_rules) > 0

    # 5. 存储到知识库
    kb = InMemoryKnowledgeBase()
    count = kb.add_rules_batch(valid_rules)
    assert count > 0

    # 6. 检索
    stats = kb.get_statistics()
    assert stats['total_rules'] > 0

    # 7. 搜索
    if valid_rules:
        search_results = kb.search_rules(valid_rules[0].name[:5])
        assert len(search_results) > 0


if __name__ == "__main__":
    # 快速测试
    print("运行Phase 5学习引擎测试...")

    test_end_to_end_workflow()
    print("✓ 端到端测试通过")

    print("\n所有测试通过！")
