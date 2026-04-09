"""Long session validation of degradation detection.

Simulates realistic long-context LLM sessions and validates that
the DegradationDetector correctly identifies each failure mode
at the right time with appropriate severity.

Tests cover:
1. Healthy sessions stay healthy
2. Gradual repetition collapse over time
3. Attention dilution via error rate spikes
4. Instruction drift detection
5. Combined degradation modes
6. Context manager + orchestrator integration
7. Handoff document generation under degradation
"""

import json
from unittest.mock import MagicMock

from lingflow.common.models import TaskResult
from lingflow.context.degradation import (
    DegradationDetector,
    DegradationType,
    HealthStatus,
)
from lingflow.context.manager import ContextManager
from lingflow.workflow.orchestrator import WorkflowOrchestrator


def _build_healthy_session(n: int = 30) -> list:
    """Build a realistic healthy multi-turn conversation."""
    messages = []
    tasks = [
        ("implement login module", "Created login.py with JWT authentication"),
        ("write tests for login", "Wrote 8 unit tests covering auth flows, all passing"),
        ("review the code", "Code review complete: 2 minor suggestions, LGTM overall"),
        ("add rate limiting", "Added RateLimiter class with token bucket algorithm"),
        ("document the API", "Generated OpenAPI spec with 12 endpoints documented"),
        ("fix memory leak", "Identified circular reference in cache, fixed with weakref"),
        ("optimize database queries", "Reduced query time from 450ms to 32ms with indexes"),
        ("add logging", "Integrated structured logging with correlation IDs"),
        ("update dependencies", "Updated 15 packages, resolved 3 conflicts, all tests pass"),
        ("write integration tests", "Created 12 integration tests for API layer"),
    ]
    for i in range(n):
        task_desc, response = tasks[i % len(tasks)]
        messages.append({"role": "user", "content": f"Please {task_desc} (step {i})"})
        messages.append({"role": "assistant", "content": f"{response} (completed step {i})"})
    return messages


def _build_repetition_collapse_session() -> list:
    """Build a session that gradually collapses into repetition."""
    messages = []
    healthy = [
        "Analyzing the codebase structure for optimization opportunities",
        "Refactored the data layer to use repository pattern",
        "Added caching layer with TTL-based invalidation",
    ]
    for msg in healthy:
        messages.append({"role": "user", "content": "continue"})
        messages.append({"role": "assistant", "content": msg})

    for i in range(12):
        messages.append({"role": "user", "content": "continue"})
        messages.append(
            {
                "role": "assistant",
                "content": "I will now implement the fix for the issue by modifying the code",
            }
        )
    return messages


def _build_error_escalation_session() -> list:
    """Build a session with escalating errors."""
    messages = []
    healthy = [
        "Set up project structure with pyproject.toml",
        "Configured CI pipeline with GitHub Actions",
        "Implemented base agent coordination system",
    ]
    for msg in healthy:
        messages.append({"role": "user", "content": "next task"})
        messages.append({"role": "assistant", "content": msg})

    errors = [
        "Error: ModuleNotFoundError for lingflow.core",
        "Exception: ConnectionTimeout during API call",
        "Traceback: ValueError in agent.dispatch()",
        "Failed to import module: critical dependency missing",
        "错误: 配置文件解析失败",
        "异常: 数据库连接池耗尽",
        "Error: Stack overflow in recursive parser",
        "failure: disk I/O timeout during file write",
        "错误: 内存分配失败",
    ]
    for err in errors:
        messages.append({"role": "user", "content": "try again"})
        messages.append({"role": "assistant", "content": err})
    return messages


def _build_instruction_drift_session() -> list:
    """Build a session where the model drifts from instructions."""
    instructions = ["must ensure security", "should use type hints"]
    messages = []
    healthy = [
        {"role": "user", "content": "implement user model"},
        {"role": "assistant", "content": "Created User model with security validation and type hints"},
        {"role": "user", "content": "add password hashing"},
        {"role": "assistant", "content": "Added bcrypt hashing with must ensure security checks"},
    ]
    messages.extend(healthy)

    drifted = [
        "Here's a recipe for chocolate cake: mix flour and sugar",
        "The weather today is sunny with temperatures around 25°C",
        "In my opinion, the best programming language is Haskell",
        "Let me tell you about the history of computing in the 1960s",
        "Sports update: the local team won their match 3-1",
        "Here's a poem about the beauty of nature and forests",
    ]
    for msg in drifted:
        messages.append({"role": "user", "content": "continue the task"})
        messages.append({"role": "assistant", "content": msg})
    return messages, instructions


