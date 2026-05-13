#!/bin/bash
# lingflow 启用脚本

# 添加到 PATH (建议添加到 ~/.bashrc)
export PATH="/home/ai/lingflow:$PATH"

# 创建别名
alias lingflow='python /home/ai/lingflow/cli.py'

echo "lingflow 已启用！"
echo ""
echo "可用命令:"
echo "  lingflow list-skills              # 列出所有技能"
echo "  lingflow run <skill>              # 执行技能"
echo "  lingflow workflow <workflow>      # 执行工作流"
echo "  lingflow context status           # 查看上下文状态"
echo "  lingflow context compress         # 压缩上下文"
echo ""
echo "示例:"
echo "  lingflow run code-review --params '{\"target\": \"./\"}'"
echo "  lingflow workflow workflows/requirements-analysis.yaml"
