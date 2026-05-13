# lingflow学习Claude Code的实战计划

> **基于Claude Code Python移植版本 (claw-code)的实际源码分析**
> **日期**: 2026-04-01
> **目标**: 从Claude Code的实际实现中学习，系统性地改进lingflow

---

## 第一部分：核心架构对比

### 1. Session管理系统

#### Claude Code实现（`session_store.py`）

```python
@dataclass(frozen=True)
class StoredSession:
    session_id: str
    messages: tuple[str, ...]
    input_tokens: int
    output_tokens: int

# 简洁但完整的设计：
# - JSON持久化
# - Token统计追踪
# - 不可变设计（frozen）
```

**核心思想**：
1. **不可变性**：使用frozen dataclass确保session不会被意外修改
2. **简洁性**：只存储必要信息，不保存整个状态树
3. **Token追踪**：内置使用量统计，便于成本控制

#### lingflow现状

```python
# lingflow/context/session.py
class Session:
    def __init__(self):
        self.context = {}  # ⚠️ 可变字典
        self.tasks = []    # ⚠️ 可变列表
        # ⚠️ 缺少token统计
```

**差距**：
- ❌ 缺少token统计
- ❌ 可变状态，容易出bug
- ❌ 没有简洁的持久化方案

#### 改进方案

```python
# lingflow/core/session_v2.py
from dataclasses import dataclass, field
from typing import Tuple
import json
from pathlib import Path
from datetime import datetime

@dataclass(frozen=True)
class SessionSnapshot:
    """不可变的Session快照"""
    session_id: str
    messages: Tuple[str, ...]
    input_tokens: int
    output_tokens: int
    created_at: str
    metadata: dict = field(default_factory=dict)

class SessionManager:
    """Session管理器"""

    def __init__(self, session_dir: Path = Path(".lingflow/sessions")):
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # 当前会话状态（可变）
        self._current_messages: list[str] = []
        self._current_input_tokens: int = 0
        self._current_output_tokens: int = 0

    def add_message(self, message: str, input_tokens: int = 0, output_tokens: int = 0):
        """添加消息"""
        self._current_messages.append(message)
        self._current_input_tokens += input_tokens
        self._current_output_tokens += output_tokens

    def create_snapshot(self, session_id: str) -> SessionSnapshot:
        """创建不可变快照"""
        return SessionSnapshot(
            session_id=session_id,
            messages=tuple(self._current_messages),
            input_tokens=self._current_input_tokens,
            output_tokens=self._current_output_tokens,
            created_at=datetime.now().isoformat()
        )

    def save_session(self, session_id: str) -> Path:
        """保存会话"""
        snapshot = self.create_snapshot(session_id)
        session_path = self.session_dir / f"{session_id}.json"

        with open(session_path, 'w') as f:
            json.dump({
                'session_id': snapshot.session_id,
                'messages': snapshot.messages,
                'input_tokens': snapshot.input_tokens,
                'output_tokens': snapshot.output_tokens,
                'created_at': snapshot.created_at,
                'metadata': snapshot.metadata
            }, f, indent=2)

        return session_path

    def load_session(self, session_id: str) -> SessionSnapshot:
        """加载会话"""
        session_path = self.session_dir / f"{session_id}.json"

        with open(session_path, 'r') as f:
            data = json.load(f)

        return SessionSnapshot(**data)

    def get_usage_summary(self) -> dict:
        """获取使用量摘要"""
        return {
            'messages': len(self._current_messages),
            'input_tokens': self._current_input_tokens,
            'output_tokens': self._current_output_tokens,
            'total_tokens': self._current_input_tokens + self._current_output_tokens
        }
```

---

### 2. QueryEngine架构

#### Claude Code实现（`query_engine.py`）

```python
@dataclass(frozen=True)
class QueryEngineConfig:
    max_turns: int = 8
    max_budget_tokens: int = 200000
    compact_after_turns: int = 12
    structured_output: bool = False
    structured_retry_limit: int = 2

@dataclass
class QueryEnginePort:
    manifest: PortManifest
    config: QueryEngineConfig
    session_id: str
    mutable_messages: list[str]
    total_usage: UsageSummary

    def submit_message(self, prompt, ...) -> TurnResult:
        # 1. 检查max_turns
        # 2. 格式化输出
        # 3. 更新usage
        # 4. 自动紧凑化消息
        # 5. 返回结构化结果
```

