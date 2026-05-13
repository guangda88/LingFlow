# Anthropic 长期运行代理研究对 lingflow 的启示

**日期**: 2026-03-22
**参考**: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
**lingflow 版本**: v3.2.0

---

## 📋 核心问题总结

Anthropic 面临的核心挑战：

1. **上下文窗口限制**：代理必须在离散的会话中工作，每个新会话开始时没有前一个会话的记忆
2. **过度一次性完成**：代理倾向于一次性做太多事情，导致上下文用尽，留下半实现的代码
3. **过早声明完成**：代理可能过早认为整个项目已完成
4. **状态不清晰**：新会话无法快速理解之前的工作状态

---

## 🎯 Anthropic 的解决方案

### 双代理架构

#### 1. Initializer Agent（初始化代理）
- **职责**：第一次运行时设置环境
- **输出**：
  - `init.sh` 脚本（启动开发服务器、运行基本测试）
  - `claude-progress.txt` 进度日志文件
  - 初始 git commit（显示添加的文件）
- **关键作用**：为所有后续代理建立基础

#### 2. Coding Agent（编码代理）
- **职责**：每次会话只做一个功能，留下清晰记录
- **行为**：
  - 增量式进度（每次只做一个功能）
  - Git commit 描述性消息
  - 在进度文件中写入总结
  - 留下干净状态（可合并到主分支的状态）

### 环境管理组件

#### 1. Feature List（功能列表）
- **格式**：JSON（比 Markdown 更稳定）
- **结构**：
  ```json
  {
    "category": "functional",
    "description": "功能描述",
    "steps": ["步骤1", "步骤2", ...],
    "passes": false
  }
  ```
- **规则**：
  - 初始化代理创建全面的功能列表
  - 编码代理只能修改 `passes` 字段
  - 强烈提示不允许删除或编辑测试

#### 2. 增量进度
- **策略**：一次只做一个功能
- **机制**：
  - Git commit 保存进度
  - 进度文件记录总结
  - 可使用 git 恢复坏状态

#### 3. 测试
- **要求**：端到端测试（不仅仅是单元测试）
- **工具**：浏览器自动化（Puppeteer MCP）
- **行为**：像真实用户一样测试

#### 4. 快速启动流程
每个会话开始时的标准步骤：
1. `pwd` - 查看工作目录
2. 读取 git log 和进度文件
3. 读取功能列表文件
4. 运行 init.sh 启动服务器
5. 执行基本端到端测试
6. 开始工作

---

## 💡 对 lingflow 的启示

### ✅ lingflow 已有的优势

1. **工作流系统**
   - ✅ 基于 YAML 的工作流定义
   - ✅ 支持任务依赖
   - ✅ 条件分支和循环迭代
   - ✅ 示例：`workflows/self_optimize.yaml`

2. **多代理协调**
   - ✅ `AgentCoordinator` 支持并行执行
   - ✅ 代理类型系统（implementation, review, testing 等）
   - ✅ 任务优先级和依赖管理

3. **技能系统**
   - ✅ 模块化的技能架构
   - ✅ 技能触发机制
   - ✅ 22+ 可用技能

4. **测试能力**
   - ✅ `test-runner` 技能
   - ✅ `test-driven-development` 技能（TDD 强制）
   - ✅ `verification-before-completion` 技能

---

### 🚀 需要改进的领域

#### 1. 进度持久化机制（高优先级）

**问题**：lingflow 缺少跨会话的进度跟踪

**建议实现**：

```python
# lingflow/common/progress_tracker.py

import json
import git
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class ProgressEntry:
    timestamp: str
    task_id: str
    action: str
    status: str
    output: str
    files_modified: List[str]

class ProgressTracker:
    """跨会话的进度跟踪器"""

    def __init__(self, project_path: str = "./"):
        self.project_path = Path(project_path)
        self.progress_file = self.project_path / ".lingflow" / "progress.json"
        self.progress_file.parent.mkdir(exist_ok=True)
        self.repo = git.Repo(self.project_path)

    def save_progress(self, entry: ProgressEntry):
        """保存进度条目"""
        progress = self.load_progress()
        progress["history"].append(asdict(entry))

        # 保留最近 100 条记录
        if len(progress["history"]) > 100:
            progress["history"] = progress["history"][-100:]

        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)

    def load_progress(self) -> Dict:
        """加载进度"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"history": [], "current_task": None}

    def get_recent_context(self, limit: int = 10) -> List[ProgressEntry]:
        """获取最近的进度上下文"""
        progress = self.load_progress()
        recent = progress["history"][-limit:]
        return [ProgressEntry(**entry) for entry in recent]

    def commit_with_message(self, message: str, files: List[str]):
        """创建 git commit 并记录进度"""
        # Git commit
        self.repo.index.add(files)
        commit = self.repo.index.commit(message)

        # 记录进度
        entry = ProgressEntry(
            timestamp=datetime.now().isoformat(),
            task_id=self.load_progress().get("current_task", "unknown"),
            action="commit",
            status="success",
            output=message,
            files_modified=files
        )
        self.save_progress(entry)

        return commit
```

