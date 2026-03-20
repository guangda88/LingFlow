"""test-runner 技能实现"""

import subprocess


def run_tests(params):
    """运行测试"""
    file = params.get('file')
    test_type = params.get('test_type', 'unit')
    
    # 运行 pytest 或特定测试
    result = subprocess.run(
        ['pytest', file, '-v', '--tb=short'],
        capture_output=True,
        text=True
    )
    
    return {
        'success': result.returncode == 0,
        'passed': result.stdout.count('PASSED'),
        'failed': result.stdout.count('FAILED'),
        'output': result.stdout
    }

def execute_skill(params):
    """执行技能"""
    return run_tests(params)