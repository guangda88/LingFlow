"""多项目并行调度器测试"""
import asyncio
import os
import tempfile
import pytest

from lingflow.common.models import Task, TaskResult, TaskPriority
from lingflow.coordination.project_manager import ProjectManager, ProjectContext
from lingflow.workflow.multi_project_scheduler import MultiProjectScheduler, ProjectScheduleStatus


@pytest.fixture
def tmp_projects(tmp_path):
    """创建临时项目目录"""
    projects = {}
    for name in ["LingFlow", "LingClaude", "LingYi"]:
        p = tmp_path / name
        p.mkdir()
        (p / ".git").mkdir()
        (p / "README.md").write_text(f"# {name}")
        projects[name] = str(p)
    return projects


@pytest.fixture
def pm(tmp_projects, tmp_path):
    """ProjectManager with temp registry"""
    registry = str(tmp_path / "test_projects.json")
    manager = ProjectManager(registry_path=registry)
    for name, path in tmp_projects.items():
        manager.register(name, path, description=f"Test {name}")
    return manager


class TestProjectManager:
    def test_register_and_get(self, pm):
        ctx = pm.get("LingFlow")
        assert ctx is not None
        assert ctx.name == "LingFlow"
        assert "LingFlow" in ctx.path

    def test_list(self, pm):
        projects = pm.list()
        assert len(projects) == 3
        names = {p.name for p in projects}
        assert names == {"LingFlow", "LingClaude", "LingYi"}

    def test_unregister(self, pm):
        assert pm.unregister("LingClaude") is True
        assert pm.get("LingClaude") is None
        assert len(pm.list()) == 2

    def test_persistence(self, tmp_projects, tmp_path):
        registry = str(tmp_path / "persist_test.json")
        pm1 = ProjectManager(registry_path=registry)
        pm1.register("LingFlow", tmp_projects["LingFlow"])

        pm2 = ProjectManager(registry_path=registry)
        assert pm2.get("LingFlow") is not None

    def test_git_status(self, pm, tmp_projects):
        # Init a real git repo in one project
        import subprocess
        p = tmp_projects["LingFlow"]
        subprocess.run(["git", "init"], cwd=p, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=p, capture_output=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=p, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=p, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=p, capture_output=True)
        status = pm.status("LingFlow")
        assert status["git"]["valid"] is True
        assert status["git"]["branch"] in ("master", "main")

    def test_invalid_path(self, pm):
        with pytest.raises(ValueError):
            pm.register("bad", "/nonexistent/path")

    def test_dashboard(self, pm):
        dash = pm.dashboard()
        assert len(dash) == 3
        assert all("git" in d for d in dash)

    def test_bind_session(self, pm):
        pm.bind_session("LingFlow", "session-123")
        ctx = pm.get("LingFlow")
        assert ctx.terminal_session == "session-123"


class TestMultiProjectScheduler:
    def test_group_by_project(self, pm):
        scheduler = MultiProjectScheduler(project_manager=pm)
        tasks = [
            Task(task_id="t1", name="review", description="", priority=TaskPriority.NORMAL, project="LingFlow"),
            Task(task_id="t2", name="test", description="", priority=TaskPriority.NORMAL, project="LingClaude"),
            Task(task_id="t3", name="build", description="", priority=TaskPriority.HIGH, project="LingFlow"),
            Task(task_id="t4", name="lint", description="", priority=TaskPriority.LOW, project="LingYi"),
        ]
        groups = scheduler._group_by_project(tasks)
        assert len(groups) == 3
        assert len(groups["LingFlow"]) == 2
        assert len(groups["LingClaude"]) == 1
        assert len(groups["LingYi"]) == 1

    def test_execute_cross_project(self, pm):
        scheduler = MultiProjectScheduler(project_manager=pm)
        tasks = [
            Task(task_id="t1", name="review", description="", priority=TaskPriority.NORMAL, project="LingFlow"),
            Task(task_id="t2", name="test", description="", priority=TaskPriority.NORMAL, project="LingClaude"),
            Task(task_id="t3", name="lint", description="", priority=TaskPriority.NORMAL, project="LingYi"),
        ]
        results = scheduler.execute(tasks)
        assert len(results) == 3

    def test_status_tracking(self, pm):
        scheduler = MultiProjectScheduler(project_manager=pm)
        tasks = [
            Task(task_id="t1", name="review", description="", priority=TaskPriority.NORMAL, project="LingFlow"),
            Task(task_id="t2", name="test", description="", priority=TaskPriority.NORMAL, project="LingClaude"),
        ]
        scheduler.execute(tasks)
        status = scheduler.get_status()
        assert status["total_tasks"] == 2
        assert "LingFlow" in status["projects"]
        assert "LingClaude" in status["projects"]

    def test_progress_callback(self, pm):
        callbacks = []
        scheduler = MultiProjectScheduler(project_manager=pm)
        scheduler.on_progress(lambda s: callbacks.append(s))

        tasks = [
            Task(task_id="t1", name="review", description="", priority=TaskPriority.NORMAL, project="LingFlow"),
        ]
        scheduler.execute(tasks)
        assert len(callbacks) >= 1

    def test_empty_tasks(self, pm):
        scheduler = MultiProjectScheduler(project_manager=pm)
        results = scheduler.execute([])
        assert results == {}

    def test_yaml_loading(self, tmp_path):
        yaml_content = """
tasks:
  - task_id: review_lf
    project: LingFlow
    skill: code-review
    priority: high
    depends_on: []
    params:
      target: src/

  - task_id: test_lc
    project: LingClaude
    skill: test-runner
    priority: normal
    params:
      coverage: true

  - task_id: fix_lf
    project: LingFlow
    skill: code-refactor
    priority: critical
    depends_on: [review_lf]
"""
        yaml_file = tmp_path / "cross_project.yaml"
        yaml_file.write_text(yaml_content)

        tasks = MultiProjectScheduler.load_tasks_from_yaml(str(yaml_file))
        assert len(tasks) == 3

        assert tasks[0].project == "LingFlow"
        assert tasks[0].priority == TaskPriority.HIGH
        assert tasks[0].dependencies == []

        assert tasks[1].project == "LingClaude"
        assert tasks[1].priority == TaskPriority.NORMAL

        assert tasks[2].project == "LingFlow"
        assert tasks[2].priority == TaskPriority.CRITICAL
        assert tasks[2].dependencies == ["review_lf"]
