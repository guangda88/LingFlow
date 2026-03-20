# error-handler 技能

## 技能概述

error-handler 是一个核心技能，用于任务失败时的重试和降级。它可以在任务执行失败时进行重试，或者在重试失败后执行降级策略，确保工作流的稳定性和可靠性。

## 功能特性

- **自动重试**：当任务执行失败时自动重试
- **重试策略**：支持配置重试次数和间隔
- **降级处理**：当重试失败后执行降级策略
- **错误分析**：分析任务失败的原因
- **结果处理**：处理任务执行的结果

## 使用场景

- 当你需要处理可能失败的任务时
- 当你需要确保任务最终能够成功执行时
- 当你需要在任务失败时执行备用方案时
- 当你需要提高工作流的可靠性时

## 触发条件

- `error handling`
- `retry task`
- `fallback`
- `error recovery`
- `fault tolerance`

## 依赖关系

- `task-runner` - 用于执行任务和重试

## 使用方法

### 1. 执行带重试的任务

```bash
# 使用命令行执行带重试的任务
lingflow run error-handler --params '{"task": {"skill": "database-export", "params": {"database": "mydb"}}, "retries": 3, "retry_interval": 5}'
```

### 2. 带降级策略的任务

```bash
# 带降级策略的任务
lingflow run error-handler --params '{"task": {"skill": "database-export", "params": {"database": "mydb"}}, "retries": 3, "fallback": {"skill": "backup-service", "params": {"service": "local"}}}'
```

## 技能结构

```
skills/error-handler/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **合理设置重试**：根据任务的性质和失败原因，合理设置重试次数和间隔
2. **降级策略**：为重要任务设置合理的降级策略，确保系统的可用性
3. **错误分析**：分析任务失败的原因，持续改进系统
4. **监控告警**：监控任务的执行情况，及时发现和处理问题
5. **性能考虑**：注意重试对系统性能的影响，避免过度重试

## 故障排除

- **重试失败**：检查任务失败的原因，可能需要调整任务参数或环境
- **降级策略失败**：检查降级策略的配置是否正确
- **重试间隔问题**：检查重试间隔是否合理，避免过短的间隔导致系统压力过大
- **错误分析失败**：检查错误分析的配置是否正确

## 相关技能

- `workflow-executor` - 用于执行包含错误处理的工作流
- `task-runner` - 用于执行任务和重试
- `conditional-branch` - 用于根据错误情况执行不同的处理逻辑
- `loop-iterator` - 用于批量处理任务时的错误处理
