# LingFlow 用户反馈系统指南

## 概述

LingFlow 用户反馈系统提供了完整的用户问题收集、跟踪和管理功能，帮助用户方便地报告问题并获得优化。

## 功能特性

### 1. 多渠道反馈入口

| 渠道 | 命令 | 说明 |
|------|------|------|
| CLI 命令 | `lingflow feedback submit` | 提交通用反馈 |
| CLI 快捷命令 | `lingflow feedback bug` | 快捷提交 Bug 报告 |
| 编程接口 | `submit_bug()` | 在代码中提交 |

### 2. 反馈类别

- `bug` - Bug 报告
- `feature` - 功能请求
- `improvement` - 改进建议
- `performance` - 性能问题
- `documentation` - 文档问题
- `usability` - 易用性问题
- `other` - 其他问题

### 3. 严重性级别

- `low` - 低优先级
- `medium` - 中等优先级
- `high` - 高优先级
- `critical` - 严重问题

## 使用方法

### CLI 命令使用

#### 提交 Bug 报告

```bash
# 基础 Bug 报告
lingflow feedback bug \
  --title "技能执行失败" \
  --description "执行 code-review 技能时出现错误"

# 指定严重性
lingflow feedback bug \
  --title "内存泄漏" \
  --description "长时间运行后内存占用持续增长" \
  --severity high
```

#### 提交通用反馈

```bash
# 功能请求
lingflow feedback submit \
  --title "希望支持更多编程语言" \
  --description "希望能增加对 Go 和 Rust 的支持" \
  --category feature \
  --severity medium

# 文档问题
lingflow feedback submit \
  --title "API 文档缺少示例" \
  --description "某些技能的 API 文档缺少使用示例" \
  --category documentation \
  --severity low
```

#### 查看反馈列表

```bash
# 查看所有反馈
lingflow feedback list

# 按类别过滤
lingflow feedback list --category bug

# 按状态过滤
lingflow feedback list --status open

# 限制返回数量
lingflow feedback list --limit 10
```

#### 查看反馈详情

```bash
lingflow feedback show <feedback_id>
```

#### 解决反馈

```bash
lingflow feedback resolve <feedback_id> \
  --resolution "已修复：更新了相关代码"
```

#### 导出反馈报告

```bash
lingflow feedback export --output feedback_report.md
```

#### 查看统计信息

```bash
lingflow feedback stats
```

### 编程接口使用

```python
from lingflow.feedback import (
    get_feedback_collector,
    FeedbackCategory,
    FeedbackSeverity,
    submit_bug,
)

# 快捷提交 Bug
feedback = submit_bug(
    title="技能加载失败",
    description="无法加载 custom-skill",
    reproduction_steps=[
        "1. 创建自定义技能",
        "2. 尝试加载技能",
        "3. 收到加载失败错误"
    ]
)
print(f"反馈 ID: {feedback.id}")

# 详细反馈提交
collector = get_feedback_collector()
feedback = collector.submit_feedback(
    category=FeedbackCategory.FEATURE,
    severity=FeedbackSeverity.MEDIUM,
    title="支持并行执行",
    description="希望能支持多个技能的并行执行",
    user="user123",
    email="user@example.com",
)

# 查询反馈
open_bugs = collector.get_feedbacks(
    category=FeedbackCategory.BUG,
    status="open",
    limit=10
)

# 获取统计
stats = collector.get_statistics()
print(f"总计: {stats['total']}, 待处理: {stats['open']}")
```

### 自动错误捕获

```python
import sys
from lingflow.feedback import submit_bug

def main():
    try:
        # 你的代码
        run_application()
    except Exception as e:
        # 自动捕获并上报错误
        submit_bug(
            title=f"未捕获的异常: {type(e).__name__}",
            description=str(e),
            stack_trace=__import__('traceback').format_exc()
        )
        raise
```

## 反馈状态流转

```
open → in_progress → resolved → closed
  ↓        ↓
 └────→ closed (直接关闭)
```

- `open` - 新提交的反馈
- `in_progress` - 正在处理中
- `resolved` - 已解决
- `closed` - 已关闭

## 反馈存储

反馈数据存储在 `.lingflow/feedback/feedbacks.json` 文件中，包含：

- 反馈 ID
- 类别和严重性
- 标题和描述
- 复现步骤
- 环境信息
- 堆栈跟踪
- 状态和解决方案

## 集成运维监控

反馈系统与 LingFlow 的运维监控系统深度集成：

```python
from lingflow.monitoring import get_operations_monitor, add_alert_rule
from lingflow.feedback import submit_bug
from lingflow.monitoring.operations_monitor import AlertSeverity

# 将告警自动转化为 Bug 报告
def auto_submit_bug_handler(alert):
    if alert.severity == AlertSeverity.CRITICAL:
        submit_bug(
            title=f"自动报告: {alert.source}",
            description=alert.message,
            severity=FeedbackSeverity.HIGH,
        )

monitor = get_operations_monitor()
monitor.add_notification_handler(auto_submit_bug_handler)
```

## 最佳实践

### 1. 提交有效的 Bug 报告

- **清晰的标题**: 简明扼要地描述问题
- **详细的描述**: 说明期望行为和实际行为
- **复现步骤**: 提供可重现问题的步骤
- **环境信息**: 包含 OS、Python 版本等
- **堆栈跟踪**: 附带完整的错误堆栈

### 2. 功能请求建议

- 说明使用场景
- 描述期望的功能
- 分析收益和价值
- 提供可能的实现思路

### 3. 反馈跟踪

- 记录反馈 ID 用于后续跟踪
- 定期查看反馈状态
- 及时提供补充信息
- 确认问题解决后关闭反馈

## 反馈处理流程

1. **收集**: 用户通过 CLI 或 API 提交反馈
2. **分类**: 系统自动分类和标记严重性
3. **分析**: 开发团队分析和评估
4. **处理**: 更新状态为 in_progress
5. **解决**: 修复问题并标记为 resolved
6. **确认**: 用户确认后关闭

## 远程上报配置

```python
from lingflow.feedback import get_feedback_collector

collector = get_feedback_collector()
collector.auto_report = True
collector.report_url = "https://your-server.com/api/feedback"
```

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                   用户反馈系统                            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ CLI 接口    │  │ Python API  │  │ Web UI      │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│           │               │               │             │
│           └───────────────┴───────────────┘             │
│                         ↓                                │
│           ┌─────────────────────────────┐               │
│           │    FeedbackCollector        │               │
│           │  - 收集反馈                 │               │
│           │  - 分类管理                 │               │
│           │  - 状态跟踪                 │               │
│           └─────────────────────────────┘               │
│                         ↓                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │              存储层 (.lingflow/feedback/)       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```
