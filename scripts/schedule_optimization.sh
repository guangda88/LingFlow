#!/bin/bash
# LingFlow 定期自优化脚本
# 建议通过cron定期运行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/.lingflow/logs"
REPORT_DIR="$PROJECT_DIR/.lingflow/reports"

# 创建必要目录
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/optimization_$(date +%Y%m%d_%H%M%S).log"

echo "========================================" | tee -a "$LOG_FILE"
echo "LingFlow 定期自优化" | tee -a "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 激活虚拟环境（如果存在）
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    echo "激活虚拟环境..." | tee -a "$LOG_FILE"
    source "$PROJECT_DIR/venv/bin/activate"
fi

# 运行自优化
echo "" | tee -a "$LOG_FILE"
echo "运行LingMinOpt优化..." | tee -a "$LOG_FILE"
echo "目标: $PROJECT_DIR/lingflow" | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

python -c "
from lingflow.self_optimizer import quick_optimize
from pathlib import Path
import json
from datetime import datetime

# 运行优化
result = quick_optimize(
    target='lingflow',
    goal='structure',
    async_mode=False
)

# 保存报告
report = {
    'timestamp': datetime.now().isoformat(),
    'violations': result.best_score,
    'experiments': result.experiments,
    'best_params': result.best_params,
    'duration': result.duration
}

report_file = Path('$REPORT_DIR') / f'autonomous_optimization_{datetime.now():%Y%m%d_%H%M%S}.json'
report_file.parent.mkdir(parents=True, exist_ok=True)

with open(report_file, 'w') as f:
    json.dump(report, f, indent=2)

print(f'违规数: {result.best_score}')
print(f'实验次数: {result.experiments}')
print(f'报告保存: {report_file}')
" 2>&1 | tee -a "$LOG_FILE"

# 检查是否需要警告
VIOLATIONS=$(tail -n 20 "$LOG_FILE" | grep "违规数:" | awk '{print $2}')
THRESHOLD=20

if [ ! -z "$VIOLATIONS" ] && [ $(echo "$VIOLATIONS > $THRESHOLD" | bc -l) -eq 1 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "⚠️  警告: 违规数 ($VIOLATIONS) 超过阈值 ($THRESHOLD)" | tee -a "$LOG_FILE"
    echo "建议: 立即检查代码质量并重构问题模块" | tee -a "$LOG_FILE"
fi

# 完成信息
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "优化完成时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "日志文件: $LOG_FILE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
