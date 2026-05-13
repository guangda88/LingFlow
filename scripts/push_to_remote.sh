#!/bin/bash

# lingflow v3.1.0 推送脚本
# 用于将代码和 Tags 推送到远程仓库

echo "============================================================"
echo "  lingflow v3.1.0 推送脚本"
echo "============================================================"
echo ""

# 切换到项目目录
cd /home/ai/lingzhi/lingflow

# 显示当前 Git 状态
echo "1. 当前 Git 状态:"
echo "   ---------------------------------------------------"
git status
echo ""

# 显示当前分支
echo "2. 当前分支:"
echo "   ---------------------------------------------------"
git branch
echo ""

# 显示最新提交
echo "3. 最新提交:"
echo "   ---------------------------------------------------"
git log --oneline -1
echo ""

# 显示 Tags
echo "4. 本地 Tags:"
echo "   ---------------------------------------------------"
git tag -l
echo ""

# 显示远程仓库配置
echo "5. 远程仓库配置:"
echo "   ---------------------------------------------------"
git remote -v
echo ""

# 推送代码
echo "============================================================"
echo "  步骤 1: 推送代码到远程仓库"
echo "============================================================"
echo ""

read -p "是否要推送代码到远程仓库? (y/n): " push_code

if [ "$push_code" = "y" ] || [ "$push_code" = "Y" ]; then
    echo "正在推送代码..."
    git push -u origin master

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 代码推送成功！"
    else
        echo ""
        echo "❌ 代码推送失败，请检查："
        echo "   - 网络连接"
        echo "   - 远程仓库 URL"
        echo "   - 认证信息"
    fi
else
    echo "跳过代码推送"
fi

echo ""

# 推送 Tags
echo "============================================================"
echo "  步骤 2: 推送 Tags 到远程仓库"
echo "============================================================"
echo ""

read -p "是否要推送 Tags 到远程仓库? (y/n): " push_tags

if [ "$push_tags" = "y" ] || [ "$push_tags" = "Y" ]; then
    echo "正在推送 Tags..."
    git push origin v3.1.0

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Tags 推送成功！"
    else
        echo ""
        echo "❌ Tags 推送失败，请检查："
        echo "   - 网络连接"
        echo "   - 远程仓库 URL"
        echo "   - 认证信息"
    fi
else
    echo "跳过 Tags 推送"
fi

echo ""

# 验证推送
echo "============================================================"
echo "  步骤 3: 验证推送"
echo "============================================================"
echo ""

echo "远程分支:"
git branch -r
echo ""

echo "远程 Tags:"
git ls-remote --tags origin 2>/dev/null | tail -5
echo ""

# 最终总结
echo "============================================================"
echo "  推送完成"
echo "============================================================"
echo ""

echo "下一步:"
echo "  1. 访问远程仓库验证: http://zhinenggitea.iepose.cn/guangda/lingflow"
echo "  2. 检查 Tag v3.1.0 是否已创建"
echo "  3. 查看 GIT_PUSH_REPORT.md 了解详细信息"
echo ""

echo "版本: v3.1.0"
echo "状态: ✅ 生产就绪"
echo ""
