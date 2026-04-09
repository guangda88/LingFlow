"""可信输出验证框架

让 AI 的输出可验证、可质疑、可信。
"""

from .verifier import (
    VerificationLevel,
    VerificationResult,
    TaskClaim,
    Verifier,
    FileContentVerifier,
    CommandOutputVerifier,
    DirectoryStructureVerifier,
    GitDiffVerifier,
    VerificationPipeline,
    Skeptic,
    AuditReport,
    VerificationReport,
)

from .metacognition import (
    CapabilityLevel,
    Capability,
    EvolutionPath,
    TaskRequirements,
    MetacognitiveAgent,
    get_metacognitive_agent,
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
