#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试 - 场景定义系统
"""

import pytest
from pathlib import Path

from lingflow.testing import (
    CodeTestScenario,
    TestInteractionType,
    REFACTORING_SCENARIO,
    DETECT_SECURITY_ISSUE,
    OPTIMIZATION_SCENARIO,
    create_custom_scenario
)


class TestCodeTestScenario:
    """测试 CodeTestScenario"""

    def test_create_scenario_success(self):
        """测试成功创建场景"""
        scenario = CodeTestScenario(
            name="test_scenario",
            prompt="测试提示词",
            description="测试描述",
            code_content="def foo(): pass"
        )

        assert scenario.name == "test_scenario"
        assert scenario.prompt == "测试提示词"
        assert scenario.code_content == "def foo(): pass"
        assert scenario.max_turns == 3
        assert scenario.language == "python"

    def test_validate_success(self):
        """测试验证成功"""
        scenario = CodeTestScenario(
            name="test",
            prompt="提示词",
            description="描述",
            code_content="x = 1"
        )

        assert scenario.validate() is True

    def test_validate_missing_name(self):
        """测试缺少名称验证失败"""
        scenario = CodeTestScenario(
            name="",
            prompt="提示词",
            description="描述",
            code_content="x = 1"
        )

        with pytest.raises(ValueError, match="Scenario name is required"):
            scenario.validate()

    def test_validate_missing_prompt(self):
        """测试缺少提示词验证失败"""
        scenario = CodeTestScenario(
            name="test",
            prompt="",
            description="描述",
            code_content="x = 1"
        )

        with pytest.raises(ValueError, match="Scenario prompt is required"):
            scenario.validate()

    def test_validate_missing_code(self):
        """测试缺少代码验证失败"""
        scenario = CodeTestScenario(
            name="test",
            prompt="提示词",
            description="描述",
            code_content=""
        )

        with pytest.raises(ValueError, match="Scenario code_content is required"):
            scenario.validate()

    def test_validate_invalid_max_turns(self):
        """测试无效最大轮数验证失败"""
        scenario = CodeTestScenario(
            name="test",
            prompt="提示词",
            description="描述",
            code_content="x = 1",
            max_turns=0
        )

        with pytest.raises(ValueError, match="max_turns must be at least 1"):
            scenario.validate()

    def test_to_dict(self):
        """测试转换为字典"""
        scenario = CodeTestScenario(
            name="test",
            prompt="提示词",
            description="描述",
            code_content="x = 1",
            max_turns=5,
            tags=["test", "demo"]
        )

        data = scenario.to_dict()

        assert data["name"] == "test"
        assert data["prompt"] == "提示词"
        assert data["max_turns"] == 5
        assert data["tags"] == ["test", "demo"]
        assert data["category"] == TestInteractionType.CODE_ANALYSIS.value


class TestPredefinedScenarios:
    """测试预定义场景"""

    def test_refactoring_scenario_exists(self):
        """测试重构场景存在"""
        assert REFACTORING_SCENARIO is not None
        assert REFACTORING_SCENARIO.name == "refactor_complex_function"
        assert REFACTORING_SCENARIO.category == TestInteractionType.CODE_REFACTORING

    def test_security_scenario_exists(self):
        """测试安全场景存在"""
        assert DETECT_SECURITY_ISSUE is not None
        assert DETECT_SECURITY_ISSUE.name == "detect_sql_injection"
        assert DETECT_SECURITY_ISSUE.category == TestInteractionType.SECURITY_SCAN

    def test_optimization_scenario_exists(self):
        """测试优化场景存在"""
        assert OPTIMIZATION_SCENARIO is not None
        assert OPTIMIZATION_SCENARIO.name == "optimize_performance"
        assert OPTIMIZATION_SCENARIO.category == TestInteractionType.PERFORMANCE_TEST

    def test_scenarios_validate(self):
        """测试预定义场景验证通过"""
        scenarios = [
            REFACTORING_SCENARIO,
            DETECT_SECURITY_ISSUE,
            OPTIMIZATION_SCENARIO
        ]

        for scenario in scenarios:
            assert scenario.validate() is True

    def test_refactoring_scenario_tools(self):
        """测试重构场景期望工具"""
        expected_tools = [
            "analyze_complexity",
            "identify_smells",
            "suggest_refactoring",
            "apply_refactoring",
            "verify_equivalence"
        ]

        assert REFACTORING_SCENARIO.expected_tools == expected_tools
        assert "analyze_complexity" in REFACTORING_SCENARIO.expected_tools

    def test_security_scenario_required_tools(self):
        """测试安全场景必需工具"""
        assert "security_scan" in DETECT_SECURITY_ISSUE.required_tools
        assert DETECT_SECURITY_ISSUE.required_tools == ["security_scan"]


class TestCreateCustomScenario:
    """测试创建自定义场景"""

    def test_create_custom_scenario_success(self):
        """测试成功创建自定义场景"""
        scenario = create_custom_scenario(
            name="custom_test",
            prompt="自定义提示词",
            code_content="def custom(): pass",
            description="自定义描述"
        )

        assert scenario.name == "custom_test"
        assert scenario.prompt == "自定义提示词"
        assert scenario.validate() is True

    def test_create_custom_scenario_with_kwargs(self):
        """测试使用 kwargs 创建自定义场景"""
        scenario = create_custom_scenario(
            name="custom_test",
            prompt="提示词",
            code_content="x = 1",
            max_turns=10,
            timeout=120,
            priority=5
        )

        assert scenario.max_turns == 10
        assert scenario.timeout == 120
        assert scenario.priority == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
