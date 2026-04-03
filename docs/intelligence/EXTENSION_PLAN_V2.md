# LingFlow 情报系统扩展方案 v2.0

**版本**: v2.0
**日期**: 2026-04-03
**目标**: 完整的情报采集、分析、报告系统

---

## 一、系统现状

### 1.1 已实现组件

```
lingflow/intelligence/
├── collectors/
│   ├── lingflow_monitor.py  ✅ GitHub Issues/Discussions/Releases
│   └── star_tracker.py      ✅ Star增长追踪
└── analyzers/
    └── sentiment.py         ✅ 情感分析
```

### 1.2 数据模型

- `MentionData`: 提及数据（已实现）
- `StargazerData`: Star用户数据（已实现）
- `SentimentResult`: 情感分析结果（已实现）

### 1.3 数据存储

```
.lingflow/intelligence/
├── raw/
│   ├── github/          ✅ GitHub采集数据
│   └── stars/           ✅ Star历史数据
└── reports/
    └── github_trends/   ✅ 趋势报告
```

---

## 二、扩展架构

### 2.1 目标架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    LingFlow 情报系统 v2.0                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ 数据采集层    │ -> │ 分析处理层    │ -> │ 报告呈现层    │     │
│  │ Collectors   │    │ Analyzers    │    │ Reporters    │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                                 │
│  采集源:               分析能力:            输出形式:          │
│  • GitHub             • 情感分析           • 每日简报         │
│  • Reddit             • 趋势分析           • 周报摘要         │
│  • Hacker News        • 话题聚类           • 可视化图表       │
│  • 中文社区           • 影响力评分         • MCP工具          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 新增目录结构

```
lingflow/intelligence/
├── collectors/           # 采集器
│   ├── __init__.py
│   ├── base.py           🆕 基础采集器抽象类
│   ├── lingflow_monitor.py  ✅ 已有
│   ├── star_tracker.py      ✅ 已有
│   ├── reddit.py        🆕 Reddit采集
│   ├── hackernews.py    🆕 HN采集
│   └── domestic.py      🆕 中文社区(掘金/知乎)
├── analyzers/           # 分析器
│   ├── __init__.py
│   ├── base.py          🆕 基础分析器抽象类
│   ├── sentiment.py     ✅ 已有
│   ├── trend.py         🆕 趋势分析
│   ├── topic.py         🆕 话题聚类
│   └── influence.py     🆕 影响力评分
├── reporters/           # 报告生成器
│   ├── __init__.py
│   ├── daily.py         🆕 每日简报
│   ├── weekly.py        🆕 周报摘要
│   ├── visualizer.py    🆕 图表生成
│   └── mcp_report.py    🆕 MCP工具输出
├── storage/             # 存储层
│   ├── __init__.py
│   ├── json_store.py    🆕 JSON存储
│   └── cache.py         🆕 缓存管理
└── models/              # 数据模型
    ├── __init__.py
    └── common.py        🆕 通用模型定义
```

---

## 三、详细设计

### 3.1 新增采集器

#### Reddit Collector

```python
@dataclass
class RedditPost(MentionData):
    """Reddit帖子数据"""
    subreddit: str = ""
    score: int = 0
    upvote_ratio: float = 0.0
    num_comments: int = 0

class RedditCollector(BaseCollector):
    """Reddit讨论采集器

    使用Reddit API (无需认证只读模式)
    """

    SUBREDDITS = ["Python", "LocalLLaMA", "learnprogramming",
                  "LanguageTechnology", "MachineLearning"]

    def search_mentions(self, keywords: List[str],
                        limit: int = 100) -> List[RedditPost]:
        """搜索提及LingFlow的帖子"""
        # 使用Reddit搜索API或pushshift/snoofall
```

#### HackerNews Collector

```python
@dataclass
class HNPost(MentionData):
    """HN帖子数据"""
    points: int = 0
    num_comments: int = 0
    rank: int = 0  # 排名

class HNCollector(BaseCollector):
    """Hacker News采集器

    使用Algolia HN Search API
    """

    API_BASE = "http://hn.algolia.com/api/v1"

    def search_mentions(self, keywords: List[str],
                        days: int = 7) -> List[HNPost]:
        """搜索提及LingFlow的帖子"""
```

#### 中文社区采集器

```python
class DomesticCollector(BaseCollector):
    """中文社区采集器

    目标平台:
    - 掘金: 搜索API
    - 知乎: 搜索API (需登录)
    - V2EX: 节点API
    """

    def search_juejin(self, keyword: str) -> List[Post]:
        """掘金搜索"""

    def search_zhihu(self, keyword: str) -> List[Post]:
        """知乎搜索"""
```

### 3.2 新增分析器

#### 趋势分析器

```python
@dataclass
class TrendMetrics:
    """趋势指标"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # up/down/stable
    forecast: Optional[float] = None

class TrendAnalyzer(BaseAnalyzer):
    """趋势分析器

    分析各指标的时间趋势
    """

    def analyze_growth(self, data: List[Dict]) -> TrendMetrics:
        """分析增长趋势"""

    def detect_anomalies(self, data: List[Dict]) -> List[Dict]:
        """检测异常点"""

    def forecast(self, history: List[Dict],
                 periods: int = 7) -> List[float]:
        """简单预测 (移动平均/线性回归)"""
```