**集成到工作流**：

```python
# lingflow/workflow/orchestrator.py

from lingflow.common.progress_tracker import ProgressTracker

class WorkflowOrchestrator:
    def __init__(self, coordinator: AgentCoordinator, project_path: str):
        self.coordinator = coordinator
        self.progress_tracker = ProgressTracker(project_path)

    async def execute_workflow(self, tasks: List[Task]) -> Dict[str, TaskResult]:
        """执行工作流（带进度跟踪）"""

        # 1. 开始工作流
        self.progress_tracker.save_progress(ProgressEntry(
            timestamp=datetime.now().isoformat(),
            task_id="workflow_start",
            action="start",
            status="in_progress",
            output=f"Starting workflow with {len(tasks)} tasks",
            files_modified=[]
        ))

        # 2. 执行任务
        for task in tasks:
            result = await self.execute_task_with_progress(task)

            # 3. 如果成功，记录并提交
            if result.success:
                self.progress_tracker.commit_with_message(
                    message=f"Complete task: {task.name}",
                    files=result.files_modified or []
                )

        return results
```

---

#### 2. 功能列表跟踪系统（高优先级）

**问题**：缺少结构化的功能状态跟踪

**建议实现**：

```python
# lingflow/common/feature_list.py

import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict

@dataclass
class Feature:
    id: str
    category: str  # "functional", "performance", "security", etc.
    description: str
    steps: List[str]
    status: str  # "pending", "in_progress", "passing", "failing"
    passes: bool
    dependencies: List[str] = None
    priority: int = 0

class FeatureManager:
    """功能列表管理器"""

    def __init__(self, project_path: str = "./"):
        self.project_path = Path(project_path)
        self.feature_file = self.project_path / ".lingflow" / "features.json"
        self.feature_file.parent.mkdir(exist_ok=True)

    def initialize_features(self, spec: str):
        """从规范初始化功能列表（Initializer Agent 使用）"""
        features = self._parse_spec_to_features(spec)

        with open(self.feature_file, 'w') as f:
            json.dump([asdict(f) for f in features], f, indent=2)

    def get_next_feature(self) -> Optional[Feature]:
        """获取下一个待处理的功能"""
        features = self.load_features()

        # 找到状态为 pending 的功能
        pending = [f for f in features if f.status == "pending"]
        if not pending:
            return None

        # 按优先级排序
        pending.sort(key=lambda f: f.priority, reverse=True)
        return pending[0]

    def update_feature_status(self, feature_id: str, status: str, passes: bool = False):
        """更新功能状态"""
        features = self.load_features()

        for feature in features:
            if feature.id == feature_id:
                feature.status = status
                if passes:
                    feature.passes = True
                break

        with open(self.feature_file, 'w') as f:
            json.dump([asdict(f) for f in features], f, indent=2)

    def load_features(self) -> List[Feature]:
        """加载所有功能"""
        if self.feature_file.exists():
            with open(self.feature_file, 'r') as f:
                data = json.load(f)
                return [Feature(**f) for f in data]
        return []
```

**YAML 工作流集成**：

```yaml
# workflows/long_running_project.yaml

name: 长期运行项目工作流
description: 按照功能列表逐步实现项目

tasks:
  # Initializer Agent 阶段
  - id: initialize_project
    skill: initializer
    params:
      spec: "{{spec}}"
      create_init_script: true
      setup_git: true

  # Coding Agent 循环
  - id: implement_next_feature
    skill: feature-implementation
    params:
      mode: "incremental"
      test_e2e: true
      commit: true
    condition: "{{features.has_pending}}"

  # 验证所有功能
  - id: verify_all_features
    skill: feature-verification
    params:
      test_type: "e2e"
    condition: "{{!features.has_pending}}"
```

---

#### 3. 增强测试能力（中优先级）

**问题**：缺少端到端测试和浏览器自动化

**建议实现**：

