#!/bin/bash
# lingflow 包装命令 - 自动设置环境并执行命令

export PATH="$HOME/.local/bin:$PATH"
cd /home/ai/lingflow

# 如果有参数，执行 lingflow 命令
if [ $# -gt 0 ]; then
    python3 cli.py "$@"
else
    # 没有参数，显示帮助
    python3 cli.py --help
fi
