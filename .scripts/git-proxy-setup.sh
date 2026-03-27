#!/bin/bash
# Git 代理配置脚本
# 用于解决国内访问 GitHub 不稳定的问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROXY_CONFIG_FILE="$HOME/.git-proxy-config"

# 代理服务器配置（根据实际情况修改）
GHPROXY_SERVER=""      # 格式: http://server:port
CF_PROXY_URL=""        # 格式: https://your-worker.workers.dev

# 打印帮助信息
show_help() {
    echo "Git 代理配置脚本 - 解决国内 GitHub 访问问题"
    echo ""
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  setup-ghproxy <server>    配置 ghproxy 代理"
    echo "  setup-cf <url>            配置 Cloudflare Workers 代理"
    echo "  setup-hybrid <ghproxy> <cf>  混合策略"
    echo "  status                    查看当前配置"
    echo "  clear                     清除所有代理配置"
    echo "  test-connection           测试 GitHub 连接"
    echo ""
    echo "示例:"
    echo "  $0 setup-ghproxy http://localhost:8080"
    echo "  $0 setup-cf https://my-proxy.workers.dev"
    echo "  $0 setup-hybrid http://localhost:8080 https://my-proxy.workers.dev"
}

# 检测网络连接
test_github_connection() {
    echo -e "${YELLOW}测试 GitHub 连接...${NC}"

    # 测试 raw.github.com
    if curl -s --max-time 5 https://raw.githubusercontent.com > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 直接连接成功${NC}"
        return 0
    else
        echo -e "${RED}✗ 直接连接失败${NC}"
    fi

    # 测试当前代理
    if [ -n "$GHPROXY_SERVER" ]; then
        echo -e "${YELLOW}测试代理 $GHPROXY_SERVER...${NC}"
        if curl -s --max-time 5 --proxy "$GHPROXY_SERVER" https://github.com > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 代理连接成功${NC}"
            return 0
        else
            echo -e "${RED}✗ 代理连接失败${NC}"
        fi
    fi

    return 1
}

# 配置 ghproxy
setup_ghproxy() {
    local server=$1

    if [ -z "$server" ]; then
        echo -e "${RED}错误: 请指定代理服务器地址${NC}"
        echo "用法: $0 setup-ghproxy http://server:port"
        exit 1
    fi

    echo -e "${GREEN}配置 ghproxy 代理: $server${NC}"

    # 设置全局代理
    git config --global http.https://github.com.proxy "$server"
    git config --global https.https://github.com.proxy "$server"

    # 保存配置
    cat > "$PROXY_CONFIG_FILE" << EOF
GIT_PROXY_TYPE=ghproxy
GHPROXY_SERVER=$server
EOF

    echo -e "${GREEN}✓ ghproxy 配置完成${NC}"
    show_status
}

# 配置 Cloudflare Workers 代理
setup_cf() {
    local url=$1

    if [ -z "$url" ]; then
        echo -e "${RED}错误: 请指定 Workers URL${NC}"
        echo "用法: $0 setup-cf https://your-worker.workers.dev"
        exit 1
    fi

    echo -e "${GREEN}配置 Cloudflare Workers 代理: $url${NC}"

    # 使用 url rewriting
    git config --global url."$url".insteadOf "https://github.com"
    git config --global url."$url".insteadOf "https://raw.githubusercontent.com"

    # 保存配置
    cat > "$PROXY_CONFIG_FILE" << EOF
GIT_PROXY_TYPE=cf
CF_PROXY_URL=$url
EOF

    echo -e "${GREEN}✓ Cloudflare Workers 配置完成${NC}"
    show_status
}

# 配置混合策略
setup_hybrid() {
    local ghproxy=$1
    local cf_url=$2

    if [ -z "$ghproxy" ] || [ -z "$cf_url" ]; then
        echo -e "${RED}错误: 请同时指定 ghproxy 和 CF Workers URL${NC}"
        echo "用法: $0 setup-hybrid <ghproxy> <cf-url>"
        exit 1
    fi

    echo -e "${GREEN}配置混合策略${NC}"
    echo "  Git 推送/拉取: $ghproxy"
    echo "  Raw 文件/API: $cf_url"

    # Git 操作走 ghproxy
    git config --global http.https://github.com.proxy "$ghproxy"
    git config --global https.https://github.com.proxy "$ghproxy"

    # Raw 文件走 CF Workers
    git config --global url."$cf_url".insteadOf "https://raw.githubusercontent.com"

    # 保存配置
    cat > "$PROXY_CONFIG_FILE" << EOF
GIT_PROXY_TYPE=hybrid
GHPROXY_SERVER=$ghproxy
CF_PROXY_URL=$cf_url
EOF

    echo -e "${GREEN}✓ 混合策略配置完成${NC}"
    show_status
}

# 显示当前状态
show_status() {
    echo -e "\n${YELLOW}=== 当前 Git 代理配置 ===${NC}"

    # 检查全局代理
    local http_proxy=$(git config --global --get http.https://github.com.proxy)
    local https_proxy=$(git config --global --get https.https://github.com.proxy)

    if [ -n "$http_proxy" ]; then
        echo -e "GitHub HTTP 代理: ${GREEN}$http_proxy${NC}"
    else
        echo -e "GitHub HTTP 代理: ${YELLOW}未设置${NC}"
    fi

    if [ -n "$https_proxy" ]; then
        echo -e "GitHub HTTPS 代理: ${GREEN}$https_proxy${NC}"
    else
        echo -e "GitHub HTTPS 代理: ${YELLOW}未设置${NC}"
    fi

    # 检查 URL 重写
    local url_rewrite=$(git config --global --get-regexp "^url.*.insteadof$" || true)
    if [ -n "$url_rewrite" ]; then
        echo -e "\nURL 重写规则:"
        echo "$url_rewrite"
    fi

    # 测试连接
    test_github_connection
}

# 清除所有代理配置
clear_proxy() {
    echo -e "${YELLOW}清除所有 Git 代理配置...${NC}"

    git config --global --unset http.https://github.com.proxy
    git config --global --unset https.https://github.com.proxy
    git config --global --unset-all url."https://github.com/".insteadof
    git config --global --unset-all url."https://raw.githubusercontent.com/".insteadof

    rm -f "$PROXY_CONFIG_FILE"

    echo -e "${GREEN}✓ 代理配置已清除${NC}"
}

# 快速测试推送
test_push() {
    echo -e "${YELLOW}测试 Git 推送...${NC}"

    # 创建测试分支
    local test_branch="test-proxy-$(date +%s)"
    git checkout -b "$test_branch" 2>/dev/null || git checkout -b "$test_branch"

    # 创建测试提交
    echo "proxy test" > .proxy-test
    git add .proxy-test
    git commit -m "test proxy connection"

    echo -e "${YELLOW}尝试推送到远程仓库...${NC}"
    if git push -u origin "$test_branch" 2>&1; then
        echo -e "${GREEN}✓ 推送成功${NC}"
        git branch -D "$test_branch"
        return 0
    else
        echo -e "${RED}✗ 推送失败${NC}"
        git checkout -
        git branch -D "$test_branch" 2>/dev/null
        return 1
    fi
}

# 主函数
main() {
    case "${1:-}" in
        setup-ghproxy)
            setup_ghproxy "$2"
            ;;
        setup-cf)
            setup_cf "$2"
            ;;
        setup-hybrid)
            setup_hybrid "$2" "$3"
            ;;
        status)
            show_status
            ;;
        clear)
            clear_proxy
            ;;
        test-connection)
            test_github_connection
            ;;
        test-push)
            test_push
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}错误: 未知命令 '${1:-}'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
