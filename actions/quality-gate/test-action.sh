#!/bin/bash
# 本地测试 GitHub Action 的脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  LingFlow Quality Gate - 本地测试"
echo "=========================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

# 构建镜像
echo "1. 构建 Docker 镜像..."
docker build -t lingflow-quality-gate:test .

echo ""
echo "2. 运行测试（基础审查）..."

# 创建测试目录
TEST_DIR="/tmp/lingflow-test"
mkdir -p "$TEST_DIR"

# 创建测试代码
cat > "$TEST_DIR/test.py" << 'EOF'
def example_function(param1, param2, param3, param4, param5):
    """这是一个示例函数"""
    result = 0
    for i in range(100):
        for j in range(100):
            if param1:
                if param2:
                    if param3:
                        result += i * j
            elif param4:
                result += 1
            else:
                if param5:
                    result += 2
    return result
EOF

# 运行测试
echo ""
echo "测试参数："
echo "  Command: review"
echo "  Path: $TEST_DIR"
echo "  Output: markdown"
echo ""

docker run --rm \
    -v "$TEST_DIR:/github/workspace/src" \
    -v "$PWD/entrypoint.sh:/usr/local/bin/entrypoint.sh" \
    -e GITHUB_STEP_SUMMARY=/tmp/summary.md \
    lingflow-quality-gate:test \
    review \
    ./src \
    markdown \
    false \
    ""

echo ""
echo "3. 测试 JSON 输出..."

docker run --rm \
    -v "$TEST_DIR:/github/workspace/src" \
    -v "$PWD/entrypoint.sh:/usr/local/bin/entrypoint.sh" \
    lingflow-quality-gate:test \
    review \
    ./src \
    json \
    false \
    ""

echo ""
echo "4. 清理..."
rm -rf "$TEST_DIR"

echo ""
echo "✅ 测试完成！"
echo ""
echo "=========================================="
echo "  下一步："
echo "=========================================="
echo ""
echo "1. 在真实仓库中测试："
echo "   - 将 action.yml 复制到 .github/workflows/"
echo "   - 提交并推送"
echo "   - 查看 Actions 标签页"
echo ""
echo "2. 发布到 GitHub Marketplace："
echo "   - 创建 Release（tag: v1.0.0）"
echo "   - 在 Marketplace 中发布"
echo ""