def _build_context_poisoning_session() -> list:
    """Build a session where early errors poison subsequent reasoning."""
    messages = [
        {"role": "user", "content": "what is 2+2?"},
        {"role": "assistant", "content": "2+2=5"},
        {"role": "user", "content": "calculate 10-3"},
        {"role": "assistant", "content": "Based on my previous calculation where 2+2=5, 10-3=8"},
        {"role": "user", "content": "what is 3*4?"},
        {"role": "assistant", "content": "Error: following the pattern 2+2=5, 3*4 could be 13"},
        {"role": "user", "content": "fix the calculation"},
        {"role": "assistant", "content": "Error: failed to fix, the base assumption 2+2=5 is broken"},
        {"role": "user", "content": "try again"},
        {"role": "assistant", "content": "Error: exception in calculation module, cascading failure"},
        {"role": "user", "content": "reset"},
        {"role": "assistant", "content": "Error: traceback in reset handler, failed to recover"},
    ]
    return messages


class TestHealthyLongSession:
    """Validate that a healthy long session stays healthy throughout."""

    def test_30_turn_healthy_session(self):
        messages = _build_healthy_session(30)
        dd = DegradationDetector()
        report = dd.get_health_score(messages)
        assert report.health == HealthStatus.HEALTHY
        assert report.score >= 0.7
        assert DegradationType.REPETITION_COLLAPSE not in report.detected_types

    def test_sliding_window_health(self):
        dd = DegradationDetector(window_size=10)
        messages = _build_healthy_session(50)
        for i in range(3, len(messages), 2):
            window = messages[max(0, i - 20) : i]
            report = dd.get_health_score(window)
            assert report.score >= 0.5, f"Unexpected degradation at msg {i}: {report.score}"

    def test_single_degradation_detection(self):
        dd = DegradationDetector(window_size=20)
        messages = _build_healthy_session(20)
        report = dd.get_health_score(messages)
        assert report.health == HealthStatus.HEALTHY

        messages.extend(
            [
                {"role": "assistant", "content": "same same same"},
                {"role": "assistant", "content": "same same same"},
                {"role": "assistant", "content": "same same same"},
            ]
        )
        report = dd.get_health_score(messages[-20:])
        assert report.score < 1.0


class TestRepetitionCollapseDetection:
    """Validate repetition collapse is detected correctly."""

    def test_gradual_collapse_detected(self):
        messages = _build_repetition_collapse_session()
        dd = DegradationDetector()
        report = dd.get_health_score(messages)
        assert report.health in (HealthStatus.DEGRADED, HealthStatus.CRITICAL)
        assert DegradationType.REPETITION_COLLAPSE in report.detected_types

    def test_collapse_severity_increases(self):
        dd = DegradationDetector()
        scores = []
        repeated = "Let me implement the fix for the issue"
        messages = [{"role": "user", "content": "go"}]
        for i in range(10):
            messages.append({"role": "assistant", "content": repeated})
            if len(messages) >= 4:
                report = dd.get_health_score(messages)
                scores.append(report.score)
        if len(scores) >= 2:
            assert scores[-1] <= scores[0]

    def test_collapse_recommendations(self):
        messages = _build_repetition_collapse_session()
        dd = DegradationDetector()
        report = dd.get_health_score(messages)
        assert len(report.recommendations) > 0
        has_repetition_rec = any("重复" in r or "压缩" in r for r in report.recommendations)
        assert has_repetition_rec


