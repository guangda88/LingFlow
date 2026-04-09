"""可信输出验证框架

让 AI 的输出可验证、可质疑、可信。
"""

from .metacognition import (
    Capability,
    CapabilityLevel,
    EvolutionPath,
    MetacognitiveAgent,
    TaskRequirements,
    get_metacognitive_agent,
)
from .verifier import (
    AuditReport,
    CommandOutputVerifier,
    DirectoryStructureVerifier,
    FileContentVerifier,
    GitDiffVerifier,
    Skeptic,
    TaskClaim,
    VerificationLevel,
    VerificationPipeline,
    VerificationReport,
    VerificationResult,
    Verifier,
)

__all__ = [
    "VerificationLevel",
    "VerificationResult",
    "TaskClaim",
    "Verifier",
    "FileContentVerifier",
    "CommandOutputVerifier",
    "DirectoryStructureVerifier",
    "GitDiffVerifier",
    "VerificationPipeline",
    "Skeptic",
    "AuditReport",
    "VerificationReport",
    # Metacognition
    "CapabilityLevel",
    "Capability",
    "EvolutionPath",
    "TaskRequirements",
    "MetacognitiveAgent",
    "get_metacognitive_agent",
]
