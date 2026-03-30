#!/bin/bash
# LingFlow Hooks 配置 v1.0 - VibeCoding 渐进式部署
# 质量门控 + AI 辅助 + 渐进式实施

# ==================== VibeCoding 原则配置 ====================

# 质量门控级别设置
# 0=关闭, 1=警告, 2=阻断
export HOOKS_QUALITY_GATE="${HOOKS_QUALITY_GATE:-1}"

# P0 检查（基础质量 - 必需，阻断）
export HOOKS_P0_FLAKE8="${HOOKS_P0_FLAKE8:-2}"        # flake8 代码质量
export HOOKS_P0_TESTS="${HOOKS_P0_TESTS:-1}"          # 测试状态

# P1 检查（文档规范 - 警告性）
export HOOKS_P1_DOCS="${HOOKS_P1_DOCS:-1}"            # 文档完整性
export HOOKS_P1_FORMAT="${HOOKS_P1_FORMAT:-1}"        # 代码格式
export HOOKS_P1_COMMIT_MSG="${HOOKS_P1_COMMIT_MSG:-2}" # 提交消息格式

# P2 检查（增强功能 - 建议性）
export HOOKS_P2_PERF="${HOOKS_P2_PERF:-0}"            # 性能基准
export HOOKS_P2_MULTI_REPO="${HOOKS_P2_MULTI_REPO:-0}" # 多仓库一致性
export HOOKS_P2_COMPLEXITY="${HOOKS_P2_COMPLEXITY:-0}" # 复杂度检查

# ==================== 快速迭代模式 ====================

# 快速迭代模式：降低检查级别，加速开发
# 使用: HOOKS_FAST_ITERATION=1 git commit
if [ "${HOOKS_FAST_ITERATION:-0}" = "1" ]; then
    export HOOKS_P0_FLAKE8=1
    export HOOKS_P0_TESTS=0
    export HOOKS_P1_DOCS=0
    export HOOKS_P1_FORMAT=0
    export HOOKS_P2_PERF=0
    export HOOKS_P2_COMPLEXITY=0
fi

# ==================== 质量门控函数 ====================

# 获取检查级别名称
get_gate_name() {
    local level=$1
    case $level in
        0) echo "关闭" ;;
        1) echo "警告" ;;
        2) echo "阻断" ;;
        *) echo "未知" ;;
    esac
}

# 执行质量门控检查
# 参数: $1=检查级别, $2=检查名称, $3=检查结果
# 返回: 0=通过, 1=阻断
quality_gate() {
    local level=$1
    local name=$2
    local result=$3

    local gate_name=$(get_gate_name $level)

    if [ $level -eq 0 ]; then
        # 检查关闭，直接通过
        return 0
    elif [ $level -eq 1 ]; then
        # 警告级别
        if [ $result -ne 0 ]; then
            echo -e "${YELLOW}[WARN]${NC} $name - 建议修复（当前为警告级别）"
            return 0  # 警告不阻断
        fi
        return 0
    elif [ $level -eq 2 ]; then
        # 阻断级别
        if [ $result -ne 0 ]; then
            echo -e "${RED}[BLOCK]${NC} $name - 必须修复（当前为阻断级别）"
            return 1  # 阻断提交
        fi
        return 0
    fi

    return 0
}

# ==================== AI 辅助函数 ====================

# AI 智能提示：根据检查结果提供修复建议
ai_suggest_fix() {
    local check_name=$1
    local error_info=$2

    case $check_name in
        "flake8")
            echo "💡 AI 建议：运行 'flake8 <files> --fix' 或手动修复代码风格问题"
            ;;
        "format")
            echo "💡 AI 建议：运行 'black <files>' 自动格式化代码"
            ;;
        "tests")
            echo "💡 AI 建议：运行 'pytest' 查看失败测试，或使用 HOOKS_FAST_ITERATION=1 跳过"
            ;;
        "docs")
            echo "💡 AI 建议：为公共函数添加 docstring，说明功能、参数和返回值"
            ;;
        "complexity")
            echo "💡 AI 建议：拆分复杂函数，单一职责原则"
            ;;
        *)
            echo "💡 AI 建议：查看具体错误信息进行修复"
            ;;
    esac
}

# ==================== 渐进式部署函数 ====================

# 显示当前配置
show_hooks_config() {
    echo ""
    echo -e "${BLUE}=== Hooks 配置 (VibeCoding 渐进式) ===${NC}"
    echo ""
    echo "P0 检查（基础质量 - 必需）:"
    echo "  flake8    : $(get_gate_name $HOOKS_P0_FLAKE8)"
    echo "  tests     : $(get_gate_name $HOOKS_P0_TESTS)"
    echo ""
    echo "P1 检查（文档规范 - 警告）:"
    echo "  docs      : $(get_gate_name $HOOKS_P1_DOCS)"
    echo "  format    : $(get_gate_name $HOOKS_P1_FORMAT)"
    echo "  commit_msg: $(get_gate_name $HOOKS_P1_COMMIT_MSG)"
    echo ""
    echo "P2 检查（增强功能 - 建议）:"
    echo "  perf      : $(get_gate_name $HOOKS_P2_PERF)"
    echo "  multi_repo: $(get_gate_name $HOOKS_P2_MULTI_REPO)"
    echo "  complexity: $(get_gate_name $HOOKS_P2_COMPLEXITY)"
    echo ""
    echo "快速迭代模式: ${HOOKS_FAST_ITERATION:-0}"
    echo ""
}

# ==================== 配置验证 ====================

# 验证配置有效性
validate_hooks_config() {
    # 确保级别在 0-2 范围内
    for var in HOOKS_P0_FLAKE8 HOOKS_P0_TESTS HOOKS_P1_DOCS HOOKS_P1_FORMAT \
               HOOKS_P1_COMMIT_MSG HOOKS_P2_PERF HOOKS_P2_MULTI_REPO HOOKS_P2_COMPLEXITY; do
        local value=${!var}
        if [ "$value" -lt 0 ] || [ "$value" -gt 2 ]; then
            echo "警告: $var=$value 不在有效范围 [0-2]，重置为 1"
            export $var=1
        fi
    done
}

# 初始化时验证配置
validate_hooks_config
