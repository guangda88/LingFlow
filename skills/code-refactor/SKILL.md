# code-refactor 技能

## 技能概述

code-refactor 是一个用于执行代码重构的技能，它可以根据优化方案对代码进行修改，包括提取函数、删除死代码、拆分复杂函数等操作，并在执行前创建备份。

## 功能特性

- **代码重构**：执行各种代码重构操作
- **备份功能**：在执行重构前创建代码备份
- **变更应用**：应用优化方案中的代码变更
- **安全性检查**：确保重构操作的安全性
- **结果验证**：验证重构后的代码是否正确

## 使用场景

- 当你需要执行代码重构时
- 当你需要应用优化方案中的变更时
- 当你需要在工作流中集成代码重构功能时
- 当你需要批量处理代码重构时

## 触发条件

- `refactor code`
- `code refactor`
- `apply changes`
- `execute refactor`
- `code modification`

## 依赖关系

- `code-optimizer` - 用于获取优化方案

## 使用方法

### 1. 执行代码重构

```bash
# 使用命令行执行代码重构
lingflow run code-refactor --params '{"changes": [{"file": "file.py", "type": "remove_function", "description": "删除未使用的函数 test"}], "backup": true}'
```

### 2. 执行批量重构

```bash
# 执行批量重构
lingflow run code-refactor --params '{"changes": [{"file": "file1.py", "type": "remove_function", "description": "删除未使用的函数 test"}, {"file": "file2.py", "type": "extract_function", "description": "提取重复代码为函数"}], "backup": true}'
```

## 技能结构

```
skills/code-refactor/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **备份代码**：在执行重构前，确保创建代码备份
2. **逐步执行**：对于大型重构，建议逐步执行，避免一次性修改过多代码
3. **验证结果**：在执行重构后，使用 test-runner 技能验证重构结果
4. **审查变更**：在执行重构前，审查变更内容，确保变更的正确性
5. **版本控制**：使用版本控制系统管理重构前后的代码变更

## 故障排除

- **备份失败**：检查是否有足够的权限创建备份目录
- **重构失败**：检查变更内容是否正确，以及是否有足够的权限修改文件
- **验证失败**：如果重构后的代码验证失败，检查变更内容并回滚到备份
- **文件不存在**：检查变更中指定的文件是否存在

## 相关技能

- `code-optimizer` - 用于获取优化方案
- `test-runner` - 用于验证重构结果
- `workflow-executor` - 用于在工作流中执行代码重构
- `error-handler` - 用于处理重构过程中的错误
