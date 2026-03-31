# 工作流定义示例

本文档提供LingFlow工作流定义的详细示例和最佳实践。

## 目录

- [基础工作流](#基础工作流)
- [任务依赖](#任务依赖)
- [并行执行](#并行执行)
- [条件执行](#条件执行)
- [错误处理](#错误处理)
- [高级特性](#高级特性)

## 基础工作流

### 最小工作流

```yaml
name: "简单工作流"
tasks:
  - name: "代码检查"
    agent: "code_reviewer"
    skill: "static_analysis"
```

### 完整工作流

```yaml
name: "完整CI/CD流程"
description: "从代码检查到部署的完整流程"
version: "1.0"

# 全局参数
params:
  project_root: "."
  timeout: 3600

# 任务定义
tasks:
  - name: "代码检查"
    agent: "code_reviewer"
    skill: "static_analysis"
    params:
      target: "{{ params.project_root }}/src"
      severity: "warning"

  - name: "运行测试"
    agent: "tester"
    skill: "run_tests"
    depends_on: ["代码检查"]
    params:
      test_path: "{{ params.project_root }}/tests"
      coverage: true

  - name: "构建"
    agent: "builder"
    skill: "build"
    depends_on: ["运行测试"]
    params:
      output: "{{ params.project_root }}/dist"

  - name: "部署"
    agent: "deployer"
    skill: "deploy"
    depends_on: ["构建"]
    params:
      environment: "production"
```

## 任务依赖

### 串行依赖

```yaml
name: "串行执行"
tasks:
  - name: "步骤1"
    agent: "agent1"
    skill: "skill1"

  - name: "步骤2"
    agent: "agent2"
    skill: "skill2"
    depends_on: ["步骤1"]

  - name: "步骤3"
    agent: "agent3"
    skill: "skill3"
    depends_on: ["步骤2"]
```

### 多重依赖

```yaml
name: "多重依赖"
tasks:
  - name: "基础构建"
    agent: "builder"
    skill: "build"
    params:
      target: "core"

  - name: "前端构建"
    agent: "builder"
    skill: "build"
    params:
      target: "frontend"
    depends_on: ["基础构建"]

  - name: "后端构建"
    agent: "builder"
    skill: "build"
    params:
      target: "backend"
    depends_on: ["基础构建"]

  - name: "集成测试"
    agent: "tester"
    skill: "integration_test"
    depends_on: ["前端构建", "后端构建"]
```

## 并行执行

### 独立并行任务

```yaml
name: "并行测试"
tasks:
  - name: "单元测试"
    agent: "tester"
    skill: "run_tests"
    params:
      test_path: "tests/unit/"

  - name: "集成测试"
    agent: "tester"
    skill: "run_tests"
    params:
      test_path: "tests/integration/"

  - name: "E2E测试"
    agent: "tester"
    skill: "run_tests"
    params:
      test_path: "tests/e2e/"
```

### 并行后汇聚

```yaml
name: "并行处理"
tasks:
  - name: "数据处理A"
    agent: "processor"
    skill: "process"
    params:
      input: "data_a.csv"

  - name: "数据处理B"
    agent: "processor"
    skill: "process"
    params:
      input: "data_b.csv"

  - name: "数据合并"
    agent: "merger"
    skill: "merge"
    depends_on: ["数据处理A", "数据处理B"]
    params:
      sources: ["result_a.json", "result_b.json"]
      output: "merged.json"
```

## 条件执行

### 基于结果的条件

```yaml
name: "条件执行"
tasks:
  - name: "代码检查"
    agent: "code_reviewer"
    skill: "static_analysis"
    params:
      target: "src/"
    metadata:
      continue_on_failure: true

  - name: "修复警告"
    agent: "fixer"
    skill: "auto_fix"
    depends_on: ["代码检查"]
    condition: "{{ tasks.代码检查.issues | length > 0 }}"
    params:
      issues: "{{ tasks.代码检查.issues }}"

  - name: "运行测试"
    agent: "tester"
    skill: "run_tests"
    depends_on: ["代码检查", "修复警告"]
```

### 环境条件

```yaml
name: "环境相关"
tasks:
  - name: "开发部署"
    agent: "deployer"
    skill: "deploy"
    condition: "{{ environment == 'development' }}"
    params:
      environment: "dev"

  - name: "生产部署"
    agent: "deployer"
    skill: "deploy"
    condition: "{{ environment == 'production' }}"
    params:
      environment: "prod"
      approval: true
```

## 错误处理

### 失败重试

```yaml
name: "带重试的工作流"
tasks:
  - name: "API调用"
    agent: "api_client"
    skill: "call_api"
    retry:
      max_attempts: 3
      backoff: exponential
      initial_delay: 1
    params:
      endpoint: "https://api.example.com"
```

### 失败继续

```yaml
name: "容错工作流"
tasks:
  - name: "可选检查"
    agent: "checker"
    skill: "optional_check"
    continue_on_failure: true
    params:
      target: "src/"

  - name: "必需测试"
    agent: "tester"
    skill: "run_tests"
    depends_on: ["可选检查"]
    params:
      test_path: "tests/"
```

### 回滚机制

```yaml
name: "带回滚的部署"
tasks:
  - name: "部署"
    agent: "deployer"
    skill: "deploy"
    on_failure: "回滚"
    params:
      environment: "production"

  - name: "验证"
    agent: "validator"
    skill: "validate_deployment"
    depends_on: ["部署"]
    on_failure: "回滚"
    params:
      timeout: 300

  - name: "回滚"
    agent: "deployer"
    skill: "rollback"
    run_if: "any_parent_failed"
    params:
      backup: true
```

## 高级特性

### 循环和批处理

```yaml
name: "批处理"
tasks:
  - name: "获取文件列表"
    agent: "scanner"
    skill: "scan_files"
    params:
      directory: "src/"
      pattern: "*.py"

  - name: "批量审查"
    agent: "code_reviewer"
    skill: "batch_review"
    depends_on: ["获取文件列表"]
    params:
      files: "{{ tasks.获取文件列表.files }}"
      batch_size: 10
```

### 参数传递

```yaml
name: "参数传递"
tasks:
  - name: "生成配置"
    agent: "config_generator"
    skill: "generate"
    params:
      environment: "production"

  - name: "使用配置"
    agent: "deployer"
    skill: "deploy"
    depends_on: ["生成配置"]
    params:
      config: "{{ tasks.生成配置.output }}"

  - name: "验证"
    agent: "validator"
    skill: "validate"
    depends_on: ["使用配置"]
    params:
      deployment_id: "{{ tasks.使用配置.deployment_id }}"
```

### 动态任务生成

```yaml
name: "动态任务"
tasks:
  - name: "发现测试"
    agent: "discoverer"
    skill: "discover_tests"
    params:
      test_directory: "tests/"

  - name: "运行发现的测试"
    agent: "tester"
    skill: "run_test"
    depends_on: ["发现测试"]
    dynamic: true
    params:
      test: "{{ item }}"
    items: "{{ tasks.发现测试.tests }}"
```

## 实际场景示例

### 场景1: 微服务部署

```yaml
name: "微服务部署流水线"
description: "部署多个微服务并验证"

tasks:
  # 准备阶段
  - name: "构建所有服务"
    agent: "builder"
    skill: "build_all"
    params:
      services: ["auth", "api", "worker", "frontend"]

  # 部署阶段（并行）
  - name: "部署认证服务"
    agent: "deployer"
    skill: "deploy_service"
    depends_on: ["构建所有服务"]
    params:
      service: "auth"
      replicas: 3

  - name: "部署API服务"
    agent: "deployer"
    skill: "deploy_service"
    depends_on: ["构建所有服务"]
    params:
      service: "api"
      replicas: 5

  - name: "部署Worker服务"
    agent: "deployer"
    skill: "deploy_service"
    depends_on: ["构建所有服务"]
    params:
      service: "worker"
      replicas: 10

  # 验证阶段
  - name: "健康检查"
    agent: "monitor"
    skill: "health_check"
    depends_on: ["部署认证服务", "部署API服务", "部署Worker服务"]
    params:
      services: ["auth", "api", "worker"]
      timeout: 300

  - name: "集成测试"
    agent: "tester"
    skill: "integration_test"
    depends_on: ["健康检查"]
    params:
      test_suite: "microservice"
```

### 场景2: 数据处理管道

```yaml
name: "ETL数据管道"
description: "提取、转换、加载数据"

tasks:
  # 提取
  - name: "提取源数据A"
    agent: "extractor"
    skill: "extract"
    params:
      source: "database_a"
      query: "SELECT * FROM users"

  - name: "提取源数据B"
    agent: "extractor"
    skill: "extract"
    params:
      source: "api_b"
      endpoint: "/data/export"

  # 转换（并行）
  - name: "清洗数据A"
    agent: "transformer"
    skill: "clean"
    depends_on: ["提取源数据A"]
    params:
      input: "{{ tasks.提取源数据A.output }}"
      rules: "cleaning_rules_a.yaml"

  - name: "清洗数据B"
    agent: "transformer"
    skill: "clean"
    depends_on: ["提取源数据B"]
    params:
      input: "{{ tasks.提取源数据B.output }}"
      rules: "cleaning_rules_b.yaml"

  # 合并
  - name: "合并数据"
    agent: "merger"
    skill: "merge"
    depends_on: ["清洗数据A", "清洗数据B"]
    params:
      sources:
        - "{{ tasks.清洗数据A.output }}"
        - "{{ tasks.清洗数据B.output }}"
      strategy: "full_outer_join"
      output: "merged_data.parquet"

  # 加载
  - name: "加载数据仓库"
    agent: "loader"
    skill: "load"
    depends_on: ["合并数据"]
    params:
      source: "{{ tasks.合并数据.output }}"
      destination: "data_warehouse"
      table: "unified_data"

  # 验证
  - name: "数据质量检查"
    agent: "validator"
    skill: "validate_data"
    depends_on: ["加载数据仓库"]
    params:
      table: "unified_data"
      checks: "quality_rules.yaml"
```

### 场景3: 机器学习训练流程

```yaml
name: "ML训练流程"
description: "数据准备、模型训练、评估和部署"

tasks:
  # 数据准备
  - name: "数据预处理"
    agent: "data_engineer"
    skill: "preprocess"
    params:
      raw_data: "data/raw/"
      output: "data/processed/"
      features: ["feature1", "feature2", "feature3"]

  - name: "数据分割"
    agent: "data_engineer"
    skill: "split_data"
    depends_on: ["数据预处理"]
    params:
      input: "{{ tasks.数据预处理.output }}"
      train_ratio: 0.7
      val_ratio: 0.15
      test_ratio: 0.15

  # 模型训练
  - name: "超参数优化"
    agent: "ml_engineer"
    skill: "hyperparameter_tuning"
    depends_on: ["数据分割"]
    params:
      train_data: "{{ tasks.数据分割.train }}"
      val_data: "{{ tasks.数据分割.val }}"
      n_trials: 100
      timeout: 3600

  - name: "训练最终模型"
    agent: "ml_engineer"
    skill: "train_model"
    depends_on: ["超参数优化"]
    params:
      train_data: "{{ tasks.数据分割.train }}"
      val_data: "{{ tasks.数据分割.val }}"
      hyperparameters: "{{ tasks.超参数优化.best_params }}"

  # 评估和部署
  - name: "模型评估"
    agent: "ml_engineer"
    skill: "evaluate"
    depends_on: ["训练最终模型"]
    params:
      model: "{{ tasks.训练最终模型.model }}"
      test_data: "{{ tasks.数据分割.test }}"
      metrics: ["accuracy", "precision", "recall", "f1"]

  - name: "模型部署"
    agent: "mlops"
    skill: "deploy_model"
    depends_on: ["模型评估"]
    condition: "{{ tasks.模型评估.accuracy > 0.9 }}"
    params:
      model: "{{ tasks.训练最终模型.model }}"
      environment: "production"

  - name: "监控设置"
    agent: "mlops"
    skill: "setup_monitoring"
    depends_on: ["模型部署"]
    params:
      model_id: "{{ tasks.模型部署.model_id }}"
      metrics: ["prediction_latency", "model_drift"]
```

## 最佳实践

### 1. 模块化设计

```yaml
# base.yaml - 基础检查
tasks:
  - name: "预检查"
    agent: "guard"
    skill: "pre_check"

# tests.yaml - 测试套件
tasks:
  - name: "单元测试"
    agent: "tester"
    skill: "unit_tests"
  - name: "集成测试"
    agent: "tester"
    skill: "integration_tests"

# deploy.yaml - 部署流程
tasks:
  - name: "部署"
    agent: "deployer"
    skill: "deploy"
```

### 2. 参数化

```yaml
name: "参数化工作流"
params:
  environment: "{{ env | default('development') }}"
  version: "{{ version | default('latest') }}"

tasks:
  - name: "部署"
    agent: "deployer"
    skill: "deploy"
    params:
      environment: "{{ params.environment }}"
      version: "{{ params.version }}"
```

### 3. 版本控制

```yaml
name: "CI/CD v2.0"
version: "2.0"
description: "改进的CI/CD流程"

tasks:
  # ...
```

### 4. 文档化

```yaml
name: "文档化的工作流"
description: |
  这是一个完整的工作流示例，包含：
  1. 代码检查
  2. 测试执行
  3. 构建
  4. 部署

  作者: DevOps团队
  最后更新: 2026-03-31
```

## 相关文档

- [基础用法示例](basic_usage.md)
- [自定义Agent示例](custom_agent.md)
- [工作流引擎指南](../guides/workflow_engine.md)
