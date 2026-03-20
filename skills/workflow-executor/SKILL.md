# workflow-executor 技能

## 技能概述

workflow-executor 是一个核心技能，用于执行YAML/JSON定义的工作流。它可以解析工作流配置，按照定义的顺序执行任务，并处理任务之间的依赖关系。

## 功能特性

- **工作流解析**：解析YAML/JSON格式的工作流配置
- **任务执行**：按照工作流定义执行任务
- **依赖管理**：处理任务之间的依赖关系
- **状态管理**：跟踪工作流的执行状态
- **错误处理**：处理工作流执行过程中的错误

## 使用场景

- 当你需要执行复杂的工作流程时
- 当你需要按照特定顺序执行多个任务时
- 当你需要处理任务之间的依赖关系时
- 当你需要自动化执行一系列相关任务时

## 触发条件

- `run workflow`
- `execute workflow`
- `workflow run`
- `workflow execute`
- `run workflow file`

## 依赖关系

- `task-runner` - 用于执行单个任务

## 使用方法

### 1. 执行工作流文件

```bash
# 使用命令行执行工作流文件
lingflow run workflow-executor --params '{"workflow_file": "workflows/daily_backup.yaml"}'
```

### 2. 执行工作流配置

```bash
# 执行工作流配置
lingflow run workflow-executor --params '{"workflow": {"name": "backup", "tasks": [{"name": "backup_db", "skill": "database-export"}]}}'
```

## 工作流配置格式

### YAML 格式

```yaml
name: daily_backup
description: 每日备份工作流
tasks:
  - name: backup_db
    skill: database-export
    params:
      database: "mydb"
      output: "backup/db.sql"
  - name: upload_backup
    skill: upload-115
    params:
      file: "backup/db.sql"
      folder: "/backup"
    depends_on:
      - backup_db
```

### JSON 格式

```json
{
  "name": "daily_backup",
  "description": "每日备份工作流",
  "tasks": [
    {
      "name": "backup_db",
      "skill": "database-export",
      "params": {
        "database": "mydb",
        "output": "backup/db.sql"
      }
    },
    {
      "name": "upload_backup",
      "skill": "upload-115",
      "params": {
        "file": "backup/db.sql",
        "folder": "/backup"
      },
      "depends_on": ["backup_db"]
    }
  ]
}
```

## 技能结构

```
skills/workflow-executor/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **明确工作流目标**：在创建工作流前，明确工作流的目标和执行顺序
2. **合理设置依赖**：根据任务之间的依赖关系，合理设置 `depends_on` 字段
3. **错误处理**：为工作流添加适当的错误处理机制
4. **测试工作流**：在正式执行前，测试工作流的执行效果
5. **监控执行**：监控工作流的执行状态，及时发现和处理问题

## 故障排除

- **工作流文件不存在**：检查工作流文件路径是否正确
- **任务执行失败**：检查任务的参数是否正确，以及依赖的技能是否存在
- **依赖解析错误**：检查 `depends_on` 字段是否指向存在的任务
- **配置格式错误**：检查工作流配置文件的格式是否正确

## 相关技能

- `task-runner` - 用于执行单个任务
- `conditional-branch` - 用于工作流中的条件判断
- `loop-iterator` - 用于工作流中的循环执行
- `error-handler` - 用于任务失败时的重试和降级
