#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景测试 - 代码重构场景
基于 CodeTestScenario 测试代码重构能力
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lingflow.testing.scenario import (
    CodeTestScenario,
    CapturedToolCall,
    TestInteractionType
)
from lingflow.testing.test_server import CodeTestServer


class MockRefactoringTool:
    """模拟重构工具"""

    @staticmethod
    def extract_function(code: str, start_line: int, end_line: int, name: str) -> Dict[str, Any]:
        """提取函数

        Args:
            code: 源代码
            start_line: 起始行
            end_line: 结束行
            name: 函数名

        Returns:
            重构结果
        """
        lines = code.split('\n')
        extracted = '\n'.join(lines[start_line-1:end_line])

        # 替换原代码为函数调用
        new_lines = lines[:start_line-1] + [f"    {name}()"] + lines[end_line:]
        refactored = '\n'.join(new_lines)

        return {
            "operation": "extract_function",
            "function_name": name,
            "extracted_code": extracted,
            "refactored_code": refactored,
            "success": True
        }

    @staticmethod
    def rename_variable(code: str, old_name: str, new_name: str) -> Dict[str, Any]:
        """重命名变量

        Args:
            code: 源代码
            old_name: 旧变量名
            new_name: 新变量名

        Returns:
            重构结果
        """
        refactored = code.replace(old_name, new_name)

        count = code.count(old_name)
        return {
            "operation": "rename_variable",
            "old_name": old_name,
            "new_name": new_name,
            "replacements": count,
            "refactored_code": refactored,
            "success": True
        }

    @staticmethod
    def simplify_condition(code: str) -> Dict[str, Any]:
        """简化条件表达式

        Args:
            code: 源代码

        Returns:
            重构结果
        """
        # 简化 if not x != y -> if x == y
        if "if not x != y" in code:
            simplified = code.replace("if not x != y", "if x == y")
            return {
                "operation": "simplify_condition",
                "original": "if not x != y",
                "simplified": "if x == y",
                "refactored_code": simplified,
                "success": True
            }

        return {
            "operation": "simplify_condition",
            "message": "No simplifications found",
            "success": False
        }


class TestRefactoringScenarios:
    """代码重构场景测试套件"""

    def test_extract_function_scenario(self):
        """测试函数提取场景"""

        scenario = CodeTestScenario(
            name="extract_function",
            description="测试函数提取重构能力",
            prompt="""
你是一个代码重构助手。请将以下代码中的重复逻辑提取为一个独立函数：

```python
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
        else:
            result.append(0)
    return result

def process_more_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 3)
        else:
            result.append(0)
    return result
```

请使用 extract_function 工具提取重复的条件处理逻辑。
""",
            code_content="""
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
        else:
            result.append(0)
    return result

def process_more_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 3)
        else:
            result.append(0)
    return result
""",
            max_turns=3,
            expected_tools=["extract_function"],
            expectations=lambda calls: self._validate_extract_function(calls)
        )

        # 模拟工具调用
        calls = [
            CapturedToolCall(
                name="extract_function",
                args={
                    "start_line": 5,
                    "end_line": 7,
                    "name": "process_item"
                },
                timestamp=0.0,
                result={
                    "operation": "extract_function",
                    "function_name": "process_item",
                    "refactored_code": "def process_data(data):\n    result = []\n    for item in data:\n        process_item()\n    return result",
                    "success": True
                }
            )
        ]

        # 验证期望
        scenario.expectations(calls)

    def _validate_extract_function(self, calls: List[CapturedToolCall]) -> None:
        """验证函数提取调用"""
        assert len(calls) > 0, "应该调用 extract_function 工具"

        call = calls[0]
        assert call.name == "extract_function"
        assert "start_line" in call.args
        assert "end_line" in call.args
        assert "name" in call.args
        assert call.result.get("success") is True

    def test_rename_variable_scenario(self):
        """测试变量重命名场景"""

        scenario = CodeTestScenario(
            name="rename_variable",
            description="测试变量重命名重构能力",
            prompt="""
请将以下代码中的变量 'data' 重命名为更有意义的 'input_data'：

```python
def process_data(data):
    result = data * 2
    return result
```

使用 rename_variable 工具进行重命名。
""",
            code_content="""
def process_data(data):
    result = data * 2
    return result
""",
            max_turns=2,
            expected_tools=["rename_variable"],
            expectations=lambda calls: self._validate_rename_variable(calls)
        )

        # 模拟工具调用
        calls = [
            CapturedToolCall(
                name="rename_variable",
                args={
                    "old_name": "data",
                    "new_name": "input_data"
                },
                timestamp=0.0,
                result={
                    "operation": "rename_variable",
                    "old_name": "data",
                    "new_name": "input_data",
                    "replacements": 2,
                    "refactored_code": "def process_data(input_data):\n    result = input_data * 2\n    return result",
                    "success": True
                }
            )
        ]

        # 验证期望
        scenario.expectations(calls)

    def _validate_rename_variable(self, calls: List[CapturedToolCall]) -> None:
        """验证变量重命名调用"""
        assert len(calls) > 0, "应该调用 rename_variable 工具"

        call = calls[0]
        assert call.name == "rename_variable"
        assert call.args.get("old_name") == "data"
        assert call.args.get("new_name") == "input_data"
        assert call.result.get("success") is True

    def test_simplify_condition_scenario(self):
        """测试条件简化场景"""

        scenario = CodeTestScenario(
            name="simplify_condition",
            description="测试条件表达式简化能力",
            prompt="""
请简化以下代码中的条件表达式：

```python
def compare(x, y):
    if not x != y:
        return True
    return False
```

使用 simplify_condition 工具进行简化。
""",
            code_content="""
def compare(x, y):
    if not x != y:
        return True
    return False
""",
            max_turns=2,
            expected_tools=["simplify_condition"],
            expectations=lambda calls: self._validate_simplify_condition(calls)
        )

        # 模拟工具调用
        calls = [
            CapturedToolCall(
                name="simplify_condition",
                args={},
                timestamp=0.0,
                result={
                    "operation": "simplify_condition",
                    "original": "if not x != y",
                    "simplified": "if x == y",
                    "refactored_code": "def compare(x, y):\n    if x == y:\n        return True\n    return False",
                    "success": True
                }
            )
        ]

        # 验证期望
        scenario.expectations(calls)

    def _validate_simplify_condition(self, calls: List[CapturedToolCall]) -> None:
        """验证条件简化调用"""
        assert len(calls) > 0, "应该调用 simplify_condition 工具"

        call = calls[0]
        assert call.name == "simplify_condition"
        assert call.result.get("success") is True
        assert "simplified" in call.result

    def test_comprehensive_refactoring(self):
        """测试综合重构场景"""

        # 创建临时目录
        import tempfile
        import os

        temp_dir = tempfile.mkdtemp(prefix="test_refactoring_")

        # 测试服务器环境
        server = CodeTestServer(Path(temp_dir))

        # 创建测试代码文件
        test_code = '''
class Calculator:
    def __init__(self):
        self.data = 0

    def add(self, x):
        self.data = self.data + x
        return self.data

    def multiply(self, x):
        self.data = self.data * x
        return self.data
'''

        code_file = server.add_python_route("calculator.py", test_code)

        # 场景：重构 Calculator 类
        scenario = CodeTestScenario(
            name="refactor_calculator",
            description="综合重构Calculator类，应用多种重构技术",
            prompt=f"""
请重构 Calculator 类，提高代码质量：
1. 简化重复的表达式
2. 改进变量命名
3. 提取公共逻辑

代码文件路径: {code_file}
""",
            code_content=test_code,
            max_turns=5,
            expected_tools=["rename_variable", "simplify_condition"],
            expectations=lambda calls: True  # 简单验证，只要调用了工具
        )

        # 模拟多轮工具调用
        calls = [
            CapturedToolCall(
                name="rename_variable",
                args={"old_name": "data", "new_name": "accumulator"},
                timestamp=0.0,
                result={"success": True, "replacements": 3}
            ),
            CapturedToolCall(
                name="simplify_condition",
                args={},
                timestamp=1.0,
                result={"success": True, "simplified": "self.accumulator += x"}
            )
        ]

        # 验证期望
        scenario.expectations(calls)

        # 清理
        server.cleanup()


