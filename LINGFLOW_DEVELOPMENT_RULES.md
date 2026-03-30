# LingFlow 项目开发规则 v1.0

**文档版本**: 1.0.0
**创建日期**: 2026-03-29
**适用**: LingFlow 多智能体系统
**基于**: 智能知识系统开发规则 V4.0

---

## 目录

1. [项目特性](#1-项目特性)
2. [代码规范](#2-代码规范)
3. [多智能体系统规范](#3-多智能体系统规范)
4. [Git工作流](#4-git工作流)
5. [测试要求](#5-测试要求)
6. [性能规范](#6-性能规范)
7. [安全规范](#7-安全规范)
8. [文档要求](#8-文档要求)

---

## 1. 项目特性

### 1.1 项目概述

LingFlow 是一个多智能体编排系统，具有以下特性：

- **多智能体协作**: 支持多个 AI Agent 协同工作
- **插件化架构**: 模块化设计，易于扩展
- **工作流编排**: 复杂任务的可视化编排
- **分布式执行**: 支持本地和远程 Agent 执行
- **实时监控**: Agent 状态和性能监控

### 1.2 技术栈

- **语言**: Python 3.11+
- **异步框架**: asyncio
- **类型检查**: mypy (strict mode)
- **代码格式**: black (line-length=88)
- **代码检查**: flake8
- **测试框架**: pytest

### 1.3 目录结构

```
lingflow/
├── bootstrap.py         # 系统启动
├── cli.py              # 命令行接口
├── code_review/        # 代码审查模块
├── common/             # 通用工具
├── compression/        # 压缩模块
├── context/            # 上下文管理
├── coordination/       # 协调模块
├── core/               # 核心功能
├── feedback/           # 反馈系统
├── guardrail/          # 安全防护
├── monitoring/         # 监控系统
├── requirements/       # 依赖管理
├── testing/            # 测试模块
├── utils/              # 工具函数
└── workflow/           # 工作流引擎
```

---

## 2. 代码规范

### 2.1 Python 代码规范

遵循 PEP 8 标准，使用 Black 格式化：

```bash
# 格式化代码
black lingflow/

# 检查代码
flake8 lingflow/ --max-line-length=88 --ignore=E203,W503

# 类型检查
mypy lingflow/ --strict
```

### 2.2 必须遵守的规则

1. **类型注解**: 所有公共函数必须有类型注解

```python
from typing import List, Dict, Optional

async def execute_workflow(
    workflow_id: str,
    agents: List[str],
    context: Optional[Dict] = None
) -> Dict:
    """执行工作流"""
    ...
```

2. **异步优先**: I/O 操作必须使用 async/await

```python
# ✅ 正确
async def get_agent_status(agent_id: str) -> Dict:
    return await db.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)

# ❌ 错误
def get_agent_status(agent_id: str) -> Dict:
    return db.fetchrow("SELECT * FROM agents WHERE id = $1", agent_id)
```

3. **文档字符串**: 所有公共模块和函数必须有 docstring

```python
def coordinate_agents(task: Task, agents: List[Agent]) -> Result:
    """
    协调多个 Agent 执行任务

    Args:
        task: 要执行的任务
        agents: 可用的 Agent 列表

    Returns:
        执行结果，包含状态和输出

    Raises:
        CoordinationError: 协调失败时抛出
    """
    ...
```

### 2.3 代码复杂度限制

| 指标 | 限制 | 说明 |
|------|------|------|
| 函数行数 | < 50 | 超过必须拆分 |
| 圈复杂度 | < 10 | 嵌套层数 |
| 参数数量 | < 5 | 超过使用对象 |
| 异步嵌套 | < 3 | 避免回调地狱 |

---

## 3. 多智能体系统规范

### 3.1 Agent 设计原则

1. **单一职责**: 每个 Agent 专注于特定领域
2. **状态隔离**: Agent 之间不共享可变状态
3. **消息传递**: 通过消息进行通信
4. **错误隔离**: Agent 错误不应影响其他 Agent

### 3.2 Agent 接口规范

```python
from typing import Protocol

class Agent(Protocol):
    """Agent 接口协议"""

    async def initialize(self) -> None:
        """初始化 Agent"""
        ...

    async def process(self, task: Task) -> Result:
        """处理任务"""
        ...

    async def shutdown(self) -> None:
        """关闭 Agent"""
        ...

    @property
    def status(self) -> AgentStatus:
        """获取 Agent 状态"""
        ...
```

### 3.3 协调模式

1. **主从模式**: 一个主 Agent 协调多个从 Agent
2. **流水线模式**: Agent 按顺序处理任务
3. **并行模式**: 多个 Agent 并行处理
4. **投票模式**: 多个 Agent 投票决策

---

## 4. Git工作流

### 4.1 分支策略

```
main (生产分支)
├── develop (开发分支)
│   ├── feature/xxx (功能分支)
│   └── fix/xxx (修复分支)
```

### 4.2 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式（不影响代码运行的变动）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建过程或辅助工具的变动

**作用域 (scope)**:
- `agent`: Agent 相关
- `workflow`: 工作流相关
- `coordination`: 协调相关
- `monitoring`: 监控相关
- `core`: 核心功能
- `utils`: 工具函数

**示例**:
```
feat(agent): 添加新的代码审查 Agent

- 实现 Agent 基础接口
- 添加任务队列管理
- 实现状态监控

Closes #123
```

### 4.3 Hooks 检查

项目配置了以下 Git Hooks：

1. **pre-commit**: 代码质量检查
2. **commit-msg**: 提交消息格式验证
3. **pre-push**: 多仓库一致性检查

---

## 5. 测试要求

### 5.1 测试覆盖率

| 代码类型 | 覆盖率要求 |
|----------|------------|
| Agent 核心逻辑 | > 80% |
| 协调模块 | > 70% |
| 工作流引擎 | > 75% |
| 工具函数 | > 60% |

### 5.2 测试类型

1. **单元测试**: 测试单个函数和类
2. **集成测试**: 测试模块间交互
3. **端到端测试**: 测试完整工作流
4. **性能测试**: 测试系统性能

### 5.3 测试命名

```python
def test_<功能>_<场景>_<预期>() -> None:
    """测试函数命名规范"""
    ...

# 示例
def test_agent_process_success_returns_result() -> None:
    """测试 Agent 成功处理任务返回结果"""
    ...

def test_workflow_parallel_execution_all_agents_complete() -> None:
    """测试工作流并行执行所有 Agent 完成"""
    ...
```

---

## 6. 性能规范

### 6.1 性能目标

| 指标 | 目标 | 说明 |
|------|------|------|
| Agent 启动时间 | < 2s | 冷启动 |
| 任务分发延迟 | < 100ms | 内存队列 |
| Agent 通信延迟 | < 50ms | 本地通信 |
| 工作流执行 | > 1000 tasks/min | 吞吐量 |

### 6.2 性能优化原则

1. **异步优先**: 使用 asyncio 避免阻塞
2. **批量处理**: 批量处理任务减少开销
3. **缓存策略**: 合理使用缓存
4. **资源池化**: 使用连接池和对象池

---

## 7. 安全规范

### 7.1 输入验证

```python
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    """Agent 配置验证"""
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern="^(reviewer|executor|coordinator)$")
    max_tasks: int = Field(..., gt=0, le=100)
```

### 7.2 敏感信息保护

1. **禁止硬编码**: 密钥、密码不能硬编码
2. **环境变量**: 使用环境变量存储敏感信息
3. **密钥管理**: 使用密钥管理服务
4. **日志脱敏**: 日志中不记录敏感信息

### 7.3 Agent 隔离

1. **沙箱执行**: Agent 在受限环境中执行
2. **资源限制**: 限制 CPU、内存使用
3. **网络隔离**: 控制网络访问
4. **权限控制**: 最小权限原则

---

## 8. 文档要求

### 8.1 必需文档

| 文档 | 位置 | 说明 |
|------|------|------|
| README.md | 项目根目录 | 项目介绍 |
| ARCHITECTURE.md | docs/ | 架构设计 |
| API.md | docs/ | API 文档 |
| CONTRIBUTING.md | 项目根目录 | 贡献指南 |
| CHANGELOG.md | 项目根目录 | 变更日志 |

### 8.2 代码文档

1. **模块文档**: 每个 `__init__.py` 应有模块说明
2. **类文档**: 每个类应有 docstring
3. **函数文档**: 公共函数应有完整的 docstring
4. **注释**: 复杂逻辑应有注释说明

### 8.3 文档格式

使用 Markdown 格式，遵循 Google 文档风格：

```python
def coordinate_agents(
    primary: Agent,
    secondaries: List[Agent],
    timeout: float = 30.0
) -> CoordinationResult:
    """
    协调主 Agent 和辅助 Agent 执行任务

    主 Agent 负责任务分解和结果整合，辅助 Agent 负责子任务执行。
    协调过程使用消息传递模式，确保 Agent 之间的隔离性。

    Args:
        primary: 主 Agent，负责任务协调
        secondaries: 辅助 Agent 列表，执行子任务
        timeout: 超时时间（秒），默认 30 秒

    Returns:
        CoordinationResult: 协调结果，包含：
            - success: 是否成功
            - results: 各 Agent 的执行结果
            - metrics: 性能指标

    Raises:
        CoordinationTimeoutError: 协调超时
        AgentUnavailableError: Agent 不可用

    Example:
        >>> primary = CoordinatorAgent()
        >>> secondaries = [ExecutorAgent(), ReviewerAgent()]
        >>> result = await coordinate_agents(primary, secondaries)
        >>> print(result.success)
        True
    """
    ...
```

---

## 9. Hooks 系统说明

### 9.1 Pre-commit Hooks

检查项目：
- 代码格式
- 代码质量
- 类型检查
- 测试状态

### 9.2 Commit-msg Hooks

验证：
- 提交消息格式
- 必需字段存在性
- 消息长度限制

### 9.3 Pre-push Hooks

检查：
- 多仓库一致性（GitHub + Gitea）
- 版本号同步
- 测试通过确认

---

## 附录

### A. 快速开始

```bash
# 克隆项目
git clone http://zhinenggitea.iepose.cn/guangda/LingFlow.git
cd LingFlow

# 安装依赖
pip install -e .

# 运行测试
pytest

# 格式化代码
black lingflow/
```

### B. 开发工作流

```bash
# 创建功能分支
git checkout -b feature/new-agent

# 开发并提交
git add .
git commit -m "feat(agent): 添加新的 Agent"

# 推送到远程
git push origin feature/new-agent

# 创建 PR
# 等待代码审查和 CI 通过
```

### C. 常见问题

**Q: 如何调试 Agent？**
A: 使用 `--debug` 参数启用详细日志。

**Q: 如何添加新的 Agent？**
A: 继承 `Agent` 基类，实现必需方法。

**Q: 如何测试工作流？**
A: 使用 `pytest tests/workflows/` 运行工作流测试。

---

**文档版本**: 1.0.0
**创建日期**: 2026-03-29
**下次审查**: 2026-06-29
