# task-runner 技能

## 技能概述

task-runner 是一个核心技能，用于执行单个任务（技能调用）。它可以调用其他技能，传递参数，并返回执行结果。

## 功能特性

- **技能调用**：调用其他技能执行任务
- **参数传递**：向被调用的技能传递参数
- **结果返回**：返回技能执行的结果
- **错误处理**：处理技能执行过程中的错误
- **任务监控**：监控任务的执行状态

## 使用场景

- 当你需要执行单个技能时
- 当你需要向技能传递参数时
- 当你需要获取技能执行的结果时
- 当你需要在工作流中执行单个任务时

## 触发条件

- `run task`
- `execute task`
- `run skill`
- `execute skill`
- `call skill`

## 依赖关系

- 无直接依赖关系

## 使用方法

### 1. 执行单个任务

```bash
# 使用命令行执行单个任务
lingflow run task-runner --params '{"skill": "database-export", "params": {"database": "mydb", "output": "backup/db.sql"}}'
```

### 2. 执行多个任务

```bash
# 执行多个任务
lingflow run task-runner --params '{"tasks": [{"skill": "database-export", "params": {"database": "mydb"}}, {"skill": "upload-115", "params": {"file": "backup/db.sql"}}]}'
```

## 技能结构

```
skills/task-runner/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **明确任务目标**：在执行任务前，明确任务的目标和参数
2. **合理传递参数**：根据技能的要求，合理传递参数
3. **错误处理**：处理任务执行过程中的错误
4. **结果处理**：正确处理任务执行的结果
5. **性能优化**：优化任务执行的性能

## 故障排除

- **技能不存在**：检查技能名称是否正确
- **参数错误**：检查传递的参数是否符合技能的要求
- **执行失败**：检查技能的实现是否正确
- **权限不足**：检查是否有足够的权限执行任务

## 相关技能

- `workflow-executor` - 用于执行工作流
- `conditional-branch` - 用于工作流中的条件判断
- `loop-iterator` - 用于工作流中的循环执行
- `error-handler` - 用于任务失败时的重试和降级
