"""code-review 技能实现"""

import os
import json
from pathlib import Path


def review_code(params):
    """审查代码"""
    focus = params.get('focus', 'code_quality')
    files = params.get('files', [])
    
    # 验证参数
    if not files:
        return {"error": "请指定要审查的文件或目录"}
    
    # 初始化结果
    result = {
        'reviewed_files': [],
        'issues': [],
        'suggestions': [],
        'summary': f"已审查 {len(files)} 个文件"
    }
    
    # 审查每个文件
    for file_path in files:
        try:
            file = Path(file_path)
            if not file.exists():
                print(f"文件不存在: {file_path}")
                continue
            
            # 检查是文件还是目录
            if file.is_file():
                review_result = review_file(file, focus)
                result['reviewed_files'].append(file_path)
                result['issues'].extend(review_result.get('issues', []))
                result['suggestions'].extend(review_result.get('suggestions', []))
            elif file.is_dir():
                # 审查目录中的所有 Python 文件
                for py_file in file.rglob('*.py'):
                    review_result = review_file(py_file, focus)
                    result['reviewed_files'].append(str(py_file))
                    result['issues'].extend(review_result.get('issues', []))
                    result['suggestions'].extend(review_result.get('suggestions', []))
        except Exception as e:
            print(f"审查文件时出错: {str(e)}")
    
    # 更新摘要
    result['summary'] = f"已审查 {len(result['reviewed_files'])} 个文件，发现 {len(result['issues'])} 个问题，提供 {len(result['suggestions'])} 个建议"
    
    return result

def review_file(file, focus):
    """审查单个文件"""
    # 初始化结果
    result = {
        'issues': [],
        'suggestions': []
    }
    
    try:
        content = file.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        if focus == 'duplicate_code':
            # 检查重复代码
            result = review_duplicate_code(file, content, lines)
        elif focus == 'code_quality':
            # 检查代码质量
            result = review_code_quality(file, content, lines)
        elif focus == 'security':
            # 检查安全问题
            result = review_security(file, content, lines)
        else:
            # 默认检查
            result = review_default(file, content, lines)
    except Exception as e:
        print(f"审查文件 {file} 时出错: {str(e)}")
    
    return result

def review_duplicate_code(file, content, lines):
    """检查重复代码"""
    result = {
        'issues': [],
        'suggestions': []
    }
    
    # 简单的重复代码检测
    # 实际应用中，可能需要更复杂的算法
    line_count = len(lines)
    if line_count > 100:
        result['issues'].append({
            'file': str(file),
            'issue': '文件过长',
            'severity': 'warning',
            'line': 1
        })
        result['suggestions'].append({
            'file': str(file),
            'suggestion': '考虑将文件拆分为多个模块',
            'priority': 'medium'
        })
    
    return result

def review_code_quality(file, content, lines):
    """检查代码质量"""
    result = {
        'issues': [],
        'suggestions': []
    }
    
    # 检查代码质量
    # 实际应用中，可能需要使用更专业的工具
    function_count = content.count('def ')
    if function_count > 20:
        result['issues'].append({
            'file': str(file),
            'issue': '函数数量过多',
            'severity': 'warning',
            'line': 1
        })
        result['suggestions'].append({
            'file': str(file),
            'suggestion': '考虑将相关函数提取到单独的模块',
            'priority': 'medium'
        })
    
    return result

def review_security(file, content, lines):
    """检查安全问题"""
    result = {
        'issues': [],
        'suggestions': []
    }
    
    # 检查安全问题
    # 实际应用中，可能需要使用更专业的工具
    security_patterns = ['eval(', 'exec(', 'input(', 'open(']
    for pattern in security_patterns:
        if pattern in content:
            result['issues'].append({
                'file': str(file),
                'issue': f'可能存在安全风险: {pattern}',
                'severity': 'warning',
                'line': content.index(pattern) // 100 + 1
            })
            result['suggestions'].append({
                'file': str(file),
                'suggestion': f'请谨慎使用 {pattern}，确保输入安全',
                'priority': 'high'
            })
    
    return result

def review_default(file, content, lines):
    """默认检查"""
    result = {
        'issues': [],
        'suggestions': []
    }
    
    # 简单的默认检查
    line_count = len(lines)
    if line_count == 0:
        result['issues'].append({
            'file': str(file),
            'issue': '空文件',
            'severity': 'info',
            'line': 1
        })
    
    return result

def execute_skill(params):
    """执行技能"""
    return review_code(params)