**核心思想**：
1. **配置驱动**：所有行为由config控制
2. **自动紧凑化**：超过阈值自动删除旧消息
3. **Token预算**：硬性限制防止成本失控
4. **结构化输出**：支持JSON格式输出

#### lingflow现状

```python
# lingflow/coordination/coordinator.py
class AgentCoordinator:
    def __init__(self):
        self.agents = []
        # ⚠️ 没有配置系统
        # ⚠️ 没有消息管理
        # ⚠️ 没有预算控制
```

#### 改进方案

```python
# lingflow/core/query_engine.py
from dataclasses import dataclass, field
from typing import Optional, Tuple
from enum import Enum

class StopReason(Enum):
    """停止原因"""
    COMPLETED = "completed"
    MAX_TURNS_REACHED = "max_turns_reached"
    MAX_BUDGET_REACHED = "max_budget_reached"
    USER_CANCELLED = "user_cancelled"
    ERROR = "error"

@dataclass(frozen=True)
class TurnConfig:
    """单轮配置"""
    max_turns: int = 8
    max_budget_tokens: int = 200000
    compact_after_turns: int = 12
    timeout_seconds: int = 120

@dataclass
class TurnResult:
    """单轮结果"""
    prompt: str
    output: str
    matched_tools: Tuple[str, ...]
    matched_agents: Tuple[str, ...]
    input_tokens: int
    output_tokens: int
    stop_reason: StopReason
    error: Optional[str] = None

class QueryEngine:
    """查询引擎"""

    def __init__(self, config: TurnConfig):
        self.config = config
        self._messages: list[str] = []
        self._input_tokens = 0
        self._output_tokens = 0
        self._turn_count = 0

    def submit(
        self,
        prompt: str,
        matched_tools: Tuple[str, ...] = (),
        matched_agents: Tuple[str, ...] = ()
    ) -> TurnResult:
        """提交查询"""

        # 1. 检查轮次限制
        if self._turn_count >= self.config.max_turns:
            return TurnResult(
                prompt=prompt,
                output=f"Max turns ({self.config.max_turns}) reached",
                matched_tools=matched_tools,
                matched_agents=matched_agents,
                input_tokens=0,
                output_tokens=0,
                stop_reason=StopReason.MAX_TURNS_REACHED
            )

        # 2. 执行查询（简化版）
        output = self._execute_query(prompt, matched_tools, matched_agents)

        # 3. 估算token使用
        input_tokens = len(prompt.split())
        output_tokens = len(output.split())

        # 4. 检查预算
        if (self._input_tokens + input_tokens +
            self._output_tokens + output_tokens) > self.config.max_budget_tokens:
            return TurnResult(
                prompt=prompt,
                output="Max budget reached",
                matched_tools=matched_tools,
                matched_agents=matched_agents,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                stop_reason=StopReason.MAX_BUDGET_REACHED
            )

        # 5. 更新状态
        self._messages.append(prompt)
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self._turn_count += 1

        # 6. 自动紧凑化
        if len(self._messages) > self.config.compact_after_turns:
            self._compact_messages()

        return TurnResult(
            prompt=prompt,
            output=output,
            matched_tools=matched_tools,
            matched_agents=matched_agents,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stop_reason=StopReason.COMPLETED
        )

    def _execute_query(
        self,
        prompt: str,
        matched_tools: Tuple[str, ...],
        matched_agents: Tuple[str, ...]
    ) -> str:
        """执行查询（实际实现会调用LLM）"""
        # 简化实现
        return f"Processed: {prompt[:50]}..."

    def _compact_messages(self):
        """紧凑化消息"""
        keep = self.config.compact_after_turns
        self._messages = self._messages[-keep:]

    def get_summary(self) -> dict:
        """获取摘要"""
        return {
            'turns': self._turn_count,
            'input_tokens': self._input_tokens,
            'output_tokens': self._output_tokens,
            'total_tokens': self._input_tokens + self._output_tokens,
            'messages_kept': len(self._messages)
        }
```

---

### 3. Prompt路由系统

#### Claude Code实现（`runtime.py`）

