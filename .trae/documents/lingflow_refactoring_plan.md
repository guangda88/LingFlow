# LingFlow 重构计划 - 将 agent_coordinator.py 拆分为四个模块

## 项目概述

根据项目在 `http://zhinenggitea.iepose.cn/guangda/LingFlow` 的信息，LingFlow 是一个基于 Superpowers 理念的智能软件开发工作流引擎，通过技能驱动的架构实现自动化开发、测试、审查和文档生成。

## 重构目标

将现有的 `agent_coordinator.py` 文件拆分为以下四个模块：
1. **compression/** - 上下文压缩功能
2. **coordination/** - 多智能体协调功能
3. **skills/** - 技能系统
4. **workflow/** - 工作流编排功能

## 任务清单

### [x] 任务 1: 创建目录结构
- **Priority**: P0
- **Depends On**: None
- **Description**: 创建四个目标目录及其必要的子目录
- **Success Criteria**: 所有目录结构创建完成
- **Test Requirements**:
  - `programmatic` TR-1.1: 目录结构存在且正确
  - `human-judgement` TR-1.2: 目录命名符合规范
- **Notes**: 需要创建的目录：compression/、coordination/、skills/、workflow/、common/（用于共享模型）

### [x] 任务 2: 提取数据模型到 common/models.py
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**: 将 agent_coordinator.py 中的所有数据模型提取到 common/models.py 文件中
- **Success Criteria**: 所有数据模型成功移动到新文件
- **Test Requirements**:
  - `programmatic` TR-2.1: common/models.py 文件存在且包含所有数据模型
  - `programmatic` TR-2.2: 数据模型结构完整，无语法错误
- **Notes**: 需要移动的模型包括：AgentStatus、TaskPriority、AgentConfig、Task、TaskResult

### [x] 任务 3: 提取上下文压缩功能到 compression/compressor.py
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**: 将 ContextCompressor 类及其相关功能移动到 compression/compressor.py
- **Success Criteria**: ContextCompressor 类成功移动到新文件
- **Test Requirements**:
  - `programmatic` TR-3.1: compression/compressor.py 文件存在且包含 ContextCompressor 类
  - `programmatic` TR-3.2: 压缩功能正常工作
- **Notes**: 确保导入路径正确

### [x] 任务 4: 提取代理相关功能到 coordination/ 目录
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**:
  - 将 Agent 类移动到 coordination/agent.py
  - 将 AgentRegistry 类移动到 coordination/registry.py
  - 将 AgentCoordinator 类移动到 coordination/coordinator.py
- **Success Criteria**: 所有代理相关类成功移动到对应的文件
- **Test Requirements**:
  - `programmatic` TR-4.1: 三个文件存在且包含对应的类
  - `programmatic` TR-4.2: 代理功能正常工作
- **Notes**: 确保类之间的依赖关系正确

### [x] 任务 5: 提取工作流编排功能到 workflow/orchestrator.py
- **Priority**: P1
- **Depends On**: 任务 4
- **Description**: 将工作流执行相关功能移动到 workflow/orchestrator.py
- **Success Criteria**: WorkflowOrchestrator 类成功创建并实现工作流编排功能
- **Test Requirements**:
  - `programmatic` TR-5.1: workflow/orchestrator.py 文件存在且包含 WorkflowOrchestrator 类
  - `programmatic` TR-5.2: 工作流执行功能正常
- **Notes**: 从 AgentCoordinator 中提取 execute_workflow 方法

### [x] 任务 6: 创建 __init__.py 文件
- **Priority**: P2
- **Depends On**: 任务 2-5
- **Description**: 为每个模块创建 __init__.py 文件，确保模块可导入
- **Success Criteria**: 所有模块都有正确的 __init__.py 文件
- **Test Requirements**:
  - `programmatic` TR-6.1: 所有目录都有 __init__.py 文件
  - `programmatic` TR-6.2: 模块导入正常
- **Notes**: 在 __init__.py 中导出主要类

### [x] 任务 7: 更新主入口文件 agent_coordinator.py
- **Priority**: P1
- **Depends On**: 任务 2-6
- **Description**: 更新 agent_coordinator.py 作为主入口，整合所有模块
- **Success Criteria**: 主入口文件正确导入并使用所有模块
- **Test Requirements**:
  - `programmatic` TR-7.1: agent_coordinator.py 文件存在且能正常运行
  - `programmatic` TR-7.2: 所有功能正常执行
- **Notes**: 保留测试主函数，确保系统功能完整

### [x] 任务 8: 更新测试文件
- **Priority**: P1
- **Depends On**: 任务 7
- **Description**: 更新 test_comprehensive.py 和 verify_system_simple.py 的导入路径
- **Success Criteria**: 测试文件能正确导入新模块
- **Test Requirements**:
  - `programmatic` TR-8.1: 测试文件能正常运行
  - `programmatic` TR-8.2: 所有测试通过
- **Notes**: 需要更新导入语句，使用新的模块路径

### [x] 任务 9: 验证重构结果
- **Priority**: P0
- **Depends On**: 任务 8
- **Description**: 运行所有测试，验证重构后的系统是否正常工作
- **Success Criteria**: 所有测试通过，系统功能完整
- **Test Requirements**:
  - `programmatic` TR-9.1: verify_system_simple.py 测试通过
  - `programmatic` TR-9.2: test_comprehensive.py 测试通过
  - `programmatic` TR-9.3: agent_coordinator.py 运行正常
- **Notes**: 确保所有功能都能正常工作

## 验证方法

1. **目录结构验证**：使用 `ls` 命令检查目录结构
2. **代码语法验证**：使用 Python 解释器检查语法错误
3. **功能验证**：运行测试脚本验证功能
4. **集成验证**：运行主入口文件验证完整流程

## 预期成果

重构后的项目结构将更加清晰，代码组织更加合理，便于后续的维护和扩展。每个模块都有明确的职责，符合软件工程的最佳实践。

## 风险评估

1. **导入路径错误**：可能会出现模块导入错误，需要仔细检查
2. **依赖关系问题**：类之间的依赖关系可能会出现问题，需要确保正确处理
3. **测试失败**：重构可能会导致测试失败，需要及时修复

## 时间估计

| 任务 | 估计时间 |
|------|----------|
| 任务 1 | 10 分钟 |
| 任务 2 | 15 分钟 |
| 任务 3 | 10 分钟 |
| 任务 4 | 20 分钟 |
| 任务 5 | 15 分钟 |
| 任务 6 | 10 分钟 |
| 任务 7 | 15 分钟 |
| 任务 8 | 10 分钟 |
| 任务 9 | 10 分钟 |
| **总计** | **115 分钟** |
