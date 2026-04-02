# Phase 4-5 迁移指南

**版本**: v1.0
**日期**: 2026-03-31

---

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [配置迁移](#配置迁移)
4. [代码迁移](#代码迁移)
5. [工作流迁移](#工作流迁移)
6. [故障排除](#故障排除)
7. [最佳实践](#最佳实践)

---

## 概述

### 迁移原则

1. **零破坏**：现有代码无需修改即可继续工作
2. **渐进式**：可以逐步启用新功能
3. **可选性**：所有新功能都通过配置控制
4. **向后兼容**：保持所有现有API不变

### 迁移路径

```
现有系统 (v3.6)
    ↓
可选启用 Phase 4/5 (v3.7)
    ↓
逐步采用新功能 (v3.8+)
    ↓
完全集成 (v4.0)
```

---

## 快速开始

### 安装

```bash
# 基础安装（包含Phase 4/5）
pip install lingflow[full]

# 或分别安装
pip install lingflow
pip install optuna  # Phase 4依赖
```

### 验证安装

```bash
# 验证LingFlow安装
lingflow --version

# 验证Phase 4
python -c "from lingflow.self_optimizer.phase4 import OptimizationEngine; print('Phase 4 OK')"

# 验证Phase 5
python -c "from lingflow.self_optimizer.phase5 import get_available_adapters; print('Phase 5 OK')"
```

### 初始化配置

```bash
# 交互式初始化
lingflow config init

# 启用Phase 4/5
lingflow config init --enable-phase4 --enable-phase5

# 验证配置
lingflow config validate
```

---

## 配置迁移

### 1. 基础配置

#### 旧配置（v3.6）

```yaml
# ~/.lingflow/config.yaml
optimization:
  max_experiments: 50
  time_budget: 120

code_review:
  enabled: true
  strict_mode: false
```

#### 新配置（v3.7+）

```yaml
# ~/.lingflow/config.yaml
# 现有配置保持不变
optimization:
  max_experiments: 50
  time_budget: 120

code_review:
  enabled: true
  strict_mode: false

# Phase 4 新增配置（可选）
phase4:
  enabled: true  # 启用贝叶斯优化
  optimizer:
    algorithm: bayesian
    backend: optuna
    n_trials: 50
    timeout: 120
  cache:
    enabled: true
    max_size: 1000

# Phase 5 新增配置（可选）
phase5:
  enabled: true  # 启用AI工具学习
  auto_collect: true
  default_tools: [semgrep, ruff]
  min_confidence: 0.8
```

### 2. 自动迁移工具

```bash
# 自动迁移配置
lingflow config migrate --from=v3.6 --to=v3.7

# 备份旧配置
lingflow config migrate --backup

# 预览迁移（不实际执行）
lingflow config migrate --dry-run
```

### 3. 手动迁移步骤

#### 步骤1：备份现有配置

```bash
cp ~/.lingflow/config.yaml ~/.lingflow/config.yaml.backup
```

#### 步骤2：添加Phase 4配置

```yaml
# 在现有配置文件末尾添加

phase4:
  # 是否启用（默认false）
  enabled: false

  # 优化器配置
  optimizer:
    algorithm: bayesian  # bayesian, grid, random
    backend: optuna
    n_trials: 50
    timeout: 120

  # 搜索空间配置
  search_spaces:
    structure:
      max_class_size: {min: 100, max: 500, step: 50}
      max_method_count: {choices: [10, 15, 20, 25]}

  # 缓存配置
  cache:
    enabled: true
    max_size: 1000
    ttl: 86400

  # 知识迁移配置
  transfer:
    enabled: true
    similarity_threshold: 0.7
```

#### 步骤3：添加Phase 5配置

```yaml
# 在现有配置文件末尾添加

phase5:
  # 是否启用（默认false）
  enabled: false

  # 自动收集反馈
  auto_collect: false

  # 默认工具列表
  default_tools: [semgrep, ruff]

  # 工具特定配置
  tools:
    semgrep:
      enabled: true
      rules: [auto]
      timeout: 300
    ruff:
      enabled: true
      select: [F, E, W]
      ignore: []
    pylint:
      enabled: false

  # 学习配置
  learning:
    min_confidence: 0.8
    auto_apply_threshold: 0.9
    validate_rules: true

  # 知识库配置
  knowledge_base:
    type: memory  # memory, file, database
    max_rules: 1000
```

#### 步骤4：验证配置

```bash
lingflow config validate
```

---

## 代码迁移

### 1. CLI使用迁移

#### 优化命令

##### 旧方式（继续支持）

```bash
# 使用传统优化器
lingflow optimize run structure --target .
```

##### 新方式（可选）

```bash
# 使用Phase 4贝叶斯优化
lingflow optimize run structure --target . --use-phase4

# 或在配置中启用后
lingflow optimize run structure --target .
```

#### 学习命令（新增）

```bash
# 从AI工具学习规则
lingflow learn from-tools --tools semgrep,ruff --target ./src

# 列出学习到的规则
lingflow learn list-rules --category security

# 验证规则
lingflow learn validate --rules rules.json
```

### 2. Python API迁移

#### 优化API

##### 旧方式（继续支持）

```python
from lingflow.self_optimizer import quick_optimize

result = quick_optimize(
    target=".",
    goal="structure"
)
```

##### 新方式（可选）

```python
# 使用Phase 4优化器
from lingflow.self_optimizer.phase4 import quick_optimize

result = quick_optimize(
    target=".",
    goal="structure",
    config={
        "n_trials": 50,
        "timeout": 120,
        "enable_cache": True
    }
)

# 或使用智能路由
from lingflow.integration import SmartOptimizerRouter

router = SmartOptimizerRouter()
optimizer = router.get_optimizer({"class_count": 100})
result = optimizer.optimize(request)
```

#### 学习API（新增）

```python
from lingflow.self_optimizer.phase5 import (
    get_available_adapters,
    RuleExtractor,
    InMemoryKnowledgeBase
)

# 1. 收集反馈
adapters = get_available_adapters()
all_feedback = []

for adapter in adapters:
    feedback = adapter.run_scan("./src")
    all_feedback.extend(feedback)

# 2. 提取规则
extractor = RuleExtractor()
rules = extractor.extract_patterns(all_feedback)

# 3. 保存规则
kb = InMemoryKnowledgeBase()
for rule in rules:
    kb.add_rule(rule)
```

### 3. Skill开发迁移

#### 旧方式（继续支持）

```python
from lingflow.core.skill import BaseSkill

class MyReviewSkill(BaseSkill):
    name = "my-review"
    description = "My code review skill"
    version = "1.0.0"

    def _execute_impl(self, context):
        # 实现审查逻辑
        return {"issues": []}
```

#### 新方式（可选增强）

```python
from lingflow.core.skill import BaseSkill
from lingflow.integration import Phase5Mixin

class MyEnhancedReviewSkill(BaseSkill, Phase5Mixin):
    name = "my-review-enhanced"
    description = "Enhanced review with Phase 5"
    version = "2.0.0"

    def __init__(self):
        super().__init__()
        self.phase5_enabled = True

    def _execute_impl(self, context):
        # 1. 基础审查
        result = self._basic_review(context)

        # 2. Phase 5增强（如果启用）
        if self.phase5_enabled:
            rules = self.learn_from_tools(
                target=context.working_dir,
                tools=["semgrep", "ruff"]
            )
            result["learned_rules"] = len(rules)

        return result
```

---

## 工作流迁移

### 1. 基础工作流

#### 旧工作流（继续支持）

```yaml
# workflow.yaml
tasks:
  - name: review
    skill: code-review
    params:
      target: ./src

  - name: optimize
    skill: optimize
    params:
      goal: structure
      target: .
```

#### 增强工作流（可选）

```yaml
# workflow_enhanced.yaml
tasks:
  # Phase 5增强的代码审查
  - name: review
    skill: code-review
    params:
      target: ./src
      use_phase5: true
      ai_tools: [semgrep, ruff]
      auto_apply_rules: false

  # Phase 4增强的优化
  - name: optimize
    skill: optimize
    depends_on: [review]
    params:
      goal: structure
      target: .
      use_phase4: true
      optimization_method: bayesian
      max_time: 120
      enable_cache: true

  # 新增：学习任务
  - name: learn
    skill: learn
    depends_on: [optimize]
    params:
      tools: [semgrep, ruff, pylint]
      target: ./src
      save_rules: true
      validate: true
```

### 2. 自动增强

#### 使用CLI自动增强

```bash
# 执行工作流时自动增强
lingflow workflow workflow.yaml --enhance

# 预览增强（不实际执行）
lingflow workflow workflow.yaml --enhance --dry-run
```

#### 使用代码自动增强

```python
from lingflow import LingFlow
from lingflow.integration import WorkflowEnhancer

lf = LingFlow()

# 加载原始工作流
tasks = lf._orchestrator.load_workflow_from_yaml("workflow.yaml")

# 自动增强
enhancer = WorkflowEnhancer(lf._orchestrator)
enhanced_tasks = enhancer.enhance_workflow(tasks)

# 执行增强后的工作流
result = lf._orchestrator.execute(enhanced_tasks)
```

---

## 故障排除

### 常见问题

#### 1. Phase 4未生效

**症状**：
```bash
lingflow optimize run structure --use-phase4
# 仍然使用传统优化器
```

**解决方案**：

```bash
# 检查依赖
pip install optuna

# 检查配置
lingflow config validate

# 查看日志
lingflow optimize run structure --use-phase4 --verbose
```

#### 2. Phase 5工具不可用

**症状**：
```bash
lingflow learn from-tools --tools semgrep
# Error: Tool not available
```

**解决方案**：

```bash
# 安装工具
pip install semgrep
pip install ruff
pip install pylint

# 验证工具
semgrep --version
ruff --version
pylint --version

# 检查配置
lingflow config show phase5
```

#### 3. 配置冲突

**症状**：
```bash
lingflow config validate
# Error: Configuration conflict
```

**解决方案**：

```bash
# 查看详细错误
lingflow config validate --verbose

# 重置配置
lingflow config reset

# 重新初始化
lingflow config init
```

#### 4. 性能下降

**症状**：
启用Phase 4/5后性能下降

**解决方案**：

```yaml
# 调整配置
phase4:
  cache:
    enabled: true  # 启用缓存
  optimizer:
    n_trials: 30  # 减少试验次数

phase5:
  auto_collect: false  # 禁用自动收集
  tools:
    semgrep:
      timeout: 120  # 减少超时时间
```

### 日志调试

```bash
# 启用调试日志
export LINGFLOW_LOG_LEVEL=DEBUG

# 查看详细日志
lingflow optimize run structure --verbose --log-file debug.log

# 分析日志
grep ERROR debug.log
grep WARNING debug.log
```

### 回滚策略

```bash
# 禁用Phase 4/5
lingflow config set phase4.enabled false
lingflow config set phase5.enabled false

# 或直接删除配置
# 编辑 ~/.lingflow/config.yaml
# 删除 phase4 和 phase5 段

# 重启LingFlow
lingflow --version
```

---

## 最佳实践

### 1. 渐进式启用

#### 第一阶段：观察

```yaml
# 禁用Phase 4/5，保持现有行为
phase4:
  enabled: false

phase5:
  enabled: false
  auto_collect: false
```

#### 第二阶段：试用

```yaml
# 启用Phase 4，观察效果
phase4:
  enabled: true
  optimizer:
    n_trials: 20  # 减少试验次数

# Phase 5保持禁用
phase5:
  enabled: false
```

#### 第三阶段：全面启用

```yaml
# 全面启用
phase4:
  enabled: true
  optimizer:
    n_trials: 50

phase5:
  enabled: true
  auto_collect: true
```

### 2. 性能优化

#### 启用缓存

```yaml
phase4:
  cache:
    enabled: true
    max_size: 1000
    ttl: 86400
```

#### 参数复用

```yaml
phase4:
  transfer:
    enabled: true
    similarity_threshold: 0.7
```

#### 并行处理

```yaml
phase5:
  tools:
    semgrep:
      parallel: true
      jobs: 4
```

### 3. 安全配置

#### 规则验证

```yaml
phase5:
  learning:
    validate_rules: true
    min_confidence: 0.8
    auto_apply_threshold: 0.9
```

#### 工具限制

```yaml
phase5:
  tools:
    semgrep:
      timeout: 300
      max_issues: 1000
```

### 4. 监控和维护

#### 定期检查

```bash
# 每周检查优化状态
lingflow optimize status

# 每月检查学习效果
lingflow learn list-rules --min-quality 0.8
```

#### 清理缓存

```bash
# 清理过期的缓存
lingflow cache clean --older-than 30d

# 重置知识库
lingflow learn reset-kb
```

#### 性能监控

```bash
# 查看性能报告
lingflow report performance --last 7d

# 导出指标
lingflow metrics export --format json > metrics.json
```

### 5. 团队协作

#### 共享配置

```bash
# 导出团队配置
lingflow config export > team-config.yaml

# 导入团队配置
lingflow config import team-config.yaml
```

#### 规则共享

```bash
# 导出学习到的规则
lingflow learn export-rules --output rules.json

# 导入规则
lingflow learn import-rules --input rules.json
```

---

## 附录

### A. 配置参考

完整配置选项参考：`CONFIG_REFERENCE.md`

### B. API文档

完整API文档：`API_REFERENCE.md`

### C. 迁移检查清单

- [ ] 备份现有配置
- [ ] 安装新依赖
- [ ] 更新配置文件
- [ ] 验证配置
- [ ] 测试CLI命令
- [ ] 测试Python API
- [ ] 更新工作流
- [ ] 性能测试
- [ ] 监控运行
- [ ] 团队培训

### D. 获取帮助

```bash
# 帮助命令
lingflow --help
lingflow optimize --help
lingflow learn --help

# 文档
lingflow docs
lingflow docs phase4
lingflow docs phase5

# 社区支持
https://github.com/guangda88/LingFlow/issues
```

---

**迁移指南版本**: v1.0
**最后更新**: 2026-03-31
**维护者**: LingFlow团队
