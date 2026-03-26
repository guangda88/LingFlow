#!/usr/bin/env python
"""Check for missing type hints in LingFlow codebase."""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple


def extract_functions_without_type_hints(filepath: Path) -> List[Dict[str, str]]:
    """Extract functions without complete type hints."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content, filename=filepath.name)

    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check function definition
            func_name = node.name
            line_num = node.lineno
            file_str = str(filepath.relative_to(Path.cwd()))

            # Check return type
            has_return_type = node.returns is not None

            # Check parameter types
            has_param_types = all(arg.annotation is not None for arg in node.args.args)

            # Skip special methods and dunder methods
            if func_name.startswith("_") and not func_name.startswith("__"):
                continue

            # Skip if it's a property or setter
            if any(
                decorator.id in ["property", "setter", "staticmethod", "classmethod"]
                for decorator in node.decorator_list
                if isinstance(decorator, ast.Name)
            ):
                continue

            # If missing return type or any parameter type
            if not has_return_type or not has_param_types:
                results.append({
                    "file": file_str,
                    "function": func_name,
                    "line": line_num,
                    "has_return": has_return_type,
                    "has_params": has_param_types,
                })

    return results


def main():
    """Main function to analyze codebase."""
    lingflow_dir = Path.cwd() / "lingflow"

    # Find all Python files
    python_files = list(lingflow_dir.rglob("*.py"))

    all_issues = []
    for filepath in python_files:
        if "__pycache__" in str(filepath):
            continue

        try:
            issues = extract_functions_without_type_hints(filepath)
            all_issues.extend(issues)
        except SyntaxError:
            pass  # Skip files with syntax errors

    # Group by module
    by_module: Dict[str, List[Dict]] = {}
    for issue in all_issues:
        module = issue["file"].split("/")[1] if "/" in issue["file"] else "root"
        if module not in by_module:
            by_module[module] = []
        by_module[module].append(issue)

    # Print summary
    print("=" * 80)
    print("Missing Type Hints Analysis")
    print("=" * 80)
    print(f"\nTotal functions/methods missing type hints: {len(all_issues)}")
    print(f"Python files analyzed: {len(python_files)}")

    # Group by module
    print("\n" + "-" * 80)
    print("By Module:")
    print("-" * 80)

    for module in sorted(by_module.keys()):
        issues = by_module[module]
        print(f"\n{module}/")
        print(f"  Total missing: {len(issues)}")
        print(f"  Files affected: {len(set(i['file'] for i in issues))}")

        # Show top 5 issues per module
        for issue in issues[:5]:
            missing = []
            if not issue["has_return"]:
                missing.append("return")
            if not issue["has_params"]:
                missing.append("params")
            print(f"    - {issue['function']}() line {issue['line']} (missing: {', '.join(missing)})")

        if len(issues) > 5:
            print(f"    ... and {len(issues) - 5} more")

    # Summary statistics
    print("\n" + "=" * 80)
    print("Summary Statistics:")
    print("=" * 80)
    print(f"Total issues: {len(all_issues)}")
    print(f"Modules affected: {len(by_module)}")

    missing_return = sum(1 for i in all_issues if not i["has_return"])
    missing_params = sum(1 for i in all_issues if not i["has_params"])
    missing_both = sum(1 for i in all_issues if not i["has_return"] and not i["has_params"])

    print(f"Missing return type: {missing_return}")
    print(f"Missing param types: {missing_params}")
    print(f"Missing both: {missing_both}")


if __name__ == "__main__":
    main()
