"""code-review 技能实现 - 8维代码审查框架"""

import os
import re
import ast
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ============== 常量配置 ==============
COMPLEXITY_THRESHOLD = 10
MAX_FILE_LINES = 300
MAX_METHODS_IN_CLASS = 15
MAX_IMPORTS = 20

# 严重程度权重
SEVERITY_WEIGHTS = {
    'critical': 10.0,
    'high': 5.0,
    'medium': 2.0,
    'low': 0.5,
    'warning': 0.2
}

# 维度权重
DIMENSION_WEIGHTS = {
    'security': 0.30,      # 安全性权重最高
    'bugs': 0.25,          # Bug 次之
    'code_quality': 0.20,
    'architecture': 0.10,
    'performance': 0.05,
    'maintainability': 0.05,
    'best_practices': 0.03,
    'autoresearch_consistency': 0.02,
}


def review_code(params):
    """审查代码 - 8维全面审查

    Args:
        params: 审查参数，包含:
            - focus: 审查焦点 (code_quality, architecture, performance,
                     security, maintainability, best_practices,
                     autoresearch_consistency, bug_analysis, all)
            - files: 要审查的文件或目录列表
            - strict: 严格模式 (默认True)

    Returns:
        审查结果字典
    """
    focus = params.get('focus', 'all')
    files = params.get('files', [])
    strict = params.get('strict', True)

    # 验证参数
    if not files:
        return {"error": "请指定要审查的文件或目录"}

    # 初始化8维结果
    result = {
        'reviewed_files': [],
        'dimensions': {
            'code_quality': {'issues': [], 'suggestions': [], 'score': 0},
            'architecture': {'issues': [], 'suggestions': [], 'score': 0},
            'performance': {'issues': [], 'suggestions': [], 'score': 0},
            'security': {'issues': [], 'suggestions': [], 'score': 0},
            'maintainability': {'issues': [], 'suggestions': [], 'score': 0},
            'best_practices': {'issues': [], 'suggestions': [], 'score': 0},
            'autoresearch_consistency': {'issues': [], 'suggestions': [], 'score': 0},
            'bug_analysis': {'issues': [], 'suggestions': [], 'score': 0}
        },
        'summary': "",
        'overall_score': 0,
        'review_time': datetime.now().isoformat()
    }

    # 审查每个文件
    for file_path in files:
        try:
            file = Path(file_path)
            if not file.exists():
                logger.warning(f"文件不存在: {file_path}")
                continue

            # 检查是文件还是目录
            if file.is_file():
                review_result = review_file(file, focus, strict)
                result['reviewed_files'].append(str(file))
                merge_dimensions(result['dimensions'], review_result)
            elif file.is_dir():
                # 审查目录中的所有 Python 文件
                for py_file in file.rglob('*.py'):
                    review_result = review_file(py_file, focus, strict)
                    result['reviewed_files'].append(str(py_file))
                    merge_dimensions(result['dimensions'], review_result)
        except Exception as e:
            logger.error(f"审查文件时出错: {str(e)}")

    # 计算得分
    calculate_scores(result)

    # 生成摘要
    result['summary'] = generate_summary(result, focus)

    return result


def merge_dimensions(target_dimensions: Dict, source_result: Dict):
    """合并审查结果到目标维度"""
    for dimension in target_dimensions:
        if dimension in source_result:
            target_dimensions[dimension]['issues'].extend(
                source_result[dimension].get('issues', [])
            )
            target_dimensions[dimension]['suggestions'].extend(
                source_result[dimension].get('suggestions', [])
            )


def calculate_scores(result: Dict):
    """计算各维度得分 - 使用加权评分系统"""
    dimension_scores = {}

    for dimension, data in result['dimensions'].items():
        issues = data['issues']
        suggestions = data['suggestions']

        # 计算加权分数
        penalty = 0.0
        for issue in issues:
            severity = issue.get('severity', 'low')
            penalty += SEVERITY_WEIGHTS.get(severity, 0.5)

        for suggestion in suggestions:
            priority = suggestion.get('priority', 'low')
            penalty += SEVERITY_WEIGHTS.get(priority, 0.3)

        # 5分满分，扣分制
        base_score = 5.0
        final_score = max(0.0, base_score - penalty)

        dimension_scores[dimension] = final_score
        data['score'] = final_score

    # 计算加权总分
    weighted_score = sum(
        dimension_scores[dim] * DIMENSION_WEIGHTS.get(dim, 0.1)
        for dim in dimension_scores
    )

    result['overall_score'] = weighted_score