```python
# skills/e2e-testing/SKILL.md

---
name: e2e-testing
description: 执行端到端测试，使用浏览器自动化验证完整功能
---

# End-to-End Testing

## Overview

执行完整的功能测试，不仅仅是单元测试。使用浏览器自动化工具（如 Playwright、Puppeteer）模拟真实用户操作。

## Checklist

- [ ] 启动应用服务器（如果有）
- [ ] 使用浏览器自动化工具打开应用
- [ ] 执行用户场景的所有步骤
- [ ] 验证每个步骤的预期结果
- [ ] 截图记录测试结果
- [ ] 记录发现的任何问题
- [ ] 更新功能状态（passing/failing）

## Supported Browsers

- Chrome/Chromium
- Firefox
- Safari (macOS)
- Edge
```

**Python 实现**：

```python
# skills/e2e-testing/implementation.py

from playwright.sync_api import sync_playwright

class E2ETester:
    """端到端测试器"""

    def test_feature(self, feature: Feature, config: dict):
        """测试单个功能"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.get("headless", True))
            page = browser.new_page()

            # 执行功能步骤
            for step in feature.steps:
                result = self.execute_step(page, step)
                if not result.success:
                    return {
                        "feature_id": feature.id,
                        "status": "failing",
                        "error": result.error,
                        "screenshot": result.screenshot
                    }

            browser.close()
            return {
                "feature_id": feature.id,
                "status": "passing",
                "screenshot": None
            }

    def execute_step(self, page, step: str):
        """执行单个测试步骤"""
        # 实现步骤解析和执行逻辑
        pass
```

---

#### 4. 双代理模式实现（中优先级）

**建议实现**：

```python
# skills/initializer/SKILL.md

---
name: initializer
description: 初始化项目环境，设置功能列表、开发脚本和进度跟踪
---

# Initializer Agent

## Overview

这是第一次会话运行的专用代理。它负责：
1. 分析项目规范
2. 创建功能列表（JSON 格式）
3. 创建 init.sh 脚本（启动服务器、运行测试）
4. 初始化 git 仓库
5. 创建进度跟踪文件
6. 执行初始端到端测试

## Checklist

- [ ] 分析项目规范并分解为功能列表
- [ ] 创建 `.lingflow/features.json`
- [ ] 创建 `.lingflow/progress.json`
- [ ] 创建 `init.sh` 脚本
- [ ] 初始化 git 仓库（如果需要）
- [ ] 执行初始 commit
- [ ] 运行基本测试验证环境

## Output Files

- `.lingflow/features.json` - 功能列表
- `.lingflow/progress.json` - 进度日志
- `.lingflow/init.sh` - 初始化脚本
- `.lingflow/config.yaml` - 项目配置
```

```python
# skills/coding-agent/SKILL.md

---
name: coding-agent
description: 增量式编码代理，每次会话只实现一个功能
---

# Coding Agent

## Overview

每个会话只做一个功能，留下干净状态。遵循增量式开发原则。

## Session Startup Checklist

- [ ] 运行 `pwd` 确认工作目录
- [ ] 读取 `.lingflow/progress.json` 了解最近工作
- [ ] 读取 `.lingflow/features.json` 获取待处理功能
- [ ] 运行 `./.lingflow/init.sh` 启动服务器
- [ ] 执行基本端到端测试验证环境健康
- [ ] 选择最高优先级的待处理功能

## Feature Implementation

- [ ] 实现单个功能
- [ ] 编写并运行测试
- [ ] 端到端测试验证
- [ ] Git commit 描述性消息
- [ ] 更新 `.lingflow/progress.json`
- [ ] 更新功能状态（passing/failing）
- [ ] 留下干净状态（可合并到主分支）

## Hard Gates

- **每次只做一个功能**
- **必须通过端到端测试才能标记为 passing**
- **必须 git commit 每次变更**
- **不能删除或修改功能列表中的测试步骤**
```

---

#### 5. 快速上下文恢复（中优先级）

**建议实现**：

