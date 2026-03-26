# LingFlow V3.5 封装优化方案

**版本**: V3.5.0
**日期**: 2026-03-25
**类型**: 封装优化（聚焦方案）
**时间线**: 6周
**向后兼容**: 完全兼容

---

## 执行摘要

本方案针对LingFlow的**4个核心封装问题**，采用**最小化改动**和**渐进式迁移**策略，在6周内完成优化。

**核心改进**：
1. ✅ 统一返回类型 - 使用简化的Result类型
2. ✅ 类型安全的配置 - 使用dataclass
3. ✅ 标准化技能接口 - 轻量级基类
4. ✅ 全局状态管理 - 单例模式+依赖注入

**设计原则**：
- 🎯 **聚焦核心问题** - 只解决封装问题，不做额外功能
- 🐍 **符合Python习惯** - 不引入Rust风格的Result
- 🔄 **向后兼容** - 旧代码无需修改即可运行
- 📈 **渐进式迁移** - 新旧API共存，逐步迁移
- ⏱️ **快速交付** - 6周完成，风险可控

**预期收益**：
- 类型安全性：从无到有
- API一致性：从混乱到统一
- 代码可读性：提升30%
- 测试覆盖率：提升50%

---

## 一、当前问题分析

### 1.1 核心封装问题（4个）

| 问题 | 当前状态 | 影响 | 优先级 |
|------|---------|------|--------|
| **1. 返回类型不一致** | 所有方法返回`Dict[str, Any]` | 类型不安全，IDE无提示 | P0 |
| **2. 配置使用字典** | `config: Dict[str, Any]` | 类型不安全，无验证 | P0 |
| **3. 技能接口不统一** | 无统一接口 | 难以扩展和维护 | P1 |
| **4. 全局状态暴露** | `AgentCoordinator`暴露内部状态 | 封装泄漏，难以测试 | P1 |

---

### 1.2 问题1：返回类型不一致

**当前代码**：
```python
class LingFlow:
    def run_skill(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """返回Dict[str, Any]，类型不安全"""
        return self._coordinator.execute_skill(skill_name, params or {})

    def run_workflow(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """返回Dict[str, Any]，类型不安全"""
        tasks = workflow_def.get("tasks", [])
        return self._orchestrator.execute(tasks)
```

**问题分析**：
```python
# ❌ 类型不安全
result = lingflow.run_skill("echo", {"message": "hello"})
# result是Dict[str, Any]，IDE不知道里面有什么

# ❌ 无法区分成功和失败
result = lingflow.run_skill("invalid_skill", {})
# 失败时返回什么？{'error': '...'} 还是抛出异常？

# ❌ 无法类型提示
# IDE无法提示result有哪些键
result["data"]  # IDE不知道data存在
```

---

### 1.3 问题2：配置使用字典

**当前代码**：
```python
class LingFlow:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """config被忽略，实际未使用"""
        self._coordinator = AgentCoordinator()  # ❌ 硬编码
        self._orchestrator = WorkflowOrchestrator(self._coordinator)
```

**问题分析**：
```python
# ❌ 无类型安全
config = {
    "max_parallel": 10,  # 整数
    "timeout": "600",    # 字符串 - 类型错误！
    "unknown_key": "xxx" # 拼写错误 - 无验证！
}

# ❌ 无文档提示
# 用户不知道有哪些配置项，有哪些有效值

# ❌ 无默认值
# 用户必须提供完整的配置

# ❌ 无法验证
# 配置错误只能在运行时发现
```

---

### 1.4 问题3：技能接口不统一

**当前状态**：
- 无统一的技能基类
- 技能可以是函数、类、模块
- 无参数验证
- 无错误处理标准

**问题分析**：
```python
# 技能1: 简单函数
def my_skill(params):
    return {"result": "ok"}

# 技能2: 类
class MySkill:
    def execute(self, params):
        return {"result": "ok"}

# 技能3: 模块
# skills/my_skill.py
def run(params):
    return {"result": "ok"}

# ❌ 三种形式，难以维护
# ❌ 无统一的参数验证
# ❌ 无统一的错误处理
# ❌ 难以添加钩子（pre_execute, post_execute）
```

---

### 1.5 问题4：全局状态暴露

