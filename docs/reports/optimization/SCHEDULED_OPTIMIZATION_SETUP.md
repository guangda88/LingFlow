# lingflow 定期优化设置指南

> **自动化代码质量优化系统**
> **设置日期**: 2026-04-01
> **状态**: ✅ 已配置并测试

---

## 📊 概述

lingflow自优化系统现已配置为定期自动运行，使用lingminopt框架持续优化代码质量。

### 已配置的任务

```bash
# 每周一凌晨2点自动运行优化
0 2 * * 1 /home/ai/lingflow/scripts/run_optimization_simple.sh
```

**特点**:
- ✅ 自动化执行：无需手动触发
- ✅ 完整日志：所有运行记录保存到 `.lingflow/logs/`
- ✅ 报告生成：每次优化生成JSON报告到 `.lingflow/reports/`
- ✅ 错误处理：失败时记录错误信息
- ✅ 阈值警告：违规数超过20时发出警告

---

## 🚀 快速开始

### 手动运行优化

```bash
# 方式1: 使用简化脚本（推荐）
/home/ai/lingflow/scripts/run_optimization_simple.sh

# 方式2: 使用Python脚本
python /home/ai/lingflow/run_self_optimization.py

# 方式3: 直接在代码中调用
python -c "from lingflow.self_optimizer import quick_optimize; quick_optimize('lingflow', 'structure')"
```

### 查看优化结果

```bash
# 查看最新报告
ls -lt .lingflow/reports/autonomous_optimization_*.json | head -1

# 查看报告内容
cat .lingflow/reports/autonomous_optimization_*.json | tail -1 | jq '.'

# 查看最新日志
ls -lt .lingflow/logs/optimization_*.log | head -1

# 查看日志内容
tail -50 .lingflow/logs/optimization_*.log | tail -1
```

---

## 📅 Crontab管理

### 查看当前配置

```bash
crontab -l
```

输出示例:
```
# lingflow 定期自优化（每周一凌晨2点执行）
0 2 * * 1 /home/ai/lingflow/scripts/run_optimization_simple.sh
```

### 修改优化时间

```bash
# 编辑crontab
crontab -e

# 修改时间格式:
# 分 时 日 月 周 命令
# 0  2  *  *  1  /home/ai/lingflow/scripts/run_optimization_simple.sh
# │  │  │  │  │
# │  │  │  │  └─── 星期几 (0-7, 0和7都是周日)
# │  │  │  └────── 月份 (1-12)
# │  │  └───────── 日期 (1-31)
# │  └──────────── 小时 (0-23)
# └─────────────── 分钟 (0-59)
```

**常用时间设置**:

```bash
# 每天凌晨2点
0 2 * * * /home/ai/lingflow/scripts/run_optimization_simple.sh

# 每周一凌晨2点（当前配置）
0 2 * * 1 /home/ai/lingflow/scripts/run_optimization_simple.sh

# 每周日凌晨3点
0 3 * * 0 /home/ai/lingflow/scripts/run_optimization_simple.sh

# 每月1日凌晨2点
0 2 1 * * /home/ai/lingflow/scripts/run_optimization_simple.sh

# 每小时（仅用于测试，不推荐生产环境）
0 * * * * /home/ai/lingflow/scripts/run_optimization_simple.sh

# 每6小时
0 */6 * * * /home/ai/lingflow/scripts/run_optimization_simple.sh
```

### 禁用定期优化

```bash
# 方式1: 注释掉crontab行
crontab -e
# 在命令前加 #:
# 0 2 * * 1 /home/ai/lingflow/scripts/run_optimization_simple.sh

# 方式2: 删除crontab行
crontab -e
# 删除整行

# 方式3: 临时禁用（不删除配置）
mv /home/ai/lingflow/scripts/run_optimization_simple.sh \
   /home/ai/lingflow/scripts/run_optimization_simple.sh.disabled
```

### 删除Crontab配置

```bash
# 删除所有crontab配置（谨慎使用！）
crontab -r

# 删除lingflow配置行
crontab -l | grep -v "lingflow" | crontab -
```

