# test-runner 技能

## 技能概述

test-runner 是一个用于运行测试并返回结果的技能，它可以运行单元测试、集成测试等，并返回测试结果和覆盖率报告。

## 功能特性

- **测试执行**：运行各种类型的测试
- **结果分析**：分析测试结果，统计通过和失败的测试用例
- **覆盖率报告**：生成代码覆盖率报告
- **测试环境**：设置和管理测试环境
- **测试报告**：生成详细的测试报告

## 使用场景

- 当你需要运行测试验证代码变更时
- 当你需要在工作流中集成测试功能时
- 当你需要批量运行测试时
- 当你需要生成测试覆盖率报告时

## 触发条件

- `run tests`
- `test runner`
- `execute tests`
- `test verification`
- `run unit tests`

## 依赖关系

- 无直接依赖关系

## 使用方法

### 1. 运行单元测试

```bash
# 使用命令行运行单元测试
lingflow run test-runner --params '{"file": "./tests/test_example.py", "test_type": "unit"}'
```

### 2. 运行集成测试

```bash
# 运行集成测试
lingflow run test-runner --params '{"file": "./tests/integration", "test_type": "integration"}'
```

### 3. 生成覆盖率报告

```bash
# 生成覆盖率报告
lingflow run test-runner --params '{"file": "./tests", "test_type": "coverage"}'
```

## 技能结构

```
skills/test-runner/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
└── implementation.py # 技能实现文件
```

## 最佳实践

1. **定期测试**：定期运行测试，确保代码的质量和可靠性
2. **全面测试**：运行各种类型的测试，包括单元测试、集成测试和端到端测试
3. **覆盖率目标**：设定合理的代码覆盖率目标，确保代码的测试覆盖度
4. **自动化测试**：将测试集成到工作流中，实现自动化测试
5. **测试结果分析**：分析测试结果，及时发现和解决问题

## 故障排除

- **测试失败**：检查测试代码是否正确，以及被测试的代码是否符合预期
- **环境问题**：检查测试环境是否正确设置，以及依赖项是否安装
- **覆盖率低**：分析覆盖率报告，找出未覆盖的代码并添加测试
- **运行超时**：检查测试是否有无限循环或耗时操作

## 相关技能

- `code-refactor` - 用于执行代码重构
- `code-optimizer` - 用于生成优化方案
- `workflow-executor` - 用于在工作流中执行测试
- `error-handler` - 用于处理测试过程中的错误
