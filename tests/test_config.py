"""Unit tests for lingflow.core.config module."""

import warnings

import pytest

from lingflow.core.config import LingFlowConfig


@pytest.mark.filterwarnings("ignore:LingFlowConfig is deprecated:DeprecationWarning")
class TestLingFlowConfig:
    """Test LingFlowConfig configuration class."""

    def test_default_config(self):
        """Test creating config with default values."""
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

    def test_custom_config(self):
        """Test creating config with custom values."""
        config = LingFlowConfig(
            max_parallel=4,
            skill_timeout=60.0,
            agent_timeout=180.0,
        )
        assert config.max_parallel == 4
        assert config.skill_timeout == 60.0
        assert config.agent_timeout == 180.0
        # Default values for other fields
        assert config.max_iterations == 100
        assert config.compression_enabled is True

    def test_config_validate_success(self):
        """Test validation with valid config."""
        config = LingFlowConfig(max_parallel=4, skill_timeout=60.0)
        # Should not raise
        config.validate()

    def test_config_validate_max_parallel_too_low(self):
        """Test validation fails when max_parallel < 1."""
        config = LingFlowConfig(max_parallel=0)
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "max_parallel must be >= 1" in str(exc_info.value)

    def test_config_validate_max_iterations_too_low(self):
        """Test validation fails when max_iterations < 1."""
        config = LingFlowConfig(max_iterations=0)
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "max_iterations must be >= 1" in str(exc_info.value)

    def test_config_validate_workflow_timeout_negative(self):
        """Test validation fails when workflow_timeout < 0."""
        config = LingFlowConfig(workflow_timeout=-1.0)
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "workflow_timeout must be >= 0" in str(exc_info.value)

    def test_config_validate_skill_timeout_negative(self):
        """Test validation fails when skill_timeout < 0."""
        config = LingFlowConfig(skill_timeout=-1.0)
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "skill_timeout must be >= 0" in str(exc_info.value)

    def test_config_validate_agent_timeout_negative(self):
        """Test validation fails when agent_timeout < 0."""
        config = LingFlowConfig(agent_timeout=-1.0)
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "agent_timeout must be >= 0" in str(exc_info.value)

    def test_config_validate_agent_context_limit_too_low(self):
        """Test validation fails when agent_context_limit < 1000."""
        config = LingFlowConfig(agent_context_limit=999)
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "agent_context_limit must be >= 1000" in str(exc_info.value)

    def test_config_validate_compression_target_too_low(self):
        """Test validation fails when compression_target_tokens < 1000."""
        config = LingFlowConfig(compression_target_tokens=999)
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "compression_target_tokens must be >= 1000" in str(exc_info.value)

    def test_config_validate_invalid_log_level(self):
        """Test validation fails with invalid log level."""
        config = LingFlowConfig(log_level="INVALID")
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL" in str(exc_info.value)

    def test_config_validate_valid_log_levels(self):
        """Test validation passes with all valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LingFlowConfig(log_level=level)
            config.validate()  # Should not raise

    def test_from_dict_basic(self):
        """Test creating config from dictionary."""
        config_dict = {"max_parallel": 4, "skill_timeout": 60.0}
        config = LingFlowConfig.from_dict(config_dict)
        assert config.max_parallel == 4
        assert config.skill_timeout == 60.0
        # Default values for other fields
        assert config.max_iterations == 100
        assert config.compression_enabled is True

    def test_from_dict_filters_unknown_keys(self):
        """Test that from_dict filters out unknown keys."""
        config_dict = {
            "max_parallel": 4,
            "unknown_key": "should_be_ignored",
            "another_unknown": 123,
        }
        config = LingFlowConfig.from_dict(config_dict)
        assert config.max_parallel == 4
        # Unknown keys should be ignored
        assert not hasattr(config, "unknown_key")
        assert not hasattr(config, "another_unknown")

    def test_from_dict_empty(self):
        """Test creating config from empty dictionary (all defaults)."""
        config = LingFlowConfig.from_dict({})
        assert config.max_parallel == 2
        assert config.skill_timeout == 30.0
        assert config.compression_enabled is True

    def test_to_dict_basic(self):
        """Test converting config to dictionary."""
        config = LingFlowConfig(max_parallel=4, skill_timeout=60.0)
        config_dict = config.to_dict()
        assert config_dict["max_parallel"] == 4
        assert config_dict["skill_timeout"] == 60.0
        assert config_dict["max_iterations"] == 100  # Default value
        assert config_dict["compression_enabled"] is True

    def test_to_dict_roundtrip(self):
        """Test that to_dict -> from_dict preserves values."""
        original = LingFlowConfig(
            max_parallel=4,
            skill_timeout=60.0,
            agent_timeout=180.0,
            log_level="DEBUG",
        )
        config_dict = original.to_dict()
        restored = LingFlowConfig.from_dict(config_dict)
        assert restored.max_parallel == original.max_parallel
        assert restored.skill_timeout == original.skill_timeout
        assert restored.agent_timeout == original.agent_timeout
        assert restored.log_level == original.log_level

    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all fields."""
        config = LingFlowConfig()
        config_dict = config.to_dict()
        expected_keys = {
            "max_parallel",
            "max_iterations",
            "workflow_timeout",
            "skills_path",
            "skill_timeout",
            "skill_cache_enabled",
            "agent_timeout",
            "agent_context_limit",
            "compression_enabled",
            "compression_target_tokens",
            "log_level",
        }
        assert set(config_dict.keys()) == expected_keys

    def test_config_immutability_not_enforced(self):
        """Test that config fields can be modified (dataclass default behavior)."""
        config = LingFlowConfig(max_parallel=2)
        config.max_parallel = 4  # This is allowed (not frozen dataclass)
        assert config.max_parallel == 4

    def test_compression_can_be_disabled(self):
        """Test disabling compression."""
        config = LingFlowConfig(compression_enabled=False)
        assert config.compression_enabled is False
        config.validate()  # Should not raise

    def test_skill_cache_can_be_enabled(self):
        """Test enabling skill cache."""
        config = LingFlowConfig(skill_cache_enabled=True)
        assert config.skill_cache_enabled is True
        config.validate()  # Should not raise

    def test_skills_path_custom(self):
        """Test custom skills path."""
        config = LingFlowConfig(skills_path="/custom/path/to/skills")
        assert config.skills_path == "/custom/path/to/skills"
        config.validate()  # Should not raise

    def test_zero_timeouts_valid(self):
        """Test that zero timeouts are valid (except context limit)."""
        config = LingFlowConfig(workflow_timeout=0.0, skill_timeout=0.0, agent_timeout=0.0)
        config.validate()  # Should not raise

    def test_deprecation_warning(self):
        """Test that LingFlowConfig emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            LingFlowConfig()
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "ConfigManager" in str(w[0].message)
