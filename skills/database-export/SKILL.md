# database-export 技能

## 技能概述

database-export 是一个业务技能，用于导出数据库数据。它可以连接到数据库，执行查询，并将结果导出为各种格式（如 CSV、JSON、Excel 等）。

## 功能特性

- **数据库连接**：连接到各种类型的数据库
- **数据查询**：执行 SQL 查询获取数据
- **格式导出**：将数据导出为 CSV、JSON、Excel 等格式
- **文件保存**：将导出的数据保存到指定位置
- **错误处理**：处理数据库连接和查询过程中的错误

## 使用场景

- 当你需要导出数据库中的数据时
- 当你需要将数据库数据转换为其他格式时
- 当你需要备份数据库数据时
- 当你需要在工作流中集成数据库导出功能时

## 触发条件

- `export database`
- `database export`
- `export data`
- `data export`
- `backup database`

## 依赖关系

- 无直接依赖关系

## 使用方法

### 1. 导出数据库数据

```bash
# 使用命令行导出数据库数据
lingflow run database-export --params '{"database": "mydb", "query": "SELECT * FROM users", "output": "users.csv", "format": "csv"}'
```

### 2. 导出整个数据库

```bash
# 导出整个数据库
lingflow run database-export --params '{"database": "mydb", "output": "backup", "format": "json", "export_all": true}'
```

## 技能结构

```
skills/database-export/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **明确导出目标**：在导出前，明确导出的目标和格式
2. **优化查询**：使用优化的 SQL 查询，避免导出过多数据
3. **格式选择**：根据需要选择合适的导出格式
4. **错误处理**：处理数据库连接和查询过程中的错误
5. **文件管理**：合理管理导出的文件，避免磁盘空间不足

## 故障排除

- **数据库连接失败**：检查数据库连接参数是否正确
- **查询执行失败**：检查 SQL 查询是否正确
- **文件写入失败**：检查文件路径是否正确，以及是否有足够的权限
- **格式转换失败**：检查导出格式是否支持

## 相关技能

- `upload-115` - 用于上传导出的数据文件
- `workflow-executor` - 用于在工作流中执行数据库导出
- `task-runner` - 用于执行数据库导出任务
