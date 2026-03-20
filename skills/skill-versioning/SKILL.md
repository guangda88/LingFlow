# skill-versioning 技能

## 技能概述

skill-versioning 是一个用于管理技能版本的工具，它可以记录技能的每次变更，支持回滚到历史版本，并生成版本变更日志。

## 功能特性

- **版本记录**：记录技能的每次变更
- **版本回滚**：支持回滚到历史版本
- **变更日志**：生成版本变更日志
- **版本比较**：比较不同版本之间的差异
- **版本管理**：管理技能的版本生命周期

## 使用场景

- 当你需要跟踪技能的变更历史时
- 当你需要回滚到技能的历史版本时
- 当你需要生成技能的变更日志时
- 当你需要比较不同版本之间的差异时

## 触发条件

- `version skill`
- `skill history`
- `rollback skill`
- `skill changelog`
- `version control`

## 依赖关系

- `skill-creator` - 用于获取技能的基本信息

## 目录结构

```
skills/{skill-name}/
├── versions/
│   ├── v1.0.0/
│   ├── v1.1.0/
│   └── v2.0.0/
├── current -> versions/v2.0.0/
└── CHANGELOG.md
```

## 变更日志示例

```markdown
# CHANGELOG

## v2.0.0 (2026-03-21)

### 主要变更
- 重写了核心逻辑，提高了性能
- 添加了新的参数选项
- 修复了多个bug

### 向后兼容
- 旧版本的API调用仍然兼容

## v1.1.0 (2026-03-15)

### 功能添加
- 添加了错误处理机制
- 支持更多的输入格式

### 修复
- 修复了空输入的处理问题

## v1.0.0 (2026-03-10)

### 初始版本
- 实现了基本功能
- 支持基本的参数处理
```

## 使用方法

### 1. 创建新版本

```bash
# 使用命令行创建新版本
lingflow run skill-versioning --params '{"skill_name": "database-export", "version": "1.1.0", "changes": "添加了新功能"}'
```

### 2. 回滚到历史版本

```bash
# 回滚到历史版本
lingflow run skill-versioning --params '{"skill_name": "database-export", "action": "rollback", "version": "1.0.0"}'
```

### 3. 查看版本历史

```bash
# 查看版本历史
lingflow run skill-versioning --params '{"skill_name": "database-export", "action": "history"}'
```

### 4. 生成变更日志

```bash
# 生成变更日志
lingflow run skill-versioning --params '{"skill_name": "database-export", "action": "changelog"}'
```

## 技能结构

```
skills/skill-versioning/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **语义化版本**：使用语义化版本号（如 v1.0.0）
2. **详细记录**：每次变更都要详细记录变更内容
3. **定期备份**：定期创建版本快照，以便在需要时回滚
4. **版本测试**：每个版本都要进行测试，确保功能正常
5. **变更日志**：保持变更日志的更新，方便用户了解版本变化

## 故障排除

- **版本冲突**：检查是否有未提交的变更，解决冲突后再创建新版本
- **回滚失败**：检查目标版本是否存在，以及是否有足够的权限
- **版本历史丢失**：确保版本目录的权限正确，定期备份版本历史
- **变更日志生成失败**：检查技能目录结构是否正确

## 相关技能

- `skill-creator` - 用于创建和管理技能
- `skill-testing` - 用于测试不同版本的技能
- `skill-categorization` - 用于对技能进行分类管理
- `skill-analytics` - 用于分析技能的使用情况
