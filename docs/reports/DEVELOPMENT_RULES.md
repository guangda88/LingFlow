# lingflow - 项目总体开发规则

**版本**: 3.5.0
**日期**: 2026-03-25
**适用**: V3.5 渐进式改进阶段
**状态**: 生效中

---

## 0. V3.5 版本说明

### V3.5 核心原则

| 原则 | 说明 |
|------|------|
| **渐进式改进** | 不破坏现有代码，平滑迁移 |
| **向后兼容** | 新旧API并存，不强制替换 |
| **推荐实践** | 引导使用新模式，但不强制 |
| **实用优先** | 解决实际问题，避免过度设计 |
| **警惕过度开发** | 简洁设计，避免不必要的抽象和复杂度 |

### 版本路线图

```
V3.3 (当前稳定)
    ↓
V3.5 (渐进改进) ← 当前目标
    ↓
V4.0 (未来优化)
```

### 与V4.0方案对比

| 特性 | V4.0方案 | V3.5方案 |
|------|----------|----------|
| Result类型 | 强制全部使用 | 推荐，新代码使用 |
| 异步支持 | 全面重写为异步 | 同步为主，异步可选 |
| 技能基类 | 强制继承 | 推荐继承，函数式仍支持 |
| 配置系统 | 强制lingflowConfig | 推荐使用，字典仍支持 |
| 实施周期 | 12周 | 4-6周 |
| 风险等级 | 高 | 低 |

---

## 1. 项目结构规范

### 当前实际目录结构

```
lingflow/
├── __init__.py             # 包入口，lingflow类
├── cli.py                  # CLI入口
├── common/                 # 公共模块
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── exceptions.py       # 异常定义
│   ├── logger.py           # 日志工具
│   ├── models.py           # 数据模型
│   └── skill_manager.py    # 技能管理
├── coordination/           # 协调模块
│   ├── __init__.py
│   ├── base.py            # 基础接口
│   ├── coordinator.py     # 协调器实现
│   ├── agent.py           # Agent实现
│   └── registry.py        # 注册表
├── compression/           # 压缩模块
│   ├── __init__.py
│   └── compressor.py      # 上下文压缩器
├── context/              # 上下文模块
│   ├── __init__.py
│   └── context.py         # 上下文管理
├── core/                 # 核心模块（V3.5新增）
│   ├── __init__.py
│   ├── types.py           # Result类型（V3.5新增）
│   ├── config.py          # Config类型（V3.5新增）
│   └── skill.py           # BaseSkill类（V3.5新增）
├── workflow/             # 工作流模块
│   ├── __init__.py
│   └── orchestrator.py    # 工作流编排器
├── guardrail/            # 安全防护
│   ├── __init__.py
├── tdd/                  # TDD工具
│   ├── __init__.py
├── utils/                # 工具函数
│   ├── __init__.py
│   └── performance.py
├── skills/               # 技能库
│   └── <skill_name>/     # 技能目录
│       ├── implementation.py  # 技能实现
│       └── SKILL.md           # 技能文档（lingflow标准）
├── agents/               # Agent配置
│   └── agents.json
├── hooks/                # 工作流钩子
│   └── hooks.json
├── tests/                # 测试代码（V3.5扩展）
│   └── (待补充)
├── docs/                 # 文档
│   ├── CORE_WORKFLOW.md
│   └── (其他文档)
├── DEVELOPMENT_RULES.md  # 本文件
├── CHANGELOG.md          # 变更日志
└── README.md             # 项目说明
```

### 文件命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| Python模块 | 小写+下划线 | `coordinator.py`, `skill_manager.py` |
| 类名 | 大驼峰 | `AgentCoordinator`, `lingflow` |
| 函数名 | 小写+下划线 | `execute_skill`, `compress_context` |
| 常量 | 大写+下划线 | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| 私有成员 | 前缀下划线 | `_internal_method`, `_config` |
| 技能目录 | 小写+短横线 | `code-analysis`, `test-driven` |

---

## 2. 代码编写规范

### Python代码规范

遵循 **基本PEP 8风格**，适配项目实际情况：

```python
# 缩进：4空格
# 行长度：最大120字符（实际可读性优先）
# 导入顺序：标准库 -> 第三方库 -> 本地模块
```

### 类型注解规范

**V3.5规则**：新代码**必须**添加类型注解

