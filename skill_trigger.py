"""
LingFlow Skill Trigger System

This module provides the skill triggering mechanism for LingFlow,
automatically detecting when to invoke specific skills based on context.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SkillTrigger:
    """Determines which skills should be triggered based on context.

    This class analyzes context, task types, and development phases
    to automatically determine which LingFlow skills should be invoked.
    It supports keyword-based triggers, phase-based triggers, and
    explicit skill mentions.
    """

    def __init__(self, skills_config_path: str = "skills/skills.json"):
        """Initialize the skill trigger system.

        Args:
            skills_config_path: Path to skills configuration file
        """
        self.skills_config_path = Path(skills_config_path)
        self.skills = self._load_skills()
        self.settings = self._load_settings()

    def _load_skills(self) -> List[Dict[str, Any]]:
        """Load skills from configuration file.

        Returns:
            List of skill configurations
        """
        if not self.skills_config_path.exists():
            logger.warning(f"Skills config not found: {self.skills_config_path}")
            return []

        with open(self.skills_config_path, 'r') as f:
            config = json.load(f)
            return config.get('skills', [])

    def _load_settings(self) -> Dict[str, Any]:
        """Load global settings from configuration.

        Returns:
            Settings dictionary
        """
        if not self.skills_config_path.exists():
            return {}

        with open(self.skills_config_path, 'r') as f:
            config = json.load(f)
            return config.get('settings', {})

    def trigger_skill(
        self,
        context: str,
        task_type: str,
        current_phase: Optional[str] = None,
        completed_phases: Optional[List[str]] = None
    ) -> Optional[str]:
        """Determine which skill to trigger based on context.

        Args:
            context: The user's request or current context
            task_type: Type of task (e.g., "feature", "debug", "plan")
            current_phase: Current development phase (optional)
            completed_phases: List of completed phases (optional)

        Returns:
            Name of skill to trigger, or None if no match
        """
        context_lower = context.lower()

        # Check for explicit skill mentions
        if "use brainstorming" in context_lower or "brainstorm" in context_lower:
            return "brainstorming"
        if "write plan" in context_lower or "create plan" in context_lower:
            return "writing-plans"
        if "test-driven" in context_lower or "tdd" in context_lower:
            return "test-driven-development"
        if "verify" in context_lower or "check" in context_lower:
            return "verification-before-completion"
        if "debug" in context_lower or "fix" in context_lower:
            return "systematic-debugging"

        # Auto-trigger based on task type and phase
        skill = self._determine_skill_by_phase(task_type, current_phase, completed_phases)
        if skill:
            return skill

        # Auto-trigger based on keywords
        skill = self._determine_skill_by_keywords(context_lower, task_type)
        if skill:
            return skill

        return None

    def _determine_skill_by_phase(
        self,
        task_type: str,
        current_phase: Optional[str],
        completed_phases: Optional[List[str]]
    ) -> Optional[str]:
        """Determine skill based on development phase.

        Args:
            task_type: Type of task
            current_phase: Current development phase
            completed_phases: Completed phases

        Returns:
            Skill name or None
        """
        completed = completed_phases or []

        # Phase-based workflow
        if current_phase is None or not completed:
            # Starting a new task - brainstorming
            if task_type in ["feature", "implement", "create", "build"]:
                return "brainstorming"

        elif "brainstorming" in completed and "writing-plans" not in completed:
            # Design approved - write plan
            return "writing-plans"

        elif "writing-plans" in completed and "using-git-worktrees" not in completed:
            # Plan ready - create worktree
            return "using-git-worktrees"

        elif "using-git-worktrees" in completed and "subagent-driven-development" not in completed:
            # Worktree ready - start implementation
            return "subagent-driven-development"

        elif "subagent-driven-development" in completed:
            # Implementation complete - finishing
            return "finishing-a-development-branch"

        return None

    def _determine_skill_by_keywords(self, context: str, task_type: str) -> Optional[str]:
        """Determine skill based on keywords in context.

        Args:
            context: Lowercase context string
            task_type: Type of task

        Returns:
            Skill name or None
        """
        for skill in self.skills:
            triggers = skill.get('triggers', [])
            skill_name = skill.get('name')

            for trigger in triggers:
                trigger_lower = trigger.lower()
                if trigger_lower in context:
                    return skill_name

        return None

    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill information or None if not found
        """
        for skill in self.skills:
            if skill.get('name') == skill_name:
                return skill
        return None

    def list_available_skills(self) -> List[str]:
        """List all available skills.

        Returns:
            List of skill names
        """
        return [skill.get('name') for skill in self.skills]

    def can_trigger_skill(
        self,
        skill_name: str,
        completed_phases: Optional[List[str]] = None
    ) -> bool:
        """Check if a skill can be triggered based on dependencies.

        Args:
            skill_name: Name of the skill
            completed_phases: Completed phases

        Returns:
            True if skill can be triggered, False otherwise
        """
        skill_info = self.get_skill_info(skill_name)
        if not skill_info:
            return False

        depends_on = skill_info.get('depends_on', [])
        completed = completed_phases or []

        for dependency in depends_on:
            if dependency not in completed:
                logger.info(
                    f"Skill '{skill_name}' depends on '{dependency}' "
                    f"which is not completed yet"
                )
                return False

        return True


def main() -> None:
    """Main entry point for testing the skill trigger system."""

    # Initialize trigger system
    trigger = SkillTrigger()

    # Test examples
    test_cases = [
        ("I want to add a user authentication feature", "feature"),
        ("Help me debug this timeout issue", "debug"),
        ("Write a plan for the authentication system", "plan"),
        ("Verify the fix works", "verify"),
        ("Implement the user login functionality", "implement"),
    ]

    print("=" * 60)
    print("LingFlow Skill Trigger System")
    print("=" * 60)

    for context, task_type in test_cases:
        print(f"\nContext: {context}")
        print(f"Task Type: {task_type}")

        triggered_skill = trigger.trigger_skill(
            context=context,
            task_type=task_type
        )

        if triggered_skill:
            skill_info = trigger.get_skill_info(triggered_skill)
            print(f"✓ Triggered Skill: {triggered_skill}")
            if skill_info:
                print(f"  Description: {skill_info.get('description', '')}")
        else:
            print("✗ No skill triggered")

    print("\n" + "=" * 60)
    print(f"Available Skills: {', '.join(trigger.list_available_skills())}")
    print("=" * 60)


if __name__ == "__main__":
    main()
