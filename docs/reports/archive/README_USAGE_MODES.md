---

## 🚀 四种使用方式

LingFlow 现在支持 **4 种使用方式**，从本地命令行到云端 API，满足不同场景需求：

### 1️⃣ 命令行工具（CLI）

最简单直接的方式，适合日常开发和脚本自动化。

```bash
# 安装
pip install lingflow-core

# 列出技能
lingflow list-skills

# 执行技能
lingflow run code-generation --prompt "创建一个用户认证系统"

# 代码审查
lingflow review ./src

# 运行工作流
lingflow workflow run feature-development
```

**文档**: [CLI 使用指南](docs/cli.md)

---

### 2️⃣ Python SDK

适合 Python 开发者，深度集成到自己的应用中。

```python
from lingflow_sdk import LingFlowClient

# 初始化客户端
client = LingFlowClient(work_dir="./my-project")

# 执行技能
result = client.skills.execute(
    "code-generation",
    params={"prompt": "创建 REST API", "language": "python"}
)

# 运行工作流
workflow_result = client.workflows.run(
    "feature-development",
    params={"feature": "user-auth"}
)

# 代码审查
review = client.review.code("./src")
print(f"总分: {review.overall_score}")
```

**文档**: [SDK 参考](docs/sdk.md)

---

### 3️⃣ REST API

跨语言的云端 API，适合任何技术栈。

```bash
# 启动本地服务器
lingflow-api start

# 或使用 Docker
docker run -p 8000:8000 guangda88/lingflow-api:latest

# 访问 API 文档
open http://localhost:8000/docs
```

**示例：cURL**
```bash
# 列出技能
curl http://localhost:8000/api/v1/skills \
  -H "X-API-Key: dev-key-12345"

# 执行技能
curl -X POST http://localhost:8000/api/v1/skills/code-generation/execute \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"params": {"prompt": "创建 API"}, "timeout": 60}'
```

**示例：JavaScript**
```javascript
const response = await fetch('http://localhost:8000/api/v1/skills', {
  headers: { 'X-API-Key': 'dev-key-12345' }
});
const skills = await response.json();
```

**公开 Demo**: https://lingflow-api.up.railway.app

**文档**: [API 文档](https://lingflow-api.up.railway.app/docs)

---

### 4️⃣ GitHub Actions

CI/CD 集成，质量门禁自动化。

```yaml
name: LingFlow Quality Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run LingFlow Review
        uses: guangda88/LingFlow/actions/quality-gate@v1
        with:
          command: review
          path: ./src
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

**功能**：
- ✅ 自动代码审查
- ✅ PR 评论集成
- ✅ 质量门禁
- ✅ 多种命令支持

**文档**: [Action README](actions/quality-gate/README.md)

---

## 📊 使用方式对比

| 方式 | 适用场景 | 学习成本 | 集成难度 |
|------|----------|----------|----------|
| **CLI** | 日常开发、脚本 | ⭐ 低 | ⭐ 低 |
| **Python SDK** | Python 应用 | ⭐⭐ 中 | ⭐⭐ 中 |
| **REST API** | 跨语言、微服务 | ⭐⭐ 中 | ⭐ 低 |
| **GitHub Actions** | CI/CD | ⭐ 低 | ⭐ 低 |

---

## 🔗 快速链接

### 核心资源
- 📦 [PyPI 包](https://pypi.org/project/lingflow-core/)
- 🐳 [Docker Hub](https://hub.docker.com/r/guangda88)
- 📖 [完整文档](https://lingflow.dev)
- 💬 [GitHub Issues](https://github.com/guangda88/LingFlow/issues)

### 在线服务
- 🌐 [API Demo](https://lingflow-api.up.railway.app)
- 🛠️ [技能市场](https://github.com/lingflow/skills-index)
- 🔧 [GitHub Actions](https://github.com/marketplace/actions/lingflow-actions)

---

## 🎓 选择你的方式

### 我是开发者，想快速开始
→ **使用 CLI 工具**

```bash
pip install lingflow-core
lingflow --help
```

### 我想在 Python 代码中使用
→ **使用 Python SDK**

```python
pip install lingflow-sdk
```

### 我需要跨语言集成
→ **使用 REST API**

```bash
docker run -p 8000:8000 guangda88/lingflow-api:latest
```

### 我想集成到 CI/CD
→ **使用 GitHub Actions**

```yaml
- uses: guangda88/LingFlow/actions/quality-gate@v1
```

---

**"众智混元，万法灵通"** - 选择最适合你的方式！
