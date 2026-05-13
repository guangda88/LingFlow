# 📡 lingflow GitHub 趋势情报系统 - 用户指南

**更新日期**: 2026-04-02
**系统状态**: ✅ 运行中
**采集频率**: 每日 2 次 (09:00, 21:00)

---

## 🎯 系统简介

### 什么是情况感知模块？

**lingflow GitHub 趋势情报系统** 是一个**独立情报采集系统**，**不自动学习**，仅用于：

1. **收集情报**: 从 GitHub 发现相关的高价值项目
2. **人工审查**: 手动评估是否值得借鉴
3. **谨慎采纳**: 选择性吸收优秀实践

### 核心原则

```
📊 情报采集 → 🔍 人工审查 → ⚠️ 谨慎采纳
```

**重要**:
- ❌ 不是自动学习系统
- ❌ 不会自动修改代码
- ✅ 只提供参考信息
- ✅ 由你决定是否采纳

---

## 📂 查看情报报告

### 1. 综合分析报告

**位置**: `.lingflow/reports/github_trends/GITHUB_TREND_REVIEW_20260401.md`

**内容**:
- 采集统计数据（51个仓库，60.8%高价值）
- Top 10 高价值发现（MetaGPT, Jedi, PR-Agent等）
- 关键词效果分析
- 重点推荐项目（⭐⭐⭐⭐⭐）
- 优化建议

**查看命令**:
```bash
cat .lingflow/reports/github_trends/GITHUB_TREND_REVIEW_20260401.md
# 或
less .lingflow/reports/github_trends/GITHUB_TREND_REVIEW_20260401.md
```

### 2. 原始采集数据

**位置**: `.lingflow/reports/github_trends/trends_*.json`

**最新数据**:
```bash
ls -lht .lingflow/reports/github_trends/*.json | head -1
# .lingflow/reports/github_trends/trends_20260401_183849.json (78KB)
```

**查看示例**:
```bash
# 查看所有采集的仓库
cat .lingflow/reports/github_trends/trends_20260401_183849.json | \
  python3 -c "import json, sys; data = json.load(sys.stdin); print(f\"Total: {len(data['repos'])} repos\"); [print(f\"{r['stars']}⭐ {r['full_name']} - {r.get('description', 'N/A')[:60]}\") for r in data['repos'][:10]]"

# 查看高价值项目（80分以上）
cat .lingflow/reports/github_trends/trends_20260401_183849.json | \
  python3 -c "import json, sys; data = json.load(sys.stdin); high_value = [r for r in data['repos'] if r['relevance_score'] >= 80]; print(f\"High value: {len(high_value)} repos\"); [print(f\"{r['relevance_score']}分 {r['full_name']} ({r['stars']}⭐)\") for r in high_value]"
```

### 3. 运行日志

**位置**: `.lingflow/logs/github_trend_collector.log`

**查看最新日志**:
```bash
tail -50 .lingflow/logs/github_trend_collector.log
```

---

## 🎯 Top 10 高价值发现

### ⭐⭐⭐⭐⭐ 第一优先级（深入研究）

#### 1. **MetaGPT** (66,524⭐)
- **仓库**: https://github.com/geekan/MetaGPT
- **价值**: 多Agent软件开发框架，模拟AI软件公司
- **可借鉴**:
  - 角色定义模式（产品经理、架构师、工程师）
  - SOP（标准操作程序）驱动的工作流
  - 人类-readable的中间产物
  - 任务分解和执行

#### 2. **Jedi** (6,127⭐)
- **仓库**: https://github.com/davidhalter/jedi
- **价值**: Python自动补全、静态分析和重构库
- **可借鉴**:
  - 成熟的Python AST处理
  - 静态分析和重构能力
  - 代码分析实现模式

#### 3. **Code-Review-Graph** (3,914⭐)
- **仓库**: https://github.com/wshobson/code-review-graph
- **价值**: Claude Code的本地知识图谱
- **可借鉴**:
  - 持久化代码库映射
  - Token优化（6.8×减少）
  - 知识图谱构建算法

#### 4. **PR-Agent** (10,731⭐)
- **仓库**: https://github.com/Codium-ai/pr-agent
- **价值**: 开源PR审查工具
- **可借鉴**:
  - 自动化PR审查
  - 多维度代码分析
  - 反馈生成模式

#### 5. **wshobson/agents** (32,700⭐)
- **仓库**: https://github.com/wshobson/agents
- **价值**: Claude Code的多Agent编排
- **可借鉴**:
  - Claude Code生态集成
  - Agent编排实践
  - 实际应用案例

### ⭐⭐⭐⭐ 第二优先级（值得关注）

6. **OpenAI Swarm** (21,265⭐) - 轻量级多Agent编排
7. **AgentScope** (22,674⭐) - 可视化Agent开发和运行
8. **Vulnhuntr** (2,614⭐) - LLM零样本漏洞发现
9. **ChatDev** (32,505⭐) - 多Agent软件开发自动化
10. **Auto-Research-In-Sleep** (5,076⭐) - 自主ML研究技能

---

## 📊 系统运行状态

### 自动化调度

