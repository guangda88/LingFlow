# Skill Creator 技能

## 技能概述

Skill Creator 是一个用于创建、修改和管理 lingflow 技能的专用工具。它允许用户快速创建新的技能模板，修改现有技能，以及管理技能的触发条件和依赖关系。

## 功能特性

- **创建新技能**：生成完整的技能目录结构和 SKILL.md 文件
- **修改现有技能**：更新技能描述、触发条件和依赖关系
- **技能验证**：检查技能配置的完整性和正确性
- **技能测试**：模拟技能触发和执行过程
- **技能文档生成**：自动生成技能的使用文档

## 使用场景

- 当你需要创建一个新的技能来扩展 lingflow 的功能时
- 当你需要修改现有技能的行为或触发条件时
- 当你需要为团队创建自定义技能时
- 当你需要验证技能配置是否正确时

## 触发条件

- `create skill`
- `new skill`
- `modify skill`
- `update skill`
- `skill configuration`
- `skill template`

## 依赖关系

- `brainstorming` - 在创建技能前需要先进行需求分析
- `writing-plans` - 需要制定技能的实现计划

## 使用方法

### 1. 创建新技能

```bash
# 使用命令行创建新技能
lingflow run skill-creator --params '{"action": "create", "skill_name": "my-new-skill", "description": "我的新技能"}'
```

### 2. 修改现有技能

```bash
# 修改现有技能
lingflow run skill-creator --params '{"action": "modify", "skill_name": "brainstorming", "description": "更新后的技能描述"}'
```

### 3. 验证技能

```bash
# 验证技能配置
lingflow run skill-creator --params '{"action": "validate", "skill_name": "brainstorming"}'
```

## 技能结构

创建的技能将包含以下文件结构：

```
skills/skill-name/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件（可选）
```

## 技能配置格式

技能的配置信息将被添加到 `skills.json` 文件中，格式如下：

```json
{
  "name": "skill-name",
  "description": "技能描述",
  "path": "skills/skill-name/SKILL.md",
  "triggers": ["trigger1", "trigger2"],
  "depends_on": ["dependency1", "dependency2"]
}
```

## 最佳实践

1. **清晰的技能描述**：使用简洁明了的语言描述技能的功能和用途
2. **合理的触发条件**：选择能够准确反映技能使用场景的触发词
3. **适当的依赖关系**：明确技能之间的依赖关系，确保工作流的正确性
4. **完整的文档**：为技能编写详细的使用文档，包括示例和最佳实践
5. **定期更新**：根据实际使用情况定期更新技能的配置和实现

## 示例

### 创建一个代码分析技能

```bash
lingflow run skill-creator --params '{
  "action": "create",
  "skill_name": "code-analysis",
  "description": "分析代码质量和性能",
  "triggers": ["analyze code", "code quality", "performance analysis"],
  "depends_on": ["brainstorming"]
}'
```

### 修改现有技能的触发条件

```bash
lingflow run skill-creator --params '{
  "action": "modify",
  "skill_name": "brainstorming",
  "triggers": ["feature", "build", "create", "design", "plan"]
}'
```

## 故障排除

- **技能创建失败**：检查技能名称是否已存在，以及权限是否正确
- **技能验证失败**：检查技能配置格式是否正确，依赖关系是否存在
- **技能触发不生效**：检查触发条件是否正确，以及技能是否已正确注册到 skills.json

## 相关技能

- `brainstorming` - 用于技能需求分析
- `writing-plans` - 用于技能实现规划
- `test-driven-development` - 用于技能测试
- `verification-before-completion` - 用于技能验证
