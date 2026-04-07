"""LingFlow 公共 API 端到端契约测试

验证用户通过 LingFlow 类调用的真实路径，不 mock 任何内部组件。
"""

from pathlib import Path
import pytest


@pytest.fixture
def lf():
    from lingflow import LingFlow
    return LingFlow()


class TestPublicAPIContract:
    """公共 API 契约：确保用户传入 dict 时系统能正常工作"""

    def test_run_workflow_accepts_dict_tasks(self, lf):
        """run_workflow 接受 dict 格式的 task 列表"""
        result = lf.run_workflow({
            "tasks": [
                {"id": "t1", "name": "hello", "description": "test task"}
            ]
        })
        assert "t1" in result
        assert result["t1"].success is True

    def test_run_workflow_dict_with_priority(self, lf):
        """run_workflow 支持通过 dict 指定 priority"""
        result = lf.run_workflow({
            "tasks": [
                {"id": "t1", "name": "high", "priority": "high"}
            ]
        })
        assert "t1" in result
        assert result["t1"].success is True

    def test_run_workflow_dict_with_dependencies(self, lf):
        """run_workflow 支持通过 dict 指定依赖"""
        result = lf.run_workflow({
            "tasks": [
                {"id": "t1", "name": "first"},
                {"id": "t2", "name": "second", "depends_on": ["t1"]},
            ]
        })
        assert "t1" in result
        assert "t2" in result
        assert result["t1"].success is True
        assert result["t2"].success is True

    def test_run_workflow_dict_with_skill_field(self, lf):
        """run_workflow 支持 skill 字段作为 agent_type"""
        result = lf.run_workflow({
            "tasks": [
                {"id": "t1", "skill": "review", "description": "code review"}
            ]
        })
        assert "t1" in result
        assert result["t1"].success is True

    def test_run_workflow_dict_with_params(self, lf):
        """run_workflow 支持 params 字段传递给 task"""
        result = lf.run_workflow({
            "tasks": [
                {"id": "t1", "name": "test", "params": {"key": "value"}}
            ]
        })
        assert "t1" in result
        assert result["t1"].success is True

    def test_run_workflow_empty_tasks(self, lf):
        """run_workflow 空任务列表返回空结果"""
        result = lf.run_workflow({"tasks": []})
        assert result == {}

    def test_run_workflow_no_tasks_key(self, lf):
        """run_workflow 缺少 tasks 键返回空结果"""
        result = lf.run_workflow({})
        assert result == {}

    def test_run_workflow_mixed_task_and_dict(self, lf):
        """run_workflow 支持 Task dataclass 和 dict 混合"""
        from lingflow.common.models import Task, TaskPriority
        task = Task(task_id="t1", name="dataclass task", description="test", priority=TaskPriority.NORMAL)
        result = lf.run_workflow({"tasks": [task, {"id": "t2", "name": "dict task"}]})
        assert "t1" in result
        assert "t2" in result

    def test_run_skill_returns_dict(self, lf):
        """run_skill 返回 dict 结果"""
        result = lf.run_skill("task-runner", {"skill": "code-review", "params": {}})
        assert isinstance(result, dict)
        assert "skill" in result

    def test_run_skill_nonexistent(self, lf):
        """run_skill 对不存在的技能返回错误"""
        result = lf.run_skill("nonexistent_skill_xyz", {})
        assert "error" in result

    def test_list_skills_returns_list(self, lf):
        """list_skills 返回技能名称列表"""
        skills = lf.list_skills()
        assert isinstance(skills, list)
        assert len(skills) > 0

    def test_run_workflow_file_yaml(self, lf):
        """run_workflow_file 能执行 YAML 工作流文件"""
        workflow_dir = Path("/home/ai/LingFlow") / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        wf_path = workflow_dir / "_test_contract.yaml"
        wf_path.write_text("tasks:\n  - id: t1\n    name: test\n    description: yaml workflow\n", encoding="utf-8")
        try:
            result = lf.run_workflow_file(str(wf_path))
            assert "t1" in result
            assert result["t1"].success is True
        finally:
            wf_path.unlink(missing_ok=True)

    def test_run_workflow_file_not_found(self, lf):
        """run_workflow_file 对不存在的文件抛出异常"""
        with pytest.raises((FileNotFoundError, ValueError)):
            lf.run_workflow_file("/nonexistent/path/workflow.yaml")


class TestCrossLayerIntegration:
    """跨层集成测试：验证完整数据流（不 mock 任何组件）"""

    def test_skill_loads_through_sandbox(self, lf):
        """技能通过沙箱验证后能正常加载和执行"""
        result = lf.run_skill("task-runner", {"skill": "code-review", "params": {"code": "x=1"}})
        assert "result" in result
        assert isinstance(result["result"], dict)

    def test_workflow_with_multiple_tasks(self, lf):
        """多任务工作流能完整执行"""
        result = lf.run_workflow({
            "tasks": [
                {"id": "t1", "name": "task one", "description": "first"},
                {"id": "t2", "name": "task two", "description": "second"},
                {"id": "t3", "name": "task three", "description": "third"},
            ]
        })
        assert len(result) == 3
        assert all(r.success for r in result.values())

    def test_workflow_with_chain_dependencies(self, lf):
        """链式依赖工作流按顺序执行"""
        result = lf.run_workflow({
            "tasks": [
                {"id": "t1", "name": "step 1"},
                {"id": "t2", "name": "step 2", "depends_on": ["t1"]},
                {"id": "t3", "name": "step 3", "depends_on": ["t2"]},
            ]
        })
        assert all(result[tid].success for tid in ["t1", "t2", "t3"])

    def test_init_creates_coordinator_and_orchestrator(self, lf):
        """LingFlow 初始化创建协调器和编排器"""
        assert lf._coordinator is not None
        assert lf._orchestrator is not None
