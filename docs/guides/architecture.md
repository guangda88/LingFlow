# lingflow 架构概览

本文档详细说明lingflow系统的架构设计和核心组件。

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        lingflow 系统                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Agent     │  │  Workflow   │  │   Context   │         │
│  │  Coordination│  │  Orchestrator│  │  Manager    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                  ┌───────▼───────┐                          │
│                  │  lingflow     │                          │
│                  │  Core Engine  │                          │
│                  └───────┬───────┘                          │
│                          │                                  │
│  ┌─────────────┐  ┌──────┴──────┐  ┌─────────────┐         │
│  │   Self      │  │   Guardrail │  │  Monitoring │         │
│  │ Optimizer   │  │   System    │  │   System    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Agent协调系统 (Coordination)

**职责**: 管理和协调多个AI Agent的工作

```
lingflow/coordination/
├── agent.py           # Agent基类和实现
├── coordinator.py     # Agent协调器
├── base.py           # 基础抽象类
└── registry.py       # Agent注册表
```

**核心类**:

- `BaseAgent`: Agent基类
  - `execute_skill()`: 执行技能
  - `get_status()`: 获取状态
  - `shutdown()`: 优雅关闭

- `AgentCoordinator`: 协调器
  - `register_agent()`: 注册Agent
  - `execute_skill()`: 执行技能
  - `coordinate_agents()`: 协调多Agent

- `AgentRegistry`: 注册表
  - `register()`: 注册
  - `get()`: 获取Agent
  - `list()`: 列出所有Agent

### 2. 工作流引擎 (Workflow)

**职责**: 编排和执行复杂的工作流

```
lingflow/workflow/
├── orchestrator.py    # 工作流编排器
└── cache.py          # 执行缓存
```

**核心类**:

- `WorkflowOrchestrator`: 编排器
  - `load_workflow_from_yaml()`: 加载YAML工作流
  - `execute()`: 执行工作流
  - `validate_workflow()`: 验证工作流

**工作流格式**:

```yaml
name: "工作流名称"
tasks:
  - name: "任务1"
    agent: "agent_name"
    skill: "skill_name"
    params: {}
    depends_on: []
```

### 3. 上下文管理 (Context)

**职责**: 管理系统上下文和状态

```
lingflow/context/
├── manager.py        # 上下文管理器
├── session.py        # 会话管理
└── auto_resume.py    # 自动恢复
```

**核心类**:

- `ContextManager`: 管理器
  - `compress_now()`: 压缩上下文
  - `save_session()`: 保存会话
  - `load_session()`: 加载会话

- `SmartCompressor`: 智能压缩器
  - `compress()`: 压缩内容
  - `should_compress()`: 判断是否需要压缩

### 4. 自优化系统 (Self Optimizer)

**职责**: 自动优化系统参数和学习改进

```
lingflow/self_optimizer/
├── optimizer.py      # 优化器核心
├── evaluator.py      # 评估器
├── trigger.py        # 触发器
├── advisor.py        # 顾问
├── config.py         # 配置管理
├── phase4/           # Phase 4: 参数优化
│   ├── optuna_adapter.py
│   ├── param_space.py
│   └── optimization_loop.py
└── phase5/           # Phase 5: AI学习
    ├── learning_engine.py
    ├── feedback_collector.py
    └── knowledge_base.py
```

**Phase 4: 参数优化**

- 使用Optuna进行参数优化
- 支持多目标优化
- 自动超参数调优

**Phase 5: AI学习**

- 收集反馈数据
- 持续学习和改进
- 知识库管理

### 5. 安全防护系统 (Guardrail)

**职责**: 确保系统安全和合规

```
lingflow/guardrail/
├── safety.py         # 安全检查
├── compliance.py     # 合规检查
└── hooks.py          # 钩子系统
```

### 6. 监控系统 (Monitoring)

**职责**: 监控系统性能和运行状态

```
lingflow/monitoring/
├── operations_monitor.py  # 运营监控
└── default_checks.py      # 默认检查
```

## 数据流

### 1. 请求处理流程

```
用户请求
   │
   ▼
lingflow 入口
   │
   ├─→ 技能执行 → AgentCoordinator → Agent → 结果
   │
   └─→ 工作流执行 → WorkflowOrchestrator → 多个Agent → 结果
```

### 2. 上下文管理流程

```
上下文创建
   │
   ▼
ContextManager
   │
   ├─→ 追踪使用
   │
   ├─→ 判断阈值
   │
   └─→ 压缩保存 → SmartCompressor → 压缩后的上下文
```

### 3. 自优化流程

```
触发器检测
   │
   ▼
评估器评估
   │
   ▼
优化器优化
   │
   ├─→ Phase 4: 参数优化 → Optuna → 最优参数
   │
   └─→ Phase 5: AI学习 → 反馈收集 → 知识更新
```

## 设计模式

### 1. 协调器模式

多个Agent通过协调器协同工作，避免直接依赖。

```python
class AgentCoordinator:
    def __init__(self):
        self.agents = {}

    def register_agent(self, name: str, agent: BaseAgent):
        self.agents[name] = agent

    def execute_skill(self, agent_name: str, skill: str, params: dict):
        agent = self.agents.get(agent_name)
        return agent.execute_skill(skill, params)
```

