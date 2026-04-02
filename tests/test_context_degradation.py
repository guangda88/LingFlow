#!/usr/bin/env python3
"""退化检测器测试

测试 DegradationDetector 的各项功能:
1. 重复崩溃检测
2. 指令漂移检测
3. 错误率检测
4. 综合健康评分
"""

import pytest
from lingflow.context.degradation import (
    DegradationDetector,
    DegradationReport,
    DegradationType,
    HealthStatus,
)


class TestRepetitionDetection:
    """重复崩溃检测测试"""

    def test_no_repetition_with_diverse_messages(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "assistant", "content": "I implemented feature A with approach X."},
            {"role": "assistant", "content": "Now moving to feature B, using strategy Y."},
            {"role": "assistant", "content": "Completed testing of module C."},
        ]
        is_repeat, score = dd.check_repetition(msgs)
        assert is_repeat is False
        assert score < 0.5

    def test_detects_repetition_with_identical_messages(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
        ]
        is_repeat, score = dd.check_repetition(msgs)
        assert is_repeat is True
        assert score >= 0.7

    def test_insufficient_messages(self):
        dd = DegradationDetector()
        msgs = [{"role": "assistant", "content": "hello"}]
        is_repeat, score = dd.check_repetition(msgs)
        assert is_repeat is False
        assert score == 0.0

    def test_empty_messages(self):
        dd = DegradationDetector()
        is_repeat, score = dd.check_repetition([])
        assert is_repeat is False

    def test_only_user_messages(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "user", "content": "do task A"},
            {"role": "user", "content": "do task B"},
        ]
        is_repeat, score = dd.check_repetition(msgs)
        assert is_repeat is False

    def test_high_similarity_detected(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "assistant", "content": "I will now implement the login function using Python"},
            {"role": "assistant", "content": "I will now implement the login function using Python"},
            {"role": "assistant", "content": "I will now implement the login function using Python"},
            {"role": "assistant", "content": "I will now implement the login function using Python"},
        ]
        is_repeat, score = dd.check_repetition(msgs)
        assert is_repeat is True


class TestInstructionDrift:
    """指令漂移检测测试"""

    def test_no_drift_with_following_messages(self):
        dd = DegradationDetector()
        instructions = ["must implement tests", "should use pytest"]
        msgs = [
            {"role": "assistant", "content": "I must implement tests with pytest framework."},
            {"role": "assistant", "content": "Now I should use pytest to write unit tests."},
        ]
        is_drift, score = dd.check_instruction_drift(instructions, msgs)
        assert is_drift is False

    def test_detects_drift(self):
        dd = DegradationDetector()
        instructions = ["must ensure security"]
        msgs = [
            {"role": "assistant", "content": "The weather is nice today."},
            {"role": "assistant", "content": "Let's talk about sports."},
            {"role": "assistant", "content": "I like pizza."},
        ]
        is_drift, score = dd.check_instruction_drift(instructions, msgs)
        assert is_drift is True
        assert score > 0.5

    def test_empty_instructions(self):
        dd = DegradationDetector()
        msgs = [{"role": "assistant", "content": "hello"}]
        is_drift, score = dd.check_instruction_drift([], msgs)
        assert is_drift is False

    def test_insufficient_messages_for_drift(self):
        dd = DegradationDetector()
        is_drift, score = dd.check_instruction_drift(["must test"], [])
        assert is_drift is False


