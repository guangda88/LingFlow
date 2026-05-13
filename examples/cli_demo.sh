#!/bin/bash
# lingflow CLI 快速演示脚本

set -e

echo "================================"
echo "lingflow CLI 快速演示"
echo "================================"
echo ""

# 1. 显示帮助
echo "1. 显示帮助"
echo "命令: lingflow --help"
echo ""
python -m lingflow.cli --help
echo ""
read -p "按回车继续..."
echo ""

# 2. 列出技能
echo "2. 列出可用技能"
echo "命令: lingflow list-skills"
echo ""
python -m lingflow.cli list-skills
echo ""
read -p "按回车继续..."
echo ""

# 3. 分析命令帮助
echo "3. 分析命令帮助"
echo "命令: lingflow analyze --help"
echo ""
python -m lingflow.cli analyze --help
echo ""
read -p "按回车继续..."
echo ""

# 4. 学习命令帮助
echo "4. 学习命令帮助"
echo "命令: lingflow learn --help"
echo ""
python -m lingflow.cli learn --help
echo ""
read -p "按回车继续..."
echo ""

# 5. 优化命令帮助
echo "5. 优化命令帮助"
echo "命令: lingflow optimize --help"
echo ""
python -m lingflow.cli optimize --help
echo ""
read -p "按回车继续..."
echo ""

# 6. 测试命令帮助
echo "6. 测试命令帮助"
echo "命令: lingflow test --help"
echo ""
python -m lingflow.cli test --help
echo ""
read -p "按回车继续..."
echo ""

echo "================================"
echo "演示完成！"
echo "================================"
echo ""
echo "更多命令示例:"
echo "  lingflow analyze run-analyze --target ./lingflow"
echo "  lingflow learn run-learn --tools ruff --target ./lingflow"
echo "  lingflow optimize run structure --target ./lingflow"
echo "  lingflow test run-test --coverage"
echo ""
echo "查看完整文档: docs/CLI_GUIDE.md"
