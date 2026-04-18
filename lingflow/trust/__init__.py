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
from .l3_monitor import (
    IdentityDriftDetector,
    IdentityModel,
    L3Severity,
    MetacognitiveStateMonitor,
    MSObservation,
    MSStatus,
    OntologyValidator,
    create_ms_monitor,
)
from .l3_query_engine import (
    L3EnhancedQueryEngine,
    create_l3_enhanced_engine,
)
from .l3_checkpoint_validator import (
    CheckpointType,
    CounterfactualValidator,
    IntegrityChecker,
    MSCheckpoint,
    MSCheckpointValidator,
    ValidationResult,
    ValidationReport,
    create_ms_validator,
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
    # Metacognition (MC - 能力层）
    "CapabilityLevel",
    "Capability",
    "EvolutionPath",
    "TaskRequirements",
    "MetacognitiveAgent",
    "get_metacognitive_agent",
    # L3 Monitor (MS - 状态层）
    "MSStatus",
    "L3Severity",
    "IdentityModel",
    "MSObservation",
    "IdentityDriftDetector",
    "OntologyValidator",
    "MetacognitiveStateMonitor",
    "create_ms_monitor",
    # L3 Checkpoint Validator (完整性验证层）
    "CheckpointType",
    "ValidationResult",
    "MSCheckpoint",
    "ValidationReport",
    "IntegrityChecker",
    "CounterfactualValidator",
    "MSCheckpointValidator",
    "create_ms_validator",
    # L3 Enhanced QueryEngine (集成层）
    "L3EnhancedQueryEngine",
    "create_l3_enhanced_engine",
]
