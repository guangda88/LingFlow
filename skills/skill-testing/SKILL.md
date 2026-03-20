# skill-testing 技能

## 技能概述

skill-testing 是一个用于测试技能的功能、性能和可靠性的专用工具。它可以根据技能的配置生成测试用例，模拟技能执行环境，并验证输入输出是否符合预期。

## 功能特性

- **生成测试用例**：根据技能类型自动生成测试用例
- **模拟执行环境**：创建模拟的技能执行环境
- **验证结果**：检查技能执行结果是否符合预期
- **性能测试**：测试技能的执行时间和资源消耗
- **生成测试报告**：生成详细的测试报告

## 使用场景

- 当你创建了一个新技能，需要验证其功能是否正常时
- 当你修改了现有技能，需要确保没有破坏原有功能时
- 当你需要评估技能的性能和可靠性时
- 当你需要为技能提供质量保证时

## 触发条件

- `test skill`
- `run skill test`
- `skill validation`
- `skill quality`
- `test skill performance`

## 依赖关系

- `skill-creator` - 用于获取技能的配置信息
- `verification-before-completion` - 用于验证测试结果

## 工作流程

1. 加载目标技能的 SKILL.md 配置
2. 根据技能类型生成测试用例
3. 模拟技能执行环境
4. 验证输入输出是否符合预期
5. 生成测试报告

## 测试类型

- **功能测试**：验证基本功能是否正常
- **边界测试**：测试极端输入的处理
- **依赖测试**：验证依赖技能是否可用
- **性能测试**：测试执行时间和资源消耗

## 测试报告示例

```markdown
## 技能测试报告：database-export

### 测试结果
| 测试项 | 状态 | 耗时 | 备注 |
|--------|------|------|------|
| 基本导出 | ✅ | 0.3s | CSV格式正常 |
| 大文件导出 | ✅ | 2.1s | 10万条记录 |
| 空数据导出 | ✅ | 0.1s | 返回空CSV |
| 格式错误处理 | ✅ | 0.05s | 返回错误信息 |
| 依赖检查 | ✅ | - | 依赖sqlite可用 |

### 综合评分
- 功能完整性：95%
- 错误处理：90%
- 性能：优秀
- 推荐：✅ 可发布
```

## 使用方法

### 1. 测试单个技能

```bash
# 使用命令行测试技能
lingflow run skill-testing --params '{"skill_name": "database-export"}'
```

### 2. 测试技能的特定功能

```bash
# 测试技能的特定功能
lingflow run skill-testing --params '{"skill_name": "database-export", "test_type": "performance"}'
```

### 3. 批量测试多个技能

```bash
# 批量测试多个技能
lingflow run skill-testing --params '{"skill_names": ["database-export", "notification"]}'
```

## 技能结构

```
skills/skill-testing/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
├── implementation.py # 技能实现文件
└── test_templates/   # 测试模板目录
    ├── data_skill.py
    ├── api_skill.py
    └── analysis_skill.py
```

## 最佳实践

1. **全面测试**：对每个技能进行全面的功能测试、边界测试和性能测试
2. **定期测试**：在技能更新后定期进行测试，确保功能正常
3. **自动化测试**：将测试集成到 CI/CD 流程中，实现自动化测试
4. **测试覆盖**：确保测试覆盖技能的所有主要功能和边缘情况
5. **性能监控**：定期测试技能的性能，确保其在生产环境中表现良好

## 故障排除

- **测试失败**：检查技能的实现是否正确，以及测试用例是否合理
- **性能问题**：分析技能的执行时间和资源消耗，找出性能瓶颈
- **依赖问题**：确保技能的依赖项可用且版本兼容
- **环境问题**：检查测试环境是否与生产环境一致

## 相关技能

- `skill-creator` - 用于创建和管理技能
- `verification-before-completion` - 用于验证技能的完成状态
- `systematic-debugging` - 用于调试技能的问题
- `skill-analytics` - 用于分析技能的使用情况
