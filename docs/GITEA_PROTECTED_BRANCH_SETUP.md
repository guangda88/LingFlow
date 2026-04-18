# Gitea Protected Branch 配置指南

本文档说明如何为 LingFlow 项目配置 Gitea 的 Protected Branch，实现四层防护机制。

## 📋 目录

1. [Protected Branch 配置](#protected-branch-配置)
2. [Pre-receive Hooks 配置](#pre-receive-hooks-配置)
3. [CI Required Checks 配置](#ci-required-checks-配置)
4. [GPG 签名配置](#gpg-签名配置)
5. [验证配置](#验证配置)

---

## Protected Branch 配置

### 目标

保护 `master` 分支，防止：
- 直接 push（必须通过 Pull Request）
- 未通过 CI 的合并
- 缺少代码审查的合并

### 配置步骤

#### 1. 进入仓库设置

访问：`http://zhinenggitea.iepose.cn/guangda/LingFlow/settings/branches`

#### 2. 添加 Protected Branch

点击 **"Protected Branches"** → **"Add Protected Branch"**

#### 3. 配置保护规则

| 设置项 | 配置值 | 说明 |
|--------|--------|------|
| **Branch name** | `master` | 要保护的分支名 |
| **Enable Push Access** | ❌ 禁用 | 禁止直接 push |
| **Require Pull Request to merge** | ✅ 启用 | 必须通过 PR |
| **Require approvals** | ✅ 启用 | 要求审批 |
| **Required Approvals** | `1` | 至少 1 人审批 |
| **Dismiss stale reviews** | ✅ 启用 | 代码更新后失效之前的审批 |
| **Require signed commits** | ✅ 启用 | 要求 GPG 签名（可选） |
| **Block outdated branch** | ✅ 启用 | 过时代码禁止合并 |
| **Force push** | ❌ 禁用 | 禁止强制 push |

#### 4. 配置 Required Checks

在 **"Required Status Checks"** 部分，添加以下检查：

| Check Name | 说明 |
|------------|------|
| `test-required` | 所有测试必须通过 |
| `format-required` | 代码格式必须正确 |
| `type-check-required` | 类型检查必须通过 |
| `security-required` | 安全扫描必须通过 |
| `commit-message-check` | 提交信息格式必须正确 |
| `secrets-check` | 无敏感文件泄露 |

### 配置预览

```
Protected Branch: master

✓ Require Pull Request to merge
  - Required Approvals: 1
  - Dismiss stale reviews: Yes
  - Require signed commits: Yes
  - Block outdated branch: Yes

✓ Restrict who can push
  - Limit to: reviewers, admins

✓ Required Status Checks
  - test-required
  - format-required
  - type-check-required
  - security-required
  - commit-message-check
  - secrets-check

✓ Block force push
  - Enabled
```

---

## Pre-receive Hooks 配置

### 目标

在服务器端强制检查：
- 提交信息格式
- 文件大小限制（10MB）
- 敏感文件检测
- Python 语法检查

### 配置步骤

#### 1. 准备 Hook 脚本

项目已提供 hook 脚本：`.gitea/hooks/pre-receive`

#### 2. 上传到服务器

```bash
# 在服务器上执行
cd /var/lib/gitea/repositories/guangda/LingFlow.git/hooks
curl -o pre-receive https://raw.githubusercontent.com/guangda/LingFlow/master/.gitea/hooks/pre-receive
chmod +x pre-receive
chown git:git pre-receive
```

#### 3. 验证 Hook 权限

```bash
ls -la /var/lib/gitea/repositories/guangda/LingFlow.git/hooks/pre-receive
# 应显示：-rwxr-xr-x 1 git git ...
```

#### 4. 测试 Hook

尝试推送一个不合规的提交：

```bash
# 创建测试提交
git checkout -b test-hook
echo "test" > test.txt
git add test.txt
git commit -m "invalid commit message"  # 不遵循 Conventional Commits

# 尝试推送（应该被拒绝）
git push origin test-hook:master
```

如果配置正确，应该看到：
```
remote: [ERROR] Invalid commit message format:
remote: [ERROR]   Commit: abc123...
remote: [ERROR]   Message: invalid commit message
remote:
remote: Required format: (feat|fix|docs|refactor|chore|test|perf|style): description
```

---

## CI Required Checks 配置

### 目标

通过 GitHub Actions 确保代码质量：
- 所有测试通过
- 代码格式正确
- 类型检查通过
- 无安全漏洞
- 无敏感信息泄露

### 配置步骤

#### 1. 确认 CI Workflow 已创建

检查文件：`.github/workflows/pr-gate.yml`

#### 2. 在 Gitea 中启用 CI

访问：`http://zhinenggitea.iepose.cn/guangda/LingFlow/settings/actions`

确保 **"Enable Repository Actions"** 已启用。

#### 3. 配置 Required Checks

在 Protected Branch 设置中（见上方），添加以下检查：

```
✓ Required Status Checks
  - test-required
  - format-required
  - type-check-required
  - security-required
  - commit-message-check
  - secrets-check
```

#### 4. 测试 CI Checks

创建一个 PR 并观察 CI 运行：

```bash
# 创建特性分支
git checkout -b feature/test-ci
echo "# Test" > test.md
git add test.md
git commit -m "test: CI verification"
git push origin feature/test-ci
```

在 Gitea 中创建 PR，检查 CI 状态。

---

## GPG 签名配置

### 目标

确保所有提交都经过 GPG 签名，防止身份冒充。

### 配置步骤

#### 1. 生成 GPG 密钥

```bash
# 运行配置脚本
cd /home/ai/LingFlow
chmod +x .gitea/setup-gpg.sh
./.gitea/setup-gpg.sh --configure
```

脚本会：
- 生成 4096-bit RSA 密钥对
- 导出公钥
- 配置 Git 使用签名
- 测试签名功能

#### 2. 导出公钥

公钥会保存在 `/tmp/lingflow-gpg-public-key.asc`，内容类似：

```
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBGI...（公钥内容）
...Xg==
-----END PGP PUBLIC KEY BLOCK-----
```

#### 3. 上传公钥到 Gitea

1. 访问：`http://zhinenggitea.iepose.cn/user/settings/keys`
2. 点击 **"Add GPG Key"**
3. 粘贴公钥内容
4. 点击 **"Add Key"**

#### 4. 验证签名

```bash
# 检查最近的提交是否签名
git log --show-signature -1

# 验证特定提交
git verify-commit HEAD

# 查看所有未签名的提交
for commit in $(git log --format=%H origin/master..HEAD); do
    if ! git verify-commit $commit >/dev/null 2>&1; then
        echo "Unsigned: $commit"
    fi
done
```

#### 5. 在 Protected Branch 中启用签名要求

在 Protected Branch 设置中，勾选 **"Require signed commits"**。

---

## 验证配置

### 完整测试流程

#### 测试 1: 直接 push 应该被拒绝

```bash
echo "test" > direct-push.txt
git add direct-push.txt
git commit -m "test: direct push"
git push origin master
```

**预期结果**：
```
remote: Protected branch 'master' cannot be pushed to
```

#### 测试 2: 不合规的提交信息应该被拒绝

```bash
git checkout -b test-invalid-msg
echo "test" > test.txt
git add test.txt
git commit -m "invalid message"
git push origin test-invalid-msg
```

**预期结果**：
```
remote: [ERROR] Invalid commit message format
```

#### 测试 3: 未通过测试的 PR 应该被阻止

创建一个 PR，提交会失败的测试，然后尝试合并。

**预期结果**：
- PR 显示 CI 失败
- 合并按钮被禁用

#### 测试 4: 敏感文件应该被检测

```bash
git checkout -b test-secrets
echo "password='secret123'" > config.py
git add config.py
git commit -m "test: secrets"
git push origin test-secrets
```

**预期结果**：
```
remote: [ERROR] Potential secret detected in: config.py
```

#### 测试 5: 正常流程应该成功

```bash
git checkout -b feature/normal
echo "# Test" > test.md
git add test.md
git commit -m "feat: add test file"
git push origin feature/normal
```

**预期结果**：
- 提交成功
- GPG 签名正常
- 所有 CI 检查通过
- 可以合并

---

## 常见问题

### Q1: 如何临时允许某个不符合规则的提交？

**A**: 只有管理员可以绕过限制。在 Gitea 中，勾选 **"Bypass rules"** 选项即可。

### Q2: GPG 签名失败怎么办？

**A**: 检查以下几点：
```bash
# 检查 GPG 密钥是否存在
gpg --list-secret-keys

# 测试签名
echo "test" | gpg --clearsign

# 重启 GPG agent
gpgconf --kill gpg-agent
```

### Q3: CI 检查超时怎么办？

**A**: 增加超时时间，在 `.github/workflows/pr-gate.yml` 中添加：
```yaml
jobs:
  test-required:
    timeout-minutes: 30
```

### Q4: 如何更新 Pre-receive Hook？

**A**:
```bash
cd /var/lib/gitea/repositories/guangda/LingFlow.git/hooks
curl -o pre-receive https://raw.githubusercontent.com/guangda/LingFlow/master/.gitea/hooks/pre-receive
chmod +x pre-receive
```

### Q5: 如何查看 Hook 日志？

**A**: Gitea 日志位置：`/var/log/gitea/gitea.log`

---

## 参考资料

- [Gitea Protected Branches 文档](https://docs.gitea.io/en-us/protected-branches/)
- [Gitea Webhooks 文档](https://docs.gitea.io/en-us/webhooks/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [GPG 文档](https://gnupg.org/documentation/)

---

**维护者**: LingFlow Team
**最后更新**: 2026-04-13
