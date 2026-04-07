"""
规则应用器

将知识库中学习的规则应用到新代码中，实现主动质量检查。
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from .models import LearnedRule, FeedbackCategory


class RuleApplier:
    """规则应用器 - 将学习到的规则应用到代码检查"""

    def __init__(self, knowledge_base):
        """初始化规则应用器

        Args:
            knowledge_base: 知识库实例
        """
        self.knowledge_base = knowledge_base
        self._applied_count = 0

    def check_file(self, file_path: str, category: Optional[FeedbackCategory] = None) -> List[Dict[str, Any]]:
        """检查单个文件

        Args:
            file_path: 文件路径
            category: 可选的类别过滤

        Returns:
            检测到的问题列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception:
            return []

        return self.check_code(source_code, file_path, category)

    def check_code(
        self,
        source_code: str,
        file_path: str,
        category: Optional[FeedbackCategory] = None
    ) -> List[Dict[str, Any]]:
        """检查代码

        Args:
            source_code: 源代码
            file_path: 文件路径
            category: 可选的类别过滤

        Returns:
            检测到的问题列表
        """
        issues = []

        # 获取启用的规则
        rules = self.knowledge_base.get_all_rules(
            category=category,
            status="approved",
            limit=1000
        )

        for rule in rules:
            rule_issues = self._apply_rule(rule, source_code, file_path)
            issues.extend(rule_issues)

        self._applied_count += len(issues)
        return issues

    def check_directory(
        self,
        directory: str,
        pattern: str = "*.py",
        category: Optional[FeedbackCategory] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """检查目录中的所有文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            category: 可选的类别过滤

        Returns:
            文件路径到问题列表的映射
        """
        results = {}
        dir_path = Path(directory)

        for file_path in dir_path.rglob(pattern):
            if file_path.is_file():
                issues = self.check_file(str(file_path), category)
                if issues:
                    results[str(file_path)] = issues

        return results

    def _apply_rule(
        self,
        rule: LearnedRule,
        source_code: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """应用单个规则到代码

        Args:
            rule: 学习到的规则
            source_code: 源代码
            file_path: 文件路径

        Returns:
            检测到的问题列表
        """
        issues: list[dict[str, Any]] = []

        # 检查文件模式
        if not self._matches_file_pattern(rule, file_path):
            return issues

        # 检查代码模式
        for code_pattern in rule.pattern.code_patterns:
            matches = self._find_pattern_matches(code_pattern, source_code)
            for match in matches:
                line_num = source_code[:match.start()].count('\n') + 1
                line_content = source_code.split('\n')[line_num - 1]

                issues.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "category": rule.category.value,
                    "severity": self._map_severity(rule),
                    "message": rule.description,
                    "file_path": file_path,
                    "line": line_num,
                    "snippet": line_content.strip(),
                    "suggestion": rule.pattern.tool_support[0] if rule.pattern.tool_support else None,
                    "confidence": rule.confidence,
                })

        # 检查上下文关键词
        if rule.pattern.context_keywords:
            keyword_issues = self._check_keywords(rule, source_code, file_path)
            issues.extend(keyword_issues)

        return issues

    def _matches_file_pattern(self, rule: LearnedRule, file_path: str) -> bool:
        """检查文件是否匹配规则的文件模式"""
        if not rule.pattern.file_patterns:
            return True

        file_path_obj = Path(file_path)

        for pattern in rule.pattern.file_patterns:
            # 简单的通配符匹配
            if pattern.startswith("*."):
                if file_path_obj.suffix == pattern[1:]:
                    return True
            elif pattern.endswith("*"):
                if file_path_obj.name.startswith(pattern[:-1]):
                    return True
            elif pattern in file_path:
                return True

        return False

    def _find_pattern_matches(self, pattern: str, source_code: str) -> List[Any]:
        """在源代码中查找模式匹配"""
        matches: list[Any] = []

        try:
            # 尝试作为正则表达式
            regex = re.compile(pattern)
            matches.extend(regex.finditer(source_code))
        except re.error:
            # 作为字面字符串搜索
            start = 0
            while True:
                pos = source_code.find(pattern, start)
                if pos == -1:
                    break
                matches.append(type('Match', (), {'start': lambda self, p=pos: p})())
                start = pos + 1

        return matches

    def _check_keywords(
        self,
        rule: LearnedRule,
        source_code: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """检查上下文关键词"""
        issues = []
        code_lower = source_code.lower()

        for keyword in rule.pattern.context_keywords:
            if keyword.lower() in code_lower:
                # 找到包含关键词的行
                lines = source_code.split('\n')
                for i, line in enumerate(lines, 1):
                    if keyword.lower() in line.lower():
                        issues.append({
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "category": rule.category.value,
                            "severity": self._map_severity(rule),
                            "message": f"Potential issue: {rule.description}",
                            "file_path": file_path,
                            "line": i,
                            "snippet": line.strip(),
                            "suggestion": f"Review usage of '{keyword}'",
                            "confidence": rule.confidence * 0.7,  # 关键词匹配置信度较低
                        })
                        break  # 每个关键词只报告一次

        return issues

    def _map_severity(self, rule: LearnedRule) -> str:
        """根据规则模式映射严重程度"""
        severity_dist = rule.pattern.severity_distribution

        if not severity_dist:
            return "MEDIUM"

        # 返回最常见的严重程度
        return max(severity_dist.items(), key=lambda x: x[1])[0].lower()

    def get_statistics(self) -> Dict[str, Any]:
        """获取应用统计"""
        return {
            "applied_count": self._applied_count,
        }


class AutoFixer:
    """自动修复器 - 尝试自动修复检测到的问题"""

    def __init__(self, applier: RuleApplier):
        """初始化自动修复器

        Args:
            applier: 规则应用器实例
        """
        self.applier = applier
        self._fixed_count = 0

    def fix_file(
        self,
        file_path: str,
        issues: List[Dict[str, Any]],
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """修复文件中的问题

        Args:
            file_path: 文件路径
            issues: 问题列表
            dry_run: 是否只模拟不实际修改

        Returns:
            修复结果
        """
        if dry_run:
            return {
                "file_path": file_path,
                "total_issues": len(issues),
                "fixable": self._count_fixable(issues),
                "fixed": 0,
                "dry_run": True,
            }

        with open(file_path, 'r') as f:
            original_content = f.read()

        backup_path = file_path + ".bak"
        try:
            from pathlib import Path as _Path
            _Path(backup_path).write_text(original_content)
        except OSError:
            pass

        modified_content = original_content
        fixed_count = 0

        # 按行号倒序处理（避免行号偏移）
        sorted_issues = sorted(issues, key=lambda x: x["line"], reverse=True)

        for issue in sorted_issues:
            try:
                modified_content = self._apply_fix(modified_content, issue)
                fixed_count += 1
            except Exception:
                continue

        if modified_content != original_content:
            with open(file_path, 'w') as f:
                f.write(modified_content)

        self._fixed_count += fixed_count

        return {
            "file_path": file_path,
            "total_issues": len(issues),
            "fixable": self._count_fixable(issues),
            "fixed": fixed_count,
            "dry_run": False,
        }

    def _count_fixable(self, issues: List[Dict[str, Any]]) -> int:
        """计算可修复的问题数量"""
        return sum(1 for issue in issues if self._is_fixable(issue))

    def _is_fixable(self, issue: Dict[str, Any]) -> bool:
        """判断问题是否可修复"""
        fixable_patterns = [
            "unused",
            "import",
            "blank-line",
        ]
        return any(p in issue.get("rule_id", "").lower()
                   for p in fixable_patterns)

    def _apply_fix(self, content: str, issue: Dict[str, Any]) -> str:
        """应用单个修复"""
        lines = content.split('\n')
        line_num = issue["line"] - 1

        if 0 <= line_num < len(lines):
            # 简单的修复逻辑示例
            if "unused import" in issue.get("rule_id", "").lower():
                # 移除未使用的导入行
                lines.pop(line_num)
            elif "blank line" in issue.get("rule_id", "").lower():
                # 移除空行
                lines.pop(line_num)

        return '\n'.join(lines)


class PreCommitHookGenerator:
    """Pre-commit钩子生成器"""

    @staticmethod
    def generate_hook(
        knowledge_base,
        output_path: str = ".git/hooks/pre-commit",
        categories: Optional[List[str]] = None
    ) -> None:
        """生成pre-commit钩子脚本

        Args:
            knowledge_base: 知识库实例
            output_path: 输出路径
            categories: 要检查的类别列表
        """
        script = '''#!/bin/bash
# LingFlow Self-Learning Pre-commit Hook
# Auto-generated by LingFlow v3.9.0

python3 -c "
from lingflow.self_optimizer.phase5 import SelfLearningSystem
from lingflow.self_optimizer.phase5.applier import RuleApplier
import sys

system = SelfLearningSystem()
applier = RuleApplier(system.knowledge_base)

files_to_check = [f for f in sys.argv[1:] if f.endswith('.py']]

exit_code = 0
for file_path in files_to_check:
    issues = applier.check_file(file_path)
    if issues:
        print(f'LingFlow: {{len(issues)}} issues in {{file_path}}')
        for issue in issues:
            print(f'  Line {{issue["line"]}}: {{issue["message"]}}')
        exit_code = 1

sys.exit(exit_code)
" "$@

# Check the exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "LingFlow: Code quality issues detected. Please fix before committing."
    echo "Run: python scripts/activate_self_learning.py --report"
    exit 1
fi
'''

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(script)

        # 设置可执行权限
        import os
        os.chmod(output_path, 0o755)

    @staticmethod
    def generate_config(
        knowledge_base,
        output_path: str = ".lingflow/pre-commit-config.yaml"
    ) -> None:
        """生成pre-commit配置文件

        Args:
            knowledge_base: 知识库实例
            output_path: 输出路径
        """
        import yaml

        stats = knowledge_base.get_statistics()

        config = {
            "repos": [
                {
                    "repo": "local",
                    "hooks": [
                        {
                            "id": "lingflow-self-learning",
                            "name": "LingFlow Self-Learning",
                            "entry": "python scripts/activate_self_learning.py --scan",
                            "language": "system",
                            "pass_filenames": True,
                            "files": r"\\.py$",
                        }
                    ],
                }
            ],
            "lingflow": {
                "total_rules": stats["total_rules"],
                "categories": stats["by_category"],
            }
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)


__all__ = [
    "RuleApplier",
    "AutoFixer",
    "PreCommitHookGenerator",
]
