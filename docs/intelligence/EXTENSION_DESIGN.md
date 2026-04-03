# LingFlow 情报系统扩展设计方案

**版本**: v1.0
**日期**: 2026-04-03
**目标**: 增加情报收集节点 + 收集网络对LingFlow的评价

---

## 一、现状分析

### 当前情报系统

```
┌─────────────────────────────────────────────────┐
│  现有情报采集 (被动发现)                         │
├─────────────────────────────────────────────────┤
│  • GitHub Trend Collector  - GitHub项目趋势      │
│  • NPM Trend Collector    - npm包趋势           │
│  • Relevance Analyzer      - 相关性分析           │
│  • Trend Reporter         - 报告生成             │
└─────────────────────────────────────────────────┘
```

**采集内容**: 竞品/相关项目的技术信息
**采集对象**: GitHub仓库、npm包
**采集方式**: 搜索关键词 → API获取 → 本地分析

---

## 二、扩展目标

### 2.1 新增情报收集节点

```
现有关注: 竞品/相关项目技术信息
↓ 扩展
新增关注: LingFlow自身的网络评价与讨论
```

### 2.2 核心需求

| 需求 | 优先级 | 说明 |
|------|--------|------|
| **GitHub Issues监控** | P0 | 收集github.com/guangda88/LingFlow的Issues |
| **GitHub Discussions** | P0 | 收集LingFlow相关 Discussions |
| **Reddit 讨论** | P1 | r/Python, r/LocalLLaMA 等社区 |
| **Hacker News** | P1 | HN上的讨论和评价 |
| **中文社区** | P2 | 掘金、知乎、V2EX等 |
| **Star/Fork 追踪** | P0 | 用户增长趋势分析 |

---

## 三、设计方案

### 3.1 新增采集器架构

```
lingflow/intelligence/
├── collectors/
│   ├── __init__.py
│   ├── base.py              # 基础采集器
│   ├── github_trends.py     # 现有: GitHub项目趋势
│   ├── lingflow_monitor.py  # 🆕 LingFlow自身监控
│   ├── social_media.py      # 🆕 社交媒体采集
│   └── star_tracker.py      # 🆕 Star增长追踪
├── analyzers/
│   ├── __init__.py
│   ├── relevance.py         # 现有: 相关性分析
│   ├── sentiment.py          # 🆕 情感分析
│   └── trend.py             # 🆕 趋势分析
├── reporters/
│   ├── __init__.py
│   ├── trends.py            # 现有: 趋势报告
│   ├── lingflow_reputation.py # 🆕 LingFlow声誉报告
│   └── summary.py           # 🆕 每日汇总
└── storage/
    ├── __init__.py
    ├── json_db.py           # JSON存储
    └── sqlite_db.py          # SQLite存储
```

### 3.2 数据模型

#### 3.2.1 原始数据模型

```python
@dataclass
class MentionData:
    """提及数据模型"""
    platform: str          # 平台名称 (github/reddit/hn)
    source_type: str       # 来源类型 (issue/discussion/post/comment)
    source_id: str         # 来源唯一ID
    author: str            # 作者
    content: str           # 内容
    url: str              # 链接
    published_at: datetime # 发布时间
    collected_at: datetime # 采集时间
    metrics: Dict         # 指标 (stars/replies/etc)
```

#### 3.2.2 分析结果模型

```python
@dataclass
class ReputationMetrics:
    """声誉指标模型"""
    period: str            # 统计周期
    total_mentions: int    # 总提及次数
    sentiment_score: float # 情感分数 (-1 到 1)
    star_growth: int       # Star增长数
    new_stars: List[str]   # 新Star用户
    top_issues: List      # 热门议题
```

---

## 四、具体实现

### 4.1 LingFlow 自身监控

#### GitHub Issues/Discussions 采集

```python
class LingFlowMonitor:
    """LingFlow项目监控器"""

    def __init__(self, repo: str = "guangda88/LingFlow"):
        self.repo = repo
        self.token = os.getenv('GITHUB_TOKEN')

    def collect_issues(self, state: str = "open") -> List[Issue]:
        """采集Issues"""
        # GET /repos/{owner}/{repo}/issues
        # 关注标签: enhancement, bug, question, discussion

    def collect_discussions(self) -> List[Discussion]:
        """采集Discussions"""
        # GET /repos/{owner}/{repo}/discussions
```

#### Star 增长追踪

```python
class StarTracker:
    """Star增长追踪器"""

    def collect_stargazers(self, since: datetime) -> List[Stargazer]:
        """采集新增Star用户"""
        # GET /repos/{owner}/{repo}/stargazers
        # 对比历史数据，计算增量
```

### 4.2 社交媒体采集

#### Reddit 采集