```python
# lingflow/common/context_recovery.py

class ContextRecovery:
    """上下文恢复工具"""

    @staticmethod
    def get_briefing(project_path: str) -> str:
        """生成快速简报，用于新会话启动"""
        tracker = ProgressTracker(project_path)
        feature_mgr = FeatureManager(project_path)

        # 获取最近进度
        recent = tracker.get_recent_context(limit=5)

        # 获取当前功能
        current_feature = feature_mgr.get_current_feature()

        # 获取挂起的任务
        pending_features = feature_mgr.get_pending_features()[:3]

        briefing = f"""
# lingflow 项目简报

## 最近工作
"""

        for entry in recent:
            briefing += f"- [{entry.timestamp}] {entry.action}: {entry.output}\n"

        briefing += f"\n## 当前功能\n"
        if current_feature:
            briefing += f"- **{current_feature.id}**: {current_feature.description}\n"
            briefing += f"  状态: {current_feature.status}\n"
            briefing += f"  进度: {current_feature.progress}\n"
        else:
            briefing += "- 无当前功能\n"

        briefing += f"\n## 待处理功能\n"
        for feature in pending_features:
            briefing += f"- **{feature.id}** (优先级 {feature.priority}): {feature.description}\n"

        briefing += f"\n## 下一步\n"
        briefing += "1. 运行 `./.lingflow/init.sh` 启动环境\n"
        briefing += "2. 执行基本测试验证环境\n"
        if current_feature:
            briefing += f"3. 继续功能: {current_feature.id}\n"
        else:
            briefing += "3. 开始下一个待处理功能\n"

        return briefing

    @staticmethod
    def print_briefing(project_path: str = "./"):
        """打印项目简报"""
        briefing = ContextRecovery.get_briefing(project_path)
        print(briefing)
```

**CLI 集成**：

```python
# cli.py

@cli.command()
def brief():
    """显示项目简报（快速上下文恢复）"""
    from lingflow.common.context_recovery import ContextRecovery

    ContextRecovery.print_briefing()

@cli.command()
def session():
    """启动新的工作会话"""
    from lingflow.common.context_recovery import ContextRecovery

    # 1. 显示简报
    ContextRecovery.print_briefing()

    # 2. 询问用户确认
    click.confirm("继续?", default=True, abort=True)

    # 3. 运行初始化脚本
    os.system("./.lingflow/init.sh")

    # 4. 进入交互模式
    # ... 实现
```

---

## 📊 实施优先级

### 第一阶段（高优先级）

1. **进度跟踪器**（`ProgressTracker`）
   - 预计时间：2-3 小时
   - 影响：解决跨会话记忆问题
   - 测试：创建会话，保存进度，恢复会话

2. **功能管理器**（`FeatureManager`）
   - 预计时间：3-4 小时
   - 影响：结构化功能状态跟踪
   - 测试：创建功能列表，更新状态，获取下一个功能

### 第二阶段（中优先级）

3. **双代理模式**
   - 预计时间：4-6 小时
   - 影响：明确的职责分离
   - 测试：初始化代理创建环境，编码代理实现功能

4. **上下文恢复工具**
   - 预计时间：2-3 小时
   - 影响：快速启动新会话
   - 测试：`lingflow brief` 命令

5. **端到端测试技能**
   - 预计时间：6-8 小时
   - 影响：更可靠的测试
   - 测试：浏览器自动化测试功能

### 第三阶段（低优先级）

6. **工作流增强**
   - 支持条件执行（基于功能状态）
   - 自动化测试和验证循环
   - 更好的错误恢复

7. **可视化仪表板**
   - 功能进度可视化
   - 测试通过率图表
   - 项目健康状态

---

## 🎯 关键差异对比

| 维度 | Anthropic 方案 | lingflow 现状 | 建议 |
|--------|---------------|----------------|------|
| 进度持久化 | `claude-progress.txt` | ❌ 缺失 | ✅ `ProgressTracker` |
| 功能跟踪 | `features.json` | ❌ 缺失 | ✅ `FeatureManager` |
| 双代理模式 | Initializer + Coding | ⚠️ 未分离 | ✅ 分离技能 |
| 端到端测试 | Puppeteer MCP | ⚠️ 只有单元测试 | ✅ `e2e-testing` |
| 快速启动 | 标准化流程 | ⚠️ 部分 | ✅ `ContextRecovery` |
| Git 集成 | 每次变更提交 | ⚠️ 手动 | ✅ 自动 commit |
| 测试验证 | 严格要求 | ✅ TDD 强制 | ✅ 增强 E2E |
| 状态恢复 | 清晰的文件 | ❌ 不清晰 | ✅ 结构化恢复 |

---

## 🔄 工作流程对比

### Anthropic 模式

```
[初始化]
↓
创建功能列表 → init.sh → progress.txt → git init
↓
[会话 1]
读取进度 → 运行 init.sh → 选择下一个功能 → 实现 → 测试 → git commit → 更新进度
↓
[会话 2]
读取进度 → 运行 init.sh → 选择下一个功能 → 实现 → 测试 → git commit → 更新进度
↓
... 重复直到所有功能通过
```

### lingflow 改进后的模式

