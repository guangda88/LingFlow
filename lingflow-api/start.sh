#!/bin/bash
# LingFlow REST API - 快速启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi

    print_info "Docker 环境检查通过"
}

# 创建 .env 文件
create_env() {
    if [ ! -f .env ]; then
        print_info "创建 .env 文件"
        cat > .env << EOF
# API Keys（逗号分隔）
LINGFLOW_API_KEYS=dev-key-12345,test-key-67890

# 工作目录
LINGFLOW_WORK_DIR=/workspace

# 日志级别
LOG_LEVEL=INFO

# GitHub Token（可选，用于情报系统）
GITHUB_TOKEN=

# npm Token（可选）
NPM_TOKEN=
EOF
        print_info ".env 文件已创建"
    else
        print_info ".env 文件已存在"
    fi
}

# 构建镜像
build_images() {
    print_info "构建 Docker 镜像..."
    docker-compose build --no-cache
    print_info "镜像构建完成"
}

# 启动服务
start_services() {
    print_info "启动 LingFlow API 服务..."
    docker-compose up -d

    print_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    if docker-compose ps | grep -q "Exit"; then
        print_error "服务启动失败，请查看日志"
        docker-compose logs
        exit 1
    fi

    print_info "服务启动成功！"
}

# 显示访问信息
show_info() {
    echo ""
    echo "=========================================="
    echo "  LingFlow REST API 已启动"
    echo "=========================================="
    echo ""
    echo "📖 API 文档:"
    echo "   Swagger UI: http://localhost:8000/docs"
    echo "   ReDoc:      http://localhost:8000/redoc"
    echo ""
    echo "🔧 API 端点:"
    echo "   基础 URL:   http://localhost:8000/api/v1"
    echo "   健康检查:   http://localhost:8000/health"
    echo ""
    echo "🔑 测试 API Key:"
    echo "   dev-key-12345"
    echo ""
    echo "📊 监控和管理:"
    echo "   查看日志:    docker-compose logs -f api"
    echo "   查看状态:    docker-compose ps"
    echo "   重启服务:    docker-compose restart"
    echo "   停止服务:    docker-compose down"
    echo ""
    echo "=========================================="
}

# 测试 API
test_api() {
    print_info "测试 API 连接..."

    # 健康检查
    HEALTH=$(curl -s http://localhost:8000/health)
    if [ $? -eq 0 ]; then
        print_info "✓ 健康检查通过"
    else
        print_error "✗ 健康检查失败"
        return 1
    fi

    # 列出技能
    print_info "测试列出技能..."
    SKILLS=$(curl -s -H "X-API-Key: dev-key-12345" http://localhost:8000/api/v1/skills)
    if [ $? -eq 0 ]; then
        print_info "✓ 技能列表获取成功"
    else
        print_warn "✗ 技能列表获取失败（可能需要配置）"
    fi
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  LingFlow REST API - 快速启动"
    echo "=========================================="
    echo ""

    check_docker
    create_env

    # 询问是否构建
    read -p "$(echo -e ${YELLOW}是否重新构建镜像？[y/N]${NC} ) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_images
    fi

    start_services
    show_info
    test_api

    echo ""
    print_info "启动完成！开始使用 LingFlow API 吧 🚀"
}

# 运行
main "$@"
