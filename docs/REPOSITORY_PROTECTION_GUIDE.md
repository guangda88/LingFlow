# 🛡️ LingFlow 远程仓库防护措施总览

**目标**: 防止未验证代码直推 — 确保所有提交符合质量标准、安全要求、代码规范。

## 📋 四层防护体系

```
┌─────────────────────────────────────────────────────────────┐
│  第一层：Protected Branch（分支保护）                         │
│  ✅ 禁止直接 push，必须通过 Pull Request                      │
│  ✅ 要求至少 1 人审批                                         │
│  ✅ 要求所有 CI 检查通过                                      │
│  ✅ 禁止 force push                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  第二层：Pre-receive Hooks（服务器端检查）                     │
│  ✅ 提交信息格式检查（Conventional Commits）                   │
│  ✅ 文件大小限制（10MB）                                      │
│  ✅ 敏感文件检测（密钥、证书、环境变量）                       │
│  ✅ Python 语法检查                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  第三层：CI Required Checks（自动化检查）                     │
│  ✅ 测试通过（pytest）                                        │
│  ✅ 代码格式正确（black + isort）                             │
│  ✅ 类型检查通过（mypy）                                      │
│  ✅ 安全扫描通过（bandit）                                    │
│  ✅ 无敏感信息泄露                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  第四层：GPG 签名（身份验证）                                 │
│  ✅ 所有提交必须签名                                          │
│  ✅ 验证提交者身份                                            │
│  ✅ 防止身份冒充                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 配置 GPG 签名

```bash
cd /home/ai/LingFlow
./.gitea/setup-gpg.sh --configure
```

### 2. 上传公钥到 Gitea

1. 访问：`http://zhinenggitea.iepose.cn/user/settings/keys`
2. 粘贴 `/tmp/lingflow-gpg-public-key.asc` 的内容
3. 点击 **"Add Key"**

### 3. 配置 Protected Branch（需要管理员权限）

访问：`http://zhinenggitea.iepose.cn/guangda/LingFlow/settings/branches`

按 `docs/GITEA_PROTECTED_BRANCH_SETUP.md` 中的步骤配置。

### 4. 配置 Pre-receive Hook（需要服务器访问权限）

```bash
# 在服务器上执行
cd /var/lib/gitea/repositories/guangda/LingFlow.git/hooks
curl -o pre-receive https://raw.githubusercontent.com/guangda/LingFlow/master/.gitea/hooks/pre-receive
chmod +x pre-receive
chown git:git pre-receive
```

## 📝 提交规范

所有提交必须遵循 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Type（类型）

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: add user authentication` |
| `fix` | 修复 bug | `fix: resolve memory leak in scheduler` |
| `docs` | 文档更新 | `docs: update API documentation` |
| `refactor` | 代码重构 | `refactor: simplify agent selection logic` |
| `chore` | 构建/工具更新 | `chore: upgrade to pytest 8.0` |
| `test` | 测试相关 | `test: add unit tests for coordinator` |
| `perf` | 性能优化 | `perf: reduce context compression time` |
| `style` | 代码风格（不影响功能） | `style: format code with black` |
| `revert` | 回滚之前的提交 | `revert: feat(user): remove login feature` |

### 示例

```bash
# 正确
git commit -m "feat: add rate limiting to agent coordinator"
git commit -m "fix: resolve deadlock in parallel task execution"
git commit -m "docs: update security configuration guide"

# 错误
git commit -m "add feature"          # 缺少 type
git commit -m "Update README.md"   # 大写 type
git commit -m "bug fix"             # 不符合格式
```

## ✅ PR 合并检查清单

在合并 PR 之前，确保：

- [ ] 所有测试通过（✅ 绿色 checkmark）
- [ ] 代码格式正确（black + isort）
- [ ] 类型检查通过（mypy）
- [ ] 安全扫描通过（bandit）
- [ ] 提交信息格式正确
- [ ] 无敏感信息泄露
- [ ] 至少 1 人审批
- [ ] 代码是最新的（无冲突）
- [ ] 提交已签名（如果启用了 GPG）

## 🚫 禁止事项

### 1. 禁止直接 push 到 master

```bash
# ❌ 错误
git push origin master

