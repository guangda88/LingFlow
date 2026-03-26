#!/usr/bin/env python3
"""简单的复杂度分析工具"""

import ast
import sys
from collections import defaultdict
from pathlib import Path


def analyze_complexity(file_path: str):
    """分析文件的圈复杂度"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)

    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self):
            self.function_complexities = {}
            self.class_methods = defaultdict(list)
            self.current_class = None

        def visit_ClassDef(self, node):
            self.current_class = node.name
            self.generic_visit(node)
            self.current_class = None

        def visit_FunctionDef(self, node):
            complexity = self.calculate_complexity(node)
            name = node.name
            if self.current_class:
                full_name = f"{self.current_class}.{name}"
                self.class_methods[self.current_class].append((name, complexity))
            else:
                full_name = name
            self.function_complexities[full_name] = complexity
            self.generic_visit(node)

        def calculate_complexity(self, node):
            """计算圈复杂度"""
            complexity = 1  # 基础复杂度

            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(child, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1
                elif isinstance(child, (ast.And, ast.Or)):
                    complexity += 1

            return complexity

    visitor = ComplexityVisitor()
    visitor.visit(tree)

    return visitor.function_complexities, visitor.class_methods


def print_report(file_path: str, function_complexities: dict, class_methods: dict):
    """打印复杂度报告"""
    print(f"\n{'='*70}")
    print(f"  复杂度分析报告: {file_path}")
    print(f"{'='*70}")

    high_complexity = []
    medium_complexity = []
    low_complexity = []

    for func, complexity in function_complexities.items():
        if complexity > 10:
            high_complexity.append((func, complexity))
        elif complexity > 5:
            medium_complexity.append((func, complexity))
        else:
            low_complexity.append((func, complexity))

    print(f"\n🔴 高复杂度 (>10): {len(high_complexity)} 个")
    if high_complexity:
        for func, complexity in sorted(high_complexity, key=lambda x: -x[1]):
            print(f"  - {func}: {complexity}")

    print(f"\n🟡 中等复杂度 (6-10): {len(medium_complexity)} 个")
    if medium_complexity:
        for func, complexity in sorted(medium_complexity, key=lambda x: -x[1]):
            print(f"  - {func}: {complexity}")

    print(f"\n🟢 低复杂度 (1-5): {len(low_complexity)} 个")

    avg_complexity = sum(function_complexities.values()) / len(function_complexities) if function_complexities else 0
    max_complexity = max(function_complexities.values()) if function_complexities else 0

    print(f"\n📊 统计:")
    print(f"  - 总函数数: {len(function_complexities)}")
    print(f"  - 平均复杂度: {avg_complexity:.1f}")
    print(f"  - 最大复杂度: {max_complexity}")

    # 按类分组
    if class_methods:
        print(f"\n📦 类方法详情:")
        for class_name, methods in class_methods.items():
            class_max = max(m[1] for m in methods) if methods else 0
            class_avg = sum(m[1] for m in methods) / len(methods) if methods else 0
            print(f"  {class_name}:")
            print(f"    - 方法数: {len(methods)}")
            print(f"    - 平均复杂度: {class_avg:.1f}")
            print(f"    - 最大复杂度: {class_max}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python simple_complexity.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    function_complexities, class_methods = analyze_complexity(file_path)
    print_report(file_path, function_complexities, class_methods)
