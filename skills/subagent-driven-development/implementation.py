"""subagent-driven-development 技能实现 - 子代理驱动开发

快速迭代配合两阶段审查（规范符合性，然后代码质量）。
"""


def execute_skill(params):
    """执行子代理驱动开发技能

    Args:
        params: 包含以下键的字典:
            - plan: 实现计划
            - iteration_mode: 迭代模式 (默认 'rapid')

    Returns:
        开发流程指导
    """
    plan = params.get('plan', '')
    iteration_mode = params.get('iteration_mode', 'rapid')

    result = {
        'skill': 'subagent-driven-development',
        'status': 'ready',
        'iteration_mode': iteration_mode,
        'review_stages': [
            'spec_compliance - 规范符合性审查',
            'code_quality - 代码质量审查'
        ],
        'process': [
            '1. 审查实现计划',
            '2. 执行规范符合性审查',
            '3. 执行代码质量审查',
            '4. 快速迭代直到完成'
        ]
    }

    if plan:
        result['plan'] = plan
        result['guidance'] = '按照计划执行子代理驱动开发流程'

    return result
