# skill-categorization 技能

## 技能概述

skill-categorization 是一个用于管理技能分类的工具，它可以对技能进行分类组织，方便用户查找和管理技能。

## 功能特性

- **技能分类**：对技能进行分类组织
- **分类管理**：管理技能分类体系
- **技能查询**：按分类查询技能
- **分类统计**：统计各分类的技能数量
- **分类导入导出**：导入导出分类配置

## 使用场景

- 当技能数量增多时，需要对技能进行分类管理
- 当你需要快速找到特定类型的技能时
- 当你需要了解技能的分布情况时
- 当你需要为团队建立技能分类体系时

## 触发条件

- `categorize skill`
- `organize skills`
- `skill taxonomy`
- `skill classification`
- `category management`

## 依赖关系

- `skill-creator` - 用于获取技能的基本信息

## 分类体系建议

```
技能分类：
├── 数据处理类
│   ├── database-export
│   ├── data-transform
│   └── data-validate
├── AI分析类
│   ├── code-review
│   ├── text-summarize
│   └── sentiment-analysis
├── 集成类
│   ├── upload-115
│   ├── send-notification
│   └── call-api
├── 开发类
│   ├── skill-creator
│   ├── skill-testing
│   └── skill-versioning
└── 工作流类
    ├── workflow-executor
    └── conditional-branch
```

## 使用方法

### 1. 为技能添加分类

```bash
# 使用命令行为技能添加分类
lingflow run skill-categorization --params '{"skill_name": "database-export", "category": "数据处理类"}'
```

### 2. 查看分类列表

```bash
# 查看分类列表
lingflow run skill-categorization --params '{"action": "list_categories"}'
```

### 3. 按分类查询技能

```bash
# 按分类查询技能
lingflow run skill-categorization --params '{"action": "skills_by_category", "category": "数据处理类"}'
```

### 4. 生成分类统计

```bash
# 生成分类统计
lingflow run skill-categorization --params '{"action": "category_stats"}'
```

## 技能结构

```
skills/skill-categorization/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **合理分类**：根据技能的功能和用途进行合理分类
2. **层次清晰**：分类体系应该层次清晰，避免过深的嵌套
3. **命名规范**：分类名称应该简洁明了，反映技能的类型
4. **定期维护**：定期检查和维护分类体系，确保其与技能的发展保持一致
5. **标准化**：建立统一的分类标准，确保团队成员使用一致的分类方法

## 故障排除

- **分类不存在**：检查分类名称是否正确，以及分类是否已创建
- **技能分类失败**：检查技能是否存在，以及是否有足够的权限
- **分类统计错误**：检查分类配置是否正确，以及技能是否正确分类
- **导入导出失败**：检查文件格式是否正确，以及权限是否足够

## 相关技能

- `skill-creator` - 用于创建和管理技能
- `skill-testing` - 用于测试技能
- `skill-versioning` - 用于管理技能的版本
- `skill-analytics` - 用于分析技能的使用情况