---

## 📈 监控和分析

### 查看优化历史

```bash
# 查看所有报告
ls -lh .lingflow/reports/autonomous_optimization_*.json

# 查看最新5次优化
ls -lt .lingflow/reports/autonomous_optimization_*.json | head -5

# 查看违规数趋势
for file in .lingflow/reports/autonomous_optimization_*.json; do
    timestamp=$(jq -r '.timestamp' "$file")
    violations=$(jq -r '.violations' "$file")
    echo "$timestamp: $violations 个违规"
done | sort
```

### 分析优化效果

```python
import json
from pathlib import Path

reports_dir = Path(".lingflow/reports")
reports = sorted(reports_dir.glob("autonomous_optimization_*.json"))

print("📊 lingflow 优化历史\n")
print("=" * 70)

for report_file in reports:
    with open(report_file) as f:
        data = json.load(f)

    timestamp = data['timestamp']
    violations = data.get('violations', 'N/A')
    experiments = data.get('experiments', 'N/A')
    duration = data.get('duration', 'N/A')

    print(f"时间: {timestamp}")
    print(f"违规数: {violations}")
    print(f"实验次数: {experiments}")
    print(f"耗时: {duration}秒")
    print("-" * 70)
```

### 绘制趋势图

```python
import json
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

# 读取所有报告
reports_dir = Path(".lingflow/reports")
reports = []
for report_file in reports_dir.glob("autonomous_optimization_*.json"):
    with open(report_file) as f:
        data = json.load(f)
        reports.append(data)

# 按时间排序
reports.sort(key=lambda x: x['timestamp'])

# 提取数据
timestamps = [datetime.fromisoformat(r['timestamp']) for r in reports]
violations = [r.get('violations', 0) for r in reports]

# 绘图
plt.figure(figsize=(12, 6))
plt.plot(timestamps, violations, marker='o', linewidth=2, markersize=8)
plt.xlabel('优化时间', fontsize=12)
plt.ylabel('违规数量', fontsize=12)
plt.title('lingflow 代码质量优化趋势', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# 保存图表
chart_path = '.lingflow/reports/optimization_trend.png'
plt.savefig(chart_path, dpi=300, bbox_inches='tight')
print(f"✅ 趋势图已保存: {chart_path}")
```

---

## 🔧 故障排除

### 问题1: Crontab任务没有运行

**检查步骤**:

```bash
# 1. 确认crontab配置
crontab -l | grep lingflow

# 2. 检查cron服务状态
sudo systemctl status cron

# 3. 查看cron日志
sudo tail -f /var/log/syslog | grep CRON

# 4. 手动测试脚本
/home/ai/lingflow/scripts/run_optimization_simple.sh
```

**常见原因**:
- 脚本没有执行权限: `chmod +x /home/ai/lingflow/scripts/run_optimization_simple.sh`
- 路径使用~而不是绝对路径: 使用完整路径 `/home/ai/lingflow`
- 虚拟环境激活失败: 检查venv路径是否正确

### 问题2: 优化失败

**检查日志**:

```bash
# 查看最新日志
tail -100 .lingflow/logs/optimization_*.log | tail -1

# 查看错误信息
grep -i "error\|错误\|失败" .lingflow/logs/optimization_*.log | tail -1
```

**常见错误**:

1. **ModuleNotFoundError**: 缺少依赖
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **权限错误**: 无法写入报告目录
   ```bash
   chmod 755 .lingflow/reports
   ```

3. **ImportError**: 模块路径问题
   ```bash
   cd /home/ai/lingflow
   python -c "from lingflow.self_optimizer import quick_optimize"
   ```

### 问题3: 违规数异常

**检查代码库**:

```bash
# 运行详细分析
python -c "
from lingflow.self_optimizer import quick_optimize
result = quick_optimize('lingflow', 'structure', async_mode=False)
print(f'违规数: {result.best_score}')
print(f'最佳参数: {result.best_params}')
"
```

---

