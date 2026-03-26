# deployment-automation 技能

## 技能概述

deployment-automation 是一个自动化部署技能，支持生成容器化配置、Kubernetes 部署清单、蓝绿部署和回滚机制。

## 功能特性

### 1. Dockerfile 生成
- 自动检测项目类型（Python、Node.js、Go、Java等）
- 生成优化的多阶段构建 Dockerfile
- 支持自定义基础镜像和构建参数
- 遵循最佳安全实践

### 2. Kubernetes 部署配置
- 生成 Deployment、Service、Ingress 配置
- 支持 ConfigMap 和 Secret 管理
- HPA (Horizontal Pod Autoscaler) 配置
- 资源限制和请求配置

### 3. 蓝绿部署
- 生成蓝绿部署清单
- Service 切换配置
- 流量迁移策略
- 健康检查配置

### 4. 回滚机制
- 版本管理
- 自动化回滚脚本
- 回滚策略配置
- 健康检查和故障转移

### 5. 部署工作流
- CI/CD pipeline 配置
- 环境变量管理
- 构建和部署脚本

## 使用场景

- 需要容器化应用时
- 需要 Kubernetes 部署配置时
- 实施蓝绿部署策略时
- 配置自动化回滚机制时
- 建立 CI/CD 流水线时

## 触发条件

- `deploy automation`
- `generate dockerfile`
- `kubernetes deployment`
- `blue green deployment`
- `deployment rollback`
- `容器化部署`
- `k8s 部署`
- `蓝绿部署`

## 参数配置

```json
{
  "project_type": "python|nodejs|go|java|static",
  "app_name": "application-name",
  "port": 8080,
  "replicas": 3,
  "dockerfile_options": {
    "base_image": "python:3.11-slim",
    "multi_stage": true,
    "include_dev": false
  },
  "k8s_options": {
    "namespace": "default",
    "create_service": true,
    "create_ingress": false,
    "enable_hpa": false,
    "resources": {
      "requests": {"cpu": "100m", "memory": "128Mi"},
      "limits": {"cpu": "500m", "memory": "512Mi"}
    }
  },
  "deployment_strategy": "rolling|blue_green",
  "blue_green_options": {
    "active_color": "blue",
    "health_check_path": "/health",
    "switch_service": true
  }
}
```

## 使用方法

### 1. 生成 Dockerfile

```bash
lingflow run deployment-automation --params '{
  "action": "generate_dockerfile",
  "project_type": "python",
  "output_path": "./Dockerfile"
}'
```

### 2. 生成 Kubernetes 配置

```bash
lingflow run deployment-automation --params '{
  "action": "generate_k8s",
  "app_name": "myapp",
  "port": 8080,
  "output_dir": "./k8s"
}'
```

### 3. 蓝绿部署配置

```bash
lingflow run deployment-automation --params '{
  "action": "blue_green_deploy",
  "app_name": "myapp",
  "output_dir": "./k8s/blue-green"
}'
```

### 4. 生成完整部署方案

```bash
lingflow run deployment-automation --params '{
  "action": "full",
  "project_type": "nodejs",
  "app_name": "myapp",
  "port": 3000,
  "deployment_strategy": "blue_green",
  "output_dir": "./deployment"
}'
```

## 技能结构

```
skills/deployment-automation/
├── SKILL.md              # 技能描述文件
├── implementation.py      # 技能实现文件
└── templates/            # 配置模板目录
    ├── dockerfile/       # Dockerfile 模板
    │   ├── python.j2
    │   ├── nodejs.j2
    │   ├── go.j2
    │   └── java.j2
    ├── k8s/              # Kubernetes 模板
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── ingress.yaml
    │   └── hpa.yaml
    └── blue-green/       # 蓝绿部署模板
        ├── deployment-blue.yaml
        ├── deployment-green.yaml
        └── service-switch.yaml
```

## 最佳实践

1. **安全扫描**：生成 Dockerfile 后进行安全扫描
2. **资源限制**：合理设置 CPU 和内存限制
3. **健康检查**：配置 readiness 和 liveness 探针
4. **版本标签**：使用语义化版本标签
5. **配置管理**：敏感信息使用 Secret，配置用 ConfigMap

## 故障排除

- **镜像构建失败**：检查 Dockerfile 语法和依赖
- **部署超时**：增加健康检查超时时间
- **资源不足**：调整 requests 和 limits
- **蓝绿切换失败**：验证健康检查配置

## 相关技能

- `ci-cd-orchestrator` - CI/CD 流水线编排
- `environment-manager` - 环境管理
- `code-review` - 部署前代码审查