```python
class RedditCollector:
    """Reddit讨论采集器"""

    def __init__(self):
        # 使用 Reddit API (无需认证只读)
        self.subreddits = ["Python", "LocalLLaMA", "learnprogramming"]

    def search_mentions(self, keyword: str = "LingFlow") -> List[Post]:
        """搜索提及LingFlow的帖子"""
        # 使用Reddit搜索API或rss2json
```

#### Hacker News 采集

```python
class HNCollector:
    """Hacker News采集器"""

    def search_mentions(self, keyword: str = "LingFlow") -> List[Post]:
        """搜索提及LingFlow的帖子"""
        # 使用 Algolia API (HN搜索)
        # https://hn.algolia.com/api/v1/search
```

### 4.3 情感分析

```python
class SentimentAnalyzer:
    """情感分析器"""

    def analyze(self, text: str) -> Dict:
        """分析文本情感"""
        # 简单规则基线:
        # - 正面词: good, great, awesome, useful, powerful
        # - 负面词: bad, broken, slow, buggy, useless
        # - 扩展: 使用 TextBlob 或 VADER
```

---

## 五、实现计划

### Phase 1: 基础监控 (1周)

| # | 任务 | 产出 |
|---|------|------|
| 1.1 | 创建 `lingflow/intelligence/` 目录 | 基础架构 |
| 1.2 | 实现 `LingFlowMonitor` | GitHub Issues/Discussions采集 |
| 1.3 | 实现 `StarTracker` | Star增长追踪 |
| 1.4 | 每日报告脚本 | crontab 定时运行 |

### Phase 2: 社交媒体 (1周)

| # | 任务 | 产出 |
|---|------|------|
| 2.1 | 实现 `RedditCollector` | Reddit帖子采集 |
| 2.2 | 实现 `HNCollector` | Hacker News采集 |
| 2.3 | 实现 `SentimentAnalyzer` | 简单情感分析 |
| 2.4 | 整合到现有情报系统 | 统一入口 |

### Phase 3: 报告与可视化 (2周)

| # | 任务 | 产出 |
|---|------|------|
| 3.1 | `LingFlowReputationReport` | 声誉报告生成 |
| 3.2 | 趋势图表 | Star/提及/情感趋势 |
| 3.3 | MCP 工具集成 | 灵探增强 |

---

## 六、MCP 工具集成

### 新增工具

| 中文名 | 工具名称 | 功能 |
|--------|----------|------|
| 灵听 | `get_lingflow_mentions` | 获取关于LingFlow的提及 |
| 灵誉 | `get_reputation_metrics` | 获取声誉指标 |
| 灵感 | `analyze_sentiment` | 分析讨论情感 |
| 灵脉 | `get_star_trends` | 获取Star趋势 |
| 灵议 | `get_top_issues` | 获取热门议题 |

---

## 七、技术约束

### 7.1 API 限制

| 平台 | 限制 | 绕过方案 |
|------|------|----------|
| GitHub | 5000 req/hour (认证) | Token + 缓存 |
| Reddit | 100 req/min | 限制请求频率 |
| HN (Algolia) | 无硬限制 | 合理使用 |

### 7.2 数据存储

```bash
.lingflow/intelligence/
├── raw/                   # 原始数据
│   ├── github/          # GitHub数据
│   ├── reddit/           # Reddit数据
│   └── hn/               # HN数据
├── analyzed/             # 分析结果
│   ├── daily/            # 每日汇总
│   └── trends/           # 趋势数据
└── reports/              # 报告
    ├── reputation/       # 声誉报告
    └── summaries/        # 每周汇总
```

---

## 八、预期效果

### 8.1 每日情报

```
📊 LingFlow 情报简报 - 2026-04-03

📈 今日统计:
  - GitHub Issues: 3 个新增
  - Discussions: 2 个新增
  - Reddit 提及: 5 次
  - Hacker News: 0 次
  - 新增 Stars: 12 个

💬 情感分析:
  - 正面: 65%
  - 中性: 30%
  - 负面: 5%

🔥 热门议题:
  1. "LingFlow 与 Cursor 对比"
  2. "自优化系统效果如何?"
  3. "MCP 集成教程请求"
```

### 8.2 趋势洞察

- **Star增长曲线**: 每周增长趋势
- **情感变化**: 社区态度演变
- **热门功能**: 用户最讨论的功能
- **竞品对比**: 与其他工具的讨论对比

---

## 九、风险与缓解

| 风险 | 缓解 |
|------|------|
| API 限流 | 缓存 + 分散请求时间 |
| 数据量过大 | 只保留30天数据 |
| 隐私问题 | 只采集公开数据 |
| 情感准确性 | 持续优化分析模型 |

---

**设计完成**: 2026-04-03
**下一步**: Phase 1 实现