```python
class PortRuntime:
    def route_prompt(self, prompt: str, limit: int = 5) -> list[RoutedMatch]:
        # 1. Token化prompt
        tokens = {token.lower() for token in prompt.split()}

        # 2. 分别匹配commands和tools
        by_kind = {
            'command': self._collect_matches(tokens, PORTED_COMMANDS, 'command'),
            'tool': self._collect_matches(tokens, PORTED_TOOLS, 'tool'),
        }

        # 3. 选择最佳匹配
        selected: list[RoutedMatch] = []
        for kind in ('command', 'tool'):
            if by_kind[kind]:
                selected.append(by_kind[kind].pop(0))

        # 4. 填充剩余位置
        leftovers = sorted(by_kind.values(), key=lambda item: (-item.score, item.kind))
        selected.extend(leftovers[: max(0, limit - len(selected))])

        return selected[:limit]

    def _score(tokens: set, module: PortingModule) -> int:
        """评分函数"""
        haystacks = [module.name, module.source_hint, module.responsibility]
        score = 0
        for token in tokens:
            if any(token in haystack for haystack in haystacks):
                score += 1
        return score
```

**核心思想**：
1. **智能匹配**：基于关键词匹配，而非硬编码规则
2. **分类路由**：区分commands和tools
3. **评分排序**：根据相关度排序
4. **多样性**：优先选择不同类型的匹配

#### lingflow现状

```python
# lingflow/coordination/coordinator.py
def _find_agent_for_task(self, task: Task):
    # ⚠️ 简单的name匹配
    for agent in self.agents:
        if agent.config.name == task.agent_type:
            return agent
    return None
```

#### 改进方案

```python
# lingflow/core/router.py
from typing import List, Tuple
from dataclasses import dataclass
from lingflow.core.tools import BaseTool
from lingflow.coordination.agent import BaseAgent

@dataclass(frozen=True)
class RouteMatch:
    """路由匹配"""
    kind: str  # 'tool' or 'agent'
    name: str
    score: int
    description: str

class PromptRouter:
    """Prompt路由器"""

    def __init__(
        self,
        tools: List[BaseTool],
        agents: List[BaseAgent]
    ):
        self.tools = tools
        self.agents = agents

    def route(self, prompt: str, limit: int = 5) -> List[RouteMatch]:
        """路由prompt到合适的tools和agents"""

        # 1. Token化
        tokens = self._tokenize(prompt)

        # 2. 分别匹配tools和agents
        tool_matches = self._match_tools(tokens)
        agent_matches = self._match_agents(tokens)

        # 3. 选择最佳匹配
        matches = []

        # 优先选择不同类型
        if tool_matches:
            matches.append(tool_matches[0])
        if agent_matches:
            matches.append(agent_matches[0])

        # 4. 填充剩余位置
        all_matches = tool_matches[1:] + agent_matches[1:]
        all_matches.sort(key=lambda m: -m.score)
        matches.extend(all_matches[: limit - len(matches)])

        return matches[:limit]

    def _tokenize(self, prompt: str) -> set:
        """Token化prompt"""
        # 移除特殊字符，转小写
        import re
        cleaned = re.sub(r'[^\w\s]', ' ', prompt.lower())
        return set(cleaned.split())

    def _match_tools(self, tokens: set) -> List[RouteMatch]:
        """匹配tools"""
        matches = []
        for tool in self.tools:
            score = self._score(tokens, tool.name, tool.description)
            if score > 0:
                matches.append(RouteMatch(
                    kind='tool',
                    name=tool.name,
                    score=score,
                    description=tool.description
                ))
        matches.sort(key=lambda m: -m.score)
        return matches

    def _match_agents(self, tokens: set) -> List[RouteMatch]:
        """匹配agents"""
        matches = []
        for agent in self.agents:
            score = self._score(
                tokens,
                agent.config.name,
                agent.config.description
            )
            if score > 0:
                matches.append(RouteMatch(
                    kind='agent',
                    name=agent.config.name,
                    score=score,
                    description=agent.config.description
                ))
        matches.sort(key=lambda m: -m.score)
        return matches

    def _score(self, tokens: set, name: str, description: str) -> int:
        """评分"""
        haystack = f"{name} {description}".lower()
        score = 0
        for token in tokens:
            if token in haystack:
                score += 1
        return score
```

---

## 第二部分：实施计划

### 阶段1：核心基础设施（1-2周）

**目标**：建立lingflow的基础架构

#### 任务1.1：Session管理重构
- [ ] 实现`SessionManager`
- [ ] 添加token统计
- [ ] 实现session持久化
- [ ] 编写单元测试

