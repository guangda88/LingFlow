#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快照测试 - 代码分析输出稳定性测试
基于 SnapshotTest 进行回归检测
"""

import pytest
import ast
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lingflow.testing.snapshot import SnapshotTest, SnapshotMetadata


class CodeAnalyzer:
    """简单的代码分析器 - 用于快照测试

    这个分析器会分析 Python 代码的：
    - 函数定义
    - 类定义
    - 复杂度指标
    - 导入语句
    - 代码行数
    """

    @staticmethod
    def analyze_code(code: str) -> Dict[str, Any]:
        """分析 Python 代码

        Args:
            code: Python 源代码

        Returns:
            分析结果字典
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"error": "SyntaxError", "message": str(e), "success": False}

        result = {
            "success": True,
            "functions": [],
            "classes": [],
            "imports": [],
            "stats": {"total_lines": len(code.splitlines()), "blank_lines": 0, "comment_lines": 0, "code_lines": 0},
            "complexity": 0,
            "warnings": [],
        }

        # 分析代码
        for node in ast.walk(tree):
            # 函数定义
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [d.id if isinstance(d, ast.Name) else str(type(d).__name__) for d in node.decorator_list],
                    "has_return": any(isinstance(n, ast.Return) for n in ast.walk(node)),
                }
                result["functions"].append(func_info)
                result["complexity"] += 1

            # 类定义
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "bases": [base.id if isinstance(base, ast.Name) else str(type(base).__name__) for base in node.bases],
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                }
                result["classes"].append(class_info)

            # 导入语句
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append({"module": alias.name, "alias": alias.asname, "lineno": node.lineno})

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    result["imports"].append(
                        {"module": node.module, "name": alias.name, "alias": alias.asname, "lineno": node.lineno}
                    )

        # 统计代码行数
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                result["stats"]["blank_lines"] += 1
            elif stripped.startswith("#"):
                result["stats"]["comment_lines"] += 1
            else:
                result["stats"]["code_lines"] += 1

        # 生成警告
        if len(result["functions"]) > 10:
            result["warnings"].append(f"函数数量过多: {len(result['functions'])}")

        if result["complexity"] > 15:
            result["warnings"].append(f"复杂度过高: {result['complexity']}")

        return result


# 创建快照测试实例
snapshot_dir = Path(__file__).parent.parent / "fixtures" / "snapshots"
snapshot = SnapshotTest(snapshot_dir)

# 创建代码分析器
analyzer = CodeAnalyzer()


class TestCodeAnalysisSnapshots:
    """代码分析快照测试套件

    这些测试确保代码分析器的输出在不同版本间保持稳定
    """

    def test_simple_function_analysis(self):
        """测试简单函数分析"""
        code = """
def calculate_sum(a: int, b: int) -> int:
    return a + b
"""
        result = analyzer.analyze_code(code)
        snapshot.assert_match("simple_function_analysis", result)

    def test_class_analysis(self):
        """测试类分析"""
        code = """
class Calculator:
    def __init__(self):
        self.value = 0

    def add(self, x: int) -> int:
        self.value += x
        return self.value

    def subtract(self, x: int) -> int:
        self.value -= x
        return self.value
"""
        result = analyzer.analyze_code(code)
        snapshot.assert_match("class_analysis", result)

    def test_complex_code_analysis(self):
        """测试复杂代码分析"""
        code = """
from typing import List, Dict, Optional
import os
import sys

class DataProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data: List[Dict] = []
        self.processed_count = 0

    def load_data(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        with open(path, 'r') as f:
            self.data = json.load(f)
        return True

    def process_item(self, item: Dict) -> Optional[Dict]:
        if not item:
            return None
        result = {"id": item.get("id"), "value": item.get("value", 0)}
        self.processed_count += 1
        return result

    def batch_process(self, items: List[Dict]) -> List[Dict]:
        results = []
        for item in items:
            processed = self.process_item(item)
            if processed:
                results.append(processed)
        return results
"""
        result = analyzer.analyze_code(code)
        snapshot.assert_match("complex_code_analysis", result)

    def test_decorator_analysis(self):
        """测试装饰器分析"""
        code = """
def cache(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@cache
def expensive_computation(x: int) -> int:
    return x ** 2
"""
        result = analyzer.analyze_code(code)
        snapshot.assert_match("decorator_analysis", result)

    def test_import_analysis(self):
        """测试导入分析"""
        code = """
import os
import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict as dd
"""
        result = analyzer.analyze_code(code)
        snapshot.assert_match("import_analysis", result)

    def test_syntax_error_detection(self):
        """测试语法错误检测"""
        code = """
def broken_function(
    return "missing closing parenthesis"
"""
        result = analyzer.analyze_code(code)
        snapshot.assert_match("syntax_error_detection", result)

    def test_statistics_calculation(self):
        """测试统计计算"""
        code = '''
# This is a comment
def function1():
    """Function docstring"""
    pass

def function2():
    return 42


class MyClass:
    pass
'''
        result = analyzer.analyze_code(code)
        snapshot.assert_match("statistics_calculation", result)

    def test_complexity_analysis(self):
        """测试复杂度分析"""
        code = """
def high_complexity_function():
    def helper1():
        pass
    def helper2():
        pass
    def helper3():
        pass
    return helper1, helper2, helper3
"""
        result = analyzer.analyze_code(code)
        snapshot.assert_match("complexity_analysis", result)

    def test_nested_classes(self):
        """测试嵌套类"""
        code = """
class OuterClass:
    def __init__(self):
        self.value = 0

    def process(self):
        class InnerClass:
            def __init__(self):
                self.data = []
        return InnerClass()
"""
        result = analyzer.analyze_code(code)
        snapshot.assert_match("nested_classes", result)

    def test_method_analysis(self):
        """测试方法分析"""
        code = """
class Service:
    def __init__(self, config):
        self.config = config

    def get_config(self, key):
        return self.config.get(key)

    def set_config(self, key, value):
        self.config[key] = value
"""
        result = analyzer.analyze_code(code)
        snapshot.assert_match("method_analysis", result)