```yaml
# workflows/long_running_project.yaml

name: 长期运行项目
description: 结构化的长期项目执行

tasks:
  # Initializer 阶段（只运行一次）
  - id: initialize
    skill: initializer
    params:
      spec: "{{spec}}"
      outputs:
        - features.json
        - progress.json
        - init.sh

  # 增量开发循环
  - id: dev_cycle
    skill: coding-agent
    mode: "incremental"
    params:
      e2e_test: true
      auto_commit: true
    condition: "{{features.has_pending}}"
    on_complete:
      update_feature_status:
        id: "{{current_feature.id}}"
        status: "passing"

  # 最终验证
  - id: final_verification
    skill: e2e-testing
    params:
      scope: "all_features"
    condition: "{{!features.has_pending}}"
```

---

## 💻 代码示例：完整集成

### 初始化工作流

```python
# lingflow/workflow/long_running.py

from lingflow.common.progress_tracker import ProgressTracker
from lingflow.common.feature_list import FeatureManager
from lingflow.common.context_recovery import ContextRecovery

class LongRunningWorkflow:
    """长期运行项目工作流"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.progress = ProgressTracker(project_path)
        self.features = FeatureManager(project_path)
        self.recovery = ContextRecovery()

    def initialize(self, spec: str):
        """初始化项目（Initializer Agent）"""
        # 1. 创建功能列表
        self.features.initialize_features(spec)

        # 2. 保存初始进度
        self.progress.save_progress(ProgressEntry(
            timestamp=datetime.now().isoformat(),
            task_id="init",
            action="initialize",
            status="success",
            output=f"Initialized with {len(self.features.load_features())} features",
            files_modified=[".lingflow/features.json"]
        ))

        # 3. 创建 init.sh
        self._create_init_script()

    def start_session(self):
        """启动新的工作会话（Coding Agent）"""
        # 1. 显示简报
        self.recovery.print_briefing(self.project_path)

        # 2. 运行 init.sh
        os.system("./.lingflow/init.sh")

        # 3. 获取下一个功能
        feature = self.features.get_next_feature()
        if not feature:
            print("✅ 所有功能已完成！")
            return

        # 4. 实现功能
        self._implement_feature(feature)

    def _implement_feature(self, feature: Feature):
        """实现单个功能"""
        print(f"\n🚀 实现功能: {feature.id}")
        print(f"   {feature.description}")

        # 1. 标记为进行中
        self.features.update_feature_status(feature.id, "in_progress")

        # 2. 实现
        # ... 实现逻辑

        # 3. 测试
        test_result = self._test_feature(feature)

        # 4. 提交
        if test_result.passes:
            self.progress.commit_with_message(
                message=f"Complete {feature.id}: {feature.description}",
                files=test_result.files_modified
            )
            self.features.update_feature_status(feature.id, "passing", passes=True)
        else:
            self.features.update_feature_status(feature.id, "failing", passes=False)
```

---

## 📝 总结与行动项

### 核心启示

1. **跨会话记忆至关重要**：必须有结构化的进度跟踪和功能状态
2. **增量式开发**：一次只做一件事，留下干净状态
3. **双代理模式**：初始化和编码职责分离
4. **端到端测试**：不仅仅依赖单元测试
5. **快速上下文恢复**：标准化会话启动流程

### lingflow 优势

✅ 已有强大的工作流系统
✅ 已有多代理协调能力
✅ 已有技能触发机制
✅ 已有 TDD 强制机制

### 需要实现

❌ 进度跟踪器（`ProgressTracker`）
❌ 功能管理器（`FeatureManager`）
❌ 初始化器技能（`initializer`）
❌ 编码代理技能（`coding-agent`）
❌ 端到端测试（`e2e-testing`）
❌ 上下文恢复工具（`ContextRecovery`）

### 实施计划

**第 1 周**：
- [ ] 实现 `ProgressTracker`
- [ ] 实现 `FeatureManager`
- [ ] 单元测试

**第 2 周**：
- [ ] 实现 `initializer` 技能
- [ ] 实现 `coding-agent` 技能
- [ ] 集成测试

**第 3 周**：
- [ ] 实现 `e2e-testing` 技能
- [ ] 实现 `ContextRecovery`
- [ ] CLI 集成（`lingflow brief`, `lingflow session`）

**第 4 周**：
- [ ] 端到端测试
- [ ] 文档更新
- [ ] 示例项目

---

**结论**：Anthropic 的研究验证了 lingflow 的方向是正确的，但在进度持久化和状态管理方面需要加强。通过实施上述建议，lingflow 可以成为一个更强大的长期运行代理系统。
