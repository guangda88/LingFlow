# Phase 4-5 集成测试用例

**版本**: v1.0
**日期**: 2026-03-31

---

## 目录

1. [测试策略](#测试策略)
2. [单元测试](#单元测试)
3. [集成测试](#集成测试)
4. [端到端测试](#端到端测试)
5. [性能测试](#性能测试)
6. [测试数据](#测试数据)

---

## 测试策略

### 测试金字塔

```
        E2E Tests (10%)
       /             \
      /               \
     /                 \
    /                   \
   /                     \
  /                       \
 /      Integration Tests (30%)
/                           \
-----------------------------\
      Unit Tests (60%)
```

### 测试覆盖目标

| 层级 | 覆盖率目标 | 重点 |
|------|-----------|------|
| 单元测试 | 85%+ | 核心逻辑、边界条件 |
| 集成测试 | 75%+ | 组件交互、数据流 |
| E2E测试 | 50%+ | 关键路径、用户场景 |
| 性能测试 | N/A | 基准、压力测试 |

---

## 单元测试

### 1. SmartOptimizerRouter 测试

```python
import pytest
from lingflow.integration import SmartOptimizerRouter
from lingflow.self_optimizer import SynchronousOptimizer
from lingflow.self_optimizer.phase4 import OptimizationEngine

class TestSmartOptimizerRouter:
    """测试智能优化器路由"""

    @pytest.fixture
    def router(self):
        """创建路由器实例"""
        config = {
            "phase4.enabled": False,
            "phase4.project_size_threshold": 50
        }
        return SmartOptimizerRouter(config)

    def test_small_project_uses_legacy(self, router):
        """小型项目使用传统优化器"""
        context = {"class_count": 30}
        optimizer = router.get_optimizer(context)

        assert isinstance(optimizer, SynchronousOptimizer)
        assert not isinstance(optimizer, OptimizationEngine)

    def test_large_project_uses_phase4(self, router):
        """大型项目使用Phase 4优化器"""
        context = {"class_count": 100}
        optimizer = router.get_optimizer(context)

        assert isinstance(optimizer, OptimizationEngine)

    def test_phase4_explicitly_enabled(self, router):
        """显式启用Phase 4"""
        router.phase4_enabled = True
        context = {"class_count": 30}

        optimizer = router.get_optimizer(context)

        assert isinstance(optimizer, OptimizationEngine)

    def test_long_optimization_uses_phase4(self, router):
        """长时间优化使用Phase 4"""
        context = {"max_time": 400}
        optimizer = router.get_optimizer(context)

        assert isinstance(optimizer, OptimizationEngine)

    @pytest.mark.parametrize("class_count,expected", [
        (0, SynchronousOptimizer),
        (49, SynchronousOptimizer),
        (50, OptimizationEngine),
        (51, OptimizationEngine),
        (200, OptimizationEngine),
    ])
    def test_boundary_conditions(self, router, class_count, expected):
        """测试边界条件"""
        context = {"class_count": class_count}
        optimizer = router.get_optimizer(context)

        assert isinstance(optimizer, expected)
```

### 2. WorkflowEnhancer 测试

```python
from lingflow.integration import WorkflowEnhancer
from lingflow.common.models import Task, TaskPriority

class TestWorkflowEnhancer:
    """测试工作流增强器"""

    @pytest.fixture
    def enhancer(self, orchestrator):
        """创建增强器实例"""
        config = {
            "phase5.enabled": True,
            "phase4.enabled": True,
            "phase5.default_tools": ["semgrep", "ruff"]
        }
        return WorkflowEnhancer(orchestrator, config)

    @pytest.fixture
    def sample_tasks(self):
        """创建示例任务"""
        return [
            Task(
                task_id="review",
                name="code-review",
                description="Review code",
                agent_type="code-reviewer",
                context={"target": "./src"},
                priority=TaskPriority.NORMAL,
                dependencies=[]
            ),
            Task(
                task_id="optimize",
                name="optimize",
                description="Optimize code",
                agent_type="optimizer",
                context={"goal": "structure"},
                priority=TaskPriority.NORMAL,
                dependencies=["review"]
            ),
            Task(
                task_id="test",
                name="test",
                description="Run tests",
                agent_type="tester",
                context={"path": "./tests"},
                priority=TaskPriority.NORMAL,
                dependencies=[]
            )
        ]

    def test_enhance_code_review_task(self, enhancer, sample_tasks):
        """测试增强代码审查任务"""
        enhanced = enhancer.enhance_workflow(sample_tasks)

        review_task = [t for t in enhanced if t.name == "code-review"][0]
        assert review_task.context.get("use_phase5") == True
        assert "semgrep" in review_task.context.get("ai_tools", [])

    def test_enhance_optimize_task(self, enhancer, sample_tasks):
        """测试增强优化任务"""
        enhanced = enhancer.enhance_workflow(sample_tasks)

        optimize_task = [t for t in enhanced if t.name == "optimize"][0]
        assert optimize_task.context.get("use_phase4") == True
        assert optimize_task.context.get("optimization_method") == "bayesian"

    def test_no_enhance_for_other_tasks(self, enhancer, sample_tasks):
        """测试其他任务不增强"""
        enhanced = enhancer.enhance_workflow(sample_tasks)

        test_task = [t for t in enhanced if t.name == "test"][0]
        assert test_task.context.get("use_phase5") is None
        assert test_task.context.get("use_phase4") is None

    def test_phase5_disabled(self, sample_tasks, orchestrator):
        """测试Phase 5禁用时不增强代码审查"""
        config = {"phase5.enabled": False}
        enhancer = WorkflowEnhancer(orchestrator, config)

        enhanced = enhancer.enhance_workflow(sample_tasks)
        review_task = [t for t in enhanced if t.name == "code-review"][0]

        assert review_task.context.get("use_phase5") is None

    def test_preserve_dependencies(self, enhancer, sample_tasks):
        """测试保留任务依赖"""
        enhanced = enhancer.enhance_workflow(sample_tasks)

        optimize_task = [t for t in enhanced if t.name == "optimize"][0]
        assert optimize_task.dependencies == ["review"]
```

### 3. CodeReviewIntegration 测试

```python
from lingflow.integration import CodeReviewIntegration
from lingflow.self_optimizer.phase5 import (
    InMemoryKnowledgeBase,
    RuleExtractor
)
from unittest.mock import Mock, MagicMock

class TestCodeReviewIntegration:
    """测试代码审查集成"""

    @pytest.fixture
    def integration(self, code_reviewer, phase5_system):
        """创建集成实例"""
        config = {
            "phase5.default_tools": ["semgrep", "ruff"],
            "phase5.min_confidence": 0.8
        }
        return CodeReviewIntegration(
            code_reviewer,
            phase5_system,
            config
        )

    def test_enhance_with_ai_tools(self, integration, tmp_path):
        """测试使用AI工具增强"""
        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    pass\n")

        # 模拟反馈收集
        integration._collect_feedback = Mock(return_value=[
            Mock(rule_id="R001", severity="HIGH", message="Test rule")
        ])

        # 模拟规则提取
        integration._extract_rules = Mock(return_value=[
            Mock(id="R001", pattern={}, severity="HIGH", category="CODE_QUALITY")
        ])

        # 模拟规则验证
        integration._validate_rules = Mock(return_value=[
            Mock(id="R001", pattern={}, severity="HIGH", category="CODE_QUALITY")
        ])

        # 执行
        rules = integration.enhance_with_ai_tools(str(tmp_path))

        # 验证
        assert len(rules) == 1
        assert rules[0].id == "R001"

    def test_get_default_tools(self, integration):
        """测试获取默认工具"""
        tools = integration._get_default_tools()

        assert len(tools) == 2
        from lingflow.self_optimizer.phase5.models import FeedbackSource
        assert FeedbackSource.SEMGREP in tools
        assert FeedbackSource.RUFF in tools

    def test_register_rules(self, integration):
        """测试注册规则"""
        rules = [
            Mock(id="R001", pattern={}, severity="HIGH", category="CODE_QUALITY"),
            Mock(id="R002", pattern={}, severity="MEDIUM", category="STYLE")
        ]

        # 模拟规则引擎
        integration.code_reviewer.rule_engine = Mock()

        # 执行
        integration._register_rules(rules)

        # 验证
        assert integration.code_reviewer.rule_engine.add_rule.call_count == 2

    def test_log_error_on_validation_failure(self, integration, tmp_path, caplog):
        """测试验证失败时记录错误"""
        # 模拟验证失败
        rules = [Mock(id="R001")]
        integration._validate_rules = Mock(side_effect=Exception("Validation failed"))

        # 执行（应该不抛出异常）
        with caplog.at_level(logging.WARNING):
            result = integration._validate_rules(rules, str(tmp_path))

        # 验证错误被记录
        assert "Validation failed" in caplog.text
```

---

## 集成测试

### 1. CLI 集成测试

```python
from click.testing import CliRunner
from lingflow.cli import cli

class TestCLIIntegration:
    """测试CLI集成"""

    @pytest.fixture
    def runner(self):
        """创建CLI运行器"""
        return CliRunner()

    def test_optimize_with_phase4(self, runner, tmp_path):
        """测试使用Phase 4优化"""
        with runner.isolated_file_system():
            # 创建测试项目
            project_dir = tmp_path / "project"
            project_dir.mkdir()
            (project_dir / "test.py").write_text("class Foo:\n    pass\n")

            # 运行命令
            result = runner.invoke(cli, [
                "optimize", "run", "structure",
                "--target", str(project_dir),
                "--use-phase4"
            ])

            # 验证
            assert result.exit_code == 0
            assert "最佳参数" in result.output or "best_params" in result.output

    def test_learn_from_tools(self, runner, tmp_path):
        """测试从工具学习"""
        with runner.isolated_file_system():
            # 创建测试项目
            project_dir = tmp_path / "project"
            project_dir.mkdir()
            (project_dir / "test.py").write_text("x = 1\n")

            # 运行命令
            result = runner.invoke(cli, [
                "learn", "from-tools",
                "--target", str(project_dir),
                "--tools", "ruff"
            ])

            # 验证
            assert result.exit_code == 0
            # 根据是否有工具调整断言

    def test_workflow_enhancement(self, runner, tmp_path):
        """测试工作流增强"""
        with runner.isolated_file_system():
            # 创建工作流文件
            workflow_file = tmp_path / "workflow.yaml"
            workflow_file.write_text("""
tasks:
  - name: review
    skill: code-review
    params:
      target: .
            """)

            # 运行命令
            result = runner.invoke(cli, [
                "workflow", str(workflow_file),
                "--enhance"
            ])

            # 验证
            assert result.exit_code == 0

    def test_config_init_with_phase4_phase5(self, runner, tmp_path):
        """测试初始化配置"""
        with runner.isolated_file_system():
            result = runner.invoke(cli, [
                "config", "init",
                "--enable-phase4",
                "--enable-phase5"
            ])

            # 验证配置文件创建
            assert result.exit_code == 0
            # 可以进一步验证配置文件内容
```

### 2. Skill 集成测试

```python
from lingflow.core.skill import SkillRegistry, get_skill
from lingflow.integration.skills import EnhancedCodeReviewSkill

class TestSkillIntegration:
    """测试Skill集成"""

    def test_enhanced_code_review_skill(self):
        """测试增强的代码审查技能"""
        # 获取技能
        skill = get_skill("code-review-enhanced")

        assert skill is not None
        assert isinstance(skill, EnhancedCodeReviewSkill)

    def test_skill_execution_with_phase5(self, tmp_path):
        """测试技能执行（使用Phase 5）"""
        skill = EnhancedCodeReviewSkill()

        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    pass\n")

        # 执行技能
        result = skill.execute({
            "target": str(tmp_path),
            "use_phase5": True,
            "ai_tools": ["ruff"]
        })

        # 验证结果
        assert result.success
        assert "learned_rules" in result.data or "issues" in result.data

    def test_skill_registry_contains_new_skills(self):
        """测试技能注册表包含新技能"""
        registry = SkillRegistry()

        skills = registry.list()

        assert "code-review-enhanced" in skills
        assert "learn" in skills
```

### 3. Hook 集成测试

```python
from lingflow.hooks import OptimizationHooks, ReviewHooks
from lingflow.integration.hooks import Phase4IntegrationHook, Phase5IntegrationHook

class TestHookIntegration:
    """测试Hook集成"""

    def test_optimization_hook_saves_params(self, tmp_path):
        """测试优化Hook保存参数"""
        hook = Phase4IntegrationHook()

        # 模拟优化结果
        result = Mock(
            success=True,
            best_params={"max_class_size": 300},
            best_score=0.5
        )

        context = {
            "project": "test",
            "goal": "structure"
        }

        # 执行Hook
        hook.post_optimization(context, result)

        # 验证参数已保存
        from lingflow.self_optimizer.phase4 import load_params
        saved_params = load_params("test", "structure")

        assert saved_params is not None
        assert saved_params.get("max_class_size") == 300

    def test_review_hook_triggers_learning(self, tmp_path, caplog):
        """测试审查Hook触发学习"""
        hook = Phase5IntegrationHook()

        # 模拟审查结果
        result = Mock(issues_found=10)

        context = {
            "target": str(tmp_path),
            "auto_learn": True
        }

        # 执行Hook
        with caplog.at_level(logging.INFO):
            hook.post_review(context, result)

        # 验证学习被触发
        # 根据实际实现调整断言
```

---

## 端到端测试

### 1. 完整工作流测试

```python
class TestE2EWorkflow:
    """端到端工作流测试"""

    def test_complete_optimization_workflow(self, tmp_path):
        """测试完整优化工作流"""
        # 1. 创建测试项目
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # 创建多个Python文件
        for i in range(10):
            (project_dir / f"module{i}.py").write_text(f"""
class MyClass{i}:
    def method1(self):
        pass

    def method2(self):
        pass

    def method3(self):
        pass
            """)

        # 2. 创建工作流文件
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text(f"""
tasks:
  - name: review
    skill: code-review
    params:
      target: {project_dir}

  - name: optimize
    skill: optimize
    depends_on: [review]
    params:
      goal: structure
      target: {project_dir}
      use_phase4: true
        """)

        # 3. 执行工作流
        from lingflow import LingFlow
        lf = LingFlow()
        result = lf.run_workflow_file(str(workflow_file))

        # 4. 验证结果
        assert result is not None
        assert "review" in result
        assert "optimize" in result

        # 验证优化成功
        optimize_result = result["optimize"]
        assert optimize_result.get("success") is True

    def test_complete_learning_workflow(self, tmp_path):
        """测试完整学习工作流"""
        # 1. 创建测试项目
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        (project_dir / "test.py").write_text("""
x = 1
y = 2
z = 3  # unused
        """)

        # 2. 运行学习
        from lingflow.self_optimizer.phase5 import RuleExtractor
        from lingflow.self_optimizer.phase5.adapters import RuffAdapter

        adapter = RuffAdapter()
        feedback = adapter.run_scan(str(project_dir))

        extractor = RuleExtractor()
        rules = extractor.extract_patterns(feedback)

        # 3. 验证规则学习
        assert len(rules) > 0

        # 4. 应用规则
        from lingflow.code_review import RuleEngine
        engine = RuleEngine()

        for rule in rules:
            engine.add_rule(
                rule_id=rule.id,
                pattern=rule.pattern,
                severity=rule.severity,
                category=rule.category
            )

        # 5. 验证规则注册
        assert len(engine.list_rules()) > 0
```

### 2. 集成场景测试

```python
class TestIntegrationScenarios:
    """集成场景测试"""

    def test_phase4_phase5_collaboration(self, tmp_path):
        """测试Phase 4和Phase 5协作"""
        # 场景: 使用Phase 5学习规则，然后用Phase 4优化参数

        # 1. Phase 5: 学习规则
        from lingflow.integration import CodeReviewIntegration
        integration = CodeReviewIntegration(...)

        rules = integration.enhance_with_ai_tools(
            target_path=str(tmp_path),
            tools=[FeedbackSource.RUFF]
        )

        # 2. Phase 4: 优化参数
        from lingflow.self_optimizer.phase4 import quick_optimize

        result = quick_optimize(
            target=str(tmp_path),
            goal="structure"
        )

        # 3. 验证两者都成功
        assert len(rules) > 0
        assert result.success

    def test_fallback_on_phase4_failure(self, tmp_path):
        """测试Phase 4失败时的回退"""
        # 场景: Phase 4失败，自动回退到传统优化器

        from lingflow.integration import SmartOptimizerRouter
        from unittest.mock import patch

        router = SmartOptimizerRouter({"phase4.enabled": True})

        # 模拟Phase 4失败
        with patch('lingflow.self_optimizer.phase4.OptimizationEngine') as mock_engine:
            mock_engine.side_effect = Exception("Phase 4 failed")

            # 应该回退到传统优化器
            optimizer = router.get_optimizer({"class_count": 100})

            from lingflow.self_optimizer import SynchronousOptimizer
            assert isinstance(optimizer, SynchronousOptimizer)
```

---

## 性能测试

### 1. 优化性能基准测试

```python
import time
import pytest

class TestOptimizationPerformance:
    """优化性能测试"""

    @pytest.mark.parametrize("class_count,max_time", [
        (50, 60),
        (100, 90),
        (200, 120),
    ])
    def test_optimization_time(self, tmp_path, class_count, max_time):
        """测试优化时间"""
        # 创建测试项目
        project_dir = tmp_path / f"project_{class_count}"
        project_dir.mkdir()

        for i in range(class_count):
            (project_dir / f"class{i}.py").write_text(f"""
class Class{i}:
    def method1(self):
        pass
            """)

        # 运行优化
        start_time = time.time()

        from lingflow.self_optimizer.phase4 import quick_optimize
        result = quick_optimize(
            target=str(project_dir),
            goal="structure",
            config={"n_trials": 10}  # 减少试验次数以加快测试
        )

        duration = time.time() - start_time

        # 验证结果和时间
        assert result.success
        assert duration < max_time

    def test_cache_performance(self, tmp_path):
        """测试缓存性能"""
        from lingflow.self_optimizer.phase4 import ParameterCache

        cache = ParameterCache(max_size=100)

        # 第一次调用（无缓存）
        params = {"max_class_size": 300}
        start = time.time()
        cache.set(params, "test", 0.5)
        first_call = time.time() - start

        # 第二次调用（有缓存）
        start = time.time()
        result = cache.get(params, "test")
        second_call = time.time() - start

        # 验证缓存有效
        assert result == 0.5
        assert second_call < first_call
```

### 2. 内存使用测试

```python
import psutil
import os

class TestMemoryUsage:
    """内存使用测试"""

    def test_optimization_memory(self, tmp_path):
        """测试优化内存使用"""
        process = psutil.Process(os.getpid())

        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 创建测试项目
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        for i in range(100):
            (project_dir / f"module{i}.py").write_text("""
class Foo:
    pass
            """)

        # 运行优化
        from lingflow.self_optimizer.phase4 import quick_optimize
        result = quick_optimize(
            target=str(project_dir),
            goal="structure",
            config={"n_trials": 5}
        )

        # 记录峰值内存
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # 验证内存增长在合理范围内
        assert memory_increase < 100  # 不应超过100MB
        assert result.success
```

---

## 测试数据

### 1. 测试项目结构

```
tests/fixtures/
├── small_project/          # 30个类
│   ├── module1.py
│   ├── module2.py
│   └── ...
├── medium_project/         # 100个类
│   ├── package1/
│   │   ├── module1.py
│   │   └── ...
│   └── package2/
│       └── ...
├── large_project/          # 200个类
│   └── ...
└── workflows/
    ├── basic_workflow.yaml
    ├── enhanced_workflow.yaml
    └── learning_workflow.yaml
```

### 2. 测试数据生成器

```python
import pytest

@pytest.fixture
def generate_test_project(tmp_path):
    """生成测试项目"""
    def _generate(class_count: int, methods_per_class: int = 3):
        project_dir = tmp_path / f"project_{class_count}"
        project_dir.mkdir(exist_ok=True)

        for i in range(class_count):
            module_file = project_dir / f"module{i}.py"

            methods = "\n".join([
                f"    def method{j}(self):\n        pass"
                for j in range(methods_per_class)
            ])

            module_file.write_text(f"""
class Class{i}:
{methods}
            """)

        return project_dir

    return _generate
```

---

## 测试运行

### 运行所有测试

```bash
# 运行所有测试
pytest tests/integration/

# 运行特定测试文件
pytest tests/integration/test_integration.py

# 运行特定测试类
pytest tests/integration/test_integration.py::TestSmartOptimizerRouter

# 运行特定测试方法
pytest tests/integration/test_integration.py::TestSmartOptimizerRouter::test_large_project_uses_phase4

# 带覆盖率报告
pytest tests/integration/ --cov=lingflow/integration --cov-report=html
```

### 性能基准测试

```bash
# 运行性能测试
pytest tests/integration/test_performance.py --benchmark-only

# 生成性能报告
pytest tests/integration/test_performance.py --benchmark-json=benchmark.json
```

---

**测试版本**: v1.0
**最后更新**: 2026-03-31