def generate_summary(result: Dict, focus: str) -> str:
    """生成审查摘要"""
    reviewed_count = len(result['reviewed_files'])
    total_issues = sum(len(d['issues']) for d in result['dimensions'].values())
    total_suggestions = sum(len(d['suggestions']) for d in result['dimensions'].values())
    score = result['overall_score']

    emoji_scores = {
        5: '⭐⭐⭐⭐⭐',
        4: '⭐⭐⭐⭐',
        3: '⭐⭐⭐',
        2: '⭐⭐',
        1: '⭐'
    }
    emoji = emoji_scores.get(int(score), '?')

    summary = f"""
{'='*60}
📊 代码审查报告 - 8维全面审查
{'='*60}

📁 审查范围: {reviewed_count} 个文件
🎯 审查焦点: {focus}
📅 审查时间: {result['review_time']}

📈 总体评分: {score:.1f}/5.0 {emoji}

📋 问题统计:
  - 严重问题: {count_issues_by_severity(result, 'critical')}
  - 高优先级: {count_issues_by_severity(result, 'high')}
  - 中优先级: {count_issues_by_severity(result, 'medium')}
  - 低优先级: {count_issues_by_severity(result, 'low')}
  - 总计: {total_issues}

💡 建议统计: {total_suggestions}

{'='*60}
"""

    # 添加各维度详情
    for dimension, data in result['dimensions'].items():
        if data['issues'] or data['suggestions']:
            summary += f"\n{dimension.upper()} (得分: {data['score']:.1f}):\n"
            for issue in data['issues']:
                emoji = {'critical': '🔴', 'high': '🔶', 'medium': '⚠️', 'low': '🔵'}
                summary += f"  {emoji.get(issue['severity'], '📝')} [{issue['severity']}] {issue['issue']}\n"
            for suggestion in data['suggestions'][:3]:  # 只显示前3个
                summary += f"  💡 {suggestion['suggestion']}\n"

    return summary


def count_issues_by_severity(result: Dict, severity: str) -> int:
    """计算特定严重级别的问题数量"""
    count = 0
    for dimension in result['dimensions'].values():
        count += sum(1 for issue in dimension['issues']
                    if issue.get('severity') == severity)
    return count


def review_file(file: Path, focus: str, strict: bool) -> Dict:
    """审查单个文件 - 8维审查"""
    result = {
        'code_quality': {'issues': [], 'suggestions': []},
        'architecture': {'issues': [], 'suggestions': []},
        'performance': {'issues': [], 'suggestions': []},
        'security': {'issues': [], 'suggestions': []},
        'maintainability': {'issues': [], 'suggestions': []},
        'best_practices': {'issues': [], 'suggestions': []},
        'autoresearch_consistency': {'issues': [], 'suggestions': []},
        'bug_analysis': {'issues': [], 'suggestions': []}
    }

    try:
        content = file.read_text(encoding='utf-8')
        lines = content.split('\n')

        # 解析AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            result['bug_analysis']['issues'].append({
                'file': str(file),
                'issue': '语法错误 - 无法解析AST',
                'severity': 'critical',
                'line': 0
            })
            return result

        # 根据焦点选择审查维度
        if focus in ['all', 'code_quality']:
            review_code_quality(file, content, lines, tree, result)
        if focus in ['all', 'architecture']:
            review_architecture(file, content, lines, tree, result)
        if focus in ['all', 'performance']:
            review_performance(file, content, lines, tree, result)
        if focus in ['all', 'security']:
            review_security(file, content, lines, result)
        if focus in ['all', 'maintainability']:
            review_maintainability(file, content, lines, tree, result)
        if focus in ['all', 'best_practices']:
            review_best_practices(file, content, lines, tree, result)
        if focus in ['all', 'autoresearch_consistency']:
            review_autoresearch_consistency(file, content, lines, result)
        if focus in ['all', 'bug_analysis']:
            review_bug_analysis(file, content, lines, tree, result)

    except Exception as e:
        logger.error(f"审查文件 {file} 时出错: {str(e)}")

    return result


