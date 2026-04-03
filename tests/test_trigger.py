import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from lingflow.self_optimizer.trigger import OptimizationTrigger, TriggerInfo
from lingflow.self_optimizer.config import OptimizationConfig, get_global_config, set_global_config


class TestTriggerInfo:
    def test_init_defaults(self):
        info = TriggerInfo(
            type="quality",
            reason="test",
            priority="high",
            current_value=42,
            threshold=50,
            metrics={"a": 1},
        )
        assert info.type == "quality"
        assert info.reason == "test"
        assert info.priority == "high"
        assert info.current_value == 42
        assert info.threshold == 50
        assert info.metrics == {"a": 1}

    def test_init_with_none_values(self):
        info = TriggerInfo(
            type="user",
            reason="user triggered",
            priority="high",
            current_value=None,
            threshold=None,
            metrics={},
        )
        assert info.current_value is None
        assert info.threshold is None


class TestOptimizationTriggerInit:
    def test_default_config(self):
        trigger = OptimizationTrigger()
        assert trigger.config is not None
        assert isinstance(trigger.config, OptimizationConfig)

    def test_custom_config(self):
        cfg = OptimizationConfig()
        trigger = OptimizationTrigger(config=cfg)
        assert trigger.config is cfg

    def test_last_check_initialized(self):
        trigger = OptimizationTrigger()
        assert trigger.last_check == {}


class TestCheckAllConditions:
    def test_user_triggered(self):
        trigger = OptimizationTrigger()
        should, info = trigger.check_all_conditions({"user_triggered": True})
        assert should is True
        assert info is not None
        assert info.type == "user"
        assert info.priority == "high"

    def test_user_triggered_false(self):
        trigger = OptimizationTrigger()
        should, info = trigger.check_all_conditions({"user_triggered": False})
        assert should is False
        assert info is None

    def test_no_triggers(self):
        trigger = OptimizationTrigger()
        should, info = trigger.check_all_conditions({})
        assert should is False
        assert info is None

    def test_quality_trigger_only(self):
        trigger = OptimizationTrigger()
        should, info = trigger.check_all_conditions({"review_score": 30})
        assert should is True
        assert info is not None
        assert info.type == "quality"

    def test_multiple_triggers_returns_highest_priority(self):
        trigger = OptimizationTrigger()
        ctx = {
            "review_score": 30,
            "todo_count": 25,
        }
        should, info = trigger.check_all_conditions(ctx)
        assert should is True
        assert info.priority == "high"


