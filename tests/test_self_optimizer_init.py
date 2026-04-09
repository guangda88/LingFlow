import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from lingflow.self_optimizer import (
    DEFAULT_CONFIG,
    ConfigManager,
    OptimizationAdvisor,
    OptimizationConfig,
    OptimizationRequest,
    OptimizationResult,
    OptimizationTrigger,
    ProcessIsolatedOptimizer,
    SimplicityEvaluator,
    StructureEvaluator,
    SynchronousOptimizer,
    TriggerInfo,
    check_and_optimize,
    quick_optimize,
)


class TestQuickOptimize:
    def test_sync_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "sample.py"), "w") as f:
                f.write("x = 1\n")
            result = quick_optimize(target=tmp, goal="structure")
            assert result is not None
            assert result.success is True

    def test_sync_performance(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "sample.py"), "w") as f:
                f.write("x = 1\n")
            result = quick_optimize(target=tmp, goal="performance")
            assert result is not None
            assert result.success is True

    def test_sync_simplicity(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "sample.py"), "w") as f:
                f.write("x = 1\n")
            result = quick_optimize(target=tmp, goal="simplicity")
            assert result is not None
            assert result.success is True

    def test_async_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = quick_optimize(target=tmp, goal="structure", async_mode=True)
            assert result is None

    def test_invalid_goal(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = quick_optimize(target=tmp, goal="unknown")
            assert result is not None
            assert result.success is True


class TestCheckAndOptimize:
    def test_no_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            triggered, result = check_and_optimize(
                context={"review_score": 90},
                target=tmp,
                goal="structure",
            )
            assert triggered is False
            assert result is None

    def test_with_trigger_auto(self):
        cfg = OptimizationConfig()
        cfg.config["hooks"]["require_confirmation"] = False
        from lingflow.self_optimizer.config import get_global_config, set_global_config

        old = get_global_config()
        set_global_config(cfg)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with open(os.path.join(tmp, "sample.py"), "w") as f:
                    f.write("x = 1\n")
                triggered, result = check_and_optimize(
                    context={"review_score": 30},
                    target=tmp,
                    goal="structure",
                )
                assert triggered is True
                assert result is not None
        finally:
            set_global_config(old)

    def test_with_trigger_requires_confirmation(self):
        cfg = OptimizationConfig()
        cfg.config["hooks"]["require_confirmation"] = True
        from lingflow.self_optimizer.config import get_global_config, set_global_config

        old = get_global_config()
        set_global_config(cfg)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with patch("builtins.input", return_value="n"):
                    triggered, result = check_and_optimize(
                        context={"review_score": 10},
                        target=tmp,
                        goal="structure",
                    )
                assert triggered is False
                assert result is None
        finally:
            set_global_config(old)


class TestImports:
    def test_config_manager(self):
        assert ConfigManager is OptimizationConfig

    def test_default_config(self):
        assert isinstance(DEFAULT_CONFIG, dict)
        assert "triggers" in DEFAULT_CONFIG

    def test_trigger_classes(self):
        assert OptimizationTrigger is not None
        assert TriggerInfo is not None

    def test_optimizer_classes(self):
        assert ProcessIsolatedOptimizer is not None
        assert SynchronousOptimizer is not None
        assert OptimizationRequest is not None
        assert OptimizationResult is not None

    def test_evaluator_classes(self):
        assert StructureEvaluator is not None
        assert SimplicityEvaluator is not None
        assert OptimizationAdvisor is not None
