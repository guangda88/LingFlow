"""code-optimizer 技能实现"""

import os
import json
from pathlib import Path


def generate_optimization(params):
    """生成优化方案"""
    issues = params.get('issues', {})
    strategy = params.get('strategy', 'refactor_duplicates')
    
    # 初始化结果
    result = {
        'is_safe': True,
        'changes': [],
        'estimated_improvement': '0%'
    }
    
    # 根据策略生成优化方案
    if strategy == 'refactor_duplicates':
        result = generate_duplication_refactor(issues)
    elif strategy == 'remove_dead_code':
        result = generate_dead_code_removal(issues)
    elif strategy == 'reduce_complexity':
        result = generate_complexity_reduction(issues)
    else:
        # 默认策略：综合优化
        result = generate_comprehensive_optimization(issues)
    
    return result

def generate_duplication_refactor(issues):
    """生成重复代码重构方案"""
    changes = []
    duplicate_rate = issues.get('duplication_rate', 0)
    duplicate_files = issues.get('duplicate_files', [])
    
    # 针对重复代码生成重构建议
    for duplicate in duplicate_files:
        file1 = duplicate.get('file1')
        file2 = duplicate.get('file2')
        common_lines = duplicate.get('common_lines', 0)
        
        # 生成提取函数的建议
        changes.append({
            'file': file1,
            'type': 'extract_function',
            'description': f'提取与 {file2} 重复的 {common_lines} 行代码为函数',
            'safe': True
        })
    
    # 计算估计改进率
    if duplicate_rate > 0:
        estimated_improvement = f'{int(duplicate_rate * 100)}% reduction in duplication'
    else:
        estimated_improvement = '0% reduction in duplication'
    
    return {
        'is_safe': True,
        'changes': changes,
        'estimated_improvement': estimated_improvement
    }

def generate_dead_code_removal(issues):
    """生成死代码删除方案"""
    changes = []
    dead_code = issues.get('dead_code', [])
    
    # 针对死代码生成删除建议
    for item in dead_code:
        file = item.get('file')
        dead_issues = item.get('issues', [])
        
        for issue in dead_issues:
            if '未使用的函数' in issue:
                function_name = issue.split(': ')[1]
                changes.append({
                    'file': file,
                    'type': 'remove_function',
                    'description': f'删除未使用的函数 {function_name}',
                    'safe': True
                })
            elif '未使用的变量' in issue:
                variable_name = issue.split(': ')[1]
                changes.append({
                    'file': file,
                    'type': 'remove_variable',
                    'description': f'删除未使用的变量 {variable_name}',
                    'safe': True
                })
    
    # 计算估计改进率
    if dead_code:
        estimated_improvement = f'{len(changes)} dead code items removed'
    else:
        estimated_improvement = '0 dead code items removed'
    
    return {
        'is_safe': True,
        'changes': changes,
        'estimated_improvement': estimated_improvement
    }

def generate_complexity_reduction(issues):
    """生成复杂度降低方案"""
    changes = []
    complexity = issues.get('complexity', {})
    
    # 针对高复杂度代码生成拆分建议
    for file, comp in complexity.items():
        if comp > 10:  # 复杂度阈值
            changes.append({
                'file': file,
                'type': 'split_function',
                'description': f'拆分复杂度为 {comp} 的函数',
                'safe': True
            })
    
    # 计算估计改进率
    if complexity:
        high_complexity_files = sum(1 for comp in complexity.values() if comp > 10)
        estimated_improvement = f'{high_complexity_files} high complexity files addressed'
    else:
        estimated_improvement = '0 high complexity files addressed'
    
    return {
        'is_safe': True,
        'changes': changes,
        'estimated_improvement': estimated_improvement
    }

def generate_comprehensive_optimization(issues):
    """生成综合优化方案"""
    changes = []
    
    # 处理重复代码
    duplicate_files = issues.get('duplicate_files', [])
    for duplicate in duplicate_files:
        file1 = duplicate.get('file1')
        changes.append({
            'file': file1,
            'type': 'extract_function',
            'description': f'提取重复代码为函数',
            'safe': True
        })
    
    # 处理死代码
    dead_code = issues.get('dead_code', [])
    for item in dead_code:
        file = item.get('file')
        dead_issues = item.get('issues', [])
        for issue in dead_issues:
            if '未使用的' in issue:
                changes.append({
                    'file': file,
                    'type': 'remove_unused',
                    'description': f'删除{issue}',
                    'safe': True
                })
    
    # 处理高复杂度
    complexity = issues.get('complexity', {})
    for file, comp in complexity.items():
        if comp > 10:
            changes.append({
                'file': file,
                'type': 'split_function',
                'description': f'拆分高复杂度函数',
                'safe': True
            })
    
    # 计算估计改进率
    total_changes = len(changes)
    if total_changes > 0:
        estimated_improvement = f'{total_changes} optimization changes proposed'
    else:
        estimated_improvement = '0 optimization changes proposed'
    
    return {
        'is_safe': True,
        'changes': changes,
        'estimated_improvement': estimated_improvement
    }

def execute_skill(params):
    """执行技能"""
    return generate_optimization(params)
