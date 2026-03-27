"""writing-plans 技能实现 - 编写实现计划

将规格或需求分解为可执行的任务列表。
"""


def execute_skill(params):
    """执行编写计划技能

    Args:
        params: 包含以下键的字典:
            - spec: 规格说明
            - granularity: 细节程度 (默认 'task-level')

    Returns:
        计划编写指导
    """
    spec = params.get('spec', '')
    granularity = params.get('granularity', 'task-level')

    result = {
        'skill': 'writing-plans',
        'status': 'ready',
        'granularity': granularity,
        'description': '将规格或需求分解为可执行的任务列表',
        'output_format': 'YYYY-MM-DD-<topic>-plan.md',
        'output_location': 'docs/superpowers/plans/',
        'plan_structure': [
            '概述 - 目标和成功标准',
            '先决条件 - 需要先完成的工作',
            '任务列表 - 按优先级排序的详细任务',
            '验收标准 - 如何验证完成',
            '估计时间 - 每个任务的估计时间'
        ]
    }

    if spec:
        result['spec'] = spec
        result['guidance'] = '根据规格编写详细实现计划'

    return result
