# lingflow 核心模块 API 文档

版本: 3.6.0
更新日期: 2026-03-31

---

## 目录

- [核心类型 (lingflow.core.types)](#核心类型-lingflowcoretypes)
  - [Result](#result)
- [技能系统 (lingflow.core.skill)](#技能系统-lingflowcoreskill)
  - [BaseSkill](#baseskill)
  - [FunctionSkill](#functionskill)
  - [SkillContext](#skillcontext)
  - [SkillRegistry](#skillregistry)
  - [便捷函数](#便捷函数)
- [分层技能加载器 (lingflow.core.layered_skill_loader)](#分层技能加载器-lingflowcorelayered_skill_loader)
  - [LayeredSkillLoader](#layeredskillloader)
  - [SkillRouter](#skillrouter)
  - [配置类型](#配置类型)
  - [便捷函数](#便捷函数-1)
- [配置系统 (lingflow.core.config)](#配置系统-lingflowcoreconfig)
  - [lingflowConfig](#lingflowconfig)
- [合规性系统 (lingflow.core.constitution)](#合规性系统-lingflowcoreconstitution)
  - [Constitution](#constitution)
  - [ConstitutionalPrinciple](#constitutionalprinciple)
  - [ComplianceReport](#compliancereport)
  - [EnforcementLevel](#enforcementlevel)
- [合规性矩阵 (lingflow.core.compliance_matrix)](#合规性矩阵-lingflowcorecompliance_matrix)
  - [ComplianceMatrix](#compliancematrix)
  - [ComplianceEntry](#complianceentry)
  - [Implementation](#implementation)
  - [VerificationStatus](#verificationstatus)

---

## 核心类型 (lingflow.core.types)

lingflow 的标准化类型系统。

### Result

类型安全的成功/失败结果处理类。

```python
from lingflow.core.types import Result

# 创建成功结果
success = Result.ok(data={"key": "value"}, extra_info="...")

# 创建失败结果
failure = Result.fail(
    error="Something went wrong",
    code="ERR_001",
    context="additional context"
)

# 检查状态
if result.is_ok:
    print(result.data)

if result.is_error:
    print(result.error)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `is_ok` | `bool` | success 的别名 |
| `is_error` | `bool` | 是否为错误 |
| `data` | `Optional[T]` | 成功数据 |
| `error` | `Optional[str]` | 错误消息 |
| `code` | `str` | 错误代码 |
| `details` | `Dict[str, Any]` | 额外详情 |

#### 类方法

##### `Result.ok(data, **details)`

创建成功结果。

```python
result = Result.ok({"user": "alice"}, status="active")
```

##### `Result.fail(error, code="", **details)`

创建失败结果。

```python
result = Result.fail("User not found", code="404", user_id="123")
```

#### 实例方法

##### `to_dict()`

转换为字典。

```python
d = result.to_dict()
# {"success": True, "data": {...}, "error": None, ...}
```

---

## 技能系统 (lingflow.core.skill)

lingflow 的技能系统，支持基于类和基于函数的技能。

### BaseSkill

技能基类（推荐用于新技能）。

```python
from lingflow.core.skill import BaseSkill, SkillContext, Result

class MySkill(BaseSkill):
    """自定义技能示例"""
    name = "my-skill"
    description = "我的自定义技能"
    version = "1.0.0"

    def _execute_impl(self, context: SkillContext) -> Any:
        """实现技能逻辑"""
        params = context.params
        # 处理参数
        return {"result": "success"}

    def validate_params(self, params: dict) -> Result[None]:
        """可选的参数验证"""
        if "required_param" not in params:
            return Result.fail("缺少必需参数")
        return Result.ok(None)

# 使用
skill = MySkill()
result = skill.execute({"required_param": "value"})
```

#### 类属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | "base-skill" | 技能标识符 |
| `description` | `str` | "Base skill" | 技能描述 |
| `version` | `str` | "1.0.0" | 技能版本 |

#### 方法

##### `execute(params: Dict[str, Any]) -> Result[Any]`

执行技能。

```python
result = skill.execute({"param1": "value1", "param2": "value2"})
```

##### `_execute_impl(context: SkillContext) -> Any`

抽象方法：实现技能逻辑（必须子类实现）。

##### `validate_params(params: Dict[str, Any]) -> Result[None]`

验证参数（可选覆盖）。

---

### FunctionSkill

将函数包装为技能。

```python
from lingflow.core.skill import FunctionSkill, register_function

def my_function(params):
    """普通函数"""
    return {"output": params["input"] * 2}

# 创建 FunctionSkill
skill = FunctionSkill(
    name="double",
    func=my_function,
    description="将输入值翻倍"
)

# 或直接注册
register_function("double", my_function, "将输入值翻倍")
```

---

### SkillContext

技能执行上下文。

```python
@dataclass
class SkillContext:
    skill_name: str           # 技能名称
    params: Dict[str, Any]    # 参数字典
    working_dir: str = "."    # 工作目录
    metadata: Dict[str, Any]  # 额外元数据
```

---

### SkillRegistry

技能注册表（单例模式）。

```python
from lingflow.core.skill import SkillRegistry, BaseSkill

registry = SkillRegistry()

# 注册技能
registry.register(MySkill())

# 注册函数
registry.register_function("my-func", my_function, "描述")

# 获取技能
skill = registry.get("my-skill")

# 列出所有技能
names = registry.list()

# 检查技能是否存在
if registry.has("my-skill"):
    print("技能已注册")

# 清空注册表
registry.clear()
```

#### 方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `register(skill)` | `None` | 注册技能 |
| `register_function(name, func, description)` | `None` | 注册函数 |
| `get(name)` | `Optional[BaseSkill]` | 获取技能 |
| `list()` | `List[str]` | 列出所有技能名称 |
| `has(name)` | `bool` | 检查技能是否存在 |
| `clear()` | `None` | 清空注册表 |

---

### 便捷函数

```python
from lingflow.core.skill import register_skill, register_function, get_skill

# 注册技能
register_skill(MySkill())

# 注册函数
register_function("my-func", my_function, "描述")

# 获取技能
skill = get_skill("my-skill")
```

---

## 分层技能加载器 (lingflow.core.layered_skill_loader)

三层架构技能加载系统：
- **L1**: 核心调度层（5个技能）- 永不卸载
- **L2**: 专业能力层（12个技能）- 常驻内存
- **L3**: 扩展能力层（16个技能）- 按需加载/卸载

### LayeredSkillLoader

分层技能加载器。

```python
from lingflow.core.layered_skill_loader import LayeredSkillLoader

loader = LayeredSkillLoader()

# 加载技能
loader.load_skill("code-review")

# 标记任务完成
loader.mark_task_complete("code-review")

# 获取层级统计
stats = loader.get_layer_stats()
print(stats)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `L1_SKILLS` | `Set[str]` | L1 核心技能集合 |
| `L2_SKILLS` | `Set[str]` | L2 专业技能集合 |

#### 方法

##### `load_skill(skill_name: str) -> bool`

加载技能。

##### `unload_skill(skill_name: str) -> bool`

卸载技能。

##### `mark_task_complete(skill_name: str)`

标记任务完成（触发卸载逻辑）。

##### `get_layer_stats() -> Dict[str, Any]`

获取层级统计信息。

---

### SkillRouter

技能路由器。

```python
from lingflow.core.layered_skill_loader import SkillRouter

router = SkillRouter()

# 路由到技能
skill_name = router.route(
    input_text="请审查这段代码",
    active_skills={"code-review", "refactor"}
)
```

#### 方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `route(input_text, active_skills)` | `Optional[str]` | 路由到合适的技能 |
| `get_dependencies(skill_name)` | `List[str]` | 获取依赖链 |

---

### 配置类型

#### SkillLayer

技能分层枚举。

```python
from lingflow.core.layered_skill_loader import SkillLayer

SkillLayer.L1  # 核心调度层
SkillLayer.L2  # 专业能力层
SkillLayer.L3  # 扩展能力层
```

#### LoadingStrategy

加载策略枚举。

```python
from lingflow.core.layered_skill_loader import LoadingStrategy

LoadingStrategy.EAGER  # 启动时加载
LoadingStrategy.LAZY    # 按需加载
```

#### UnloadingStrategy

卸载策略枚举。

```python
from lingflow.core.layered_skill_loader import UnloadingStrategy

UnloadingStrategy.NEVER         # 永不卸载
UnloadingStrategy.AFTER_TASK    # 任务完成后卸载
UnloadingStrategy.IDLE_TIMEOUT  # 空闲超时后卸载
```

#### SkillConfig

技能配置数据类。

```python
@dataclass
class SkillConfig:
    name: str
    layer: SkillLayer
    category: str = ""
    description: str = ""
    triggers: List[str] = []
    loading_strategy: LoadingStrategy = LoadingStrategy.LAZY
    unloading_strategy: UnloadingStrategy = UnloadingStrategy.NEVER
    dependencies: List[str] = []
    timeout: int = 300
    priority: int = 5
```

---

### 便捷函数

```python
from lingflow.core.layered_skill_loader import (
    get_layered_loader,
    get_layer_stats,
    get_memory_usage,
    load_skill,
    unload_skill,
    mark_task_complete,
    route_skill
)

# 获取加载器
loader = get_layered_loader()

# 获取统计
stats = get_layer_stats()

# 获取内存使用
memory = get_memory_usage()

# 加载/卸载技能
load_skill("code-review")
unload_skill("code-review")
mark_task_complete("code-review")

# 路由技能
skill_name = route_skill("请审查这段代码")
```

---

## 配置系统 (lingflow.core.config)

类型安全的配置管理。

### lingflowConfig

lingflow 配置类。

```python
from lingflow.core.config import lingflowConfig

# 创建默认配置
config = lingflowConfig()

# 自定义配置
config = lingflowConfig(
    max_parallel=4,
    skill_timeout=60.0,
    log_level="DEBUG"
)

# 从字典创建
config = lingflowConfig.from_dict({
    "max_parallel": 4,
    "skill_cache_enabled": True
})

# 验证配置
config.validate()

# 转换为字典
config_dict = config.to_dict()
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_parallel` | `int` | 2 | 最大并行任务数 |
| `max_iterations` | `int` | 100 | 最大工作流迭代次数 |
| `workflow_timeout` | `float` | 600.0 | 工作流超时（秒） |
| `skills_path` | `str` | "skills" | 技能目录路径 |
| `skill_timeout` | `float` | 30.0 | 技能超时（秒） |
| `skill_cache_enabled` | `bool` | False | 启用技能缓存 |
| `agent_timeout` | `float` | 300.0 | 代理超时（秒） |
| `agent_context_limit` | `int` | 8000 | 代理上下文限制 |
| `compression_enabled` | `bool` | True | 启用上下文压缩 |
| `compression_target_tokens` | `int` | 4000 | 压缩目标 token 数 |
| `log_level` | `str` | "INFO" | 日志级别 |

#### 方法

##### `validate()`

验证配置值。

```python
config.validate()
# 如果无效，抛出 ValueError
```

##### `from_dict(config: Dict[str, Any]) -> lingflowConfig`

从字典创建配置（类方法）。

##### `to_dict() -> Dict[str, Any]`

转换为字典。

---

## 合规性系统 (lingflow.core.constitution)

基于宪法的合规性约束系统。

### Constitution

机器可读的安全宪法。

```python
from lingflow.core.constitution import Constitution

# 加载默认宪法
constitution = Constitution()

# 从文件加载
constitution = Constitution("path/to/constitution.yaml")

# 验证合规性
report = constitution.validate_code_file("app.py")

# 获取所有原则
principles = constitution.get_principles()

# 根据 CWE 查找原则
principle = constitution.get_principle_by_cwe("CWE-79")
```

#### 内置原则

| ID | CWE | 名称 | 强制级别 |
|----|-----|------|----------|
| SEC-001 | CWE-79 | XSS 防护 | MUST |
| SEC-002 | CWE-89 | SQL 注入防护 | MUST |
| SEC-003 | CWE-352 | CSRF 防护 | MUST |
| SEC-004 | CWE-327 | 弱加密算法 | MUST |
| SEC-005 | CWE-798 | 硬编码凭据 | MUST |
| SEC-006 | CWE-22 | 路径遍历 | MUST |
| SEC-007 | CWE-400 | 资源消耗控制 | SHOULD |
| SEC-008 | CWE-502 | 反序列化 | MUST |
| SEC-009 | CWE-287 | 身份验证 | MUST |
| SEC-010 | CWE-20 | 输入验证 | SHOULD |

#### 方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `validate_code_file(file_path)` | `ComplianceReport` | 验证代码文件 |
| `get_principles()` | `List[ConstitutionalPrinciple]` | 获取所有原则 |
| `get_principle_by_id(id)` | `Optional[ConstitutionalPrinciple]` | 按 ID 获取原则 |
| `get_principle_by_cwe(cwe)` | `Optional[ConstitutionalPrinciple]` | 按 CWE 获取原则 |

---

### ConstitutionalPrinciple

宪法原则数据类。

```python
@dataclass
class ConstitutionalPrinciple:
    id: str                              # 原则 ID
    cwe: str                             # CWE 标识符
    name: str                            # 原则名称
    level: EnforcementLevel              # 强制级别
    constraint: str                      # 约束描述
    implementation_pattern: str          # 实现模式
    rationale: str                       # 基本原理
```

---

### ComplianceReport

合规性报告。

```python
from lingflow.core.constitution import ComplianceReport

report = ComplianceReport(
    is_compliant=True,
    total_principles=10,
    compliant_principles=10,
    violations=[],
    coverage=1.0
)

# 获取摘要
summary = report.get_summary()
```

#### 方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `add_violation(violation)` | `None` | 添加违规项 |
| `get_summary()` | `Dict[str, Any]` | 获取摘要统计 |

---

### EnforcementLevel

强制级别枚举。

```python
from lingflow.core.constitution import EnforcementLevel

EnforcementLevel.MUST     # 不可协商的要求
EnforcementLevel.SHOULD   # 推荐但可有例外
EnforcementLevel.MAY      # 可选指南
```

---

## 合规性矩阵 (lingflow.core.compliance_matrix)

合规性追溯矩阵，持续追踪合规性实现。

### ComplianceMatrix

合规性矩阵。

```python
from lingflow.core.compliance_matrix import ComplianceMatrix, Implementation

# 创建或加载矩阵
matrix = ComplianceMatrix(".lingflow/compliance_matrix.json")

# 添加实现
implementation = Implementation(
    file="app.py",
    lines=[42, 43],
    technique="参数化查询",
    status=VerificationStatus.VERIFIED
)
matrix.add_implementation("SEC-002", implementation)

# 保存矩阵
matrix.save()

# 生成报告
report = matrix.generate_report()
```

#### 方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `add_implementation(principle_id, implementation)` | `None` | 添加实现 |
| `verify_implementation(principle_id, file, lines, verified_by)` | `None` | 验证实现 |
| `get_entry(principle_id)` | `Optional[ComplianceEntry]` | 获取条目 |
| `generate_report()` | `Dict[str, Any]` | 生成报告 |
| `save()` | `None` | 保存到文件 |

---

### ComplianceEntry

合规性条目。

```python
@dataclass
class ComplianceEntry:
    principle_id: str
    cwe: str
    principle_name: str
    level: str  # MUST, SHOULD, MAY
    implementations: List[Implementation]
    last_verified: Optional[str]
    coverage: float  # 0.0 到 1.0
```

#### 方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `add_implementation(implementation)` | `None` | 添加实现 |
| `update_coverage()` | `None` | 更新覆盖率 |
| `get_summary()` | `Dict[str, Any]` | 获取摘要 |

---

### Implementation

实现记录。

```python
@dataclass
class Implementation:
    file: str
    lines: List[int]
    technique: str
    status: VerificationStatus
    verified_at: Optional[str]
    verified_by: Optional[str]
    notes: Optional[str]
    hash: Optional[str]
```

#### 方法

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `calculate_hash(content)` | `None` | 计算内容哈希 |
| `is_verified()` | `bool` | 是否已验证 |

---

### VerificationStatus

验证状态枚举。

```python
from lingflow.core.compliance_matrix import VerificationStatus

VerificationStatus.UNVERIFIED  # 未验证
VerificationStatus.PENDING     # 待验证
VerificationStatus.VERIFIED    # 已验证
VerificationStatus.FAILED      # 验证失败
```

---

## 核心模块导出

```python
from lingflow.core import (
    # 类型
    Result,
    # 技能系统
    BaseSkill,
    FunctionSkill,
    SkillContext,
    SkillRegistry,
    get_skill,
    register_function,
    register_skill,
    # 分层加载器
    LayeredSkillLoader,
    get_layered_loader,
    get_layer_stats,
    get_memory_usage,
    layered_load_skill,
    layered_unload_skill,
    mark_task_complete,
    route_skill,
    # 配置
    lingflowConfig,
    # 合规性
    Constitution,
    ConstitutionalPrinciple,
    ComplianceReport,
    # 合规性矩阵
    ComplianceMatrix,
    # 异常
    lingflowError,
)
```

---

## 版本信息

- **lingflow.core**: 3.6.0
- **Python**: 3.8+

---

## 许可证

© 2026 lingflow Team. All rights reserved.
