"""Tests for lingflow.core.config module"""

import pytest

from lingflow.core.config import LingFlowConfig


class TestLingFlowConfig:
    """Test LingFlowConfig dataclass"""

    def test_default_values(self):
        """Test default configuration values"""
        config = LingFlowConfig()
        assert config.max_parallel == 2
        assert config.max_iterations == 100
        assert config.workflow_timeout == 600.0
        assert config.skills_path == "skills"
        assert config.skill_timeout == 30.0
        assert config.skill_cache_enabled is False
        assert config.agent_timeout == 300.0
        assert config.agent_context_limit == 8000
        assert config.compression_enabled is True
        assert config.compression_target_tokens == 4000
        assert config.log_level == "INFO"

    def test_custom_values(self):
        """Test custom configuration values"""
        config = LingFlowConfig(
            max_parallel=4,
            max_iterations=200,
            workflow_timeout=1200.0,
            skills_path="custom_skills",
            skill_timeout=60.0,
            skill_cache_enabled=True,
            agent_timeout=600.0,
            agent_context_limit=16000,
            compression_enabled=False,
            compression_target_tokens=8000,
            log_level="DEBUG",
        )
        assert config.max_parallel == 4
        assert config.max_iterations == 200
        assert config.workflow_timeout == 1200.0
        assert config.skills_path == "custom_skills"
        assert config.skill_timeout == 60.0
        assert config.skill_cache_enabled is True
        assert config.agent_timeout == 600.0
        assert config.agent_context_limit == 16000
        assert config.compression_enabled is False
        assert config.compression_target_tokens == 8000
        assert config.log_level == "DEBUG"

    def test_validate_success(self):
        """Test validation with valid values"""
        config = LingFlowConfig()
        config.validate()  # Should not raise

    def test_validate_max_parallel_too_low(self):
        """Test validation fails when max_parallel < 1"""
        config = LingFlowConfig(max_parallel=0)
        with pytest.raises(ValueError, match="max_parallel must be >= 1"):
            config.validate()

    def test_validate_max_iterations_too_low(self):
        """Test validation fails when max_iterations < 1"""
        config = LingFlowConfig(max_iterations=0)
        with pytest.raises(ValueError, match="max_iterations must be >= 1"):
            config.validate()

    def test_validate_negative_workflow_timeout(self):
        """Test validation fails when workflow_timeout < 0"""
        config = LingFlowConfig(workflow_timeout=-1.0)
        with pytest.raises(ValueError, match="workflow_timeout must be >= 0"):
            config.validate()

    def test_validate_negative_skill_timeout(self):
        """Test validation fails when skill_timeout < 0"""
        config = LingFlowConfig(skill_timeout=-1.0)
        with pytest.raises(ValueError, match="skill_timeout must be >= 0"):
            config.validate()

    def test_validate_negative_agent_timeout(self):
        """Test validation fails when agent_timeout < 0"""
        config = LingFlowConfig(agent_timeout=-1.0)
        with pytest.raises(ValueError, match="agent_timeout must be >= 0"):
            config.validate()

    def test_validate_agent_context_limit_too_low(self):
        """Test validation fails when agent_context_limit < 1000"""
        config = LingFlowConfig(agent_context_limit=500)
        with pytest.raises(ValueError, match="agent_context_limit must be >= 1000"):
            config.validate()

    def test_validate_compression_target_tokens_too_low(self):
        """Test validation fails when compression_target_tokens < 1000"""
        config = LingFlowConfig(compression_target_tokens=500)
        with pytest.raises(ValueError, match="compression_target_tokens must be >= 1000"):
            config.validate()

    def test_validate_invalid_log_level(self):
        """Test validation fails with invalid log level"""
        config = LingFlowConfig(log_level="INVALID")
        with pytest.raises(ValueError, match="log_level must be one of"):
            config.validate()

    def test_from_dict_valid(self):
        """Test creating config from dictionary"""
        config_dict = {"max_parallel": 8, "skill_timeout": 45.0, "log_level": "DEBUG"}
        config = LingFlowConfig.from_dict(config_dict)
        assert config.max_parallel == 8
        assert config.skill_timeout == 45.0
        assert config.log_level == "DEBUG"

    def test_from_dict_filters_unknown_keys(self):
        """Test that from_dict filters unknown keys"""
        config_dict = {"max_parallel": 4, "unknown_key": "value", "another_unknown": 123}
        config = LingFlowConfig.from_dict(config_dict)
        assert config.max_parallel == 4
        assert not hasattr(config, "unknown_key")

    def test_from_dict_empty(self):
        """Test creating config from empty dictionary"""
        config = LingFlowConfig.from_dict({})
        # Should use all defaults
        assert config.max_parallel == 2
        assert config.max_iterations == 100

    def test_to_dict(self):
        """Test converting config to dictionary"""
        config = LingFlowConfig(max_parallel=4, skill_timeout=60.0)
        config_dict = config.to_dict()
        assert config_dict["max_parallel"] == 4
        assert config_dict["skill_timeout"] == 60.0
        assert config_dict["max_iterations"] == 100  # default

    def test_deprecation_warning(self):
        """Test that LingFlowConfig emits deprecation warning"""
        with pytest.warns(DeprecationWarning, match="LingFlowConfig is deprecated"):
            LingFlowConfig()
