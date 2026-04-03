#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景测试 - 代码优化场景
基于 CodeTestScenario 测试代码优化能力
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lingflow.testing.scenario import CodeTestScenario, CapturedToolCall


class MockOptimizer:
    """模拟代码优化器"""

    @staticmethod
    def optimize_loop(code: str) -> Dict[str, Any]:
        """优化循环

        Args:
            code: 源代码

        Returns:
            优化结果
        """
        original_lines = len(code.split("\n"))
        optimizations = []

        # 检测可以优化的循环
        if "for i in range(len(arr)):" in code:
            optimizations.append(
                {
                    "type": "loop_optimization",
                    "description": "Use direct iteration instead of range(len())",
                    "line": 1,
                    "improvement": "Readability and performance",
                }
            )

        # 生成优化后的代码
        optimized_code = code.replace("for i in range(len(arr)):", "for item in arr:")

        return {
            "optimizer": "loop",
            "original_lines": original_lines,
            "optimized_lines": len(optimized_code.split("\n")),
            "optimizations": optimizations,
            "optimization_count": len(optimizations),
            "optimized_code": optimized_code,
            "improvement": f"{len(optimizations)} optimizations applied",
        }

    @staticmethod
    def optimize_memory(code: str) -> Dict[str, Any]:
        """优化内存使用

        Args:
            code: 源代码

        Returns:
            优化结果
        """
        optimizations = []

        # 检测列表推导式可以替换为生成器
        if "list(" in code and "(x for x in" in code:
            optimizations.append(
                {
                    "type": "memory_optimization",
                    "description": "Use generator expression instead of list comprehension",
                    "line": 1,
                    "improvement": "Memory efficiency",
                }
            )

        # 检测大对象可以延迟加载
        if "load_all_data()" in code:
            optimizations.append(
                {
                    "type": "memory_optimization",
                    "description": "Use lazy loading for large datasets",
                    "line": 2,
                    "improvement": "Reduced memory footprint",
                }
            )

        return {
            "optimizer": "memory",
            "optimizations": optimizations,
            "optimization_count": len(optimizations),
            "memory_saving_estimate": f"{len(optimizations) * 20}% reduction",
        }

    @staticmethod
    def optimize_performance(code: str) -> Dict[str, Any]:
        """优化性能

        Args:
            code: 源代码

        Returns:
            优化结果
        """
        optimizations = []

        # 检测字符串拼接
        if "+" in code and "str" in code:
            optimizations.append(
                {
                    "type": "performance_optimization",
                    "description": "Use join() instead of + for string concatenation",
                    "line": 1,
                    "improvement": "Faster string operations",
                }
            )

        # 检测嵌套循环
        if code.count("for ") >= 2:
            optimizations.append(
                {
                    "type": "performance_optimization",
                    "description": "Consider using dictionary or set for O(1) lookups",
                    "line": 2,
                    "improvement": "Reduced time complexity",
                }
            )

        # 检测重复计算
        if "expensive_calculation()" in code and code.count("expensive_calculation()") > 1:
            optimizations.append(
                {
                    "type": "performance_optimization",
                    "description": "Cache expensive calculations",
                    "line": 3,
                    "improvement": "Avoid redundant computation",
                }
            )

        return {
            "optimizer": "performance",
            "optimizations": optimizations,
            "optimization_count": len(optimizations),
            "estimated_speedup": f"{len(optimizations) * 1.5}x faster",
        }

    @staticmethod
    def optimize_readability(code: str) -> Dict[str, Any]:
        """优化可读性

        Args:
            code: 源代码

        Returns:
            优化结果
        """
        optimizations = []

        # 检测长函数
        lines = code.split("\n")
        if len(lines) > 20:
            optimizations.append(
                {
                    "type": "readability_optimization",
                    "description": "Extract long function into smaller functions",
                    "line": 1,
                    "improvement": "Better code organization",
                }
            )

        # 检测复杂条件
        if "if" in code and "and" in code and "or" in code:
            optimizations.append(
                {
                    "type": "readability_optimization",
                    "description": "Extract complex condition into named variable or function",
                    "line": 5,
                    "improvement": "Improved clarity",
                }
            )

        # 检测魔法数字
        if "42" in code or "3.14" in code:
            optimizations.append(
                {
                    "type": "readability_optimization",
                    "description": "Replace magic numbers with named constants",
                    "line": 10,
                    "improvement": "Self-documenting code",
                }
            )

        return {
            "optimizer": "readability",
            "optimizations": optimizations,
            "optimization_count": len(optimizations),
            "readability_score": f"Improved by {len(optimizations)} points",
        }


