# LingFlow 发布形态演进路线图

**版本**: v1.0.0
**日期**: 2026-04-02
**核心理念**: "众智混元，万法灵通" - 让工程流能力触达更多开发者

---

## 📋 执行摘要

本文档基于 LingFlow 当前的发布形态（CLI、Python SDK、MCP Server），规划了**6 种新的发布形态**，以覆盖不同用户群体和使用场景。

### 现有形态 ✅

| 形态 | 状态 | 受众 | 特点 |
|------|------|------|------|
| **CLI 工具** | ✅ v3.8.0 | 命令行用户、脚本集成 | 直接、轻量，适合手动操作和 CI/CD |
| **Python SDK** | ✅ 内置 | Python 开发者 | 功能完整，与 CLI 共享核心库 |
| **MCP Server** | ✅ v1.3.0 | AI 助手（Claude、Cursor） | 自然语言交互，AI 原生 |

### 计划新增形态 🚀

| 形态 | 优先级 | 预计周期 | 状态 |
|------|--------|----------|------|
| **REST API 服务** | 🔴 P0 | 2周 | ⏳ 规划中 |
| **Docker 镜像** | 🔴 P0 | 1周 | ⏳ 规划中 |
| **PyPI 独立 SDK** | 🔴 P0 | 1周 | ⏳ 规划中 |
| **VSCode 插件** | 🟡 P1 | 3周 | ⏳ 规划中 |
| **Web 可视化** | 🟡 P1 | 4周 | ⏳ 规划中 |
| **技能市场** | 🟢 P2 | 6周 | ⏳ 规划中 |

---

## 🎯 用户群体覆盖策略

```
                    ┌─────────────────────────┐
                    │    非技术用户            │
                    │  (PM、架构师、管理层)    │
                    └────────────┬────────────┘
                                 │ Web UI
                    ┌────────────▼────────────┐
                    │    一线开发者           │
                    │  (编码、调试、提交)      │
                    └────────────┬────────────┘
                                 │ IDE 插件
                    ┌────────────▼────────────┐
                    │   Python 开发者         │
                    │  (脚本、Notebook)       │
                    └────────────┬────────────┘
                                 │ SDK / CLI
                    ┌────────────▼────────────┐
                    │   集成者                │
                    │  (CI/CD、内部系统)       │
                    └────────────┬────────────┘
                                 │ REST API
                    ┌────────────▼────────────┐
                    │   AI 用户               │
                    │  (Claude、Cursor)       │
                    └─────────────────────────┘
                                 │ MCP Server
```

---

## 📦 按模块的封装建议

### 1️⃣ 技能系统（33 Skills）

**最适合**: Python SDK、REST API、IDE 插件

| 发布形态 | 价值 | 优先级 |
|----------|------|--------|
| **Python SDK** | 提供简洁的技能执行接口 | 🔴 P0 |
| **REST API** | 跨语言调用 | 🔴 P0 |
| **VSCode 插件** | 右键菜单执行技能 | 🟡 P1 |

**技术方案**:
```python
# SDK 设计
class LingFlowSkillsClient:
    def list_skills(self, category: str = None) -> List[Skill]
    def execute_skill(self, name: str, **kwargs) -> SkillResult
    def execute_batch(self, tasks: List[Task]) -> List[SkillResult]

# REST API 端点
GET    /api/v1/skills              # 列出技能
GET    /api/v1/skills/{name}       # 获取技能详情
POST   /api/v1/skills/{name}/execute  # 执行技能
POST   /api/v1/skills/batch        # 批量执行
```

### 2️⃣ 工作流引擎（MultiWorkflow）

**最适合**: Web 可视化、REST API、IDE 插件

| 发布形态 | 价值 | 优先级 |
|----------|------|--------|
| **Web 工作流设计器** | 拖拽式编排 | 🟡 P1 |
| **REST API** | 异步执行、状态查询 | 🔴 P0 |
| **VSCode 插件** | 一键运行工作流 | 🟡 P1 |

**技术方案**:
```python
# SDK 设计
class LingFlowWorkflowsClient:
    def list_workflows(self, type_filter: str = None) -> List[Workflow]
    def run_workflow(self, id: str, params: dict, async: bool = True)
    def get_status(self, task_id: str) -> WorkflowStatus
    def create_workflow(self, definition: dict) -> Workflow

# REST API 端点
GET    /api/v1/workflows           # 列出工作流
POST   /api/v1/workflows/{id}/run  # 执行工作流
GET    /api/v1/tasks/{task_id}     # 查询任务状态
POST   /api/v1/workflows           # 创建自定义工作流
```

### 3️⃣ 自优化系统（LingMinOpt）

**最适合**: IDE 插件、REST API

