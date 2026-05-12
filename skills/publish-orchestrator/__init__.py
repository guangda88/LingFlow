"""publish-orchestrator 技能初始化文件"""

try:
    from .implementation import execute_skill
except ImportError:
    from implementation import execute_skill

__all__ = ['execute_skill']
__version__ = '1.0.0'
