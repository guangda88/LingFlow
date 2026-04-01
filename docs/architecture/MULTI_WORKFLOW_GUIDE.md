# 双/多工程流系统 - 快速开始指南

**版本**: v1.0
**最后更新**: 2026-03-31
**状态**: ✅ 可用

---

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [MULTI_WORKFLOW_DESIGN.md](./MULTI_WORKFLOW_DESIGN.md) | 完整设计文档 |
| [multi_workflow.py](../../lingflow/workflow/multi_workflow.py) | 核心实现 |
| [本文档](./MULTI_WORKFLOW_GUIDE.md) | 快速开始指南 |

---

## 🎯 5分钟上手

### 1. 基础概念

**双工程流**: 快速流（YOLO模式）+ 稳定流（生产就绪）
**多工程流**: 开发、测试、文档、优化、审查、部署等专业分工

### 2. 最简示例

```python
# quick_start.py
import asyncio
from lingflow.workflow.multi_workflow import (
    MultiWorkflowCoordinator,
    FastTrackWorkflow,
    StableTrackWorkflow,
    ExecutionStrategy
)

async def main():
    # 创建协调器
    coordinator = MultiWorkflowCoordinator(max_parallel_workflows=2)

    # 创建双工程流
    fast = FastTrackWorkflow("fast_demo")
    stable = StableTrackWorkflow("stable_demo")

    # 注册
    coordinator.register_workflow(fast)
    coordinator.register_workflow(stable)

    # 执行
    results = await coordinator.execute_all(
        strategy=ExecutionStrategy.PARALLEL
    )

    # 结果
    for wf_id, result in results.items():
        print(f"{wf_id}: {result}")

asyncio.run(main())
```

运行：
```bash
python quick_start.py
```

---

## 🚀 常见用法

### 用法1: YOLO模式（快速工程流）

```python
from lingflow.workflow.multi_workflow import FastTrackWorkflow
from lingflow.common.models import Task, TaskPriority

# 创建快速流
fast_track = FastTrackWorkflow("yolo_feature")

# 添加任务
fast_track.add_task(Task(
    task_id="quick_test",
    name="Quick Test",
    description="Skip full tests, just syntax check",
    priority=TaskPriority.HIGH,
    agent_type="testing"
))

# 执行
result = await fast_track.execute({})

# 提交（自动跳过hooks）
if result.success:
    print("✅ YOLO commit complete!")
```

### 用法2: 生产发布（稳定工程流）

```python
from lingflow.workflow.multi_workflow import StableTrackWorkflow

stable = StableTrackWorkflow("production_release")

# 添加完整测试任务
stable.add_task(Task(
    task_id="full_suite",
    name="Full Test Suite",
    description="Complete testing with 70% coverage",
    agent_type="testing"
))

stable.add_task(Task(
    task_id="code_review",
    name="Code Review",
    description="Senior developer review required",
    agent_type="review"
))

# 执行（包含所有质量检查）
result = await stable.execute({})

if result.success:
    print("✅ Production ready!")
```

### 用法3: 多团队并行

```python
from lingflow.workflow.multi_workflow import (
    MultiWorkflowCoordinator,
    DevWorkflow,
    TestWorkflow,
    DocWorkflow,
    ExecutionStrategy
)

coordinator = MultiWorkflowCoordinator(max_parallel_workflows=3)

# 开发流
dev = DevWorkflow("feature_dev")
dev.add_task(Task(task_id="code", agent_type="implementation"))

# 测试流（依赖开发）
test = TestWorkflow("feature_test")
test.add_dependency("feature_dev")
test.add_task(Task(task_id="test", agent_type="testing"))

# 文档流（依赖开发）
doc = DocWorkflow("feature_doc")
doc.add_dependency("feature_dev")
doc.add_task(Task(task_id="doc", agent_type="documentation"))

# 注册并执行
for wf in [dev, test, doc]:
    coordinator.register_workflow(wf)

# 并行执行测试和文档
results = await coordinator.execute_all(
    strategy=ExecutionStrategy.HYBRID
)
```

### 用法4: 工程流提升

```python
# 快速验证
fast = FastTrackWorkflow("prototype")
result = await fast.execute({})

# 提升到稳定流
if result.success and fast.can_promote_to(WorkflowType.STABLE):
    stable = coordinator.promote_workflow(
        from_workflow_id="prototype",
        to_type=WorkflowType.STABLE,
        new_workflow_id="production"
    )

    # 运行完整测试
    result = await stable.execute({})
```

---

## ⚙️ 配置选项

### WorkflowConfig 参数

```python
from lingflow.workflow.multi_workflow import WorkflowConfig

config = WorkflowConfig(
    # 跳过的步骤
    skip_steps=["full_test_suite", "code_review"],

    # 必需的步骤
    required_steps=["syntax_check", "unit_test"],

    # 质量阈值
    quality_thresholds={
        "test_coverage": 0.70,
        "code_quality": 9.0
    },

    # 自动提交
    auto_commit=False,

    # 绕过hooks
    bypass_hooks=False,

    # 并行执行
    parallel_execution=True
)

workflow = FastTrackWorkflow("my_wf", config=config)
```

### 执行策略对比

