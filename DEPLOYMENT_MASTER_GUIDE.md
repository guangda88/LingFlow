# 🚀 LingFlow v3.8.0 部署指导 - 3个核心任务

**目标**: 完成 LingFlow 生态的完整部署
**预计时间**: 30-45 分钟
**难度**: 中等（需要一些平台账号）

---

## 📋 任务概览

```
✅ 准备工作: 已完成
⏳ 任务 1: 推送 Docker 镜像 (5-10 min) - 进行中
⏳ 任务 2: 部署 REST API 到 Railway (10-15 min)
⏳ 任务 3: 发布 GitHub Action (5-10 min)
```

---

## ⚙️ 准备工作检查

### 必需的账号

| 平台 | 账号 | 是否需要 | 状态 |
|------|------|----------|------|
| **Docker Hub** | guangda88 | ✅ 需要 | 待登录 |
| **Railway** | (任意) | ✅ 需要 | 待注册 |
| **GitHub** | guangda88 | ✅ 已有 | ✅ OK |

### 本地文件检查

```bash
✅ Docker 镜像: lingflow-api:test (333MB)
✅ API 代码: lingflow-api/
✅ Action 代码: actions/quality-gate/
✅ 配置文件: railway.json, nixpacks.toml
```

---

## 🐳 任务 1: 推送 Docker 镜像到 Docker Hub

**时间**: 5-10 分钟
**难度**: ⭐⭐ (简单)
**状态**: 🔄 进行中

### Step 1: 登录 Docker Hub (你需要执行)

```bash
# 在终端执行
docker login

# 输入:
# Username: guangda88
# Password: [你的 Docker Hub 密码或访问令牌]
```

**💡 提示**:
- 如果没有访问令牌，建议在 Docker Hub 网站创建一个
- 访问: https://hub.docker.com/settings/security

### Step 2: 标记镜像 (我来执行)

```bash
# 标记 latest 版本
docker tag lingflow-api:test guangda88/lingflow-api:latest

# 标记版本号
docker tag lingflow-api:test guangda88/lingflow-api:v3.8.0

# 验证标记
docker images | grep lingflow-api
```

**预期输出**:
```
guangda88/lingflow-api   latest              c55063cd9b9d        333MB
guangda88/lingflow-api   v3.8.0              c55063cd9b9d        333MB
lingflow-api             test                c55063cd9b9d        333MB
```

### Step 3: 推送镜像 (你需要执行)

```bash
# 推送 latest (通常更快，因为可能已有层缓存)
docker push guangda88/lingflow-api:latest

# 推送版本标签
docker push guangda88/lingflow-api:v3.8.0
```

**预期输出**:
```
The push refers to repository [docker.io/guangda88/lingflow-api]
...
v3.8.0: digest: sha256:... size: 1234
```

**⏱️ 预计时间**: 首次推送 3-5 分钟 (333MB)

### Step 4: 验证推送

```bash
# 方法1: 检查 Docker Hub
# 访问: https://hub.docker.com/r/guangda88/lingflow-api/tags

# 方法2: 命令行验证
docker pull guangda88/lingflow-api:latest

# 方法3: 测试运行
docker run --rm -p 8000:8000 \
  -e LINGFLOW_API_KEYS=test-key-12345 \
  guangda88/lingflow-api:latest

# 在另一个终端测试
curl http://localhost:8000/health
# 预期: {"status":"healthy","version":"3.8.0"}
```

### ✅ 完成标志

- [ ] Docker Hub 显示两个标签 (latest, v3.8.0)
- [ ] 可以 `docker pull` 成功
- [ ] 本地测试运行正常
- [ ] `/health` 端点返回正常

**🎉 任务 1 完成！**

---

## 🚂 任务 2: 部署 REST API 到 Railway

**时间**: 10-15 分钟
**难度**: ⭐⭐⭐ (中等)
**状态**: ⏳ 待开始

### Step 1: 注册 Railway (如果你还没有)

1. 访问: https://railway.app/
2. 点击 "Start Deploying"
3. 使用 GitHub 账号登录（推荐）
4. Railway 会获得你仓库的只读访问权限

### Step 2: 安装 Railway CLI (可选，推荐)

```bash
# 安装 CLI
npm install -g @railway/cli

# 或使用 Homebrew (macOS)
brew install railway

# 登录
railway login
# 会自动打开浏览器进行授权
```

**💡 提示**: CLI 更方便，但也可以使用 Web UI

### Step 3: 创建项目并部署

**方法 A: 使用 CLI (推荐)**

