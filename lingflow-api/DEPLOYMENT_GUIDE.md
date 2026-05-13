# lingflow REST API - 生产部署指南

**任务**: 公开发布和部署服务
**状态**: 执行中

---

## 🐳 Docker 镜像发布

### Step 1: 构建镜像

```bash
cd /home/ai/lingflow/lingflow-api

# 构建镜像
docker build -t lingflow/api:latest -t lingflow/api:v1.0.0 -f Dockerfile .

# 测试镜像
docker run --rm -p 8000:8000 \
  -e LINGFLOW_API_KEYS=test-key-123 \
  lingflow/api:latest
```

### Step 2: 推送到 Docker Hub

```bash
# 登录 Docker Hub
docker login

# 打标签
docker tag lingflow/api:latest guangda88/lingflow-api:latest
docker tag lingflow/api:v1.0.0 guangda88/lingflow-api:v1.0.0

# 推送
docker push guangda88/lingflow-api:latest
docker push guangda88/lingflow-api:v1.0.0
```

### Step 3: 推送 CLI 镜像

```bash
# CLI 镜像
docker build -t lingflow/cli:latest -f Dockerfile.cli .
docker tag lingflow/cli:latest guangda88/lingflow-cli:latest
docker push guangda88/lingflow-cli:latest
```

---

## 🚀 Railway 部署

### Step 1: 准备部署文件

**railway.json**:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main_simple:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```

**nixpacks.toml**:
```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.build]
cmds = [
    "pip install --no-cache-dir -r requirements.txt"
]

[start]
cmd = "uvicorn main_simple:app --host 0.0.0.0 --port $PORT"
```

### Step 2: 部署到 Railway

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 创建项目
railway init

# 部署
railway up
```

### Step 3: 配置环境变量

在 Railway 控制台设置：
- `LINGFLOW_API_KEYS`: `dev-key-12345,prod-key-67890`
- `GITHUB_TOKEN`: (可选)
- `LOG_LEVEL`: `INFO`

### Step 4: 获取公开 URL

部署后，Railway 会提供一个公开 URL：
```
https://lingflow-api-production.up.railway.app
```

---

## 🔧 Render 部署（备选）

### render.yaml

```yaml
services:
  - type: web
    name: lingflow-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main_simple:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PORT
        value: 8000
      - key: LINGFLOW_API_KEYS
        value: dev-key-12345
```

### 部署步骤

1. 连接 GitHub 仓库
2. 选择 `lingflow-api` 目录
3. 配置环境变量
4. 部署

---

## 📦 GitHub Action 发布

### Step 1: 创建 Release

```bash
cd /home/ai/lingflow

# 创建 Git tag
git tag -a actions/quality-gate/v1.0.0 -m "lingflow Quality Gate v1.0.0

# 推送标签
git push origin actions/quality-gate/v1.0.0
```

### Step 2: 发布到 Marketplace

1. 访问 https://github.com/marketplace/actions
2. 点击 "Create a new Action"
3. 填写信息：
   - Name: lingflow Quality Gate
   - Description: AI-powered code review and quality gate
   - Organization: guangda88 (或 lingflow)
   - Repository: lingflow
   - Action: actions/quality-gate
4. 发布

---

## 🌐 技能索引仓库发布

### Step 1: 推送索引仓库

```bash
cd /home/ai/lingflow-skills-index

# 初始化 Git（如果还没有）
git init
git add .
git commit -m "feat: 初始化技能索引仓库

- 中央索引文件
- skill.yaml Schema
- 自动扫描脚本
- GitHub Action 自动更新
"

# 添加远程
git remote add origin git@github.com:lingflow/skills-index.git

# 推送
git push -u origin main
```

### Step 2: 创建第一个示例技能

```bash
# 创建 skills 仓库
mkdir -p /tmp/lingflow-skills
cd /tmp/lingflow-skills

# 初始化
git init

# 创建示例技能
mkdir -p python-fastapi-validator
# (按 PUBLISH_GUIDE.md 中的步骤)

# 提交并推送
gh repo create lingflow/skills --public
git remote add origin git@github.com:lingflow/skills.git
git push -u origin main
```

---

## ✅ 验收清单

### Docker 镜像
- [ ] lingflow/api:latest 已推送
- [ ] lingflow/cli:latest 已推送
- [ ] 镜像可从 Docker Hub 拉取

### Railway 部署
- [ ] API 服务已部署
- [ ] 公开 URL 可访问
- [ ] /health 端点正常
- [ ] /docs 端点可访问

### GitHub Action
- [ ] Release 已创建
- [ ] Marketplace 已发布
- [ ] 可在第三方仓库使用

### 技能索引
- [ ] skills-index 仓库已公开
- [ ] index.json 可访问
- [ ] GitHub Action 自动更新

---

## 📊 成功指标

### 技术指标
- ✅ Docker 镜像大小 < 200MB
- ✅ API 响应时间 < 200ms (P95)
- ✅ 部署成功率 100%

### 可访问性
- ✅ Railway Demo 可访问
- ✅ Docker Hub 镜像可拉取
- ✅ GitHub Action 可使用
- ✅ 技能索引可浏览

---

## 🎯 下一步

部署完成后：
1. 更新主 README 添加部署链接
2. 创建 Demo 仓库展示 Action 使用
3. 发布公告到社区

---

**状态**: 执行中
**预计完成**: 今日内
