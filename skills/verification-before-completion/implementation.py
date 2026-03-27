"""verification-before-completion 技能实现 - 完成前验证

确保问题真正修复，不要假设。
"""


def execute_skill(params):
    """执行完成前验证技能

    Args:
        params: 包含以下键的字典:
            - fix: 修复描述
            - test_command: 测试命令 (可选)

    Returns:
        验证指导
    """
    fix = params.get('fix', '')
    test_command = params.get('test_command', '')

    result = {
        'skill': 'verification-before-completion',
        'status': 'ready',
        'principle': '确保问题真正修复，不要假设',
        'steps': [
            '1. 运行复现步骤 - 确认问题已修复',
            '2. 运行测试套件 - 确保没有回归',
            '3. 检查边缘情况 - 确保修复完整',
            '4. 验证副作用 - 确保没有引入新问题'
        ],
        'anti_pattern': '不要假设修复有效 - 实际运行测试验证'
    }

    if fix:
        result['fix'] = fix
        result['guidance'] = f'验证修复 "{fix}" 是否真正解决问题'

    if test_command:
        result['test_command'] = test_command

    return result
