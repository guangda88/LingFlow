"""code-analysis 技能实现"""

import os
import json
import ast
from pathlib import Path


def analyze_code(params):
    """分析代码"""
    target = params.get('target')
    metrics = params.get('metrics', [])
    
    # 验证参数
    if not target:
        return {"error": "请指定要分析的目标路径"}
    
    # 初始化结果
    result = {
        'total_files': 0,
        'total_lines': 0,
        'complexity': {},
        'duplication_rate': 0,
        'duplicate_files': [],
        'dead_code': []
    }
    
    # 遍历目标目录
    target_path = Path(target)
    if not target_path.exists():
        return {"error": f"目标路径 {target} 不存在"}
    
    # 收集所有 Python 文件
    py_files = list(target_path.rglob('*.py'))
    result['total_files'] = len(py_files)
    
    # 分析每个文件
    for py_file in py_files:
        try:
            # 读取文件内容
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            result['total_lines'] += len(lines)
            
            # 分析复杂度
            if 'complexity' in metrics:
                complexity = calculate_complexity(content)
                result['complexity'][str(py_file)] = complexity
            
            # 检测死代码
            if 'dead_code' in metrics:
                dead_code = detect_dead_code(content)
                if dead_code:
                    result['dead_code'].append({
                        'file': str(py_file),
                        'issues': dead_code
                    })
        except Exception as e:
            print(f"分析文件 {py_file} 时出错: {str(e)}")
    
    # 检测重复代码
    if 'duplication' in metrics and len(py_files) > 1:
        duplication = detect_duplication(py_files)
        result['duplication_rate'] = duplication['rate']
        result['duplicate_files'] = duplication['files']
    
    return result

def calculate_complexity(code):
    """计算代码的圈复杂度"""
    # 简单的圈复杂度计算
    # 实际应用中，可能需要使用更复杂的算法
    complexity = 1
    for line in code.split('\n'):
        line = line.strip()
        if any(keyword in line for keyword in ['if', 'elif', 'while', 'for', 'try', 'except', 'with']):
            complexity += 1
    return complexity

def detect_dead_code(code):
    """检测死代码"""
    # 简单的死代码检测
    # 实际应用中，可能需要使用更复杂的分析
    dead_code = []
    
    # 解析代码
    try:
        tree = ast.parse(code)
    except Exception:
        return dead_code
    
    # 收集所有函数和变量定义
    defined_functions = set()
    defined_variables = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined_functions.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_variables.add(target.id)
    
    # 收集所有函数和变量使用
    used_functions = set()
    used_variables = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            used_functions.add(node.func.id)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_variables.add(node.id)
    
    # 识别未使用的函数和变量
    for func in defined_functions:
        # 排除 __init__ 方法和特殊方法
        if func not in used_functions and not func.startswith('__'):
            dead_code.append(f"未使用的函数: {func}")
    
    for var in defined_variables:
        # 排除 __all__ 变量和特殊变量
        if var not in used_variables and not var.startswith('__'):
            dead_code.append(f"未使用的变量: {var}")
    
    return dead_code

def detect_duplication(files):
    """检测重复代码"""
    # 简单的重复代码检测
    # 实际应用中，可能需要使用更复杂的算法
    duplicate_files = []
    total_lines = 0
    duplicate_lines = 0
    
    # 计算文件内容的相似度
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            try:
                content1 = files[i].read_text(encoding='utf-8')
                content2 = files[j].read_text(encoding='utf-8')
                
                # 简单的相似度计算
                lines1 = content1.split('\n')
                lines2 = content2.split('\n')
                
                # 计算相同的行数
                common_lines = set(lines1) & set(lines2)
                common_count = len(common_lines)
                
                if common_count > 5:  # 只考虑至少5行相同的情况
                    duplicate_files.append({
                        'file1': str(files[i]),
                        'file2': str(files[j]),
                        'common_lines': common_count
                    })
                    duplicate_lines += common_count
                    total_lines += len(lines1) + len(lines2)
            except Exception as e:
                print(f"比较文件 {files[i]} 和 {files[j]} 时出错: {str(e)}")
    
    # 计算重复率
    if total_lines > 0:
        duplication_rate = duplicate_lines / total_lines
    else:
        duplication_rate = 0
    
    return {
        'rate': duplication_rate,
        'files': duplicate_files
    }

def execute_skill(params):
    """执行技能"""
    return analyze_code(params)
