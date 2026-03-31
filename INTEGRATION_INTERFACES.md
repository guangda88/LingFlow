# Phase 4-5 集成接口定义

**版本**: v1.0
**日期**: 2026-03-31

---

## 目录

1. [核心接口](#核心接口)
2. [集成接口](#集成接口)
3. [数据模型](#数据模型)
4. [错误处理](#错误处理)
5. [事件系统](#事件系统)

---

## 核心接口

### 1. 优化器协议

```python
from typing import Protocol, Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class OptimizationGoal(Enum):
    """优化目标"""
    STRUCTURE = "structure"
    PERFORMANCE = "performance"
    SIMPLICITY = "simplicity"
    ALL = "all"

@dataclass
class OptimizationRequest:
    """优化请求"""
    target: str
    goal: OptimizationGoal
    search_space: Dict[str, Any]
    max_time: float = 120.0
    max_trials: int = 50
    enable_cache: bool = True
    enable_transfer: bool = True
    project_name: str = "default"

@dataclass
class OptimizationResult:
    """优化结果"""
    success: bool
    best_params: Dict[str, Any]
    best_score: float
    n_trials: int
    duration: float
    converged: bool
    error: Optional[str] = None

    # Phase 4扩展
    sensitivities: Optional[Dict[str, float]] = None
    pareto_front: Optional[List[Dict[str, Any]]] = None
    convergence_rate: Optional[float] = None

class OptimizerProtocol(Protocol):
    """优化器协议"""

    def optimize(
        self,
        request: OptimizationRequest
    ) -> OptimizationResult:
        """执行优化"""
        ...

    def get_progress(self) -> Dict[str, Any]:
        """获取优化进度"""
        ...

    def cancel(self) -> bool:
        """取消优化"""
        ...
```

### 2. 学习器协议

```python
from enum import Enum

class FeedbackSource(Enum):
    """反馈源"""
    SEMGREP = "semgrep"
    RUFF = "ruff"
    PYLINT = "pylint"
    CUSTOM = "custom"

@dataclass
class LearningRequest:
    """学习请求"""
    target: str
    tools: List[FeedbackSource]
    auto_apply: bool = False
    min_confidence: float = 0.8
    save_rules: bool = True

@dataclass
class LearningResult:
    """学习结果"""
    success: bool
    feedback_count: int
    rules_learned: int
    rules: List[Any]
    duration: float
    error: Optional[str] = None

class LearningProtocol(Protocol):
    """学习器协议"""

    def learn(
        self,
        request: LearningRequest
    ) -> LearningResult:
        """执行学习"""
        ...

    def validate_rules(
        self,
        rules: List[Any]
    ) -> Dict[str, bool]:
        """验证规则"""
        ...

    def apply_rules(
        self,
        rules: List[Any],
        auto_apply: bool = False
    ) -> bool:
        """应用规则"""
        ...
```

---

## 集成接口

### 1. 智能优化器路由

```python
class SmartOptimizerRouter:
    """智能优化器路由

    根据项目特征和配置自动选择最合适的优化器
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化路由器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.phase4_enabled = self.config.get("phase4.enabled", False)
        self.project_size_threshold = self.config.get(
            "phase4.project_size_threshold",
            50
        )

    def get_optimizer(
        self,
        project_context: Dict[str, Any]
    ) -> OptimizerProtocol:
        """获取优化器实例

        Args:
            project_context: 项目上下文信息

        Returns:
            优化器实例
        """
        # 检查是否应该使用Phase 4
        if self._should_use_phase4(project_context):
            return self._create_phase4_optimizer()
        else:
            return self._create_legacy_optimizer()

    def _should_use_phase4(
        self,
        context: Dict[str, Any]
    ) -> bool:
        """判断是否使用Phase 4优化器

        Args:
            context: 项目上下文

        Returns:
            是否使用Phase 4
        """
        # 显式启用
        if self.phase4_enabled:
            return True

        # 大型项目
        class_count = context.get("class_count", 0)
        if class_count > self.project_size_threshold:
            return True

        # 长时间优化需求
        max_time = context.get("max_time", 0)
        if max_time > 300:  # 5分钟以上
            return True

        return False

    def _create_phase4_optimizer(self) -> OptimizerProtocol:
        """创建Phase 4优化器"""
        from lingflow.self_optimizer.phase4 import OptimizationEngine
        return OptimizationEngine(config=self.config)

    def _create_legacy_optimizer(self) -> OptimizerProtocol:
        """创建传统优化器"""
        from lingflow.self_optimizer import SynchronousOptimizer
        return SynchronousOptimizer()
```

### 2. 工作流增强器

```python
from lingflow.common.models import Task

class WorkflowEnhancer:
    """工作流增强器

    自动增强工作流中的相关任务
    """

    def __init__(
        self,
        orchestrator,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化增强器

        Args:
            orchestrator: 工作流编排器
            config: 配置字典
        """
        self.orchestrator = orchestrator
        self.config = config or {}

    def enhance_workflow(
        self,
        tasks: List[Task]
    ) -> List[Task]:
        """增强工作流任务

        Args:
            tasks: 原始任务列表

        Returns:
            增强后的任务列表
        """
        enhanced_tasks = []

        for task in tasks:
            enhanced_task = self._enhance_task(task)
            enhanced_tasks.append(enhanced_task)

        return enhanced_tasks

    def _enhance_task(self, task: Task) -> Task:
        """增强单个任务

        Args:
            task: 原始任务

        Returns:
            增强后的任务
        """
        # 根据任务类型增强
        if task.name == "code-review":
            return self._enhance_code_review(task)
        elif task.name == "optimize":
            return self._enhance_optimize(task)
        else:
            return task

    def _enhance_code_review(self, task: Task) -> Task:
        """增强代码审查任务

        Args:
            task: 代码审查任务

        Returns:
            增强后的任务
        """
        phase5_enabled = self.config.get("phase5.enabled", False)
        if not phase5_enabled:
            return task

        # 添加Phase 5参数
        params = task.context.copy()
        params.setdefault("use_phase5", True)
        params.setdefault(
            "ai_tools",
            self.config.get("phase5.default_tools", ["semgrep", "ruff"])
        )

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
        """增强优化任务

        Args:
            task: 优化任务

        Returns:
            增强后的任务
        """
        phase4_enabled = self.config.get("phase4.enabled", False)
        if not phase4_enabled:
            return task

        params = task.context.copy()
        params.setdefault("use_phase4", True)
        params.setdefault(
            "optimization_method",
            self.config.get("phase4.optimizer.algorithm", "bayesian")
        )

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

### 3. 代码审查集成

```python
class CodeReviewIntegration:
    """代码审查与Phase 5集成

    将AI工具学习到的规则集成到代码审查流程
    """

    def __init__(
        self,
        code_reviewer,
        phase5_system,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化集成

        Args:
            code_reviewer: 代码审查器
            phase5_system: Phase 5学习系统
            config: 配置字典
        """
        self.code_reviewer = code_reviewer
        self.phase5_system = phase5_system
        self.config = config or {}

    def enhance_with_ai_tools(
        self,
        target_path: str,
        tools: Optional[List[FeedbackSource]] = None
    ) -> List[Any]:
        """使用AI工具增强代码审查

        Args:
            target_path: 目标路径
            tools: AI工具列表

        Returns:
            学习到的规则列表
        """
        # 1. 确定工具列表
        if tools is None:
            tools = self._get_default_tools()

        # 2. 收集反馈
        feedback_list = self._collect_feedback(target_path, tools)

        # 3. 提取规则
        rules = self._extract_rules(feedback_list)

        # 4. 验证规则
        validated_rules = self._validate_rules(rules, target_path)

        # 5. 注册规则
        self._register_rules(validated_rules)

        return validated_rules

    def _get_default_tools(self) -> List[FeedbackSource]:
        """获取默认工具列表"""
        default_tools = self.config.get(
            "phase5.default_tools",
            ["semgrep", "ruff"]
        )

        tool_map = {
            "semgrep": FeedbackSource.SEMGREP,
            "ruff": FeedbackSource.RUFF,
            "pylint": FeedbackSource.PYLINT
        }

        return [
            tool_map[tool]
            for tool in default_tools
            if tool in tool_map
        ]

    def _collect_feedback(
        self,
        target_path: str,
        tools: List[FeedbackSource]
    ) -> List[Any]:
        """收集AI工具反馈"""
        from lingflow.self_optimizer.phase5 import get_available_adapters

        all_feedback = []

        # 获取可用适配器
        adapter_configs = self._get_adapter_configs(tools)
        adapters = get_available_adapters(adapter_configs)

        # 运行扫描
        for adapter in adapters:
            try:
                feedback = adapter.run_scan(target_path)
                all_feedback.extend(feedback)
            except Exception as e:
                # 记录错误但继续
                self._log_error(adapter.name, e)

        return all_feedback

    def _extract_rules(self, feedback_list: List[Any]) -> List[Any]:
        """从反馈中提取规则"""
        from lingflow.self_optimizer.phase5 import RuleExtractor

        extractor = RuleExtractor(config=self.config)
        rules = extractor.extract_patterns(feedback_list)

        # 去重
        deduplicator = RuleDeduplicator()
        rules = deduplicator.deduplicate(rules)

        return rules

    def _validate_rules(
        self,
        rules: List[Any],
        target_path: str
    ) -> List[Any]:
        """验证规则"""
        from lingflow.self_optimizer.phase5 import RuleValidator

        validator = RuleValidator(config=self.config)
        validated_rules = []

        for rule in rules:
            try:
                validation = validator.validate_rule(rule, target_path)
                if validation.is_safe:
                    validated_rules.append(rule)
            except Exception as e:
                # 记录错误但继续
                self._log_error(f"Validation for {rule.id}", e)

        return validated_rules

    def _register_rules(self, rules: List[Any]) -> None:
        """注册规则到代码审查器"""
        for rule in rules:
            try:
                self.code_reviewer.rule_engine.add_rule(
                    rule_id=rule.id,
                    pattern=rule.pattern,
                    severity=rule.severity,
                    category=rule.category
                )
            except Exception as e:
                # 记录错误但继续
                self._log_error(f"Registering rule {rule.id}", e)

    def _get_adapter_configs(
        self,
        tools: List[FeedbackSource]
    ) -> Dict[FeedbackSource, Dict[str, Any]]:
        """获取适配器配置"""
        configs = {}

        for tool in tools:
            # 从配置中读取工具特定配置
            tool_config = self.config.get(f"phase5.tools.{tool.value}", {})
            configs[tool] = tool_config

        return configs

    def _log_error(self, context: str, error: Exception) -> None:
        """记录错误"""
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error in {context}: {error}")
```

---

## 数据模型

### 1. 统一结果模型

```python
from typing import Generic, TypeVar, Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

T = TypeVar('T')

@dataclass
class IntegrationResult(Generic[T]):
    """集成结果（统一格式）"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def is_error(self) -> bool:
        """是否错误"""
        return not self.success or self.error is not None

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0
```

### 2. 集成配置模型

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class IntegrationConfig:
    """集成配置"""
    # Phase 4配置
    phase4_enabled: bool = False
    phase4_auto_enable: bool = False
    phase4_project_size_threshold: int = 50

    # Phase 5配置
    phase5_enabled: bool = False
    phase5_auto_collect: bool = False
    phase5_default_tools: List[str] = field(default_factory=lambda: ["semgrep", "ruff"])
    phase5_min_confidence: float = 0.8
    phase5_auto_apply_threshold: float = 0.9

    # 工作流配置
    workflow_auto_enhance: bool = True
    workflow_dry_run: bool = False

    # 路由配置
    smart_optimizer_routing: bool = True
    fallback_on_error: bool = True

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'IntegrationConfig':
        """从字典创建配置"""
        return cls(
            phase4_enabled=config.get("phase4.enabled", False),
            phase4_auto_enable=config.get("phase4.auto_enable", False),
            phase4_project_size_threshold=config.get(
                "phase4.project_size_threshold",
                50
            ),
            phase5_enabled=config.get("phase5.enabled", False),
            phase5_auto_collect=config.get("phase5.auto_collect", False),
            phase5_default_tools=config.get(
                "phase5.default_tools",
                ["semgrep", "ruff"]
            ),
            phase5_min_confidence=config.get("phase5.min_confidence", 0.8),
            phase5_auto_apply_threshold=config.get(
                "phase5.auto_apply_threshold",
                0.9
            ),
            workflow_auto_enhance=config.get("integration.workflow_auto_enhance", True),
            workflow_dry_run=config.get("integration.workflow_dry_run", False),
            smart_optimizer_routing=config.get(
                "integration.smart_optimizer_routing",
                True
            ),
            fallback_on_error=config.get("integration.fallback_on_error", True),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "phase4.enabled": self.phase4_enabled,
            "phase4.auto_enable": self.phase4_auto_enable,
            "phase4.project_size_threshold": self.phase4_project_size_threshold,
            "phase5.enabled": self.phase5_enabled,
            "phase5.auto_collect": self.phase5_auto_collect,
            "phase5.default_tools": self.phase5_default_tools,
            "phase5.min_confidence": self.phase5_min_confidence,
            "phase5.auto_apply_threshold": self.phase5_auto_apply_threshold,
            "integration.workflow_auto_enhance": self.workflow_auto_enhance,
            "integration.workflow_dry_run": self.workflow_dry_run,
            "integration.smart_optimizer_routing": self.smart_optimizer_routing,
            "integration.fallback_on_error": self.fallback_on_error,
        }
```

---

## 错误处理

### 1. 集成异常

```python
class IntegrationError(Exception):
    """集成错误基类"""
    pass

class ConfigurationError(IntegrationError):
    """配置错误"""
    pass

class OptimizerNotFoundError(IntegrationError):
    """优化器未找到错误"""
    pass

class LearningError(IntegrationError):
    """学习错误"""
    pass

class RuleValidationError(IntegrationError):
    """规则验证错误"""
    pass

class ToolNotAvailableError(IntegrationError):
    """工具不可用错误"""
    pass
```

### 2. 错误处理器

```python
class IntegrationErrorHandler:
    """集成错误处理器"""

    def __init__(self, logger=None):
        """初始化错误处理器"""
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}
        self.error_callbacks = {}

    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> None:
        """处理错误

        Args:
            error: 异常对象
            context: 错误上下文
        """
        # 记录错误
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # 记录日志
        self.logger.error(
            f"Integration error: {error}",
            extra={"context": context, "error_type": error_type}
        )

        # 调用回调
        callback = self.error_callbacks.get(error_type)
        if callback:
            callback(error, context)

    def register_callback(
        self,
        error_type: str,
        callback: callable
    ) -> None:
        """注册错误回调

        Args:
            error_type: 错误类型
            callback: 回调函数
        """
        self.error_callbacks[error_type] = callback

    def get_error_stats(self) -> Dict[str, int]:
        """获取错误统计"""
        return self.error_counts.copy()
```

---

## 事件系统

### 1. 事件定义

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Callable, List

class IntegrationEventType(Enum):
    """集成事件类型"""
    OPTIMIZATION_STARTED = "optimization_started"
    OPTIMIZATION_COMPLETED = "optimization_completed"
    OPTIMIZATION_FAILED = "optimization_failed"

    LEARNING_STARTED = "learning_started"
    LEARNING_COMPLETED = "learning_completed"
    LEARNING_FAILED = "learning_failed"

    RULE_LEARNED = "rule_learned"
    RULE_VALIDATED = "rule_validated"
    RULE_APPLIED = "rule_applied"

    WORKFLOW_ENHANCED = "workflow_enhanced"

@dataclass
class IntegrationEvent:
    """集成事件"""
    type: IntegrationEventType
    data: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
```

### 2. 事件总线

```python
class IntegrationEventBus:
    """集成事件总线"""

    def __init__(self):
        """初始化事件总线"""
        self._listeners: Dict[IntegrationEventType, List[Callable]] = {}

    def subscribe(
        self,
        event_type: IntegrationEventType,
        callback: Callable[[IntegrationEvent], None]
    ) -> None:
        """订阅事件

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(callback)

    def publish(self, event: IntegrationEvent) -> None:
        """发布事件

        Args:
            event: 事件对象
        """
        listeners = self._listeners.get(event.type, [])

        for callback in listeners:
            try:
                callback(event)
            except Exception as e:
                # 记录错误但继续执行其他回调
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"Error in event callback for {event.type}: {e}"
                )

    def unsubscribe(
        self,
        event_type: IntegrationEventType,
        callback: Callable[[IntegrationEvent], None]
    ) -> None:
        """取消订阅

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
            except ValueError:
                pass

# 全局事件总线实例
_global_event_bus = None

def get_global_event_bus() -> IntegrationEventBus:
    """获取全局事件总线"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = IntegrationEventBus()
    return _global_event_bus
```

### 3. 事件使用示例

```python
# 订阅事件
event_bus = get_global_event_bus()

def on_optimization_completed(event: IntegrationEvent):
    """优化完成事件处理"""
    result = event.data.get("result")
    print(f"Optimization completed: {result.best_score}")

event_bus.subscribe(
    IntegrationEventType.OPTIMIZATION_COMPLETED,
    on_optimization_completed
)

# 发布事件
event = IntegrationEvent(
    type=IntegrationEventType.OPTIMIZATION_COMPLETED,
    data={"result": optimization_result}
)
event_bus.publish(event)
```

---

**接口版本**: v1.0
**最后更新**: 2026-03-31