**当前代码**：
```python
class AgentCoordinator:
    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or AgentRegistry()  # ❌ 公开
        self.task_queue: List[Task] = []  # ❌ 公开
        self.completed_tasks: Dict[str, TaskResult] = {}  # ❌ 公开
        self.failed_tasks: Dict[str, TaskResult] = {}  # ❌ 公开
        self.compressor = ContextCompressor()  # ❌ 公开
```

**问题分析**：
```python
# ❌ 外部可以直接修改内部状态
coordinator = AgentCoordinator()
coordinator.task_queue.clear()  # 直接清空任务队列
coordinator.completed_tasks = {}  # 直接覆盖已完成任务

# ❌ 封装泄漏
coordinator.compressor.compress(context)  # 直接访问内部组件

# ❌ 难以测试
# 无法mock内部组件
# 无法隔离状态
```

---

## 二、方案设计

### 2.1 设计原则

| 原则 | 说明 |
|------|------|
| 🎯 **聚焦** | 只解决4个封装问题，不做额外功能 |
| 🐍 **Pythonic** | 符合Python习惯，不照搬其他语言 |
| 🔄 **兼容** | 完全向后兼容，旧代码无需修改 |
| 📈 **渐进** | 新旧API共存，逐步迁移 |
| ⏱️ **快速** | 6周完成，风险可控 |

**不做什么**：
- ❌ 不做缓存系统（非封装问题）
- ❌ 不做监控系统（非封装问题）
- ❌ 不做插件系统（非封装问题）
- ❌ 不做配置热重载（非封装问题）
- ❌ 不做双模式API（非封装问题）
- ❌ 不做性能优化（非封装问题）
- ❌ 不做复杂的Result类型（过度设计）

---

### 2.2 方案1：统一返回类型

**设计目标**：
- 提供类型安全的返回值
- 支持成功/失败状态
- 简单、易用、符合Python习惯

**方案选择**：
- ❌ Rust风格的Result（过度设计，不符合Python习惯）
- ❌ try/except（Python习惯，但不够结构化）
- ✅ 简化的Result类型（类型安全 + Python习惯）

**实现**：

```python
# lingflow/core/types.py

from dataclasses import dataclass, field
from typing import Generic, TypeVar, Optional, Dict, Any

T = TypeVar('T')


@dataclass
class Result(Generic[T]):
    """简化的结果类型

    Features:
        - 类型安全（泛型）
        - 成功/失败状态
        - 错误信息
        - Python习惯

    Examples:
        >>> # 成功
        >>> result = Result.ok({"value": 42})
        >>> result.success  # True
        >>> result.data  # {"value": 42}

        >>> # 失败
        >>> result = Result.fail("Operation failed")
        >>> result.success  # False
        >>> result.error  # "Operation failed"

        >>> # 类型提示
        >>> result: Result[int] = Result.ok(42)
        >>> value: int = result.unwrap()
    """

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    code: str = "OK"
    details: Dict[str, Any] = field(default_factory=dict)

    # ==================== 工厂方法 ====================

    @classmethod
    def ok(cls, data: T, **details) -> "Result[T]":
        """创建成功结果"""
        return cls(success=True, data=data, code="OK", details=details)

    @classmethod
    def fail(cls, error: str, code: str = "ERROR", **details) -> "Result[T]":
        """创建失败结果"""
        return cls(success=False, data=None, error=error, code=code, details=details)

    # ==================== 属性 ====================

    @property
    def is_ok(self) -> bool:
        """是否成功"""
        return self.success

    @property
    def is_error(self) -> bool:
        """是否失败"""
        return not self.success

    # ==================== 方法 ====================

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（向后兼容）"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "code": self.code,
            "details": self.details,
        }


class LingFlowError(Exception):
    """LingFlow异常"""

    def __init__(self, message: str, *, code: str = "LF000", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(f"[{code}] {message}")
```

**使用示例**：

```python
# 新API（推荐）
from lingflow import LingFlow, Result

lf = LingFlow()

# 执行技能
result: Result[Dict[str, Any]] = lf.run_skill("echo", {"message": "hello"})

if result.success:
    print(f"Success: {result.data}")
else:
    print(f"Error: {result.error}")

# 链式调用（简单）
result = Result.ok("  hello  ")
print(result.unwrap().strip().upper())  # "HELLO"

# 兼容旧代码（仍然支持）
result_dict = lf.run_skill("echo", {"message": "hello"})
# 返回Dict[str, Any]，但内部使用Result实现
```