# ✅ 正确
git checkout -b feature/my-feature
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
# 然后在 Gitea 上创建 PR
```

### 2. 禁止提交敏感信息

```python
# ❌ 错误
password = "secret123"
api_key = "sk-1234567890"
private_key = "-----BEGIN RSA PRIVATE KEY-----..."

# ✅ 正确
password = os.environ.get("DB_PASSWORD")
api_key = os.environ.get("API_KEY")
private_key = load_private_key_from_file()
```

### 3. 禁止提交大文件

```bash
# ❌ 错误（>10MB）
git add large-data.zip
git commit -m "feat: add data"
git push origin feature/data

# ✅ 正确
# 使用 LFS 或外部存储
git lfs track "*.zip"
git add large-data.zip
git commit -m "feat: add data with LFS"
```

## 🔧 故障排查

### 问题：提交被拒绝

**错误信息**：
```
remote: Protected branch 'master' cannot be pushed to
```

**解决方法**：
1. 创建特性分支
2. 在 Gitea 上创建 Pull Request
3. 等待 CI 检查通过
4. 请求代码审查
5. 合并 PR

### 问题：CI 检查失败

**错误信息**：
```
❌ Tests failed
```

**解决方法**：
1. 在本地运行测试：`pytest`
2. 修复失败的测试
3. 提交修复
4. CI 会自动重新运行

### 问题：提交信息格式错误

**错误信息**：
```
remote: [ERROR] Invalid commit message format
```

**解决方法**：
1. 修改提交信息：
   ```bash
   git commit --amend -m "feat: correct format"
   ```
2. 或者创建新的提交

### 问题：敏感文件被检测

**错误信息**：
```
remote: [ERROR] Potential secret detected in: config.py
```

**解决方法**：
1. 移除敏感信息
2. 使用环境变量或密钥管理服务
3. 如果文件已经提交，需要：
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch config.py' \
     --prune-empty --tag-name-filter cat -- --all
   ```

### 问题：GPG 签名失败

**错误信息**：
```
gpg: skipped "XXXXXX": No secret key
gpg: signing failed: No secret key
```

**解决方法**：
1. 检查 GPG 密钥：
   ```bash
   gpg --list-secret-keys
   ```
2. 如果没有密钥，运行配置脚本：
   ```bash
   ./.gitea/setup-gpg.sh --configure
   ```
3. 重启 GPG agent：
   ```bash
   gpgconf --kill gpg-agent
   ```

## 📚 相关文档

- [Gitea Protected Branch 配置指南](docs/GITEA_PROTECTED_BRANCH_SETUP.md)
- [灵族安全策略](docs/灵族安全策略.md)
- [LingFlow 安全文档](SECURITY.md)
- [灵通宪章](docs/CHARTER.md)

## 🎯 效果验证

配置完成后，以下操作应该被阻止：

1. ❌ 直接 push 到 master 分支
2. ❌ 提交信息不符合 Conventional Commits 格式
3. ❌ 提交包含敏感信息
4. ❌ 提交超过 10MB 的大文件
5. ❌ 提交 Python 语法错误的文件
6. ❌ 未通过 CI 检查的 PR
7. ❌ 未通过代码审查的 PR
8. ❌ Force push 到 protected branch

以下操作应该被允许：

1. ✅ 通过 PR 合并到 master
2. ✅ 提交信息符合规范
3. ✅ 通过所有 CI 检查
4. ✅ 至少 1 人审批
5. ✅ 提交已签名（如果启用）

## 📞 联系方式

如有问题，请联系：
- LingFlow Team: guangda@iepose.cn
- Gitea 管理员: （需要添加）

---

**最后更新**: 2026-04-13
**维护者**: LingFlow Team