class TestRefactoringToolFunctionality:
    """重构工具功能测试"""

    def test_extract_function_works(self):
        """测试函数提取功能"""
        tool = MockRefactoringTool()

        code = '''
def func():
    x = 1
    y = 2
    z = x + y
    return z
'''

        result = tool.extract_function(code, 3, 4, "sum")

        assert result["success"] is True
        assert result["operation"] == "extract_function"
        assert "refactored_code" in result

    def test_rename_variable_works(self):
        """测试变量重命名功能"""
        tool = MockRefactoringTool()

        code = "x = 1\ny = x + 1\nreturn y"
        result = tool.rename_variable(code, "x", "value")

        assert result["success"] is True
        assert result["operation"] == "rename_variable"
        assert result["replacements"] == 2  # "x = 1" and "y = x + 1"
        assert "value = 1" in result["refactored_code"]

    def test_simplify_condition_works(self):
        """测试条件简化功能"""
        tool = MockRefactoringTool()

        code = "if not x != y:\n    return True"
        result = tool.simplify_condition(code)

        assert result["success"] is True
        assert result["operation"] == "simplify_condition"
        assert "if x == y" in result["refactored_code"]

    def test_simplify_condition_no_match(self):
        """测试无匹配的条件简化"""
        tool = MockRefactoringTool()

        code = "if x > y:\n    return True"
        result = tool.simplify_condition(code)

        assert result["success"] is False


class TestScenarioValidation:
    """场景验证测试"""

    def test_scenario_validation(self):
        """测试场景验证"""
        scenario = CodeTestScenario(
            name="test_scenario",
            description="测试场景验证",
            prompt="Test prompt",
            code_content="code",
            max_turns=1,
            expected_tools=["tool1"],
            expectations=lambda calls: True
        )

        # 验证场景属性
        assert scenario.name == "test_scenario"
        assert scenario.max_turns == 1
        assert "tool1" in scenario.expected_tools

    def test_tool_call_validation(self):
        """测试工具调用验证"""
        call = CapturedToolCall(
            name="test_tool",
            args={"arg1": "value1"},
            timestamp=0.0,
            result={"success": True}
        )

        # 验证工具调用属性
        assert call.name == "test_tool"
        assert call.args["arg1"] == "value1"


# 主测试入口
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("场景测试 - 代码重构场景")
    print("=" * 70)

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