#### 话题聚类器

```python
class TopicAnalyzer(BaseAnalyzer):
    """话题分析器

    提取讨论中的热门话题
    """

    def extract_topics(self, mentions: List[MentionData]) -> List[str]:
        """提取热门话题

        方法:
        1. 关键词提取
        2. 相似度聚类
        3. 频次排序
        """

    def cluster_discussions(self, mentions: List[MentionData]) -> List[Cluster]:
        """将讨论聚类"""
```

#### 影响力评分

```python
@dataclass
class InfluenceScore:
    """影响力分数"""
    platform: str
    score: float  # 0-100
    components: Dict[str, float]
    level: str  # high/medium/low

class InfluenceAnalyzer(BaseAnalyzer):
    """影响力分析器

    评估每个提及的影响力
    """

    def calculate_score(self, mention: MentionData) -> InfluenceScore:
        """计算单个提及的影响力

        考虑因素:
        - 平台权重 (GitHub > HN > Reddit)
        - 互动指标 (stars/comments/upvotes)
        - 作者活跃度
        - 内容质量 (情感/长度)
        """
```

### 3.3 报告生成器

#### 每日简报

```python
class DailyReporter:
    """每日情报简报

    生成格式:
    - 终端输出 (带emoji)
    - Markdown文件
    - JSON数据
    """

    def generate(self, date: datetime) -> DailyReport:
        """生成当日报告"""

@dataclass
class DailyReport:
    """每日报告"""
    date: str
    summary: str
    metrics: Dict[str, Any]
    highlights: List[str]
    concerns: List[str]
    sentiment_summary: Dict
    top_topics: List[str]
    actionable_insights: List[str]
```

#### 可视化

```python
class ReportVisualizer:
    """报告可视化

    生成图表:
    - Star增长曲线
    - 提及量趋势
    - 情感分布饼图
    - 平台来源对比
    """

    def create_trend_chart(self, data: List[Dict]) -> str:
        """创建趋势图 (SVG/ASCII)"""

    def create_sentiment_chart(self, data: Dict) -> str:
        """创建情感分布图"""
```

### 3.4 MCP工具集成

#### 新增工具定义

```python
# 灵听 - 获取提及
@mcp_tool
def get_lingflow_mentions(
    platform: str = "all",
    days: int = 7,
    min_influence: float = 0.5
) -> List[Dict]:
    """获取关于LingFlow的提及

    Args:
        platform: 平台过滤 (all/github/reddit/hn)
        days: 最近N天
        min_influence: 最低影响力分数 (0-1)
    """

# 灵誉 - 声誉指标
@mcp_tool
def get_reputation_metrics(
    period: str = "week"
) -> Dict:
    """获取声誉指标

    Args:
        period: 统计周期 (week/month)

    Returns:
        {
            "period": "week",
            "total_mentions": 42,
            "sentiment_score": 0.65,
            "influence_score": 7.2,
            "star_growth": 15,
            "trend": "up"
        }
    """

# 灵感 - 情感分析
@mcp_tool
def analyze_sentiment(
    text: str = None,
    period: str = "week"
) -> Dict:
    """分析讨论情感

    可以分析指定文本或统计周期的情感
    """

# 灵脉 - Star趋势
@mcp_tool
def get_star_trends(
    days: int = 30
) -> Dict:
    """获取Star增长趋势"""

# 灵议 - 热门议题
@mcp_tool
def get_top_issues(
    days: int = 7,
    limit: int = 10
) -> List[Dict]:
    """获取热门讨论议题"""
```

---

## 四、实现计划

### Phase 1: 社交媒体采集 (Week 1)

| 任务 | 产出 | 状态 |
|------|------|------|
| 1.1 创建BaseCollector抽象类 | `collectors/base.py` | 🔲 |
| 1.2 实现RedditCollector | `collectors/reddit.py` | 🔲 |
| 1.3 实现HNCollector | `collectors/hackernews.py` | 🔲 |
| 1.4 单元测试 | `tests/test_collectors.py` | 🔲 |

### Phase 2: 分析增强 (Week 2)

| 任务 | 产出 | 状态 |
|------|------|------|
| 2.1 实现TrendAnalyzer | `analyzers/trend.py` | 🔲 |
| 2.2 实现TopicAnalyzer | `analyzers/topic.py` | 🔲 |
| 2.3 实现InfluenceAnalyzer | `analyzers/influence.py` | 🔲 |
| 2.4 集成测试 | `tests/test_analyzers.py` | 🔲 |

### Phase 3: 报告系统 (Week 3)

| 任务 | 产出 | 状态 |
|------|------|------|
| 3.1 实现DailyReporter | `reporters/daily.py` | 🔲 |
| 3.2 实现WeeklyReporter | `reporters/weekly.py` | 🔲 |
| 3.3 实现Visualizer | `reporters/visualizer.py` | 🔲 |
| 3.4 报告模板 | `templates/` | 🔲 |

