#!/bin/bash
# lingflow PyPI 发布脚本
# 使用方法: ./scripts/publish_to_pypi.sh [test|prod]

set -e  # 遇到错误立即退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查版本一致性
check_version() {
    log_info "检查版本一致性..."

    SETUP_VERSION=$(grep "version=" setup.py | head -1 | sed 's/.*version="\([^"]*\)".*/\1/')
    INIT_VERSION=$(grep "__version__" lingflow/__init__.py | head -1 | sed 's/.*__version__ = "\([^"]*\)".*/\1/')

    log_info "setup.py 版本: $SETUP_VERSION"
    log_info "__init__.py 版本: $INIT_VERSION"

    if [ "$SETUP_VERSION" != "$INIT_VERSION" ]; then
        log_error "版本不一致！setup.py: $SETUP_VERSION, __init__.py: $INIT_VERSION"
        exit 1
    fi

    if [ -z "$SETUP_VERSION" ]; then
        log_error "无法读取版本号"
        exit 1
    fi

    log_info "✅ 版本一致: $SETUP_VERSION"
}

# 清理旧构建
clean_build() {
    log_info "清理旧构建..."
    rm -rf dist build
    log_info "✅ 清理完成"
}

# 构建包
build_package() {
    log_info "构建包..."

    # 检查 build 工具
    if ! python -c "import build" 2>/dev/null; then
        log_warn "build 模块未安装，尝试安装..."
        pip install build twine --break-system-packages --quiet
    fi

    # 构建
    python -m build

    if [ $? -eq 0 ]; then
        log_info "✅ 构建成功"
        ls -lh dist/
    else
        log_error "构建失败"
        exit 1
    fi
}

# 验证包
check_package() {
    log_info "验证包..."

    # 检查 twine
    if ! python -c "import twine" 2>/dev/null; then
        log_warn "twine 未安装，尝试安装..."
        pip install twine --break-system-packages --quiet
    fi

    twine check dist/*

    if [ $? -eq 0 ]; then
        log_info "✅ 包验证通过"
    else
        log_error "包验证失败"
        exit 1
    fi
}

# 发布到 TestPyPI
publish_test() {
    log_warn "即将发布到 TestPyPI..."
    read -p "确认发布？[y/N] " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "发布到 TestPyPI..."
        twine upload --repository testpypi dist/*
        log_info "✅ TestPyPI 发布完成"
        log_info "测试安装: pip install --index-url https://test.pypi.org/simple/ lingflow-core"
    else
        log_warn "取消发布"
    fi
}

# 发布到正式 PyPI
publish_prod() {
    log_warn "即将发布到正式 PyPI..."
    log_warn "这是一次不可逆操作！"
    read -p "确认发布版本 $SETUP_VERSION 到 PyPI？[y/N] " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "发布到 PyPI..."
        twine upload dist/*
        log_info "✅ PyPI 发布完成"
        log_info "访问: https://pypi.org/project/lingflow-core/"
    else
        log_warn "取消发布"
    fi
}

# 主流程
main() {
    log_info "🚀 lingflow PyPI 发布脚本"
    echo ""

    check_version
    clean_build
    build_package
    check_package

    # 根据参数选择发布目标
    TARGET=${1:-"prod"}

    case $TARGET in
        test)
            publish_test
            ;;
        prod)
            publish_prod
            ;;
        *)
            log_error "未知目标: $TARGET"
            echo "使用方法: $0 [test|prod]"
            exit 1
            ;;
    esac
}

# 运行主流程
main "$@"