**向后兼容**：
```python
# 旧代码仍然可以工作
result = lingflow.run_skill("echo", {"message": "hello"})
# result仍然是Dict[str, Any]

# 内部实现
class LingFlow:
    def run_skill(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """向后兼容：返回Dict"""
        result = self._run_skill_impl(skill_name, params)
        return result.to_dict()  # 转换为Dict

    def run_skill_typed(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Result[Dict[str, Any]]:
        """新API：返回Result"""
        return self._run_skill_impl(skill_name, params)

    def _run_skill_impl(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Result[Dict[str, Any]]:
        """内部实现"""
        try:
            # 执行技能
            data = self._coordinator.execute_skill(skill_name, params or {})
            return Result.ok(data)
        except Exception as e:
            return Result.fail(str(e))
```

---

### 2.3 方案2：类型安全的配置

**设计目标**：
- 类型安全的配置
- 支持验证
- 支持默认值
- 符合Python习惯

**实现**：

```python
# lingflow/core/config.py

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class LingFlowConfig:
    """LingFlow配置类（类型安全）"""

    # 协调器配置
    max_parallel: int = 2
    max_iterations: int = 100
    workflow_timeout: float = 600.0

    # 技能配置
    skills_path: str = "skills"
    skill_timeout: float = 30.0
    skill_cache_enabled: bool = False

    # 代理配置
    agent_timeout: float = 300.0
    agent_context_limit: int = 8000

    # 压缩配置
    compression_enabled: bool = True
    compression_target_tokens: int = 4000

    # 日志配置
    log_level: str = "INFO"

    def validate(self) -> None:
        """验证配置"""
        if self.max_parallel < 1:
            raise ValueError("max_parallel must be >= 1")
        if self.skill_timeout < 0:
            raise ValueError("skill_timeout must be >= 0")
        if self.agent_timeout < 0:
            raise ValueError("agent_timeout must be >= 0")
        if self.compression_target_tokens < 1000:
            raise ValueError("compression_target_tokens must be >= 1000")

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "LingFlowConfig":
        """从字典创建配置（兼容旧API）"""
        # 过滤未知键
        valid_keys = {f.name for f in cls.__dataclass_fields__}
        filtered_config = {k: v for k, v in config.items() if k in valid_keys}

        # 创建配置对象
        return cls(**filtered_config)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
```

**使用示例**：

```python
# 方式1: 使用默认配置
config = LingFlowConfig()  # 使用所有默认值

# 方式2: 指定部分配置
config = LingFlowConfig(
    max_parallel=4,
    skill_timeout=60.0
)

# 方式3: 从字典创建（兼容旧API）
old_config_dict = {
    "max_parallel": 4,
    "skill_timeout": 60.0,
    "unknown_key": "xxx"  # 自动过滤
}
config = LingFlowConfig.from_dict(old_config_dict)

# 方式4: 验证配置
try:
    config.validate()
except ValueError as e:
    print(f"Invalid config: {e}")

# 在LingFlow中使用
lf = LingFlow(config=config)

# 或者兼容旧API
lf = LingFlow(config=config.to_dict())
```

**说明**：配置的文件加载和保存由应用层处理，不作为 LingFlowConfig 的内置方法，以避免引入额外的依赖。

应用层示例：

```python
import yaml

# 应用层可选的文件I/O功能
def load_config_from_yaml(file_path: str) -> LingFlowConfig:
    """应用层：从YAML文件加载配置（需要安装PyYAML）"""
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return LingFlowConfig(**data)

def save_config_to_yaml(config: LingFlowConfig, file_path: str):
    """应用层：保存配置到YAML文件（需要安装PyYAML）"""
    with open(file_path, 'w') as f:
        yaml.dump(config.to_dict(), f)
```

**YAML配置示例**：

```yaml
# config.yaml
max_parallel: 4
skill_timeout: 60.0
agent_timeout: 300.0
compression_enabled: true
log_level: "INFO"
```

