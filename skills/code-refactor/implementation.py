"""code-refactor 技能实现"""

import os
import shutil
from datetime import datetime


def apply_refactor(params):
    """执行代码重构"""
    changes = params.get('changes', [])
    backup = params.get('backup', True)
    
    # 创建备份
    backup_path = None
    if backup:
        backup_path = f".backup/{datetime.now().isoformat()}"
        os.makedirs(backup_path, exist_ok=True)
        # 备份整个lingflow目录
        shutil.copytree('./lingflow', os.path.join(backup_path, 'lingflow'))
    
    modified_files = []
    
    # 应用每个变更
    for change in changes:
        file_path = change.get('file')
        change_type = change.get('type')
        
        if file_path and os.path.exists(file_path):
            if change_type == 'remove_function':
                # 移除未使用的函数
                func_name = change.get('function_name')
                if func_name:
                    remove_function(file_path, func_name)
                    modified_files.append(file_path)
            elif change_type == 'remove_variable':
                # 移除未使用的变量
                var_name = change.get('variable_name')
                if var_name:
                    remove_variable(file_path, var_name)
                    modified_files.append(file_path)
            elif change_type == 'refactor':
                # 执行重构
                refactor_file(file_path)
                modified_files.append(file_path)
    
    return {
        'modified_files': modified_files,
        'backup_path': backup_path if backup else None
    }

def remove_function(file_path, func_name):
    """移除未使用的函数"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 简单的函数移除逻辑
    # 实际应用中可能需要更复杂的解析
    lines = content.split('\n')
    new_lines = []
    in_function = False
    function_indent = ''
    
    for line in lines:
        if f'def {func_name}(' in line:
            in_function = True
            function_indent = line[:line.index('def')]
        elif in_function and line.startswith(function_indent) and line.strip() and not line.startswith(f'{function_indent}    '):
            in_function = False
            new_lines.append(line)
        elif not in_function:
            new_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

def remove_variable(file_path, var_name):
    """移除未使用的变量"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 简单的变量移除逻辑
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if f'{var_name} =' not in line:
            new_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

def refactor_file(file_path):
    """重构文件"""
    # 这里可以添加具体的重构逻辑
    # 例如：提取重复代码、简化复杂逻辑等
    pass

def execute_skill(params):
    """执行技能"""
    return apply_refactor(params)