def review_code_quality(file: Path, content: str, lines: List[str], tree: ast.AST, result: Dict):
    """代码质量审查"""
    # 1. 检查函数复杂度
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # 计算圈复杂度（简化版）
            complexity = calculate_complexity(node)
            if complexity > COMPLEXITY_THRESHOLD:
                result['code_quality']['issues'].append({
                    'file': str(file),
                    'issue': f'函数 {node.name} 复杂度过高 ({complexity})',
                    'severity': 'medium',
                    'line': node.lineno
                })
                result['code_quality']['suggestions'].append({
                    'file': str(file),
                    'suggestion': f'考虑重构函数 {node.name}，降低复杂度',
                    'priority': 'medium'
                })

    # 2. 检查命名规范
    naming_issues = check_naming_convention(tree)
    for issue in naming_issues:
        result['code_quality']['issues'].append({
            'file': str(file),
            'issue': issue,
            'severity': 'low',
            'line': 0
        })

    # 3. 检查代码行数
    if len(lines) > MAX_FILE_LINES:
        result['code_quality']['issues'].append({
            'file': str(file),
            'issue': f'文件过长 ({len(lines)} 行)',
            'severity': 'warning',
            'line': 1
        })
        result['code_quality']['suggestions'].append({
            'file': str(file),
            'suggestion': '考虑将文件拆分为多个模块',
            'priority': 'medium'
        })


def review_architecture(file: Path, content: str, lines: List[str], tree: ast.AST, result: Dict):
    """架构设计审查"""
    # 1. 检查类的设计
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            if len(methods) > MAX_METHODS_IN_CLASS:
                result['architecture']['issues'].append({
                    'file': str(file),
                    'issue': f'类 {node.name} 方法过多 ({len(methods)} 个)',
                    'severity': 'medium',
                    'line': node.lineno
                })
                result['architecture']['suggestions'].append({
                    'file': str(file),
                    'suggestion': f'考虑将类 {node.name} 拆分为多个小类',
                    'priority': 'medium'
                })

    # 2. 检查导入依赖
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    if len(imports) > MAX_IMPORTS:
        result['architecture']['issues'].append({
            'file': str(file),
            'issue': f'导入过多 ({len(imports)} 个)',
            'severity': 'low',
            'line': 1
        })
        result['architecture']['suggestions'].append({
            'file': str(file),
            'suggestion': '考虑减少不必要的导入或重新组织模块',
            'priority': 'low'
        })


def review_performance(file: Path, content: str, lines: List[str], tree: ast.AST, result: Dict):
    """性能分析"""
    # 1. 检查循环嵌套
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            nested_loops = count_nested_loops(node)
            if nested_loops > 2:
                result['performance']['issues'].append({
                    'file': str(file),
                    'issue': f'检测到 {nested_loops} 层嵌套循环',
                    'severity': 'medium',
                    'line': node.lineno
                })
                result['performance']['suggestions'].append({
                    'file': str(file),
                    'suggestion': '考虑优化循环结构或使用向量化操作',
                    'priority': 'medium'
                })

    # 2. 检查字符串拼接
    for i, line in enumerate(lines, 1):
        if '+=' in line and 'str' not in line:
            # 简单检测，可能有误报
            result['performance']['suggestions'].append({
                'file': str(file),
                'suggestion': f'第 {i} 行: 考虑使用str.join()代替字符串拼接',
                'priority': 'low'
            })


def review_security(file: Path, content: str, lines: List[str], result: Dict):
    """安全检查"""
    # 1. 检查危险函数
    dangerous_patterns = [
        ('eval(', 'critical', 'eval()函数存在代码注入风险'),
        ('exec(', 'critical', 'exec()函数存在代码注入风险'),
        ('pickle.loads(', 'high', 'pickle反序列化可能不安全'),
        ('subprocess.call(', 'medium', 'subprocess调用需注意命令注入'),
        ('os.system(', 'high', 'os.system()存在命令注入风险'),
        ('input(', 'low', 'input()需验证用户输入'),
        ('open(', 'low', '文件操作需注意路径遍历'),
    ]

    for pattern, severity, message in dangerous_patterns:
        if pattern in content:
            # 找到出现位置
            for i, line in enumerate(lines, 1):
                if pattern in line:
                    result['security']['issues'].append({
                        'file': str(file),
                        'issue': message,
                        'severity': severity,
                        'line': i
                    })
                    break

    # 2. 检查硬编码的密钥或密码
    secret_patterns = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
    ]

    for pattern in secret_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            result['security']['issues'].append({
                'file': str(file),
                'issue': '检测到可能的硬编码敏感信息',
                'severity': 'high',
                'line': 0
            })
            result['security']['suggestions'].append({
                'file': str(file),
                'suggestion': '使用环境变量或配置文件存储敏感信息',
                'priority': 'high'
            })