class TestCheckQuality:
    def _make_trigger(self):
        return OptimizationTrigger(config=OptimizationConfig())

    def test_review_score_below_high(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({"review_score": 40})
        assert result is not None
        assert result.type == "quality"
        assert result.priority == "high"
        assert result.current_value == 40

    def test_review_score_below_medium(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({"review_score": 60})
        assert result is not None
        assert result.priority == "medium"

    def test_review_score_ok(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({"review_score": 80})
        assert result is None

    def test_review_score_default_100(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({})
        assert result is None

    def test_coverage_drop(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({"coverage_drop": 10})
        assert result is not None
        assert result.priority == "medium"
        assert "coverage_drop" in result.metrics

    def test_coverage_drop_below_threshold(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({"coverage_drop": 3})
        assert result is None

    def test_coverage_drop_default_zero(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({})
        assert result is None

    def test_test_failure_rate(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({"test_failure_rate": 15})
        assert result is not None
        assert result.priority == "high"

    def test_test_failure_rate_below_threshold(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({"test_failure_rate": 5})
        assert result is None

    def test_review_score_returns_first(self):
        trigger = self._make_trigger()
        result = trigger._check_quality({"review_score": 30, "coverage_drop": 10})
        assert result is not None
        assert result.metrics.get("review_score") == 30


class TestCheckStructure:
    def test_complexity_above(self):
        trigger = OptimizationTrigger()
        result = trigger._check_structure({"avg_complexity": 20})
        assert result is not None
        assert result.type == "structure"
        assert result.priority == "medium"
        assert result.metrics["avg_complexity"] == 20

    def test_complexity_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_structure({"avg_complexity": 10})
        assert result is None

    def test_large_classes_count(self):
        trigger = OptimizationTrigger()
        result = trigger._check_structure({"large_classes_count": 10})
        assert result is not None
        assert result.priority == "medium"

    def test_large_classes_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_structure({"large_classes_count": 3})
        assert result is None

    def test_duplication_rate(self):
        trigger = OptimizationTrigger()
        result = trigger._check_structure({"duplication_rate": 0.1})
        assert result is not None
        assert result.priority == "low"
        assert "0.1" in result.reason or "10.0" in result.reason

    def test_duplication_rate_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_structure({"duplication_rate": 0.03})
        assert result is None

    def test_coupling(self):
        trigger = OptimizationTrigger()
        result = trigger._check_structure({"avg_coupling": 15})
        assert result is not None
        assert result.priority == "medium"

    def test_coupling_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_structure({"avg_coupling": 5})
        assert result is None

    def test_no_structure_issues(self):
        trigger = OptimizationTrigger()
        result = trigger._check_structure({})
        assert result is None


class TestCheckPerformance:
    def test_execution_time_increase(self):
        trigger = OptimizationTrigger()
        result = trigger._check_performance({
            "execution_time": 3.0,
            "baseline_time": 1.0,
        })
        assert result is not None
        assert result.type == "performance"
        assert result.priority == "high"

    def test_execution_time_ok(self):
        trigger = OptimizationTrigger()
        result = trigger._check_performance({
            "execution_time": 1.2,
            "baseline_time": 1.0,
        })
        assert result is None

    def test_execution_time_no_baseline(self):
        trigger = OptimizationTrigger()
        result = trigger._check_performance({"execution_time": 5.0})
        assert result is None

    def test_memory_usage(self):
        trigger = OptimizationTrigger()
        result = trigger._check_performance({"memory_usage_mb": 600})
        assert result is not None
        assert result.priority == "high"

    def test_memory_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_performance({"memory_usage_mb": 300})
        assert result is None

    def test_response_time(self):
        trigger = OptimizationTrigger()
        result = trigger._check_performance({"response_time_ms": 200})
        assert result is not None
        assert result.priority == "medium"

    def test_response_time_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_performance({"response_time_ms": 50})
        assert result is None

    def test_no_performance_issues(self):
        trigger = OptimizationTrigger()
        result = trigger._check_performance({})
        assert result is None


class TestCheckScale:
    def test_new_lines(self):
        trigger = OptimizationTrigger()
        result = trigger._check_scale({"new_lines": 600})
        assert result is not None
        assert result.type == "scale"
        assert result.priority == "low"

    def test_new_lines_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_scale({"new_lines": 300})
        assert result is None

    def test_new_files(self):
        trigger = OptimizationTrigger()
        result = trigger._check_scale({"new_files": 15})
        assert result is not None
        assert result.priority == "low"

    def test_new_files_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_scale({"new_files": 5})
        assert result is None

    def test_no_scale_issues(self):
        trigger = OptimizationTrigger()
        result = trigger._check_scale({})
        assert result is None


class TestCheckTechDebt:
    def test_todo_count(self):
        trigger = OptimizationTrigger()
        result = trigger._check_tech_debt({"todo_count": 30})
        assert result is not None
        assert result.type == "tech_debt"
        assert result.priority == "low"

    def test_todo_count_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_tech_debt({"todo_count": 10})
        assert result is None

    def test_hack_comments(self):
        trigger = OptimizationTrigger()
        result = trigger._check_tech_debt({"hack_comments": 5})
        assert result is not None
        assert result.priority == "medium"

    def test_hack_comments_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_tech_debt({"hack_comments": 2})
        assert result is None

    def test_no_debt_issues(self):
        trigger = OptimizationTrigger()
        result = trigger._check_tech_debt({})
        assert result is None


class TestCheckTime:
    def test_days_since_last_optimization(self):
        trigger = OptimizationTrigger()
        last_time = datetime.now() - timedelta(days=10)
        result = trigger._check_time({"last_optimization_time": last_time})
        assert result is not None
        assert result.type == "time"
        assert result.priority == "low"

    def test_days_since_string(self):
        trigger = OptimizationTrigger()
        last_time = (datetime.now() - timedelta(days=10)).isoformat()
        result = trigger._check_time({"last_optimization_time": last_time})
        assert result is not None

    def test_days_since_recent(self):
        trigger = OptimizationTrigger()
        last_time = datetime.now() - timedelta(days=2)
        result = trigger._check_time({"last_optimization_time": last_time})
        assert result is None

    def test_commits_since(self):
        trigger = OptimizationTrigger()
        result = trigger._check_time({"commits_since_last_check": 25})
        assert result is not None

    def test_commits_since_below(self):
        trigger = OptimizationTrigger()
        result = trigger._check_time({"commits_since_last_check": 10})
        assert result is None

    def test_no_time_issues(self):
        trigger = OptimizationTrigger()
        result = trigger._check_time({})
        assert result is None


class TestShouldAutoTrigger:
    def test_default_hooks(self):
        trigger = OptimizationTrigger()
        result = trigger.should_auto_trigger()
        assert isinstance(result, bool)

    def test_with_hooks_enabled(self):
        cfg = OptimizationConfig()
        cfg.config["hooks"]["enable_on_review"] = True
        trigger = OptimizationTrigger(config=cfg)
        assert trigger.should_auto_trigger() is True

    def test_with_hooks_disabled(self):
        cfg = OptimizationConfig()
        cfg.config["hooks"] = {
            "enable_on_review": False,
            "enable_on_test": False,
            "enable_on_commit": False,
        }
        trigger = OptimizationTrigger(config=cfg)
        assert trigger.should_auto_trigger() is False


class TestRequiresConfirmation:
    def test_default(self):
        trigger = OptimizationTrigger()
        assert trigger.requires_confirmation() is True

    def test_disabled(self):
        cfg = OptimizationConfig()
        cfg.config["hooks"]["require_confirmation"] = False
        trigger = OptimizationTrigger(config=cfg)
        assert trigger.requires_confirmation() is False
