#!/bin/bash
# lingflow 自学习系统调度配置
#
# 将此脚本添加到 crontab 中实现定期执行:
#   0 2 * * * /home/ai/lingflow/scripts/schedule_self_learning.sh
#
# 或者使用 lingflow 内置调度器

PROJECT_ROOT="/home/ai/lingflow"
SCRIPT="$PROJECT_ROOT/scripts/activate_self_learning.py"
LOG_DIR="$PROJECT_ROOT/.lingflow/logs"
REPORT_DIR="$PROJECT_ROOT/.lingflow/reports"

# 确保目录存在
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# 记录开始时间
echo "=== $(date) ===" >> "$LOG_DIR/scheduler.log"

# 运行学习周期
python3 "$SCRIPT" --full >> "$LOG_DIR/scheduler.log" 2>&1

# 记录结束时间
echo "=== Completed at $(date) ===" >> "$LOG_DIR/scheduler.log"
echo "" >> "$LOG_DIR/scheduler.log"
