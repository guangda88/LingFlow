# Trust Guardrail Skill

## 概述 (Overview)

Trust Guardrail 在 AI 声称完成任务时自动验证其输出，确保可追溯、可质疑、可信。

## 目的 (Purpose)

解决 "AI 声称完成但未验证" 的问题（如之前 `energy_pct` 数据幻觉事件）。

## 核心原则 (Core Principles)

### 数据真实性原则 (Data Truth Principle)

任何 UI 字段必须回答：
1. **数据来源？** - Where does data come from?
2. **谁更新？** - Who updates it?

### 反模式：数据幻觉 (Anti-pattern: Data Hallucination)

- 字段被定义、存储、显示，但**从未被更新**
- 例如：`energy_pct` 在 lingyi 中只显示为 0，无任何更新逻辑

## 检查清单 (Checklist)

在声称完成任何任务前，必须：

### 1. 四层验证 (Four-Layer Verification)

- [ ] **语法层 (SYNTAX)**: 能运行吗？(文件存在、命令执行成功)
- [ ] **语义层 (SEMANTIC)**: 做了说的事吗？(文件包含预期内容、输出匹配)
- [ ] **意图层 (INTENT)**: 解决了真正的问题吗？(符合用户需求)
- [ ] **边界层 (BOUNDARY)**: 有没有遗漏约束？(边界条件、异常处理)

### 2. 质疑者自审 (Skeptic Self-Audit)

提出并回答：
- [ ] "I claimed:" - 我声称完成了什么？
- [ ] "Target:" - 目标是什么？
- [ ] "Expected:" - 期望什么结果？
- [ ] "Verification passed?" - 验证通过了吗？

### 3. 证据收集 (Evidence Collection)

- [ ] 执行了验证步骤吗？
- [ ] 验证结果是什么？
- [ ] 如果用户问 "did you verify"，能回答什么？

## 使用方式 (Usage)

### 方式 1: 手动验证

```python
from lingflow.trust import (
    TaskClaim,
    VerificationPipeline,
    FileContentVerifier,
    CommandOutputVerifier,
    Skeptic
)

# 创建声称
claim = TaskClaim(
    action="添加功能 X 到文件 Y",
    target="/path/to/file.py",
    expected="function_x"
)

# 创建验证管道
pipeline = VerificationPipeline()
pipeline.add_verifier(FileContentVerifier())

# 执行验证
result = pipeline.execute(claim)

# 质疑者审计
skeptic = Skeptic()
skeptic.verification_results = [result]
report = skeptic.audit(claim)

# 检查置信度
if report.confidence < 0.8:
    print(f"验证失败: {report.challenges}")
else:
    print(f"验证通过: {report.summary}")
```

### 方式 2: 自动验证（Skill 集成）

将验证作为技能执行的标准步骤：

1. **执行任务**
2. **自动验证**
3. **质疑者审计**
4. **报告结果**

## 验证器类型 (Verifier Types)

| 验证器 | 用途 | 层级 |
|--------|------|------|
| `FileContentVerifier` | 检查文件是否包含预期内容 | SEMANTIC |
| `CommandOutputVerifier` | 检查命令输出是否包含预期内容 | SYNTAX |
| `DirectoryStructureVerifier` | 检查目录结构和文件 | SEMANTIC |
| `GitDiffVerifier` | 检查 git diff 是否包含预期更改 | SEMANTIC |

## 示例场景 (Example Scenarios)

### 场景 1: 编辑代码文件

**Claim:** "添加 `calculate_energy()` 函数到 `energy.py`"

**Verification:**
```python
claim = TaskClaim(
    action="添加函数",
    target="energy.py",
    expected="def calculate_energy()"
)

pipeline = VerificationPipeline()
pipeline.add_verifier(FileContentVerifier())
result = pipeline.execute(claim)
```

### 场景 2: 运行测试

**Claim:** "运行单元测试并通过"

**Verification:**
```python
claim = TaskClaim(
    action="运行测试",
    target="pytest",
    expected="PASSED"
)

pipeline = VerificationPipeline()
pipeline.add_verifier(CommandOutputVerifier())
result = pipeline.execute(claim, actual_result=test_output)
```

### 场景 3: 创建目录结构

**Claim:** "创建项目目录结构"

**Verification:**
```python
claim = TaskClaim(
    action="创建目录结构",
    target="/home/ai/myproject",
    expected="src,tests,docs"
)

pipeline = VerificationPipeline()
pipeline.add_verifier(DirectoryStructureVerifier())
result = pipeline.execute(claim)
```

## 门禁 (Gates)

此技能适用于所有声称"完成"的任务，特别是：

- 代码编辑
- 文件创建
- 功能实现
- 测试执行
- 部署操作

## 失败处理 (Failure Handling)

如果验证失败：

1. **不要声称完成** - 返回详细错误信息
2. **提供修复建议** - 基于验证结果
3. **记录审计日志** - 保存验证失败证据

## 与 lingyi 的关联 (Connection to lingyi)

此技能直接响应 lingyi 中的 "数据幻觉" 问题：

- **问题**: `energy_pct` 字段存在但从不更新
- **原因**: 无人问 "谁更新它？"
- **解决**: 所有 UI 字段必须回答数据来源和更新者

## 相关资源 (Related Resources)

- `lingflow/trust/verifier.py` - 验证框架核心代码
- `tests/test_trust.py` - 测试套件（10 个测试，全部通过）
- `AGENTS.md` - 包含数据真实性原则