def review_maintainability(file: Path, content: str, lines: List[str], tree: ast.AST, result: Dict):
    """可维护性评估"""
    # 1. 检查文档字符串
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not ast.get_docstring(node):
                result['maintainability']['issues'].append({
                    'file': str(file),
                    'issue': f'函数 {node.name} 缺少文档字符串',
                    'severity': 'low',
                    'line': node.lineno
                })

        if isinstance(node, ast.ClassDef):
            if not ast.get_docstring(node):
                result['maintainability']['issues'].append({
                    'file': str(file),
                    'issue': f'类 {node.name} 缺少文档字符串',
                    'severity': 'low',
                    'line': node.lineno
                })

    # 2. 检查注释率
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))

    if code_lines > 0:
        comment_ratio = comment_lines / code_lines
        if comment_ratio < 0.1:
            result['maintainability']['suggestions'].append({
                'file': str(file),
                'suggestion': f'注释率较低 ({comment_ratio:.1%})，建议增加注释',
                'priority': 'low'
            })


def review_best_practices(file: Path, content: str, lines: List[str], tree: ast.AST, result: Dict):
    """最佳实践检查"""
    # 1. 检查异常处理
    has_try_except = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    if not has_try_except and len(content) > 100:
        result['best_practices']['suggestions'].append({
            'file': str(file),
            'suggestion': '建议添加异常处理机制',
            'priority': 'medium'
        })

    # 2. 检查类型提示
    has_type_hints = any(
        node.returns or any(arg.annotation for arg in node.args.args)
        for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    )

    if not has_type_hints:
        result['best_practices']['issues'].append({
            'file': str(file),
            'issue': '缺少类型提示',
            'severity': 'low',
            'line': 0
        })
        result['best_practices']['suggestions'].append({
            'file': str(file),
            'suggestion': '建议添加类型提示以提高代码可读性',
            'priority': 'low'
        })


def review_autoresearch_consistency(file: Path, content: str, lines: List[str], result: Dict):
    """autoresearch理念一致性检查"""
    # 检查是否遵循autoresearch核心理念
    autoresearch_principles = [
        ('prepare.py', '时间预算', 'TRAIN_TIME_BUDGET'),
        ('prepare.py', '序列长度', 'SEQ_LENGTH'),
        ('train.py', '模型架构', 'class LanguageModel'),
        ('train.py', '训练循环', 'def train_one_epoch'),
    ]

    file_name = file.name
    for principle_file, aspect, keyword in autoresearch_principles:
        if file_name == principle_file and keyword not in content:
            result['autoresearch_consistency']['issues'].append({
                'file': str(file),
                'issue': f'缺少autoresearch核心要素: {aspect}',
                'severity': 'high',
                'line': 0
            })


def review_bug_analysis(file: Path, content: str, lines: List[str], tree: ast.AST, result: Dict):
    """潜在Bug分析"""
    # 1. 检查除零风险
    for i, line in enumerate(lines, 1):
        if re.search(r'/\s*\w+', line):
            result['bug_analysis']['suggestions'].append({
                'file': str(file),
                'suggestion': f'第 {i} 行: 检查除零风险',
                'priority': 'low'
            })

    # 2. 检查未使用的变量（简化版）
    defined_vars = set()
    used_vars = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            defined_vars.add(node.id)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_vars.add(node.id)

    unused = defined_vars - used_vars - {'__name__', '__file__'}
    if unused:
        result['bug_analysis']['issues'].append({
            'file': str(file),
            'issue': f'可能存在未使用的变量: {", ".join(list(unused)[:3])}',
            'severity': 'low',
            'line': 0
        })


def calculate_complexity(node: ast.FunctionDef) -> int:
    """计算圈复杂度（简化版）"""
    complexity = 1  # 基础复杂度

    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1

    return complexity


def check_naming_convention(tree: ast.AST) -> List[str]:
    """检查命名规范（简化版）"""
    issues = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not node.name[0].isupper() or '_' in node.name:
                issues.append(f'类名 {node.name} 不符合PascalCase规范')

        if isinstance(node, ast.FunctionDef):
            if '_' not in node.name or node.name[0].isupper():
                issues.append(f'函数名 {node.name} 不符合snake_case规范')

    return issues


def count_nested_loops(node: ast.For) -> int:
    """计算嵌套循环深度"""
    max_depth = 1
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.For):
            depth = count_nested_loops(child) + 1
            max_depth = max(max_depth, depth)
    return max_depth


def execute_skill(params):
    """执行技能"""
    return review_code(params)
