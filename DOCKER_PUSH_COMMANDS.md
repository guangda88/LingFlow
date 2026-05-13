# Docker 镜像推送指南 - v3.8.0

**状态**: 代码已构建，待推送

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
cd /home/ai/lingflow

# API 镜像
docker tag lingflow-api:test guangda88/lingflow-api:latest
docker tag lingflow-api:test guangda88/lingflow-api:v3.8.0

# 验证标记
docker images | grep lingflow-api
```

### 3. 推送镜像
```bash
# 推送 latest
docker push guangda88/lingflow-api:latest

# 推送版本标签
docker push guangda88/lingflow-api:v3.8.0
```

### 4. 验证
```bash
# 拉取测试
docker pull guangda88/lingflow-api:latest

# 运行测试
docker run --rm -p 8000:8000 \
  -e LINGFLOW_API_KEYS=test-key-12345 \
  guangda88/lingflow-api:latest

# 健康检查
curl http://localhost:8000/health
```

---

## 📊 镜像信息

| 镜像名 | 大小 | 用途 |
|--------|------|------|
| `guangda88/lingflow-api:latest` | ~333MB | REST API 服务 |
| `guangda88/lingflow-api:v3.8.0` | ~333MB | REST API 服务 |

---

## 🔗 相关链接

- **Docker Hub**: https://hub.docker.com/r/guangda88/lingflow-api
- **PyPI**: https://pypi.org/project/lingflow-core/
- **GitHub**: https://github.com/guangda88/lingflow

---

**预计时间**: 5-10 分钟（取决于网速）
