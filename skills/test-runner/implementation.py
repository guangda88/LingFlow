"""test-runner 技能实现"""

import os
import json
import subprocess
from pathlib import Path


def run_tests(params):
    """运行测试"""
    file = params.get('file')
    test_type = params.get('test_type', 'unit')
    
    # 验证参数
    if not file:
        return {"error": "请指定要测试的文件或目录"}
    
    # 检查文件或目录是否存在
    test_path = Path(file)
    if not test_path.exists():
        return {"error": f"文件或目录不存在: {file}"}
    
    # 构建测试命令
    if test_type == 'unit':
        command = ['pytest', str(test_path), '-v', '--tb=short']
    elif test_type == 'integration':
        command = ['pytest', str(test_path), '-v', '--tb=short', '-m', 'integration']
    elif test_type == 'coverage':
        command = ['pytest', str(test_path), '-v', '--tb=short', '--cov=lingflow']
    else:
        # 默认运行单元测试
        command = ['pytest', str(test_path), '-v', '--tb=short']
    
    # 运行测试
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        # 分析结果
        output = result.stdout
        passed = output.count('PASSED')
        failed = output.count('FAILED')
        error = output.count('ERROR')
        skipped = output.count('SKIPPED')
        
        # 构建结果
        test_result = {
            'success': result.returncode == 0,
            'passed': passed,
            'failed': failed,
            'error': error,
            'skipped': skipped,
            'returncode': result.returncode,
            'output': output,
            'stderr': result.stderr
        }
        
        return test_result
    except Exception as e:
        return {
            "error": f"运行测试时出错: {str(e)}",
            "success": False,
            "output": f"运行测试时出错: {str(e)}"
        }

def execute_skill(params):
    """执行技能"""
    return run_tests(params)
