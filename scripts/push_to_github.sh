#!/bin/bash
# 推送代码到 GitHub v3.3.0 的脚本

echo "========================================"
echo "LingFlow v3.3.0 推送到 GitHub"
echo "========================================"
echo ""

# 检查当前分支
CURRENT_BRANCH=$(git branch --show-current)
echo "当前分支: $CURRENT_BRANCH"

# 检查当前提交
CURRENT_COMMIT=$(git log -1 --oneline)
echo "当前提交: $CURRENT_COMMIT"

# 检查标签
echo "当前标签:"
git tag -l "v3.*"

echo ""
echo "========================================"
echo "推送方法 1: 使用个人访问令牌（推荐）"
echo "========================================"
echo ""
echo "步骤："
echo "1. 访问: https://github.com/settings/tokens"
echo "2. 点击 'Generate new token (classic)'"
echo "3. 勾选 'repo' 权限（用于代码推送）"
echo "4. 生成令牌并复制（格式类似: ghp_xxxxxxxxxxxx）"
echo "5. 运行以下命令："
echo ""
echo "   git remote set-url github https://YOUR_TOKEN@github.com/guangda88/LingFlow.git"
echo "   git push github master"
echo "   git push github v3.3.0"
echo ""

echo "========================================"
echo "推送方法 2: 配置 SSH 密钥"
echo "========================================"
echo ""
echo "步骤："
echo "1. 复制你的 SSH 公钥："
echo "   cat ~/.ssh/id_ed25519.pub"
echo ""
echo "2. 访问: https://github.com/settings/keys"
echo "3. 点击 'New SSH key'"
echo "4. 粘贴公钥并保存"
echo "5. 测试连接："
echo "   ssh -T git@github.com"
echo ""
echo "6. 推送代码："
echo "   git push github master"
echo "   git push github v3.3.0"
echo ""

echo "========================================"
echo "推送方法 3: 手动输入凭据"
echo "========================================"
echo ""
echo "运行以下命令，系统会提示输入用户名和密码："
echo "   git remote set-url github https://github.com/guangda88/LingFlow.git"
echo "   git push github master"
echo "   git push github v3.3.0"
echo ""
echo "注意：密码需要使用 GitHub 个人访问令牌，不是账户密码"
echo ""

echo "========================================"
echo "验证推送结果"
echo "========================================"
echo ""
echo "推送成功后，访问以下地址验证："
echo "  - GitHub 仓库: https://github.com/guangda88/LingFlow"
echo "  - v3.3.0 标签: https://github.com/guangda88/LingFlow/releases/tag/v3.3.0"
echo ""
