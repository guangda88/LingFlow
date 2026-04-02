#!/bin/bash
# LingFlow 初始化脚本

echo "正在初始化 LingFlow 工程流系统..."
echo ""

# 检查是否在 LingFlow 目录
if [ ! -f "pyproject.toml" ] || [ ! -d "lingflow" ]; then
    echo "错误: 请在 LingFlow 项目根目录运行此脚本"
    echo "当前目录: $(pwd)"
    exit 1
fi

# 确保 .local/bin 在 PATH 中
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo "将 $HOME/.local/bin 添加到 PATH..."
    export PATH="$HOME/.local/bin:$PATH"
    echo "建议将以下行添加到 ~/.bashrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# 检查日志目录权限
mkdir -p logs
chmod 755 logs

# 运行基本检查
echo "正在运行系统检查..."
python3 cli.py list-skills > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ LingFlow 初始化成功!"
    echo ""
    echo "版本信息:"
    cat VERSION
    echo ""
    echo "可用命令:"
    echo "  lingflow list-skills              # 列出所有技能"
    echo "  lingflow run <skill>              # 执行技能"
    echo "  lingflow workflow <workflow>     # 执行工作流"
    echo "  lingflow context status           # 查看上下文状态"
    echo "  lingflow context compress         # 压缩上下文"
    echo ""
    echo "示例:"
    echo "  lingflow run code-review --params '{\"target\": \"./lingflow/\"}'"
    echo "  lingflow workflow workflows/requirements-analysis.yaml"
else
    echo "❌ 初始化失败，请检查错误信息"
    exit 1
fi