| 发布形态 | 价值 | 优先级 |
|----------|------|--------|
| **VSCode 插件** | 实时显示优化建议 | 🟡 P1 |
| **REST API** | 批量优化、CI 集成 | 🔴 P0 |

**技术方案**:
```python
# SDK 设计
class LingFlowOptimizerClient:
    def check_optimization_needed(self, target: str) -> OptimizationReport
    def run_optimization(self, target: str, mode: str) -> OptimizationResult
    def get_suggestions(self, file_path: str) -> List[Suggestion]

# IDE 插件集成
# 在 VSCode 中显示问题建议（Code Lens）
# 提供 "Fix with LingFlow" 快捷操作
```

### 4️⃣ 情报系统（GitHub/npm Trends）

**最适合**: REST API、Web 可视化、定时推送

| 发布形态 | 价值 | 优先级 |
|----------|------|--------|
| **REST API** | 数据查询服务 | 🔴 P0 |
| **Web 仪表盘** | 趋势图表展示 | 🟡 P1 |
| **定时报告** | 邮件/IM 推送 | 🟢 P2 |

**技术方案**:
```python
# SDK 设计
class LingFlowIntelligenceClient:
    def get_github_trends(self, keywords: List[str]) -> List[Repo]
    def get_npm_trends(self, keywords: List[str]) -> List[Package]
    def subscribe_report(self, frequency: str, webhook: str)

# REST API 端点
GET    /api/v1/intelligence/github  # GitHub 趋势
GET    /api/v1/intelligence/npm     # npm 趋势
POST   /api/v1/intelligence/subscribe  # 订阅报告
```

### 5️⃣ 需求追溯（Requirements）

**最适合**: Web 可视化、REST API

| 发布形态 | 价值 | 优先级 |
|----------|------|--------|
| **Web 看板** | 需求管理界面 | 🟡 P1 |
| **REST API** | 外部系统集成 | 🔴 P0 |

**技术方案**:
```python
# SDK 设计
class LingFlowRequirementsClient:
    def create_requirement(self, **kwargs) -> Requirement
    def get_requirement(self, id: str) -> Requirement
    def update_requirement(self, id: str, **kwargs)
    def link_to_branch(self, req_id: str, branch: str)
    def get_traceability_graph(self, req_id: str) -> Graph

# Web UI
# 需求看板（类似 Trello）
# 追溯图（需求 → 分支 → 提交 → PR）
```

### 6️⃣ 代码审查（Code Review）

**最适合**: IDE 插件、REST API

| 发布形态 | 价值 | 优先级 |
|----------|------|--------|
| **VSCode 插件** | 实时审查结果高亮 | 🟡 P1 |
| **REST API** | PR 自动审查 | 🔴 P0 |

**技术方案**:
```python
# IDE 插件集成
# 在编辑器中显示：
# - 复杂度警告（波浪线）
# - 安全问题（红色）
# - 风格建议（黄色）
# - 一键修复建议（Code Action）
```

### 7️⃣ 测试框架（Testing）

**最适合**: CI/CD 集成、REST API

| 发布形态 | 价值 | 优先级 |
|----------|------|--------|
| **GitHub Actions** | 开箱即用的 CI | 🟡 P1 |
| **REST API** | 触发测试、获取报告 | 🔴 P0 |

**技术方案**:
```yaml
# GitHub Action 示例
- name: LingFlow 测试
  uses: guangda88/lingflow-action@v1
  with:
    test-type: 'all'
    coverage: true
    report-format: 'html'
```

### 8️⃣ 运维监控（Monitoring）

**最适合**: Web 可视化、告警集成

| 发布形态 | 价值 | 优先级 |
|----------|------|--------|
| **Grafana 仪表盘** | 监控数据展示 | 🟡 P1 |
| **Prometheus 导出** | 指标采集 | 🟢 P2 |
| **Webhook 告警** | 企业微信/钉钉 | 🟢 P2 |

---

## 🚀 实施路线图（总计 14 周）

### 🔴 Phase 1: 基础设施（4 周）

#### Week 1-2: REST API 服务
**目标**: 建立通用的 HTTP API 层

**技术栈**:
- 后端: FastAPI
- 认证: API Key + JWT
- 异步任务: Celery + Redis
- 文档: Swagger/OpenAPI

**实现内容**:
```python
# 项目结构
lingflow-api/
├── app/
│   ├── main.py              # FastAPI 应用
│   ├── api/
│   │   ├── v1/
│   │   │   ├── skills.py    # 技能 API
│   │   │   ├── workflows.py # 工作流 API
│   │   │   ├── review.py    # 审查 API
│   │   │   └── intelligence.py # 情报 API
│   │   └── dependencies.py  # 依赖注入
│   ├── core/
│   │   ├── config.py        # 配置
│   │   ├── security.py      # 认证
│   │   └── tasks.py         # 异步任务
│   └── models/
│       ├── requests.py      # 请求模型
│       └── responses.py     # 响应模型
├── tests/
├── Dockerfile
└── requirements.txt
```

