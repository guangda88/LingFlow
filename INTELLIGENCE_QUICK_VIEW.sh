#!/bin/bash
# 📡 lingflow 情报系统 - 快速查看命令
# 使用方法: source INTELLIGENCE_QUICK_VIEW.sh 或直接复制命令

echo "🔍 lingflow GitHub 趋势情报 - 快速查看"
echo "=========================================="

# 1. 查看最新综合报告
echo ""
echo "📊 查看最新综合分析报告:"
echo "less .lingflow/reports/github_trends/GITHUB_TREND_REVIEW_*.md | head -1 | xargs cat"

# 2. 查看Top 10高价值项目
echo ""
echo "⭐ 查看Top 10高价值项目:"
cat .lingflow/reports/github_trends/trends_*.json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
repos = sorted(data['repos'], key=lambda x: x['relevance_score'], reverse=True)[:10]
for i, r in enumerate(repos, 1):
    print(f\"{i:2d}. {r['relevance_score']:3d}分 {r['stars']:8d}⭐ {r['full_name']}\")
"

# 3. 统计信息
echo ""
echo "📈 采集统计:"
cat .lingflow/reports/github_trends/trends_*.json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
total = len(data['repos'])
high = len([r for r in data['repos'] if r['relevance_score'] >= 80])
medium = len([r for r in data['repos'] if 50 <= r['relevance_score'] < 80])
low = len([r for r in data['repos'] if r['relevance_score'] < 50])
print(f\"  总计: {total} 个仓库\")
print(f\"  🔥 高价值: {high} 个 ({high*100//total}%)\" )
print(f\"  📊 中等: {medium} 个 ({medium*100//total}%)\")
print(f\"  ⚠️  低价值: {low} 个 ({low*100//total}%)\")
"

# 4. 最新采集时间
echo ""
echo "⏰ 最新采集时间:"
ls -lht .lingflow/reports/github_trends/*.json | head -1 | awk '{print "  " $6, $7, $8, $9}'

# 5. 下次采集时间
echo ""
echo "🔄 下次自动采集:"
crontab -l | grep github_trend_collector | awk '{print "  " $2 ":00 (今日)"}'

# 6. 快速查看分类项目
echo ""
echo "🔖 按分类查看:"
echo "  多智能体框架:"
cat .lingflow/reports/github_trends/trends_*.json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
agent_repos = [r for r in data['repos'] if 'agent' in r['name'].lower() or 'agent' in r.get('description', '').lower()]
for r in sorted(agent_repos, key=lambda x: x['stars'], reverse=True)[:5]:
    print(f\"    {r['stars']:8d}⭐ {r['full_name']}\")
"

echo ""
echo "  代码分析工具:"
cat .lingflow/reports/github_trends/trends_*.json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
analysis_repos = [r for r in data['repos'] if any(k in r.get('description', '').lower() for k in ['static', 'analysis', 'ast', 'review'])]
for r in sorted(analysis_repos, key=lambda x: x['stars'], reverse=True)[:5]:
    print(f\"    {r['stars']:8d}⭐ {r['full_name']}\")
"

echo ""
echo "=========================================="
echo "📖 完整指南: cat GITHUB_TREND_INTELLIGENCE_GUIDE.md"
echo ""
