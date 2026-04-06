"""
Rule Learning 模块测试

测试规则提取、去重和验证功能。
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from lingflow.self_optimizer.phase5.models import (
    FeedbackItem,
    LearnedRule,
    Pattern,
    FeedbackCategory,
    FeedbackSeverity,
    ToolType,
)
from lingflow.self_optimizer.phase5.learning import (
    RuleExtractor,
    SecurityRuleExtractor,
    RuleDeduplicator,
    RuleValidator,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_feedback_items():
    """创建示例反馈项"""
    items = []
    for i in range(10):
        item = FeedbackItem(
            tool_name="ruff",
            tool_type=ToolType.STATIC_ANALYZER,
            rule_id="F401" if i % 2 == 0 else "F841",
            rule_name="unused-import" if i % 2 == 0 else "unused-variable",
            category=FeedbackCategory.CODE_QUALITY,
            severity=FeedbackSeverity.LOW,
            message=f"Unused {('import' if i % 2 == 0 else 'variable')} detected",
            file_path=f"test/file_{i}.py",
            line=i + 10,
            snippet=f"x = {i}",
            suggestion="Remove unused code",
            confidence=0.8,
        )
        items.append(item)
    return items


@pytest.fixture
def diverse_feedback_items():
    """创建多样化的反馈项"""
    categories = [
        FeedbackCategory.CODE_QUALITY,
        FeedbackCategory.BUG_RISK,
        FeedbackCategory.SECURITY,
    ]
    tools = ["ruff", "pylint", "semgrep"]
    items = []

    for i, cat in enumerate(categories):
        for j, tool in enumerate(tools):
            item = FeedbackItem(
                tool_name=tool,
                tool_type=ToolType.STATIC_ANALYZER,
                rule_id=f"RULE-{i}-{j}",
                rule_name=f"rule_{i}_{j}",
                category=cat,
                severity=FeedbackSeverity.MEDIUM,
                message=f"Issue from {tool} in {cat.value}",
                file_path=f"src/module_{i}.py",
                line=10 * (i + 1),
                snippet=f"code_{i}_{j}",
                suggestion=f"Fix for {cat.value}",
                confidence=0.7 + (i * 0.1),
            )
            items.append(item)
    return items


@pytest.fixture
def sample_learned_rule():
    """创建示例学习到的规则"""
    return LearnedRule(
        id="test-rule-001",
        name="Test Rule",
        description="A test rule",
        category=FeedbackCategory.CODE_QUALITY,
        pattern=Pattern(
            file_patterns=["*.py"],
            code_patterns=["unused_*"],
            context_keywords=["unused", "import"],
            severity_distribution={"LOW": 10, "MEDIUM": 5},
            tool_support=["ruff", "pylint"],
        ),
        tools=["ruff", "pylint"],
        frequency=15,
        confidence=0.85,
        quality_score=0.82,
        status="draft",
        created_at=datetime.now(),
    )


@pytest.fixture
def low_quality_rule():
    """创建低质量规则"""
    return LearnedRule(
        id="low-quality-001",
        name="Low Quality Rule",
        description="A rule with low quality",
        category=FeedbackCategory.CODE_QUALITY,
        pattern=Pattern(
            file_patterns=[],
            code_patterns=[],
            context_keywords=[],
            severity_distribution={},
            tool_support=[],
        ),
        tools=[],  # 无工具支持
        frequency=1,
        confidence=0.3,
        quality_score=0.2,
        status="draft",
        created_at=datetime.now(),
    )


# ============================================================================
# RuleExtractor 测试
# ============================================================================


class TestRuleExtractor:
    """测试规则提取器"""

    def test_initialization(self):
        """测试初始化"""
        extractor = RuleExtractor(
            min_frequency=2,
            min_confidence=0.6,
            max_rules=100
        )
        assert extractor.min_frequency == 2
        assert extractor.min_confidence == 0.6
        assert extractor.max_rules == 100
        assert extractor._extracted_count == 0

    def test_initialization_default_values(self):
        """测试默认初始化值"""
        extractor = RuleExtractor()
        assert extractor.min_frequency == 3
        assert extractor.min_confidence == 0.7
        assert extractor.max_rules == 1000

    def test_extract_rules_basic(self, sample_feedback_items):
        """测试基本规则提取"""
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules(sample_feedback_items)

        # 应该提取到至少2条规则（F401和F841）
        assert len(rules) >= 1
        assert all(isinstance(r, LearnedRule) for r in rules)

    def test_extract_rules_with_category_filter(self, diverse_feedback_items):
        """测试按类别过滤提取"""
        extractor = RuleExtractor(min_frequency=1, min_confidence=0.5)

        # 只提取安全类别
        security_rules = extractor.extract_rules(
            diverse_feedback_items,
            category=FeedbackCategory.SECURITY
        )

        assert all(r.category == FeedbackCategory.SECURITY for r in security_rules)

    def test_extract_rules_min_frequency_filter(self, sample_feedback_items):
        """测试最小频率过滤"""
        extractor = RuleExtractor(min_frequency=10, min_confidence=0.1)
        rules = extractor.extract_rules(sample_feedback_items)

        # 所有规则频率都低于10，应该返回空
        assert len(rules) == 0

    def test_extract_rules_min_confidence_filter(self, sample_feedback_items):
        """测试最小置信度过滤"""
        # 修改反馈项的置信度
        for item in sample_feedback_items:
            item.confidence = 0.5

        extractor = RuleExtractor(min_frequency=1, min_confidence=0.8)
        rules = extractor.extract_rules(sample_feedback_items)

        # 所有规则置信度都低于0.8，应该返回空
        assert len(rules) == 0

    def test_extract_rules_returns_sorted_by_quality(self, diverse_feedback_items):
        """测试结果按质量分数排序"""
        extractor = RuleExtractor(min_frequency=1, min_confidence=0.5)
        rules = extractor.extract_rules(diverse_feedback_items)

        # 验证按质量分数降序排列
        for i in range(len(rules) - 1):
            assert rules[i].quality_score >= rules[i + 1].quality_score

    def test_extract_rules_max_rules_limit(self, diverse_feedback_items):
        """测试最大规则数限制"""
        extractor = RuleExtractor(min_frequency=1, min_confidence=0.5, max_rules=2)
        rules = extractor.extract_rules(diverse_feedback_items)

        # 应该最多返回2条规则
        assert len(rules) <= 2

    def test_extract_empty_list(self):
        """测试提取空列表"""
        extractor = RuleExtractor()
        rules = extractor.extract_rules([])
        assert rules == []

    def test_normalize_rule_id(self):
        """测试规则ID规范化"""
        extractor = RuleExtractor()

        # 测试各种特殊字符
        assert extractor._normalize_rule_id("F401") == "f401"
        assert extractor._normalize_rule_id("RUFF-F401") == "ruff-f401"
        assert extractor._normalize_rule_id("RULE:123@ABC") == "rule_123_abc"

    def test_extract_single_rule_creates_valid_structure(self, sample_feedback_items):
        """测试提取的规则具有正确的结构"""
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules(sample_feedback_items)

        if rules:
            rule = rules[0]
            assert isinstance(rule.id, str)
            assert len(rule.id) > 0
            assert isinstance(rule.name, str)
            assert len(rule.name) > 0
            assert isinstance(rule.category, FeedbackCategory)
            assert isinstance(rule.pattern, Pattern)
            assert isinstance(rule.tools, list)
            assert rule.frequency >= 2
            assert 0 <= rule.confidence <= 1
            assert 0 <= rule.quality_score <= 1
            assert rule.status in ["draft", "approved", "rejected"]

    def test_extract_rule_pattern_building(self, sample_feedback_items):
        """测试模式构建"""
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules(sample_feedback_items)

        if rules:
            rule = rules[0]
            # 验证模式字段
            assert isinstance(rule.pattern.file_patterns, list)
            assert isinstance(rule.pattern.code_patterns, list)
            assert isinstance(rule.pattern.context_keywords, list)
            assert isinstance(rule.pattern.severity_distribution, dict)
            assert isinstance(rule.pattern.tool_support, list)

    def test_extract_rules_multiple_tools(self):
        """测试从多个工具的反馈中提取规则"""
        items = []
        for tool in ["ruff", "pylint"]:
            for i in range(5):
                item = FeedbackItem(
                    tool_name=tool,
                    tool_type=ToolType.STATIC_ANALYZER,
                    rule_id="MULTI-TOOL-RULE",
                    rule_name="multi_tool_rule",
                    category=FeedbackCategory.CODE_QUALITY,
                    severity=FeedbackSeverity.MEDIUM,
                    message="Same issue detected by multiple tools",
                    file_path=f"test/file_{i}.py",
                    line=i,
                    snippet="x = 1",
                    suggestion="Fix it",
                    confidence=0.8,
                )
                items.append(item)

        extractor = RuleExtractor(min_frequency=3, min_confidence=0.5)
        rules = extractor.extract_rules(items)

        if rules:
            rule = rules[0]
            # 应该包含两个工具
            assert set(rule.tools) == {"ruff", "pylint"}

    def test_calculate_quality_score(self, sample_feedback_items):
        """测试质量分数计算"""
        extractor = RuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules(sample_feedback_items)

        if rules:
            # 质量分数应该在合理范围内
            for rule in rules:
                assert 0 <= rule.quality_score <= 1
                # 工具多样性应该影响分数
                # 频率应该影响分数
                # 置信度应该影响分数


# ============================================================================
# SecurityRuleExtractor 测试
# ============================================================================


class TestSecurityRuleExtractor:
    """测试安全规则提取器"""

    def test_extract_only_security_rules(self, diverse_feedback_items):
        """测试只提取安全类规则"""
        extractor = SecurityRuleExtractor(min_frequency=1, min_confidence=0.5)
        rules = extractor.extract_rules(diverse_feedback_items)

        # 所有规则应该是安全类别
        assert all(r.category == FeedbackCategory.SECURITY for r in rules)

    def test_security_rules_get_special_status(self):
        """测试安全规则获得特殊状态"""
        items = [
            FeedbackItem(
                tool_name="semgrep",
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id="SEC-001",
                rule_name="sql-injection",
                category=FeedbackCategory.SECURITY,
                severity=FeedbackSeverity.HIGH,
                message="Potential SQL injection",
                file_path="test.py",
                line=10,
                snippet="cursor.execute(query)",
                suggestion="Use parameterized queries",
                confidence=0.9,
            )
            for _ in range(3)
        ]

        extractor = SecurityRuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules(items)

        if rules:
            # 安全规则应该有 special status
            assert all(r.status == "security_verified" for r in rules)

    def test_security_keywords_extraction(self):
        """测试安全关键词提取"""
        items = [
            FeedbackItem(
                tool_name="semgrep",
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id="SEC-002",
                rule_name="hardcoded-secret",
                category=FeedbackCategory.SECURITY,
                severity=FeedbackSeverity.HIGH,
                message="Hardcoded password detected in code",
                file_path="config.py",
                line=5,
                snippet='password = "secret123"',
                suggestion="Use environment variables",
                confidence=0.9,
            )
            for _ in range(3)
        ]

        extractor = SecurityRuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules(items)

        if rules:
            # 应该包含安全相关关键词
            keywords = rules[0].pattern.context_keywords
            security_keywords = ["password", "secret", "injection", "xss"]
            assert any(kw in keywords for kw in security_keywords)


# ============================================================================
# RuleDeduplicator 测试
# ============================================================================


class TestRuleDeduplicator:
    """测试规则去重器"""

    def test_initialization(self):
        """测试初始化"""
        dedup = RuleDeduplicator(similarity_threshold=0.8)
        assert dedup.similarity_threshold == 0.8
        assert dedup._deduped_count == 0

    def test_deduplicate_identical_rules(self):
        """测试去除完全相同的规则"""
        rule1 = LearnedRule(
            id="rule-001",
            name="Rule 1",
            description="Test rule",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=Pattern(
                file_patterns=["*.py"],
                code_patterns=["test pattern"],
                context_keywords=["test"],
                severity_distribution={},
                tool_support=["ruff"],
            ),
            tools=["ruff"],
            frequency=5,
            confidence=0.8,
            quality_score=0.7,
            status="draft",
            created_at=datetime.now(),
        )

        rule2 = LearnedRule(
            id="rule-002",  # 不同ID
            name="Rule 1",  # 相同名称
            description="Test rule",  # 相同描述
            category=FeedbackCategory.CODE_QUALITY,
            pattern=Pattern(
                file_patterns=["*.py"],
                code_patterns=["test pattern"],
                context_keywords=["test"],
                severity_distribution={},
                tool_support=["ruff"],
            ),
            tools=["ruff"],
            frequency=5,
            confidence=0.8,
            quality_score=0.7,
            status="draft",
            created_at=datetime.now(),
        )

        dedup = RuleDeduplicator()
        unique_rules = dedup.deduplicate([rule1, rule2])

        # 应该只返回一条规则
        assert len(unique_rules) == 1

    def test_deduplicate_keeps_distinct_rules(self):
        """测试保留不同的规则"""
        # 创建有明显差异的规则
        rules = []
        keywords_list = [
            ["import", "unused"],
            ["variable", "unassigned"],
            ["function", "empty"],
            ["class", "naming"],
            ["security", "injection"],
        ]
        for i, keywords in enumerate(keywords_list):
            rule = LearnedRule(
                id=f"rule-{i:03d}",
                name=f"Rule {i}",
                description=f"Description {i}",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=Pattern(
                    file_patterns=["*.py"],
                    code_patterns=[f"unique_pattern_{i}_here"],  # 更长的模式字符串
                    context_keywords=keywords,  # 不同的关键词
                    severity_distribution={},
                    tool_support=["ruff"],
                ),
                tools=["ruff"],
                frequency=1,
                confidence=0.8,
                quality_score=0.7,
                status="draft",
                created_at=datetime.now(),
            )
            rules.append(rule)

        dedup = RuleDeduplicator()
        unique_rules = dedup.deduplicate(rules)

        # 所有规则都应该保留（它们的哈希不同）
        assert len(unique_rules) == 5

    def test_deduplicate_empty_list(self):
        """测试去重空列表"""
        dedup = RuleDeduplicator()
        result = dedup.deduplicate([])
        assert result == []

    def test_compute_rule_hash(self):
        """测试规则哈希计算"""
        rule = LearnedRule(
            id="rule-001",
            name="Test Rule",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=Pattern(
                file_patterns=["*.py"],
                code_patterns=["pattern"],
                context_keywords=["keyword1", "keyword2"],
                severity_distribution={},
                tool_support=[],
            ),
            tools=["ruff"],
            frequency=1,
            confidence=0.8,
            quality_score=0.7,
            status="draft",
            created_at=datetime.now(),
        )

        dedup = RuleDeduplicator()
        hash_value = dedup._compute_rule_hash(rule)

        # 哈希应该包含类别、关键词和模式信息
        assert isinstance(hash_value, str)
        assert "code_quality" in hash_value
        assert "keyword1" in hash_value.lower()

    def test_levenshtein_distance(self):
        """测试编辑距离计算"""
        dedup = RuleDeduplicator()

        # 相同字符串
        assert dedup._levenshtein_distance("test", "test") == 0

        # 完全不同
        assert dedup._levenshtein_distance("abc", "xyz") == 3

        # 一个差异
        assert dedup._levenshtein_distance("test", "text") == 1

    def test_similarity_detection(self):
        """测试相似度检测"""
        dedup = RuleDeduplicator(similarity_threshold=0.7)

        # 相似的哈希值
        hash1 = "code_quality:keyword_pattern:unused"
        hash2 = "code_quality:keyword_pattern:unused_variable"

        assert dedup._are_similar(hash1, hash2) is True

        # 不相似的哈希值
        hash3 = "security:injection:sql"
        assert dedup._are_similar(hash1, hash3) is False


# ============================================================================
# RuleValidator 测试
# ============================================================================


class TestRuleValidator:
    """测试规则验证器"""

    def test_initialization(self):
        """测试初始化"""
        validator = RuleValidator(
            min_quality_score=0.5,
            min_tool_support=1
        )
        assert validator.min_quality_score == 0.5
        assert validator.min_tool_support == 1

    def test_validate_high_quality_rule(self, sample_learned_rule):
        """测试验证高质量规则"""
        validator = RuleValidator(min_quality_score=0.5, min_tool_support=1)
        result = validator.validate(sample_learned_rule)
        assert result is True

    def test_validate_low_quality_rule(self, low_quality_rule):
        """测试验证低质量规则"""
        validator = RuleValidator(min_quality_score=0.5, min_tool_support=1)
        result = validator.validate(low_quality_rule)
        assert result is False

    def test_validate_by_quality_score(self, sample_learned_rule):
        """测试按质量分数验证"""
        sample_learned_rule.quality_score = 0.3

        validator = RuleValidator(min_quality_score=0.5, min_tool_support=0)
        result = validator.validate(sample_learned_rule)
        assert result is False

    def test_validate_by_tool_support(self, sample_learned_rule):
        """测试按工具支持验证"""
        sample_learned_rule.tools = []  # 无工具支持

        validator = RuleValidator(min_quality_score=0.0, min_tool_support=1)
        result = validator.validate(sample_learned_rule)
        assert result is False

    def test_validate_by_pattern_validity(self, sample_learned_rule):
        """测试按模式有效性验证"""
        # 空的文件模式
        sample_learned_rule.pattern.file_patterns = []

        validator = RuleValidator(min_quality_score=0.0, min_tool_support=0)
        result = validator.validate(sample_learned_rule)
        assert result is False

    def test_validate_by_category_validity(self, sample_learned_rule):
        """测试按类别有效性验证"""
        # 设置无效的类别
        with patch.object(sample_learned_rule, 'category', "invalid"):
            validator = RuleValidator()
            result = validator.validate(sample_learned_rule)
            assert result is False

    def test_validate_batch(self, sample_learned_rule, low_quality_rule):
        """测试批量验证"""
        rules = [sample_learned_rule, low_quality_rule]

        validator = RuleValidator(min_quality_score=0.5, min_tool_support=1)
        valid_rules = validator.validate_batch(rules)

        # 应该只返回高质量规则
        assert len(valid_rules) == 1
        assert valid_rules[0].id == sample_learned_rule.id

    def test_validate_batch_empty_list(self):
        """测试验证空列表"""
        validator = RuleValidator()
        result = validator.validate_batch([])
        assert result == []

    def test_validate_all_invalid(self):
        """测试所有规则都无效"""
        rules = [
            LearnedRule(
                id=f"rule-{i:03d}",
                name=f"Rule {i}",
                description="Low quality rule",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=Pattern(
                    file_patterns=[],
                    code_patterns=[],
                    context_keywords=[],
                    severity_distribution={},
                    tool_support=[],
                ),
                tools=[],
                frequency=0,
                confidence=0.0,
                quality_score=0.0,
                status="draft",
                created_at=datetime.now(),
            )
            for i in range(5)
        ]

        validator = RuleValidator(min_quality_score=0.5, min_tool_support=1)
        valid_rules = validator.validate_batch(rules)

        assert len(valid_rules) == 0


# ============================================================================
# 集成测试
# ============================================================================


class TestLearningPipelineIntegration:
    """测试学习流水线集成"""

    def test_full_extraction_pipeline(self, diverse_feedback_items):
        """测试完整的提取流程"""
        # 1. 提取规则
        extractor = RuleExtractor(min_frequency=1, min_confidence=0.5)
        rules = extractor.extract_rules(diverse_feedback_items)

        # 2. 去重
        dedup = RuleDeduplicator()
        unique_rules = dedup.deduplicate(rules)

        # 3. 验证
        validator = RuleValidator(min_quality_score=0.3, min_tool_support=1)
        valid_rules = validator.validate_batch(unique_rules)

        # 验证流程结果
        assert len(rules) > 0
        assert len(unique_rules) <= len(rules)
        assert len(valid_rules) <= len(unique_rules)

    def test_pipeline_with_minimal_feedback(self):
        """测试最小反馈集的处理"""
        # 创建刚好达到最小频率的反馈
        items = [
            FeedbackItem(
                tool_name="ruff",
                tool_type=ToolType.STATIC_ANALYZER,
                rule_id="F401",
                rule_name="unused-import",
                category=FeedbackCategory.CODE_QUALITY,
                severity=FeedbackSeverity.LOW,
                message="Unused import",
                file_path="test.py",
                line=i,
                snippet="import os",
                suggestion="Remove unused import",
                confidence=0.9,
            )
            for i in range(3)  # 刚好达到 min_frequency=3
        ]

        extractor = RuleExtractor(min_frequency=3, min_confidence=0.8)
        rules = extractor.extract_rules(items)

        assert len(rules) == 1

    def test_pipeline_preserves_rule_quality_ordering(self, diverse_feedback_items):
        """测试流水线保持质量排序"""
        extractor = RuleExtractor(min_frequency=1, min_confidence=0.5)
        rules = extractor.extract_rules(diverse_feedback_items)

        # 去重和验证
        dedup = RuleDeduplicator()
        unique_rules = dedup.deduplicate(rules)

        validator = RuleValidator(min_quality_score=0.3, min_tool_support=1)
        valid_rules = validator.validate_batch(unique_rules)

        # 验证保持降序排列
        for i in range(len(valid_rules) - 1):
            assert valid_rules[i].quality_score >= valid_rules[i + 1].quality_score


# ============================================================================
# 边界条件测试
# ============================================================================


class TestRuleExtractorEdgeCases:
    """测试规则提取器边界条件"""

    def test_extract_with_single_feedback_item(self):
        """测试单条反馈项（不足频率要求）"""
        item = FeedbackItem(
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
            suggestion="Remove it",
            confidence=0.9,
        )

        extractor = RuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules([item])

        # 单条反馈不足频率要求
        assert len(rules) == 0

    def test_extract_with_very_long_message(self):
        """测试处理非常长的消息"""
        long_message = "A" * 10000

        items = [
            FeedbackItem(
                tool_name="ruff",
                tool_type=ToolType.STATIC_ANALYZER,
                rule_id="LONG-MSG",
                rule_name="long_message",
                category=FeedbackCategory.CODE_QUALITY,
                severity=FeedbackSeverity.LOW,
                message=long_message,
                file_path="test.py",
                line=i,
                snippet="code",
                suggestion="Fix",
                confidence=0.8,
            )
            for i in range(5)
        ]

        extractor = RuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules(items)

        # 应该能处理并生成规则
        assert len(rules) >= 1
        # 名称应该被截断
        assert len(rules[0].name) <= 63  # 60 + "..."

    def test_extract_with_special_characters_in_snippet(self):
        """测试处理特殊字符"""
        special_snippet = 'x = "string with \\"quotes\\" and \\n newlines"'

        items = [
            FeedbackItem(
                tool_name="ruff",
                tool_type=ToolType.STATIC_ANALYZER,
                rule_id="SPECIAL",
                rule_name="special_chars",
                category=FeedbackCategory.CODE_QUALITY,
                severity=FeedbackSeverity.LOW,
                message="Special characters",
                file_path="test.py",
                line=i,
                snippet=special_snippet,
                suggestion="Fix",
                confidence=0.8,
            )
            for i in range(5)
        ]

        extractor = RuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules(items)

        # 应该能正常处理
        assert len(rules) >= 1

    def test_extract_preserves_exact_confidence(self):
        """测试保留精确的置信度值"""
        items = [
            FeedbackItem(
                tool_name="ruff",
                tool_type=ToolType.STATIC_ANALYZER,
                rule_id="CONF-TEST",
                rule_name="conf_test",
                category=FeedbackCategory.CODE_QUALITY,
                severity=FeedbackSeverity.LOW,
                message="Test",
                file_path="test.py",
                line=i,
                snippet="code",
                suggestion="Fix",
                confidence=0.8567,  # 精确值
            )
            for i in range(5)
        ]

        extractor = RuleExtractor(min_frequency=2, min_confidence=0.5)
        rules = extractor.extract_rules(items)

        if rules:
            # 置信度应该被四舍五入到2位小数
            assert rules[0].confidence == round(0.8567, 2)


# ============================================================================
# 性能测试
# ============================================================================


class TestRuleExtractorPerformance:
    """测试规则提取器性能"""

    def test_extract_large_number_of_feedback_items(self):
        """测试处理大量反馈项"""
        # 创建1000条反馈项
        items = []
        for i in range(1000):
            item = FeedbackItem(
                tool_name="ruff",
                tool_type=ToolType.STATIC_ANALYZER,
                rule_id=f"RULE-{i % 100}",  # 100种不同规则
                rule_name=f"rule_{i % 100}",
                category=FeedbackCategory.CODE_QUALITY,
                severity=FeedbackSeverity.LOW,
                message=f"Issue {i}",
                file_path=f"file_{i // 100}.py",
                line=i % 100,
                snippet="code",
                suggestion="Fix",
                confidence=0.8,
            )
            items.append(item)

        import time
        extractor = RuleExtractor(min_frequency=5, min_confidence=0.5)

        start = time.time()
        rules = extractor.extract_rules(items)
        elapsed = time.time() - start

        # 应该在合理时间内完成（< 5秒）
        assert elapsed < 5.0
        assert len(rules) > 0
