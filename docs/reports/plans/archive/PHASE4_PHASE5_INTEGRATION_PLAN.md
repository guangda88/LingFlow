# Phase 4-5 系统集成方案

**版本**: v1.0
**日期**: 2026-03-31
**状态**: 集成方案设计

---

## 目录

1. [执行摘要](#执行摘要)
2. [系统架构分析](#系统架构分析)
3. [集成点识别](#集成点识别)
4. [集成架构设计](#集成架构设计)
5. [接口定义](#接口定义)
6. [数据流设计](#数据流设计)
7. [集成实施计划](#集成实施计划)
8. [风险评估与缓解](#风险评估与缓解)
9. [测试策略](#测试策略)
10. [迁移指南](#迁移指南)

---

## 执行摘要

### 集成目标

将Phase 4（参数优化系统）和Phase 5（AI工具学习系统）无缝集成到现有lingflow系统中，实现：

1. **零破坏集成**：保持100%向后兼容性
2. **渐进式增强**：可选启用新功能
3. **统一接口**：一致的API和CLI体验
4. **性能优化**：最小化性能影响
5. **平滑迁移**：提供清晰的迁移路径

### 核心原则

- **不破坏现有功能**：所有现有代码继续工作
- **可选启用**：新功能通过配置开关控制
- **模块化设计**：各组件独立可测试
- **向后兼容**：保持现有API不变
- **可观测性**：完整的日志和监控

---

## 系统架构分析

### 现有系统组件

#### 1. 核心系统

```
lingflow/
├── __init__.py           # lingflow统一入口
├── cli.py                # CLI命令行接口
├── core/
│   └── skill.py          # Skill系统（BaseSkill, SkillRegistry）
├── coordination/
│   └── coordinator.py    # AgentCoordinator（任务协调）
├── workflow/
│   └── orchestrator.py   # WorkflowOrchestrator（工作流编排）
├── code_review/          # 代码审查框架
└── self_optimizer/       # 自优化系统（Phase 1-3）
    ├── config.py
    ├── trigger.py
    ├── optimizer.py
    ├── evaluator.py
    └── advisor.py
```

#### 2. Skill系统

**核心接口**：
```python
class BaseSkill(ABC):
    name: str
    description: str
    version: str

    def execute(self, params: Dict[str, Any]) -> Result[Any]
    def _execute_impl(self, context: SkillContext) -> Any

class SkillRegistry:
    def register(self, skill: BaseSkill) -> None
    def get(self, name: str) -> Optional[BaseSkill]
    def list(self) -> List[str]
```

**已注册技能**：
- `code-review`: 代码审查
- `optimize`: 自优化
- `test`: 测试相关

#### 3. CLI系统

**命令结构**：
```bash
lingflow run <skill> [options]
lingflow workflow <workflow_file>
lingflow optimize run <goal> [options]
lingflow feedback submit [options]
```

#### 4. 工作流系统

**核心接口**：
```python
class WorkflowOrchestrator:
    def load_workflow_from_yaml(self, filepath: str) -> List[Task]
    def execute_workflow(self, tasks: List[Task], max_parallel: int) -> Dict[str, TaskResult]
```

### Phase 4系统（参数优化）

**核心组件**：
```
lingflow/self_optimizer/phase4/
├── engine.py              # OptimizationEngine（主引擎）
├── bayesian_optimizer.py  # BayesianOptimizer（贝叶斯优化）
├── multi_objective.py     # MultiObjectiveOptimizer（多目标优化）
├── sensitivity.py         # SensitivityAnalyzer（敏感性分析）
├── storage.py             # FileSystemParameterStore（参数存储）
├── cache.py               # ParameterCache（参数缓存）
├── visualization.py       # OptimizationVisualizer（可视化）
└── integration.py         # Phase4Integration（集成适配器）
```

**核心接口**：
```python
class OptimizationEngine:
    def optimize(self, request: OptimizationRequest) -> OptimizationResult
    def optimize_single_objective(self, target_path, goal, config) -> Dict
    def optimize_multiple_objectives(self, target_path, goals, config) -> Dict

class FileSystemParameterStore:
    def save(self, version: ParameterVersion) -> bool
    def load(self, version_id: str) -> Optional[ParameterVersion]
    def get_best_params(self, project: str, goal: str) -> Optional[Dict[str, Any]]
```

**已有集成适配器**：
```python
class Phase4Integration:
    @staticmethod
    def enhance_optimizer_request(request) -> Dict[str, Any]

class EnhancedOptimizerAdapter:
    def optimize(self, request) -> OptimizationResult
```

### Phase 5系统（AI工具学习）

**核心组件**：
```
lingflow/self_optimizer/phase5/
├── models.py              # 数据模型（FeedbackItem, LearnedRule, Pattern）
├── learning.py            # RuleExtractor（规则提取）
├── patterns.py            # PatternRecognizer（模式识别）
├── knowledge.py           # KnowledgeBase（知识库）
├── adapters.py            # AIToolAdapter（工具适配器）
└── test_adapters.py       # 适配器测试
```

**核心接口**：
```python
class AIToolAdapter:
    def check_available(self) -> bool
    def run_scan(self, target_path: str, **kwargs) -> List[AIFeedback]

class RuleExtractor:
    def extract_patterns(self, feedback_items: List[FeedbackItem]) -> List[LearnedRule]
    def validate_rule(self, rule: LearnedRule) -> ValidationReport

class KnowledgeBase:
    def add_rule(self, rule: LearnedRule) -> None
    def get_rules(self, category: str = None) -> List[LearnedRule]
```

**工具适配器**：
- `SemgrepAdapter`: Semgrep集成
- `RuffAdapter`: Ruff集成
- `PylintAdapter`: Pylint集成

---

## 集成点识别

### 1. 与code-review技能集成

**集成点**：
```
code-review skill
    ↓
Phase 5: AI工具适配器
    ↓
收集反馈 → 规则提取 → 规则验证 → 规则应用
    ↓
code-review skill（增强）
```

**集成方式**：
- Phase 5作为code-review的数据源
- 提取的规则自动注册到code-review的RuleEngine
- 实现规则质量评分和优先级排序

**接口定义**：
```python
class CodeReviewIntegration:
    """code-review与Phase 5集成"""

    def __init__(self, code_reviewer, phase5_system):
        self.code_reviewer = code_reviewer
        self.phase5_system = phase5_system

    def enhance_with_ai_tools(
        self,
        target_path: str,
        tools: List[FeedbackSource] = None
    ) -> List[LearnedRule]:
        """使用AI工具增强代码审查

        Args:
            target_path: 目标路径
            tools: 要使用的AI工具列表

        Returns:
            学习到的规则列表
        """
        # 1. 运行AI工具扫描
        feedback_list = self.phase5_system.collect_feedback(target_path, tools)

        # 2. 提取规则
        rules = self.phase5_system.extract_rules(feedback_list)

        # 3. 验证规则
        validated_rules = []
        for rule in rules:
            validation = self.phase5_system.validate_rule(rule, target_path)
            if validation.is_safe:
                validated_rules.append(rule)

        # 4. 注册到code-review
        for rule in validated_rules:
            self.code_reviewer.rule_engine.add_rule(
                rule_id=rule.id,
                pattern=rule.pattern,
                severity=rule.severity,
                category=rule.category
            )

        return validated_rules
```

### 2. 与self_optimizer模块集成

**集成点**：
```
self_optimizer (Phase 1-3)
    ↓
Phase 4: 参数优化
    ↓
增强优化器 → 贝叶斯优化 → 参数持久化
    ↓
self_optimizer (增强版)
```

**集成方式**：
- Phase 4作为self_optimizer的增强层
- 通过适配器保持向后兼容
- 可选启用贝叶斯优化

**实现状态**：
- ✅ 已有 `EnhancedOptimizerAdapter`
- ✅ 已有 `Phase4Integration`
- ✅ 已有 `enable_phase4_integration()` 函数

**改进建议**：
```python
# 改进集成，使其更智能
class SmartOptimizerRouter:
    """智能优化器路由

    根据项目规模和优化目标自动选择最合适的优化器
    """

    def __init__(self):
        self.phase4_enabled = get_config("phase4.enabled", False)
        self.project_size_threshold = get_config("phase4.project_size_threshold", 50)

    def get_optimizer(self, project_context: Dict) -> BaseOptimizer:
        """获取最适合的优化器

        Args:
            project_context: 项目上下文（类数量、文件数等）

        Returns:
            优化器实例
        """
        # 大型项目或启用Phase 4时使用贝叶斯优化
        if self.phase4_enabled or project_context.get("class_count", 0) > self.project_size_threshold:
            from lingflow.self_optimizer.phase4 import OptimizationEngine
            return OptimizationEngine()
        else:
            # 小型项目使用传统优化器
            from lingflow.self_optimizer import SynchronousOptimizer
            return SynchronousOptimizer()
```

### 3. 与工作流系统集成

**集成点**：
```
WorkflowOrchestrator
    ↓
工作流任务定义
    ↓
├─ 代码审查任务 → Phase 5增强
├─ 优化任务 → Phase 4增强
└─ 自定义任务 → 扩展点
```

**集成方式**：
- 在工作流YAML中支持Phase 4/5配置
- 自动增强相关任务
- 提供新的任务类型

**YAML扩展**：
```yaml
# example_workflow.yaml
tasks:
  # 传统代码审查
  - name: code-review
    skill: code-review
    params:
      target: "./src"

  # Phase 5增强的代码审查
  - name: enhanced-review
    skill: code-review
    params:
      target: "./src"
      use_phase5: true
      ai_tools: [semgrep, ruff, pylint]
      auto_apply_rules: false

  # 传统优化
  - name: optimize
    skill: optimize
    params:
      goal: structure
      target: "."

  # Phase 4增强的优化
  - name: smart-optimize
    skill: optimize
    params:
      goal: structure
      target: "."
      use_phase4: true
      optimization_method: bayesian
      max_time: 120
      enable_cache: true

  # Phase 5学习任务
  - name: learn-from-tools
    skill: learn
    params:
      tools: [semgrep, ruff]
      target: "./src"
      save_rules: true
```

**工作流增强器**：
```python
class WorkflowEnhancer:
    """工作流增强器

    自动增强工作流中的相关任务
    """

    def __init__(self, orchestrator: WorkflowOrchestrator):
        self.orchestrator = orchestrator

    def enhance_workflow(self, tasks: List[Task]) -> List[Task]:
        """增强工作流任务

        Args:
            tasks: 原始任务列表

        Returns:
            增强后的任务列表
        """
        enhanced_tasks = []

        for task in tasks:
            # 检查是否需要增强
            if task.name == "code-review":
                # 自动注入Phase 5
                enhanced_task = self._enhance_code_review(task)
                enhanced_tasks.append(enhanced_task)

            elif task.name == "optimize":
                # 自动注入Phase 4
                enhanced_task = self._enhance_optimize(task)
                enhanced_tasks.append(enhanced_task)

            else:
                # 保持原样
                enhanced_tasks.append(task)

        return enhanced_tasks

    def _enhance_code_review(self, task: Task) -> Task:
        """增强代码审查任务"""
        # 检查配置
        config = get_global_config()
        phase5_enabled = config.get("phase5.enabled", False)

        if not phase5_enabled:
            return task

        # 添加Phase 5参数
        params = task.context.copy()
        params.setdefault("use_phase5", True)
        params.setdefault("ai_tools", ["semgrep", "ruff"])

        return Task(
            task_id=task.task_id,
            name=task.name,
            description=task.description,
            agent_type=task.agent_type,
            context=params,
            priority=task.priority,
            dependencies=task.dependencies
        )

    def _enhance_optimize(self, task: Task) -> Task:
        """增强优化任务"""
        config = get_global_config()
        phase4_enabled = config.get("phase4.enabled", False)

        if not phase4_enabled:
            return task

        params = task.context.copy()
        params.setdefault("use_phase4", True)
        params.setdefault("optimization_method", "bayesian")

        return Task(
            task_id=task.task_id,
            name=task.name,
            description=task.description,
            agent_type=task.agent_type,
            context=params,
            priority=task.priority,
            dependencies=task.dependencies
        )
```

### 4. 与CLI集成

**集成点**：
```
CLI命令
    ↓
├─ lingflow optimize → Phase 4增强
├─ lingflow review → Phase 5增强
├─ lingflow learn → 新命令（Phase 5）
└─ lingflow workflow → 工作流增强
```

**新增/扩展命令**：

```python
# 1. 扩展optimize命令
@optimize.command()
@click.option("--use-phase4/--no-phase4", default=None, help="启用Phase 4贝叶斯优化")
@click.option("--method", type=click.Choice(["bayesian", "grid", "random"]), default="bayesian")
def run(goal, target, use_phase4, method):
    """运行优化（支持Phase 4）"""
    # 自动检测或使用配置
    if use_phase4 is None:
        config = get_global_config()
        use_phase4 = config.get("phase4.enabled", False)

    if use_phase4:
        from lingflow.self_optimizer.phase4 import quick_optimize
        result = quick_optimize(target, goal)
    else:
        from lingflow.self_optimizer import quick_optimize
        result = quick_optimize(target, goal)

# 2. 新增learn命令
@cli.group()
def learn():
    """AI工具学习系统（Phase 5）"""
    pass

@learn.command()
@click.option("--target", "-t", default=".", help="目标路径")
@click.option("--tools", help="工具列表（逗号分隔）")
@click.option("--save", "-s", help="保存规则到文件")
def from_tools(target, tools, save):
    """从AI工具学习规则"""
    from lingflow.self_optimizer.phase5 import get_available_adapters, RuleExtractor

    # 获取适配器
    tool_list = tools.split(",") if tools else ["semgrep", "ruff"]
    adapters = get_available_adapters()

    # 收集反馈
    all_feedback = []
    for adapter in adapters:
        if adapter.tool_name in tool_list:
            feedback = adapter.run_scan(target)
            all_feedback.extend(feedback)

    # 提取规则
    extractor = RuleExtractor()
    rules = extractor.extract_patterns(all_feedback)

    click.echo(f"学习到 {len(rules)} 条规则")

    # 保存规则
    if save:
        import json
        with open(save, 'w') as f:
            json.dump([r.__dict__ for r in rules], f, indent=2)
        click.echo(f"规则已保存到: {save}")

@learn.command()
@click.option("--category", "-c", help="按类别过滤")
def list_rules(category):
    """列出学习到的规则"""
    from lingflow.self_optimizer.phase5 import InMemoryKnowledgeBase

    kb = InMemoryKnowledgeBase()
    rules = kb.get_rules(category)

    click.echo(f"找到 {len(rules)} 条规则")
    for rule in rules:
        click.echo(f"  - [{rule.category.value}] {rule.id}")

# 3. 扩展workflow命令
@cli.command()
@click.option("--enhance/--no-enhance", default=True, help="自动启用Phase 4/5增强")
def workflow(workflow_file, enhance):
    """执行工作流（支持增强）"""
    lf = lingflow()

    if enhance:
        from lingflow.integration import WorkflowEnhancer
        # 加载并增强工作流
        tasks = lf._orchestrator.load_workflow_from_yaml(workflow_file)
        enhancer = WorkflowEnhancer(lf._orchestrator)
        enhanced_tasks = enhancer.enhance_workflow(tasks)

        # 执行增强后的工作流
        result = lf._orchestrator.execute(enhanced_tasks)
    else:
        # 执行原始工作流
        result = lf.run_workflow_file(workflow_file)
```

---

## 集成架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         lingflow CLI                            │
├─────────────────────────────────────────────────────────────────┤
│  run | workflow | optimize | learn | feedback                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                    Integration Layer                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ WorkflowEnhancer │  │ SmartOptimizer    │  │ CodeReview   │ │
│  │                  │  │ Router            │  │ Integration  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼──────────┐ ┌▼──────────────┐
│   Existing   │ │  Phase 4    │ │   Phase 5     │
│   System     │ │  (Param     │ │  (AI Tool     │
│              │ │   Opt)      │ │   Learning)   │
├──────────────┤ ├─────────────┤ ├───────────────┤
│ SkillSystem  │ │BayesianOpt  │ │AIToolAdapter  │
│ Workflow     │ │MultiObj     │ │RuleExtractor  │
│ CodeReview   │ │Sensitivity  │ │PatternRecog   │
│ SelfOptimize │ │Storage      │ │KnowledgeBase  │
└──────────────┘ └─────────────┘ └───────────────┘
        │            │            │
        └────────────┼────────────┘
                     │
            ┌────────▼────────┐
            │  Data Layer     │
            │  - Parameters   │
            │  - Rules        │
            │  - Feedback     │
            └─────────────────┘
```

### 数据流设计

#### 1. Phase 4数据流

```
用户请求优化
    ↓
CLI命令 (lingflow optimize run structure)
    ↓
SmartOptimizerRouter (选择优化器)
    ↓
OptimizationEngine.optimize()
    ↓
├─ ParameterStore.get_best_params() (尝试加载历史参数)
├─ KnowledgeTransfer.transfer() (尝试参数迁移)
│   ↓
├─ BayesianOptimizer.suggest() (建议参数)
│   ↓
├─ ParameterCache.get() (检查缓存)
│   ├─ 命中 → 返回缓存结果
│   └─ 未命中 ↓
├─ EvaluationFramework.evaluate() (评估参数)
│   ↓
├─ BayesianOptimizer.observe() (观察结果)
│   ↓
├─ ConvergenceDetector.update() (检查收敛)
│   ├─ 收敛 → 停止
│   └─ 未收敛 → 继续循环
│   ↓
├─ SensitivityAnalyzer.analyze() (敏感性分析)
│   ↓
└─ ParameterStore.save() (保存最佳参数)
    ↓
返回优化结果
```

#### 2. Phase 5数据流

```
用户请求学习
    ↓
CLI命令 (lingflow learn from-tools)
    ↓
AIToolAdapter.run_scan() (运行AI工具)
    ↓
收集反馈 (AIFeedback列表)
    ↓
RuleExtractor.extract_patterns() (提取规则)
    ↓
├─ RuleDeduplicator.deduplicate() (去重)
├─ RuleValidator.validate() (验证)
│   ↓
│   ├─ SecurityAnalyzer.analyze() (安全检查)
│   ├─ ABTester.evaluate() (A/B测试)
│   └─ 通过 → 继续
│   └─ 失败 → 丢弃
│   ↓
├─ QualityScorer.calculate_quality() (质量评分)
│   ↓
└─ KnowledgeBase.add_rule() (保存规则)
    ↓
CodeReviewIntegration.enhance_with_ai_tools()
    ↓
RuleEngine.add_rule() (注册到审查系统)
    ↓
返回学习结果
```

#### 3. 集成数据流

```
工作流执行
    ↓
WorkflowEnhancer.enhance_workflow()
    ↓
├─ 代码审查任务
│   ↓
│   CodeReviewIntegration.enhance_with_ai_tools()
│   ↓
│   Phase 5: 收集反馈 → 提取规则 → 注册规则
│   ↓
│   CodeReviewSkill.execute() (使用增强的规则)
│   ↓
├─ 优化任务
│   ↓
│   SmartOptimizerRouter.get_optimizer()
│   ↓
│   Phase 4: 贝叶斯优化 → 参数持久化
│   ↓
│   优化完成
│   ↓
└─ 汇总结果
    ↓
返回工作流结果
```

---

## 接口定义

### 1. 统一优化接口

```python
from typing import Protocol, Dict, Any, Optional

class OptimizerProtocol(Protocol):
    """优化器协议（统一接口）"""

    def optimize(
        self,
        target: str,
        goal: str,
        config: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """执行优化

        Args:
            target: 目标路径
            goal: 优化目标 (structure/performance/simplicity)
            config: 配置参数

        Returns:
            优化结果
        """
        ...

class OptimizationResult:
    """优化结果（统一格式）"""

    success: bool
    best_params: Dict[str, Any]
    best_score: float
    n_trials: int
    duration: float
    converged: bool
    error: Optional[str]

    # Phase 4扩展字段
    sensitivities: Optional[Dict[str, float]] = None
    pareto_front: Optional[List[Dict[str, Any]]] = None

    # Phase 5扩展字段
    learned_rules: Optional[List[Any]] = None
```

### 2. 统一学习接口

```python
class LearningProtocol(Protocol):
    """学习器协议（统一接口）"""

    def learn(
        self,
        target: str,
        tools: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> LearningResult:
        """执行学习

        Args:
            target: 目标路径
            tools: AI工具列表
            config: 配置参数

        Returns:
            学习结果
        """
        ...

class LearningResult:
    """学习结果（统一格式）"""

    success: bool
    feedback_count: int
    rules_learned: int
    rules: List[Any]
    duration: float
    error: Optional[str]
```

### 3. Skill集成接口

```python
class EnhancedCodeReviewSkill(BaseSkill):
    """增强的代码审查技能"""

    name = "code-review-enhanced"
    description = "代码审查（支持Phase 5 AI工具学习）"
    version = "2.0.0"

    def __init__(self):
        super().__init__()
        self.phase5_enabled = get_config("phase5.enabled", False)

    def _execute_impl(self, context: SkillContext) -> Any:
        """执行代码审查"""
        # 1. 基础审查
        result = self._basic_review(context)

        # 2. Phase 5增强（如果启用）
        if self.phase5_enabled:
            phase5_result = self._phase5_enhance(context)
            result = self._merge_results(result, phase5_result)

        return result

    def _phase5_enhance(self, context: SkillContext) -> Any:
        """使用Phase 5增强审查"""
        from lingflow.integration import CodeReviewIntegration

        integration = CodeReviewIntegration(
            self.code_reviewer,
            self.phase5_system
        )

        rules = integration.enhance_with_ai_tools(
            target_path=context.working_dir,
            tools=context.params.get("ai_tools")
        )

        return {"learned_rules": rules}
```

### 4. Hook集成接口

```python
# lingflow/hooks/__init__.py

class OptimizationHooks:
    """优化钩子（集成Phase 4）"""

    def pre_optimization(self, context: Dict) -> None:
        """优化前钩子"""
        # 记录初始状态
        pass

    def post_optimization(self, context: Dict, result: OptimizationResult) -> None:
        """优化后钩子"""
        # 1. 保存参数到Phase 4存储
        if get_config("phase4.enabled"):
            from lingflow.self_optimizer.phase4 import save_params
            save_params(
                project=context["project"],
                goal=context["goal"],
                params=result.best_params,
                metadata={"score": result.best_score}
            )

        # 2. 触发Phase 5学习
        if get_config("phase5.auto_learn"):
            from lingflow.self_optimizer.phase5 import RuleExtractor
            # 从优化结果中提取规则
            pass

class ReviewHooks:
    """审查钩子（集成Phase 5）"""

    def post_review(self, context: Dict, result: ReviewResult) -> None:
        """审查后钩子"""
        # 自动触发AI工具学习
        if get_config("phase5.auto_collect"):
            from lingflow.integration import CodeReviewIntegration

            integration = CodeReviewIntegration(...)
            rules = integration.enhance_with_ai_tools(
                target_path=context["target"],
                tools=get_config("phase5.default_tools", ["semgrep"])
            )
```

---

## 集成实施计划

### 阶段1: 基础设施（Week 1-2）

**目标**: 建立集成基础设施

**任务**:

1. **创建集成模块**
   - [ ] 创建 `lingflow/integration/__init__.py`
   - [ ] 实现 `SmartOptimizerRouter`
   - [ ] 实现 `WorkflowEnhancer`
   - [ ] 实现 `CodeReviewIntegration`

2. **配置系统扩展**
   - [ ] 扩展 `~/.lingflow/config.yaml` 支持Phase 4/5配置
   - [ ] 实现配置验证
   - [ ] 添加配置迁移工具

3. **统一接口定义**
   - [ ] 定义 `OptimizerProtocol`
   - [ ] 定义 `LearningProtocol`
   - [ ] 统一结果格式

**交付物**:
- `lingflow/integration/` 模块
- 配置文件示例
- 接口文档

**验收标准**:
- 所有接口定义完整
- 单元测试覆盖率 >80%
- 配置验证通过

### 阶段2: CLI集成（Week 3）

**目标**: 完成CLI命令集成

**任务**:

1. **扩展现有命令**
   - [ ] 扩展 `lingflow optimize` 支持Phase 4
   - [ ] 扩展 `lingflow workflow` 支持增强
   - [ ] 扩展 `lingflow run` 支持新技能

2. **新增命令**
   - [ ] 实现 `lingflow learn` 命令组
   - [ ] 实现 `lingflow learn from-tools`
   - [ ] 实现 `lingflow learn list-rules`
   - [ ] 实现 `lingflow learn validate`

3. **帮助和文档**
   - [ ] 更新 `lingflow --help`
   - [ ] 添加命令示例
   - [ ] 添加错误提示

**交付物**:
- 更新的 `lingflow/cli.py`
- CLI使用文档
- 命令示例脚本

**验收标准**:
- 所有命令正常工作
- 帮助文档完整
- 错误处理完善

### 阶段3: Skill集成（Week 4）

**目标**: 完成Skill系统集成

**任务**:

1. **增强现有技能**
   - [ ] 增强 `code-review` 技能
   - [ ] 增强 `optimize` 技能
   - [ ] 保持向后兼容

2. **新增技能**
   - [ ] 实现 `learn` 技能
   - [ ] 实现 `analyze` 技能（敏感性分析）

3. **技能注册**
   - [ ] 注册新技能到SkillRegistry
   - [ ] 更新技能列表
   - [ ] 添加技能依赖检查

**交付物**:
- 增强的技能实现
- 技能使用示例
- 技能测试套件

**验收标准**:
- 所有技能可独立工作
- 技能集成测试通过
- 性能影响 <10%

### 阶段4: 工作流集成（Week 5）

**目标**: 完成工作流系统集成

**任务**:

1. **工作流增强器**
   - [ ] 实现 `WorkflowEnhancer`
   - [ ] 支持YAML配置增强
   - [ ] 自动检测增强机会

2. **工作流测试**
   - [ ] 创建集成测试工作流
   - [ ] 验证增强效果
   - [ ] 性能基准测试

3. **文档和示例**
   - [ ] 创建工作流示例
   - [ ] 编写迁移指南
   - [ ] 添加故障排除文档

**交付物**:
- 完整的工作流增强器
- 示例工作流文件
- 集成测试套件

**验收标准**:
- 工作流正常执行
- 增强功能按预期工作
- 文档完整准确

### 阶段5: 监控和优化（Week 6）

**目标**: 完成监控和性能优化

**任务**:

1. **监控系统**
   - [ ] 实现性能监控
   - [ ] 添加使用统计
   - [ ] 创建监控仪表板

2. **性能优化**
   - [ ] 优化集成路径
   - [ ] 减少不必要的检查
   - [ ] 实现缓存优化

3. **文档完善**
   - [ ] API文档
   - [ ] 用户指南
   - [ ] 开发者指南

**交付物**:
- 监控系统
- 性能报告
- 完整文档

**验收标准**:
- 性能指标达标
- 监控正常工作
- 文档完整

---

## 风险评估与缓解

### 风险识别

| 风险 | 影响 | 概率 | 优先级 |
|------|------|------|--------|
| 破坏现有功能 | 高 | 中 | P0 |
| 性能下降 | 中 | 中 | P1 |
| 配置冲突 | 中 | 低 | P2 |
| 依赖问题 | 低 | 低 | P3 |
| 用户困惑 | 中 | 中 | P1 |

### 缓解措施

#### P0: 破坏现有功能

**预防**:
- 所有新功能默认禁用
- 保持100%向后兼容
- 完整的回归测试

**检测**:
- 自动化测试套件
- 集成测试覆盖
- Beta测试

**恢复**:
- 一键禁用新功能
- 快速回滚机制
- 详细的错误日志

#### P1: 性能下降

**预防**:
- 性能基准测试
- 渐进式增强
- 可选启用

**检测**:
- 性能监控
- 自动化基准测试
- 用户反馈

**缓解**:
- 懒加载机制
- 缓存优化
- 异步处理

#### P1: 用户困惑

**预防**:
- 清晰的文档
- 渐进式披露
- 智能默认值

**检测**:
- 用户测试
- 反馈收集
- 使用分析

**缓解**:
- 交互式引导
- 错误提示改进
- 帮助链接

---

## 测试策略

### 单元测试

**覆盖范围**:
- 集成模块所有公共接口
- 配置验证逻辑
- 路由逻辑

**示例**:
```python
def test_smart_optimizer_router():
    """测试智能优化器路由"""
    router = SmartOptimizerRouter()

    # 小型项目 → 传统优化器
    context = {"class_count": 30}
    optimizer = router.get_optimizer(context)
    assert isinstance(optimizer, SynchronousOptimizer)

    # 大型项目 → Phase 4优化器
    context = {"class_count": 100}
    optimizer = router.get_optimizer(context)
    assert isinstance(optimizer, OptimizationEngine)
```

### 集成测试

**测试场景**:
1. CLI命令集成
2. 工作流集成
3. Skill集成
4. Hook集成

**示例**:
```python
def test_workflow_enhancement():
    """测试工作流增强"""
    # 原始工作流
    tasks = [
        Task(name="code-review", ...),
        Task(name="optimize", ...)
    ]

    # 增强工作流
    enhancer = WorkflowEnhancer(orchestrator)
    enhanced_tasks = enhancer.enhance_workflow(tasks)

    # 验证增强
    assert enhanced_tasks[0].context.get("use_phase5") == True
    assert enhanced_tasks[1].context.get("use_phase4") == True
```

### 端到端测试

**测试流程**:
```yaml
# test_e2e_integration.yaml
tasks:
  - name: step1-review
    skill: code-review
    params:
      target: "./test_project"

  - name: step2-optimize
    skill: optimize
    depends_on: [step1-review]
    params:
      goal: structure

  - name: step3-learn
    skill: learn
    depends_on: [step2-optimize]
    params:
      tools: [semgrep, ruff]
```

**验证**:
- 工作流成功执行
- Phase 4/5功能正常
- 结果符合预期

### 性能测试

**基准测试**:
- 优化时间对比
- 内存使用对比
- 吞吐量对比

**目标**:
- 性能下降 <10%
- 内存增加 <20MB
- 功能开关开销 <1%

---

## 迁移指南

### 用户迁移

#### 1. 现有用户（零影响）

**无需任何操作**:
- 所有现有功能继续工作
- 新功能默认禁用
- 配置文件向后兼容

**可选启用**:
```yaml
# ~/.lingflow/config.yaml
phase4:
  enabled: true  # 启用Phase 4贝叶斯优化

phase5:
  enabled: true  # 启用Phase 5 AI工具学习
  auto_collect: true  # 自动收集反馈
```

#### 2. 新用户（推荐配置）

**安装**:
```bash
pip install lingflow[phase4,phase5]
```

**配置**:
```bash
# 初始化配置
lingflow config init --enable-phase4 --enable-phase5

# 验证配置
lingflow config validate
```

**使用**:
```bash
# 使用Phase 4优化
lingflow optimize run structure --use-phase4

# 使用Phase 5学习
lingflow learn from-tools --tools semgrep,ruff

# 增强工作流
lingflow workflow my_workflow.yaml --enhance
```

### 开发者迁移

#### 1. 插件开发者

**兼容性**:
- 现有插件无需修改
- 可选使用新接口

**新接口示例**:
```python
from lingflow.integration import OptimizerProtocol

class MyOptimizer:
    def optimize(self, target, goal, config=None):
        # 实现优化逻辑
        return OptimizationResult(...)
```

#### 2. 技能开发者

**增强技能**:
```python
from lingflow.core.skill import BaseSkill
from lingflow.integration import Phase5Mixin

class MySkill(BaseSkill, Phase5Mixin):
    def _execute_impl(self, context):
        # 使用Phase 5功能
        if self.phase5_enabled:
            rules = self.learn_from_tools(context.params.get("target"))

        return result
```

### 配置迁移

#### 自动迁移

**工具**:
```bash
lingflow config migrate --from=v3.6 --to=v3.7
```

**迁移内容**:
- 保留所有现有配置
- 添加Phase 4/5配置段
- 更新默认值

#### 手动迁移

**步骤**:
1. 备份现有配置
2. 添加新配置段
3. 验证配置
4. 测试功能

---

## 监控和维护

### 监控指标

**功能指标**:
- Phase 4/5启用率
- 优化时间改善
- 规则学习数量
- 错误率

**性能指标**:
- 平均响应时间
- 内存使用
- CPU使用
- 缓存命中率

**质量指标**:
- 测试覆盖率
- 代码质量分数
- 文档完整性

### 日志策略

**日志级别**:
- DEBUG: 详细调试信息
- INFO: 重要事件
- WARNING: 警告信息
- ERROR: 错误信息

**日志内容**:
- 功能启用/禁用
- 优化过程
- 学习过程
- 错误详情

### 维护计划

**定期任务**:
- 每周: 检查错误日志
- 每月: 性能评估
- 每季度: 依赖更新

**更新策略**:
- 补丁版本: 自动更新
- 次要版本: 手动确认
- 主要版本: 手动迁移

---

## 附录

### A. 配置文件示例

```yaml
# ~/.lingflow/config.yaml (完整配置)

# 现有配置
optimization:
  max_experiments: 50
  time_budget: 120

# Phase 4配置
phase4:
  enabled: true
  optimizer:
    algorithm: bayesian
    backend: optuna
    n_trials: 50
    timeout: 120
  search_spaces:
    structure:
      max_class_size: {min: 100, max: 500}
      max_method_count: {choices: [10, 15, 20, 25]}
  cache:
    enabled: true
    max_size: 1000
  transfer:
    enabled: true
    similarity_threshold: 0.7

# Phase 5配置
phase5:
  enabled: true
  auto_collect: true
  default_tools: [semgrep, ruff]
  tools:
    semgrep:
      enabled: true
      rules: [auto]
    ruff:
      enabled: true
      select: [F, E, W]
    pylint:
      enabled: false
  learning:
    min_confidence: 0.8
    auto_apply_threshold: 0.9
    validate_rules: true
  knowledge_base:
    type: memory
    max_rules: 1000

# 集成配置
integration:
  workflow_auto_enhance: true
  smart_optimizer_routing: true
  fallback_on_error: true
```

### B. CLI命令参考

```bash
# 优化命令
lingflow optimize run <goal> [options]
  --use-phase4          启用Phase 4贝叶斯优化
  --method              优化方法 (bayesian/grid/random)
  --max-time            最大时间（秒）
  --max-trials          最大试验次数
  --enable-cache        启用缓存
  --enable-transfer     启用知识迁移

# 学习命令
lingflow learn from-tools [options]
  --target              目标路径
  --tools               工具列表（逗号分隔）
  --save                保存规则到文件
  --validate            验证规则

lingflow learn list-rules [options]
  --category            按类别过滤
  --min-quality         最低质量分数

# 工作流命令
lingflow workflow <file> [options]
  --enhance             启用自动增强
  --no-enhance          禁用自动增强
  --dry-run             预览不执行

# 配置命令
lingflow config init [options]
  --enable-phase4       启用Phase 4
  --enable-phase5       启用Phase 5

lingflow config validate
lingflow config migrate [options]
```

### C. API参考

```python
# 集成模块
from lingflow.integration import (
    SmartOptimizerRouter,
    WorkflowEnhancer,
    CodeReviewIntegration
)

# 优化器路由
router = SmartOptimizerRouter()
optimizer = router.get_optimizer(project_context)
result = optimizer.optimize(target, goal, config)

# 工作流增强
enhancer = WorkflowEnhancer(orchestrator)
enhanced_tasks = enhancer.enhance_workflow(tasks)

# 代码审查集成
integration = CodeReviewIntegration(reviewer, phase5_system)
rules = integration.enhance_with_ai_tools(target, tools)

# Phase 4接口
from lingflow.self_optimizer.phase4 import (
    quick_optimize,
    quick_multi_optimize,
    quick_sensitivity_analysis,
    save_params,
    load_params
)

# Phase 5接口
from lingflow.self_optimizer.phase5 import (
    get_available_adapters,
    RuleExtractor,
    InMemoryKnowledgeBase
)
```

---

**文档版本**: v1.0
**最后更新**: 2026-03-31
**维护者**: lingflow团队
