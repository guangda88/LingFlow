#!/bin/bash
# Docker Daemon 智能代理配置
# 用途: 国际仓库走代理，国内仓库直连

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 🔒 安全检查: NodeBabyLink 依赖 Docker
# 如果 NodeBabyLink 路由服务启用，重启 Docker 将导致隧道断开
if systemctl is-enabled nodebabylink-route.service 2>/dev/null | grep -qE 'enabled|generated'; then
    log_error "⚠️  检测到 NodeBabyLink 路由服务已启用"
    echo ""
    log_error "此服务依赖 Docker，重启 Docker 将导致："
    log_error "  • NodeBabyLink 隧道 (100.66.1.8) 断开"
    log_error "  • 通过隧道的 SSH 连接中断"
    echo ""
    log_info "如需继续，请先确认："
    log_info "  1. 不在通过隧道的 SSH 会话中操作"
    log_info "  2. 隧道断开后有其他方式访问服务器"
    echo ""
    read -p "确定要继续吗? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi
fi

# 检测代理端口
PROXY_PORT=""
for port in 7890 7891 10808 10809; do
    if timeout 1 bash -c "echo > /dev/tcp/127.0.0.1/$port" 2>/dev/null; then
        PROXY_PORT=$port
        break
    fi
done

if [ -z "$PROXY_PORT" ]; then
    log_warn "未检测到代理，使用默认端口 7890"
    PROXY_PORT=7890
fi

log_info "检测到代理端口: $PROXY_PORT"

# 配置内容
CONFIG_CONTENT="[Service]
Environment=\"HTTP_PROXY=http://127.0.0.1:${PROXY_PORT}\"
Environment=\"HTTPS_PROXY=http://127.0.0.1:${PROXY_PORT}\"
Environment=\"NO_PROXY=localhost,127.0.0.1,*.aliyuncs.com,*.aliyunpcs.com,*.cn,*.tencentcloudcr.com,*.cn-north-1.cr.amazonaws.com.cn,hub-mirror.c.163.com,docker.m.daocloud.io,dockerproxy.com,docker.mirrors.ustc.edu.cn,docker.nju.edu.cn,cr.console.aliyun.com,registry.cn-hangzhou.aliyuncs.com,registry.cn-beijing.aliyuncs.com,registry.cn-shenzhen.aliyuncs.com,registry.cn-shanghai.aliyuncs.com,registry.cn-qingdao.aliyuncs.com,registry.cn-zhangjiakou.aliyuncs.com\""

log_info "配置 Docker daemon..."
echo ""
echo "$CONFIG_CONTENT"
echo ""

sudo mkdir -p /etc/systemd/system/docker.service.d
echo "$CONFIG_CONTENT" | sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null

log_info "重启 Docker daemon..."
sudo systemctl daemon-reload
sudo systemctl restart docker

sleep 3

if systemctl is-active --quiet docker; then
    log_info "✅ Docker 服务运行正常"
    log_info "配置已保存到: /etc/systemd/system/docker.service.d/http-proxy.conf"
    echo ""
    log_info "路由规则:"
    log_info "  🌍 国际仓库 (Docker Hub, GHCR) -> 代理"
    log_info "  🇨🇳 国内仓库 (阿里云, 网易) -> 直连"
else
    log_warn "⚠️ Docker 启动可能有问题，请检查: sudo systemctl status docker"
fi
