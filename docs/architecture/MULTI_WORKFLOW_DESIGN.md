# 双/多工程流系统配置方案

**版本**: v1.0
**日期**: 2026-03-31
**状态**: 设计提案

---

## 📋 目录

1. [概念定义](#概念定义)
2. [架构设计](#架构设计)
3. [配置方案](#配置方案)
4. [使用场景](#使用场景)
5. [实现路径](#实现路径)

---

## 🎯 概念定义

### 双工程流系统 (Dual-Workflow)

**定义**: 两条并行的工程流线，各司其职又相互协作

**典型模式**:
```
┌─────────────────────────────────┐
│   快速工程流 (Fast-Track)       │  ← 速度优先，快速迭代
│   - YOLO模式                    │
│   - 实验性功能                   │
│   - 快速修复                    │
└─────────────────────────────────┘
           ↕ 协作
┌─────────────────────────────────┐
│   稳定工程流 (Stable-Track)      │  ← 质量优先，严格审查
│   - 完整测试                     │
│   - 代码审查                    │
│   - 生产就绪                    │
└─────────────────────────────────┘
```

### 多工程流系统 (Multi-Workflow)

**定义**: 多条并行的专业工程流线，按需协作

**典型模式**:
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 开发流       │  │ 测试流       │  │ 文档流       │
│ Dev-Flow     │  │ Test-Flow    │  │ Doc-Flow     │
└──────────────┘  └──────────────┘  └──────────────┘
       ↓                 ↓                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 优化流       │  │ 审查流       │  │ 部署流       │
│ Optimize-Flow│  │ Review-Flow  │  │ Deploy-Flow  │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🏗️ 架构设计

### 核心组件

```python
lingflow/
├── workflow/
│   ├── orchestrator.py          # 现有：工作流编排器
│   ├── multi_workflow.py        # 新增：多工程流协调器
│   ├── workflow_base.py         # 新增：工程流基类
│   └── strategies/              # 新增：工程流策略
│       ├── fast_track.py        # 快速工程流
│       ├── stable_track.py      # 稳定工程流
│       ├── test_track.py        # 测试工程流
│       └── doc_track.py         # 文档工程流
├── coordination/
│   ├── coordinator.py           # 现有：Agent协调器
│   ├── workflow_coordinator.py  # 新增：工程流协调器
│   └── sync_manager.py          # 新增：同步管理器
└── config/
    ├── workflows/               # 新增：工程流配置
    │   ├── dual_workflow.yaml   # 双工程流配置
    │   ├── multi_workflow.yaml  # 多工程流配置
    │   └── strategies/          # 策略配置
    └── workflow_templates/      # 工程流模板
```

### 类设计

```python
# lingflow/workflow/workflow_base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum

class WorkflowType(Enum):
    """工程流类型"""
    FAST = "fast"              # 快速工程流
    STABLE = "stable"          # 稳定工程流
    TEST = "test"              # 测试工程流
    DOCUMENTATION = "doc"      # 文档工程流
    OPTIMIZATION = "optimize"  # 优化工程流
    REVIEW = "review"          # 审查工程流

class WorkflowPriority(Enum):
    """工程流优先级"""
    CRITICAL = 0   # 关键路径
    HIGH = 1       # 高优先级
    NORMAL = 2     # 正常优先级
    LOW = 3        # 低优先级

class BaseWorkflow(ABC):
    """工程流基类"""

    def __init__(
        self,
        workflow_id: str,
        workflow_type: WorkflowType,
        priority: WorkflowPriority = WorkflowPriority.NORMAL
    ):
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.priority = priority
        self.tasks: List[Task] = []
        self.status = WorkflowStatus.PENDING
        self.dependencies: List[str] = []

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> WorkflowResult:
        """执行工程流"""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """验证工程流配置"""
        pass

    def add_dependency(self, workflow_id: str) -> None:
        """添加依赖的工程流"""
        if workflow_id not in self.dependencies:
            self.dependencies.append(workflow_id)

# lingflow/workflow/multi_workflow.py

class MultiWorkflowCoordinator:
    """多工程流协调器

    管理多条工程流的并行执行、依赖关系和资源调度
    """

    def __init__(self, max_parallel_workflows: int = 3):
        self.workflows: Dict[str, BaseWorkflow] = {}
        self.max_parallel = max_parallel_workflows
        self.execution_graph = WorkflowGraph()
        self.resource_manager = WorkflowResourceManager()

    def register_workflow(self, workflow: BaseWorkflow) -> None:
        """注册工程流"""
        self.workflows[workflow.workflow_id] = workflow
        self.execution_graph.add_node(workflow)

    async def execute_all(
        self,
        strategy: ExecutionStrategy = ExecutionStrategy.PARALLEL
    ) -> Dict[str, WorkflowResult]:
        """执行所有工程流

        Args:
            strategy: 执行策略
                - PARALLEL: 并行执行所有工程流
                - SEQUENTIAL: 按依赖顺序执行
                - HYBRID: 混合模式（关键路径优先）
        """
        if strategy == ExecutionStrategy.PARALLEL:
            return await self._execute_parallel()
        elif strategy == ExecutionStrategy.SEQUENTIAL:
            return await self._execute_sequential()
        else:
            return await self._execute_hybrid()

    async def _execute_parallel(self) -> Dict[str, WorkflowResult]:
        """并行执行策略"""
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_limit(workflow: BaseWorkflow):
            async with semaphore:
                return await workflow.execute({})

        tasks = [
            execute_with_limit(wf)
            for wf in self.workflows.values()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._process_results(results)

    async def _execute_hybrid(self) -> Dict[str, WorkflowResult]:
        """混合执行策略：关键路径优先"""
        # 1. 识别关键路径（高优先级 + 无依赖）
        critical_workflows = [
            wf for wf in self.workflows.values()
            if wf.priority == WorkflowPriority.CRITICAL
            and not wf.dependencies
        ]

        # 2. 并行执行关键路径
        critical_results = await self._execute_workflows(critical_workflows)

        # 3. 执行依赖已满足的其他工程流
        remaining_workflows = self._get_ready_workflows(critical_results)
        remaining_results = await self._execute_workflows(remaining_workflows)

        return {**critical_results, **remaining_results}
```

---

## ⚙️ 配置方案

### 1. 双工程流配置 (dual_workflow.yaml)

```yaml
name: lingflow 双工程流系统
description: 快速工程流 + 稳定工程流
version: "1.0"

# 全局配置
global:
  max_parallel_workflows: 2
  sync_strategy: "event_based"  # event_based | polling | hybrid
  conflict_resolution: "priority"  # priority | manual | merge

# 工程流定义
workflows:
  # 快速工程流
  - id: fast_track
    name: 快速工程流
    type: fast
    priority: high
    description: |
      快速迭代模式，用于：
      - YOLO模式开发
      - 实验性功能
      - 快速原型验证
      - 紧急修复

    config:
      # 跳过的时间消耗步骤
      skip_steps:
        - full_test_suite
        - code_review
        - documentation

      # 保留的核心步骤
      required_steps:
        - syntax_check
        - unit_test
        - basic_integration

      # 质量阈值（较低）
      quality_thresholds:
        test_coverage: 0.30      # 30%
        code_quality: 6.0        # Pylint 6.0
        performance_check: false

      # 提交策略
      commit_strategy:
        auto_commit: true
        commit_message_prefix: "[YOLO]"
        bypass_hooks: true

    tasks:
      - id: quick_syntax_check
        skill: syntax-checker
        params:
          files: "{{context.changed_files}}"

      - id: focused_unit_tests
        skill: test-runner
        params:
          tests: "{{context.related_tests}}"
          coverage_target: 0.30

      - id: basic_integration_test
        skill: integration-test
        params:
          test_suite: "smoke"
          timeout: 60

    triggers:
      - type: manual
        command: "yolo"
      - type: label
        label: "yo lo"

  # 稳定工程流
  - id: stable_track
    name: 稳定工程流
    type: stable
    priority: critical
    description: |
      稳定发布模式，用于：
      - 生产代码
      - 重要功能
      - 长期维护

    config:
      # 完整的质量检查
      required_steps:
        - syntax_check
        - linting
        - unit_test
        - integration_test
        - e2e_test
        - code_review
        - security_scan
        - documentation
        - performance_test

      # 质量阈值（严格）
      quality_thresholds:
        test_coverage: 0.70      # 70%
        code_quality: 9.0        # Pylint 9.0
        performance_check: true
        security_scan: true

      # 审批策略
      approval_strategy:
        require_review: true
        min_reviewers: 1
        auto_approve_checks: true

    tasks:
      - id: full_syntax_check
        skill: syntax-checker
        params:
          files: "all"

      - id: comprehensive_lint
        skill: linter
        params:
          tools: [pylint, flake8, mypy]
          threshold: 9.0

      - id: full_test_suite
        skill: test-suite
        params:
          coverage_target: 0.70
          timeout: 300

      - id: code_review
        skill: code-reviewer
        params:
          reviewers: ["@senior-dev"]
          min_approvals: 1

      - id: security_scan
        skill: security-scanner
        params:
          tools: [bandit, semgrep]
          severity_threshold: "medium"

      - id: documentation_check
        skill: doc-validator
        params:
          check_coverage: true
          check_examples: true

    triggers:
      - type: branch
        branch: "main"
      - type: label
        label: "ready for production"

# 工程流间协作规则
collaboration:
  # 快速流 → 稳定流的提升机制
  promotion:
    - from: fast_track
      to: stable_track
      condition: |
        tasks.fast_track.success == true AND
        context.promotion_requested == true
      required_actions:
        - run_full_tests
        - code_review
        - update_docs

  # 状态同步
  sync:
    - type: artifact_sync
      workflows: [fast_track, stable_track]
      artifacts:
        - test_results
        - coverage_reports
        - metrics

    - type: status_broadcast
      source: stable_track
      event: "completion"
      targets: [fast_track]
```

### 2. 多工程流配置 (multi_workflow.yaml)

```yaml
name: lingflow 多工程流系统
description: 专业工程流分工协作
version: "1.0"

global:
  max_parallel_workflows: 5
  resource_limits:
    max_cpu: 80
    max_memory: 16  # GB
    max_io: 70

workflows:
  # 开发工程流
  - id: dev_flow
    name: 开发工程流
    type: dev
    priority: critical
    description: 核心开发流程

    config:
      focus: "feature_development"
      quality_mode: "balanced"
      auto_commit: false

    tasks:
      - id: code_generation
        skill: code-generator
      - id: syntax_check
        skill: syntax-checker
      - id: unit_test
        skill: test-runner
        params:
          coverage_target: 0.50

    triggers:
      - type: push
        branches: [feature/*, develop]

  # 测试工程流
  - id: test_flow
    name: 测试工程流
    type: test
    priority: high
    description: 全面测试流程

    config:
      focus: "quality_assurance"
      test_types:
        - unit
        - integration
        - e2e
        - performance
      parallel_tests: true

    tasks:
      - id: unit_tests
        skill: test-suite
        params:
          type: unit
          coverage_target: 0.70

      - id: integration_tests
        skill: test-suite
        params:
          type: integration
          timeout: 120

      - id: e2e_tests
        skill: test-suite
        params:
          type: e2e
          timeout: 300

      - id: performance_tests
        skill: performance-test
        params:
          benchmarks: true
          profiling: true

    dependencies: [dev_flow]
    triggers:
      - type: event
        event: "dev_flow.completed"

  # 文档工程流
  - id: doc_flow
    name: 文档工程流
    type: documentation
    priority: normal
    description: 文档生成与更新

    config:
      auto_generate: true
      doc_types:
        - api
        - user_guide
        - examples
      language: "zh-CN"

    tasks:
      - id: extract_api_docs
        skill: api-doc-generator
        params:
          output_format: "markdown"

      - id: generate_examples
        skill: example-generator
        params:
          min_examples: 3

      - id: validate_docs
        skill: doc-validator
        params:
          check_links: true
          check_spelling: true

    dependencies: [dev_flow]
    triggers:
      - type: schedule
        cron: "0 */6 * * *"  # 每6小时
      - type: event
        event: "dev_flow.completed"

  # 优化工程流
  - id: optimize_flow
    name: 优化工程流
    type: optimization
    priority: normal
    description: 代码质量优化

    config:
      optimization_targets:
        - performance
        - memory
        - code_size
      auto_apply: false  # 需要审查

    tasks:
      - id: analyze_code
        skill: code-analyzer
        params:
          metrics:
            - complexity
            - duplication
            - dead_code

      - id: generate_optimizations
        skill: code-optimizer
        params:
          strategy: "safe"

      - id: validate_optimizations
        skill: optimization-validator
        params:
          regression_tests: true

    triggers:
      - type: schedule
        cron: "0 2 * * *"  # 每天凌晨2点
      - type: manual
        command: "optimize"

  # 审查工程流
  - id: review_flow
    name: 审查工程流
    type: review
    priority: high
    description: 代码审查流程

    config:
      auto_assign: true
      required_reviewers: 1
      check_rules:
        - security
        - best_practices
        - architecture

    tasks:
      - id: security_review
        skill: security-reviewer
        params:
          severity: "medium"

      - id: architecture_review
        skill: architecture-reviewer
        params:
          check_solid: true
          check_patterns: true

      - id: best_practices_review
        skill: practices-reviewer
        params:
          style_guide: "PEP8"

    dependencies: [dev_flow]
    triggers:
      - type: label
        label: "ready for review"

  # 部署工程流
  - id: deploy_flow
    name: 部署工程流
    type: deploy
    priority: critical
    description: 生产部署流程

    config:
      deployment_strategy: "blue_green"
      pre_deployment_checks: true
      post_deployment_monitoring: true

    tasks:
      - id: pre_deployment_check
        skill: deployment-checker
        params:
          checks:
            - health_check
            - capacity_check
            - dependency_check

      - id: create_backup
        skill: backup-creator
        params:
          retention_days: 7

      - id: deploy
        skill: deployer
        params:
          strategy: "blue_green"
          health_check_timeout: 300

      - id: post_deployment_test
        skill: smoke-test
        params:
          critical_path_only: true

      - id: monitor_deployment
        skill: deployment-monitor
        params:
          duration: 1800  # 30分钟
          alert_on_failure: true

    dependencies: [test_flow, review_flow]
    triggers:
      - type: approval
        required_approvers: 2
      - type: branch
        branch: "main"

# 工程流协作网络
collaboration_network:
  # 并行执行组
  parallel_groups:
    - group: post_dev_parallel
      workflows: [test_flow, doc_flow, review_flow]
      condition: "dev_flow.completed"

    - group: optimization_tasks
      workflows: [optimize_flow, doc_flow]
      condition: "time_window == maintenance"

  # 数据流
  data_flow:
    - from: dev_flow
      to: [test_flow, doc_flow, review_flow]
      data:
        - changed_files
        - test_results
        - coverage_report

    - from: test_flow
      to: deploy_flow
      data:
        - test_report
        - quality_gate_status

  # 事件流
  event_flow:
    - source: test_flow
      event: "failure"
      action: "notify_dev_flow"
      targets: [dev_flow]

    - source: optimize_flow
      event: "optimization_ready"
      action: "request_review"
      targets: [review_flow]
```

### 3. 使用示例

```python
# 示例1: 使用双工程流系统

from lingflow.workflow import MultiWorkflowCoordinator
from lingflow.workflow.strategies import FastTrackWorkflow, StableTrackWorkflow

# 初始化协调器
coordinator = MultiWorkflowCoordinator(max_parallel_workflows=2)

# 创建工程流
fast_track = FastTrackWorkflow(
    workflow_id="fast_001",
    context={"files": ["src/module.py"]},
    config={"skip_tests": True}
)

stable_track = StableTrackWorkflow(
    workflow_id="stable_001",
    context={"files": ["src/core.py"]},
    config={"full_validation": True}
)

# 注册工程流
coordinator.register_workflow(fast_track)
coordinator.register_workflow(stable_track)

# 执行：并行策略
results = await coordinator.execute_all(
    strategy=ExecutionStrategy.PARALLEL
)

print(f"Fast Track: {results['fast_001'].status}")
print(f"Stable Track: {results['stable_001'].status}")

# 快速流提升到稳定流
if fast_track.is_promotable():
    stable_from_fast = stable_track.promote_from(fast_track)
    await coordinator.execute_workflow(stable_from_fast)


# 示例2: 使用多工程流系统

from lingflow.workflow import MultiWorkflowCoordinator
from lingflow.workflow.strategies import (
    DevWorkflow,
    TestWorkflow,
    DocWorkflow,
    OptimizeWorkflow,
    ReviewWorkflow,
    DeployWorkflow
)

# 创建工程流
workflows = [
    DevWorkflow("dev_001", context={"feature": "new-api"}),
    TestWorkflow("test_001", dependencies=["dev_001"]),
    DocWorkflow("doc_001", dependencies=["dev_001"]),
    OptimizeWorkflow("opt_001"),  # 独立运行
    ReviewWorkflow("review_001", dependencies=["dev_001"]),
    DeployWorkflow("deploy_001", dependencies=["test_001", "review_001"])
]

# 注册所有工程流
for wf in workflows:
    coordinator.register_workflow(wf)

# 执行：混合策略（关键路径优先）
results = await coordinator.execute_all(
    strategy=ExecutionStrategy.HYBRID
)

# 检查结果
for wf_id, result in results.items():
    if result.success:
        print(f"✅ {wf_id}: {result.execution_time:.2f}s")
    else:
        print(f"❌ {wf_id}: {result.error}")
```

---

## 🎯 使用场景

### 场景1: 快速原型 + 稳定发布

**需求**: 需要快速验证新功能，同时保持主分支稳定

**方案**: 双工程流系统

```yaml
# feature-quick 分支使用快速流
git push origin feature-quick
# → 触发 fast_track
# → 跳过完整测试
# → 快速合并到 develop

# main 分支使用稳定流
git push origin main
# → 触发 stable_track
# → 完整测试 + 审查
# → 生产就绪
```

### 场景2: 开发 + 测试 + 文档并行

**需求**: 功能开发时同时进行测试和文档编写

**方案**: 多工程流系统（并行组）

```yaml
parallel_groups:
  - group: dev_with_test_and_doc
    workflows: [dev_flow, test_flow, doc_flow]
    trigger: "push to develop"
```

### 场景3: 夜间自动优化

**需求**: 非工作时间自动优化代码

**方案**: 定时触发的优化工程流

```yaml
optimize_flow:
  triggers:
    - type: schedule
      cron: "0 2 * * *"  # 每天凌晨2点
```

### 场景4: 紧急修复流程

**需求**: 生产问题需要快速修复

**方案**: 快速工程流 + 简化流程

```bash
# 标记为紧急修复
git label add "hotfix" --push origin
# → 触发 fast_track（hotfix模式）
# → 最小测试（smoke test）
# → 快速部署
```

---

## 🚀 实现路径

### 阶段1: 基础框架 (1周)

- [ ] 创建 `BaseWorkflow` 抽象类
- [ ] 实现 `MultiWorkflowCoordinator`
- [ ] 添加工作流配置加载
- [ ] 基础测试

### 阶段2: 双工程流 (1周)

- [ ] 实现 `FastTrackWorkflow`
- [ ] 实现 `StableTrackWorkflow`
- [ ] 工程流间提升机制
- [ ] 配置文件和文档

### 阶段3: 多工程流 (2周)

- [ ] 实现 `DevWorkflow`
- [ ] 实现 `TestWorkflow`
- [ ] 实现 `DocWorkflow`
- [ ] 实现 `OptimizeWorkflow`
- [ ] 实现 `ReviewWorkflow`
- [ ] 实现 `DeployWorkflow`

### 阶段4: 高级特性 (1周)

- [ ] 工程流依赖图
- [ ] 资源管理和调度
- [ ] 事件驱动协作
- [ ] 冲突检测和解决

### 阶段5: 集成和优化 (1周)

- [ ] 与现有系统集成
- [ ] 性能优化
- [ ] 监控和日志
- [ ] 完整文档

**总计**: 6周

---

## 📊 预期效果

### 效率提升

| 指标 | 当前 | 双工程流 | 多工程流 |
|------|------|---------|---------|
| 开发迭代速度 | 1x | 1.5x | 2x |
| 测试覆盖率 | 44% | 50%+ | 70%+ |
| 文档完整性 | 60% | 70% | 90%+ |
| 代码质量 | 7.5 | 8.0 | 9.0+ |

### 质量改善

- ✅ **快速原型**: YOLO模式快速验证想法
- ✅ **稳定发布**: 严格流程保证质量
- ✅ **专业分工**: 各工程流专注自身领域
- ✅ **并行协作**: 多流程并行提升效率
- ✅ **自动化**: 减少人工干预

---

## 🔗 相关文件

- 现有架构: `docs/WORKFLOW_COMPREHENSIVE.md`
- Agent协调: `docs/AGENT_COORDINATION_GUIDE.md`
- 工作流API: `site/api/workflow/index.html`

---

**设计状态**: ✅ 完成

**下一步**: 实现阶段1（基础框架）

**众智混元，万法灵通** ⚡🚀