```python
from typing import Dict, List, Optional, Any, Callable

# ✅ 正确：完整类型注解
def execute_skill(
    skill_name: str,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """执行指定技能"""
    ...

# ✅ 可接受：最小类型注解
def execute_skill(skill_name: str, params=None):
    """执行指定技能"""
    ...

# ❌ 错误：无类型注解（新代码）
def execute_skill(skill_name, params):
    ...
```

### 文档字符串规范

**V3.5规则**：所有公共API必须有docstring

```python
def execute_skill(skill_name: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """执行指定技能

    Args:
        skill_name: 技能名称，如 "code-analysis"
        params: 技能参数字典，可选

    Returns:
        包含执行结果的字典，格式：{"success": bool, "data": ..., "error": ...}

    Raises:
        ValueError: 当技能名称无效时
        lingflowError: 当执行失败时

    Example:
        >>> result = execute_skill("echo", {"message": "hello"})
        >>> print(result["data"])
    """
```

### 错误处理规范

```python
# ✅ 正确：捕获具体异常，记录上下文
try:
    result = self._coordinator.execute_skill(skill_name, params)
    return result
except SkillNotFoundError as e:
    logger.error(f"技能不存在: {skill_name}")
    return {"success": False, "error": f"技能不存在: {skill_name}"}
except Exception as e:
    logger.error(f"执行技能失败: {skill_name}, {e}", exc_info=True)
    return {"success": False, "error": str(e)}

# ❌ 错误：捕获过于宽泛，吞掉异常
try:
    result = self._coordinator.execute_skill(skill_name, params)
except Exception:
    pass
```

### 数据类使用

**V3.5规则**：复杂数据结构推荐使用dataclass

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Task:
    """任务数据结构"""
    task_id: str
    name: str
    priority: int = 1
    dependencies: List[str] = field(default_factory=list)

