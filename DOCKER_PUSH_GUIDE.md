# Docker 镜像推送指南

**任务**: 推送 Docker 镜像到 Docker Hub
**状态**: 镜像测试通过，待推送

---

## ✅ 测试结果

### API 镜像
- ✅ 构建成功 (333MB)
- ✅ 根路径响应正常
- ✅ 健康检查通过
- ⚠️ 技能列表端点需要完整环境（Phase 2 修复）

---

## 🐳 推送步骤

### 1. 登录 Docker Hub

```bash
docker login
# 输入用户名: guangda88
# 输入密码或访问令牌
```

### 2. 标记镜像

```bash
cd /home/ai/LingFlow

# API 镜像
docker tag lingflow-api:test guangda88/lingflow-api:latest
docker tag lingflow-api:test guangda88/lingflow-api:v1.0.0
```

### 3. 推送镜像

```bash
# 推送 API 镜像
docker push guangda88/lingflow-api:latest
docker push guangda88/lingflow-api:v1.0.0
```

---

## 📋 后续镜像（Phase 2）

### CLI 镜像
```bash
docker build --target cli -t guangda88/lingflow-cli:latest -f lingflow-api/Dockerfile .
docker push guangda88/lingflow-cli:latest
```

### GitHub Action 镜像
```bash
cd actions/quality-gate
docker build -t guangda88/lingflow-action:quality-gate:v1.0.0 .
docker push guangda88/lingflow-action:quality-gate:v1.0.0
```

---

## 🔗 相关链接

- Docker Hub: https://hub.docker.com/r/guangda88/lingflow-api
- 项目仓库: https://github.com/guangda88/LingFlow

---

**状态**: 待 Docker Hub 登录后推送
