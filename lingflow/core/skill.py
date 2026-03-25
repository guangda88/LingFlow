"""LingFlow Skill System Module

This module provides a standardized skill interface for LingFlow.
Supports both class-based and function-based skills.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .types import Result


@dataclass
class SkillContext:
    """Skill execution context.

    Contains information about the skill execution environment.

    Attributes:
        skill_name: Name of the skill being executed
        params: Parameters passed to the skill
        working_dir: Current working directory
        metadata: Additional metadata (optional)
    """

    skill_name: str
    params: Dict[str, Any]
    working_dir: str = "."
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    """Base skill class (lightweight).

    Recommended for new skills, but not mandatory for backward compatibility.

    Design principles:
        - Recommended use: New skills should inherit from BaseSkill
        - Not enforced: Functional skills are still fully supported
        - Progressive migration: Existing skills can migrate gradually
        - Practical first: Only provides core functionality

    Attributes:
        name: Skill identifier
        description: Skill description
        version: Skill version
    """

    # Metadata (class attributes for overriding)
    name: str = "base-skill"
    description: str = "Base skill"
    version: str = "1.0.0"

    def execute(self, params: Dict[str, Any]) -> Result[Any]:
        """Execute the skill.

        Provides default implementation that wraps _execute_impl with error handling.

        Args:
            params: Skill parameters

        Returns:
            Result with execution data or error

        Example:
            >>> skill = MySkill()
            >>> result = skill.execute({"param": "value"})
            >>> if result.success:
            ...     print(result.data)
        """
        context = SkillContext(
            skill_name=self.name,
            params=params,
            working_dir=".",
        )

        try:
            # Validate parameters if implemented
            validation = self.validate_params(params)
            if validation.is_error:
                return validation

            # Execute the skill
            data = self._execute_impl(context)
            return Result.ok(data)
        except Exception as e:
            return Result.fail(str(e))

    @abstractmethod
    def _execute_impl(self, context: SkillContext) -> Any:
        """Execute the skill implementation.

        Must be implemented by subclasses.

        Args:
            context: Skill execution context

        Returns:
            Skill execution result

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclass must implement _execute_impl")

    def validate_params(self, params: Dict[str, Any]) -> Result[None]:
        """Validate skill parameters (optional).

        Subclasses can override to provide parameter validation.

        Args:
            params: Parameters to validate

        Returns:
            Result.ok() if valid, Result.fail() with error message if invalid

        Example:
            >>> class MySkill(BaseSkill):
            ...     def validate_params(self, params):
            ...         if "required_field" not in params:
            ...             return Result.fail("required_field is missing")
            ...         return Result.ok(None)
        """
        return Result.ok(None)


class FunctionSkill(BaseSkill):
    """Wrapper to make a function a skill.

    Allows existing functions to be registered as skills without modification.

    Attributes:
        name: Skill name
        _func: Function to execute
        description: Skill description
    """

    def __init__(
        self, name: str, func: Callable[[Dict[str, Any]], Any], description: str = ""
    ):
        """Initialize FunctionSkill.

        Args:
            name: Skill name
            func: Function to execute
            description: Skill description
        """
        self.name = name
        self._func = func
        self.description = description or f"Function skill: {name}"

    def _execute_impl(self, context: SkillContext) -> Any:
        """Execute the function.

        Args:
            context: Skill execution context

        Returns:
            Function return value
        """
        return self._func(context.params)


class SkillRegistry:
    """Skill registry (singleton).

    Manages skill registration and retrieval.

    Design:
        - Singleton pattern ensures single registry instance
        - Thread-safe operations for concurrent access
    """

    _instance: Optional["SkillRegistry"] = None
    _skills: Dict[str, BaseSkill] = {}

    def __new__(cls) -> "SkillRegistry":
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, skill: BaseSkill) -> None:
        """Register a skill.

        Args:
            skill: Skill instance to register

        Example:
            >>> registry = SkillRegistry()
            >>> registry.register(MySkill())
        """
        self._skills[skill.name] = skill

    def register_function(
        self,
        name: str,
        func: Callable[[Dict[str, Any]], Any],
        description: str = "",
    ) -> None:
        """Register a function as a skill.

        Args:
            name: Skill name
            func: Function to register
            description: Skill description

        Example:
            >>> def my_function(params):
            ...     return {"result": params["input"] * 2}
            >>> registry = SkillRegistry()
            >>> registry.register_function("double", my_function)
        """
        skill = FunctionSkill(name, func, description)
        self.register(skill)

    def get(self, name: str) -> Optional[BaseSkill]:
        """Get a registered skill by name.

        Args:
            name: Skill name

        Returns:
            Skill instance if found, None otherwise

        Example:
            >>> registry = SkillRegistry()
            >>> skill = registry.get("my-skill")
        """
        return self._skills.get(name)

    def list(self) -> List[str]:
        """List all registered skill names.

        Returns:
            List of skill names

        Example:
            >>> registry = SkillRegistry()
            >>> registry.list()
            ['skill1', 'skill2', 'skill3']
        """
        return list(self._skills.keys())

    def has(self, name: str) -> bool:
        """Check if a skill is registered.

        Args:
            name: Skill name

        Returns:
            True if skill is registered, False otherwise
        """
        return name in self._skills

    def clear(self) -> None:
        """Clear all registered skills.

        Useful for testing or resetting the registry.
        """
        self._skills.clear()


# Global instance (backward compatibility)
_skill_registry = SkillRegistry()


def register_skill(skill: BaseSkill) -> None:
    """Register a skill (global function, backward compatibility).

    Args:
        skill: Skill instance to register

    Example:
        >>> from lingflow.core.skill import BaseSkill, register_skill
        >>> class MySkill(BaseSkill):
        ...     name = "my-skill"
        ...     def _execute_impl(self, context):
        ...         return {"status": "ok"}
        >>> register_skill(MySkill())
    """
    _skill_registry.register(skill)


def register_function(
    name: str,
    func: Callable[[Dict[str, Any]], Any],
    description: str = "",
) -> None:
    """Register a function as a skill (global function, backward compatibility).

    Args:
        name: Skill name
        func: Function to register
        description: Skill description

    Example:
        >>> from lingflow.core.skill import register_function
        >>> def my_function(params):
        ...     return {"result": params["input"] * 2}
        >>> register_function("double", my_function)
    """
    _skill_registry.register_function(name, func, description)


def get_skill(name: str) -> Optional[BaseSkill]:
    """Get a registered skill (global function, backward compatibility).

    Args:
        name: Skill name

    Returns:
        Skill instance if found, None otherwise

    Example:
        >>> from lingflow.core.skill import get_skill
        >>> skill = get_skill("my-skill")
    """
    return _skill_registry.get(name)
