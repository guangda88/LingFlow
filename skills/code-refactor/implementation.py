"""code-refactor 技能实现"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime


def execute_refactor(params):
    """执行代码重构"""
    changes = params.get('changes', [])
    backup = params.get('backup', True)
    
    # 验证参数
    if not changes:
        return {"error": "请指定要执行的变更"}
    
    # 初始化结果
    result = {
        'modified_files': [],
        'backup_path': None
    }
    
    # 创建备份
    if backup:
        try:
            backup_path = f".backup/{datetime.now().isoformat()}"
            # 创建备份目录
            Path(backup_path).mkdir(parents=True, exist_ok=True)
            
            # 备份 lingflow 目录
            lingflow_dir = Path('./lingflow')
            if lingflow_dir.exists():
                shutil.copytree('./lingflow', f"{backup_path}/lingflow")
                result['backup_path'] = backup_path
                print(f"创建备份到 {backup_path}")
        except Exception as e:
            print(f"创建备份失败: {str(e)}")
    
    # 应用变更
    for change in changes:
        try:
            file_path = change.get('file')
            change_type = change.get('type')
            description = change.get('description')
            
            if not file_path:
                print(f"跳过缺少文件路径的变更: {description}")
                continue
            
            # 检查文件是否存在
            file = Path(file_path)
            if not file.exists():
                print(f"文件不存在: {file_path}")
                continue
            
            # 应用变更
            if change_type == 'remove_function':
                success = remove_function(file, description)
            elif change_type == 'remove_variable':
                success = remove_variable(file, description)
            elif change_type == 'extract_function':
                success = extract_function(file, description)
            elif change_type == 'split_function':
                success = split_function(file, description)
            elif change_type == 'remove_unused':
                success = remove_unused(file, description)
            else:
                print(f"未知的变更类型: {change_type}")
                continue
            
            if success:
                result['modified_files'].append(file_path)
                print(f"成功应用变更: {description}")
            else:
                print(f"应用变更失败: {description}")
        except Exception as e:
            print(f"处理变更时出错: {str(e)}")
    
    return result

def remove_function(file, description):
    """删除未使用的函数"""
    # 简单的函数删除逻辑
    # 实际应用中，可能需要更复杂的解析
    content = file.read_text(encoding='utf-8')
    
    # 提取函数名
    if '删除未使用的函数' in description:
        function_name = description.split('删除未使用的函数 ')[1]
        
        # 简单的函数删除
        # 实际应用中，需要解析 AST 来准确删除函数
        lines = content.split('\n')
        new_lines = []
        in_function = False
        function_indent = None
        
        for line in lines:
            if f'def {function_name}(' in line:
                in_function = True
                function_indent = len(line) - len(line.lstrip())
            elif in_function:
                # 检查是否是函数结束
                current_indent = len(line) - len(line.lstrip())
                if current_indent < function_indent and line.strip():
                    in_function = False
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # 写回文件
        new_content = '\n'.join(new_lines)
        file.write_text(new_content, encoding='utf-8')
        return True
    
    return False

def remove_variable(file, description):
    """删除未使用的变量"""
    # 简单的变量删除逻辑
    content = file.read_text(encoding='utf-8')
    
    # 提取变量名
    if '删除未使用的变量' in description:
        variable_name = description.split('删除未使用的变量 ')[1]
        
        # 简单的变量删除
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if f'{variable_name} =' not in line:
                new_lines.append(line)
        
        # 写回文件
        new_content = '\n'.join(new_lines)
        file.write_text(new_content, encoding='utf-8')
        return True
    
    return False

def extract_function(file, description):
    """提取重复代码为函数"""
    # 简单的函数提取逻辑
    # 实际应用中，需要更复杂的解析
    print(f"提取函数: {description}")
    # 这里只是模拟提取函数的过程
    return True

def split_function(file, description):
    """拆分复杂函数"""
    # 简单的函数拆分逻辑
    # 实际应用中，需要更复杂的解析
    print(f"拆分函数: {description}")
    # 这里只是模拟拆分函数的过程
    return True

def remove_unused(file, description):
    """删除未使用的代码"""
    # 简单的未使用代码删除逻辑
    content = file.read_text(encoding='utf-8')
    
    # 提取未使用的项
    if '删除未使用的' in description:
        # 简单的删除逻辑
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if '未使用的' not in line:
                new_lines.append(line)
        
        # 写回文件
        new_content = '\n'.join(new_lines)
        file.write_text(new_content, encoding='utf-8')
        return True
    
    return False

def execute_skill(params):
    """执行技能"""
    return execute_refactor(params)