# 使用
task = Task(task_id="t1", name="分析代码")
```

### 代码复杂度限制（指导性）

| 指标 | 建议值 | 硬性限制 |
|------|--------|----------|
| 函数行数 | < 50 | < 100 |
| 类行数 | < 300 | < 500 |
| 圈复杂度 | < 10 | < 15 |
| 参数数量 | < 5 | < 8 |

---

## 3. V3.5 类型系统（渐进引入）

### Result类型（推荐，非强制）

V3.5引入Result类型作为**推荐**的返回值封装方式。

**定义**（`lingflow/core/types.py`）：
```python
from typing import Generic, TypeVar, Optional, Dict, Any
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    """统一的执行结果封装（V3.5）"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    code: str = "OK"
    details: Dict[str, Any] = None

    @property
    def is_ok(self) -> bool:
        return self.success and self.code == "OK"

    @classmethod
    def ok(cls, data: T, **details) -> "Result[T]":
        return cls(success=True, data=data, details=details or {})

    @classmethod
    def fail(cls, error: str, code: str = "ERROR", **details) -> "Result[T]":
        return cls(success=False, error=error, code=code, details=details or {})
```

**使用方式**：
```python
# ✅ 推荐：新代码使用Result
def execute_skill(skill_name: str, params: Dict) -> Result[Dict]:
    """执行技能（V3.5风格）"""
    try:
        data = self._coordinator.execute_skill(skill_name, params)
        return Result.ok(data)
    except Exception as e:
        return Result.fail(str(e))

# ✅ 可接受：保持现有Dict返回
def execute_skill_legacy(skill_name: str, params: Dict) -> Dict:
    """执行技能（V3.x兼容）"""
    return self._coordinator.execute_skill(skill_name, params)
```

### 统一异常体系（推荐）

**定义**（`lingflow/common/exceptions.py`已存在）：
```python
class lingflowError(Exception):
    """lingflow基础异常"""
    pass

class SkillNotFoundError(lingflowError):
    """技能未找到异常"""
    pass

class ConfigurationError(lingflowError):
    """配置错误异常"""
    pass
```

---

## 4. 技能系统规范

### V3.5 技能实现方式

支持**两种方式并存**：

#### 方式一：函数式（V3.x兼容）

```python
# skills/code-analysis/implementation.py

def analyze_code(params):
    """分析代码 - 函数式实现

    Args:
        params: 包含target等参数的字典

    Returns:
        分析结果字典
    """
    target = params.get('target')
    if not target:
        return {"error": "请指定目标路径"}

    # 实现逻辑...
    return {"total_files": 10, "issues": []}
```

#### 方式二：类式（V3.5推荐）

```python
# skills/my-skill/implementation.py

from lingflow.core.skill import BaseSkill
from lingflow.core.types import Result

class MySkill(BaseSkill):
    """我的技能 - 类式实现"""

    name = "my-skill"
    description = "技能描述"
    version = "1.0.0"

    def execute(self, params: Dict) -> Result:
        """执行技能"""
        # 参数验证
        if not params.get('target'):
            return Result.fail("缺少target参数")

        # 实现逻辑
        result = self._do_work(params)
        return Result.ok(result)

    def _do_work(self, params):
        # 实际工作
        return {"status": "ok"}
```

### 技能文档规范（SKILL.md）

每个技能目录应包含`SKILL.md`：

```markdown
# Code Analysis

## 简介

分析Python代码的质量和复杂度。

## 触发关键词

- code-analysis
- analyze
- 代码分析

## 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| target | string | 是 | 要分析的目录路径 |
| metrics | list | 否 | 要计算的指标列表 |

## 返回值

```json
{
  "total_files": 10,
  "total_lines": 1000,
  "complexity": {...}
}
```

## 示例

```python
result = lf.run_skill("code-analysis", {
    "target": "./src",
    "metrics": ["complexity", "duplication"]
})
```
```

### 技能注册

技能在`skills.json`中注册（V3.5将实现）：
```json
{
  "code-analysis": {
    "name": "code-analysis",
    "description": "代码质量分析",
    "module": "skills.code-analysis.implementation",
    "function": "analyze_code",
    "triggers": ["code-analysis", "analyze"]
  }
}
```

---

## 5. Agent协调规范

### Agent配置（agents.json）

```json
{
  "name": "implementation",
  "description": "代码实现Agent",
  "model": "claude-sonnet-4-20250514",
  "max_tasks": 3,
  "context_limit": 8000,
  "timeout": 300,
  "capabilities": ["code_generation", "refactoring"]
}
```

### 任务优先级

```python
from enum import IntEnum

class TaskPriority(IntEnum):
    CRITICAL = 1  # 关键任务
    HIGH = 2      # 高优先级
    NORMAL = 3    # 正常优先级
    LOW = 4       # 低优先级
```

---

## 6. 测试规范

### V3.5测试策略

**核心原则**：实用优先，逐步提高覆盖率

| 代码类型 | V3.5目标 | 说明 |
|----------|----------|------|
| 核心逻辑 | > 80% | coordinator, orchestrator等 |
| 技能系统 | > 70% | 逐步提高 |
| 工具函数 | > 70% | utils, compression等 |
| CLI/入口 | > 60% | 基础覆盖 |

### 测试文件组织

```
tests/
├── test_coordinator.py     # 协调器测试
├── test_orchestrator.py    # 编排器测试
├── test_compressor.py      # 压缩器测试
├── test_skills/           # 技能测试
│   ├── test_code_analysis.py
│   └── ...
├── test_types.py          # Result类型测试（新增）
└── conftest.py            # pytest配置
```

### 测试示例

```python
# tests/test_coordinator.py

import pytest
from lingflow.coordination.coordinator import AgentCoordinator

class TestAgentCoordinator:
    """AgentCoordinator测试"""

    def test_execute_skill_with_valid_name(self):
        """测试执行有效技能"""
        coordinator = AgentCoordinator()
        result = coordinator.execute_skill("echo", {"message": "test"})
        assert result["success"] is True

    def test_execute_skill_with_invalid_name(self):
        """测试执行无效技能"""
        coordinator = AgentCoordinator()
        result = coordinator.execute_skill("nonexistent", {})
        assert result["success"] is False
        assert "error" in result
```

### TDD采用（推荐）

V3.5**推荐**TDD，但**不强制**：

```python
# 1. 先写测试
def test_result_ok():
    result = Result.ok(42)
    assert result.success
    assert result.data == 42

# 2. 实现功能
@classmethod
def ok(cls, data: T, **details):
    return cls(success=True, data=data, details=details or {})

# 3. 重构优化
# ...
```

---

## 7. 配置管理规范

### 当前配置方式（V3.x兼容）

```python
# ✅ 字典配置（当前方式）
config = {
    "max_parallel": 2,
    "agent_timeout": 300
}
lf = lingflow(config)
```

### V3.5配置类（推荐）

```python
# ✅ 配置类（V3.5新增）
from lingflow.common.config import lingflowConfig

config = lingflowConfig(
    max_parallel=2,
    agent_timeout=300
)
lf = lingflow(config)
```

### 配置验证

```python
# V3.5新增配置验证
config = lingflowConfig(max_parallel=0)  # 无效值
config.validate()  # 抛出 ConfigurationError
```

---

## 8. Git工作流规范

### 分支策略

```
master (主分支，稳定版本)
├── feature/xxx (功能分支)
├── fix/xxx (修复分支)
└── refactor/xxx (重构分支)
```

### 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug修复 |
| docs | 文档更新 |
| refactor | 重构 |
| test | 测试相关 |
| chore | 构建/工具 |

### 提交示例

```
feat(core): 添加Result类型支持

- 新增Result泛型类
- 添加ok()/fail()工厂方法
- 更新相关测试

Closes #123
```

### 提交前检查

```bash
# 1. 运行测试
python test_comprehensive.py

# 2. 快速验证
python verify_system_simple.py

# 3. 代码检查（可选）
flake8 lingflow/ --max-line-length=120

# 4. 同步更新文档（必做）
# - README.md 功能说明、版本号
# - 相关技术文档（docs/目录）
# - CHANGELOG.md 变更记录
```

### 提交前文档同步要求

> **重要**: 任何代码提交前，必须同步更新 README.md 和相关文档

| 变更类型 | 必须更新的文档 |
|----------|----------------|
| 新增功能 | README.md 功能列表、使用示例 |
| 修改API | README.md API说明、相关技术文档 |
| Bug修复 | CHANGELOG.md 修复记录 |
| 版本发布 | README.md 版本号、CHANGELOG.md、发布说明 |

---

## 9. 日志规范

### 日志级别使用

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: 开发调试信息
logger.debug(f"处理参数: {params}")

# INFO: 一般信息
logger.info(f"执行技能: {skill_name}")

# WARNING: 警告信息
logger.warning(f"配置使用默认值: {key}")

# ERROR: 错误信息
logger.error(f"技能执行失败: {error}", exc_info=True)
```

### 日志格式

```python
# ✅ 正确：包含上下文
logger.info(f"执行技能: {skill_name}, 参数: {params}")
logger.error(f"处理失败: {error}", exc_info=True)

# ❌ 错误：缺少上下文
logger.info("执行技能")
logger.error("失败")
```

---

## 10. 性能优化指南

### V3.5性能目标

| 指标 | 当前 | V3.5目标 |
|------|------|----------|
| 技能执行响应 | ~200ms | < 150ms |
| 上下文压缩 | ~500ms | < 300ms |
| 内存占用 | ~80MB | < 100MB |

### 优化建议

```python
# ✅ 使用缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def get_skill_info(skill_name: str):
    return self.skill_registry.get(skill_name)

# ✅ 批量处理
def execute_batch(skills, params_list):
    return [self.execute(s, p) for s, p in zip(skills, params_list)]

# ✅ 懒加载
class LazyLoader:
    def __getattr__(self, name):
        if name == "heavy_module":
            import heavy_module
            self.heavy_module = heavy_module
            return heavy_module
```

---

## 11. 代码审查清单

### 提交前自查

- [ ] 代码符合基本PEP 8风格
- [ ] 新函数有类型注解
- [ ] 公共API有docstring
- [ ] 有相应测试（新功能）
- [ ] 现有测试通过
- [ ] 无明显性能退化
- [ ] 日志信息合理
- [ ] **README.md 和相关文档已同步更新** ⚠️

### PR审查要点

- [ ] 代码逻辑正确性
- [ ] 错误处理完整性
- [ ] 边界条件考虑
- [ ] 安全问题检查
- [ ] 向后兼容性

---

## 12. 禁止事项

### 严格禁止

1. ❌ 硬编码密码、密钥等敏感信息
2. ❌ 跳过测试直接合并代码
3. ❌ 在master分支直接开发
4. ❌ 提交包含调试代码（print、断点等）
5. ❌ 破坏向后兼容性（V3.5核心原则）

### 不推荐

1. ⚠️ **过度开发** - 见下方详细说明
2. ⚠️ 过度优化 premature optimization
3. ⚠️ 过度抽象 over-abstraction
4. ⚠️ 添加不必要的外部依赖
5. ⚠️ 忽略类型注解（新代码）
6. ⚠️ 忽略文档字符串（公共API）

### 警惕过度开发 (Over-Engineering)

**原则**: 警惕过度开发，保持简洁实用

**什么是过度开发**:
- 为了"未来可能"的需求添加当前不需要的功能
- 过度抽象，创建多层不必要的抽象层
- 使用复杂的设计模式解决简单问题
- 追求完美的通用性而牺牲实用性

**识别过度开发的信号**:
1. 🚩 文件行数过大 (>500行)
2. 🚩 函数过长 (>50行)
3. 🚩 过多的抽象类和接口
4. 🚩 不必要的配置项
5. 🚩 过度使用设计模式

**审计标准** (基于2026-03-31审计):
- 代码复杂度评分: Phase 4 ≤ 3/10, Phase 5 ≤ 6/10
- 平均文件行数: < 400行
- 长函数比例: < 10%
- 抽象层数: ≤ 3层

**实用主义开发准则**:
```python
# ❌ 过度开发：为"未来可能"的需求设计
class AbstractAdapterFactory(ABC):
    """工厂的工厂接口 - 过度抽象"""
    @abstractmethod
    def create_factory(self) -> 'AdapterFactory':
        pass

class AdapterFactory(ABC):
    """抽象适配器工厂"""
    @abstractmethod
    def create_adapter(self) -> 'Adapter':
        pass

# ✅ 简洁实用：直接实现
def create_adapter(tool_type: str) -> 'Adapter':
    """创建适配器 - 简单直接"""
    if tool_type == "semgrep":
        return SemgrepAdapter()
    elif tool_type == "ruff":
        return RuffAdapter()
    raise ValueError(f"Unknown tool: {tool_type}")
```

**YOLO模式经验** (2026-03-31 Phase 4-5实施):
- ✅ 快速原型验证降低风险
- ✅ 先实现核心功能，再优化
- ✅ 简单测试足以保证质量
- ✅ 避免完美主义拖延进度
- ✅ 6小时完成10-12周工作量 (280-336x加速)

**记住**:
> "完美是优秀的敌人。" - Voltaire
> "过早优化是万恶之源。" - Donald Knuth
> "简单是终极的复杂。" - Leonardo da Vinci

---

## 13. V3.5 检查清单

### 新功能开发

- [ ] 确认在feature分支开发
- [ ] 添加类型注解
- [ ] 添加docstring
- [ ] 编写/更新测试
- [ ] 本地测试通过
- [ ] **同步更新 README.md 和相关文档** ⚠️

### Bug修复

- [ ] 在fix/xxx分支修复
- [ ] 添加回归测试
- [ ] 验证修复有效
- [ ] 确认无副作用

### 发布前

- [ ] 版本号更新
- [ ] CHANGELOG.md更新
- [ ] 文档更新
- [ ] 标签创建
- [ ] 推送到远程

---

## 14. 常用命令

### 开发

```bash
# 快速验证
python verify_system_simple.py

# 完整测试
python test_comprehensive.py

# 运行特定技能
python -m lingflow.cli skill code-analysis --target ./src
```

### 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_coordinator.py -v

# 测试覆盖率
pytest tests/ --cov=lingflow --cov-report=html
```

### 代码检查

```bash
# 类型检查
mypy lingflow/

# 代码风格
flake8 lingflow/ --max-line-length=120

# 复杂度检查
radon cc lingflow/ -a
```

---

## 15. 附录

### 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 核心流程 | `docs/CORE_WORKFLOW.md` | 核心业务流程 |
| Agent协调 | `docs/AGENT_COORDINATION_GUIDE.md` | Agent使用指南 |
| 压缩指南 | `docs/CONTEXT_COMPRESSION_GUIDE.md` | 上下文压缩 |
| 并行执行 | `docs/PARALLEL_EXECUTION_GUIDE.md` | 并行执行 |

### 联系方式

- 问题反馈：通过项目Issues
- 技术讨论：项目Discussions
- 文档贡献：Pull Request

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 3.5.0 | 2026-03-25 | V3.5渐进式改进规范 |
| 1.0.0 | 2026-03-25 | 初始版本 |

---

**本规则自 2026-03-25 起生效。**
**V3.5核心：渐进改进，向后兼容，实用优先。**
