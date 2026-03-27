"""finishing-a-development-branch 技能实现 - 完成开发分支

此技能处理开发分支的清理和收尾工作。
"""


def execute_skill(params):
    """执行完成开发分支技能

    Args:
        params: 包含以下键的字典:
            - branch: 分支名称 (可选)
            - verify_tests: 是否验证测试 (默认 True)

    Returns:
        包含分支完成选项的字典
    """
    branch = params.get('branch', '')
    verify_tests = params.get('verify_tests', True)

    result = {
        'skill': 'finishing-a-development-branch',
        'status': 'ready',
        'verify_tests': verify_tests,
        'cleanup_options': [
            'merge - 合并到主分支',
            'pr - 创建拉取请求',
            'keep - 保留分支以便后续工作',
            'discard - 丢弃分支（已合并或不需要）'
        ],
        'process': [
            '1. 验证测试通过',
            '2. 检查代码状态',
            '3. 提交未提交的更改',
            '4. 选择清理选项'
        ]
    }

    if branch:
        result['branch'] = branch
        result['guidance'] = f'准备完成分支 "{branch}" 的清理工作'

    return result
