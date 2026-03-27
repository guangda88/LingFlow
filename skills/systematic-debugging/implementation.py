"""systematic-debugging 技能实现 - 系统化调试

4 阶段根本原因分析过程（观察、隔离、假设、验证）。
"""


def execute_skill(params):
    """执行系统化调试技能

    Args:
        params: 包含以下键的字典:
            - issue: 问题描述
            - context: 上下文信息 (可选)

    Returns:
        调试流程指导
    """
    issue = params.get('issue', '')
    context = params.get('context', '')

    result = {
        'skill': 'systematic-debugging',
        'status': 'ready',
        'phases': [
            'observe - 观察问题',
            'isolate - 隔离问题',
            'hypothesize - 提出假设',
            'verify - 验证假设'
        ],
        'process': [
            '1. 观察问题 - 收集症状、错误信息、复现步骤',
            '2. 隔离问题 - 缩小范围，确定问题边界',
            '3. 提出假设 - 基于证据提出根本原因假设',
            '4. 验证假设 - 设计测试验证假设，直到找到根因'
        ]
    }

    if issue:
        result['issue'] = issue
        result['guidance'] = f'对问题 "{issue}" 开始系统化调试流程'

    if context:
        result['context'] = context

    return result
