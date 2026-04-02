#!/bin/bash
# LingFlow Quality Gate - Entry Point
# 处理 GitHub Action 参数并执行 LingFlow 命令

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "::group::LingFlow Quality Gate"
echo "${GREEN}LingFlow AI-Powered Code Review${NC}"
echo "${GREEN}=============================${NC}"
echo ""

# 解析参数
COMMAND=${1:-"review"}
PATH_TO_CHECK=${2:-"./src"}
OUTPUT_FORMAT=${3:-"markdown"}
FAIL_ON_ERROR=${4:-"false"}
API_KEY=${5:-""}

echo "Command: $COMMAND"
echo "Path: $PATH_TO_CHECK"
echo "Output Format: $OUTPUT_FORMAT"
echo "Fail on Error: $FAIL_ON_ERROR"
echo ""

# 检查路径是否存在
if [ ! -d "$PATH_TO_CHECK" ] && [ ! -f "$PATH_TO_CHECK" ]; then
    echo "${RED}Error: Path '$PATH_TO_CHECK' does not exist${NC}"
    exit 1
fi

# 设置输出文件
OUTPUT_DIR="/github/workspace/.lingflow"
mkdir -p "$OUTPUT_DIR"
RESULT_FILE="$OUTPUT_DIR/result.json"
MARKDOWN_FILE="$OUTPUT_DIR/result.md"

# 执行 LingFlow 命令
echo "${GREEN}Running LingFlow...${NC}"
echo ""

if [ -n "$API_KEY" ]; then
    export LINGFLOW_API_KEY="$API_KEY"
fi

# 执行审查/测试/优化命令
case $COMMAND in
    review|test|optimize|analyze)
        lingflow $COMMAND "$PATH_TO_CHECK" \
            --output-format json \
            --output-file "$RESULT_FILE" \
            ${ACTION_VERBOSE:+--verbose}
        ;;
    *)
        echo "${RED}Error: Unknown command '$COMMAND'${NC}"
        echo "Valid commands: review, test, optimize, analyze"
        exit 1
        ;;
esac

echo ""
echo "${GREEN}LingFlow completed${NC}"
echo ""

# 提取结果
if [ -f "$RESULT_FILE" ]; then
    # 提取问题数量
    ISSUES=$(jq '.issues // [] | length' "$RESULT_FILE" 2>/dev/null || echo "0")
    SCORE=$(jq '.overall_score // 0' "$RESULT_FILE" 2>/dev/null || echo "N/A")

    echo "Issues Found: $ISSUES"
    echo "Overall Score: $SCORE"
    echo ""

    # 设置输出
    echo "issues_found=$ISSUES" >> $GITHUB_OUTPUT
    echo "result_file=$RESULT_FILE" >> $GITHUB_OUTPUT
    echo "overall_score=$SCORE" >> $GITHUB_OUTPUT

    # 生成 Markdown 输出
    if [ "$OUTPUT_FORMAT" = "markdown" ]; then
        lingflow $COMMAND "$PATH_TO_CHECK" \
            --output-format markdown \
            --output-file "$MARKDOWN_FILE" 2>/dev/null || true

        if [ -f "$MARKDOWN_FILE" ]; then
            # 添加到 Summary
            echo "${GREEN}Adding results to summary...${NC}"
            cat "$MARKDOWN_FILE" >> $GITHUB_STEP_SUMMARY

            # PR 评论
            if [ -n "$GITHUB_PR_NUMBER" ] && [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then
                echo "${GREEN}Posting PR comment...${NC}"
                gh pr comment \
                    "$GITHUB_PR_NUMBER" \
                    --body "$(cat "$MARKDOWN_FILE)" \
                    --repo "$GITHUB_REPOSITORY" || echo "${YELLOW}Warning: Failed to post PR comment${NC}"
            fi
        fi
    fi

    # 检查是否失败
    if [ "$FAIL_ON_ERROR" = "true" ] && [ "$ISSUES" -gt "0" ]; then
        echo "${RED}Failing workflow: $ISSUES issue(s) found${NC}"
        exit 1
    fi

    echo "${GREEN}✅ Quality gate passed${NC}"
else
    echo "${YELLOW}Warning: Result file not found${NC}"
fi

echo ""
echo "::endgroup::"