---

### 2.4 方案3：标准化技能接口

**设计目标**：
- 统一的技能接口
- 支持参数验证
- 支持错误处理
- 支持现有的函数式技能

**设计原则**：
- **推荐使用 BaseSkill**：新技能推荐继承 BaseSkill 获得标准化能力
- **不强制继承**：函数式技能仍然完全支持，不破坏现有代码
- **渐进式迁移**：现有技能可以逐步迁移到类式，无需一次性重构
- **实用优先**：BaseSkill 只提供核心功能，避免过度设计

**实现**：

```python
# lingflow/core/skill.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional, Union
from dataclasses import dataclass

from .types import Result


@dataclass
class SkillContext:
    """技能执行上下文"""
    skill_name: str
    params: Dict[str, Any]
    working_dir: str
    metadata: Dict[str, Any] = None


class BaseSkill(ABC):
    """技能基类（轻量级）"""

    # 元数据
    name: str = "base-skill"
    description: str = "Base skill"
    version: str = "1.0.0"

    def execute(self, params: Dict[str, Any]) -> Result[Any]:
        """执行技能（默认实现）

        子类可以重写此方法或实现 _execute_impl
        """
        context = SkillContext(
            skill_name=self.name,
            params=params,
            working_dir="."
        )

        try:
            data = self._execute_impl(context)
            return Result.ok(data)
        except Exception as e:
            return Result.fail(str(e))

    def _execute_impl(self, context: SkillContext) -> Any:
        """执行技能的具体实现（子类实现）"""
        raise NotImplementedError("Subclass must implement _execute_impl")

    def validate_params(self, params: Dict[str, Any]) -> Result[None]:
        """验证参数（子类可选实现）"""
        return Result.ok(None)


class FunctionSkill(BaseSkill):
    """包装函数为技能"""

    def __init__(self, name: str, func: Callable[[Dict[str, Any]], Any], description: str = ""):
        self.name = name
        self._func = func
        self.description = description or f"Function skill: {name}"

    def _execute_impl(self, context: SkillContext) -> Any:
        """执行函数"""
        return self._func(context.params)


class SkillRegistry:
    """技能注册表（单例）"""

    _instance = None
    _skills: Dict[str, BaseSkill] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, skill: BaseSkill):
        """注册技能"""
        self._skills[skill.name] = skill

    def register_function(self, name: str, func: Callable[[Dict[str, Any]], Any], description: str = ""):
        """注册函数为技能"""
        skill = FunctionSkill(name, func, description)
        self.register(skill)

    def get(self, name: str) -> Optional[BaseSkill]:
        """获取技能"""
        return self._skills.get(name)

    def list(self) -> list[str]:
        """列出所有技能"""
        return list(self._skills.keys())


# 全局实例（向后兼容）
_skill_registry = SkillRegistry()


def register_skill(skill: BaseSkill):
    """注册技能（全局函数，向后兼容）"""
    _skill_registry.register(skill)


def register_function(name: str, func: Callable[[Dict[str, Any]], Any], description: str = ""):
    """注册函数为技能（全局函数，向后兼容）"""
    _skill_registry.register_function(name, func, description)


def get_skill(name: str) -> Optional[BaseSkill]:
    """获取技能（全局函数，向后兼容）"""
    return _skill_registry.get(name)
```

**使用示例**：

```python
# 方式1: 基于类
from lingflow.core.skill import BaseSkill, Result

class EchoSkill(BaseSkill):
    name = "echo"
    description = "Echo back input"

    def _execute_impl(self, context):
        message = context.params.get("message", "")
        return {"echo": message}

# 注册
register_skill(EchoSkill())

# 方式2: 基于函数（兼容旧技能）
def my_skill_func(params):
    message = params.get("message", "")
    return {"echo": message}

register_function("echo", my_skill_func, "Echo back input")

# 方式3: 带参数验证
class ValidatedSkill(BaseSkill):
    name = "calculator"

    def validate_params(self, params):
        if "operation" not in params:
            return Result.fail("Missing 'operation' parameter")
        if "a" not in params or "b" not in params:
            return Result.fail("Missing operands 'a' and/or 'b'")
        return Result.ok(None)

    def _execute_impl(self, context):
        op = context.params["operation"]
        a = context.params["a"]
        b = context.params["b"]

        if op == "add":
            return {"result": a + b}
        elif op == "multiply":
            return {"result": a * b}
        else:
            raise ValueError(f"Unknown operation: {op}")

# 使用
lf = LingFlow()
result = lf.run_skill("echo", {"message": "hello"})
```

