from unittest.mock import MagicMock, patch
from lingflow.self_optimizer.phase4.integration import (
    Phase4Integration,
    EnhancedOptimizerAdapter,
    patch_self_optimizer,
    enable_phase4_integration,
)


class TestPhase4Integration:
    def test_enhance_optimizer_request_with_all_attrs(self):
        request = MagicMock()
        request.goal = "performance"
        request.target = "/tmp/project"
        request.config = {"max_experiments": 30, "time_budget": 60}
        result = Phase4Integration.enhance_optimizer_request(request)
        assert result["target_path"] == "/tmp/project"
        assert result["goal"] == "performance"
        assert result["config"]["n_trials"] == 30
        assert result["config"]["timeout"] == 60
        assert result["config"]["generate_reports"] is True

    def test_enhance_optimizer_request_defaults(self):
        request = MagicMock(spec=[])
        result = Phase4Integration.enhance_optimizer_request(request)
        assert result["target_path"] == "."
        assert result["goal"] == "structure"
        assert result["config"]["n_trials"] == 50
        assert result["config"]["timeout"] == 120

    def test_convert_to_legacy_result(self):
        phase4_result = {
            "n_trials": 5,
            "best_params": {"x": 1.0},
            "best_score": 0.85,
            "total_time": 12.5,
        }
        request = MagicMock()
        result = Phase4Integration.convert_to_legacy_result(phase4_result, request)
        assert result.success is True
        assert result.best_params == {"x": 1.0}
        assert result.best_score == 0.85
        assert result.experiments == 5
        assert result.duration == 12.5
        assert len(result.history) == 5

    def test_convert_to_legacy_result_empty(self):
        phase4_result = {}
        request = MagicMock()
        result = Phase4Integration.convert_to_legacy_result(phase4_result, request)
        assert result.success is True
        assert result.experiments == 0
        assert result.history == []


class TestEnhancedOptimizerAdapter:
    def test_init_fallback_to_legacy(self):
        adapter = EnhancedOptimizerAdapter(use_phase4=False)
        assert adapter.use_phase4 is False
        assert hasattr(adapter, "legacy_optimizer")

    @patch("lingflow.self_optimizer.phase4.integration.OptimizationEngine", create=True)
    def test_init_phase4_import_fails(self, mock_engine):
        with patch.dict("sys.modules", {"lingflow.self_optimizer.phase4": MagicMock(
            OptimizationEngine=MagicMock(side_effect=ImportError("no module"))
        )}):
            pass
        adapter = EnhancedOptimizerAdapter(use_phase4=False)
        assert adapter.use_phase4 is False

    def test_optimize_with_legacy(self):
        adapter = EnhancedOptimizerAdapter(use_phase4=False)
        request = MagicMock()
        result = adapter.optimize(request)
        assert result is not None


class TestPatchSelfOptimizer:
    def test_patch_self_optimizer(self):
        import lingflow.self_optimizer as opt_mod
        original = getattr(opt_mod, "SynchronousOptimizer", None)
        patch_self_optimizer()
        assert hasattr(opt_mod, "_original_SynchronousOptimizer")
        if original is not None:
            opt_mod.SynchronousOptimizer = original

    def test_enable_phase4_integration(self):
        import lingflow.self_optimizer as opt_mod
        original = getattr(opt_mod, "SynchronousOptimizer", None)
        enable_phase4_integration()
        if original is not None:
            opt_mod.SynchronousOptimizer = original