#### 任务1.2：QueryEngine实现
- [ ] 实现`QueryEngine`类
- [ ] 添加配置系统
- [ ] 实现消息紧凑化
- [ ] 添加预算控制

#### 任务1.3：Prompt路由
- [ ] 实现`PromptRouter`
- [ ] 添加智能匹配
- [ ] 实现评分系统
- [ ] 集成到协调器

### 阶段2：Agent专业化（2-3周）

**目标**：实现专业化的Agent类型

#### 任务2.1：Agent类型系统
- [ ] 定义`AgentType`枚举
- [ ] 实现`AgentCapabilities`
- [ ] 添加工具权限控制
- [ ] 实现Agent基类

#### 任务2.2：专用Agent实现
- [ ] `ExploreAgent`（只读）
- [ ] `PlanAgent`（规划）
- [ ] `ExecuteAgent`（执行）
- [ ] `VerifyAgent`（验证）

#### 任务2.3：Agent通信
- [ ] 实现`MessageBus`
- [ ] 添加结构化消息
- [ ] 实现消息处理
- [ ] 添加广播机制

### 阶段3：高级特性（3-4周）

**目标**：添加高级功能

#### 任务3.1：错误处理
- [ ] 实现重试机制
- [ ] 添加恢复链
- [ ] 实现错误分类
- [ ] 添加降级策略

#### 任务3.2：性能优化
- [ ] 实现多级缓存
- [ ] 添加资源池
- [ ] 实现性能监控
- [ ] 添加性能报告

#### 任务3.3：安全增强
- [ ] 实现权限系统
- [ ] 添加审计日志
- [ ] 实现沙箱隔离
- [ ] 添加密钥管理

---

## 第三部分：快速开始指南

### 立即可以开始的3件事

#### 1. 实现Session管理（1天）

```bash
# 创建新文件
lingflow/core/session_v2.py

# 运行测试
pytest tests/test_session_v2.py -v
```

#### 2. 添加Token统计（半天）

```python
# 在现有代码中添加
class AgentCoordinator:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _update_token_stats(self, prompt: str, response: str):
        self.total_input_tokens += len(prompt.split())
        self.total_output_tokens += len(response.split())
```

#### 3. 实现Prompt路由（1天）

```python
# 创建新文件
lingflow/core/router.py

# 集成到协调器
class AgentCoordinator:
    def __init__(self):
        self.router = PromptRouter(tools, agents)

    def route_task(self, prompt: str) -> List[RouteMatch]:
        return self.router.route(prompt)
```

---

## 第四部分：学习资源

### 推荐阅读顺序

1. **核心文件**（按优先级）：
   - `src/session_store.py` - Session管理
   - `src/query_engine.py` - Query引擎
   - `src/runtime.py` - 运行时
   - `src/tools.py` - 工具系统

2. **架构文件**：
   - `src/models.py` - 数据模型
   - `src/context.py` - 上下文管理
   - `src/execution_registry.py` - 执行注册

3. **辅助文件**：
   - `src/tool_pool.py` - 工具池
   - `src/history.py` - 历史记录
   - `src/transcript.py` - 转录存储

### 实践建议

1. **边读边实现**：每看完一个文件，立即在lingflow中实现对应功能
2. **保持简洁**：不要过度设计，从最简单的实现开始
3. **测试驱动**：先写测试，再写实现
4. **文档同步**：实现的同时更新文档

---

## 总结

### 从Claude Code学到的3个最重要的设计思想

1. **不可变状态**
   - 使用frozen dataclass
   - 快照模式
   - 减少bug

2. **配置驱动**
   - 所有行为由配置控制
   - 易于测试和调试
   - 支持动态调整

3. **自动化管理**
   - 自动紧凑化消息
   - 自动token统计
   - 自动权限检查

### 立即行动

**今天就可以开始**：
1. 实现`SessionManager`类
2. 添加token统计到现有代码
3. 实现`PromptRouter`基础版

**本周完成**：
1. 完整的Session管理系统
2. 基础的QueryEngine
3. Prompt路由集成

**本月目标**：
1. 完成阶段1的所有任务
2. 开始阶段2的Agent专业化
3. 建立完整的测试覆盖

---

**文档版本**: v1.0
**最后更新**: 2026-04-01
**相关文档**:
- CLAUDE_CODE_AGENT_DESIGN_ANALYSIS.md
- CLAUDE_CODE_ADDITIONAL_DESIGN_INSIGHTS.md