**API 端点**:
```yaml
# 技能系统
GET    /api/v1/skills
GET    /api/v1/skills/{name}
POST   /api/v1/skills/{name}/execute
POST   /api/v1/skills/batch

# 工作流系统
GET    /api/v1/workflows
POST   /api/v1/workflows/{id}/run
GET    /api/v1/tasks/{task_id}
POST   /api/v1/workflows

# 代码审查
POST   /api/v1/review
GET    /api/v1/review/{id}

# 情报系统
GET    /api/v1/intelligence/github
GET    /api/v1/intelligence/npm

# 需求管理
GET    /api/v1/requirements
POST   /api/v1/requirements
GET    /api/v1/requirements/{id}
PUT    /api/v1/requirements/{id}
```

**部署**:
- Docker 容器化
- Railway / Render 一键部署
- 提供 docker-compose

#### Week 3: Docker 镜像
**目标**: 提供多用途 Docker 镜像

**实现内容**:
```dockerfile
# 多阶段构建
FROM python:3.11-slim as base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# CLI 镜像
FROM base as cli
COPY lingflow/ ./lingflow/
ENTRYPOINT ["lingflow"]

# API 镜像
FROM base as api
COPY lingflow-api/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]

# MCP 镜像
FROM base as mcp
COPY mcp_server/ ./mcp_server/
CMD ["lingflow-mcp", "run"]
```

**发布 Tags**:
- `lingflow/cli:latest` - CLI 工具
- `lingflow/api:latest` - REST API 服务
- `lingflow/mcp:latest` - MCP Server
- `lingflow:latest` - 完整版

#### Week 4: PyPI 独立 SDK
**目标**: 简化 Python 开发者集成

**实现内容**:
```python
# lingflow-sdk/package.py
"""
LingFlow Python SDK

轻量级客户端，简化 LingFlow 功能调用。
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

class LingFlowClient:
    """LingFlow 客户端

    支持两种模式：
    - 本地模式：直接调用 lingflow 库
    - 远程模式：调用 REST API
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        work_dir: str = "."
    ):
        """初始化客户端

        Args:
            api_key: API Key（远程模式必需）
            base_url: API 基础 URL（默认本地模式）
            work_dir: 工作目录（本地模式）
        """
        self.api_key = api_key
        self.base_url = base_url or "http://localhost:8000"
        self.work_dir = work_dir
        self._remote = api_key is not None

        # 导入子客户端
        from .skills import SkillsClient
        from .workflows import WorkflowsClient
        from .review import ReviewClient
        from .intelligence import IntelligenceClient

        self.skills = SkillsClient(self)
        self.workflows = WorkflowsClient(self)
        self.review = ReviewClient(self)
        self.intelligence = IntelligenceClient(self)

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送请求"""
        if self._remote:
            # 远程模式：HTTP 请求
            import requests
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        else:
            # 本地模式：直接调用
            return self._local_call(method, endpoint, **kwargs)

# 使用示例
from lingflow_sdk import LingFlowClient

# 本地模式
client = LingFlowClient(work_dir="./my-project")
result = client.skills.execute("code-generation", prompt="...")

# 远程模式
client = LingFlowClient(
    api_key="sk-xxx",
    base_url="https://api.lingflow.dev"
)
```

**发布**:
```bash
# 新包名：lingflow-sdk
# 与 lingflow-core 分离
pip install build
python -m build
twine upload dist/*
```

### 🟡 Phase 2: 用户体验增强（7 周）

#### Week 5-7: VSCode 插件
**目标**: 将 LingFlow 集成到编辑器

**技术栈**:
- TypeScript + VSCode Extension API
- Language Server Protocol (可选)
- 调用 REST API 或本地 CLI

**功能清单**:
```
1. 代码审查
   - 实时高亮问题
   - Code Action 快捷修复
   - 侧边栏显示审查报告

2. 工作流执行
   - 右键菜单运行工作流
   - 状态栏显示进度
   - 输出面板显示结果

3. 需求管理
   - 侧边栏需求列表
   - 快速创建需求
   - 关联分支

4. 技能执行
   - 命令面板调用技能
   - 选中代码执行技能
   - 结果预览面板
```

