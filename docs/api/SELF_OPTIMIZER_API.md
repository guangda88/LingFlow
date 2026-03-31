# LingFlow 自优化系统 API 文档

版本: 3.6.0
更新日期: 2026-03-31

---

## 目录

- [自优化系统 (self_optimizer)](#自优化系统-self_optimizer)
  - [配置管理](#配置管理)
  - [优化触发器](#优化触发器)
  - [优化器](#优化器)
  - [评估器](#评估器)
  - [优化顾问](#优化顾问)
  - [便捷函数](#便捷函数)
- [Phase 4: 参数优化系统](#phase-4-参数优化系统)
  - [核心引擎](#核心引擎)
  - [贝叶斯优化器](#贝叶斯优化器)
  - [多目标优化](#多目标优化)
  - [敏感性分析](#敏感性分析)
  - [可视化](#可视化)
  - [存储和缓存](#存储和缓存)
- [Phase 5: AI工具学习系统](#phase-5-ai工具学习系统)
  - [数据模型](#数据模型)
  - [规则提取](#规则提取)
  - [模式识别](#模式识别)
  - [知识库](#知识库)

---

## 自优化系统 (self_optimizer)

LingFlow 的核心自优化能力，基于 LingMinOpt 架构。

### 配置管理

#### `OptimizationConfig`

优化配置管理器。

```python
from lingflow.self_optimizer import OptimizationConfig, get_global_config, DEFAULT_CONFIG

# 获取全局配置
config = get_global_config()

# 获取优化配置
opt_config = config.get_optimization_config()

# 访问默认配置
print(DEFAULT_CONFIG)
```

**属性:**
- `max_class_size: int` - 最大类大小（默认: 300）
- `max_method_count: int` - 最大方法数量（默认: 15）
- `max_complexity: int` - 最大复杂度（默认: 10）

---

### 优化触发器

#### `OptimizationTrigger`

自动检测优化触发条件。

```python
from lingflow.self_optimizer import OptimizationTrigger, TriggerInfo

trigger = OptimizationTrigger()
should_trigger, trigger_info = trigger.check_all_conditions(context)

if should_trigger:
    print(f"触发原因: {trigger_info.reason}")
    print(f"优先级: {trigger_info.priority}")
```

**方法:**
- `check_all_conditions(context: dict) -> tuple[bool, TriggerInfo]` - 检查所有触发条件
- `requires_confirmation() -> bool` - 是否需要用户确认

---

### 优化器

#### `ProcessIsolatedOptimizer`

进程隔离的异步优化器。

```python
from lingflow.self_optimizer import ProcessIsolatedOptimizer, OptimizationRequest

optimizer = ProcessIsolatedOptimizer()
optimizer.start_optimization(request)
```

#### `SynchronousOptimizer`

同步优化器。

```python
from lingflow.self_optimizer import SynchronousOptimizer, OptimizationRequest

optimizer = SynchronousOptimizer()
result = optimizer.optimize(request)
```

#### `OptimizationRequest`

优化请求数据类。

**字段:**
- `target: str` - 目标路径
- `goal: str` - 优化目标 (structure/performance/simplicity)
- `params: dict` - 参数字典
- `config: OptimizationConfig` - 配置对象

#### `OptimizationResult`

优化结果数据类。

**字段:**
- `success: bool` - 是否成功
- `score: float` - 优化分数
- `params: dict` - 最佳参数
- `metrics: dict` - 详细指标
- `suggestions: list` - 改进建议

---

### 评估器

#### `StructureEvaluator`

代码结构评估器。

```python
from lingflow.self_optimizer import StructureEvaluator

evaluator = StructureEvaluator(target_path="./my_project")
score = evaluator.evaluate(params)
```

#### `PerfEvaluator`

性能评估器。

```python
from lingflow.self_optimizer import PerfEvaluator

evaluator = PerfEvaluator()
score = evaluator.evaluate(params)
```

#### `SimplicityEvaluator`

简洁性评估器。

```python
from lingflow.self_optimizer import SimplicityEvaluator

evaluator = SimplicityEvaluator()
score = evaluator.evaluate(params)
```

---

### 优化顾问

#### `OptimizationAdvisor`

提供优化建议。

```python
from lingflow.self_optimizer import OptimizationAdvisor

advisor = OptimizationAdvisor()
suggestions = advisor.get_suggestions(evaluation_result)
```

---

### 便捷函数

#### `quick_optimize()`

快速优化函数。

```python
from lingflow.self_optimizer import quick_optimize

result = quick_optimize(
    target=".",
    goal="structure",
    async_mode=False
)
```

**参数:**
- `target: str` - 目标路径（默认: "."）
- `goal: str` - 优化目标（默认: "structure"）
- `async_mode: bool` - 是否异步（默认: False）

**返回:** `OptimizationResult` 或 `None`（异步模式）

#### `check_and_optimize()`

检查条件并优化。

```python
from lingflow.self_optimizer import check_and_optimize

should_optimize, result = check_and_optimize(
    context=context,
    target=".",
    goal="structure"
)
```

---

## Phase 4: 参数优化系统

智能参数优化架构，使用贝叶斯优化和多目标优化技术。

### 核心引擎

#### `OptimizationEngine`

统一的参数优化接口。

```python
from lingflow.self_optimizer.phase4 import OptimizationEngine

engine = OptimizationEngine(config={
    "output_dir": ".lingflow/reports",
    "generate_reports": True
})

# 单目标优化
result = engine.optimize_single_objective(
    target_path="./my_project",
    goal="structure"
)

# 多目标优化
result = engine.optimize_multi_objective(
    target_path="./my_project",
    goals=["structure", "performance"],
    weights={"structure": 0.6, "performance": 0.4}
)

# 敏感性分析
result = engine.analyze_sensitivity(
    target_path="./my_project",
    goal="structure"
)
```

**方法:**
- `optimize_single_objective()` - 单目标优化
- `optimize_multi_objective()` - 多目标优化
- `analyze_sensitivity()` - 敏感性分析
- `clear_history()` - 清除优化历史

---

### 贝叶斯优化器

#### `BayesianOptimizer`

基于 Optuna 的贝叶斯优化器。

```python
from lingflow.self_optimizer.phase4 import BayesianOptimizer

optimizer = BayesianOptimizer(
    search_space=search_space,
    objective=objective_function,
    config={"n_trials": 100, "timeout": 300}
)

state = optimizer.optimize()
```

**配置选项:**
- `n_trials: int` - 最大试验次数
- `timeout: float` - 超时时间（秒）
- `early_stopping: bool` - 早停开关

#### `GridSearchOptimizer`

网格搜索优化器（贝叶斯优化的后备）。

```python
from lingflow.self_optimizer.phase4 import GridSearchOptimizer

optimizer = GridSearchOptimizer(
    search_space=search_space,
    objective=objective_function
)
```

#### `OptimizationTrial`

优化试验数据类。

**字段:**
- `trial_id: str` - 试验ID
- `params: dict` - 参数字典
- `score: float` - 目标值
- `timestamp: float` - 时间戳

#### `OptimizationState`

优化状态对象。

**方法:**
- `get_best_params() -> dict` - 获取最佳参数
- `get_best_score() -> float` - 获取最佳分数
- `should_stop() -> bool` - 是否应停止

---

### 多目标优化

#### `MultiObjectiveOptimizer`

多目标优化器。

```python
from lingflow.self_optimizer.phase4 import MultiObjectiveOptimizer

optimizer = MultiObjectiveOptimizer(
    objectives={
        "structure": structure_objective,
        "performance": performance_objective
    },
    weights={"structure": 0.7, "performance": 0.3}
)

result = optimizer.optimize(search_space)
```

#### `MultiObjectiveResult`

多目标优化结果。

**字段:**
- `pareto_front: List[ParetoPoint]` - Pareto前沿
- `all_evaluated: List` - 所有评估点

#### `ParetoPoint`

Pareto前沿点。

**字段:**
- `objectives: dict` - 目标值字典
- `aggregated_score: float` - 聚合分数

#### `optimize_multiple_objectives()`

多目标优化便捷函数。

```python
from lingflow.self_optimizer.phase4 import optimize_multiple_objectives

result = optimize_multiple_objectives(
    target_path="./my_project",
    goals=["structure", "performance", "simplicity"]
)
```

---

### 敏感性分析

#### `SensitivityAnalyzer`

参数敏感性分析器。

```python
from lingflow.self_optimizer.phase4 import SensitivityAnalyzer

analyzer = SensitivityAnalyzer()
result = analyzer.analyze(
    objective=objective_function,
    search_space=search_space
)
```

#### `SensitivityResult`

敏感性分析结果。

#### `SobolResult`

Sobol敏感性分析结果。

#### `analyze_sensitivity()`

敏感性分析便捷函数。

```python
from lingflow.self_optimizer.phase4 import analyze_sensitivity

result = analyze_sensitivity(
    target_path="./my_project",
    goal="structure"
)
```

---

### 可视化

#### `OptimizationVisualizer`

优化可视化器。

```python
from lingflow.self_optimizer.phase4 import OptimizationVisualizer

visualizer = OptimizationVisualizer(output_dir=".lingflow/reports")

# 生成HTML报告
report_path = visualizer.generate_html_report(
    optimization_state=state,
    search_space=search_space
)

# 生成敏感性热力图
heatmap_path = visualizer.generate_sensitivity_heatmap(
    sensitivity_results=result
)

# 生成Pareto前沿图
pareto_path = visualizer.generate_pareto_front_plot(
    pareto_result=result
)
```

**模块结构:**
- `lingflow.self_optimizer.phase4.visualization.visualizer` - 主可视化类
- `lingflow.self_optimizer.phase4.visualization.charts` - 图表生成器
- `lingflow.self_optimizer.phase4.visualization.data_processor` - 数据处理器

#### `plot_optimization_progress()`

绘制优化进度图。

```python
from lingflow.self_optimizer.phase4 import plot_optimization_progress

path = plot_optimization_progress(
    optimization_state=state,
    search_space=search_space,
    output_dir=".lingflow/reports"
)
```

#### `plot_sensitivity_heatmap()`

绘制敏感性热力图。

```python
from lingflow.self_optimizer.phase4 import plot_sensitivity_heatmap

path = plot_sensitivity_heatmap(
    sensitivity_results=result,
    output_dir=".lingflow/reports"
)
```

#### `plot_pareto_front()`

绘制Pareto前沿图。

```python
from lingflow.self_optimizer.phase4 import plot_pareto_front

path = plot_pareto_front(
    pareto_result=result,
    output_dir=".lingflow/reports"
)
```

---

### 存储和缓存

#### `FileSystemParameterStore`

文件系统参数存储。

```python
from lingflow.self_optimizer.phase4 import FileSystemParameterStore

store = FileSystemParameterStore(store_dir=".lingflow/params")
store.save("experiment_1", params)
params = store.load("experiment_1")
```

#### `ParameterCache`

参数缓存器。

```python
from lingflow.self_optimizer.phase4 import ParameterCache

cache = ParameterCache(max_size=1000)
cache.put(params_hash, result)
result = cache.get(params_hash)
```

#### `CachedParameterStore`

带缓存的参数存储。

#### 便捷函数

```python
from lingflow.self_optimizer.phase4 import (
    get_default_store,
    save_params,
    load_params,
    get_latest_params,
    get_default_cache
)

# 保存参数
save_params("experiment_1", params)

# 加载参数
params = load_params("experiment_1")

# 获取最新参数
params = get_latest_params()
```

---

### Phase 4 便捷函数

#### `quick_optimize()`

快速单目标优化。

```python
from lingflow.self_optimizer.phase4 import quick_optimize

result = quick_optimize(
    target_path="./my_project",
    goal="structure"
)
```

#### `quick_multi_optimize()`

快速多目标优化。

```python
from lingflow.self_optimizer.phase4 import quick_multi_optimize

result = quick_multi_optimize(
    target_path="./my_project",
    goals=["structure", "performance"]
)
```

#### `quick_sensitivity_analysis()`

快速敏感性分析。

```python
from lingflow.self_optimizer.phase4 import quick_sensitivity_analysis

result = quick_sensitivity_analysis(
    target_path="./my_project",
    goal="structure"
)
```

---

## Phase 5: AI工具学习系统

从外部AI代码分析工具中学习，自动集成到代码审查和优化流程。

### 数据模型

#### `AIFeedback`

AI工具反馈数据模型。

```python
from lingflow.self_optimizer.phase5.models import AIFeedback

feedback = AIFeedback(
    id="feedback_001",
    source=FeedbackSource.SEMGREP,
    category=FeedbackCategory.SECURITY,
    severity=FeedbackSeverity.HIGH,
    rule_id="python.flask.security.xss",
    message="潜在的XSS漏洞",
    file_path="app.py",
    line_no=42,
    suggestion="使用escape()函数转义用户输入"
)
```

**字段:**
- `id: str` - 唯一标识
- `source: FeedbackSource` - 来源工具
- `category: FeedbackCategory` - 问题类别
- `severity: FeedbackSeverity` - 严重程度
- `rule_id: str` - 规则ID
- `message: str` - 反馈消息
- `file_path: str` - 文件路径
- `line_no: int` - 行号
- `code_snippet: str` - 代码片段
- `suggestion: str` - 修复建议

#### `FeedbackSource`

反馈来源枚举。

```python
from lingflow.self_optimizer.phase5.models import FeedbackSource

FeedbackSource.SEMGREP
FeedbackSource.RUFF
FeedbackSource.PYLINT
FeedbackSource.SONARQUBE
FeedbackSource.CODEQL
```

#### `FeedbackCategory`

反馈分类枚举。

```python
from lingflow.self_optimizer.phase5.models import FeedbackCategory

FeedbackCategory.SECURITY
FeedbackCategory.PERFORMANCE
FeedbackCategory.CODE_QUALITY
FeedbackCategory.BUG_RISK
```

#### `FeedbackSeverity`

反馈严重程度枚举。

```python
from lingflow.self_optimizer.phase5.models import FeedbackSeverity

FeedbackSeverity.CRITICAL
FeedbackSeverity.HIGH
FeedbackSeverity.MEDIUM
FeedbackSeverity.LOW
FeedbackSeverity.INFO
```

#### `LearnedRule`

学习到的规则。

```python
from lingflow.self_optimizer.phase5.models import LearnedRule

rule = LearnedRule(
    id="rule_001",
    name="避免硬编码密钥",
    description="检测代码中的硬编码密钥",
    category=FeedbackCategory.SECURITY,
    pattern=pattern,
    tools=["semgrep", "ruff"],
    frequency=10,
    confidence=0.95
)
```

#### `Pattern`

规则模式。

---

### 规则提取

#### `RuleExtractor`

规则提取器。

```python
from lingflow.self_optimizer.phase5.learning import RuleExtractor

extractor = RuleExtractor(
    min_frequency=3,
    min_confidence=0.7,
    max_rules=1000
)

rules = extractor.extract_rules(
    feedback_items=feedback_list,
    category=FeedbackCategory.SECURITY
)
```

**参数:**
- `min_frequency: int` - 最小频率阈值
- `min_confidence: float` - 最小置信度
- `max_rules: int` - 最大规则数

#### `SecurityRuleExtractor`

安全规则专用提取器。

```python
from lingflow.self_optimizer.phase5.learning import SecurityRuleExtractor

extractor = SecurityRuleExtractor()
rules = extractor.extract_rules(feedback_items)
```

#### `RuleDeduplicator`

规则去重器。

```python
from lingflow.self_optimizer.phase5.learning import RuleDeduplicator

deduplicator = RuleDeduplicator()
unique_rules = deduplicator.deduplicate(rules)
```

#### `RuleValidator`

规则验证器。

```python
from lingflow.self_optimizer.phase5.learning import RuleValidator

validator = RuleValidator()
is_valid = validator.validate(rule)
```

---

### 模式识别

#### `PatternRecognizer`

模式识别器基类。

#### `PatternDetector`

通用模式检测器。

```python
from lingflow.self_optimizer.phase5.patterns import PatternDetector

detector = PatternDetector()
patterns = detector.detect(feedback_items)
```

#### `LongMethodDetector`

长方法检测器。

```python
from lingflow.self_optimizer.phase5.patterns import LongMethodDetector

detector = LongMethodDetector(max_lines=50)
long_methods = detector.detect(feedback_items)
```

#### `UnusedVariableDetector`

未使用变量检测器。

```python
from lingflow.self_optimizer.phase5.patterns import UnusedVariableDetector

detector = UnusedVariableDetector()
unused = detector.detect(feedback_items)
```

#### `HardcodedSecretDetector`

硬编码密钥检测器。

```python
from lingflow.self_optimizer.phase5.patterns import HardcodedSecretDetector

detector = HardcodedSecretDetector()
secrets = detector.detect(feedback_items)
```

#### `DuplicateCodeDetector`

重复代码检测器。

```python
from lingflow.self_optimizer.phase5.patterns import DuplicateCodeDetector

detector = DuplicateCodeDetector()
duplicates = detector.detect(feedback_items)
```

#### `EmptyBlockDetector`

空代码块检测器。

```python
from lingflow.self_optimizer.phase5.patterns import EmptyBlockDetector

detector = EmptyBlockDetector()
empty_blocks = detector.detect(feedback_items)
```

#### `ComplexityDetector`

复杂度检测器。

```python
from lingflow.self_optimizer.phase5.patterns import ComplexityDetector

detector = ComplexityDetector(max_complexity=10)
complex_items = detector.detect(feedback_items)
```

---

### 知识库

#### `KnowledgeBase`

知识库接口。

```python
from lingflow.self_optimizer.phase5.knowledge import KnowledgeBase

class MyKnowledgeBase(KnowledgeBase):
    def add_rule(self, rule: LearnedRule):
        pass

    def get_rule(self, rule_id: str) -> LearnedRule:
        pass

    def get_all_rules(self) -> List[LearnedRule]:
        pass
```

#### `InMemoryKnowledgeBase`

内存知识库实现。

```python
from lingflow.self_optimizer.phase5.knowledge import InMemoryKnowledgeBase

kb = InMemoryKnowledgeBase()
kb.add_rule(rule)
rules = kb.get_all_rules()
```

**方法:**
- `add_rule(rule)` - 添加规则
- `get_rule(rule_id)` - 获取规则
- `get_all_rules()` - 获取所有规则
- `get_rules_by_category(category)` - 按类别获取规则
- `clear()` - 清空知识库

---

### AI工具适配器

#### `BaseAdapter`

AI工具适配器基类。

```python
from lingflow.self_optimizer.phase5.adapters.base_adapter import BaseAdapter

class MyAdapter(BaseAdapter):
    def scan(self, target: str) -> List[AIFeedback]:
        pass
```

**方法:**
- `scan(target: str) -> List[AIFeedback]` - 扫描目标路径
- `is_available() -> bool` - 检查工具是否可用
- `normalize_results(results) -> List[AIFeedback]` - 规范化结果

#### `SemgrepAdapter`

Semgrep适配器。

```python
from lingflow.self_optimizer.phase5.adapters import SemgrepAdapter

adapter = SemgrepAdapter()
feedback = adapter.scan("./my_project")
```

#### `RuffAdapter`

Ruff适配器。

```python
from lingflow.self_optimizer.phase5.adapters import RuffAdapter

adapter = RuffAdapter()
feedback = adapter.scan("./my_project")
```

#### `PylintAdapter`

Pylint适配器。

```python
from lingflow.self_optimizer.phase5.adapters import PylintAdapter

adapter = PylintAdapter()
feedback = adapter.scan("./my_project")
```

---

## 版本信息

- **self_optimizer**: 3.6.0
- **Phase 4**: 4.0.0-alpha
- **Phase 5**: 5.0.0-alpha

---

## 许可证

© 2026 LingFlow Team. All rights reserved.
