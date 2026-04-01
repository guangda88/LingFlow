# LingFlow 两周冲刺计划（MVP）

**基于**: 《LingFlow 生态架构演进白皮书》
**时间**: 2026-04-02 ~ 2026-04-16
**目标**: 从"本地工具"升级为"开发者生态平台"

---

## 🎯 核心原则（来自白皮书）

1. **接入层先行** - REST API + Docker 是一切的基础
2. **不要过早投入重平台** - 技能市场先用 GitHub + JSON 索引
3. **坚持数据出口而非内置引擎** - 告警用 Prometheus，不自研
4. **GitHub Actions 是首要突破口** - CI/CD 是高频场景

---

## 📋 两周任务清单

### Week 1: REST API MVP + GitHub Action

#### Day 1-2: REST API 核心端点
**目标**: 可运行的 API 服务

**技术栈**:
- FastAPI（已选定）
- Docker（多阶段构建）
- 内存任务队列（暂不用 Redis）

**必做端点**（按白皮书优先级）:
```python
# 技能系统（原子能力，最优先）
GET    /api/v1/skills              # 列出技能
POST   /api/v1/skills/{name}/execute  # 执行技能

# 工作流（同步模式，暂不异步）
GET    /api/v1/workflows           # 列出工作流
POST   /api/v1/workflows/{id}/run  # 执行工作流（同步）

# 代码审查
POST   /api/v1/review              # 代码审查

# 情报系统（带缓存）
GET    /api/v1/intelligence/github
GET    /api/v1/intelligence/npm
```

**验收标准**:
- ✅ Swagger UI 可访问
- ✅ 所有端点可手动测试
- ✅ Docker 镜像可构建

#### Day 3-4: GitHub Action `quality-gate`
**目标**: 可在 GitHub Marketplace 使用

**实现方案**（白皮书建议）:
```yaml
# action.yml
name: 'LingFlow Quality Gate'
description: 'AI-powered code review and quality gate'
branding:
  icon: 'check-circle'
  color: 'blue'

inputs:
  command:
    description: 'Command to run'
    required: true
    default: 'review'
  path:
    description: 'Path to review'
    required: true
    default: './src'
  github_token:
    description: 'GitHub Token'
    required: true

runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - ${{ inputs.command }}
    - ${{ inputs.path }}
```

**Dockerfile**（复用 CLI 镜像）:
```dockerfile
FROM lingflow/cli:latest

# 安装 GitHub CLI
RUN apt-get update && apt-get install -y gh

# 入口脚本
COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

**entrypoint.sh**（PR 评论功能）:
```bash
#!/bin/bash
COMMAND=$1
PATH=$2

# 执行 LingFlow
RESULT=$(lingflow $COMMAND $PATH)