### Phase 4: MCP集成 (Week 4)

| 任务 | 产出 | 状态 |
|------|------|------|
| 4.1 添加MCP工具定义 | `mcp_server/lingflow_mcp/intelligence_tools.py` | 🔲 |
| 4.2 测试工具调用 | 测试脚本 | 🔲 |
| 4.3 文档更新 | `docs/intelligence/MCP_TOOLS.md` | 🔲 |

---

## 五、配置与调度

### 5.1 配置文件

```yaml
# .lingflow/intelligence/config.yaml
intelligence:
  repo: "guangda88/LingFlow"

  collectors:
    github:
      enabled: true
      schedule: "0 */6 * * *"  # 每6小时
      token_env: GITHUB_TOKEN

    reddit:
      enabled: true
      schedule: "0 */12 * * *"  # 每12小时
      subreddits:
        - Python
        - LocalLLaMA
        - MachineLearning

    hackernews:
      enabled: true
      schedule: "0 */12 * * *"
      search_keywords:
        - LingFlow
        - lingflow-core

  analyzers:
    sentiment:
      enabled: true
      model: rule_based  # rule_based/ml

    influence:
      enabled: true
      weights:
        github: 1.0
        hackernews: 0.8
        reddit: 0.6

  reporters:
    daily:
      enabled: true
      schedule: "0 8 * * *"  # 每天8点
      output_dir: ".lingflow/intelligence/reports/daily"

    weekly:
      enabled: true
      schedule: "0 8 * * 1"  # 每周一8点
      output_dir: ".lingflow/intelligence/reports/weekly"
```

### 5.2 调度脚本

```bash
# scripts/intelligence_scheduler.py
# 使用cron或systemd定时器运行各采集器
```

---

## 六、预期效果

### 6.1 每日简报示例

```
╔════════════════════════════════════════════════════════════╗
║        📊 LingFlow 情报简报 - 2026-04-03                   ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  📈 今日统计                                               ║
║    • GitHub Issues: 3 个新增                               ║
║    • Discussions: 2 个新增                                 ║
║    • Reddit 提及: 5 次                                     ║
║    • Hacker News: 1 次                                     ║
║    • 新增 Stars: +12                                       ║
║                                                            ║
║  💬 情感分析                                               ║
║    • 积极: ████████████░░░░░░░░ 65%                        ║
║    • 中性: ██████░░░░░░░░░░░░░░░ 30%                        ║
║    • 消极: ██░░░░░░░░░░░░░░░░░░░  5%                        ║
║                                                            ║
║  🔥 热门议题                                               ║
║    1. "LingFlow 与 Cursor 对比" (12条讨论)                  ║
║    2. "自优化系统效果如何?" (8条讨论)                       ║
║    3. "MCP 集成教程请求" (6条讨论)                          ║
║                                                            ║
║  📊 趋势洞察                                               ║
║    • Star增长: 本周 +45 (环比 +120%)                       ║
║    • 社区活跃: 中等上升                                    ║
║    • 情感倾向: 整体积极                                    ║
║                                                            ║
║  ⚠️  需要关注                                              ║
║    • Issues #142: 安装文档需要更新 (24条评论)              ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### 6.2 MCP工具调用示例

```
你: 获取LingFlow最近一周的声誉指标

灵誉: 📊 LingFlow 声誉指标 (最近7天)

统计周期: 2026-03-27 至 2026-04-03

核心指标:
• 总提及次数: 42 次
  - GitHub: 18次
  - Reddit: 15次
  - Hacker News: 9次

• 情感分数: 0.65 / 1.0 (积极)
  - 积极: 65%
  - 中性: 30%
  - 消极: 5%

• 影响力分数: 7.2 / 10 (高)
  主要来源: Hacker News高赞帖子

• Star增长: +15 (8.2% 日均)

趋势: 📈 上升
```

---

## 七、技术约束与风险

### 7.1 API限制

| 平台 | 限制 | 缓解策略 |
|------|------|----------|
| Reddit | 100 req/min | 请求节流、多账号 |
| HN Algolia | 无硬限制 | 合理使用、缓存 |
| 掘金 | 需登录 | Cookie/代理 |
| 知乎 | 严格反爬 | 爬虫降级或跳过 |

### 7.2 数据保留

- 原始数据: 保留30天
- 分析结果: 保留90天
- 报告文件: 保留365天

### 7.3 风险缓解

| 风险 | 缓解措施 |
|------|----------|
| API限流 | 缓存 + 分散请求 |
| 数据量过大 | 定期清理旧数据 |
| 隐私问题 | 只采集公开数据 |
| 情感准确性 | 多模型融合 + 持续优化 |

---

## 八、成功指标

### 8.1 系统指标

- 采集成功率 > 95%
- 分析耗时 < 30秒/天
- 报告生成 < 5秒

### 8.2 业务指标

- 及时发现 > 80% 的重要讨论
- 情感分析准确率 > 70%
- 趋势预测偏差 < 20%

---

**设计完成**: 2026-04-03
**下一步**: Phase 1 实现
