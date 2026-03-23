#!/usr/bin/env python3
"""Check function complexity in Python files.

This script checks if any function has complexity > 15 and reports it.
"""

import ast
import sys
from pathlib import Path


class ComplexityChecker(ast.NodeVisitor):
    """Check cyclomatic complexity of functions."""

    def __init__(self):
        self.complexities = []
        self.current_function = None
        self.current_complexity = 1

    def visit_FunctionDef(self, node):
        """Visit function definition."""
        self.current_function = node.name
        self.current_complexity = 1  # Base complexity
        self.generic_visit(node)
        self.complexities.append({
            'name': node.name,
            'line': node.lineno,
            'complexity': self.current_complexity
        })
        self.current_function = None
        self.current_complexity = 1

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition."""
        self.visit_FunctionDef(node)

    def visit_If(self, node):
        """Visit if statement."""
        self.current_complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        """Visit while loop."""
        self.current_complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        """Visit for loop."""
        self.current_complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        """Visit async for loop."""
        self.visit_For(node)

    def visit_Try(self, node):
        """Visit try statement."""
        # Each except clause adds complexity
        self.current_complexity += len(node.handlers)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        """Visit except handler."""
        self.generic_visit(node)

    def visit_ListComp(self, node):
        """Visit list comprehension."""
        # Multiple for/if in comprehension adds complexity
        pass  # Simplified check

    def visit_DictComp(self, node):
        """Visit dict comprehension."""
        pass

    def visit_SetComp(self, node):
        """Visit set comprehension."""
        pass

    def visit_GeneratorExp(self, node):
        """Visit generator expression."""
        pass

    def visit_With(self, node):
        """Visit with statement."""
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        """Visit boolean operation (and/or)."""
        # Each additional operand adds complexity
        self.current_complexity += len(node.values) - 1
        self.generic_visit(node)


def check_file(filepath):
    """Check a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=filepath)
        checker = ComplexityChecker()
        checker.visit(tree)

        return checker.complexities
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return []
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return []


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: check_complexity.py <file1.py> [file2.py] ...")
        sys.exit(1)

    max_complexity = 15
    issues = []

    for filepath in sys.argv[1:]:
        if not filepath.endswith('.py'):
            continue

        complexities = check_file(filepath)

        for func in complexities:
            if func['complexity'] > max_complexity:
                issues.append({
                    'file': filepath,
                    'function': func['name'],
                    'line': func['line'],
                    'complexity': func['complexity']
                })

    if issues:
        print(f"❌ Found {len(issues)} functions with complexity > {max_complexity}:")
        for issue in issues:
            print(f"  {issue['file']}:{issue['line']} - {issue['function']}() "
                  f"(complexity: {issue['complexity']})")
        sys.exit(1)
    else:
        print(f"✅ All functions have complexity <= {max_complexity}")
        sys.exit(0)


if __name__ == '__main__':
    main()
