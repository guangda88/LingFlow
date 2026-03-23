#!/usr/bin/env python3
"""Check for missing type hints in public functions.

This script checks if public functions (not starting with _) have type hints.
"""

import ast
import sys
from pathlib import Path


class TypeHintChecker(ast.NodeVisitor):
    """Check for type hints in functions."""

    def __init__(self):
        self.functions = []
        self.classes = {}

    def visit_ClassDef(self, node):
        """Visit class definition."""
        class_name = node.name
        self.classes[class_name] = []

        # Save current class context
        old_methods = self.functions
        self.functions = []

        # Visit methods
        self.generic_visit(node)

        # Restore
        self.classes[class_name] = self.functions[:]
        self.functions = old_methods

    def visit_FunctionDef(self, node):
        """Visit function definition."""
        func_info = {
            'name': node.name,
            'line': node.lineno,
            'is_public': not node.name.startswith('_'),
            'has_return_annotation': node.returns is not None,
            'has_param_annotations': all(
                arg.annotation is not None
                for arg in node.args.args
                if arg.arg != 'self' and arg.arg != 'cls'
            )
        }

        self.functions.append(func_info)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition."""
        self.visit_FunctionDef(node)


def check_file(filepath):
    """Check a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=filepath)
        checker = TypeHintChecker()
        checker.visit(tree)

        return checker.functions, checker.classes
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return [], {}
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return [], {}


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: check_type_hints.py <file1.py> [file2.py] ...")
        sys.exit(1)

    issues = []

    for filepath in sys.argv[1:]:
        if not filepath.endswith('.py'):
            continue

        functions, classes = check_file(filepath)

        # Check module-level functions
        for func in functions:
            if func['is_public']:
                if not func['has_param_annotations'] or not func['has_return_annotation']:
                    issues.append({
                        'file': filepath,
                        'type': 'function',
                        'name': func['name'],
                        'line': func['line'],
                        'missing': []
                    })
                    if not func['has_param_annotations']:
                        issues[-1]['missing'].append('parameter annotations')
                    if not func['has_return_annotation']:
                        issues[-1]['missing'].append('return annotation')

        # Check class methods
        for class_name, methods in classes.items():
            for method in methods:
                # Skip __magic__ methods
                if method['name'].startswith('__') and method['name'].endswith('__'):
                    continue

                # Check public and protected methods
                if not method['name'].startswith('__'):
                    if not method['has_param_annotations'] or not method['has_return_annotation']:
                        issues.append({
                            'file': filepath,
                            'type': 'method',
                            'class': class_name,
                            'name': method['name'],
                            'line': method['line'],
                            'missing': []
                        })
                        # Check if 'self' or 'cls' should be excluded from param check
                        if not method['has_param_annotations']:
                            issues[-1]['missing'].append('parameter annotations')
                        if not method['has_return_annotation']:
                            issues[-1]['missing'].append('return annotation')

    if issues:
        print(f"❌ Found {len(issues)} public functions/methods missing type hints:")
        for issue in issues[:10]:  # Show first 10
            missing_str = ' and '.join(issue['missing'])
            if issue['type'] == 'function':
                print(f"  {issue['file']}:{issue['line']} - {issue['name']}() "
                      f"missing {missing_str}")
            else:
                print(f"  {issue['file']}:{issue['line']} - {issue['class']}.{issue['name']}() "
                      f"missing {missing_str}")

        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")

        sys.exit(1)
    else:
        print("✅ All public functions and methods have type hints")
        sys.exit(0)


if __name__ == '__main__':
    main()