```bash
# 确保在 lingflow-api 目录
cd /home/ai/LingFlow/lingflow-api

# 初始化项目
railway init

# 选择或创建项目
# ? Select project: Create New Project
# ? Enter project name: lingflow-api

# 部署
railway up

# Railway 会自动:
# 1. 检测到 railway.json 和 nixpacks.toml
# 2. 构建 Docker 镜像
# 3. 部署到云端
```

**方法 B: 使用 Web UI**

1. 访问: https://railway.app/new
2. 点击 "Deploy from GitHub repo"
3. 选择 `guangda88/LingFlow` 仓库
4. 设置 Root Directory 为 `lingflow-api`
5. 点击 "Deploy Now"

### Step 4: 配置环境变量

**在 Railway Dashboard 设置**:

1. 访问你的项目: https://railway.app/project/xxx
2. 点击 "Variables" 标签
3. 添加以下变量:

```bash
LINGFLOW_API_KEYS=dev-key-12345,prod-key-67890
GITHUB_TOKEN=             # 可选，用于 GitHub 功能
LOG_LEVEL=INFO
CORS_ORIGINS=https://lingflow-api-production.up.railway.app,https://lingflow.com
```

4. 点击 "Deploy" 触发重新部署

### Step 5: 获取公开 URL

```bash
# 使用 CLI
railway domain

# 或在 Dashboard 的 "Networking" 标签查看
```

**预期 URL 格式**:
```
https://lingflow-api-production.up.railway.app
或
https://xxx.up.railway.app
```

### Step 6: 验证部署

```bash
# 健康检查
curl https://你的URL.up.railway.app/health

# 预期输出:
# {"status":"healthy","version":"3.8.0"}

# API 文档
# 访问: https://你的URL.up.railway.app/docs

# 测试 API
curl -X POST https://你的URL.up.railway.app/api/v1/code/review \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"code":"def hello():\n    print(\"world\")"}'
```

### Step 7: 设置自定义域名 (可选)

1. 在 Railway Dashboard 的 "Networking" 标签
2. 点击 "Add Custom Domain"
3. 输入域名: `api.lingflow.com` (示例)
4. 按照提示配置 DNS 记录

### ✅ 完成标志

- [ ] Railway 部署成功
- [ ] 公开 URL 可访问
- [ ] `/health` 端点返回正常
- [ ] `/docs` 文档页面可访问
- [ ] API 端点测试通过
- [ ] 环境变量已配置

**🎉 任务 2 完成！**

---

## 🎁 任务 3: 发布 GitHub Action 到 Marketplace

**时间**: 5-10 分钟
**难度**: ⭐⭐⭐⭐ (较复杂)
**状态**: ⏳ 待开始

### 准备工作检查

```bash
✅ Action 代码: actions/quality-gate/
✅ action.yml: 已配置
✅ Dockerfile: 已准备
✅ entrypoint.sh: 脚本已就绪
```

### Step 1: 创建 Release (我来执行)

```bash
# 确保在主仓库
cd /home/ai/LingFlow

# 创建 Action 版本标签
git tag -a actions/quality-gate/v1.0.0 -m "LingFlow Quality Gate v1.0.0

- AI-powered code review
- Quality gate automation
- CI/CD integration
"

# 推送标签
git push origin actions/quality-gate/v1.0.0
```

### Step 2: 在 GitHub 创建 Release (你需要执行)

**方法 A: Web 界面**

1. 访问: https://github.com/guangda88/LingFlow/releases
2. 点击 "Draft a new release"
3. 选择标签: `actions/quality-gate/v1.0.0`
4. Release title: `LingFlow Quality Gate v1.0.0`
5. Description:

```markdown
## 🎉 LingFlow Quality Gate v1.0.0

AI-powered code review and quality gate for GitHub Actions.

### Features
- 🤖 AI代码审查
- 🔍 代码质量分析
- 🚦 CI/CD 质量门禁
- 📊 多种输出格式

### Usage

```yaml
steps:
  - uses: guangda88/LingFlow/actions/quality-gate@v1.0.0
    with:
      github_token: ${{ secrets.GITHUB_TOKEN }}
      path: ./src
```

### Documentation
- README: [actions/quality-gate/README.md](https://github.com/guangda88/LingFlow/tree/master/actions/quality-gate)
- Examples: [actions/quality-gate/examples/](https://github.com/guangda88/LingFlow/tree/master/actions/quality-gate/examples)
```

6. 勾选 "Set as the latest release"
7. 点击 "Publish release"

**方法 B: GitHub CLI (如果已安装)**

```bash
gh release create actions/quality-gate/v1.0.0 \
  --title "LingFlow Quality Gate v1.0.0" \
  --notes "AI-powered code review and quality gate for GitHub Actions."
```

