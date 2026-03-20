# conditional-branch 技能

## 技能概述

conditional-branch 是一个核心技能，用于工作流中的条件判断。它可以根据指定的条件执行不同的任务分支，实现工作流的条件控制。

## 功能特性

- **条件判断**：根据条件执行不同的任务分支
- **多分支支持**：支持多个条件分支
- **默认分支**：当所有条件都不满足时执行默认分支
- **表达式支持**：支持复杂的条件表达式
- **结果传递**：将条件判断的结果传递给后续任务

## 使用场景

- 当你需要根据不同条件执行不同任务时
- 当你需要在工作流中实现条件逻辑时
- 当你需要根据前面任务的结果决定后续操作时
- 当你需要在工作流中实现分支逻辑时

## 触发条件

- `conditional branch`
- `if condition`
- `branch condition`
- `condition check`
- `conditional execution`

## 依赖关系

- `task-runner` - 用于执行条件分支中的任务

## 使用方法

### 1. 执行条件分支

```bash
# 使用命令行执行条件分支
lingflow run conditional-branch --params '{"condition": "${var} > 10", "branches": [{"condition": "${var} > 10", "tasks": [{"skill": "task1"}]}, {"condition": "${var} <= 10", "tasks": [{"skill": "task2"}]}]}'
```

### 2. 带默认分支的条件判断

```bash
# 带默认分支的条件判断
lingflow run conditional-branch --params '{"condition": "${var} > 10", "branches": [{"condition": "${var} > 10", "tasks": [{"skill": "task1"}]}, {"condition": "${var} <= 10", "tasks": [{"skill": "task2"}]}], "default_branch": [{"skill": "task3"}]}'
```

## 技能结构

```
skills/conditional-branch/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **明确条件**：在使用条件分支前，明确条件表达式和分支逻辑
2. **合理分支**：根据实际需求设置合理的分支数量
3. **默认分支**：为所有条件都不满足的情况设置默认分支
4. **结果传递**：合理使用条件判断的结果，传递给后续任务
5. **测试验证**：测试不同条件下的分支执行情况，确保逻辑正确

## 故障排除

- **条件表达式错误**：检查条件表达式的语法是否正确
- **分支执行失败**：检查分支中的任务是否正确配置
- **变量不存在**：检查条件中使用的变量是否存在
- **默认分支问题**：检查默认分支的配置是否正确

## 相关技能

- `workflow-executor` - 用于执行包含条件分支的工作流
- `task-runner` - 用于执行条件分支中的任务
- `loop-iterator` - 用于工作流中的循环执行
- `error-handler` - 用于任务失败时的重试和降级
