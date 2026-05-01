# LingFlow REST API - 快速启动包

**版本**: v1.0.0-alpha
**状态**: 开发中

---

## 🚀 快速开始

### 方式 1: 一键启动（推荐）

```bash
cd lingflow-api
chmod +x start.sh
./start.sh
```

启动完成后，访问：
- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 方式 2: Docker Compose

```bash
# 创建环境变量
cat > .env << EOF
LINGFLOW_API_KEYS=dev-key-12345
LOG_LEVEL=INFO
EOF

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f api
```

### 方式 3: 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📖 API 使用示例

### 1. 技能系统

**列出所有技能**:
```bash
curl -H "X-API-Key: dev-key-12345" \
  http://localhost:8000/api/v1/skills
```

**执行技能**:
```bash
curl -X POST \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"params": {"prompt": "Create a REST API"}}' \
  http://localhost:8000/api/v1/skills/code-generation/execute
```

### 2. 工作流系统

**列出工作流**:
```bash
curl -H "X-API-Key: dev-key-12345" \
  http://localhost:8000/api/v1/workflows
```

**执行工作流**:
```bash
curl -X POST \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"params": {"feature": "user-auth"}, "strategy": "hybrid"}' \
  http://localhost:8000/api/v1/workflows/feature-development/run
```

**查询任务状态**:
```bash
curl -H "X-API-Key: dev-key-12345" \
  http://localhost:8000/api/v1/tasks/{task_id}
```

### 3. 代码审查

**执行代码审查**:
```bash
curl -X POST \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"target_path": "./src", "dimensions": ["complexity", "security"]}' \
  http://localhost:8000/api/v1/review
```

### 4. 情报系统

**GitHub 趋势**:
```bash
curl -H "X-API-Key: dev-key-12345" \
  "http://localhost:8000/api/v1/intelligence/github?keywords=python,ai"
```

**npm 趋势**:
```bash
curl -H "X-API-Key: dev-key-12345" \
  "http://localhost:8000/api/v1/intelligence/npm?keywords=react"
```

---

## 🔐 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `LINGFLOW_API_KEYS` | API 密钥（逗号分隔） | dev-key-12345 |
| `LINGFLOW_WORK_DIR` | 工作目录 | /workspace |
| `LOG_LEVEL` | 日志级别 | INFO |
| `GITHUB_TOKEN` | GitHub Token（可选） | - |
| `NPM_TOKEN` | npm Token（可选） | - |

### Docker Compose 服务

| 服务 | 端口 | 说明 |
|------|------|------|
| api | 8000 | REST API 服务 |
| redis | 6379 | 任务队列和缓存 |
| worker | - | Celery 异步任务 |
| nginx | 80/443 | 反向代理（可选） |

---

## 🛠️ 开发指南

### 项目结构

```
lingflow-api/
├── app/
│   ├── main.py              # FastAPI 应用
│   ├── api/
│   │   └── v1/
│   │       ├── skills.py    # 技能 API
│   │       ├── workflows.py # 工作流 API
│   │       ├── review.py    # 审查 API
│   │       └── intelligence.py
│   ├── core/
│   │   ├── config.py        # 配置
│   │   ├── security.py      # 认证
│   │   └── tasks.py         # 异步任务
│   └── models/
│       ├── requests.py      # 请求模型
│       └── responses.py     # 响应模型
├── Dockerfile               # Docker 镜像
├── docker-compose.yml       # Docker Compose
├── requirements.txt         # Python 依赖
├── start.sh                 # 启动脚本
└── README.md                # 本文档
```

### 添加新端点

1. 在 `app/api/v1/` 创建新文件
2. 定义路由和请求/响应模型
3. 在 `app/main.py` 中注册路由

示例：
```python
# app/api/v1/custom.py
from fastapi import APIRouter, Depends
from app.models.requests import CustomRequest

router = APIRouter(prefix="/custom", tags=["Custom"])

@router.post("/")
async def custom_endpoint(
    request: CustomRequest,
    api_key: str = Depends(verify_api_key)
):
    # 实现逻辑
    return {"status": "ok"}
```

---

## 📊 监控和日志

### 查看日志

```bash
# API 日志
docker-compose logs -f api

# Worker 日志
docker-compose logs -f worker

# 所有服务
docker-compose logs -f
```

### 健康检查

```bash
curl http://localhost:8000/health
```

### 服务状态

```bash
docker-compose ps
```

---

## 🚢 生产部署

### Railway

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录并部署
railway login
railway up
```

### Render

1. 连接 GitHub 仓库
2. 选择 `Dockerfile` 路径: `lingflow-api/Dockerfile`
3. 设置环境变量
4. 部署

### AWS ECS

```bash
# 构建 and 推送到 ECR
docker build -t lingflow-api .
docker tag lingflow-api:latest {aws-account}.dkr.ecr.{region}.amazonaws.com/lingflow-api:latest
docker push {aws-account}.dkr.ecr.{region}.amazonaws.com/lingflow-api:latest
```

---

## 🧪 测试

### 单元测试

```bash
pytest tests/
```

### API 测试

使用提供的 Postman Collection 或 Swagger UI。

---

## 📚 相关文档

- [LingFlow 主文档](../README.md)
- [API 完整文档](http://localhost:8000/docs)
- [部署路线图](../docs/architecture/DEPLOYMENT_ROADMAP.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License - 与 LingFlow 主项目一致

---

**"众智混元，万法灵通"**

*LingFlow REST API - 让工程流能力触达更多开发者*
