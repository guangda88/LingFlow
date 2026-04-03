#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景驱动的 AI 测试框架
参考 Chrome DevTools MCP 的 eval_scenarios 模式
"""

from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class TestInteractionType(Enum):
    """测试交互类型"""

    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REFACTORING = "code_refactoring"
    BUG_DETECTION = "bug_detection"
    SECURITY_SCAN = "security_scan"
    PERFORMANCE_TEST = "performance_test"


@dataclass
class CapturedToolCall:
    """捕获的工具调用"""

    name: str
    args: Dict[str, Any]
    timestamp: float
    result: Optional[Any] = None


@dataclass
class CodeTestScenario:
    """代码测试场景定义

    基于 Chrome DevTools MCP 的 TestScenario 模式
    支持场景驱动的 AI 测试评估
    """

    # 基础信息
    name: str  # 场景名称
    prompt: str  # AI 提示词
    description: str  # 场景描述

    # 代码内容
    code_content: str  # 测试代码片段
    language: str = "python"  # 编程语言

    # 测试配置
    max_turns: int = 3  # 最大交互轮数
    timeout: int = 60  # 超时时间（秒）

    # 工具期望
    expected_tools: List[str] = field(default_factory=list)  # 期望调用的工具列表
    required_tools: List[str] = field(default_factory=list)  # 必须调用的工具列表

    # 期望验证
    expectations: Optional[Callable[[List[CapturedToolCall]], None]] = None

    # 额外上下文
    context: Dict[str, Any] = field(default_factory=dict)

    # 场景元数据
    category: TestInteractionType = TestInteractionType.CODE_ANALYSIS
    priority: int = 1  # 优先级（1-5，5最高）
    tags: List[str] = field(default_factory=list)  # 标签

    def validate(self) -> bool:
        """验证场景配置是否有效"""
        if not self.name:
            raise ValueError("Scenario name is required")
        if not self.prompt:
            raise ValueError("Scenario prompt is required")
        if not self.code_content:
            raise ValueError("Scenario code_content is required")
        if self.max_turns < 1:
            raise ValueError("max_turns must be at least 1")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "prompt": self.prompt,
            "description": self.description,
            "code_content": self.code_content,
            "language": self.language,
            "max_turns": self.max_turns,
            "timeout": self.timeout,
            "expected_tools": self.expected_tools,
            "required_tools": self.required_tools,
            "category": self.category.value,
            "priority": self.priority,
            "tags": self.tags,
            "context": self.context,
        }


# 预定义场景

REFACTORING_SCENARIO = CodeTestScenario(
    name="refactor_complex_function",
    prompt="重构这个函数，降低复杂度并保持功能不变",
    description="测试代码重构能力，要求降低圈复杂度",
    code_content="""
def process_user_data(users, filters, options):
    result = []
    for user in users:
        if user.active:
            for f in filters:
                if f.match(user):
                    if options.get('include_admin') or user.role != 'admin':
                        if options.get('verified_only') and user.verified:
                            result.append(transform(user))
                        elif not options.get('verified_only'):
                            result.append(transform(user))
    return result
""",
    language="python",
    max_turns=5,
    expected_tools=["analyze_complexity", "identify_smells", "suggest_refactoring", "apply_refactoring", "verify_equivalence"],
    category=TestInteractionType.CODE_REFACTORING,
    priority=5,
    tags=["refactoring", "complexity", "optimization"],
)


DETECT_SECURITY_ISSUE = CodeTestScenario(
    name="detect_sql_injection",
    prompt="检查这段代码的安全问题，特别是 SQL 注入漏洞",
    description="测试安全漏洞检测能力",
    code_content="""
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return execute(query)
""",
    language="python",
    max_turns=3,
    expected_tools=["security_scan", "sql_injection_check", "report_vulnerability"],
    required_tools=["security_scan"],
    category=TestInteractionType.SECURITY_SCAN,
    priority=5,
    tags=["security", "sql_injection", "vulnerability"],
)


OPTIMIZATION_SCENARIO = CodeTestScenario(
    name="optimize_performance",
    prompt="优化这段代码的性能，提高执行效率",
    description="测试性能优化建议能力",
    code_content="""
def find_duplicates(items):
    duplicates = []
    for i, item1 in enumerate(items):
        for j, item2 in enumerate(items):
            if i != j and item1 == item2:
                if item1 not in duplicates:
                    duplicates.append(item1)
    return duplicates
""",
    language="python",
    max_turns=4,
    expected_tools=["analyze_performance", "identify_bottlenecks", "suggest_optimizations"],
    category=TestInteractionType.PERFORMANCE_TEST,
    priority=4,
    tags=["performance", "optimization", "efficiency"],
)


def create_custom_scenario(
    name: str, prompt: str, code_content: str, description: str = "Custom scenario", **kwargs
) -> CodeTestScenario:
    """创建自定义测试场景"""
    return CodeTestScenario(name=name, prompt=prompt, code_content=code_content, description=description, **kwargs)


if __name__ == "__main__":  # pragma: no cover
    # 示例：运行场景验证
    print("验证预定义场景...")

    for scenario in [REFACTORING_SCENARIO, DETECT_SECURITY_ISSUE, OPTIMIZATION_SCENARIO]:
        try:
            scenario.validate()
            print(f"✅ 场景 '{scenario.name}' 验证通过")
            print(f"   类型: {scenario.category.value}")
            print(f"   期望工具: {', '.join(scenario.expected_tools)}")
        except ValueError as e:
            print(f"❌ 场景 '{scenario.name}' 验证失败: {e}")
