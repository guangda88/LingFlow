# 基础用法示例

本文档提供lingflow的基础用法示例，帮助你快速理解和使用系统。

## 目录

- [初始化系统](#初始化系统)
- [执行技能](#执行技能)
- [工作流管理](#工作流管理)
- [上下文管理](#上下文管理)
- [监控和日志](#监控和日志)

## 初始化系统

### 基础初始化

```python
from lingflow import lingflow

# 使用默认配置初始化
lf = lingflow()
```

### 自定义配置初始化

```python
from lingflow import lingflow

# 使用自定义配置
config = {
    "compression_enabled": True,
    "compression_target_tokens": 4000,
    "max_agents": 10,
    "log_level": "INFO"
}

lf = lingflow(config=config)
```

### 环境变量配置

```bash
# .env 文件
ANTHROPIC_API_KEY=your-api-key
LINGFLOW_LOG_LEVEL=DEBUG
LINGFLOW_MAX_AGENTS=20
LINGFLOW_COMPRESSION_THRESHOLD=0.85
```

```python
# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from lingflow import lingflow
lf = lingflow()
```

## 执行技能

### 代码审查

```python
# 基础代码审查
result = lf.run_skill("code_review", {
    "file_path": "src/main.py"
})

# 带关注领域的代码审查
result = lf.run_skill("code_review", {
    "file_path": "src/main.py",
    "focus_areas": ["security", "performance", "style"],
    "severity": "error"
})

# 处理结果
if result["status"] == "success":
    print(f"发现 {len(result['issues'])} 个问题")
    for issue in result["issues"]:
        print(f"- {issue['line']}: {issue['message']}")
```

### 测试执行

```python
# 运行所有测试
result = lf.run_skill("run_tests", {
    "test_path": "tests/"
})

# 运行特定测试
result = lf.run_skill("run_tests", {
    "test_path": "tests/test_auth.py",
    "verbose": True
})

# 带覆盖率的测试
result = lf.run_skill("run_tests", {
    "test_path": "tests/",
    "coverage": True,
    "coverage_threshold": 80
})
```

### 需求分析

```python
# 分析需求文档
result = lf.run_skill("analyze_requirements", {
    "doc_path": "docs/requirements.md"
})

# 提取需求
result = lf.run_skill("extract_requirements", {
    "source": "PRD-001",
    "format": "structured"
})

# 验证追溯性
result = lf.run_skill("verify_traceability", {
    "requirement_id": "REQ-001"
})
```

## 工作流管理

### YAML工作流

```yaml
# workflows/ci_cd.yaml
name: "CI/CD 流水线"
description: "完整的持续集成和部署流程"

tasks:
  - name: "代码检查"
    agent: "code_reviewer"
    skill: "static_analysis"
    params:
      target: "src/"
      severity: "warning"

  - name: "运行测试"
    agent: "tester"
    skill: "run_tests"
    depends_on: ["代码检查"]
    params:
      test_path: "tests/"
      coverage: true

  - name: "构建"
    agent: "builder"
    skill: "build"
    depends_on: ["运行测试"]
    params:
      output: "dist/"

  - name: "部署"
    agent: "deployer"
    skill: "deploy"
    depends_on: ["构建"]
    params:
      environment: "production"
```

### 执行工作流

```python
# 从文件执行
result = lf.run_workflow_file("workflows/ci_cd.yaml")

# 检查结果
if result["status"] == "success":
    print("工作流执行成功")
    for task_name, task_result in result["tasks"].items():
        print(f"  {task_name}: {task_result['status']}")
else:
    print(f"工作流失败: {result['error']}")
```

### 动态工作流

```python
# 动态定义工作流
workflow_def = {
    "name": "临时工作流",
    "tasks": [
        {
            "name": "任务1",
            "agent": "code_reviewer",
            "skill": "static_analysis",
            "params": {"target": "src/"}
        },
        {
            "name": "任务2",
            "agent": "tester",
            "skill": "run_tests",
            "depends_on": ["任务1"],
            "params": {"test_path": "tests/"}
        }
    ]
}

result = lf.run_workflow(workflow_def)
```

### 并行执行

```python
# 定义并行任务
workflow_def = {
    "name": "并行测试",
    "tasks": [
        {
            "name": "单元测试",
            "agent": "tester",
            "skill": "run_tests",
            "params": {"test_path": "tests/unit/"}
        },
        {
            "name": "集成测试",
            "agent": "tester",
            "skill": "run_tests",
            "params": {"test_path": "tests/integration/"}
        },
        {
            "name": "E2E测试",
            "agent": "tester",
            "skill": "run_tests",
            "params": {"test_path": "tests/e2e/"}
        }
    ]
}

# 这些任务将并行执行
result = lf.run_workflow(workflow_def)
```

## 上下文管理

### 获取上下文管理器

```python
from lingflow import get_context_manager

ctx_mgr = get_context_manager()

# 查看当前状态
status = ctx_mgr.get_status()
print(f"Token数: {status['token_count']}")
print(f"内存使用: {status['memory_usage']}")
```

### 手动压缩上下文

```python
from lingflow import compress_context

# 立即压缩上下文
compressed = compress_context()
print(compressed)
```

### 保存和恢复会话

```python
from lingflow import get_context_manager

ctx_mgr = get_context_manager()

# 保存当前会话
ctx_mgr.save_session("my_session")

# 恢复会话
ctx_mgr.load_session("my_session")

# 列出所有会话
sessions = ctx_mgr.list_sessions()
print(sessions)
```

### 追踪上下文

```python
from lingflow import track_context

# 使用装饰器追踪函数
@track_context
def process_data(data):
    # 处理数据
    return result

# 函数执行会自动追踪上下文
result = process_data(large_dataset)
```

## 监控和日志

### 启用监控

```python
from lingflow.monitoring import OperationsMonitor

monitor = OperationsMonitor()

# 追踪操作
@monitor.track_operation
def api_call():
    # API调用
    return response

# 查看指标
metrics = monitor.get_metrics()
print(f"平均响应时间: {metrics['avg_latency']}ms")
print(f"成功率: {metrics['success_rate']}%")
```

### 自定义日志

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("lingflow")

# 使用日志
logger.info("开始执行任务")
logger.debug("调试信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 性能分析

```python
from lingflow.utils.performance import profile_performance

@profile_performance
def expensive_operation():
    # 耗时操作
    return result

# 函数执行后会输出性能分析
result = expensive_operation()
```

## 错误处理

### 异常捕获

```python
try:
    result = lf.run_skill("code_review", {
        "file_path": "non_existent.py"
    })
except FileNotFoundError as e:
    print(f"文件不存在: {e}")
except Exception as e:
    print(f"执行失败: {e}")
```

### 重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
def run_with_retry(skill_name, params):
    return lf.run_skill(skill_name, params)

# 自动重试
result = run_with_retry("code_review", {"file_path": "main.py"})
```

## 最佳实践

### 1. 使用配置文件

```python
# config.py
LINGFLOW_CONFIG = {
    "compression_enabled": True,
    "compression_target_tokens": 4000,
    "max_agents": 10
}

# main.py
from config import LINGFLOW_CONFIG
from lingflow import lingflow

lf = lingflow(config=LINGFLOW_CONFIG)
```

### 2. 模块化工作流

```yaml
# workflows/base.yaml
tasks:
  - name: "前置检查"
    agent: "guard"
    skill: "pre_check"

# workflows/tests.yaml
tasks:
  - name: "单元测试"
    agent: "tester"
    skill: "run_tests"
  - name: "集成测试"
    agent: "tester"
    skill: "run_tests"

# workflows/deploy.yaml
tasks:
  - name: "部署"
    agent: "deployer"
    skill: "deploy"
```

### 3. 资源清理

```python
from lingflow import lingflow

lf = lingflow()

try:
    # 执行任务
    result = lf.run_skill("code_review", {"file_path": "main.py"})
finally:
    # 清理资源
    del lf
```

### 4. 日志记录

```python
import logging
from lingflow import lingflow

logger = logging.getLogger(__name__)

lf = lingflow()

logger.info("开始代码审查")
result = lf.run_skill("code_review", {"file_path": "main.py"})

if result["status"] == "success":
    logger.info(f"审查完成，发现 {len(result['issues'])} 个问题")
else:
    logger.error(f"审查失败: {result['error']}")
```

## 完整示例

### 端到端CI/CD流程

```python
#!/usr/bin/env python3
"""完整的CI/CD流程示例"""

from lingflow import lingflow
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # 初始化lingflow
    lf = lingflow()

    # 1. 代码检查
    logger.info("步骤1: 代码检查")
    review_result = lf.run_skill("code_review", {
        "file_path": "src/main.py",
        "focus_areas": ["security", "performance"]
    })

    if review_result["status"] != "success":
        logger.error("代码检查失败")
        return False

    # 2. 运行测试
    logger.info("步骤2: 运行测试")
    test_result = lf.run_skill("run_tests", {
        "test_path": "tests/",
        "coverage": True,
        "coverage_threshold": 80
    })

    if test_result["status"] != "success":
        logger.error("测试失败")
        return False

    # 3. 构建
    logger.info("步骤3: 构建项目")
    build_result = lf.run_skill("build", {
        "target": "src/",
        "output": "dist/"
    })

    if build_result["status"] != "success":
        logger.error("构建失败")
        return False

    # 4. 部署
    logger.info("步骤4: 部署")
    deploy_result = lf.run_skill("deploy", {
        "environment": "production",
        "artifact": "dist/app.zip"
    })

    if deploy_result["status"] != "success":
        logger.error("部署失败")
        return False

    logger.info("✓ CI/CD流程完成")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

## 更多示例

- [工作流定义示例](workflow_definition.md)
- [自定义Agent示例](custom_agent.md)
- [自优化配置示例](self_optimization.md)

---

## 相关文档

- [API 参考](../api/lingflow.md)
- [快速开始](../quickstart.md)
- [架构指南](../guides/architecture.md)
