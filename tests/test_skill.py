"""Unit tests for lingflow.core.skill module."""

import pytest

from lingflow.core.skill import (
    BaseSkill,
    FunctionSkill,
    SkillContext,
    SkillRegistry,
    get_skill,
    register_function,
    register_skill,
)
from lingflow.core.types import Result


class TestSkillContext:
    """Test SkillContext."""

    def test_basic_context(self):
        """Test creating basic context."""
        context = SkillContext(
            skill_name="test-skill",
            params={"key": "value"},
            working_dir="/test",
        )
        assert context.skill_name == "test-skill"
        assert context.params == {"key": "value"}
        assert context.working_dir == "/test"
        assert context.metadata == {}

    def test_context_with_metadata(self):
        """Test creating context with metadata."""
        metadata = {"user": "test", "session": "123"}
        context = SkillContext(
            skill_name="test-skill",
            params={},
            metadata=metadata,
        )
        assert context.metadata == metadata

    def test_context_default_working_dir(self):
        """Test context with default working directory."""
        context = SkillContext(skill_name="test", params={})
        assert context.working_dir == "."


class TestBaseSkill:
    """Test BaseSkill."""

    def test_skill_metadata_defaults(self):
        """Test skill has default metadata."""

        class TestSkill(BaseSkill):
            def _execute_impl(self, context):
                return {"test": "data"}

        skill = TestSkill()
        assert skill.name == "base-skill"
        assert skill.description == "Base skill"
        assert skill.version == "1.0.0"

    def test_skill_metadata_override(self):
        """Test skill can override metadata."""

        class TestSkill(BaseSkill):
            name = "test-skill"
            description = "Test description"
            version = "2.0.0"

            def _execute_impl(self, context):
                return {"test": "data"}

        skill = TestSkill()
        assert skill.name == "test-skill"
        assert skill.description == "Test description"
        assert skill.version == "2.0.0"

    def test_execute_success(self):
        """Test successful skill execution."""

        class EchoSkill(BaseSkill):
            name = "echo"

            def _execute_impl(self, context):
                return {"echo": context.params.get("message", "")}

        skill = EchoSkill()
        result = skill.execute({"message": "hello"})

        assert result.success
        assert result.data == {"echo": "hello"}

    def test_execute_error_handling(self):
        """Test error handling in skill execution."""

        class FailingSkill(BaseSkill):
            name = "failing"

            def _execute_impl(self, context):
                raise ValueError("Test error")

        skill = FailingSkill()
        result = skill.execute({})

        assert not result.success
        assert "Test error" in result.error

    def test_validate_params_default(self):
        """Test default parameter validation passes."""

        class TestSkill(BaseSkill):
            name = "test"

            def _execute_impl(self, context):
                return {"test": "data"}

        skill = TestSkill()
        result = skill.validate_params({})
        assert result.success

    def test_validate_params_custom(self):
        """Test custom parameter validation."""

        class ValidatedSkill(BaseSkill):
            name = "validated"

            def validate_params(self, params):
                if "required" not in params:
                    return Result.fail("required field missing")
                return Result.ok(None)

            def _execute_impl(self, context):
                return {"test": "data"}

        skill = ValidatedSkill()

        # Missing required field
        result = skill.execute({})
        assert not result.success
        assert "required field missing" in result.error

        # With required field
        result = skill.execute({"required": "value"})
        assert result.success


class TestFunctionSkill:
    """Test FunctionSkill."""

    def test_function_skill_basic(self):
        """Test creating and executing function skill."""

        def my_func(params):
            return {"result": params.get("input", 0) * 2}

        skill = FunctionSkill("double", my_func, description="Doubles input")
        result = skill.execute({"input": 5})

        assert result.success
        assert result.data == {"result": 10}
        assert skill.description == "Doubles input"

    def test_function_skill_error_handling(self):
        """Test error handling in function skill."""

        def failing_func(params):
            raise ValueError("Function error")

        skill = FunctionSkill("failing", failing_func)
        result = skill.execute({})

        assert not result.success
        assert "Function error" in result.error

    def test_function_skill_default_description(self):
        """Test default description generation."""

        def my_func(params):
            return {"result": "ok"}

        skill = FunctionSkill("my-func", my_func)
        assert skill.description == "Function skill: my-func"


