#!/bin/bash
# LingFlow 定期自优化脚本 - 简化版
# 建议通过cron定期运行

set -e

# 脚本目录和项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/.lingflow/logs"
REPORT_DIR="$PROJECT_DIR/.lingflow/reports"

# 创建必要目录
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/optimization_$(date +%Y%m%d_%H%M%S).log"

# 日志函数
log() {
    echo "$@" | tee -a "$LOG_FILE"
}

log "========================================"
log "LingFlow 定期自优化"
log "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
log "========================================"

# 激活虚拟环境（如果存在）
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    log "激活虚拟环境..."
    source "$PROJECT_DIR/venv/bin/activate"
fi

# 进入项目目录
cd "$PROJECT_DIR"

# 运行优化
log ""
log "运行LingMinOpt优化..."
log "目标: $PROJECT_DIR/lingflow"

# 使用Python直接运行优化，避免shell变量问题
python << 'PYTHON_SCRIPT'
import sys
from pathlib import Path
import json
from datetime import datetime

try:
    from lingflow.self_optimizer import quick_optimize

    # 运行优化
    result = quick_optimize(
        target='lingflow',
        goal='structure',
        async_mode=False
    )

    # 准备报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'violations': float(result.best_score),
        'experiments': result.experiments,
        'best_params': result.best_params,
        'duration': result.duration,
        'status': 'success'
    }

except Exception as e:
    # 错误处理
    report = {
        'timestamp': datetime.now().isoformat(),
        'status': 'error',
        'error': str(e),
        'violations': -1
    }
    print(f"错误: {e}", file=sys.stderr)

# 保存报告
report_file = Path('.lingflow/reports') / f'autonomous_optimization_{datetime.now():%Y%m%d_%H%M%S}.json'
report_file.parent.mkdir(parents=True, exist_ok=True)

with open(report_file, 'w') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

# 输出结果
if report['status'] == 'success':
    print(f"✅ 违规数: {report['violations']}")
    print(f"✅ 实验次数: {report['experiments']}")
    print(f"✅ 耗时: {report['duration']:.2f}秒")
    print(f"✅ 报告: {report_file}")
else:
    print(f"❌ 优化失败: {report.get('error', 'Unknown error')}")
    sys.exit(1)

PYTHON_SCRIPT

# 检查结果
if [ $? -eq 0 ]; then
    # 提取违规数
    VIOLATIONS=$(tail -n 20 "$LOG_FILE" | grep "违规数:" | tail -1 | awk '{print $2}')
    THRESHOLD=20

    if [ ! -z "$VIOLATIONS" ] && [ $(echo "$VIOLATIONS > $THRESHOLD" | bc -l 2>/dev/null || echo 0) -eq 1 ]; then
        log ""
        log "⚠️  警告: 违规数 ($VIOLATIONS) 超过阈值 ($THRESHOLD)"
        log "建议: 立即检查代码质量并重构问题模块"
    fi

    log ""
    log "========================================"
    log "优化完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    log "日志文件: $LOG_FILE"
    log "========================================"
else
    log ""
    log "❌ 优化失败，请检查日志"
    exit 1
fi