**迁移现有技能**：

```python
# 旧技能（函数式）
# skills/echo/implementation.py
def run(params):
    message = params.get("message", "")
    return {"echo": message}

# 迁移方案1: 包装函数
# skills/echo/implementation.py
from lingflow.core.skill import register_function

def run(params):
    message = params.get("message", "")
    return {"echo": message}

register_function("echo", run, "Echo back input")

# 迁移方案2: 转换为类
# skills/echo/skill.py
from lingflow.core.skill import BaseSkill, register_skill

class EchoSkill(BaseSkill):
    name = "echo"
    description = "Echo back input"

    def _execute_impl(self, context):
        message = context.params.get("message", "")
        return {"echo": message}

register_skill(EchoSkill())
```

---

### 2.5 方案4：全局状态管理

**设计目标**：
- 隐藏内部状态
- 支持依赖注入
- 便于测试
- 向后兼容

**实现**：

```python
# lingflow/core/state.py

from typing import Optional, Dict, Any
from pathlib import Path


class Coordinator:
    """协调器接口"""

    def execute_skill(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        raise NotImplementedError


class Orchestrator:
    """编排器接口"""

    def execute(self, tasks: list) -> Dict[str, Any]:
        """执行工作流"""
        raise NotImplementedError


class LingFlowState:
    """LingFlow全局状态（单例）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # 内部状态（私有）
        self._coordinator: Optional[Coordinator] = None
        self._orchestrator: Optional[Orchestrator] = None
        self._config: Dict[str, Any] = {}

    def set_coordinator(self, coordinator: Coordinator):
        """设置协调器（依赖注入）"""
        self._coordinator = coordinator

    def get_coordinator(self) -> Coordinator:
        """获取协调器"""
        if self._coordinator is None:
            raise RuntimeError("Coordinator not initialized")
        return self._coordinator

    def set_orchestrator(self, orchestrator: Orchestrator):
        """设置编排器（依赖注入）"""
        self._orchestrator = orchestrator

    def get_orchestrator(self) -> Orchestrator:
        """获取编排器"""
        if self._orchestrator is None:
            raise RuntimeError("Orchestrator not initialized")
        return self._orchestrator

    def set_config(self, config: Dict[str, Any]):
        """设置配置"""
        self._config = config

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._config

    def reset(self):
        """重置状态（用于测试）"""
        self._coordinator = None
        self._orchestrator = None
        self._config = {}


# 全局实例（向后兼容）
_lingflow_state = LingFlowState()


def init_lingflow(config: Optional[Dict[str, Any]] = None):
    """初始化LingFlow（全局函数，向后兼容）"""
    from ..coordination.coordinator import AgentCoordinator
    from ..workflow.orchestrator import WorkflowOrchestrator

    state = LingFlowState()

    # 创建默认组件
    coordinator = AgentCoordinator()
    orchestrator = WorkflowOrchestrator(coordinator)

    # 设置到状态
    state.set_coordinator(coordinator)
    state.set_orchestrator(orchestrator)
    state.set_config(config or {})


def get_coordinator() -> Coordinator:
    """获取协调器（全局函数，向后兼容）"""
    return _lingflow_state.get_coordinator()


def get_orchestrator() -> Orchestrator:
    """获取编排器（全局函数，向后兼容）"""
    return _lingflow_state.get_orchestrator()
```

**修改AgentCoordinator**：