class TestSkillRegistry:
    """Test SkillRegistry."""

    def test_registry_singleton(self):
        """Test registry is singleton."""
        registry1 = SkillRegistry()
        registry2 = SkillRegistry()
        assert registry1 is registry2

    def test_register_and_get_skill(self):
        """Test registering and retrieving a skill."""

        class TestSkill(BaseSkill):
            name = "test-skill"

            def _execute_impl(self, context):
                return {"test": "data"}

        registry = SkillRegistry()
        skill = TestSkill()
        registry.register(skill)

        retrieved = registry.get("test-skill")
        assert retrieved is skill

    def test_register_function(self):
        """Test registering a function as skill."""

        def my_func(params):
            return {"result": params["input"] * 2}

        registry = SkillRegistry()
        registry.register_function("double", my_func)

        skill = registry.get("double")
        assert isinstance(skill, FunctionSkill)

        result = skill.execute({"input": 3})
        assert result.success
        assert result.data == {"result": 6}

    def test_get_nonexistent_skill(self):
        """Test getting non-existent skill returns None."""
        registry = SkillRegistry()
        skill = registry.get("nonexistent")
        assert skill is None

    def test_list_skills(self):
        """Test listing registered skills."""
        registry = SkillRegistry()
        registry.clear()

        class Skill1(BaseSkill):
            name = "skill1"

            def _execute_impl(self, context):
                return {}

        class Skill2(BaseSkill):
            name = "skill2"

            def _execute_impl(self, context):
                return {}

        registry.register(Skill1())
        registry.register(Skill2())

        skills = registry.list()
        assert set(skills) == {"skill1", "skill2"}

    def test_has_skill(self):
        """Test checking if skill is registered."""
        registry = SkillRegistry()
        registry.clear()

        class TestSkill(BaseSkill):
            name = "test"

            def _execute_impl(self, context):
                return {}

        assert not registry.has("test")
        registry.register(TestSkill())
        assert registry.has("test")

    def test_clear_skills(self):
        """Test clearing all skills."""
        registry = SkillRegistry()

        class TestSkill(BaseSkill):
            name = "test"

            def _execute_impl(self, context):
                return {}

        registry.register(TestSkill())
        assert registry.has("test")

        registry.clear()
        assert not registry.has("test")


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_global_register_skill(self):
        """Test global register_skill function."""
        # Clear global registry
        SkillRegistry().clear()

        class GlobalTestSkill(BaseSkill):
            name = "global-test"

            def _execute_impl(self, context):
                return {"global": "skill"}

        register_skill(GlobalTestSkill())

        skill = get_skill("global-test")
        assert skill is not None
        assert isinstance(skill, GlobalTestSkill)

        # Cleanup
        SkillRegistry().clear()

    def test_global_register_function(self):
        """Test global register_function function."""
        # Clear global registry
        SkillRegistry().clear()

        def global_func(params):
            return {"result": params["value"]}

        register_function("global-double", global_func)

        skill = get_skill("global-double")
        assert skill is not None
        assert isinstance(skill, FunctionSkill)

        result = skill.execute({"value": 10})
        assert result.success
        assert result.data == {"result": 10}

        # Cleanup
        SkillRegistry().clear()

    def test_global_get_skill(self):
        """Test global get_skill function."""
        # Clear global registry
        SkillRegistry().clear()

        class GlobalTestSkill(BaseSkill):
            name = "global-test"

            def _execute_impl(self, context):
                return {}

        register_skill(GlobalTestSkill())

        skill = get_skill("global-test")
        assert skill is not None

        skill = get_skill("nonexistent")
        assert skill is None

        # Cleanup
        SkillRegistry().clear()