**实现示例**:
```typescript
// extension.ts
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    // 注册代码审查命令
    const reviewCommand = vscode.commands.registerCommand(
        'lingflow.reviewFile',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const filePath = editor.document.uri.fsPath;
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Running LingFlow code review...'
            }, async () => {
                // 调用 API 或 CLI
                const result = await reviewCode(filePath);
                // 显示结果
                showDiagnostics(result);
            });
        }
    );

    // 注册 Code Action
    vscode.languages.registerCodeActionsProvider('*', {
        provideCodeActions(document, range) {
            const actions = [];
            actions.push({
                title: 'Fix with LingFlow',
                command: 'lingflow.fixIssue'
            });
            return actions;
        }
    });

    context.subscriptions.push(reviewCommand);
}
```

**发布**:
- 发布到 VSCode Marketplace
- 开源代码到 GitHub

#### Week 8-11: Web 可视化平台
**目标**: 降低非技术用户使用门槛

**技术栈**:
- 前端: React + Ant Design + ECharts
- 后端: 复用 REST API
- 工作流编辑器: React Flow

**功能模块**:
```
1. 工作流设计器
   - 拖拽式节点编辑
   - YAML 导入/导出
   - 实时预览
   - 模板库

2. 需求管理看板
   - 类似 Trello 的看板视图
   - 需求状态拖拽
   - 追溯关系图

3. 监控仪表盘
   - 系统健康状态
   - 性能指标图表
   - 告警历史

4. 情报趋势图
   - GitHub/npm 趋势
   - 时间序列图表
   - 相关性分析
```

**工作流设计器实现**:
```typescript
// WorkflowEditor.tsx
import ReactFlow, { Node, Edge } from 'reactflow';

export function WorkflowEditor() {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);

    const nodeTypes = {
        skill: SkillNode,
        condition: ConditionNode,
        parallel: ParallelNode,
    };

    return (
        <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
        >
            <Controls />
            <MiniMap />
            <Background />
        </ReactFlow>
    );
}
```

**部署**:
- Vercel / Netlify 前端
- Railway 后端 API

### 🟢 Phase 2: 生态构建（3 周）

#### Week 12-14: 技能市场
**目标**: 构建社区贡献生态

**技术方案**:
```yaml
# 仓库结构
lingflow-marketplace/
├── skills/               # 技能仓库
│   ├── python/
│   │   ├── fastapi-validator/
│   │   └── django-migration/
│   └── javascript/
│       └── react-component-gen/
├── workflows/            # 工作流模板
│   ├── frontend-release.yaml
│   └── backend-deploy.yaml
└── index.json           # 索引文件
```

**CLI 集成**:
```bash
# 安装技能
lingflow marketplace install skill fastapi-validator

# 安装工作流
lingflow marketplace install workflow frontend-release

# 搜索
lingflow marketplace search --category testing

# 发布
lingflow marketplace publish ./my-skill
```

**Web 市场**:
- 浏览、搜索、评分
- 一键安装到项目
- 贡献统计

---

## 📊 成功指标

### 技术指标
- ✅ REST API 响应时间 < 200ms (P95)
- ✅ Docker 镜像大小 < 200MB
- ✅ VSCode 插件激活用户 > 1000
- ✅ SDK PyPI 下载量 > 5000/月

### 业务指标
- ✅ API 调用量 > 100,000/月
- ✅ 付费用户 > 100
- ✅ 社区贡献技能 > 50
- ✅ 企业部署 > 10

---

## 💰 商业模式

### 开源 + SaaS 混合

| 层级 | 功能 | 价格 |
|------|------|------|
| **社区版** | CLI、SDK、MCP（本地） | 免费 |
| **专业版** | 云端 API、优先支持 | $49/月 |
| **团队版** | Web UI、协作功能 | $199/月 |
| **企业版** | 私有部署、定制开发 | 联系销售 |

### 收入来源
1. **SaaS 订阅** - 云端 API 服务
2. **企业支持** - 技术支持和培训
3. **托管服务** - 私有部署和运维
4. **市场佣金** - 技能市场交易抽成

---

## 🎉 总结

### 核心策略
1. **基础设施先行** - REST API + Docker 是所有形态的基础
2. **用户体验优先** - IDE 插件和 Web UI 降低门槛
3. **生态开放** - 技能市场激发社区贡献
4. **渐进演进** - 从开源到 SaaS，从个人到企业

### 预期影响
- **开发者**: 10x 易用性提升
- **企业**: 完整的工程流解决方案
- **社区**: 开放的技能生态系统

### 下一步行动
1. **立即**: 启动 REST API 开发（Week 1-2）
2. **并行**: 准备 Docker 镜像（Week 3）
3. **准备**: SDK 重构（Week 4）

---

**"众智混元，万法灵通"** - 让 LingFlow 的工程流能力触达每一位开发者