```python
# lingflow/coordination/coordinator.py

class AgentCoordinator:
    """代理协调器（隐藏内部状态）"""

    def __init__(self):
        # 所有内部状态改为私有
        self._registry = AgentRegistry()
        self._task_queue: List[Task] = []
        self._completed_tasks: Dict[str, TaskResult] = {}
        self._failed_tasks: Dict[str, TaskResult] = {}
        self._compressor = ContextCompressor()

    # 只暴露必要的方法
    def execute_skill(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能（公开方法）"""
        # ...
        pass

    # 隐藏内部状态的方法
    def _get_task_queue(self) -> List[Task]:
        """获取任务队列（私有方法）"""
        return self._task_queue

    def _get_completed_tasks(self) -> Dict[str, TaskResult]:
        """获取已完成任务（私有方法）"""
        return self._completed_tasks

    # 移除所有公开状态
    # 不再暴露：registry, task_queue, completed_tasks, failed_tasks, compressor
```

**向后兼容**：

```python
# 旧代码仍然可以工作
from lingflow.coordination.coordinator import AgentCoordinator

coordinator = AgentCoordinator()
result = coordinator.execute_skill("echo", {"message": "hello"})

# 但无法直接访问内部状态
# coordinator.task_queue  # AttributeError（已移除）
```

---

## 三、实施计划

### 3.1 分阶段实施（6周）

| 阶段 | 时间 | 内容 | 交付物 |
|------|------|------|--------|
| **阶段1** | 第1-2周 | Result类型 + 统一异常 | `lingflow/core/types.py` |
| **阶段2** | 第3周 | 配置系统 | `lingflow/core/config.py` |
| **阶段3** | 第4周 | 技能基类 | `lingflow/core/skill.py` |
| **阶段4** | 第5周 | 全局状态管理 | `lingflow/core/state.py` |
| **阶段5** | 第5-6周 | 适配器层 + 向后兼容 | `lingflow/core/adapters.py` |
| **阶段6** | 第6周 | 文档 + 测试 | 完整文档，测试覆盖80%+ |

---

### 3.2 阶段1：Result类型 + 统一异常（第1-2周）

**任务清单**：
- [ ] 创建`lingflow/core/types.py`
- [ ] 实现`Result`类
- [ ] 实现`LingFlowError`异常
- [ ] 编写单元测试
- [ ] 更新文档

**文件结构**：
```
lingflow/
├── core/
│   ├── __init__.py
│   └── types.py         # 新增
```

**测试**：
```python
# tests/test_result.py

def test_result_ok():
    result = Result.ok(42)
    assert result.success
    assert result.data == 42
    assert result.is_ok
    assert not result.is_error

def test_result_fail():
    result = Result.fail("Error")
    assert not result.success
    assert result.error == "Error"
    assert result.is_error
    assert not result.is_ok

def test_result_unwrap():
    result = Result.ok(42)
    assert result.unwrap() == 42

def test_result_unwrap_or():
    result = Result.fail("Error")
    assert result.unwrap_or(0) == 0
```

---

### 3.3 阶段2：配置系统（第3周）

**任务清单**：
- [ ] 创建`lingflow/core/config.py`
- [ ] 实现`LingFlowConfig`类
- [ ] 实现配置验证
- [ ] 支持YAML/JSON文件
- [ ] 编写单元测试
- [ ] 更新文档

**文件结构**：
```
lingflow/
├── core/
│   ├── __init__.py
│   ├── types.py
│   └── config.py       # 新增
```

**测试**：
```python
# tests/test_config.py

def test_config_default():
    config = LingFlowConfig()
    assert config.max_parallel == 2
    assert config.skill_timeout == 30.0

def test_config_validation():
    config = LingFlowConfig(max_parallel=0)
    with pytest.raises(ValueError):
        config.validate()

def test_config_from_dict():
    config_dict = {"max_parallel": 4, "skill_timeout": 60.0}
    config = LingFlowConfig.from_dict(config_dict)
    assert config.max_parallel == 4
    assert config.skill_timeout == 60.0

def test_config_from_file():
    config = LingFlowConfig.from_file("tests/fixtures/config.yaml")
    assert config.max_parallel == 4
```

---

### 3.4 阶段3：技能基类（第4周）

**任务清单**：
- [ ] 创建`lingflow/core/skill.py`
- [ ] 实现`BaseSkill`类
- [ ] 实现`FunctionSkill`类
- [ ] 实现`SkillRegistry`单例
- [ ] 迁移现有技能
- [ ] 编写单元测试
- [ ] 更新文档

**文件结构**：
```
lingflow/
├── core/
│   ├── __init__.py
│   ├── types.py
│   ├── config.py
│   └── skill.py       # 新增
```

