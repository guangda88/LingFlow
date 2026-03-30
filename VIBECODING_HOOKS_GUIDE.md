# LingFlow Hooks 系统 v2.0 - VibeCoding 渐进式部署

**版本**: 2.0.0
**更新日期**: 2026-03-29
**部署方式**: VibeCoding 渐进式部署
**核心原则**: 质量门控 + AI 辅助 + 渐进式实施

---

## 核心原则

### 1. 质量门控

确保代码质量但不阻碍快速迭代：
- **P0 检查**: 基础质量（必需，可能阻断）
- **P1 检查**: 文档规范（警告，不阻断）
- **P2 检查**: 增强功能（建议，不阻断）

### 2. AI 辅助

自动化检查，提供智能提示：
- 自动检测代码问题
- 提供修复建议
- 学习最佳实践

### 3. 渐进式实施

先基础后增强，可配置级别：
- 从低级别开始
- 根据团队适应情况提升
- 支持快速迭代模式

---

## 检查级别说明

| 级别 | 名称 | 行为 | 适用场景 |
|------|------|------|----------|
| 0 | 关闭 | 不执行检查 | 特殊情况、紧急修复 |
| 1 | 警告 | 显示警告但不阻断 | 日常开发、快速迭代 |
| 2 | 阻断 | 显示错误并阻断提交 | 关键检查、质量保障 |

---

## 默认配置

### P0 检查（基础质量 - 必需）

| 检查项 | 默认级别 | 说明 |
|--------|----------|------|
| flake8 | 2（阻断） | 代码质量检查，PEP 8 标准 |
| tests | 1（警告） | 测试状态，10秒快速测试 |

### P1 检查（文档规范 - 警告）

| 检查项 | 默认级别 | 说明 |
|--------|----------|------|
| docs | 1（警告） | 文档完整性，公共函数 docstring |
| format | 1（警告） | 代码格式，Black 格式化 |
| commit_msg | 2（阻断） | 提交消息格式规范 |

### P2 检查（增强功能 - 建议）

| 检查项 | 默认级别 | 说明 |
|--------|----------|------|
| perf | 0（关闭） | 性能基准测试 |
| multi_repo | 0（关闭） | 多仓库一致性检查 |
| complexity | 0（关闭） | 代码复杂度检查 |

---

## 使用方式

### 日常开发

```bash
# 1. 修改代码
vim lingflow/agent/executor.py

# 2. 添加到暂存区
git add lingflow/agent/executor.py

# 3. 提交（hooks 自动运行）
git commit -m "feat(agent): 优化执行器性能"
```

### 快速迭代模式

降低检查级别，加速开发：

```bash
# 快速迭代模式：降低非关键检查级别
HOOKS_FAST_ITERATION=1 git commit -m "feat(agent): 快速添加功能"
```

### 自定义配置

通过环境变量调整检查级别：

```bash
# 将文档检查设为警告级别
HOOKS_P1_DOCS=1 git commit

# 将格式检查设为阻断级别
HOOKS_P1_FORMAT=2 git commit

# 关闭复杂度检查
HOOKS_P2_COMPLEXITY=0 git commit

# 组合使用
HOOKS_P1_DOCS=1 HOOKS_P1_FORMAT=1 HOOKS_P2_COMPLEXITY=0 git commit
```

### 跳过 Hooks

不推荐，但在特殊情况下可用：

```bash
# 跳过所有 hooks
git commit --no-verify -m "message"

# 只跳过 pre-commit
git commit --no-verify -m "message"

# 只跳过 pre-push
git push --no-verify origin branch
```

---

## 提交消息格式

### 标准格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (type)

- `feat` - 新功能
- `fix` - 修复
- `docs` - 文档
- `style` - 格式
- `refactor` - 重构
- `test` - 测试
- `chore` - 构建
- `perf` - 性能
- `ci` - CI 配置

### 作用域 (scope)

- `agent` - Agent 相关
- `workflow` - 工作流相关
- `coordination` - 协调相关
- `monitoring` - 监控相关
- `core` - 核心功能
- `utils` - 工具函数

### 示例

```
feat(agent): 添加新的代码审查 Agent

- 实现 Agent 基础接口
- 添加任务队列管理
- 实现状态监控

Closes #123
```

---

## AI 辅助提示

系统会根据检查结果提供智能修复建议：

| 检查项 | AI 建议 |
|--------|---------|
| flake8 | 运行 `flake8 <files> --fix` 或手动修复 |
| format | 运行 `black <files>` 自动格式化 |
| tests | 运行 `pytest` 查看失败测试 |
| docs | 为公共函数添加 docstring |
| complexity | 拆分复杂函数，单一职责原则 |

---

## 配置文件

配置文件位置：`.githooks/config.sh`

### 修改默认配置

编辑 `.githooks/config.sh`：

```bash
# 将 P0 测试检查设为警告级别
export HOOKS_P0_TESTS=1

# 将 P2 复杂度检查设为警告级别
export HOOKS_P2_COMPLEXITY=1
```

### 添加新检查

在相应的 hook 文件中添加检查函数，使用 `quality_gate` 函数控制阻断行为。

---

## 团队协作

### 逐步提升级别

建议按以下阶段提升检查级别：

**阶段 1（适应期）**：
- P0 flake8: 2（阻断）
- P0 tests: 0（关闭）
- P1 检查: 1（警告）

**阶段 2（规范期）**：
- P0 flake8: 2（阻断）
- P0 tests: 1（警告）
- P1 检查: 1（警告）

**阶段 3（严格期）**：
- P0 flake8: 2（阻断）
- P0 tests: 2（阻断）
- P1 检查: 2（阻断）

### 代码审查

结合 Hooks 使用：

1. Hooks 自动检查基础质量
2. 人工审查架构和设计
3. 关注产品价值实现
4. 检查 AI 协作友好性

---

## 故障排查

### Hooks 未执行

```bash
# 检查配置
git config --get core.hooksPath
# 应输出: .githooks

# 如果不是，设置它
git config core.hooksPath .githooks
```

### 检查失败

```bash
# 查看详细错误
DEBUG=1 git commit

# 快速迭代模式
HOOKS_FAST_ITERATION=1 git commit
```

### 配置问题

```bash
# 验证配置
source .githooks/config.sh
show_hooks_config
```

---

## 最佳实践

### 1. 日常开发

- 使用默认配置（平衡质量和速度）
- 遵循提交消息格式规范
- 及时修复警告级别的问题

### 2. 快速迭代

- 使用 `HOOKS_FAST_ITERATION=1` 降低检查级别
- 专注于功能实现
- 迭代完成后修复警告

### 3. 发布前

- 提升所有检查级别到 2（阻断）
- 确保所有检查通过
- 运行完整测试套件

### 4. 紧急修复

- 使用 `git commit --no-verify` 跳过检查
- 修复后补充测试和文档
- 创建后续任务改进

---

## 版本历史

- **v2.0.0** (2026-03-29): VibeCoding 渐进式部署
  - 质量门控分级系统
  - AI 辅助提示
  - 快速迭代模式
  - 可配置检查级别

- **v1.2.0** (2026-03-29): 初始版本
  - 基础 Hooks 检查
  - 提交消息验证
  - 多仓库支持

---

**相关文档**:
- [VIBECODING_IMPLEMENTATION_GUIDE.md](./VIBECODING_IMPLEMENTATION_GUIDE.md)
- [LINGFLOW_DEVELOPMENT_RULES.md](./LINGFLOW_DEVELOPMENT_RULES.md)

**支持**: 通过 GitHub Issues 或 Gitea Issues 反馈