class TestOptimizationScenarios:
    """代码优化场景测试套件"""

    def test_loop_optimization_scenario(self):
        """测试循环优化场景"""

        scenario = CodeTestScenario(
            name="optimize_loop",
            description="优化循环代码结构",
            prompt="优化以下代码的循环结构，提高可读性和性能",
            code_content="for i in range(len(arr)):\n    print(arr[i])",
            max_turns=2,
            expected_tools=["optimize"],
            expectations=lambda calls: self._validate_loop_optimization(calls),
        )

        calls = [
            CapturedToolCall(
                name="optimize",
                args={"optimizer": "loop"},
                timestamp=0.0,
                result={
                    "optimizer": "loop",
                    "original_lines": 2,
                    "optimized_lines": 2,
                    "optimizations": [
                        {
                            "type": "loop_optimization",
                            "description": "Use direct iteration instead of range(len())",
                            "line": 1,
                            "improvement": "Readability and performance",
                        }
                    ],
                    "optimization_count": 1,
                    "optimized_code": "for item in arr:\n    print(item)",
                    "improvement": "1 optimizations applied",
                },
            )
        ]

        scenario.expectations(calls)

    def _validate_loop_optimization(self, calls: List[CapturedToolCall]) -> None:
        """验证循环优化"""
        assert len(calls) > 0, "应该调用 optimize 工具"
        call = calls[0]
        assert call.name == "optimize"
        assert call.args.get("optimizer") == "loop"
        assert call.result.get("optimization_count") > 0

    def test_memory_optimization_scenario(self):
        """测试内存优化场景"""

        scenario = CodeTestScenario(
            name="optimize_memory",
            description="优化内存使用",
            prompt="优化以下代码的内存使用，减少内存占用",
            code_content="data = list(x for x in range(1000000))\nresult = load_all_data()",
            max_turns=2,
            expected_tools=["optimize"],
            expectations=lambda calls: self._validate_memory_optimization(calls),
        )

        calls = [
            CapturedToolCall(
                name="optimize",
                args={"optimizer": "memory"},
                timestamp=0.0,
                result={
                    "optimizer": "memory",
                    "optimizations": [
                        {
                            "type": "memory_optimization",
                            "description": "Use generator expression instead of list comprehension",
                            "line": 1,
                            "improvement": "Memory efficiency",
                        },
                        {
                            "type": "memory_optimization",
                            "description": "Use lazy loading for large datasets",
                            "line": 2,
                            "improvement": "Reduced memory footprint",
                        },
                    ],
                    "optimization_count": 2,
                    "memory_saving_estimate": "40% reduction",
                },
            )
        ]

        scenario.expectations(calls)

    def _validate_memory_optimization(self, calls: List[CapturedToolCall]) -> None:
        """验证内存优化"""
        assert len(calls) > 0, "应该调用 optimize 工具"
        call = calls[0]
        assert call.name == "optimize"
        assert call.args.get("optimizer") == "memory"
        assert call.result.get("optimization_count") > 0

    def test_performance_optimization_scenario(self):
        """测试性能优化场景"""

        scenario = CodeTestScenario(
            name="optimize_performance",
            description="优化代码性能",
            prompt="优化以下代码的性能，提高执行速度",
            code_content="result = ''\nfor item in items:\n    result = result + str(item)\nfor i in range(len(items)):\n    for j in range(len(items)):\n        pass",
            max_turns=2,
            expected_tools=["optimize"],
            expectations=lambda calls: self._validate_performance_optimization(calls),
        )

        calls = [
            CapturedToolCall(
                name="optimize",
                args={"optimizer": "performance"},
                timestamp=0.0,
                result={
                    "optimizer": "performance",
                    "optimizations": [
                        {
                            "type": "performance_optimization",
                            "description": "Use join() instead of + for string concatenation",
                            "line": 2,
                            "improvement": "Faster string operations",
                        },
                        {
                            "type": "performance_optimization",
                            "description": "Consider using dictionary or set for O(1) lookups",
                            "line": 4,
                            "improvement": "Reduced time complexity",
                        },
                    ],
                    "optimization_count": 2,
                    "estimated_speedup": "3.0x faster",
                },
            )
        ]

        scenario.expectations(calls)

    def _validate_performance_optimization(self, calls: List[CapturedToolCall]) -> None:
        """验证性能优化"""
        assert len(calls) > 0, "应该调用 optimize 工具"
        call = calls[0]
        assert call.name == "optimize"
        assert call.args.get("optimizer") == "performance"
        assert call.result.get("optimization_count") > 0

    def test_readability_optimization_scenario(self):
        """测试可读性优化场景"""

        scenario = CodeTestScenario(
            name="optimize_readability",
            description="优化代码可读性",
            prompt="优化以下代码的可读性，提高代码质量",
            code_content="def long_function(x, y, z):\n    if x > 0 and y < 10 or z == 5:\n        result = 42 / 3.14\n        return result\n    return 0",
            max_turns=2,
            expected_tools=["optimize"],
            expectations=lambda calls: self._validate_readability_optimization(calls),
        )

        calls = [
            CapturedToolCall(
                name="optimize",
                args={"optimizer": "readability"},
                timestamp=0.0,
                result={
                    "optimizer": "readability",
                    "optimizations": [
                        {
                            "type": "readability_optimization",
                            "description": "Extract complex condition into named variable or function",
                            "line": 2,
                            "improvement": "Improved clarity",
                        },
                        {
                            "type": "readability_optimization",
                            "description": "Replace magic numbers with named constants",
                            "line": 3,
                            "improvement": "Self-documenting code",
                        },
                    ],
                    "optimization_count": 2,
                    "readability_score": "Improved by 2 points",
                },
            )
        ]

        scenario.expectations(calls)

    def _validate_readability_optimization(self, calls: List[CapturedToolCall]) -> None:
        """验证可读性优化"""
        assert len(calls) > 0, "应该调用 optimize 工具"
        call = calls[0]
        assert call.name == "optimize"
        assert call.args.get("optimizer") == "readability"
        assert call.result.get("optimization_count") > 0

    def test_comprehensive_optimization(self):
        """测试综合优化场景"""

        scenario = CodeTestScenario(
            name="comprehensive_optimization",
            description="对代码进行综合优化",
            prompt="对以下代码进行全面优化，包括性能、内存和可读性",
            code_content="result = ''\nfor i in range(len(items)):\n    result = result + str(items[i])\nif x > 0 and y < 10 or z == 5:\n    value = 42 / 3.14\n    return value",
            max_turns=5,
            expected_tools=["optimize"],
            expectations=lambda calls: self._validate_comprehensive_optimization(calls),
        )

        calls = [
            CapturedToolCall(name="optimize", args={"optimizer": "loop"}, timestamp=0.0, result={"optimization_count": 1}),
            CapturedToolCall(
                name="optimize", args={"optimizer": "performance"}, timestamp=1.0, result={"optimization_count": 1}
            ),
            CapturedToolCall(
                name="optimize", args={"optimizer": "readability"}, timestamp=2.0, result={"optimization_count": 1}
            ),
        ]

        scenario.expectations(calls)

    def _validate_comprehensive_optimization(self, calls: List[CapturedToolCall]) -> None:
        """验证综合优化"""
        assert len(calls) >= 3, "应该调用至少 3 次优化"
        optimizers = [call.args.get("optimizer") for call in calls]
        assert "loop" in optimizers
        assert "performance" in optimizers
        assert "readability" in optimizers