**测试**：
```python
# tests/test_skill.py

def test_base_skill():
    skill = EchoSkill()
    result = skill.execute({"message": "hello"})
    assert result.success
    assert result.data == {"echo": "hello"}

def test_function_skill():
    def my_func(params):
        return {"echo": params.get("message", "")}

    skill = FunctionSkill("echo", my_func)
    result = skill.execute({"message": "hello"})
    assert result.success
    assert result.data == {"echo": "hello"}

def test_skill_registry():
    skill = EchoSkill()
    register_skill(skill)

    retrieved = get_skill("echo")
    assert retrieved is skill
```

---

### 3.5 阶段4：全局状态管理（第5周）

**任务清单**：
- [ ] 创建`lingflow/core/state.py`
- [ ] 实现`LingFlowState`单例
- [ ] 修改`AgentCoordinator`隐藏内部状态
- [ ] 实现依赖注入
- [ ] 编写单元测试
- [ ] 更新文档

**文件结构**：
```
lingflow/
├── core/
│   ├── __init__.py
│   ├── types.py
│   ├── config.py
│   ├── skill.py
│   └── state.py       # 新增
```

---

### 3.6 阶段5：适配器层 + 向后兼容（第5-6周）

**任务清单**：
- [ ] 修改`lingflow/__init__.py`添加新API
- [ ] 保留旧API（返回Dict）
- [ ] 实现适配器层
- [ ] 编写兼容性测试
- [ ] 更新文档

**修改`lingflow/__init__.py`**：

```python
# lingflow/__init__.py

from pathlib import Path
from typing import Any, Dict, Optional

from .coordination.coordinator import AgentCoordinator
from .workflow.orchestrator import WorkflowOrchestrator
from .core.types import Result, LingFlowError
from .core.config import LingFlowConfig
from .core.state import LingFlowState, init_lingflow


class LingFlow:
    """LingFlow 统一入口"""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_obj: Optional[LingFlowConfig] = None
    ):
        """初始化 LingFlow

        Args:
            config: 配置字典（旧API，向后兼容）
            config_obj: 配置对象（新API）
        """
        # 支持新配置
        if config_obj is not None:
            self.config = config_obj
        elif config is not None:
            self.config = LingFlowConfig.from_dict(config)
        else:
            self.config = LingFlowConfig()

        # 初始化
        init_lingflow(self.config.to_dict())
        state = LingFlowState()
        self._coordinator = state.get_coordinator()
        self._orchestrator = state.get_orchestrator()

    # ==================== 旧API（向后兼容）====================

    def run_skill(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行技能（旧API，返回Dict）"""
        result = self.run_skill_typed(skill_name, params)
        return result.to_dict()

    def run_workflow(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流（旧API，返回Dict）"""
        result = self.run_workflow_typed(workflow_def)
        return result.to_dict()

    def run_workflow_file(self, filepath: str) -> Dict[str, Any]:
        """执行工作流文件（旧API，返回Dict）"""
        result = self.run_workflow_file_typed(filepath)
        return result.to_dict()

    # ==================== 新API（类型安全）====================

    def run_skill_typed(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Result[Dict[str, Any]]:
        """执行技能（新API，返回Result）"""
        try:
            data = self._coordinator.execute_skill(skill_name, params or {})
            return Result.ok(data)
        except Exception as e:
            return Result.fail(str(e))

    def run_workflow_typed(self, workflow_def: Dict[str, Any]) -> Result[Dict[str, Any]]:
        """执行工作流（新API，返回Result）"""
        try:
            tasks = workflow_def.get("tasks", [])
            data = self._orchestrator.execute(tasks)
            return Result.ok(data)
        except Exception as e:
            return Result.fail(str(e))

    def run_workflow_file_typed(self, filepath: str) -> Result[Dict[str, Any]]:
        """执行工作流文件（新API，返回Result）"""
        import yaml

        base_dir = Path.cwd().resolve()
        validated_path = self._validate_filepath(filepath, base_dir)

        with open(validated_path, encoding="utf-8") as f:
            workflow_def = yaml.safe_load(f)

        return self.run_workflow_typed(workflow_def)

    # ==================== 私有方法 ====================

    def _validate_filepath(self, filepath: str, base_dir: Path) -> Path:
        """安全验证文件路径"""
        filepath_abs = (base_dir / filepath).resolve(strict=False)
        try:
            filepath_abs.relative_to(base_dir)
        except ValueError:
            raise ValueError(
                f"Access denied: {filepath} is outside allowed directory ({base_dir})"
            )

        if filepath_abs.exists() and filepath_abs.is_symlink():
            raise ValueError(f"Symbolic links not allowed: {filepath}")

        if not filepath_abs.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        return filepath_abs
```