class TestErrorRate:
    """错误率检测测试"""

    def test_normal_error_rate(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "assistant", "content": "Successfully implemented feature A."},
            {"role": "assistant", "content": "Completed task B."},
            {"role": "assistant", "content": "All tests passing."},
        ]
        is_high, rate = dd.check_error_rate(msgs)
        assert is_high is False
        assert rate == 0.0

    def test_high_error_rate(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "assistant", "content": "Error: failed to connect."},
            {"role": "assistant", "content": "Exception in module B."},
            {"role": "assistant", "content": "Traceback: ValueError occurred."},
        ]
        is_high, rate = dd.check_error_rate(msgs)
        assert is_high is True
        assert rate >= 0.5

    def test_mixed_messages(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "user", "content": "fix this"},
            {"role": "assistant", "content": "Error in processing."},
            {"role": "user", "content": "try again"},
            {"role": "assistant", "content": "Success this time."},
        ]
        is_high, rate = dd.check_error_rate(msgs)
        assert rate == 0.5  # 1 error out of 2 assistant messages

    def test_insufficient_messages(self):
        dd = DegradationDetector()
        is_high, rate = dd.check_error_rate([])
        assert is_high is False

    def test_chinese_error_keywords(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "assistant", "content": "执行失败，出现错误"},
            {"role": "assistant", "content": "发生异常，请检查"},
            {"role": "assistant", "content": "任务失败"},
        ]
        is_high, rate = dd.check_error_rate(msgs)
        assert is_high is True


class TestHealthScore:
    """综合健康评分测试"""

    def test_healthy_conversation(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "user", "content": "implement feature X"},
            {"role": "assistant", "content": "I implemented feature X using approach A."},
            {"role": "user", "content": "add tests"},
            {"role": "assistant", "content": "Added 5 unit tests, all passing."},
        ]
        report = dd.get_health_score(msgs)
        assert report.health == HealthStatus.HEALTHY
        assert report.score >= 0.7
        assert DegradationType.NONE not in report.detected_types or len(report.detected_types) == 0

    def test_degraded_conversation(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
        ]
        report = dd.get_health_score(msgs)
        assert report.health in (HealthStatus.DEGRADED, HealthStatus.CRITICAL)
        assert DegradationType.REPETITION_COLLAPSE in report.detected_types

    def test_critical_conversation(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Error: exception traceback failed"},
            {"role": "assistant", "content": "Error: failure in module Y"},
            {"role": "assistant", "content": "Error: critical error occurred"},
        ]
        report = dd.get_health_score(msgs)
        assert report.health in (HealthStatus.DEGRADED, HealthStatus.CRITICAL)
        assert len(report.detected_types) >= 1

    def test_insufficient_data(self):
        dd = DegradationDetector()
        report = dd.get_health_score([])
        assert report.health == HealthStatus.HEALTHY
        assert report.score == 1.0

    def test_report_has_details(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
            {"role": "user", "content": "bye"},
            {"role": "assistant", "content": "goodbye"},
        ]
        report = dd.get_health_score(msgs)
        assert "repetition_score" in report.details
        assert "error_rate" in report.details
        assert "drift_score" in report.details

    def test_report_to_dict(self):
        dd = DegradationDetector()
        report = dd.get_health_score([
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "user", "content": "bye"},
            {"role": "assistant", "content": "goodbye"},
        ])
        d = report.to_dict()
        assert "health" in d
        assert "score" in d
        assert "detected_types" in d
        assert "details" in d

    def test_recommendations_on_degradation(self):
        dd = DegradationDetector()
        msgs = [
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
            {"role": "assistant", "content": "Let me implement the fix for bug X"},
        ]
        report = dd.get_health_score(msgs)
        assert len(report.recommendations) > 0


class TestCustomThresholds:
    """自定义阈值测试"""

    def test_custom_repetition_threshold(self):
        dd = DegradationDetector(repetition_threshold=0.9)
        msgs = [
            {"role": "assistant", "content": "Implement feature A with approach X"},
            {"role": "assistant", "content": "Implement feature A with approach X"},
            {"role": "assistant", "content": "Implement feature A with approach X"},
        ]
        is_repeat, score = dd.check_repetition(msgs)
        assert is_repeat is True  # identical messages should still trigger

    def test_custom_error_rate_threshold(self):
        dd = DegradationDetector(error_rate_threshold=1.0)
        msgs = [
            {"role": "assistant", "content": "Error in module A"},
            {"role": "assistant", "content": "Success in module B"},
        ]
        is_high, rate = dd.check_error_rate(msgs)
        assert is_high is False  # 50% < 100%

    def test_custom_window_size(self):
        dd = DegradationDetector(window_size=5)
        assert dd.window_size == 5
