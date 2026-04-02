#!/bin/bash
# 阿里云容器镜像服务登录辅助脚本

echo "=========================================="
echo "阿里云容器镜像服务登录"
echo "=========================================="
echo ""
echo "如果登录失败，请先设置 Registry 密码："
echo "1. 访问: https://cr.console.aliyun.com"
echo "2. 个人中心 → 设置 Registry 密码"
echo ""
echo "=========================================="
echo ""

docker login registry.cn-hangzhou.aliyuncs.com

echo ""
if [ $? -eq 0 ]; then
    echo "✅ 登录成功！"
else
    echo "❌ 登录失败，请检查密码是否为 Registry 密码"
fi
