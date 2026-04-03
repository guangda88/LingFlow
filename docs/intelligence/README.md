# LingFlow 情报系统

智能采集、分析、报告LingFlow相关的网络情报。

## 系统架构

```
lingflow/intelligence/
├── collectors/           # 采集器
│   ├── base.py          # 基础采集器抽象类
│   ├── lingflow_monitor.py  # GitHub Issues/Discussions/Releases
│   ├── star_tracker.py  # Star增长追踪
│   ├── reddit.py        # Reddit讨论采集
│   └── hackernews.py    # Hacker News采集
├── analyzers/           # 分析器
│   ├── base.py          # 基础分析器抽象类
│   ├── sentiment.py     # 情感分析
│   └── influence.py     # 影响力评分
├── reporters/           # 报告生成器
│   └── daily.py         # 每日简报
└── models/              # 数据模型
    └── common.py        # 通用模型定义
```

## 快速开始

### 1. 运行完整情报流程

```bash
# 运行完整流程 (采集 + 分析 + 报告)
python scripts/intelligence_pipeline.py

# 采集最近3天数据
python scripts/intelligence_pipeline.py --days 3

# 禁用特定采集器
python scripts/intelligence_pipeline.py --no-reddit
```

### 2. 单独使用组件

#### 采集数据

```python
from lingflow.intelligence.collectors import (
    LingFlowMonitor,
    RedditCollector,
    HNCollector,
)

# GitHub采集
monitor = LingFlowMonitor()
issues = monitor.collect_issues(state="open", days=7)
discussions = monitor.collect_discussions(days=7)

# Reddit采集
reddit = RedditCollector()
mentions = reddit.search_mentions(
    keywords=["LingFlow"],
    limit=100,
    days=7
)

# Hacker News采集
hn = HNCollector()
mentions = hn.search_mentions(
    keywords=["LingFlow"],
    limit=100,
    days=7
)
```

#### 分析数据

```python
from lingflow.intelligence.analyzers import (
    SentimentAnalyzer,
    InfluenceAnalyzer,
    AnalyzerPipeline,
)

# 情感分析
sentiment = SentimentAnalyzer()
result = sentiment.analyze("LingFlow is awesome!")

# 影响力分析
influence = InfluenceAnalyzer()
score = influence.calculate_score(mention)

# 批量分析
pipeline = AnalyzerPipeline([
    SentimentAnalyzer(),
    InfluenceAnalyzer(),
])
results = pipeline.run(mentions)
```

#### 生成报告

```python
from lingflow.intelligence.reporters import DailyReporter

reporter = DailyReporter()
report = reporter.generate(
    mentions=mentions,
    star_growth=15,
    star_count=245
)

# 输出终端
print(report.format_terminal())

# 保存文件
reporter.save(report, format="markdown")
```

## 数据模型

### MentionData - 提及数据

```python
@dataclass
class MentionData:
    platform: Platform      # 平台
    source_type: SourceType # 来源类型
    source_id: str          # 唯一ID
    author: str             # 作者
    content: str            # 内容
    url: str                # 链接
    published_at: str       # 发布时间
    # ... 更多字段
```

### DailyReport - 每日报告

```python
@dataclass
class DailyReport:
    date: str
    summary: str
    metrics: Dict[str, Any]
    highlights: List[str]
    concerns: List[str]
    sentiment_summary: Dict
    top_topics: List[str]
    actionable_insights: List[str]
```

## 输出报告示例

