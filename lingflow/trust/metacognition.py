"""LingFlow Metacognition System

Provides knowledge boundary awareness and capability tracking for AI agents.

Core Concepts:
- Capability Matrix: What the AI knows (MASTERED, PARTIAL, UNKNOWN)
- Knowledge Boundaries: Explicit declaration of what is unknown
- Evolution Paths: How to move from UNKNOWN to MASTERED
- Pre-Task Checks: Verify capability before starting work
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class CapabilityLevel(Enum):
    """Knowledge/capability proficiency level"""

    MASTERED = 3  # 完全掌握，可以独立完成
    PARTIAL = 2  # 部分掌握，需要查阅文档或学习
    FAMILIAR = 1  # 熟悉概念，但缺乏实践经验
    UNKNOWN = 0  # 完全未知，需要从头学习

    def __str__(self):
        return self.name

    def can_handle(self, task_complexity: str = "medium") -> bool:
        """Check if this capability level can handle a task

        Args:
            task_complexity: simple, medium, complex

        Returns:
            True if this level can handle the task complexity
        """
        thresholds = {
            "simple": CapabilityLevel.FAMILIAR,
            "medium": CapabilityLevel.PARTIAL,
            "complex": CapabilityLevel.MASTERED,
        }
        return self.value >= thresholds.get(task_complexity, CapabilityLevel.PARTIAL).value


@dataclass
class EvolutionPath:
    """Path to evolve from current capability level to target"""

    source_level: CapabilityLevel
    target_level: CapabilityLevel
    steps: List[str]  # Learning/practice steps
    estimated_time: str  # "1 hour", "1 day", "1 week"
    resources: List[str]  # Documentation, tutorials, examples
    status: str = "planned"  # planned, in_progress, completed

    def to_dict(self) -> Dict:
        return {
            "source_level": self.source_level.name,
            "target_level": self.target_level.name,
            "steps": self.steps,
            "estimated_time": self.estimated_time,
            "resources": self.resources,
            "status": self.status,
        }


@dataclass
class Capability:
    """Single capability entry with proficiency and evolution path"""

    name: str  # e.g., "PostgreSQL", "React", "pytest"
    category: str  # e.g., "database", "frontend", "testing"
    level: CapabilityLevel
    last_used: Optional[datetime] = None
    evolution_paths: List[EvolutionPath] = field(default_factory=list)
    notes: str = ""  # Self-assessment notes

    def can_handle_task(self, task_complexity: str = "medium") -> bool:
        """Check if this capability can handle a task

        Args:
            task_complexity: simple, medium, complex

        Returns:
            True if capable, False otherwise
        """
        return self.level.can_handle(task_complexity)

    def needs_evolution(self, task_complexity: str = "medium") -> bool:
        """Check if evolution is needed to handle this complexity

        Args:
            task_complexity: simple, medium, complex

        Returns:
            True if evolution is needed
        """
        return not self.can_handle_task(task_complexity)

    def get_evolution_path(self, target_level: CapabilityLevel) -> Optional[EvolutionPath]:
        """Get evolution path to target level

        Args:
            target_level: Desired capability level

        Returns:
            Evolution path if exists, None otherwise
        """
        for path in self.evolution_paths:
            if path.target_level == target_level:
                return path
        return None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "category": self.category,
            "level": self.level.name,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "evolution_paths": [p.to_dict() for p in self.evolution_paths],
            "notes": self.notes,
        }


@dataclass
class TaskRequirements:
    """Requirements analysis for a task"""

    task_id: str
    task_description: str
    required_capabilities: List[str]  # List of capability names
    complexity: str  # simple, medium, complex
    gaps: List[str] = field(default_factory=list)  # Missing capabilities
    alternative_approaches: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class MetacognitiveAgent:
    """Agent with self-awareness of knowledge boundaries"""

    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}  # name -> Capability
        self.evolution_queue: List[EvolutionPath] = []  # Pending learning tasks
        self.learning_history: List[Dict] = []  # History of learning activities

    def declare_capability(
        self,
        name: str,
        category: str,
        level: CapabilityLevel,
        notes: str = "",
        evolution_steps: Optional[List[str]] = None,
    ) -> None:
        """Declare a capability with explicit level

        Args:
            name: Capability name
            category: Capability category
            level: Proficiency level
            notes: Self-assessment notes
            evolution_steps: Steps to reach next level
        """
        capability = Capability(
            name=name,
            category=category,
            level=level,
            last_used=datetime.now(),
            notes=notes,
        )

        # Add evolution paths if provided
        if evolution_steps:
            next_level = CapabilityLevel(min(level.value + 1, 3))
            evolution_path = EvolutionPath(
                source_level=level,
                target_level=next_level,
                steps=evolution_steps,
                estimated_time="TBD",
                resources=[],
            )
            capability.evolution_paths.append(evolution_path)

        self.capabilities[name] = capability

    def get_capability(self, name: str) -> Optional[Capability]:
        """Get capability by name

        Args:
            name: Capability name

        Returns:
            Capability if exists, None otherwise
        """
        return self.capabilities.get(name)

    def analyze_task_requirements(
        self, task_id: str, task_description: str, required_capabilities: List[str], complexity: str = "medium"
    ) -> TaskRequirements:
        """Analyze if task requirements match capabilities

        Args:
            task_id: Task identifier
            task_description: Task description
            required_capabilities: List of required capabilities
            complexity: Task complexity (simple, medium, complex)

        Returns:
            TaskRequirements with gap analysis
        """
        requirements = TaskRequirements(
            task_id=task_id,
            task_description=task_description,
            required_capabilities=required_capabilities,
            complexity=complexity,
        )

        # Analyze each required capability
        for cap_name in required_capabilities:
            capability = self.get_capability(cap_name)

            if capability is None:
                # Capability completely unknown
                requirements.gaps.append(f"UNKNOWN: {cap_name} - Completely unknown capability")
                requirements.recommendations.append(f"Need to learn {cap_name} from scratch")

            elif not capability.can_handle_task(complexity):
                # Capability exists but insufficient level
                requirements.gaps.append(
                    f"INSUFFICIENT: {cap_name} - Current level {capability.level.name}, "
                    f"need {complexity.upper()} complexity"
                )
                requirements.recommendations.append(f"Need to evolve {cap_name} to higher level")

        # Generate alternative approaches if gaps exist
        if requirements.gaps:
            requirements.alternative_approaches = [
                "Break down task into smaller sub-tasks",
                "Use simpler technologies that are already mastered",
                "Consult human expert for missing capabilities",
                "Allocate time for learning before starting",
            ]

        return requirements

    def propose_evolution(self, capability_name: str, target_level: CapabilityLevel, steps: List[str]) -> EvolutionPath:
        """Propose an evolution path

        Args:
            capability_name: Name of capability to evolve
            target_level: Target capability level
            steps: Learning/practice steps

        Returns:
            EvolutionPath that was created
        """
        capability = self.get_capability(capability_name)

        if capability is None:
            # Create new capability at UNKNOWN level
            self.declare_capability(capability_name, "general", CapabilityLevel.UNKNOWN)
            capability = self.get_capability(capability_name)

        evolution_path = EvolutionPath(
            source_level=capability.level,
            target_level=target_level,
            steps=steps,
            estimated_time="TBD",
            resources=[],
            status="planned",
        )

        capability.evolution_paths.append(evolution_path)
        self.evolution_queue.append(evolution_path)

        return evolution_path

    def start_evolution(self, capability_name: str) -> bool:
        """Mark evolution as in-progress

        Args:
            capability_name: Name of capability being evolved

        Returns:
            True if started successfully, False otherwise
        """
        capability = self.get_capability(capability_name)
        if capability is None:
            return False

        # Find first planned evolution path
        for path in capability.evolution_paths:
            if path.status == "planned":
                path.status = "in_progress"
                return True

        return False

    def complete_evolution(self, capability_name: str, target_level: CapabilityLevel) -> bool:
        """Mark evolution as complete and update capability level

        Args:
            capability_name: Name of capability that was evolved
            target_level: New capability level

        Returns:
            True if completed successfully, False otherwise
        """
        capability = self.get_capability(capability_name)
        if capability is None:
            return False

        # Update capability level
        capability.level = target_level
        capability.last_used = datetime.now()

        # Mark evolution path as completed
        for path in capability.evolution_paths:
            if path.target_level == target_level:
                path.status = "completed"

        # Record in history
        self.learning_history.append(
            {
                "capability": capability_name,
                "from_level": path.source_level.name,
                "to_level": target_level.name,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Remove from queue
        self.evolution_queue = [
            p for p in self.evolution_queue if p not in capability.evolution_paths or p.status != "completed"
        ]

        return True

    def get_knowledge_boundaries_report(self) -> Dict:
        """Generate report of knowledge boundaries

        Returns:
            Dict with categorized capabilities
        """
        mastered = []
        partial = []
        familiar = []
        unknown = []

        for capability in self.capabilities.values():
            if capability.level == CapabilityLevel.MASTERED:
                mastered.append(capability.to_dict())
            elif capability.level == CapabilityLevel.PARTIAL:
                partial.append(capability.to_dict())
            elif capability.level == CapabilityLevel.FAMILIAR:
                familiar.append(capability.to_dict())
            else:
                unknown.append(capability.to_dict())

        return {
            "mastered": mastered,
            "partial": partial,
            "familiar": familiar,
            "unknown": unknown,
            "evolution_queue": [p.to_dict() for p in self.evolution_queue],
            "learning_history": self.learning_history,
        }

    def can_declare_completion(self, task_requirements: TaskRequirements) -> tuple[bool, str]:
        """Determine if can declare task completion based on capabilities

        Args:
            task_requirements: Task requirements analysis

        Returns:
            (can_complete, reason) tuple
        """
        if task_requirements.gaps:
            return (
                False,
                f"Cannot declare completion: {len(task_requirements.gaps)} capability gaps found. "
                f"Must address: {', '.join(task_requirements.gaps[:3])}",
            )

        return True, "All required capabilities available at sufficient level"

    # -- Persistence --

    STATE_DIR = Path(".lingflow/metacognition_states")

    def to_dict(self) -> Dict:
        """Serialize agent state to a plain dict."""
        return {
            "capabilities": {name: cap.to_dict() for name, cap in self.capabilities.items()},
            "evolution_queue": [ep.to_dict() for ep in self.evolution_queue],
            "learning_history": list(self.learning_history),
            "saved_at": datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MetacognitiveAgent":
        """Reconstruct a MetacognitiveAgent from a serialized dict."""
        agent = cls()

        for name, cap_data in data.get("capabilities", {}).items():
            cap_data_copy = dict(cap_data)
            cap_data_copy["level"] = CapabilityLevel[cap_data_copy["level"]]
            if cap_data_copy.get("last_used") is not None:
                cap_data_copy["last_used"] = datetime.fromisoformat(cap_data_copy["last_used"])
            cap_data_copy["evolution_paths"] = [
                EvolutionPath(
                    source_level=CapabilityLevel[ep["source_level"]],
                    target_level=CapabilityLevel[ep["target_level"]],
                    steps=ep["steps"],
                    estimated_time=ep["estimated_time"],
                    resources=ep["resources"],
                    status=ep["status"],
                )
                for ep in cap_data_copy.get("evolution_paths", [])
            ]
            agent.capabilities[name] = Capability(**cap_data_copy)

        agent.evolution_queue = [
            EvolutionPath(
                source_level=CapabilityLevel[ep["source_level"]],
                target_level=CapabilityLevel[ep["target_level"]],
                steps=ep["steps"],
                estimated_time=ep["estimated_time"],
                resources=ep["resources"],
                status=ep["status"],
            )
            for ep in data.get("evolution_queue", [])
        ]

        agent.learning_history = list(data.get("learning_history", []))

        return agent

    def save_state(self, path: Optional[Path] = None) -> Path:
        """Save agent state to a JSON file.

        Args:
            path: Optional explicit file path. Defaults to
                  .lingflow/metacognition_states/<timestamp>.json

        Returns:
            Path to the saved file.
        """
        if path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.STATE_DIR / f"{ts}.json"

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info("MetacognitiveAgent state saved to %s", path)
        return path

    @classmethod
    def load_state(cls, path: Path) -> "MetacognitiveAgent":
        """Load agent state from a JSON file.

        Args:
            path: Path to the saved state file.

        Returns:
            Reconstructed MetacognitiveAgent.

        Raises:
            FileNotFoundError: If the state file does not exist.
            ValueError: If the state file is corrupt.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"State file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        agent = cls.from_dict(data)
        logger.info("MetacognitiveAgent state loaded from %s", path)
        return agent

    @classmethod
    def find_latest_state(cls) -> Optional[Path]:
        """Find the most recent state file in the default directory.

        Returns:
            Path to the latest state file, or None if none exist.
        """
        state_dir = cls.STATE_DIR
        if not state_dir.exists():
            return None

        files = sorted(state_dir.glob("*.json"), reverse=True)
        return files[0] if files else None


# Singleton instance
_default_metacognitive_agent: Optional[MetacognitiveAgent] = None


def get_metacognitive_agent() -> MetacognitiveAgent:
    """Get default metacognitive agent instance, auto-loading persisted state if available"""
    global _default_metacognitive_agent
    if _default_metacognitive_agent is None:
        latest = MetacognitiveAgent.find_latest_state()
        if latest is not None:
            try:
                _default_metacognitive_agent = MetacognitiveAgent.load_state(latest)
                return _default_metacognitive_agent
            except Exception:
                logger.warning("Failed to load persisted metacognitive state from %s, starting fresh", latest)
        _default_metacognitive_agent = MetacognitiveAgent()
    return _default_metacognitive_agent
