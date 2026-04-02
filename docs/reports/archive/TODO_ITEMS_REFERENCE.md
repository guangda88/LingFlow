# LingFlow TODO 项目快速参考

最后更新: 2026-03-31

## 实际技术债务统计

- **总计**: 12 个 TODO
- **需实现**: 5 个（42%）
- **配置注释**: 6 个（50%）
- **文档**: 1 个（8%）

---

## 需要实现的 TODO（5 个）

### 🔴 P1 - 高优先级（2 个）

#### 1. DevTools MCP 调用实现
**文件**: `lingflow/testing/e2e/devtools_client.py:152`

**当前代码**:
```python
# TODO: 实现 MCP 调用
# 目前返回模拟结果
return MCPResult(
    success=True,
    data={"tool": tool, "args": args}
)
```

**功能描述**:
- 实现 Chrome DevTools MCP 协议调用
- 当前只返回模拟数据
- 影响 E2E 测试功能

**建议方案**:
1. 使用 MCP SDK 实现完整的协议调用
2. 或考虑使用 Playwright/Selenium 替代
3. 评估是否真的需要完整的 DevTools 集成

**预估工作量**: 2-3 天（决策）+ 3-5 天（实现）

**GitHub Issue**: 建议创建 Issue #2

---

#### 2. 自动应用逻辑实现
**文件**: `lingflow/cli.py:736`

**当前代码**:
```python
# TODO: 实现自动应用逻辑
click.echo(f"⚠️  自动应用功能开发中")
```

**功能描述**:
- 实现 `lingflow learn apply` 命令
- 自动应用学习到的改进建议
- Phase 5 AI 学习系统的核心功能

**需要考虑**:
- 应用策略（自动 vs 半自动）
- 回滚机制
- 变更验证
- 用户确认流程

**预估工作量**: 5-7 天

**GitHub Issue**: 建议创建 Issue #1

---

### 🟡 P2 - 中优先级（1 个）

#### 3. E2E 测试框架集成
**文件**: `lingflow/cli.py:982`

**当前代码**:
```python
# TODO: 集成E2E测试框架
click.echo(f"⚠️  E2E测试功能开发中")
```

**功能描述**:
- 实现 `lingflow test e2e` 命令
- 集成端到端测试框架
- 支持场景化测试

**依赖**:
- 依赖 TODO #1（DevTools MCP）的完成

**建议方案**:
1. 等待 DevTools MCP 实现
2. 或使用 Playwright/Selenium 作为替代
3. 设计测试场景和报告格式

**预估工作量**: 3-5 天

**GitHub Issue**: 建议创建 Issue #3

---

### 🟢 P3 - 低优先级（2 个）

#### 4. 详细复杂度分析
**文件**: `lingflow/cli.py:896`

**当前代码**:
```python
# TODO: 实现详细的复杂度分析
```

**功能描述**:
- 增强 `lingflow analyze complexity` 命令
- 提供函数级复杂度分析
- 识别高复杂度热点

**当前状态**:
- 基础统计已实现
- 需要添加详细分析

**预估工作量**: 2-3 天

**GitHub Issue**: 建议创建 Issue #5

---

#### 5. 代码重复检测
**文件**: `lingflow/cli.py:916`

**当前代码**:
```python
# TODO: 实现代码重复检测
click.echo(f"\n⚠️  代码重复检测功能开发中")
```

**功能描述**:
- 实现 `lingflow analyze duplication` 命令
- 检测代码重复
- 生成重复报告

**建议方案**:
1. 使用 Pylint 的重复检测
2. 或实现基于 Token 的检测算法
3. 集成到代码质量报告

**预估工作量**: 2-3 天

**GitHub Issue**: 建议创建 Issue #6

---

## 配置注释 TODO（6 个）- 不需要实现

这些是配置文件中的说明性文本，不是待办事项：

### self_optimizer/config.py
- **行 44**: `"todo_count_above": 20,  # TODO注释超过20个`
- **行 46**: `"hack_comments_above": 3,  # HACK标记超过3个`