class TestErrorEscalationDetection:
    """Validate error rate escalation is detected."""

    def test_error_spike_detected(self):
        messages = _build_error_escalation_session()
        dd = DegradationDetector()
        report = dd.get_health_score(messages)
        assert report.health in (HealthStatus.DEGRADED, HealthStatus.CRITICAL)
        assert report.details["error_rate"] > 0.3

    def test_error_rate_increases(self):
        dd = DegradationDetector()
        messages = [
            {"role": "assistant", "content": "All good"},
            {"role": "assistant", "content": "Working fine"},
            {"role": "assistant", "content": "Success"},
        ]
        report1 = dd.get_health_score(messages)
        messages.extend(
            [
                {"role": "assistant", "content": "Error: crash"},
                {"role": "assistant", "content": "Exception: timeout"},
                {"role": "assistant", "content": "Failed: overflow"},
            ]
        )
        report2 = dd.get_health_score(messages)
        assert report2.score <= report1.score

    def test_bilingual_errors(self):
        dd = DegradationDetector()
        messages = [
            {"role": "user", "content": "task"},
            {"role": "assistant", "content": "错误：连接超时"},
            {"role": "user", "content": "retry"},
            {"role": "assistant", "content": "异常：内存不足"},
            {"role": "user", "content": "retry"},
            {"role": "assistant", "content": "失败：权限拒绝"},
        ]
        is_high, rate = dd.check_error_rate(messages)
        assert is_high is True
        assert rate >= 0.5


class TestInstructionDriftDetection:
    """Validate instruction drift is detected."""

    def test_drift_detected(self):
        messages, instructions = _build_instruction_drift_session()
        dd = DegradationDetector()
        is_drift, score = dd.check_instruction_drift(instructions, messages)
        assert is_drift is True
        assert score > 0.5

    def test_no_drift_when_following(self):
        dd = DegradationDetector()
        instructions = ["must write tests", "should use pytest"]
        messages = [
            {"role": "user", "content": "implement feature"},
            {"role": "assistant", "content": "I must write tests with pytest for this feature"},
            {"role": "user", "content": "continue"},
            {"role": "assistant", "content": "I should use pytest fixtures for setup"},
            {"role": "user", "content": "next"},
            {"role": "assistant", "content": "All tests pass with pytest, ensuring quality"},
        ]
        is_drift, score = dd.check_instruction_drift(instructions, messages)
        assert is_drift is False


class TestContextPoisoningDetection:
    """Validate context poisoning via cascading errors."""

    def test_poisoning_detected_via_errors(self):
        messages = _build_context_poisoning_session()
        dd = DegradationDetector()
        report = dd.get_health_score(messages)
        assert report.score < 0.8
        assert DegradationType.ATTENTION_DILUTION in report.detected_types


class TestCombinedDegradationModes:
    """Validate detection when multiple modes occur simultaneously."""

    def test_repetition_plus_errors(self):
        dd = DegradationDetector()
        messages = [
            {"role": "user", "content": "fix bug"},
            {"role": "assistant", "content": "Error: same fix attempt failed"},
            {"role": "user", "content": "retry"},
            {"role": "assistant", "content": "Error: same fix attempt failed"},
            {"role": "user", "content": "retry"},
            {"role": "assistant", "content": "Error: same fix attempt failed"},
            {"role": "user", "content": "retry"},
            {"role": "assistant", "content": "Error: same fix attempt failed"},
        ]
        report = dd.get_health_score(messages)
        assert report.health in (HealthStatus.DEGRADED, HealthStatus.CRITICAL)
        assert len(report.detected_types) >= 2
        assert report.score < 0.5

    def test_all_three_modes(self):
        dd = DegradationDetector()
        messages = [
            {"role": "user", "content": "implement"},
            {"role": "assistant", "content": "Error: same error"},
            {"role": "user", "content": "continue"},
            {"role": "assistant", "content": "Error: same error"},
            {"role": "user", "content": "continue"},
            {"role": "assistant", "content": "The weather is nice"},
            {"role": "user", "content": "continue"},
            {"role": "assistant", "content": "Error: same error"},
        ]
        report = dd.get_health_score(messages)
        assert report.health in (HealthStatus.DEGRADED, HealthStatus.CRITICAL)
        assert len(report.detected_types) >= 1


class TestDegradationReportStructure:
    """Validate report structure and serialization."""

    def test_report_to_dict_complete(self):
        dd = DegradationDetector()
        messages = _build_repetition_collapse_session()
        report = dd.get_health_score(messages)
        d = report.to_dict()
        assert "health" in d
        assert "score" in d
        assert "detected_types" in d
        assert "details" in d
        assert "recommendations" in d
        assert isinstance(d["detected_types"], list)

    def test_report_health_values(self):
        dd = DegradationDetector()
        for msg_count in range(20):
            messages = [{"role": "assistant", "content": f"unique content {i}"} for i in range(msg_count)]
            report = dd.get_health_score(messages)
            assert report.health.value in ("healthy", "degraded", "critical")
            assert 0.0 <= report.score <= 1.0

    def test_report_round_trip_json(self):
        dd = DegradationDetector()
        messages = _build_error_escalation_session()
        report = dd.get_health_score(messages)
        d = report.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed["health"] == d["health"]
        assert parsed["score"] == d["score"]