## 📊 性能指标

### 优化效率

根据历史数据:

```
平均违规数: 6-14
优化时间: 0-8秒
实验次数: 20次
改进幅度: 90% (从60→6)
```

### 资源占用

```
CPU使用: 低 (贝叶斯优化)
内存占用: <100MB
磁盘占用: 每次报告~1KB
```

---

## 🎯 最佳实践

### 1. 定期检查

```bash
# 每周查看优化报告
ls -lt .lingflow/reports/autonomous_optimization_*.json | head -1 | xargs cat | jq '.'

# 每月分析趋势
python scripts/analyze_optimization_trends.py
```

### 2. 阈值调整

编辑脚本，修改违规数阈值:

```bash
# 编辑脚本
vim /home/ai/lingflow/scripts/run_optimization_simple.sh

# 修改阈值（默认20）
THRESHOLD=15  # 更严格的阈值
```

### 3. 通知设置

添加邮件通知（可选）:

```bash
# 编辑脚本，添加邮件发送
if [ $VIOLATIONS -gt $THRESHOLD ]; then
    echo "警告: 违规数超过阈值" | mail -s "lingflow优化警告" your@email.com
fi
```

### 4. 备份报告

```bash
# 创建备份目录
mkdir -p /backup/lingflow/optimization

# 定期备份报告
cp -r .lingflow/reports/* /backup/lingflow/optimization/
```

---

## 🔄 升级和维护

### 更新优化脚本

```bash
# 备份当前脚本
cp /home/ai/lingflow/scripts/run_optimization_simple.sh \
   /home/ai/lingflow/scripts/run_optimization_simple.sh.backup

# 编辑脚本
vim /home/ai/lingflow/scripts/run_optimization_simple.sh

# 测试脚本
/home/ai/lingflow/scripts/run_optimization_simple.sh
```

### 更新lingminopt参数

```python
# 编辑配置文件
vim .lingflow/config/quality_gates.yaml

# 或在代码中更新默认参数
vim lingflow/self_optimizer/optimizer.py
```

---

## 📚 相关文档

- **LINGFLOW_AUTO_OPTIMIZATION_GUIDE.md**: 自动优化使用指南
- **FINAL_IMPROVEMENT_SUMMARY.md**: 完整改进总结
- **SESSION_V2_INTEGRATION_GUIDE.md**: Session v2集成指南
- **LINGMINOPT_QUICK_START.md**: lingminopt快速启动

---

## 📋 快速参考

### 常用命令

```bash
# 手动运行优化
/home/ai/lingflow/scripts/run_optimization_simple.sh

# 查看crontab
crontab -l

# 编辑crontab
crontab -e

# 查看最新报告
cat .lingflow/reports/autonomous_optimization_*.json | tail -1 | jq '.'

# 查看最新日志
tail -50 .lingflow/logs/optimization_*.log | tail -1

# 查看优化历史
ls -lt .lingflow/reports/autonomous_optimization_*.json | head -5
```

### 文件位置

```
脚本: /home/ai/lingflow/scripts/run_optimization_simple.sh
日志: .lingflow/logs/optimization_*.log
报告: .lingflow/reports/autonomous_optimization_*.json
配置: .lingflow/config/quality_gates.yaml
```

---

## 🎉 总结

### 配置完成

✅ **定期优化已配置**: 每周一凌晨2点自动运行
✅ **完整日志记录**: 所有运行结果保存
✅ **报告自动生成**: JSON格式，易于分析
✅ **错误处理**: 失败时记录详细信息
✅ **阈值警告**: 超过阈值时发出警告

### 下一步

1. **验证配置**: 等待下次定期运行或手动测试
2. **监控结果**: 定期查看优化报告
3. **调整参数**: 根据需要调整优化频率和阈值
4. **持续改进**: 根据优化结果重构代码

---

**版本**: v1.0
**配置日期**: 2026-04-01
**状态**: ✅ 生产就绪
**下次运行**: 下周一凌晨2点

🎯 **lingflow持续优化，持续改进！**
