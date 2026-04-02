"""Models module tests — AgentStatus, TaskPriority, AgentConfig, Task, TaskResult"""

from lingflow.common.models import (
    AgentStatus,
    TaskPriority,
    AgentConfig,
    Task,
    TaskResult,
)


class TestAgentStatus:
    def test_values(self):
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.BUSY.value == "busy"
        assert AgentStatus.FAILED.value == "failed"

    def test_from_value(self):
        assert AgentStatus("idle") == AgentStatus.IDLE


class TestTaskPriority:
    def test_ordering(self):
        assert TaskPriority.CRITICAL.value < TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value < TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value < TaskPriority.LOW.value

    def test_values(self):
        assert TaskPriority.CRITICAL.value == 0
        assert TaskPriority.HIGH.value == 1
        assert TaskPriority.NORMAL.value == 2
        assert TaskPriority.LOW.value == 3


class TestAgentConfig:
    def test_defaults(self):
        cfg = AgentConfig(name="a", description="b", capabilities=["c"])
        assert cfg.max_tasks == 1
        assert cfg.context_limit == 8000
        assert cfg.timeout == 300
        assert cfg.parallel_safe is True

    def test_custom(self):
        cfg = AgentConfig(
            name="x", description="y", capabilities=["z"],
            max_tasks=5, context_limit=16000, timeout=60, parallel_safe=False,
        )
        assert cfg.max_tasks == 5
        assert cfg.context_limit == 16000
        assert cfg.parallel_safe is False


class TestTask:
    def test_defaults(self):
        t = Task(task_id="t1", name="n", description="d", priority=TaskPriority.NORMAL)
        assert t.agent_type == ""
        assert t.dependencies == []
        assert t.context == {}

    def test_full(self):
        t = Task(
            task_id="t2", name="n", description="d",
            priority=TaskPriority.HIGH, agent_type="review",
            dependencies=["t1"], context={"key": "val"},
        )
        assert t.agent_type == "review"
        assert t.dependencies == ["t1"]
        assert t.context == {"key": "val"}


class TestTaskResult:
    def test_success(self):
        r = TaskResult(task_id="t1", success=True, output="ok")
        assert r.success is True
        assert r.output == "ok"
        assert r.error is None
        assert r.execution_time == 0.0
        assert r.agent_used is None

    def test_failure(self):
        r = TaskResult(task_id="t2", success=False, error="fail")
        assert r.success is False
        assert r.error == "fail"
        assert r.output is None

    def test_full(self):
        r = TaskResult(
            task_id="t3", success=True, output="done",
            execution_time=1.5, agent_used="impl",
        )
        assert r.execution_time == 1.5
        assert r.agent_used == "impl"