### self_optimizer/trigger.py
- **行 48**: `- todo_count: TODO数量`
- **行 312**: `# TODO数量`
- **行 319**: `reason=f"TODO 注释数量 ({todo_count}) 超过阈值 ({threshold})"`
- **行 326**: `# HACK标记`
- **行 333**: `reason=f"HACK 标记数量 ({hack_count}) 超过阈值 ({threshold})"`

**说明**: 这些是变量名和注释文本，描述技术债务检测器的阈值含义，不需要清理。

---

## 已清理的 TODO（1 个）

### ✅ 报告模板占位符（已删除）
**文件**: `lingflow/cli.py:1072`

**原内容**:
```python
## 💡 建议

TODO: 添加改进建议
```

**操作**: 删除了报告模板中的空建议部分

**清理时间**: 2026-03-31

---

## 优先级矩阵

```
高影响 │  ┌─────────┐  ┌─────────┐
      │  │  #2     │  │  #1     │
      │  │  MCP    │  │  自动   │
      │  │  调用   │  │  应用   │
      ├─────────────┼─────────────┤
低影响 │  └─────────┘  └─────────┘
      │  ┌─────────┐  ┌─────────┐
      │  │  #3     │  │  #5, #6 │
      │  │  E2E    │  │  分析   │
      │  │  测试   │  │  增强   │
      └─────────────┴─────────────┘
        低紧急        高紧急
```

---

## 实施路线图

### 第一阶段：核心功能（2 周）
```
Week 1-2:
├── Issue #2: 决策并实现 MCP 或替代方案
│   ├── 评估技术方案（2-3 天）
│   └── 实现选定方案（3-5 天）
│
└── Issue #1: 实现自动应用逻辑
    ├── 设计应用策略（1-2 天）
    ├── 实现核心逻辑（3-4 天）
    └── 测试和验证（1-2 天）
```

### 第二阶段：测试能力（1 周）
```
Week 3:
└── Issue #3: 集成 E2E 测试框架
    ├── 设计测试场景（1 天）
    ├── 实现测试运行器（2-3 天）
    └── 集成到 CLI（1 天）
```

### 第三阶段：功能增强（持续）
```
Week 4+:
├── Issue #5: 增强复杂度分析（2-3 天）
└── Issue #6: 实现重复检测（2-3 天）
```

---

## TODO 标记规范建议

### 格式
```python
# TODO: [Issue-#] 简短描述 - 附加信息（可选）

# 示例:
# TODO: [Issue-1] 实现自动应用逻辑 - 需要回滚机制
# TODO: [Issue-2] 实现 MCP 调用 - 使用官方 SDK
```

### 规则
1. **必须关联 Issue**: 每个 TODO 应该有对应的 GitHub Issue
2. **描述清晰**: 简洁说明需要做什么
3. **必要时附加信息**: 如依赖、注意事项等
4. **完成后删除**: 实现后立即删除 TODO 标记
5. **代码审查检查**: PR 审查时检查 TODO 增减

---

## 快速命令参考

### 扫描 TODO
```bash
# 扫描所有 TODO
grep -rn "TODO" lingflow/ --include="*.py"

# 统计 TODO 数量
grep -rn "TODO" lingflow/ --include="*.py" | wc -l

# 按文件分组
grep -rn "TODO" lingflow/ --include="*.py" | cut -d: -f1 | sort | uniq -c
```

### 验证清理
```bash
# 检查是否还有 FIXME 或 HACK
grep -rn "FIXME\|HACK" lingflow/ --include="*.py"

# 应该返回空结果
```

---

## 相关文档

- 📊 [详细分析报告](./TECHNICAL_DEBT_REPORT.md)
- 📋 [清理总结](./TECHNICAL_DEBT_CLEANUP_SUMMARY.md)
- 🔧 [开发规范](./docs/reports/DEVELOPMENT_RULES.md)

---

## 更新日志

### 2026-03-31
- ✅ 删除报告模板占位符 TODO
- 📊 完成全面技术债务扫描
- 📋 生成分析报告和清理计划
- 🎯 建立 GitHub Issues 跟踪建议

---

**注意**: 审计报告中提到的 1,919 个 TODO 是不准确的。实际只有 13 个 TODO，其中 12 个在本次清理后保留（5 个需实现，6 个是配置注释，1 个已清理）。