### 2. 编排器模式

工作流编排器负责任务的调度和执行。

```python
class WorkflowOrchestrator:
    def execute(self, tasks: list):
        results = {}
        for task in tasks:
            if self._dependencies_met(task, results):
                results[task.name] = self._execute_task(task)
        return results
```

### 3. 策略模式

不同的压缩策略可以根据情况选择。

```python
class CompressionStrategy:
    def compress(self, content: str) -> str:
        pass

class AggressiveCompression(CompressionStrategy):
    def compress(self, content: str) -> str:
        # 激进压缩策略
        pass

class BalancedCompression(CompressionStrategy):
    def compress(self, content: str) -> str:
        # 平衡压缩策略
        pass
```

### 4. 观察者模式

监控系统观察系统事件并做出响应。

```python
class OperationsMonitor:
    def __init__(self):
        self.callbacks = []

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def notify(self, event: dict):
        for callback in self.callbacks:
            callback(event)
```

## 扩展性设计

### 1. 插件化Agent

```python
class CustomAgent(BaseAgent):
    def execute_skill(self, skill_name: str, params: dict) -> dict:
        # 自定义技能实现
        pass

# 注册自定义Agent
registry.register("custom", CustomAgent)
```

### 2. 自定义技能

```python
class AgentWithCustomSkills(BaseAgent):
    def execute_skill(self, skill_name: str, params: dict) -> dict:
        if skill_name == "custom_skill":
            return self._custom_skill(params)
        return super().execute_skill(skill_name, params)
```

### 3. 自定义评估器

```python
class CustomEvaluator:
    def evaluate(self, metrics: dict) -> float:
        # 自定义评估逻辑
        return score

optimizer = ParameterOptimizer(evaluator=CustomEvaluator())
```

## 性能考虑

### 1. 并行执行

```yaml
tasks:
  - name: "任务1"
    # 独立任务，可并行
  - name: "任务2"
    # 独立任务，可并行
```

### 2. 缓存机制

```python
class WorkflowOrchestrator:
    def __init__(self):
        self.cache = ExecutionCache()

    def execute(self, tasks: list):
        # 检查缓存
        if cached := self.cache.get(tasks):
            return cached
        # 执行并缓存
        result = self._execute(tasks)
        self.cache.set(tasks, result)
        return result
```

### 3. 懒加载

```python
def _import_core_modules():
    """延迟导入核心模块"""
    global _AgentCoordinator
    if _AgentCoordinator is None:
        from .coordination.coordinator import AgentCoordinator
        _AgentCoordinator = AgentCoordinator
```

## 安全考虑

### 1. 路径验证

```python
def _validate_filepath(self, filepath: str, base_dir: Path) -> Path:
    """安全验证文件路径"""
    filepath_abs = (base_dir / filepath).resolve()
    filepath_abs.relative_to(base_dir)  # 确保在base_dir内
    if filepath_abs.is_symlink():
        raise ValueError("符号链接不允许")
    return filepath_abs
```

### 2. 权限检查

```python
class GuardrailSystem:
    def check_permission(self, agent: str, skill: str) -> bool:
        # 检查Agent是否有权限执行技能
        pass
```

### 3. 输入验证

```python
def validate_params(params: dict) -> bool:
    """验证参数"""
    required = ["file_path", "focus_areas"]
    return all(key in params for key in required)
```

## 配置管理

### 全局配置

```yaml
# .lingflow/config.yaml
agents:
  max_concurrent: 10
  timeout: 300

workflows:
  default_timeout: 3600
  max_retries: 3

self_optimization:
  enabled: true
  optimization_interval: 86400

monitoring:
  enabled: true
  metrics_interval: 60
```

### 环境变量

```bash
export ANTHROPIC_API_KEY="your-key"
export LINGFLOW_HOME="/path/to/project"
export LINGFLOW_LOG_LEVEL="INFO"
export LINGFLOW_MAX_AGENTS=10
```

## 测试策略

### 1. 单元测试

```python
def test_agent_execution():
    agent = TestAgent()
    result = agent.execute_skill("test", {})
    assert result["status"] == "success"
```

### 2. 集成测试

```python
def test_workflow_execution():
    lf = lingflow()
    result = lf.run_workflow_file("test_workflow.yaml")
    assert result["status"] == "success"
```

### 3. 端到端测试

```python
def test_e2e_ci_cd():
    lf = lingflow()
    result = lf.run_workflow_file("ci_cd.yaml")
    assert result["status"] == "success"
```

## 最佳实践

### 1. 模块化设计

- 每个组件职责单一
- 接口清晰明确
- 避免循环依赖

### 2. 错误处理

- 使用异常处理错误
- 提供有用的错误信息
- 支持重试机制

### 3. 日志记录

- 记录关键操作
- 使用适当的日志级别
- 便于调试和监控

### 4. 文档完整

- API文档完整
- 使用示例丰富
- 架构说明清晰

## 相关文档

- [Agent协调指南](agent_coordination.md)
- [工作流引擎指南](workflow_engine.md)
- [参数优化指南](parameter_optimization.md)
- [AI学习系统指南](ai_learning.md)
