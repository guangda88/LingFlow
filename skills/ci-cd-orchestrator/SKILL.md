# ci-cd-orchestrator 技能

## 技能概述

ci-cd-orchestrator 是一个 CI/CD 流水线编排器，用于自动化生成和管理 CI/CD 配置。它支持多种主流 CI/CD 平台和编程语言，可以快速生成测试、构建和部署流程的配置文件。

## 功能特性

### 支持的平台

**1. GitHub Actions**：
- 生成 `.github/workflows/` 配置
- 支持矩阵构建策略
- 集成 GitHub Secrets
- 自动发布和部署

**2. Jenkins Pipeline**：
- 生成声明式 Jenkinsfile
- 支持多阶段流水线
- 集成 Jenkins 生态

**3. GitLab CI**：
- 生成 `.gitlab-ci.yml` 配置
- 支持并行作业
- 集成 GitLab Registry

**4. Azure Pipelines**：
- 生成 Azure Pipelines YAML
- 支持多阶段部署
- 集成 Azure Artifacts

**5. CircleCI**：
- 生成 `.circleci/config.yml`
- 支持工作流编排
- 集成 Orbs

### 支持的编程语言

- **Python** - pip, poetry, uv 包管理
- **JavaScript/TypeScript** - npm, yarn, pnpm
- **Go** - go modules
- **Rust** - cargo
- **Java** - Maven, Gradle

### 支持的部署目标

- **Docker** - 容器化部署到 Docker Registry
- **Kubernetes** - K8s 集群部署
- **Serverless** - AWS Lambda, Azure Functions
- **Static** - Vercel, Netlify 部署

### 核心功能

**1. 流水线生成**：
- 根据项目类型自动生成配置
- 支持自定义阶段配置
- 智能依赖检测

**2. 配置验证**：
- 语法检查
- 结构验证
- 最佳实践检查

**3. 模板管理**：
- 预定义模板库
- 自定义模板支持
- 模板版本管理

**4. 流程编排**：
- 测试阶段编排
- 构建阶段编排
- 部署阶段编排
- 条件执行支持

## 使用场景

- 当你需要为新项目创建 CI/CD 流水线时
- 当你需要迁移到不同的 CI/CD 平台时
- 当你需要标准化团队 CI/CD 配置时
- 当你需要配置自动化部署流程时
- 当你需要验证现有 CI/CD 配置时
- 当你需要快速原型化流水线时

## 触发条件

### 通用触发
- `ci cd`
- `pipeline`
- `workflow`
- `continuous integration`
- `continuous deployment`
- `build pipeline`
- `deploy pipeline`

### 平台特定触发
- `github actions` / `gh actions`
- `jenkins pipeline` / `jenkinsfile`
- `gitlab ci` / `gitlab-ci`
- `azure pipelines` / `azure pipeline`
- `circleci`

### 操作触发
- `generate pipeline` / `create pipeline`
- `validate workflow` / `check pipeline`
- `setup ci cd` / `configure ci`

## 依赖关系

- 无直接依赖关系
- 可与 `code-review` 结合进行代码质量检查
- 可与 `test-runner` 结合进行自动化测试
- 可与 `deployment-automation` 结合进行高级部署

## 使用方法

### 1. 生成 GitHub Actions 工作流

```bash
lingflow run ci-cd-orchestrator --params '{
  "action": "generate",
  "platform": "github",
  "language": "python",
  "stages": ["test", "build", "deploy"],
  "deploy_target": "docker",
  "output_file": ".github/workflows/ci.yml"
}'
```

### 2. 生成 Jenkins Pipeline

```bash
lingflow run ci-cd-orchestrator --params '{
  "action": "generate",
  "platform": "jenkins",
  "language": "javascript",
  "stages": ["test", "build"],
  "output_file": "Jenkinsfile"
}'
```

### 3. 验证现有配置

```bash
lingflow run ci-cd-orchestrator --params '{
  "action": "validate",
  "config_path": ".github/workflows/ci.yml"
}'
```

### 4. 列出可用模板

```bash
lingflow run ci-cd-orchestrator --params '{
  "action": "list"
}'
```

## 技能结构

```
skills/ci-cd-orchestrator/
├── SKILL.md              # 技能描述文件
├── implementation.py     # 技能实现文件
├── templates/            # 配置模板目录
│   ├── github-actions.yml
│   ├── jenkinsfile
│   ├── gitlab-ci.yml
│   ├── azure-pipelines.yml
│   └── circleci.yml
└── examples/             # 示例配置
    ├── python-github.yml
    ├── node-jenkins.groovy
    └── go-gitlab.yml
```

## 配置参数

### 生成参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | string | 否 | 操作类型 (generate/validate/list/help) |
| platform | string | 是 | CI/CD 平台 (github/jenkins/gitlab/azure/circleci) |
| language | string | 是 | 编程语言 (python/javascript/go/rust/java) |
| stages | array | 否 | 启用的阶段 (test/build/deploy) |
| deploy_target | string | 否 | 部署目标 (docker/kubernetes/serverless/static) |
| output_file | string | 否 | 输出文件路径 |
| custom_config | object | 否 | 自定义配置 |

### 验证参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | string | 是 | validate |
| config_path | string | 是 | 配置文件路径 |

## 最佳实践

1. **版本控制**：将 CI/CD 配置纳入版本控制
2. ** Secrets 管理**：使用平台 Secrets 功能存储敏感信息
3. **缓存优化**：配置依赖缓存加速构建
4. **并行执行**：利用矩阵策略并行测试
5. **渐进式部署**：使用蓝绿部署或金丝雀发布
6. **监控告警**：配置构建失败通知
7. **定期更新**：保持 CI/CD 工具和依赖最新

## 生成的配置示例

### GitHub Actions (Python)

```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        version: ['3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.version }}
      - name: Install dependencies
        run: pip install -e .[test]
      - name: Run tests
        run: pytest
  build:
    runs-on: ubuntu-latest
    needs: [test]
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: python -m build
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: build-artifacts
          path: dist/
```

### Jenkins Pipeline (JavaScript)

```groovy
pipeline {
    agent any

    environment {
        PROJECT_NAME = '${PROJECT_NAME:-my-project}'
        BRANCH_NAME = '${env.GIT_BRANCH ?: "main"}'
    }

    stages {
        stage("Test") {
            steps {
                sh 'git checkout ${env.GIT_BRANCH}'
                echo 'Running tests...'
                sh 'npm test'
            }
        }
        stage("Build") {
            steps {
                echo 'Building project...'
                sh 'npm run build'
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
```

## 故障排除

### 生成失败
- 检查平台和语言组合是否支持
- 验证输出目录是否有写入权限
- 检查自定义配置格式是否正确

### 配置验证失败
- 检查 YAML/语法是否正确
- 确认必需的配置项存在
- 查看详细错误信息

### 执行失败
- 检查 Secrets 是否正确配置
- 验证依赖安装命令是否有效
- 查看构建日志获取详细错误

## 相关技能

- `code-review` - 代码质量检查
- `test-runner` - 自动化测试执行
- `deployment-automation` - 高级部署自动化
- `environment-manager` - 环境配置管理
- `notification` - 构建通知
