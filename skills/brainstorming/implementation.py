"""brainstorming 技能实现 - 文档驱动技能

此技能通过 SKILL.md 文档驱动，提供设计探索和头脑风暴流程。
"""


def execute_skill(params):
    """执行头脑风暴技能

    Args:
        params: 包含以下键的字典:
            - topic: 要探索的主题 (可选)
            - context: 项目上下文 (可选)
            - questions: 初始问题列表 (可选)

    Returns:
        包含技能说明和指导的字典
    """
    topic = params.get('topic', '')
    context = params.get('context', '')

    result = {
        'skill': 'brainstorming',
        'status': 'ready',
        'instructions': '请按照以下流程进行头脑风暴：',
        'process': [
            '1. 探索项目上下文 - 检查文件、文档、最近的提交',
            '2. 提出澄清问题 - 一次一个，理解目的/约束/成功标准',
            '3. 提出2-3种方法 - 包含权衡和你的推荐',
            '4. 展示设计 - 按部分展示，每部分后获得用户批准',
            '5. 编写设计文档 - 保存到 docs/superpowers/specs/',
            '6. 转移到实现 - 调用 writing-plans 技能创建实现计划'
        ],
        'hard_gate': '在获得用户批准设计之前，不要进行任何实现操作！'
    }

    if topic:
        result['topic'] = topic
        result['guidance'] = f'针对主题 "{topic}" 开始头脑风暴流程'

    if context:
        result['context'] = context

    return result
