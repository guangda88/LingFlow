"""ui-mockup-generator 技能包

从自然语言需求描述生成 HTML/CSS UI 原型
"""

from .implementation import generate_mockup, parse_requirements, execute_skill

__all__ = ['generate_mockup', 'parse_requirements', 'execute_skill']
__version__ = '1.0.0'
