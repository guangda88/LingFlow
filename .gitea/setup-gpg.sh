#!/bin/bash
# GPG 签名配置脚本
# 用途：为 LingFlow 项目配置 GPG 签名

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否已安装 GPG
check_gpg() {
    if ! command -v gpg &> /dev/null; then
        log_error "GPG is not installed"
        log_info "Install with: sudo apt-get install gnupg  # Ubuntu/Debian"
        log_info "              sudo yum install gnupg2       # CentOS/RHEL"
        exit 1
    fi
    log_info "GPG is installed"
}

# 检查是否已有 GPG 密钥
check_existing_keys() {
    local keys=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep -E "^sec" | wc -l)
    if [ "$keys" -gt 0 ]; then
        log_info "Found $keys existing GPG key(s)"
        return 0
    else
        return 1
    fi
}

# 生成新的 GPG 密钥
generate_key() {
    log_step "Generating new GPG key..."

    cat > /tmp/gpg-key-input <<EOF
%no-protection
Key-Type: RSA
Key-Length: 4096
Name-Real: LingFlow
Name-Email: lingflow@guangda.ai
Expire-Date: 0
%commit
EOF

    gpg --batch --generate-key /tmp/gpg-key-input
    rm -f /tmp/gpg-key-input

    log_info "GPG key generated successfully"
}

# 显示 GPG 密钥信息
show_key_info() {
    log_info "Your GPG keys:"
    gpg --list-secret-keys --keyid-format LONG
}

# 导出公钥
export_public_key() {
    log_step "Exporting public key..."

    local key_id=$(gpg --list-secret-keys --keyid-format LONG | grep -E "^sec" | head -1 | sed -E 's/^.+\/([A-Z0-9]+) .+/\1/')

    if [ -z "$key_id" ]; then
        log_error "No GPG key found"
        exit 1
    fi

    log_info "Exporting public key for key ID: $key_id"
    gpg --armor --export "$key_id" > /tmp/lingflow-gpg-public-key.asc

    log_info "Public key exported to: /tmp/lingflow-gpg-public-key.asc"
    log_info "Content:"
    echo ""
    cat /tmp/lingflow-gpg-public-key.asc
    echo ""

    log_info "Please upload this public key to Gitea:"
    log_info "  Settings → SSH/GPG Keys → Add GPG Key"
}

# 配置 Git 使用 GPG 签名
configure_git() {
    log_step "Configuring Git for GPG signing..."

    local key_id=$(gpg --list-secret-keys --keyid-format LONG | grep -E "^sec" | head -1 | sed -E 's/^.+\/([A-Z0-9]+) .+/\1/')

    if [ -z "$key_id" ]; then
        log_error "No GPG key found"
        exit 1
    fi

    # 全局配置
    git config --global commit.gpgsign true
    git config --global user.signingkey "$key_id"
    git config --global gpg.program gpg

    log_info "Git configured to sign commits with key: $key_id"
    log_info "Configured options:"
    log_info "  commit.gpgsign = true"
    log_info "  user.signingkey = $key_id"
}

# 测试 GPG 签名
test_signing() {
    log_step "Testing GPG signing..."

    # 创建测试提交
    local test_branch="test-gpg-$(date +%s)"
    git checkout -b "$test_branch" 2>/dev/null || true

    # 创建测试文件
    echo "GPG signing test" > /tmp/test-gpg.txt
    git add /tmp/test-gpg.txt 2>/dev/null || true

    # 尝试签名提交
    if git commit -S -m "test: GPG signing test" 2>&1 | grep -q "gpg: skipped"; then
        log_error "GPG signing failed"
        log_info "Please check your GPG configuration"
        git checkout master 2>/dev/null || git checkout main
        git branch -D "$test_branch" 2>/dev/null || true
        exit 1
    fi

    log_info "GPG signing test passed! ✅"

    # 清理
    git checkout master 2>/dev/null || git checkout main
    git branch -D "$test_branch" 2>/dev/null || true
}

# 显示使用说明
show_usage() {
    log_info ""
    log_info "📋 Usage Instructions:"
    log_info ""
    log_info "1. Normal commit (auto-signed):"
    log_info "   git commit -m 'feat: add new feature'"
    log_info ""
    log_info "2. Manual signing (if auto-sign is disabled):"
    log_info "   git commit -S -m 'feat: add new feature'"
    log_info ""
    log_info "3. Check if a commit is signed:"
    log_info "   git log --show-signature -1"
    log_info ""
    log_info "4. Verify a commit:"
    log_info "   git verify-commit <commit-hash>"
    log_info ""
    log_info "5. Disable signing temporarily:"
    log_info "   git commit --no-gpg-sign -m 'message'"
    log_info ""
}

# 主函数
main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  LingFlow GPG Signing Setup${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    check_gpg

    if ! check_existing_keys; then
        log_warn "No GPG key found. Generating a new one..."
        generate_key
    fi

    show_key_info

    if [ -n "$GIT_CONFIGURE" ] || [ "$1" = "--configure" ]; then
        configure_git
        export_public_key
        test_signing
    else
        log_info ""
        log_warn "To configure Git for GPG signing, run:"
        log_warn "  $0 --configure"
        log_warn ""
    fi

    show_usage
}

main "$@"