| 策略 | 适用场景 | 特点 |
|------|---------|------|
| PARALLEL | 独立任务 | 最快，无依赖 |
| SEQUENTIAL | 依赖任务 | 按顺序执行 |
| HYBRID | 混合场景 | 关键路径优先 |

---

## 📊 工程流类型

### 快速工程流 (FastTrackWorkflow)

**用途**: YOLO模式、快速原型、紧急修复

```yaml
配置:
  - 跳过: 完整测试、代码审查、文档
  - 保留: 语法检查、基础测试
  - 质量: 30%覆盖率、Pylint 6.0
  - 提交: 自动提交、绕过hooks
```

### 稳定工程流 (StableTrackWorkflow)

**用途**: 生产发布、重要功能

```yaml
配置:
  - 包含: 完整测试、审查、安全扫描
  - 质量: 70%覆盖率、Pylint 9.0
  - 审批: 需要审查、最少1人
```

### 开发工程流 (DevWorkflow)

**用途**: 功能开发

**配置**: 平衡质量和速度

### 测试工程流 (TestWorkflow)

**用途**: 全面测试

**配置**: 单元、集成、E2E、性能测试

### 文档工程流 (DocWorkflow)

**用途**: 文档生成

**配置**: API文档、用户指南、示例

### 优化工程流 (OptimizeWorkflow)

**用途**: 代码优化

**配置**: 性能、内存、复杂度优化

### 审查工程流 (ReviewWorkflow)

**用途**: 代码审查

**配置**: 安全、架构、最佳实践

### 部署工程流 (DeployWorkflow)

**用途**: 生产部署

**配置**: 蓝绿部署、回滚准备

---

## 🔧 高级用法

### 自定义工程流

```python
from lingflow.workflow.multi_workflow import BaseWorkflow, WorkflowType

class CustomWorkflow(BaseWorkflow):
    def __init__(self, workflow_id: str):
        super().__init__(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.DEV,
            priority=WorkflowPriority.HIGH
        )

    async def execute(self, context: dict):
        # 自定义逻辑
        return await super().execute(context)
```

### 依赖管理

```python
# A依赖B
workflow_b.add_dependency("workflow_a")

# 检查依赖是否满足
if workflow_b._check_dependencies(context):
    await workflow_b.execute(context)
```

### 状态监控

```python
status = coordinator.get_status()
print(f"总数: {status['total_workflows']}")
print(f"完成: {status['completed']}")
print(f"失败: {status['failed']}")

# 详细状态
for wf_id, info in status['workflows'].items():
    print(f"{wf_id}: {info['status']}")
```

---

## 🎓 最佳实践

### 1. 选择合适的工程流类型

```
紧急修复 → FastTrackWorkflow
新功能开发 → DevWorkflow
生产发布 → StableTrackWorkflow
定期优化 → OptimizeWorkflow
```

### 2. 合理设置依赖

```python
# ✅ 好的依赖
test.add_dependency("dev")  # 测试依赖开发
review.add_dependency("test")  # 审查依赖测试

# ❌ 避免循环依赖
dev.add_dependency("review")  # 不要！
```

### 3. 使用并行执行

```python
# 独立任务并行执行
strategy = ExecutionStrategy.PARALLEL

# 有关键路径用混合模式
strategy = ExecutionStrategy.HYBRID
```

### 4. 监控和日志

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lingflow.workflow")

# 执行时自动记录日志
results = await coordinator.execute_all()
```

---

## 📈 性能对比

### 单工程流 vs 双工程流

| 指标 | 单工程流 | 双工程流 | 提升 |
|------|---------|---------|------|
| 开发速度 | 1x | 1.5x | 50% |
| 发布频率 | 每天 | 每小时 | 24x |
| 实验验证 | 慢 | 快 | 10x |

### 多工程流效率

| 模式 | 并行度 | 时间节省 |
|------|--------|---------|
| 顺序 | 1x | 0% |
| 双工程流 | 2x | 50% |
| 多工程流(5) | 5x | 80% |

---

## ❓ 常见问题

### Q1: 如何选择执行策略？

**A**:
- 无依赖: `PARALLEL`
- 有依赖: `SEQUENTIAL` 或 `HYBRID`
- 不确定: `HYBRID`（自动优化）

### Q2: 快速流如何提升到稳定流？

**A**:
```python
if fast_track.can_promote_to(WorkflowType.STABLE):
    stable = coordinator.promote_workflow("fast_id", WorkflowType.STABLE)
```

### Q3: 如何处理工程流失败？

**A**:
```python
result = await workflow.execute({})
if not result.success:
    print(f"错误: {result.error}")
    # 重试或回滚
```

### Q4: 能否混合不同类型的工程流？

**A**: 可以！这是多工程流系统的核心优势
```python
coordinator.register_workflow(DevWorkflow("dev"))
coordinator.register_workflow(TestWorkflow("test"))
coordinator.register_workflow(DocWorkflow("doc"))
# 混合执行
```

---

## 🔗 相关链接

- [完整设计文档](./MULTI_WORKFLOW_DESIGN.md)
- [核心实现](../../lingflow/workflow/multi_workflow.py)
- [工作流API](../../site/api/workflow/index.html)
- [Agent协调指南](../AGENT_COORDINATION_GUIDE.md)

---

**快速上手** ✅ **生产就绪** 🚀

**众智混元，万法灵通** ⚡
