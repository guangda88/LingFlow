"""Exception hierarchy tests"""

import pytest

from lingflow.common.exceptions import (
    AgentError,
    AgentExecutionError,
    AgentNotFoundError,
    CompressionError,
    ConfigurationError,
    lingflowError,
    SkillError,
    SkillExecutionError,
    SkillLoadError,
    SkillNotFoundError,
    ValidationError,
    WorkflowError,
    WorkflowExecutionError,
    WorkflowValidationError,
)


class TestlingflowError:
    def test_basic(self):
        e = lingflowError("test error")
        assert str(e) == "[LF_ERROR] test error"
        assert e.code == "LF_ERROR"
        assert e.details == {}

    def test_custom_code(self):
        e = lingflowError("msg", code="CUSTOM_001")
        assert e.code == "CUSTOM_001"
        assert "[CUSTOM_001]" in str(e)

    def test_with_details(self):
        e = lingflowError("msg", details={"key": "val"})
        assert e.details == {"key": "val"}

    def test_is_exception(self):
        with pytest.raises(lingflowError):
            raise lingflowError("boom")


class TestSkillErrors:
    def test_skill_not_found(self):
        e = SkillNotFoundError("skill-x")
        assert isinstance(e, SkillError)
        assert isinstance(e, lingflowError)

    def test_skill_load(self):
        e = SkillLoadError("load failed")
        assert isinstance(e, SkillError)

    def test_skill_execution(self):
        e = SkillExecutionError("exec failed")
        assert isinstance(e, SkillError)


class TestWorkflowErrors:
    def test_validation(self):
        e = WorkflowValidationError("bad yaml")
        assert isinstance(e, WorkflowError)

    def test_execution(self):
        e = WorkflowExecutionError("timeout")
        assert isinstance(e, WorkflowError)


class TestAgentErrors:
    def test_not_found(self):
        e = AgentNotFoundError("agent-x")
        assert isinstance(e, AgentError)

    def test_execution(self):
        e = AgentExecutionError("crash")
        assert isinstance(e, AgentError)


class TestOtherErrors:
    def test_compression(self):
        assert isinstance(CompressionError("c"), lingflowError)

    def test_configuration(self):
        assert isinstance(ConfigurationError("c"), lingflowError)

    def test_validation(self):
        assert isinstance(ValidationError("c"), lingflowError)
