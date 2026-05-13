#!/bin/bash
# lingflow Hooks 测试脚本 v1.0
# 功能: 验证 Hooks 系统正确安装和运行

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 统计变量
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 日志函数
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    ((TOTAL_TESTS++))
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# 测试函数
test_hooks_configured() {
    log_test "检查 Hooks 配置"

    local hooks_path=$(git config --get core.hooksPath)
    if [ "$hooks_path" = ".githooks" ]; then
        log_pass "Hooks 路径配置正确: .githooks"
        return 0
    else
        log_fail "Hooks 路径配置错误: $hooks_path"
        return 1
    fi
}

test_hook_files_exist() {
    log_test "检查 Hook 文件存在性"

    local missing=0

    for hook in pre-commit commit-msg pre-push; do
        if [ -f ".githooks/$hook" ]; then
            log_info "✓ .githooks/$hook"
        else
            log_fail "✗ .githooks/$hook 不存在"
            missing=1
        fi
    done

    if [ $missing -eq 0 ]; then
        log_pass "所有 Hook 文件存在"
        return 0
    else
        return 1
    fi
}

test_hook_files_executable() {
    log_test "检查 Hook 文件可执行权限"

    local not_exec=0

    for hook in .githooks/pre-commit .githooks/commit-msg .githooks/pre-push; do
        if [ -x "$hook" ]; then
            log_info "✓ $hook"
        else
            log_fail "✗ $hook 不可执行"
            not_exec=1
        fi
    done

    if [ $not_exec -eq 0 ]; then
        log_pass "所有 Hook 文件可执行"
        return 0
    else
        return 1
    fi
}

test_pre_commit_hook() {
    log_test "测试 Pre-commit Hook"

    # 创建测试文件
    cat > /tmp/test_hook_file.py << 'EOF'
def test_function():
    x=1
    return x
EOF

    # 运行 hook
    if .githooks/pre-commit < /dev/null 2>&1; then
        log_pass "Pre-commit Hook 运行成功"
        rm -f /tmp/test_hook_file.py
        return 0
    else
        local exit_code=$?
        log_fail "Pre-commit Hook 运行失败 (exit code: $exit_code)"
        rm -f /tmp/test_hook_file.py
        return 1
    fi
}

test_commit_msg_hook() {
    log_test "测试 Commit-msg Hook"

    # 创建测试提交消息
    cat > /tmp/test_commit_msg.txt << 'EOF'
feat(agent): 添加测试 Agent
EOF

    # 运行 hook
    if .githooks/commit-msg /tmp/test_commit_msg.txt 2>&1 | grep -q "检查通过"; then
        log_pass "Commit-msg Hook 运行成功"
        rm -f /tmp/test_commit_msg.txt
        return 0
    else
        log_fail "Commit-msg Hook 运行失败"
        rm -f /tmp/test_commit_msg.txt
        return 1
    fi
}

test_commit_msg_hook_bad_format() {
    log_test "测试 Commit-msg Hook 格式验证"

    # 创建错误的提交消息
    cat > /tmp/test_commit_msg_bad.txt << 'EOF'
bad commit message
EOF

    # 运行 hook（应该失败）
    if .githooks/commit-msg /tmp/test_commit_msg_bad.txt > /dev/null 2>&1; then
        log_fail "Commit-msg Hook 未正确拒绝错误格式"
        rm -f /tmp/test_commit_msg_bad.txt
        return 1
    else
        # 检查退出码
        local exit_code=$?
        if [ $exit_code -ne 0 ]; then
            log_pass "Commit-msg Hook 正确拒绝错误格式 (exit code: $exit_code)"
            rm -f /tmp/test_commit_msg_bad.txt
            return 0
        else
            log_fail "Commit-msg Hook 未正确验证格式"
            rm -f /tmp/test_commit_msg_bad.txt
            return 1
        fi
    fi
}

test_pre_push_hook() {
    log_test "测试 Pre-push Hook"

    # 模拟推送输入（使用空的推送，跳过实际检查）
    local push_input="0000000000000000000000000000000000000000 0000000000000000000000000000000000000000 refs/heads/test $(git rev-parse HEAD) origin http://test.url/repo.git"

    # 运行 hook（检查是否能够执行）
    if echo "" | LINGFLOW_SKIP_TESTS=1 .githooks/pre-push > /dev/null 2>&1; then
        log_pass "Pre-push Hook 运行成功"
        return 0
    else
        log_fail "Pre-push Hook 运行失败"
        return 1
    fi
}

test_development_rules_exist() {
    log_test "检查开发规则文档"

    if [ -f "LINGFLOW_DEVELOPMENT_RULES.md" ]; then
        log_pass "开发规则文档存在"
        return 0
    else
        log_fail "开发规则文档不存在"
        return 1
    fi
}

test_deployment_guide_exist() {
    log_test "检查部署指南文档"

    if [ -f "HOOKS_DEPLOYMENT_GUIDE.md" ]; then
        log_pass "部署指南文档存在"
        return 0
    else
        log_fail "部署指南文档不存在"
        return 1
    fi
}

# 主测试流程
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  lingflow Hooks 系统测试 v1.0${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # 切换到项目根目录
    if [ -f "pyproject.toml" ]; then
        log_info "当前目录: $(pwd)"
    else
        log_fail "请在 lingflow 项目根目录运行此脚本"
        exit 1
    fi

    # 运行所有测试
    test_hooks_configured || true
    test_hook_files_exist || true
    test_hook_files_executable || true
    test_pre_commit_hook || true
    test_commit_msg_hook || true
    test_commit_msg_hook_bad_format || true
    test_pre_push_hook || true
    test_development_rules_exist || true
    test_deployment_guide_exist || true

    # 输出总结
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  测试总结${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "  总测试数: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "  通过: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "  失败: ${RED}$FAILED_TESTS${NC}"
    echo ""

    # 计算通过率
    if [ $TOTAL_TESTS -gt 0 ]; then
        local pass_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
        echo -e "  通过率: ${BLUE}${pass_rate}%${NC}"
    fi

    echo ""

    # 返回状态
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✓ 所有测试通过！Hooks 系统部署成功。${NC}"
        echo ""
        echo "下一步:"
        echo "  1. 阅读部署指南: cat HOOKS_DEPLOYMENT_GUIDE.md"
        echo "  2. 查看开发规则: cat LINGFLOW_DEVELOPMENT_RULES.md"
        echo "  3. 开始使用 Hooks 进行开发"
        echo ""
        exit 0
    else
        echo -e "${RED}✗ 部分测试失败，请检查上述错误。${NC}"
        echo ""
        echo "排查建议:"
        echo "  1. 检查 Git 配置: git config --get core.hooksPath"
        echo "  2. 检查文件权限: ls -la .githooks/"
        echo "  3. 查看详细错误: DEBUG=1 bash test_hooks.sh"
        echo ""
        exit 1
    fi
}

# 执行主函数
main "$@"
