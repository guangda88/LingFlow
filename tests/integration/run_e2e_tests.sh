#!/bin/bash
# Phase 4-5 端到端测试运行脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}LingFlow Phase 4-5 E2E Tests${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# 检查虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo -e "${YELLOW}激活虚拟环境...${NC}"
        source venv/bin/activate
    else
        echo -e "${YELLOW}未检测到虚拟环境，使用系统Python${NC}"
    fi
fi

# 检查依赖
echo -e "${YELLOW}检查测试依赖...${NC}"
python -c "import pytest" 2>/dev/null || {
    echo -e "${RED}pytest未安装，正在安装...${NC}"
    pip install pytest pytest-cov pytest-asyncio
}

# 运行测试函数
run_test_suite() {
    local test_name=$1
    local test_path=$2
    local extra_args=$3

    echo -e "\n${GREEN}运行 $test_name...${NC}"
    echo "========================================"

    if pytest "$test_path" -v --tb=short $extra_args; then
        echo -e "${GREEN}✓ $test_name 通过${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_name 失败${NC}"
        return 1
    fi
}

# 测试选项
TEST_PHASE4=false
TEST_PHASE5=false
TEST_INTEGRATION=false
TEST_EDGE_CASES=false
TEST_ALL=true
COVERAGE=false
VERBOSE=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --phase4)
            TEST_PHASE4=true
            TEST_ALL=false
            shift
            ;;
        --phase5)
            TEST_PHASE5=true
            TEST_ALL=false
            shift
            ;;
        --integration)
            TEST_INTEGRATION=true
            TEST_ALL=false
            shift
            ;;
        --edge)
            TEST_EDGE_CASES=true
            TEST_ALL=false
            shift
            ;;
        --all)
            TEST_ALL=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --phase4        仅运行Phase 4测试"
            echo "  --phase5        仅运行Phase 5测试"
            echo "  --integration   仅运行集成测试"
            echo "  --edge          仅运行边界条件测试"
            echo "  --all           运行所有测试（默认）"
            echo "  --coverage      生成覆盖率报告"
            echo "  --verbose, -v   详细输出"
            echo "  --help, -h      显示帮助"
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            exit 1
            ;;
    esac
done

# 构建pytest参数
PYTEST_ARGS=""
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -v -s"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=lingflow.self_optimizer --cov-report=html --cov-report=term"
fi

# 运行测试
FAILED=0

if [ "$TEST_ALL" = true ] || [ "$TEST_PHASE4" = true ]; then
    run_test_suite "Phase 4 E2E Tests" \
        "tests/integration/test_phase4_e2e.py" \
        "$PYTEST_ARGS" || FAILED=1
fi

if [ "$TEST_ALL" = true ] || [ "$TEST_PHASE5" = true ]; then
    run_test_suite "Phase 5 E2E Tests" \
        "tests/integration/test_phase5_e2e.py" \
        "$PYTEST_ARGS" || FAILED=1
fi

if [ "$TEST_ALL" = true ] || [ "$TEST_INTEGRATION" = true ]; then
    run_test_suite "Integration Tests" \
        "tests/integration/test_integration_e2e.py" \
        "$PYTEST_ARGS" || FAILED=1
fi

if [ "$TEST_ALL" = true ] || [ "$TEST_EDGE_CASES" = true ]; then
    run_test_suite "Edge Cases Tests" \
        "tests/integration/test_edge_cases.py" \
        "$PYTEST_ARGS" || FAILED=1
fi

# 总结
echo ""
echo -e "${GREEN}=====================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}所有测试通过！${NC}"
    if [ "$COVERAGE" = true ]; then
        echo -e "${GREEN}覆盖率报告: htmlcov/index.html${NC}"
    fi
    exit 0
else
    echo -e "${RED}部分测试失败${NC}"
    exit 1
fi
