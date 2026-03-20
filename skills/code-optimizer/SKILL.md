# code-optimizer 技能

## 技能概述

code-optimizer 是一个用于基于代码分析结果生成优化方案的技能，它可以针对代码中的问题生成具体的优化建议和代码变更。

## 功能特性

- **优化方案生成**：基于代码分析结果生成优化方案
- **重复代码重构**：针对重复代码生成提取函数的建议
- **复杂度优化**：针对高复杂度代码生成拆分建议
- **死代码清理**：针对死代码生成删除建议
- **安全性评估**：评估优化方案的安全性

## 使用场景

- 当你需要基于代码分析结果生成优化方案时
- 当你需要自动生成代码重构建议时
- 当你需要在工作流中集成代码优化功能时
- 当你需要批量处理代码优化时

## 触发条件

- `optimize code`
- `code optimizer`
- `generate optimization`
- `code refactor`
- `optimization strategy`

## 依赖关系

- `code-analysis` - 用于获取代码分析结果

## 使用方法

### 1. 生成优化方案

```bash
# 使用命令行生成优化方案
lingflow run code-optimizer --params '{"issues": {"duplication_rate": 0.2, "dead_code": [{"file": "file.py", "issues": ["未使用的函数: test"]}], "complexity": {"file.py": 10}}, "strategy": "refactor_duplicates"}'
```

### 2. 针对特定问题生成优化方案

```bash
# 针对特定问题生成优化方案
lingflow run code-optimizer --params '{"issues": {"dead_code": [{"file": "file.py", "issues": ["未使用的函数: test"]}], "strategy": "remove_dead_code"}'
```

## 技能结构

```
skills/code-optimizer/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **基于分析结果**：在生成优化方案前，先使用 code-analysis 技能分析代码
2. **选择合适的策略**：根据代码问题选择合适的优化策略
3. **评估安全性**：在执行优化前，评估优化方案的安全性
4. **逐步优化**：对于大型代码库，建议逐步执行优化，避免一次性修改过多代码
5. **测试验证**：在执行优化后，使用 test-runner 技能验证优化结果

## 故障排除

- **分析结果不完整**：确保 code-analysis 技能的分析结果完整
- **优化方案不适用**：检查优化策略是否适合当前的代码问题
- **安全性评估失败**：如果优化方案被评估为不安全，需要人工审查
- **生成失败**：检查输入参数是否正确，以及是否有足够的权限

## 相关技能

- `code-analysis` - 用于获取代码分析结果
- `code-refactor` - 用于执行代码重构
- `test-runner` - 用于验证优化结果
- `workflow-executor` - 用于在工作流中执行代码优化
