# intel-pipeline

## 描述
lingflow 情报系统统一管线。编排 Star 追踪 → 多平台采集 → 分析 → 报告生成全流程。
支持独立运行或注册到 LingScheduler 定时调度。

## 参数

| 参数 | 类型 | 必选 | 默认值 | 说明 |
|------|------|------|--------|------|
| days | int | 否 | 1 | 采集回溯天数 |
| enable_github | bool | 否 | true | 启用 GitHub 采集 |
| enable_reddit | bool | 否 | true | 启用 Reddit 采集 |
| enable_hn | bool | 否 | true | 启用 HN 采集 |
| enable_stars | bool | 否 | true | 启用 Star 追踪 |
| collect_only | bool | 否 | false | 仅采集，跳过分析和报告 |
| dry_run | bool | 否 | false | 仅返回预估，不执行任何采集 |
| schedule | string | 否 | "" | 注册定时调度（cron 格式 "HH:MM"），空字符串=不注册 |
| report_formats | list | 否 | ["txt","json","markdown"] | 报告输出格式 |

## 输出
```json
{
  "phase": "complete",
  "mentions_count": 42,
  "star_count": 1200,
  "star_growth": 5,
  "analysis": {
    "sentiment": {"positive": 30, "neutral": 10, "negative": 2},
    "influence": {"avg_score": 45.2, "high_influence": 3}
  },
  "reports": ["path/to/report.txt", "path/to/report.json"],
  "elapsed_seconds": 12.5,
  "scheduler_task_id": null
}
```

## 依赖
- lingflow.intelligence (collectors, analyzers, reporters)
- lingflow.scheduler (可选，仅 schedule 参数非空时)