---

### 3.7 阶段6：文档 + 测试（第6周）

**任务清单**：
- [ ] 更新README.md
- [ ] 编写迁移指南
- [ ] 编写API文档
- [ ] 编写示例代码
- [ ] 确保测试覆盖率>80%
- [ ] 编写CHANGELOG.md

---

## 四、风险与缓解

### 4.1 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| **技能迁移复杂** | 高 | 中 | 保留旧API，渐进式迁移 |
| **向后兼容性问题** | 高 | 低 | 充分的兼容性测试 |
| **性能下降** | 中 | 低 | 不引入额外开销 |
| **学习成本** | 低 | 中 | 详细的文档和示例 |
| **用户不接受** | 高 | 低 | 保留旧API，用户可选 |

---

### 4.2 缓解措施

**1. 完全向后兼容**
```python
# 旧代码无需修改
result = lingflow.run_skill("echo", {"message": "hello"})
# 仍然返回Dict[str, Any]

# 新代码可以渐进式迁移
result = lingflow.run_skill_typed("echo", {"message": "hello"})
# 返回Result[Dict[str, Any]]
```

**2. 渐进式迁移**
- 新旧API共存
- 用户可以选择何时迁移
- 提供迁移指南

**3. 充分测试**
- 单元测试覆盖率>80%
- 集成测试
- 兼容性测试

**4. 详细文档**
- API文档
- 迁移指南
- 示例代码

---

## 五、成功指标

### 5.1 技术指标

| 指标 | 当前 | 目标 | 测量方法 |
|------|------|------|---------|
| 类型覆盖率 | 0% | 60% | mypy检查 |
| 测试覆盖率（总体） | 60% | >75% | pytest-cov |
| - 核心逻辑 | 未知 | >80% | pytest-cov |
| - 技能系统 | 未知 | >70% | pytest-cov |
| - 工具函数 | 未知 | >70% | pytest-cov |
| - CLI/入口 | 未知 | >60% | pytest-cov |
| API一致性 | 低 | 高 | 代码审查 |
| 向后兼容性 | N/A | 100% | 兼容性测试 |

---

### 5.2 业务指标

| 指标 | 当前 | 目标 | 测量方法 |
|------|------|------|---------|
| 代码可读性 | 3/5 | 4/5 | 代码审查 |
| 开发效率 | 基准 | +20% | 用户反馈 |
| Bug数量 | 基准 | -30% | Bug追踪 |
| 用户满意度 | 基准 | +10% | 用户调研 |

---

## 六、总结

### 6.1 方案特点

| 特点 | 说明 |
|------|------|
| 🎯 **聚焦** | 只解决4个封装问题 |
| 🐍 **Pythonic** | 符合Python习惯 |
| 🔄 **兼容** | 完全向后兼容 |
| 📈 **渐进** | 渐进式迁移 |
| ⏱️ **快速** | 6周完成 |

---

### 6.2 与V4.0对比

| 维度 | V4.0（被否决） | V3.5（本方案） |
|------|---------------|---------------|
| **范围** | 2762行，8个创新点 | 4个核心问题 |
| **时间** | 12周 | 6周 |
| **兼容性** | 部分兼容 | 完全兼容 |
| **设计** | 过度设计 | 简化设计 |
| **可行性** | 低 | 高 |

---

### 6.3 下一步

1. **评审本方案** - 确认方案方向
2. **开始实施** - 按阶段计划执行
3. **持续测试** - 确保质量和兼容性
4. **迭代优化** - 根据反馈调整

---

**文档版本**: V1.0
**创建日期**: 2026-03-25
**作者**: AI Assistant
**状态**: 待评审
