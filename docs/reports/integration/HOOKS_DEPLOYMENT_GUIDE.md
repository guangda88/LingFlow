# lingflow Hooks 系统 v1.2.0 部署指南

**文档版本**: 1.2.0
**创建日期**: 2026-03-29
**适用**: lingflow 多智能体系统
**状态**: 已部署

---

## 目录

1. [系统概述](#1-系统概述)
2. [部署步骤](#2-部署步骤)
3. [Hooks 说明](#3-hooks-说明)
4. [测试验证](#4-测试验证)
5. [使用指南](#5-使用指南)
6. [故障排查](#6-故障排查)
7. [维护说明](#7-维护说明)

---

## 1. 系统概述

### 1.1 Hooks 系统 v1.2.0

lingflow Hooks 系统 v1.2.0 是一套完整的 Git Hooks 自动化检查系统，旨在：

- **保证代码质量**: 自动检查代码格式、风格、类型注解
- **规范提交消息**: 强制使用规范的提交消息格式
- **确保多仓库一致性**: 检查 GitHub 和 Gitea 仓库的一致性
- **验证测试状态**: 推送前确保测试通过

### 1.2 系统架构

```
.githooks/
├── pre-commit    # 提交前检查
├── commit-msg    # 提交消息验证
└── pre-push      # 推送前检查
```

### 1.3 技术特性

- **零依赖**: 仅使用 Bash 和常见工具（black, flake8, mypy, pytest）
- **可配置**: 通过环境变量控制行为
- **可扩展**: 模块化设计，易于添加新检查
- **多仓库支持**: 同时支持 GitHub 和 Gitea

---

## 2. 部署步骤

### 2.1 前置要求

确保已安装以下工具：

```bash
# Python 代码检查
pip install black flake8 mypy isort pytest

# 确认安装
black --version
flake8 --version
mypy --version
pytest --version
```

### 2.2 自动部署（推荐）

在 lingflow 项目根目录执行：

```bash
# 配置 Git 使用项目本地 hooks
git config core.hooksPath .githooks

# 验证配置
git config --get core.hooksPath
# 输出应为: .githooks
```

### 2.3 手动部署

如果想使用系统级 hooks：

```bash
# 复制 hooks 到 .git/hooks
cp .githooks/pre-commit .git/hooks/
cp .githooks/commit-msg .git/hooks/
cp .githooks/pre-push .git/hooks/

# 设置可执行权限
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-push
```

### 2.4 全局部署

如果想让所有项目使用这些 hooks：

```bash
# 创建全局 hooks 目录
mkdir -p ~/.git-templates/hooks

# 复制 hooks
cp .githooks/* ~/.git-templates/hooks/

# 配置 Git 使用全局模板
git config --global init.templatedir '~/.git-templates/hooks'

# 对现有项目重新初始化
git init
```

---

## 3. Hooks 说明

### 3.1 Pre-commit Hook

**触发时机**: `git commit` 执行前，暂存文件后

**检查项目**:

1. **Python 代码格式**
   - 使用 black 检查代码格式
   - 不通过时提供修复命令

2. **Python 代码质量**
   - 使用 flake8 检查代码质量
   - 最大行长度: 88 字符
   - 忽略: E203, W503

3. **类型注解检查**
   - 检查公共函数是否有类型注解
   - 警告缺失的类型注解

4. **文档字符串检查**
   - 检查公共函数是否有 docstring
   - 警告缺失的文档

5. **测试文件检查**
   - 检查新代码是否有对应测试
   - 警告缺失的测试文件

6. **敏感信息检查**
   - 检查硬编码的密码、密钥
   - 检查 IP 地址
   - 阻止包含敏感信息的提交

7. **代码复杂度检查**
   - 检查函数行数（> 50 行警告）
   - 建议拆分复杂函数

8. **导入顺序检查**
   - 使用 isort 检查导入顺序
   - 遵循 Black 配置

**输出示例**:

```
=== lingflow Pre-commit Hook v1.2.0 ===

[INFO] 检查的文件:
  lingflow/agent/executor.py
  tests/test_executor.py

=== 检查 Python 代码格式 ===
[PASS] 代码格式检查通过

=== 检查 Python 代码质量 ===
[PASS] 代码质量检查通过

=== 检查类型注解 ===
[PASS] 类型注解检查通过

=== 检查文档字符串 ===
[PASS] 文档字符串检查通过

=== 检查测试覆盖 ===
[PASS] 测试文件检查通过

=== 检查敏感信息 ===
[PASS] 敏感信息检查通过

=== 检查代码复杂度 ===
[PASS] 代码复杂度检查通过

=== 检查导入顺序 ===
[PASS] 导入顺序检查通过

=== 检查总结 ===
  通过: 8
  警告: 0
  失败: 0

[PASS] Pre-commit 检查通过
```

### 3.2 Commit-msg Hook

**触发时机**: `git commit` 执行时，提交消息写入后

**检查项目**:

1. **提交消息格式**
   - 必须符合: `<type>(<scope>): <subject>`
   - 类型: feat, fix, docs, style, refactor, test, chore, perf, ci
   - 作用域: agent, workflow, coordination, monitoring, core, utils

2. **提交消息长度**
   - 第一行不超过 72 字符
   - 建议添加详细描述

3. **关联信息检查**
   - fix/feat 提交建议关联 Issue

4. **禁止模式检查**
   - 禁止无意义的提交消息
   - 警告临时、hack 等词汇

5. **多智能体系统特定规则**
   - Agent 相关提交建议说明 Agent 类型

**输出示例**:

```
=== lingflow Commit-msg Hook v1.2.0 ===

[INFO] 检查提交消息:
  feat(agent): 添加新的代码审查 Agent

[INFO] 提交消息格式正确
[INFO] 提交消息长度符合要求
[INFO] 建议关联 Issue: Closes #123

[PASS] 提交消息检查通过
```

### 3.3 Pre-push Hook

**触发时机**: `git push` 执行前

**检查项目**:

1. **远程仓库检查**
   - 验证 GitHub 和 Gitea 远程仓库配置
   - 确保至少有一个远程仓库

2. **分支一致性检查**
   - 检查本地和远程分支的提交差异
   - 警告不一致的分支

3. **版本号一致性**
   - 检查多个版本文件的一致性
   - 确保 pyproject.toml, setup.py 版本同步

4. **测试状态检查**
   - 运行快速测试（30 秒超时）
   - 可通过 LINGFLOW_SKIP_TESTS=1 跳过

5. **待推送提交检查**
   - 显示待推送的提交数量
   - 显示最近的提交历史

6. **大文件检查**
   - 警告超过 1MB 的大文件
   - 提示可能影响推送速度

7. **敏感文件检查**
   - 检查 .env, .key, .pem 等敏感文件
   - 阻止推送包含敏感文件的提交

**输出示例**:

```
=== lingflow Pre-push Hook v1.2.0 ===

[INFO] 推送目标: origin (http://zhinenggitea.iepose.cn/guangda/lingflow.git)

=== 检查远程仓库配置 ===
[INFO] Gitea: http://zhinenggitea.iepose.cn/guangda/lingflow.git
[PASS] 远程仓库检查通过

=== 检查分支一致性 ===
[INFO] 当前分支: feature/mvp-textbook-7
[PASS] 分支一致性检查通过

=== 检查版本号一致性 ===
[INFO] pyproject.toml: 0.1.0
[PASS] 版本号检查通过

=== 检查测试状态 ===
[INFO] 运行快速测试检查...
[PASS] 快速测试通过

=== 检查待推送的提交 ===
[INFO] origin: 有 3 个提交待推送

    最近的提交:
    a1b2c3d feat(agent): 添加新的代码审查 Agent
    d4e5f6g fix(workflow): 修复并行执行死锁问题
    h7i8j9k docs: 更新 README

[PASS] 待推送提交检查完成

=== 检查总结 ===
  通过: 5
  警告: 0
  失败: 0

[PASS] Pre-push 检查通过
[INFO] 准备推送到: origin
```

---

## 4. 测试验证

### 4.1 验证 Hooks 安装

```bash
# 检查 hooks 是否配置
ls -la .git/hooks/ | grep -E "(pre-commit|commit-msg|pre-push)"

# 或检查配置
git config --get core.hooksPath
```

### 4.2 测试 Pre-commit Hook

```bash
# 创建一个测试文件
cat > test_hook.py << 'EOF'
def bad_function( ):
    x=1+2
    return x
EOF

# 添加到暂存区
git add test_hook.py

# 尝试提交（应该被阻止）
git commit -m "test: test pre-commit hook"

# 清理
git reset HEAD test_hook.py
rm test_hook.py
```

### 4.3 测试 Commit-msg Hook

```bash
# 尝试使用不规范的提交消息
git commit -m "bad commit message"
# 应该被阻止

# 使用规范的提交消息
git commit -m "feat(agent): 添加测试 Agent"
# 应该通过
```

### 4.4 测试 Pre-push Hook

```bash
# 设置测试环境
export LINGFLOW_SKIP_TESTS=1

# 创建测试提交
git commit --allow-empty -m "feat(test): 测试 pre-push hook"

# 尝试推送
git push --dry-run origin HEAD
# 应该显示检查通过
```

---

## 5. 使用指南

### 5.1 日常使用

```bash
# 1. 修改代码
vim lingflow/agent/executor.py

# 2. 格式化代码（推荐在提交前执行）
black lingflow/

# 3. 添加到暂存区
git add lingflow/agent/executor.py

# 4. 提交（hooks 自动运行）
git commit -m "feat(agent): 优化执行器性能"

# 5. 推送（hooks 自动运行）
git push origin feature/new-agent
```

### 5.2 跳过 Hooks

不推荐，但在特殊情况下可以使用：

```bash
# 跳过 pre-commit hook
git commit --no-verify -m "message"

# 跳过 commit-msg hook
git commit --no-verify -m "any message"

# 跳过 pre-push hook
git push --no-verify origin branch

# 只跳过测试检查
LINGFLOW_SKIP_TESTS=1 git push origin branch
```

### 5.3 调试 Hooks

启用调试输出：

```bash
# 为 hooks 启用调试
export DEBUG=1

# 然后执行 git 操作
git commit -m "feat(agent): 添加测试 Agent"
```

---

## 6. 故障排查

### 6.1 Hooks 未执行

**问题**: 修改了代码但 hooks 似乎没有运行

**解决方案**:

```bash
# 检查 hooks 配置
git config --get core.hooksPath

# 如果不是 .githooks，设置它
git config core.hooksPath .githooks

# 检查 hooks 权限
ls -la .githooks/
# 应该都是 -rwxrwxrwx

# 如果没有执行权限
chmod +x .githooks/*
```

### 6.2 Pre-commit Hook 失败

**问题**: pre-commit hook 检查失败

**解决方案**:

```bash
# 查看错误信息（会显示在终端）

# 如果是格式问题
black <files>

# 如果是代码质量问题
flake8 <files>

# 修复后重新提交
git add <files>
git commit -m "message"
```

### 6.3 Commit-msg Hook 失败

**问题**: commit-msg hook 检查失败

**解决方案**:

```bash
# 使用 --amend 修改提交消息
git commit --amend -m "feat(agent): 正确的消息格式"

# 或者取消提交重新开始
git reset HEAD~1
git commit -m "feat(agent): 正确的消息格式"
```

### 6.4 Pre-push Hook 失败

**问题**: pre-push hook 检查失败

**解决方案**:

```bash
# 如果测试失败
pytest tests/

# 如果有敏感文件
git rm --cached <sensitive-files>
echo "*.key" >> .gitignore
git add .gitignore
git commit -m "chore: 添加敏感文件到 gitignore"

# 如果要跳过测试
LINGFLOW_SKIP_TESTS=1 git push
```

---

## 7. 维护说明

### 7.1 更新 Hooks

当需要更新 hooks 时：

```bash
# 1. 编辑 .githooks/ 中的文件
vim .githooks/pre-commit

# 2. 确保 hooks 可执行
chmod +x .githooks/*

# 3. 提交到仓库
git add .githooks/
git commit -m "chore: 更新 pre-commit hook"

# 4. 推送到远程
git push origin main
```

### 7.2 添加新检查

在相应的 hook 文件中添加检查函数：

```bash
# 在 pre-commit 中添加新检查
check_something_new() {
    log_section "检查新项目"

    # 实现检查逻辑
    if [ some_condition ]; then
        log_success "检查通过"
        return 0
    else
        log_error "检查失败"
        return 1
    fi
}

# 在 main 函数中调用
main() {
    # ... 其他检查
    check_something_new || true
    # ...
}
```

### 7.3 配置环境变量

支持的环境变量：

```bash
# 跳过测试检查
export LINGFLOW_SKIP_TESTS=1

# 启用调试输出
export DEBUG=1

# 自定义远程仓库名称
export GITHUB_REMOTE=github
export GITEA_REMOTE=origin
```

---

## 附录

### A. Hooks 版本历史

- **v1.2.0** (2026-03-29): lingflow 专用版本
  - 添加多智能体系统特定检查
  - 支持多仓库一致性检查
  - 优化性能和错误消息

### B. 相关文档

- [LINGFLOW_DEVELOPMENT_RULES.md](./LINGFLOW_DEVELOPMENT_RULES.md): lingflow 开发规则
- [DEVELOPMENT_RULES_V4.0.md](../zhineng-knowledge-system/DEVELOPMENT_RULES_V4.0.md): 基础开发规则

### C. 常见问题

**Q: Hooks 会降低提交速度吗？**
A: 影响很小。大多数检查在毫秒级完成，只有测试检查可能需要几秒。

**Q: 可以在 CI/CD 中使用吗？**
A: 可以。这些 hooks 的检查逻辑可以在 CI/CD 流水线中复用。

**Q: 如何在团队中推广？**
A: 将 hooks 提交到仓库，并在开发文档中说明配置方法。

---

**部署状态**: ✅ 已部署
**测试状态**: ✅ 已测试
**文档状态**: ✅ 完整

**维护者**: lingflow 开发团队
**联系方式**: 通过 GitHub Issues 或 Gitea Issues 联系
