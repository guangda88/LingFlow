# {{SKILL_NAME}} 技能

## 技能概述

{{DESCRIPTION}}

## 功能特性

- **API调用**：调用外部API服务
- **参数处理**：处理API请求参数
- **错误处理**：处理API调用错误
- **响应解析**：解析API响应数据

## 使用场景

- 当你需要调用外部API服务时
- 当你需要集成第三方服务时
- 当你需要获取外部数据时

## 触发条件

- `{{SKILL_NAME}}`
- `call api`
- `api integration`

## 依赖关系

- `skill-creator` - 用于创建技能

## 使用方法

```bash
# 使用命令行调用技能
lingflow run {{SKILL_NAME}} --params '{"endpoint": "https://api.example.com", "payload": {"key": "value"}}'
```

## 技能结构

```
skills/{{SKILL_NAME}}/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```
