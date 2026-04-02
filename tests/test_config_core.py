"""LingFlowConfig tests"""

import warnings
import pytest
from lingflow.core.config import LingFlowConfig


class TestLingFlowConfigDefaults:
    def test_defaults(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cfg = LingFlowConfig()
        assert cfg.max_parallel == 2
        assert cfg.max_iterations == 100
        assert cfg.workflow_timeout == 600.0
        assert cfg.skills_path == "skills"
        assert cfg.skill_timeout == 30.0
        assert cfg.skill_cache_enabled is False
        assert cfg.agent_timeout == 300.0
        assert cfg.agent_context_limit == 8000
        assert cfg.compression_enabled is True
        assert cfg.compression_target_tokens == 4000
        assert cfg.log_level == "INFO"

    def test_deprecation_warning(self):
        with pytest.warns(DeprecationWarning, match="deprecated"):
            LingFlowConfig()


class TestLingFlowConfigValidation:
    def _make(self, **kw):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return LingFlowConfig(**kw)

    def test_valid(self):
        cfg = self._make()
        cfg.validate()

    def test_invalid_max_parallel(self):
        cfg = self._make(max_parallel=0)
        with pytest.raises(ValueError, match="max_parallel"):
            cfg.validate()

    def test_invalid_max_iterations(self):
        cfg = self._make(max_iterations=0)
        with pytest.raises(ValueError, match="max_iterations"):
            cfg.validate()

    def test_negative_workflow_timeout(self):
        cfg = self._make(workflow_timeout=-1)
        with pytest.raises(ValueError, match="workflow_timeout"):
            cfg.validate()

    def test_negative_skill_timeout(self):
        cfg = self._make(skill_timeout=-1)
        with pytest.raises(ValueError, match="skill_timeout"):
            cfg.validate()

    def test_negative_agent_timeout(self):
        cfg = self._make(agent_timeout=-1)
        with pytest.raises(ValueError, match="agent_timeout"):
            cfg.validate()

    def test_low_agent_context_limit(self):
        cfg = self._make(agent_context_limit=500)
        with pytest.raises(ValueError, match="agent_context_limit"):
            cfg.validate()

    def test_low_compression_target(self):
        cfg = self._make(compression_target_tokens=500)
        with pytest.raises(ValueError, match="compression_target_tokens"):
            cfg.validate()

    def test_invalid_log_level(self):
        cfg = self._make(log_level="VERBOSE")
        with pytest.raises(ValueError, match="log_level"):
            cfg.validate()

    def test_all_valid_log_levels(self):
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            cfg = self._make(log_level=level)
            cfg.validate()


class TestLingFlowConfigSerialization:
    def _make(self, **kw):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return LingFlowConfig(**kw)

    def test_to_dict(self):
        cfg = self._make(max_parallel=4)
        d = cfg.to_dict()
        assert d["max_parallel"] == 4
        assert "skills_path" in d

    def test_from_dict(self):
        d = {"max_parallel": 8, "skill_timeout": 60.0}
        cfg = LingFlowConfig.from_dict(d)
        assert cfg.max_parallel == 8
        assert cfg.skill_timeout == 60.0

    def test_from_dict_ignores_unknown(self):
        d = {"max_parallel": 4, "unknown_key": "ignored"}
        cfg = LingFlowConfig.from_dict(d)
        assert cfg.max_parallel == 4

    def test_roundtrip(self):
        cfg = self._make(max_parallel=4, log_level="DEBUG")
        d = cfg.to_dict()
        cfg2 = LingFlowConfig.from_dict(d)
        assert cfg2.max_parallel == 4
        assert cfg2.log_level == "DEBUG"