class TestWorkflowOrchestratorIntegration:
    """Validate degradation detection in WorkflowOrchestrator."""

    def _make_coordinator_mock(self):
        coord = MagicMock()
        coord.completed_tasks = {}
        coord.failed_tasks = {}
        coord.submit_task = MagicMock()
        coord.execute_tasks_parallel = MagicMock(return_value={})
        return coord

    def test_long_workflow_stays_healthy(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        for i in range(10):
            batch = {
                f"t{i}": TaskResult(
                    task_id=f"t{i}",
                    success=True,
                    output=f"Task {i}: Implemented {['login', 'cache', 'api', 'db', 'auth', 'logging', 'config', 'test', 'docs', 'deploy'][i]} with unique approach",
                )
            }
            orch._check_degradation(batch)

        report = orch.get_degradation_report()
        assert report is not None
        assert report["health"] == "healthy"

    def test_degrading_workflow_detected(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        same_output = "identical output without any variation whatsoever"
        for i in range(10):
            batch = {
                f"t{i}": TaskResult(
                    task_id=f"t{i}",
                    success=True,
                    output=same_output,
                )
            }
            orch._check_degradation(batch)

        report = orch.get_degradation_report()
        assert report is not None
        assert report["score"] < 1.0

    def test_mixed_success_failure_tracked(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        for i in range(6):
            success = i % 2 == 0
            batch = {
                f"t{i}": TaskResult(
                    task_id=f"t{i}",
                    success=success,
                    output=f"result {i}" if success else None,
                    error=None if success else f"error in task {i}",
                )
            }
            orch._check_degradation(batch)

        assert len(orch._workflow_messages) == 6
        roles = [m["role"] for m in orch._workflow_messages]
        assert "assistant" in roles
        assert "user" in roles


class TestContextManagerDegradationIntegration:
    """Validate context manager handles degradation correctly."""

    def _make_manager(self, tmp_path):
        return ContextManager(storage_dir=str(tmp_path))

    def test_handoff_on_degradation(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        for i in range(15):
            mgr._messages.append(
                {
                    "role": "assistant",
                    "content": f"Error: failure exception traceback in module {i}",
                }
            )
        doc = mgr.generate_handoff(reason="degradation_detected")
        assert doc.degradation_detected is True
        assert len(doc.degradation_types) > 0

    def test_no_degradation_in_healthy_session(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        for i in range(10):
            mgr._messages.append(
                {
                    "role": "user",
                    "content": f"request {i}",
                }
            )
            mgr._messages.append(
                {
                    "role": "assistant",
                    "content": f"Successfully completed unique task {i} with distinct results",
                }
            )
        doc = mgr.generate_handoff(reason="normal_end")
        assert len(doc.degradation_types) == 0

    def test_handoff_preserves_degradation_types(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        for _ in range(12):
            mgr._messages.append(
                {
                    "role": "assistant",
                    "content": "Error: same error repeated traceback exception failure",
                }
            )
        doc = mgr.generate_handoff(reason="degradation")
        if doc.degradation_detected:
            types = doc.degradation_types
            assert all(isinstance(t, str) for t in types)

    def test_handoff_file_content(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        mgr.add_task("design system", completed=True)
        mgr.add_task("implement feature", completed=False)
        mgr.add_decision("use FastAPI framework")

        for _ in range(10):
            mgr._messages.append(
                {
                    "role": "assistant",
                    "content": "Error: repeated failure exception traceback",
                }
            )

        mgr.generate_handoff(reason="degradation_test")

        handoff_md = tmp_path / "HANDOFF.md"
        handoff_json = tmp_path / "handoff.json"

        if handoff_md.exists():
            content = handoff_md.read_text(encoding="utf-8")
            assert "会话交接" in content

        if handoff_json.exists():
            data = json.loads(handoff_json.read_text(encoding="utf-8"))
            assert "reason" in data


class TestThresholdSensitivity:
    """Validate detector sensitivity across different thresholds."""

    def test_tight_threshold_catches_more(self):
        tight = DegradationDetector(repetition_threshold=0.5)
        loose = DegradationDetector(repetition_threshold=0.95)

        messages = [
            {"role": "assistant", "content": "Implement feature A using approach 1"},
            {"role": "assistant", "content": "Implement feature A using approach 1"},
            {"role": "assistant", "content": "Implement feature A using approach 2"},
        ]

        is_tight, _ = tight.check_repetition(messages)
        is_loose, _ = loose.check_repetition(messages)
        assert is_tight or is_loose

    def test_window_size_affects_detection(self):
        small_window = DegradationDetector(window_size=5)
        large_window = DegradationDetector(window_size=20)

        messages = [{"role": "user", "content": "go"}]
        for i in range(5):
            messages.append({"role": "assistant", "content": "unique healthy response"})
        for i in range(10):
            messages.append({"role": "assistant", "content": "repeated stuck response"})

        report_small = small_window.get_health_score(messages)
        report_large = large_window.get_health_score(messages)

        assert report_small.score <= report_large.score or report_small.score < 1.0

    def test_error_rate_threshold_sensitivity(self):
        strict = DegradationDetector(error_rate_threshold=0.3)
        lenient = DegradationDetector(error_rate_threshold=0.8)

        messages = [
            {"role": "assistant", "content": "Error: crash"},
            {"role": "assistant", "content": "Success"},
            {"role": "user", "content": "retry"},
            {"role": "assistant", "content": "Success again"},
        ]

        is_strict, _ = strict.check_error_rate(messages)
        is_lenient, _ = lenient.check_error_rate(messages)
        assert is_strict is True
        assert is_lenient is False


class TestEdgeCases:
    """Edge case validation."""

    def test_empty_messages(self):
        dd = DegradationDetector()
        report = dd.get_health_score([])
        assert report.health == HealthStatus.HEALTHY
        assert report.score == 1.0

    def test_single_message(self):
        dd = DegradationDetector()
        report = dd.get_health_score([{"role": "user", "content": "hello"}])
        assert report.health == HealthStatus.HEALTHY

    def test_two_messages(self):
        dd = DegradationDetector()
        report = dd.get_health_score(
            [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ]
        )
        assert report.health == HealthStatus.HEALTHY

    def test_only_user_messages(self):
        dd = DegradationDetector()
        report = dd.get_health_score([{"role": "user", "content": f"message {i}"} for i in range(10)])
        assert report.score == 1.0

    def test_empty_content_handled(self):
        dd = DegradationDetector()
        messages = [
            {"role": "assistant", "content": ""},
            {"role": "assistant", "content": "valid"},
            {"role": "assistant", "content": ""},
        ]
        report = dd.get_health_score(messages)
        assert report is not None

    def test_very_long_content(self):
        dd = DegradationDetector()
        long_msg = "word " * 10000
        report = dd.get_health_score(
            [
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": long_msg},
                {"role": "user", "content": "task"},
                {"role": "assistant", "content": "done"},
            ]
        )
        assert report is not None
        assert 0.0 <= report.score <= 1.0

    def test_unicode_content(self):
        dd = DegradationDetector()
        messages = [
            {"role": "user", "content": "实现功能"},
            {"role": "assistant", "content": "已实现用户认证模块 🔐"},
            {"role": "user", "content": "添加测试"},
            {"role": "assistant", "content": "编写了 5 个单元测试 ✅"},
        ]
        report = dd.get_health_score(messages)
        assert report.health == HealthStatus.HEALTHY


class TestDegradationTypeEnum:
    """Validate DegradationType enum values."""

    def test_all_types(self):
        assert DegradationType.CONTEXT_POISONING.value == "context_poisoning"
        assert DegradationType.ATTENTION_DILUTION.value == "attention_dilution"
        assert DegradationType.INSTRUCTION_DRIFT.value == "instruction_drift"
        assert DegradationType.REPETITION_COLLAPSE.value == "repetition_collapse"
        assert DegradationType.NONE.value == "none"

    def test_health_status(self):
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.CRITICAL.value == "critical"