class TestRegressionDetection:
    """回归检测测试

    这些测试验证快照机制能够正确检测输出变化
    """

    def test_unchanged_output_stable(self):
        """未改变的输出应该保持稳定"""
        code = """
def stable_function():
    return "unchanged"
"""
        result1 = analyzer.analyze_code(code)
        result2 = analyzer.analyze_code(code)

        # 两次分析应该产生相同的结果
        assert result1 == result2

    def test_different_outputs_detected(self):
        """不同的输出应该被检测到"""
        code1 = "def func(): return None"
        code2 = "def func(x): return x"

        result1 = analyzer.analyze_code(code1)
        result2 = analyzer.analyze_code(code2)

        # 应该检测到差异（参数数量不同）
        assert result1 != result2

    def test_snapshot_metadata_preserved(self):
        """快照元数据应该被保留"""
        metadata = SnapshotMetadata(test_name="metadata_test", created_at="2024-01-01T00:00:00", description="测试元数据保留")

        result = {"value": 42}
        snapshot.assert_match("metadata_test", result, metadata=metadata)

        # 验证快照文件存在
        snapshot_path = snapshot._get_snapshot_path("metadata_test")
        assert snapshot_path.exists()

        # 验证元数据被保存
        loaded = snapshot._load_snapshot(snapshot_path)
        assert loaded["metadata"]["test_name"] == "metadata_test"
        assert loaded["metadata"]["description"] == "测试元数据保留"


class TestSnapshotManagement:
    """快照管理测试"""

    def test_list_snapshots(self):
        """测试列出快照"""
        snapshots = snapshot.list_snapshots()
        assert isinstance(snapshots, list)

    def test_update_existing_snapshot(self):
        """测试更新现有快照"""
        code = "def update_test(): return 'updated'"

        # 首次创建
        result1 = analyzer.analyze_code(code)
        snapshot.assert_match("update_test", result1, update=True)

        # 更新
        result2 = analyzer.analyze_code(code)
        snapshot.assert_match("update_test", result2, update=True)

        # 验证可以匹配
        result3 = analyzer.analyze_code(code)
        assert snapshot.assert_match("update_test", result3) is True

    def test_remove_snapshot(self):
        """测试移除快照"""
        # 先创建一个快照
        code = "def temp_test(): return 'temp'"
        result = analyzer.analyze_code(code)
        snapshot.assert_match("temp_test", result, update=True)

        # 移除快照
        removed = snapshot.remove_snapshot("temp_test")
        assert removed is True

        # 验证快照不存在
        removed_again = snapshot.remove_snapshot("temp_test")
        assert removed_again is False


# 主测试入口
if __name__ == "__main__":  # pragma: no cover
    import logging

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("快照测试 - 代码分析输出稳定性测试")
    print("=" * 70)

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
