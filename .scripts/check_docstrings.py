#!/usr/bin/env python3
"""Check for missing docstrings in public functions.

This script checks if public functions (not starting with _) have docstrings.
"""

import ast
import sys
from pathlib import Path


class DocstringChecker(ast.NodeVisitor):
    """Check for docstrings in functions."""

    def __init__(self):
        self.functions = []
        self.classes = {}

    def visit_ClassDef(self, node):
        """Visit class definition."""
        class_name = node.name
        self.classes[class_name] = []

        # Check class docstring
        class_doc = ast.get_docstring(node)

        # Save current class context
        old_methods = self.functions
        self.functions = []

        # Visit methods
        self.generic_visit(node)

        # Restore
        self.classes[class_name] = self.functions[:]
        self.classes[class_name]['_class_doc'] = class_doc
        self.functions = old_methods

    def visit_FunctionDef(self, node):
        """Visit function definition."""
        docstring = ast.get_docstring(node)

        func_info = {
            'name': node.name,
            'line': node.lineno,
            'is_public': not node.name.startswith('_'),
            'has_docstring': docstring is not None
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
        checker = DocstringChecker()
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
        print("Usage: check_docstrings.py <file1.py> [file2.py] ...")
        sys.exit(1)

    issues = []

    for filepath in sys.argv[1:]:
        if not filepath.endswith('.py'):
            continue

        functions, classes = check_file(filepath)

        # Check module-level functions
        for func in functions:
            if func['is_public'] and not func['has_docstring']:
                issues.append({
                    'file': filepath,
                    'type': 'function',
                    'name': func['name'],
                    'line': func['line']
                })

        # Check class methods
        for class_name, methods in classes.items():
            # Check class docstring
            if not methods.get('_class_doc'):
                issues.append({
                    'file': filepath,
                    'type': 'class',
                    'name': class_name,
                    'line': methods[0]['line'] if methods else 1
                })

            # Check methods
            for method in methods:
                # Skip __magic__ methods
                if method['name'].startswith('__') and method['name'].endswith('__'):
                    continue

                # Check public and protected methods
                if not method['name'].startswith('__') and not method['has_docstring']:
                    issues.append({
                        'file': filepath,
                        'type': 'method',
                        'class': class_name,
                        'name': method['name'],
                        'line': method['line']
                    })

    if issues:
        print(f"❌ Found {len(issues)} public items missing docstrings:")
        for issue in issues[:10]:  # Show first 10
            if issue['type'] == 'function':
                print(f"  {issue['file']}:{issue['line']} - function {issue['name']}()")
            elif issue['type'] == 'class':
                print(f"  {issue['file']}:{issue['line']} - class {issue['name']}")
            else:
                print(f"  {issue['file']}:{issue['line']} - {issue['class']}.{issue['name']}()")

        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")

        sys.exit(1)
    else:
        print("✅ All public functions, classes, and methods have docstrings")
        sys.exit(0)


if __name__ == '__main__':
    main()