**Cron 任务**:
```bash
# 每日 09:00 采集
0 9 * * * /usr/bin/python3 /home/ai/lingflow/scripts/github_trend_collector.py

# 每日 21:00 采集
0 21 * * * /usr/bin/python3 /home/ai/lingflow/scripts/github_trend_collector.py
```

**查看当前任务**:
```bash
crontab -l | grep github
```

### 手动触发采集

```bash
# 运行采集脚本
python3 scripts/github_trend_collector.py

# 查看输出
tail -f .lingflow/logs/github_trend_collector.log
```

### 检查系统状态

```bash
# 检查最新采集时间
ls -lht .lingflow/reports/github_trends/*.json | head -1

# 统计采集数量
cat .lingflow/reports/github_trends/*.json | \
  python3 -c "import json, sys; data = json.load(sys.stdin); print(f\"Total repos: {len(data['repos'])}\")"

# 检查高价值项目
cat .lingflow/reports/github_trends/*.json | \
  python3 -c "import json, sys; data = json.load(sys.stdin); high = [r for r in data['repos'] if r['relevance_score'] >= 80]; print(f\"High value: {len(high)}\")"
```

---

## 🔧 配置和自定义

### 当前采集关键词

```python
keywords = [
    "llm",              # LLM相关
    "multi-agent",      # 多智能体
    "code-optimization", # 代码优化
    "static-analysis",  # 静态分析
    "python-ast",       # Python AST
    "code-review",      # 代码审查
]
```

### 质量过滤

```python
min_stars = 500           # 最少500星
language_filter = ["Python"]  # 仅Python项目
recent_days = 30          # 最近30天活跃
```

### 修改配置

编辑 `scripts/github_trend_collector.py`:

```bash
vim scripts/github_trend_collector.py
# 或
nano scripts/github_trend_collector.py
```

**优化建议** (来自第一次审查报告):

```python
# 推荐关键词调整
keywords = [
    "llm",                    # ✅ 保留 (60%准确率)
    "multi-agent",            # ✅ 保留 (100%准确率)
    "agent",                  # ✅ 新增
    "code-optimization",      # ✅ 保留 (70%准确率)
    "static-analysis",        # ✅ 保留 (50%准确率)
    "python-static-analysis", # ✅ 新增（更精确）
    "ast-parsing",           # ✅ 新增（替代python-ast）
    "code-refactoring",       # ✅ 新增
    "llm-code-review"        # ✅ 新增（更精确）
]

# 移除低效关键词
# "python-ast" - 0%准确率
# "code-review" - 22%准确率（过于宽泛）
# "self-improving-code" - 无结果
```

---

## 📈 使用建议

### 1. 定期查看报告

```bash
# 每周查看一次最新报告
ls -lt .lingflow/reports/github_trends/GITHUB_TREND_REVIEW_*.md | head -1 | awk '{print $NF}' | xargs cat
```

### 2. 深入研究高价值项目

从审查报告中选择重点项目：
```bash
# 例如研究 MetaGPT
git clone https://github.com/geekan/MetaGPT.git /tmp/MetaGPT
cd /tmp/MetaGPT
# 阅读文档，分析架构
```

### 3. 评估集成价值

对每个高价值项目：
1. ✅ 了解核心功能
2. ✅ 分析设计模式
3. ✅ 评估与lingflow相关性
4. ⚠️ 谨慎决定是否采纳
5. ✅ 记录评估结果

### 4. 持续优化系统

根据采集结果：
- 调整关键词
- 优化评分算法
- 改进质量过滤

---

## 🎯 下一步行动

### 本周行动

- [ ] 阅读完整审查报告
- [ ] 选择3-5个重点项目深入研究
- [ ] 评估集成价值
- [ ] 记录评估结果

### 推荐研究顺序

1. **MetaGPT** - 多Agent框架（最相关）
2. **Jedi** - Python AST处理（核心功能）
3. **Code-Review-Graph** - 知识图谱（Token优化）
4. **PR-Agent** - PR审查自动化（功能参考）

---

## 📞 支持和反馈

### 问题排查

```bash
# 检查脚本是否可执行
ls -l scripts/github_trend_collector.py

# 测试运行
python3 scripts/github_trend_collector.py

# 查看错误日志
tail -100 .lingflow/logs/github_trend_collector.log
```

### GitHub Token 设置

如果遇到 API 限制，参考：
```bash
cat .lingflow/reports/github_trends/GITHUB_TOKEN_SETUP.md
```

---

## 📚 相关文档

| 文档 | 位置 |
|------|------|
| 完整审查报告 | `.lingflow/reports/github_trends/GITHUB_TREND_REVIEW_20260401.md` |
| GitHub Token 设置 | `.lingflow/reports/github_trends/GITHUB_TOKEN_SETUP.md` |
| 优化效果报告 | `.lingflow/reports/github_trends/OPTIMIZATION_EFFECT_REPORT.md` |
| 采集脚本 | `scripts/github_trend_collector.py` |
| 运行日志 | `.lingflow/logs/github_trend_collector.log` |

---

**系统状态**: ✅ 运行正常
**下次采集**: 今日 21:00
**建议**: 开始研究Top 5高价值项目

---

*"众智混元，万法灵通" - lingflow 情报感知系统*

*最后更新: 2026-04-02*