# 发布评论到 PR
if [ -n "$GITHUB_EVENT_NAME" ] && [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then
  gh pr comment "$GITHUB_PR_NUMBER" --body "$RESULT"
fi
```

**验收标准**:
- ✅ Action 可在私有仓库测试
- ✅ PR 评论功能正常
- ✅ 发布到 GitHub Marketplace

#### Day 5: 技能市场索引 MVP
**目标**: GitHub + JSON 索引（白皮书第一阶段）

**仓库结构**:
```
lingflow/skills-index/          # 索引仓库
├── index.json                  # 全局索引
├── scripts/
│   └── scan.py                # 扫描脚本
└── .github/workflows/
    └── update-index.yml       # 自动更新

lingflow/skills/                # 技能组织
├── python-fastapi-validator/  # 技能仓库 1
│   ├── skill.yaml            # 元数据
│   ├── src/                  # 实现
│   └── tests/
└── javascript-react-gen/     # 技能仓库 2
    ├── skill.yaml
    └── src/
```

**skill.yaml 规范**:
```yaml
apiVersion: lingflow.dev/v1
kind: Skill
metadata:
  name: fastapi-validator
  version: 1.0.0
  author: contributor
  description: Validate FastAPI routes against best practices
spec:
  category: testing
  language: python
  entrypoint: src/validator.py
  parameters:
    - name: route_path
      type: string
      required: true
  dependencies:
    - fastapi>=0.100.0
```

**index.json 格式**:
```json
{
  "version": "1.0.0",
  "last_updated": "2026-04-02T10:00:00Z",
  "skills": [
    {
      "id": "fastapi-validator",
      "name": "FastAPI Validator",
      "version": "1.0.0",
      "author": "contributor",
      "description": "Validate FastAPI routes",
      "repository": "https://github.com/lingflow/skills/tree/main/python-fastapi-validator",
      "category": "testing",
      "language": "python",
      "downloads": 0,
      "rating": 0.0
    }
  ]
}
```

**CLI 命令**:
```bash
# 搜索技能
lingflow skill search fastapi

# 安装技能
lingflow skill install fastapi-validator
# 实际执行：git clone https://github.com/lingflow/skills/python-fastapi-validator ~/.lingflow/skills/

# 列出已安装
lingflow skill list
```

**验收标准**:
- ✅ 创建 `lingflow/skills-index` 仓库
- ✅ 定义 `skill.yaml` schema
- ✅ 实现 `lingflow skill search/install`
- ✅ GitHub Action 自动更新索引

---

### Week 2: 完善与发布

#### Day 6-7: REST API 完善
**任务**:
- [ ] 添加错误处理和日志
- [ ] 实现 `/metrics` 端点（Prometheus 格式）
- [ ] 编写 5 个示例集成代码
- [ ] 完整的 OpenAPI 文档

#### Day 8-9: 公开发布
**任务**:
- [ ] REST API 部署到 Railway（公开 Demo）
- [ ] Docker 镜像推送到 Docker Hub
- [ ] GitHub Action 发布到 Marketplace
- [ ] 技能索引仓库公开

#### Day 10: 文档和宣发
**任务**:
- [ ] 更新 README（添加 4 种使用方式）
- [ ] 发布技术文章（白皮书建议）
- [ ] 准备 demo 视频

---

## 📁 仓库结构调整

基于白皮书的分层架构：

```
lingflow/                         # 主仓库（核心库）
├── lingflow/
│   ├── core/                    # ✅ 编排与交互层
│   ├── skills/                  # ✅ 核心能力层
│   └── infrastructure/          # 🆕 基础设施层
│       ├── storage.py           # SQLite 抽象
│       ├── queue.py             # 内存队列
│       └── metrics.py           # Prometheus 导出
├── cli/                         # CLI 工具
├── mcp_server/                  # MCP Server ✅
├── api/                         # 🆕 REST API
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/
│   │   └── core/
│   ├── Dockerfile
│   └── docker-compose.yml
└── actions/                     # 🆕 GitHub Actions
    └── quality-gate/

lingflow/skills-index/           # 🆕 技能市场索引
lingflow/skills/                 # 🆕 技能组织（包含多个技能仓库）
```

---

## 🚀 技术决策记录（ADR）

### ADR-001: 技能市场采用 GitHub 索引
**状态**: 已接受
**决策**: 使用 GitHub 仓库 + JSON 索引，不自建平台
**理由**:
- 零运维成本
- 利用 GitHub 社交优势
- 快速验证生态活力
**后果**:
- 无法实时统计（可接受）
- 依赖 GitHub（可用 GitLab mirror）

### ADR-002: Web 设计器选择 React Flow
**状态**: 已接受
**决策**: 使用 React Flow，不用 Node-RED
**理由**:
- Node-RED 是完整运行时，与 YAML 不匹配
- React Flow 可完美映射 DAG
- 社区成熟（Prefect、Airflow 都在用）
**后果**:
- 需要自己实现编辑逻辑
- 可控性更好

### ADR-003: 告警系统使用 Prometheus
**状态**: 已接受
**决策**: 只暴露 `/metrics` 端点，不自建告警引擎
**理由**:
- 不做重复轮子
- Prometheus/Alertmanager 已成熟
- 用户可自行配置
**后果**:
- 小团队学习成本（可提供 Grafana 模板）

### ADR-004: 任务队列分两阶段
**状态**: 已接受
**决策**: Phase 1 用内存队列，Phase 3 再用 Celery/Redis
**理由**:
- 降低初期复杂度
- 保持向后兼容
**后果**:
- 进程重启丢失任务（可接受，MVP 阶段）

---

## 📊 成功指标

### 技术指标
- ✅ REST API 响应时间 < 200ms (P95)
- ✅ Docker 镜像大小 < 200MB
- ✅ GitHub Action 被 10+ 仓库使用

### 社区指标
- ✅ 技能市场有 5+ 贡献技能
- ✅ GitHub Stars 增长 50%
- ✅ PR 被第三方仓库引用

---

## 🎓 学习与调整

根据白皮书反馈，我调整了以下内容：

### 之前的错误
1. ❌ 14 周计划太激进 → ✅ 调整为 2 周 MVP + 迭代
2. ❌ 技能市场想自建平台 → ✅ 先用 GitHub 索引
3. ❌ 告警系统想自研 → ✅ 用 Prometheus 导出
4. ❌ Web 设计器考虑 Node-RED → ✅ 用 React Flow
5. ❌ 忽略 GitHub Actions → ✅ 作为首要突破口

### 保留的正确部分
1. ✅ REST API 是桥梁
2. ✅ Docker 多用途镜像
3. ✅ 分层架构设计
4. ✅ 优先级划分

---

## 🤝 下一步

**本周立即行动**（按白皮书建议）：

1. **创建技能索引仓库**
   ```bash
   mkdir -p ../lingflow-skills-index
   cd ../lingflow-skills-index
   git init
   ```

2. **完善 GitHub Action**
   ```bash
   cd actions/quality-gate
   # 完善 action.yml 和 Dockerfile
   ```

3. **REST API 聚焦核心端点**
   ```bash
   cd api/app
   # 只实现 8 个核心端点
   ```

**您希望我优先完成哪个？**
- A. 技能索引仓库结构和 CLI 命令
- B. GitHub Action 完整实现
- C. REST API 核心端点
- D. 其他？

---

**基于白皮书的务实方案**

*"众智混元，万法灵通"*
