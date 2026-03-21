"""test-runner 技能实现"""

import subprocess


def run_tests(params):
    """运行测试"""
    file = params.get('file') or params.get('target')
    test_type = params.get('test_type', 'unit')
    
    # 构建 pytest 命令
    cmd = ['python', '-m', 'pytest']
    if file:
        cmd.append(file)
    cmd.extend(['-v', '--tb=short', '--ignore=test_output.txt'])
    
    # 运行 pytest 或特定测试
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
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