import tempfile
from pathlib import Path

import pytest

from lingflow.self_optimizer.config import (
    DEFAULT_CONFIG,
    OptimizationConfig,
    get_global_config,
    set_global_config,
)


class TestDefaultConfig:
    def test_has_triggers(self):
        assert "triggers" in DEFAULT_CONFIG

    def test_has_optimization(self):
        assert "optimization" in DEFAULT_CONFIG

    def test_has_hooks(self):
        assert "hooks" in DEFAULT_CONFIG

    def test_has_async(self):
        assert "async" in DEFAULT_CONFIG

    def test_has_report(self):
        assert "report" in DEFAULT_CONFIG


class TestOptimizationConfigInit:
    def test_default(self):
        cfg = OptimizationConfig()
        assert cfg.config is not None
        assert cfg.config_path is None

    def test_with_nonexistent_path(self):
        cfg = OptimizationConfig("/nonexistent/path.yaml")
        assert "triggers" in cfg.config

    def test_with_valid_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.yaml"
            config_file.write_text("hooks:\n  enable_on_review: false\n")
            cfg = OptimizationConfig(str(config_file))
            assert cfg.config["hooks"]["enable_on_review"] is False


class TestGetSet:
    def test_get_nested(self):
        cfg = OptimizationConfig()
        val = cfg.get("triggers.quality.review_score_below")
        assert val == 70

    def test_get_top_level(self):
        cfg = OptimizationConfig()
        val = cfg.get("triggers")
        assert isinstance(val, dict)

    def test_get_missing_key(self):
        cfg = OptimizationConfig()
        val = cfg.get("nonexistent.key.path", "default_val")
        assert val == "default_val"

    def test_get_default_none(self):
        cfg = OptimizationConfig()
        val = cfg.get("nonexistent")
        assert val is None

    def test_set_nested(self):
        cfg = OptimizationConfig()
        cfg.set("triggers.quality.review_score_below", 50)
        assert cfg.get("triggers.quality.review_score_below") == 50

    def test_set_new_key(self):
        cfg = OptimizationConfig()
        cfg.set("custom.section.key", "value")
        assert cfg.get("custom.section.key") == "value"


class TestSave:
    def test_save_to_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = OptimizationConfig()
            out = Path(tmpdir) / "out.yaml"
            cfg.save(str(out))
            assert out.exists()
            content = out.read_text()
            assert "triggers" in content

    def test_save_to_init_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "save.yaml"
            cfg = OptimizationConfig(str(out))
            cfg.save()
            assert out.exists()

    def test_save_no_path_raises(self):
        cfg = OptimizationConfig()
        with pytest.raises(ValueError):
            cfg.save()


class TestGetTriggerConfig:
    def test_existing_type(self):
        cfg = OptimizationConfig()
        quality = cfg.get_trigger_config("quality")
        assert "review_score_below" in quality

    def test_missing_type(self):
        cfg = OptimizationConfig()
        result = cfg.get_trigger_config("nonexistent")
        assert result == {}


class TestGetOptimizationConfig:
    def test_returns_dict(self):
        cfg = OptimizationConfig()
        opt = cfg.get_optimization_config()
        assert "max_experiments" in opt


class TestGetHooksConfig:
    def test_returns_dict(self):
        cfg = OptimizationConfig()
        hooks = cfg.get_hooks_config()
        assert "enable_on_review" in hooks


class TestLoadConfig:
    def test_merge_nested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test.yaml"
            config_file.write_text("triggers:\n  quality:\n    review_score_below: 50\n")
            cfg = OptimizationConfig(str(config_file))
            assert cfg.config["triggers"]["quality"]["review_score_below"] == 50
            assert "structure" in cfg.config["triggers"]


class TestGlobalConfig:
    def test_get_global_config(self):
        cfg = get_global_config()
        assert isinstance(cfg, OptimizationConfig)

    def test_set_global_config(self):
        custom = OptimizationConfig()
        custom.set("custom_key", "custom_value")
        old = get_global_config()
        set_global_config(custom)
        assert get_global_config() is custom
        set_global_config(old)

    def test_global_config_singleton(self):
        cfg1 = get_global_config()
        cfg2 = get_global_config()
        assert cfg1 is cfg2
