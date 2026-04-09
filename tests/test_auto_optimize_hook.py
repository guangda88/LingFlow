from unittest.mock import MagicMock, patch

import pytest

from lingflow.hooks.auto_optimize_hook import AutoOptimizeHook, get_global_hook
from lingflow.self_optimizer.config import OptimizationConfig
from lingflow.self_optimizer.optimizer import OptimizationResult
from lingflow.self_optimizer.trigger import TriggerInfo


class TestAutoOptimizeHookInit:
    def test_init(self):
        hook = AutoOptimizeHook()
        assert hook.trigger is not None
        assert hook.optimizer is not None
        assert hook.last_check_time is None
        assert hook.optimization_suggested is False


class TestOnCodeReviewComplete:
    def test_high_score_no_trigger(self):
        hook = AutoOptimizeHook()
        hook.on_code_review_complete({"overall_score": 90})
        assert hook.last_check_time is not None

    def test_low_score_triggers(self):
        hook = AutoOptimizeHook()
        with patch.object(hook, "trigger") as mock_trigger:
            mock_trigger.check_all_conditions.return_value = (
                True,
                TriggerInfo(
                    type="quality",
                    reason="low score",
                    priority="high",
                    current_value=30,
                    threshold=70.0,
                    metrics={},
                ),
            )
            mock_trigger.requires_confirmation.return_value = False
            with patch.object(hook, "_start_optimization") as mock_start:
                mock_start.return_value = None
                hook.on_code_review_complete({"overall_score": 30})

    def test_default_score(self):
        hook = AutoOptimizeHook()
        hook.on_code_review_complete({})
        assert hook.last_check_time is not None


class TestOnTestComplete:
    def test_good_results(self):
        hook = AutoOptimizeHook()
        hook.last_check = {"coverage": 80}
        hook.on_test_complete({"coverage": 90, "duration": 1.0, "total": 10, "failed": 0})
        assert hook.last_check_time is not None
        assert hook.last_check["coverage"] == 90

    def test_with_failures(self):
        hook = AutoOptimizeHook()
        hook.last_check = {"coverage": 80}
        with patch.object(hook, "trigger") as mock_trigger:
            mock_trigger.check_all_conditions.return_value = (False, None)
            hook.on_test_complete({"coverage": 50, "duration": 5.0, "total": 100, "failed": 30})
            assert hook.last_check_time is not None
            assert hook.last_check["coverage"] == 50

    def test_zero_total(self):
        hook = AutoOptimizeHook()
        hook.last_check = {"coverage": 80}
        hook.on_test_complete({"coverage": 80, "total": 0})
        assert hook.last_check_time is not None

    def test_coverage_drop(self):
        hook = AutoOptimizeHook()
        hook.last_check = {"coverage": 90}
        with patch.object(hook, "trigger") as mock_trigger:
            mock_trigger.check_all_conditions.return_value = (False, None)
            hook.on_test_complete({"coverage": 50, "duration": 5.0, "total": 20, "failed": 5})
            assert hook.last_check["coverage"] == 50


class TestOnGitCommit:
    def test_small_commit(self):
        hook = AutoOptimizeHook()
        hook.on_git_commit({"new_lines": 10, "deleted_lines": 5, "new_files": 1})
        assert hook.last_check_time is not None

    def test_large_commit(self):
        hook = AutoOptimizeHook()
        with patch.object(hook, "trigger") as mock_trigger:
            mock_trigger.check_all_conditions.return_value = (False, None)
            hook.on_git_commit({"new_lines": 1000, "deleted_lines": 100, "new_files": 20})
            assert hook.last_check_time is not None


class TestOnPerformanceMeasure:
    def test_good_performance(self):
        hook = AutoOptimizeHook()
        hook.on_performance_measure({"execution_time": 0.5, "memory_usage_mb": 100, "response_time_ms": 50})
        assert hook.last_check_time is not None

    def test_poor_performance(self):
        hook = AutoOptimizeHook()
        with patch.object(hook, "trigger") as mock_trigger:
            mock_trigger.check_all_conditions.return_value = (False, None)
            hook.on_performance_measure({"execution_time": 5.0, "memory_usage_mb": 600, "response_time_ms": 200})
            assert hook.last_check_time is not None


class TestDetermineGoal:
    def test_structure_types(self):
        hook = AutoOptimizeHook()
        for trigger_type in ["structure", "quality", "scale", "time", "user"]:
            info = TriggerInfo(type=trigger_type, reason="test", priority="high", current_value=0, threshold=0.0, metrics={})
            assert hook._determine_goal_from_trigger(info) == "structure"

    def test_performance_type(self):
        hook = AutoOptimizeHook()
        info = TriggerInfo(type="performance", reason="test", priority="high", current_value=0, threshold=0.0, metrics={})
        assert hook._determine_goal_from_trigger(info) == "performance"

    def test_tech_debt_type(self):
        hook = AutoOptimizeHook()
        info = TriggerInfo(type="tech_debt", reason="test", priority="high", current_value=0, threshold=0.0, metrics={})
        assert hook._determine_goal_from_trigger(info) == "simplicity"

    def test_unknown_type(self):
        hook = AutoOptimizeHook()
        info = TriggerInfo(type="unknown", reason="test", priority="high", current_value=0, threshold=0.0, metrics={})
        assert hook._determine_goal_from_trigger(info) == "structure"


class TestCheckAndPrompt:
    def test_optimizer_running_skips(self):
        hook = AutoOptimizeHook()
        hook.optimizer = MagicMock()
        hook.optimizer.is_running.return_value = True
        hook._check_and_prompt({}, {})
        assert hook.last_check_time is not None

    def test_no_trigger(self):
        hook = AutoOptimizeHook()
        with patch.object(hook, "trigger") as mock_trigger:
            mock_trigger.check_all_conditions.return_value = (False, None)
            hook._check_and_prompt({}, {})
            assert hook.last_check_time is not None

    def test_trigger_no_confirmation(self):
        hook = AutoOptimizeHook()
        with patch.object(hook, "trigger") as mock_trigger:
            mock_trigger.check_all_conditions.return_value = (
                True,
                TriggerInfo(
                    type="quality",
                    reason="test",
                    priority="high",
                    current_value=30,
                    threshold=70.0,
                    metrics={},
                ),
            )
            mock_trigger.requires_confirmation.return_value = False
            with patch.object(hook, "_start_optimization") as mock_start:
                hook._check_and_prompt({}, {})
                mock_start.assert_called_once()

    def test_trigger_with_confirmation(self, capsys):
        hook = AutoOptimizeHook()
        with patch.object(hook, "trigger") as mock_trigger:
            mock_trigger.check_all_conditions.return_value = (
                True,
                TriggerInfo(
                    type="quality",
                    reason="test",
                    priority="high",
                    current_value=30,
                    threshold=70.0,
                    metrics={},
                ),
            )
            mock_trigger.requires_confirmation.return_value = True
            with patch("builtins.input", return_value="n"):
                hook._check_and_prompt({}, {})


class TestDelegationMethods:
    def test_is_optimization_running(self):
        hook = AutoOptimizeHook()
        assert hook.is_optimization_running() is False

    def test_get_optimization_result(self):
        hook = AutoOptimizeHook()
        assert hook.get_optimization_result() is None

    def test_cancel_optimization(self):
        hook = AutoOptimizeHook()
        hook.cancel_optimization()


class TestGetGlobalHook:
    def test_singleton(self):
        import lingflow.hooks.auto_optimize_hook as mod

        mod._global_hook = None
        h1 = get_global_hook()
        h2 = get_global_hook()
        assert h1 is h2
        mod._global_hook = None