### Step 3: 验证 Action 可用性

```bash
# 测试 Action 是否可以在其他仓库使用

# 创建测试仓库
mkdir /tmp/test-lingflow-action
cd /tmp/test-lingflow-action
git init

# 创建 .github/workflows/test.yml
mkdir -p .github/workflows
cat > .github/workflows/test.yml <<EOF
name: Test LingFlow Action
on: push

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run LingFlow Quality Gate
        uses: guangda88/LingFlow/actions/quality-gate@v1.0.0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          path: .
          command: review
EOF

# 提交并推送
git add .
git commit -m "test: 测试 LingFlow Action"
gh repo create test-lingflow-action --public --source=.
git push -u origin main
```

### Step 4: (可选) 发布到 GitHub Marketplace

**注意**: Marketplace 发布有更严格的要求，通常用于公开分享 Action。

**如果要发布到 Marketplace**:

1. 确保符合 Marketplace 要求:
   - ✅ Action 有清晰的描述
   - ✅ 有 README 文档
   - ✅ 有使用示例
   - ✅ 有合适的图标和品牌

2. 访问: https://github.com/marketplace/actions
3. 点击 "Create a new Action"
4. 填写表单:
   - **Name**: LingFlow Quality Gate
   - **Description**: AI-powered code review and quality gate
   - **Category**: Code Review
   - **Organization**: guangda88
   - **Repository**: LingFlow
   - **Action**: actions/quality-gate

5. 提交审核

**⚠️ 注意**: Marketplace 审核可能需要几天时间

### Step 5: 文档和使用示例

Action 已经有完整的文档和示例:

```bash
# 文档
cat actions/quality-gate/README.md

# 示例
ls actions/quality-gate/examples/
```

### ✅ 完成标志

- [ ] Release 已创建
- [ ] 标签已推送到 GitHub
- [ ] Action 可以在 `.yml` 文件中引用
- [ ] 测试仓库运行成功
- [ ] 文档完整且准确
- [ ] (可选) Marketplace 提交成功

**🎉 任务 3 完成！**

---

## 📊 总体验证清单

### 任务 1: Docker Hub
```bash
# 验证命令
docker pull guangda88/lingflow-api:latest
docker inspect guangda88/lingflow-api:latest | grep "3.8.0"
```

### 任务 2: Railway
```bash
# 验证命令
curl https://你的URL.up.railway.app/health
curl https://你的URL.up.railway.app/docs
```

### 任务 3: GitHub Action
```bash
# 验证方法
# 访问: https://github.com/guangda88/LingFlow/actions
# 查看是否显示 Quality Gate Action
```

---

## 🎯 完成后做什么？

### 1. 更新 README

在主 README 添加部署信息:

```markdown
## 🚀 在线演示

- **API Demo**: https://lingflow-api.up.railway.app
- **API Docs**: https://lingflow-api.up.railway.app/docs

## 📦 安装

### Docker
```bash
docker pull guangda88/lingflow-api:latest
docker run -p 8000:8000 guangda88/lingflow-api:latest
```

### GitHub Actions
```yaml
- uses: guangda88/LingFlow/actions/quality-gate@v1.0.0
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    path: ./src
```
```

### 2. 创建 Demo 仓库

展示 LingFlow 的实际使用:

```bash
# 创建示例仓库
mkdir /tmp/lingflow-demo
cd /tmp/lingflow-demo

# 添加 LingFlow GitHub Action
# 添加 Railway 部署配置
# 添加使用示例
```

### 3. 发布公告

- GitHub Discussions
- Reddit (r/Python, r/devtools)
- Twitter/X
- LinkedIn

---

## 🆘 常见问题

### Docker 推送失败

**问题**: `denied: requested access to the resource is denied`

**解决**:
```bash
# 重新登录
docker logout
docker login
# 确保使用正确的用户名: guangda88
```

### Railway 部署失败

**问题**: Build failed

**解决**:
1. 检查构建日志
2. 确保 `requirements.txt` 完整
3. 验证 `start.sh` 可执行权限

### GitHub Action 不可用

**问题**: `Resource not accessible`

**解决**:
1. 确保仓库是公开的
2. 检查 `action.yml` 语法
3. 验证 Release 已成功创建

---

## 📞 获取帮助

- **Docker Hub**: https://docs.docker.com/docker-hub/
- **Railway**: https://docs.railway.app/
- **GitHub Actions**: https://docs.github.com/en/actions

---

**准备开始？从任务 1 开始！**

```bash
# 第一步: 登录 Docker Hub
docker login
```

---

*部署指导 v1.0 - LingFlow v3.8.0*
