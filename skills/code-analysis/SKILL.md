# code-analysis 技能

## 技能概述

code-analysis 是一个用于分析代码质量的技能，它可以分析代码的复杂度、重复率、死代码等指标，为代码优化提供依据。

## 功能特性

- **代码复杂度分析**：分析代码的圈复杂度
- **重复代码检测**：检测代码中的重复部分
- **死代码识别**：识别未使用的导入和函数
- **代码统计**：统计代码文件数量和行数
- **分析报告**：生成详细的分析报告

## 使用场景

- 当你需要分析代码质量时
- 当你需要识别代码中的问题时
- 当你需要为代码优化提供依据时
- 当你需要在工作流中集成代码分析功能时

## 触发条件

- `analyze code`
- `code analysis`
- `code quality`
- `analyze codebase`
- `code metrics`

## 依赖关系

- 无直接依赖关系

## 使用方法

### 1. 分析代码库

```bash
# 使用命令行分析代码库
lingflow run code-analysis --params '{"target": "./lingflow/", "metrics": ["complexity", "duplication", "dead_code"]}'
```

### 2. 分析单个文件

```bash
# 分析单个文件
lingflow run code-analysis --params '{"target": "./lingflow/coordination/coordinator.py", "metrics": ["complexity"]}'
```

## 技能结构

```
skills/code-analysis/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **定期分析**：定期分析代码库，及时发现问题
2. **全面分析**：分析代码的各个方面，包括复杂度、重复率和死代码
3. **针对性优化**：根据分析结果，有针对性地进行代码优化
4. **持续改进**：根据分析结果持续改进代码质量
5. **集成到工作流**：将代码分析集成到工作流中，实现自动化分析

## 故障排除

- **分析失败**：检查目标路径是否存在，以及是否有足够的权限
- **分析速度慢**：对于大型代码库，分析可能需要较长时间
- **误报**：分析结果可能存在误报，需要人工验证
- **依赖问题**：某些分析功能可能需要额外的依赖

## 相关技能

- `code-optimizer` - 用于基于分析结果生成优化方案
- `code-refactor` - 用于执行代码重构
- `test-runner` - 用于验证优化结果
- `workflow-executor` - 用于在工作流中执行代码分析
