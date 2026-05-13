#!/bin/bash
# Docker 代理配置脚本 - lingflow
# 用于网络不稳定时推送 Docker 镜像

echo "🌐 Docker 代理配置助手"
echo "======================="
echo ""

# 检测可能的代理
echo "🔍 检测系统代理..."
echo ""

# 常见的代理端口
COMMON_PORTS=(
    "7890"   # Clash 默认
    "1080"   # SOCKS5
    "1087"   # Clash HTTP
    "10808"  # Clash Mix
    "7891"   # Clash 备用
    "10809"  # Clash Mix 备用
    "8888"   # 常见 HTTP
    "8118"   # 常见 HTTP
)

found_proxy=false

for port in "${COMMON_PORTS[@]}"; do
    if timeout 1 curl -x http://127.0.0.1:$port -s https://www.google.com > /dev/null 2>&1; then
        echo "✅ 发现可用代理: http://127.0.0.1:$port"
        export HTTP_PROXY=http://127.0.0.1:$port
        export HTTPS_PROXY=http://127.0.0.1:$port
        found_proxy=true
        break
    fi
done

if [ "$found_proxy" = false ]; then
    echo "❌ 未自动发现代理"
    echo ""
    echo "请手动配置代理："
    echo ""
    echo "方法 1: 临时环境变量"
    echo "  export HTTP_PROXY=http://127.0.0.1:端口"
    echo "  export HTTPS_PROXY=http://127.0.0.1:端口"
    echo "  docker push guangda88/lingflow-api:latest"
    echo ""
    echo "方法 2: Docker daemon 配置（持久）"
    echo "  sudo mkdir -p /etc/systemd/system/docker.service.d"
    echo "  sudo vim /etc/systemd/system/docker.service.d/http-proxy.conf"
    echo "  内容: [Service]"
    echo "        Environment=\"HTTP_PROXY=http://127.0.0.1:端口\""
    echo "        Environment=\"HTTPS_PROXY=http://127.0.0.1:端口\""
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl restart docker"
    echo ""
    echo "方法 3: 使用 VPN"
    echo "  启动你的 VPN 软件"
    echo "  然后重试 docker push"
    echo ""
    exit 1
fi

echo ""
echo "✅ 代理已设置: $HTTP_PROXY"
echo ""

# 测试连接
echo "🧪 测试代理连接..."
if curl -s -m 5 https://registry-1.docker.io/v2/ > /dev/null; then
    echo "✅ 可以连接 Docker Hub"
else
    echo "⚠️ 无法连接 Docker Hub，请检查代理"
    exit 1
fi

echo ""

# 配置 Docker daemon
echo "📝 配置 Docker daemon 使用代理..."

sudo mkdir -p /etc/systemd/system/docker.service.d

sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null <<EOF
[Service]
Environment="HTTP_PROXY=$HTTP_PROXY"
Environment="HTTPS_PROXY=$HTTPS_PROXY"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF

echo "✅ Docker daemon 配置已更新"
echo ""

# 重启 Docker
echo "🔄 重启 Docker 服务..."
sudo systemctl daemon-reload
sudo systemctl restart docker

echo "等待 Docker 启动..."
sleep 3

if systemctl is-active --quiet docker; then
    echo "✅ Docker 服务已重启"
else
    echo "❌ Docker 启动失败"
    exit 1
fi

echo ""
echo "======================="
echo "🎉 代理配置完成！"
echo ""
echo "现在可以推送镜像了："
echo "  docker push guangda88/lingflow-api:latest"
echo "  docker push guangda88/lingflow-api:v3.8.0"
echo ""
echo "如需取消代理："
echo "  sudo rm /etc/systemd/system/docker.service.d/http-proxy.conf"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl restart docker"
echo ""
