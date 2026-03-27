"""test-driven-development 技能实现 - 测试驱动开发

强制 RED-GREEN-REFACTOR 循环。
"""


def execute_skill(params):
    """执行 TDD 技能

    Args:
        params: 包含以下键的字典:
            - feature: 要开发的功能
            - test_framework: 测试框架 (可选)

    Returns:
        TDD 流程指导
    """
    feature = params.get('feature', '')
    test_framework = params.get('test_framework', 'pytest')

    result = {
        'skill': 'test-driven-development',
        'status': 'ready',
        'test_framework': test_framework,
        'cycle': [
            'RED - 编写失败的测试',
            'GREEN - 编写最少代码使测试通过',
            'REFACTOR - 重构代码'
        ],
        'rules': [
            '在编写功能代码之前编写测试',
            '只编写足以使当前失败的测试通过的代码',
            '重构成简单和可维护的代码'
        ]
    }

    if feature:
        result['feature'] = feature
        result['guidance'] = f'对功能 "{feature}" 应用 TDD 流程'

    return result
