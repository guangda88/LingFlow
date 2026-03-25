# LingFlow 双仓库推送指南

## 远程仓库配置

### 当前配置

```bash
origin   http://zhinenggitea.iepose.cn/guangda/LingFlow.git (fetch/push)
github  https://github.com/guangda88/LingFlow.git (fetch/push)
```

### 设置远程仓库

```bash
# 设置 Gitea 远程仓库
git remote add origin http://zhinenggitea.iepose.cn/guangda/LingFlow.git
git remote set-url origin http://zhinenggitea.iepose.cn/guangda/LingFlow.git

# 设置 GitHub 远程仓库
git remote add github https://github.com/guangda88/LingFlow.git
git remote set-url github https://github.com/guangda88/LingFlow.git

# 查看远程仓库
git remote -v
```

---

## 推送流程

### 1. 准备工作

```bash
cd /home/ai/LingFlow

# 检查当前状态
git status
git log --oneline -3
```

### 2. 添加和提交更改

```bash
# 添加所有更改
git add -A

# 提交（使用规范的提交格式）
git commit -m "chore: release LingFlow vX.X.X

### Changes
- Change description here

### Features
- Feature description here

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

### 3. 创建版本标签

```bash
# 更新版本文件
echo "X.X.X" > VERSION

# 更新 CHANGELOG.md
# 添加新版本的变更记录

# 创建标签
git tag -a vX.X.X -m "Release LingFlow vX.X.X

Release notes here"
```

### 4. 推送到双仓库

#### 方法一：逐个推送

```bash
# 推送到 Gitea
git push origin master --tags

# 推送到 GitHub（需要代理）
git push github master --tags
```

#### 方法二：使用一键推送脚本

创建 `~/.local/bin/git-pushall`:

```bash
#!/bin/bash
# git-pushall - 同时推送到所有远程仓库

for remote in $(git remote); do
    echo "=== Pushing to $remote ==="
    git push $remote master --tags
done
```

使用：

```bash
chmod +x ~/.local/bin/git-pushall
git-pushall
```

---

## 代理配置（推送 GitHub 时需要）

### 启动 Clash 代理

```bash
cd ~/.config/clash
nohup ./clash -d . -f config.yaml > /dev/null 2>&1 &
sleep 3

# 验证代理运行
ss -tlnp | grep 7890
```

### 推送时使用代理

```bash
# 方式一：环境变量
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
git push github master --tags

# 方式二：git 配置
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
git push github master --tags

# 清除代理配置
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 停止代理

```bash
pkill -f "clash -d"
```

---

## 完整发布流程示例

```bash
#!/bin/bash
# release.sh - LingFlow 发布脚本

VERSION="X.X.X"

# 1. 更新版本文件
echo "$VERSION" > VERSION
sed -i "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" lingflow/__init__.py

# 2. 更新 CHANGELOG
# 手动编辑 CHANGELOG.md 添加新版本内容

# 3. 提交更改
git add -A
git commit -m "chore: release LingFlow v$VERSION

### Changes
- Version bump to $VERSION
- CHANGELOG update

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# 4. 创建标签
git tag -a "v$VERSION" -m "Release LingFlow v$VERSION"

# 5. 推送到 Gitea
git push origin master --tags

# 6. 启动代理并推送到 GitHub
cd ~/.config/clash
nohup ./clash -d . -f config.yaml > /dev/null 2>&1 &
sleep 3

cd - > /dev/null
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
git push github master --tags

# 清理
pkill -f "clash -d"
unset http_proxy https_proxy
```

---

## 常见问题

### Q: GitHub 推送失败 "Failed to connect"

**A**: 需要使用 Clash 代理，参见上面的代理配置章节。

### Q: 标签推送被拒绝 "already exists"

**A**: 该标签已在远程存在，可以跳过或强制更新：

```bash
# 强制更新单个标签
git push github :refs/tags/vX.X.X
git push github vX.X.X
```

### Q: 如何查看已推送的标签

```bash
# 查看本地标签
git tag -l

# 查看远程标签
git ls-remote --tags github
git ls-remote --tags origin
```

---

## 快速命令参考

```bash
# 查看远程仓库
git remote -v

# 查看状态
git status

# 查看最近提交
git log --oneline -5

# 查看标签
git tag -l

# 创建标签
git tag -a vX.X.X -m "Release vX.X.X"

# 删除本地标签
git tag -d vX.X.X

# 删除远程标签
git push github :refs/tags/vX.X.X
git push origin :refs/tags/vX.X.X
```

---

**最后更新**: 2026-03-25
**当前版本**: 3.5.0
