"""LingFlow Core Module"""

from lingflow.core.compliance_matrix import ComplianceMatrix
from lingflow.core.config import LingFlowConfig
from lingflow.core.constitution import (
    ComplianceReport,
    Constitution,
    ConstitutionalPrinciple,
)
from lingflow.core.skill import (
    BaseSkill,
    FunctionSkill,
    SkillContext,
    SkillRegistry,
    get_skill,
    register_function,
    register_skill,
)
from lingflow.core.types import LingFlowError, Result

__all__ = [
    "Constitution",
    "ConstitutionalPrinciple",
    "ComplianceReport",
    "ComplianceMatrix",
    "LingFlowConfig",
    "LingFlowError",
    "Result",
    # Skill system
    "BaseSkill",
    "FunctionSkill",
    "SkillContext",
    "SkillRegistry",
    "get_skill",
    "register_function",
    "register_skill",
]
