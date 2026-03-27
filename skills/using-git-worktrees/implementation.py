"""using-git-worktrees 技能实现 - Git 工作树

创建隔离的工作空间进行并行开发。
"""


def execute_skill(params):
    """执行 Git 工作树技能

    Args:
        params: 包含以下键的字典:
            - branch: 新分支名称
            - base_branch: 基础分支 (默认 'master')

    Returns:
        工作树创建指导或结果
    """
    branch = params.get('branch', '')
    base_branch = params.get('base_branch', 'master')

    result = {
        'skill': 'using-git-worktrees',
        'status': 'ready',
        'description': '创建 Git 工作树进行隔离开发',
        'benefits': [
            '并行开发多个功能',
            '保持主分支干净',
            '快速上下文切换',
            '独立测试环境'
        ],
        'command_template': 'git worktree add -b {branch} ../{branch}-workspace {base_branch}',
        'cleanup': '使用 finishing-a-development-branch 技能清理'
    }

    if branch:
        result['branch'] = branch
        result['base_branch'] = base_branch
        result['command'] = f'git worktree add -b {branch} ../{branch}-workspace {base_branch}'
        result['guidance'] = f'为分支 "{branch}" 创建独立工作树'

    return result