```
╔════════════════════════════════════════════════════════════╗
║        📊 LingFlow 情报简报 - 2026-04-03                   ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  📋 摘要                                                  ║
║    今日共收录 15 条讨论，Star增长 +12，社区情感积极。     ║
║                                                            ║
║  📈 今日统计                                               ║
║    • 总提及: 15 条                                         ║
║    • github: 8 条                                          ║
║    • reddit: 5 条                                          ║
║    • hackernews: 2 条                                      ║
║    • Star增长: +12                                         ║
║                                                            ║
║  💬 情感分析                                               ║
║    积极: 65%                                               ║
║    中性: 30%                                               ║
║    消极: 5%                                                ║
║                                                            ║
║  🔥 热门话题                                               ║
║    1. automation                                           ║
║    2. lingflow                                             ║
║    3. installation                                         ║
║                                                            ║
║  ✅ 亮点                                                  ║
║    • "LingFlow: The Future of Automation" (150👍)          ║
║    • "Best tool for AI automation" (45👍)                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

## 定时任务设置

### 使用 crontab

```bash
# 编辑 crontab
crontab -e

# 添加以下行 (每天早上8点运行)
0 8 * * * cd /path/to/LingFlow && python scripts/intelligence_pipeline.py >> .lingflow/logs/intelligence.log 2>&1
```

### 使用 systemd timer

创建 `~/.config/systemd/user/lingflow-intelligence.service`:

```ini
[Unit]
Description=LingFlow Intelligence System
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/path/to/LingFlow
ExecStart=/usr/bin/python3 scripts/intelligence_pipeline.py
```

创建 `~/.config/systemd/user/lingflow-intelligence.timer`:

```ini
[Unit]
Description=LingFlow Intelligence Timer

[Timer]
OnCalendar=daily
OnCalendar=08:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用服务:

```bash
systemctl --user daemon-reload
systemctl --user enable lingflow-intelligence.timer
systemctl --user start lingflow-intelligence.timer
```

## 数据存储

```
.lingflow/intelligence/
├── raw/                    # 原始采集数据
│   ├── github/            # GitHub数据
│   ├── reddit/            # Reddit数据
│   ├── hackernews/        # HN数据
│   └── stars/             # Star历史
├── analyzed/              # 分析结果
│   ├── sentiment/         # 情感分析
│   └── influence/         # 影响力分析
└── reports/               # 报告
    ├── daily/             # 每日简报
    └── weekly/            # 周报
```

## 扩展开发

### 添加新采集器

```python
from lingflow.intelligence.collectors.base import BaseCollector
from lingflow.intelligence.models.common import MentionData, Platform

class MyCollector(BaseCollector):
    PLATFORM = Platform.MYPLATFORM
    NAME = "mycollector"

    def collect(self, **kwargs) -> list[MentionData]:
        # 实现采集逻辑
        pass
```

### 添加新分析器

```python
from lingflow.intelligence.analyzers.base import BaseAnalyzer

class MyAnalyzer(BaseAnalyzer):
    NAME = "myanalyzer"

    def analyze(self, mentions, **kwargs):
        # 实现分析逻辑
        pass
```

## 配置

### 环境变量

```bash
# GitHub Token (提高API限制)
export GITHUB_TOKEN=your_token_here

# Reddit App credentials (可选)
export REDDIT_CLIENT_ID=your_client_id
export REDDIT_CLIENT_SECRET=your_client_secret
```

### 配置文件

```yaml
# .lingflow/intelligence/config.yaml
intelligence:
  repo: "guangda88/LingFlow"

  collectors:
    github:
      enabled: true
      schedule: "0 */6 * * *"
    reddit:
      enabled: true
      schedule: "0 */12 * * *"
    hackernews:
      enabled: true
      schedule: "0 */12 * * *"

  reporters:
    daily:
      enabled: true
      schedule: "0 8 * * *"
```

## 参考文档

- [扩展设计方案 v2.0](EXTENSION_PLAN_V2.md)
- [原始扩展设计](EXTENSION_DESIGN.md)
- [GitHub Trend设置](../reports/github_trends/GITHUB_TOKEN_SETUP.md)

## 版本历史

- v2.0 (2026-04-03): 完整的情报系统，支持多平台采集和分析
- v1.0 (2026-04-01): GitHub Trend Intelligence MVP
