# 快速开始指南

本指南将帮助你在5分钟内上手LingFlow工程流系统。

## 安装

### 使用pip安装

```bash
pip install lingflow
```

### 从源码安装

```bash
git clone https://github.com/guangda88/LingFlow.git
cd LingFlow
pip install -e .
```

### 开发模式安装

```bash
git clone https://github.com/guangda88/LingFlow.git
cd LingFlow
pip install -e ".[dev]"
```

## 基础概念

### LingFlow是什么？

LingFlow是一个智能工程流系统，它：
- 🤖 使用AI Agent自动执行软件工程任务
- 📊 通过工作流编排复杂的多步骤流程
- 🔄 自动优化参数和学习改进
- 🛡️ 内置安全和质量保障机制

### 核心组件

1. **Agent（智能体）** - 执行特定任务的AI助手
2. **Skill（技能）** - Agent可执行的专业能力
3. **Workflow（工作流）** - 定义任务执行顺序和依赖
4. **Coordinator（协调器）** - 管理Agent和任务调度

## 5分钟快速上手

### 1. 创建第一个LingFlow应用

```python
from lingflow import LingFlow

# 初始化LingFlow
lf = LingFlow()
```

### 2. 执行单个技能

```python
# 执行代码审查技能
result = lf.run_skill("code_review", {
    "file_path": "src/main.py",
    "focus_areas": ["security", "performance"]
})

print(result)
# {
#     "status": "success",
#     "issues": [...],
#     "suggestions": [...]
# }
```

### 3. 定义工作流

创建 `workflow.yaml`:

```yaml
name: "CI/CD 流水线"
tasks:
  - name: "代码检查"
    agent: "code_reviewer"
    skill: "static_analysis"
    params:
      target: "src/"

  - name: "运行测试"
    agent: "tester"
    skill: "run_tests"
    depends_on: ["代码检查"]
    params:
      coverage_threshold: 80

  - name: "部署"
    agent: "deployer"
    skill: "deploy"
    depends_on: ["运行测试"]
    params:
      environment: "production"
```

执行工作流：

```python
result = lf.run_workflow_file("workflow.yaml")
print(result["status"])  # "success"
```

### 4. 启用自优化

```python
from lingflow.self_optimizer.phase4 import ParameterOptimizer
from lingflow.self_optimizer.phase5 import AILearningEngine

# 初始化参数优化器
param_optimizer = ParameterOptimizer(
    project_root=".",
    n_trials=100,
    timeout=3600
)

# 运行参数优化
best_params = param_optimizer.optimize_parameters()
print(f"最优参数: {best_params}")

# 初始化AI学习引擎
learning_engine = AILearningEngine(
    project_root=".",
    learning_rate=0.1
)

# 启动持续学习
learning_engine.start_learning()
```

## 常见使用场景

### 场景1: 自动化代码审查

```python
from lingflow import LingFlow

lf = LingFlow()

# 审查单个文件
result = lf.run_skill("code_review", {
    "file_path": "app.py",
    "focus_areas": ["security", "performance", "style"]
})

# 批量审查
for file in ["app.py", "models.py", "views.py"]:
    result = lf.run_skill("code_review", {"file_path": file})
    if result["issues"]:
        print(f"{file}: 发现 {len(result['issues'])} 个问题")
```

### 场景2: 需求追溯性

```python
from lingflow.requirements import RequirementTraceability

trace = RequirementTraceability()

# 添加需求
trace.add_requirement("REQ-001", "用户认证功能")

# 追溯实现
trace.link_to_code("REQ-001", "src/auth.py")
trace.link_to_code("REQ-001", "tests/test_auth.py")

# 追溯测试
trace.link_to_test("REQ-001", "tests/test_auth.py::test_login")

# 检查覆盖率
coverage = trace.get_coverage("REQ-001")
print(f"代码覆盖率: {coverage['code']}")
print(f"测试覆盖率: {coverage['test']}")
```

### 场景3: 监控和告警

```python
from lingflow.monitoring import OperationsMonitor

monitor = OperationsMonitor()

# 添加监控指标
@monitor.track_operation
def process_request(request):
    # 处理请求
    return response

# 查看性能指标
metrics = monitor.get_metrics()
print(f"平均响应时间: {metrics['avg_latency']}ms")
print(f"成功率: {metrics['success_rate']}%")
```

## 配置文件

### 全局配置 (`.lingflow/config.yaml`)

```yaml
# Agent配置
agents:
  code_reviewer:
    model: "claude-sonnet-4"
    max_tokens: 8000
    temperature: 0.3

  tester:
    model: "claude-sonnet-4"
    max_tokens: 4000

# 工作流配置
workflows:
  default_timeout: 3600
  max_retries: 3
  retry_delay: 60

# 自优化配置
self_optimization:
  enabled: true
  optimization_interval: 86400  # 24小时
  learning_rate: 0.1
```

### 环境变量

```bash
# Anthropic API配置
export ANTHROPIC_API_KEY="your-api-key"

# LingFlow配置
export LINGFLOW_HOME="/path/to/project"
export LINGFLOW_LOG_LEVEL="INFO"
export LINGFLOW_MAX_AGENTS=10

# 自优化配置
export LINGFLOW_OPTIMIZATION_ENABLED=true
export LINGFLOW_LEARNING_RATE=0.1
```

## 下一步

### 深入学习

- 📚 [API 参考](api/lingflow.md) - 详细的API文档
- 💡 [使用示例](examples/basic_usage.md) - 实际代码示例
- 🎓 [架构指南](guides/architecture.md) - 系统架构详解

### 实践项目

- [ ] 创建一个完整的CI/CD工作流
- [ ] 实现自定义Agent和技能
- [ ] 配置参数优化
- [ ] 集成AI学习引擎

### 社区资源

- 🐛 [问题反馈](https://github.com/guangda88/LingFlow/issues)
- 💬 [讨论区](https://github.com/guangda88/LingFlow/discussions)
- 📖 [Wiki](https://github.com/guangda88/LingFlow/wiki)

## 常见问题

### Q: LingFlow支持哪些LLM？

A: 目前主要支持Anthropic Claude系列（Claude 3 Opus/Sonnet/Haiku）。未来计划支持更多模型。

### Q: 如何自定义Agent？

A: 继承 `BaseAgent` 类并实现 `execute_skill` 方法。详见[自定义Agent指南](examples/custom_agent.md)。

### Q: 工作流失败如何处理？

A: LingFlow提供自动重试机制，可以通过配置文件调整重试次数和延迟。

### Q: 自优化会影响性能吗？

A: 优化过程在后台运行，不会阻塞主流程。可以设置优化间隔以控制影响。

## 获取帮助

如果遇到问题：

1. 查看 [常见问题文档](https://github.com/guangda88/LingFlow/wiki/FAQ)
2. 搜索 [已有Issues](https://github.com/guangda88/LingFlow/issues)
3. 创建新Issue并附上详细信息

---

**祝你使用愉快！众智混元，万法灵通。** 🚀
