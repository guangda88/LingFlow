#!/bin/bash
# LingFlow 多仓库 Docker 镜像推送脚本 v2.0
# 支持: Docker Hub, 阿里云, GitHub CR
# 使用: ./docker-push.sh [version]

set -e

# 配置
IMAGE_NAME="lingflow-api"
VERSION="${1:-latest}"
SOURCE_IMAGE="${IMAGE_NAME}:test"

# 仓库列表 - 国际
REGISTRIES_INTL=(
    "guangda88/${IMAGE_NAME}"           # Docker Hub
    "ghcr.io/guangda88/${IMAGE_NAME}"   # GitHub Container Registry
)

# 仓库列表 - 国内
REGISTRIES_CN=(
    "registry.cn-hangzhou.aliyuncs.com/guangda88/${IMAGE_NAME}"    # 阿里云杭州
    "registry.cn-beijing.aliyuncs.com/guangda88/${IMAGE_NAME}"     # 阿里云北京
)

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_blue() { echo -e "${BLUE}[DOING]${NC} $1"; }

# 重试函数
retry_push() {
    local target=$1
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_blue "推送到 $target (尝试 $attempt/$max_attempts)..."

        if docker push "$target" 2>&1; then
            log_info "✅ 成功: $target"
            return 0
        fi

        if [ $attempt -lt $max_attempts ]; then
            log_warn "推送失败，等待5秒后重试..."
            sleep 5
        fi
        ((attempt++))
    done

    log_error "❌ 失败: $target"
    return 1
}

# 主流程
echo ""
echo "🐳 LingFlow 多仓库镜像推送"
echo "========================================"
log_info "源镜像: $SOURCE_IMAGE"
log_info "版本: $VERSION"
echo ""

# 检查源镜像
if ! docker image inspect "$SOURCE_IMAGE" &>/dev/null; then
    log_error "源镜像不存在: $SOURCE_IMAGE"
    log_info "可用的本地镜像:"
    docker images | grep lingflow-api || true
    exit 1
fi

# 统计
SUCCESS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=$((${#REGISTRIES_INTL[@]} + ${#REGISTRIES_CN[@]}))

# === 国际仓库 ===
echo ""
log_blue "=========================================="
log_blue "🌍 国际仓库"
log_blue "=========================================="

for registry in "${REGISTRIES_INTL[@]}"; do
    TARGET="${registry}:${VERSION}"
    log_info "标记: $TARGET"
    docker tag "$SOURCE_IMAGE" "$TARGET" 2>/dev/null || true

    if retry_push "$TARGET"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
    docker rmi "${TARGET}" &>/dev/null || true
done

# === 国内仓库 ===
echo ""
log_blue "=========================================="
log_blue "🇨🇳 国内仓库"
log_blue "=========================================="

for registry in "${REGISTRIES_CN[@]}"; do
    TARGET="${registry}:${VERSION}"
    log_info "标记: $TARGET"
    docker tag "$SOURCE_IMAGE" "$TARGET" 2>/dev/null || true

    if retry_push "$TARGET"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
    docker rmi "${TARGET}" &>/dev/null || true
done

# === 总结 ===
echo ""
echo "========================================"
log_info "推送完成: $SUCCESS_COUNT/$TOTAL_COUNT 成功"
if [ $FAIL_COUNT -gt 0 ]; then
    log_warn "失败: $FAIL_COUNT 个仓库"
fi
echo "========================================"
echo ""

# 验证地址
echo "📋 验证地址:"
echo ""
echo "国际:"
echo "  - Docker Hub: https://hub.docker.com/r/guangda88/lingflow-api/tags"
echo "  - GitHub CR:  https://ghcr.io/guangda88/lingflow-api"
echo ""
echo "国内:"
echo "  - 阿里云杭州: https://cr.console.aliyun.com/repository/registry.cn-hangzhou.aliyuncs.com/guangda88/lingflow-api"
echo "  - 阿里云北京: https://cr.console.aliyun.com/repository/registry.cn-beijing.aliyuncs.com/guangda88/lingflow-api"
echo ""
echo "📥 拉取命令:"
echo ""
echo "国际:"
echo "  docker pull guangda88/lingflow-api:$VERSION"
echo "  docker pull ghcr.io/guangda88/lingflow-api:$VERSION"
echo ""
echo "国内:"
echo "  docker pull registry.cn-hangzhou.aliyuncs.com/guangda88/lingflow-api:$VERSION"
echo "  docker pull registry.cn-beijing.aliyuncs.com/guangda88/lingflow-api:$VERSION"
echo ""

[ $FAIL_COUNT -eq 0 ] && exit 0 || exit 1
