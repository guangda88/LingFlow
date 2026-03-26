# 推送代码到 GitHub 指南

## 当前状态

✅ **已推送到 Gitea**
- 仓库：http://zhinenggitea.iepose.cn/guangda/LingFlow
- 分支：master
- 标签：v3.3.0
- 提交：080de8e Update README for v3.3.0 release

⏳ **待推送到 GitHub**
- 仓库：https://github.com/guangda88/LingFlow
- 需要：配置认证

---

## 推送方法

### 方法 1：使用个人访问令牌（推荐）

**步骤：**

1. **创建个人访问令牌**
   - 访问：https://github.com/settings/tokens
   - 点击 "Generate new token (classic)"
   - 勾选以下权限：
     - `repo` - 完整仓库访问权限
     - `workflow` - 工作流权限（可选）
   - 点击 "Generate token"
   - 复制生成的令牌（格式：`ghp_xxxxxxxxxxxx`）

2. **使用令牌推送**
   ```bash
   # 使用令牌替换 URL 中的 YOUR_TOKEN
   git remote set-url github https://ghp_xxxxxxxxxxxx@github.com/guangda88/LingFlow.git

   # 推送 master 分支
   git push github master

   # 推送 v3.3.0 标签
   git push github v3.3.0
   ```

### 方法 2：配置 SSH 密钥

**步骤：**

1. **查看现有 SSH 密钥**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
   输出类似：`ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINPUwF/2gx9XJUea9PKZlas0EBIe2+CSKvzAOPA646fV guangda@zhinenggitea.iepose.cn`

2. **添加 SSH 密钥到 GitHub**
   - 访问：https://github.com/settings/keys
   - 点击 "New SSH key"
   - Title: 输入任意名称（如：`LingFlow Server`）
   - Key: 粘贴步骤1中的公钥内容
   - 点击 "Add SSH key"

3. **测试 SSH 连接**
   ```bash
   ssh -T git@github.com
   ```
   成功会显示：`Hi guangda88! You've successfully authenticated...`

4. **推送代码**
   ```bash
   git push github master
   git push github v3.3.0
   ```

### 方法 3：使用凭据管理器

**步骤：**

```bash
# 1. 设置 HTTPS URL
git remote set-url github https://github.com/guangda88/LingFlow.git

# 2. 推送（会提示输入用户名和密码）
git push github master
git push github v3.3.0
```

**注意：**
- 用户名：`guangda88`
- 密码：**使用个人访问令牌**，不是账户密码

---

## 验证推送结果

推送成功后，访问以下地址验证：

1. **GitHub 主页**
   https://github.com/guangda88/LingFlow

2. **v3.3.0 发布标签**
   https://github.com/guangda88/LingFlow/releases/tag/v3.3.0

3. **查看提交历史**
   https://github.com/guangda88/LingFlow/commits/master

---

## 快速推送脚本

使用提供的脚本快速推送：

```bash
bash push_to_github.sh
```

---

## 常见问题

### Q: 提示 "Permission denied (publickey)"
**A:** SSH 密钥未添加到 GitHub，请参考方法2配置。

### Q: 提示 "Authentication failed"
**A:** 令牌无效或已过期，请重新生成个人访问令牌。

### Q: 推送超时
**A:** 网络问题，可以尝试：
   ```bash
   git config --global http.postBuffer 524288000
   git push github master
   ```

---

## 当前提交信息

```
080de8e Update README for v3.3.0 release
839311f Merge feature/self-optimization into master for v3.3.0 release
af47526 Update test files for v3.3.0 compatibility
```

**包含的主要更新：**
- 实现真实工作流执行逻辑
- 统一日志系统
- 性能监控模块
- LRU 缓存系统
- 宪法级别安全框架
- 完整的文档和用户指南
- 更新的 README 和项目说明