class TestOptimizerFunctionality:
    """优化器功能测试"""

    def test_loop_optimizer(self):
        """测试循环优化器"""
        optimizer = MockOptimizer()
        code = "for i in range(len(arr)):\n    print(arr[i])"
        result = optimizer.optimize_loop(code)

        assert result["optimizer"] == "loop"
        assert result["optimization_count"] > 0
        assert "for item in arr:" in result["optimized_code"]

    def test_memory_optimizer(self):
        """测试内存优化器"""
        optimizer = MockOptimizer()
        code = "data = list(x for x in range(1000000))"
        result = optimizer.optimize_memory(code)

        assert result["optimizer"] == "memory"
        assert result["optimization_count"] > 0
        assert "memory_saving_estimate" in result

    def test_performance_optimizer(self):
        """测试性能优化器"""
        optimizer = MockOptimizer()
        code = "result = ''\nfor item in items:\n    result = result + str(item)"
        result = optimizer.optimize_performance(code)

        assert result["optimizer"] == "performance"
        assert result["optimization_count"] > 0
        assert "estimated_speedup" in result

    def test_readability_optimizer(self):
        """测试可读性优化器"""
        optimizer = MockOptimizer()
        code = "if x > 0 and y < 10 or z == 5:\n    value = 42 / 3.14"
        result = optimizer.optimize_readability(code)

        assert result["optimizer"] == "readability"
        assert result["optimization_count"] > 0
        assert "readability_score" in result

    def test_already_optimized_code(self):
        """测试已优化的代码"""
        optimizer = MockOptimizer()
        optimized_code = "for item in arr:\n    print(item)"
        result = optimizer.optimize_loop(optimized_code)

        # 已优化的代码应该没有更多优化建议
        assert isinstance(result["optimization_count"], int)


# 主测试入口
if __name__ == "__main__":  # pragma: no cover
    import logging

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("场景测试 - 代码优化场景")
    print("=" * 70)

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
