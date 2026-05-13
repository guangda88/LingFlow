#!/usr/bin/env python3
"""
GitHub趋势情报系统 - MVP版本

谨慎实施原则:
1. 简单有效，不过度设计
2. 手动审核，不自动应用
3. 可控风险，随时停止
4. 逐步验证，按需扩展
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import os


class GitHubTrendCollector:
    """GitHub趋势采集器 - MVP版本"""

    def __init__(self, token: Optional[str] = None):
        """初始化采集器

        Args:
            token: GitHub Personal Access Token (可选，用于提高API限额)
        """
        self.token = token or os.getenv('GITHUB_TOKEN', '')

        # 关注的关键词（谨慎选择，聚焦lingflow相关）
        # 第一轮审查后优化（2026-04-01）
        self.keywords = [
            "llm",                    # ✅ LLM框架和工具
            "multi-agent",            # ✅ 多智能体系统
            "agent",                  # ✅ 新增：更宽泛的agent搜索
            "code-optimization",      # ✅ 代码优化
            "static-analysis",        # ⚠️ 保留：静态分析
            "python-static-analysis", # ✅ 新增：Python静态分析（更精确）
            "ast-parsing",           # ✅ 新增：AST解析（替代python-ast）
            "code-refactoring",       # ✅ 新增：代码重构
            "llm-code-review"        # ✅ 新增：LLM代码审查（更精确）
        ]

        # 质量过滤（保守策略）
        self.min_stars = 500  # 较高的门槛
        self.language_filter = ["Python"]
        self.recent_days = 30  # 只看最近一个月的活跃项目

        # GitHub API配置
        self.api_base = "https://api.github.com"
        self.headers = {}
        if self.token:
            self.headers['Authorization'] = f"token {self.token}"
        self.headers['Accept'] = 'application/vnd.github.v3+json'

    def search_repositories(self, keyword: str, sort: str = "stars", order: str = "desc") -> List[Dict]:
        """搜索GitHub仓库

        Args:
            keyword: 搜索关键词
            sort: 排序方式 (stars, forks, updated)
            order: 排序顺序 (desc, asc)

        Returns:
            仓库列表
        """
        # 搜索参数
        params = {
            'q': f"{keyword} language:python stars:>={self.min_stars}",
            'sort': sort,
            'order': order,
            'per_page': 10  # 只取前10个
        }

        try:
            response = requests.get(
                f"{self.api_base}/search/repositories",
                headers=self.headers,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get('items', [])
            else:
                print(f"⚠️  API请求失败: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return []

    def collect_trends(self) -> List[Dict[str, Any]]:
        """采集GitHub趋势"""

        print(f"\n🔍 开始采集GitHub趋势...")
        print(f"关键词: {', '.join(self.keywords[:3])}...")
        print(f"最低Stars: {self.min_stars}")
        print(f"时间范围: 最近{self.recent_days}天")

        all_repos = []
        seen_repos = set()  # 去重

        for keyword in self.keywords:
            print(f"\n  搜索: {keyword}")

            repos = self.search_repositories(keyword)

            for repo in repos:
                repo_id = repo['id']

                # 去重
                if repo_id in seen_repos:
                    continue
                seen_repos.add(repo_id)

                # 提取关键信息
                repo_info = {
                    'id': repo['id'],
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'description': repo['description'] or "无描述",
                    'stars': repo['stargazers_count'],
                    'forks': repo['forks_count'],
                    'language': repo['language'] or 'Unknown',
                    'url': repo['html_url'],
                    'created_at': repo['created_at'],
                    'updated_at': repo['updated_at'],
                    'keyword': keyword,
                    'collected_at': datetime.now().isoformat()
                }

                # 检查更新时间
                if repo['updated_at']:
                    updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
                    days_ago = (datetime.now(updated.tzinfo) - updated).days
                    if days_ago > self.recent_days:
                        continue  # 太旧的项目跳过

                all_repos.append(repo_info)

            print(f"    找到 {len(repos)} 个仓库")

        print(f"\n✅ 采集完成: 共 {len(all_repos)} 个仓库")

        return all_repos


class lingflowRelevanceAnalyzer:
    """lingflow相关性分析器"""

    def __init__(self):
        # 核心关键词（高权重）
        self.core_keywords = {
            'llm': 100,
            'multi-agent': 100,
            'agent': 80,
            'static-analysis': 90,
            'code-optimization': 90,
            'self-improving': 85,
            'code-review': 85
        }

        # 相关技术（中权重）
        self.tech_keywords = {
            'ast': 60,
            'parsing': 50,
            'syntax-tree': 60,
            'optimization': 70,
            'refactoring': 70,
            'quality': 60,
            'testing': 50,
            'monitoring': 50
        }

        # Python生态（低权重）
        self.ecosystem_keywords = {
            'library': 30,
            'framework': 30,
            'tool': 30,
            'package': 30
        }

    def calculate_relevance(self, repo: Dict) -> int:
        """计算相关性分数 (0-100)"""

        score = 0

        # 描述和名称文本
        text = f"{repo['name']} {repo.get('description', '')}".lower()

        # 核心关键词匹配
        for keyword, weight in self.core_keywords.items():
            if keyword.lower() in text:
                score += weight

        # 技术关键词匹配
        for keyword, weight in self.tech_keywords.items():
            if keyword.lower() in text:
                score += weight

        # 生态关键词匹配
        for keyword, weight in self.ecosystem_keywords.items():
            if keyword.lower() in text:
                score += weight

        # Star数加分（优化为对数增长，更好体现超Star项目价值）
        stars = repo.get('stars', 0)
        if stars >= 100000:
            score += 35  # 100k+ 超级明星项目
        elif stars >= 50000:
            score += 30  # 50k-100k
        elif stars >= 10000:
            score += 25  # 10k-50k
        elif stars >= 5000:
            score += 20  # 5k-10k
        elif stars >= 1000:
            score += 15  # 1k-5k
        elif stars >= 500:
            score += 5   # 500-1k

        # 最近更新加分
        if repo.get('updated_at'):
            try:
                updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now() - updated).days
                if days_ago < 7:
                    score += 15  # 一周内有更新
                elif days_ago < 30:
                    score += 10  # 一个月内有更新
            except:
                pass

        return min(score, 100)

    def categorize(self, repo: Dict, score: int) -> str:
        """分类项目"""
        if score >= 80:
            return "high_value"
        elif score >= 50:
            return "medium_value"
        else:
            return "low_value"

    def explain_relevance(self, repo: Dict, score: int) -> str:
        """解释相关性原因"""
        reasons = []

        text = f"{repo['name']} {repo.get('description', '')}".lower()

        # 找匹配的关键词
        for keyword, weight in self.core_keywords.items():
            if keyword.lower() in text:
                reasons.append(f"核心关键词'{keyword}'")

        if score > 50 and repo.get('stars', 0) > 1000:
            reasons.append(f"高Star项目({repo['stars']}⭐)")

        if reasons:
            return "；".join(reasons)
        else:
            return "一般相关性"


class TrendReporter:
    """趋势汇报生成器"""

    def __init__(self):
        self.report_dir = Path(".lingflow/reports/github_trends")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, repos: List[Dict], analysis: Dict) -> str:
        """生成汇报"""

        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("🌟 GitHub趋势情报报告")
        report_lines.append("=" * 70)
        report_lines.append(f"采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_lines.append(f"仓库数量: {len(repos)}")
        report_lines.append("")

        # 高价值发现
        high_value = analysis.get('high_value', [])
        if high_value:
            report_lines.append("🔥 高价值发现:")
            for i, item in enumerate(high_value, 1):
                report_lines.append(f"\n  [{i}] {item['full_name']}")
                report_lines.append(f"     ⭐ {item['stars']:,} Stars")
                report_lines.append(f"     📝 {item['description'][:80]}...")
                report_lines.append(f"     🔗 {item['url']}")
                report_lines.append(f"     💡 {item.get('relevance', 'N/A')}")

        # 中等价值
        medium_value = analysis.get('medium_value', [])
        if medium_value:
            report_lines.append(f"\n📊 中等价值项目:")
            report_lines.append(f"  发现 {len(medium_value)} 个相关项目")
            for item in medium_value[:5]:  # 只显示前5个
                report_lines.append(f"  • {item['full_name']} ({item['stars']}⭐)")

        # 统计信息
        report_lines.append(f"\n📈 统计摘要:")
        report_lines.append(f"  高价值项目: {len(high_value)} 个")
        report_lines.append(f"  中等价值项目: {len(medium_value)} 个")
        report_lines.append(f"  总采集项目: {len(repos)} 个")

        # 建议
        report_lines.append(f"\n💡 建议行动:")
        if high_value:
            report_lines.append("  1. 深入研究高价值项目的架构和设计")
            report_lines.append("  2. 关注其README和文档")
            report_lines.append("  3. 查看其Issue讨论，了解社区关注点")
        else:
            report_lines.append("  本次未发现特别高价值的项目")

        report_lines.append(f"\n📚 完整数据已保存到: {self.report_dir}/")
        report_lines.append("=" * 70)

        return "\n".join(report_lines)

    def save_data(self, repos: List[Dict], analysis: Dict) -> Path:
        """保存数据到文件"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存原始数据
        data_file = self.report_dir / f"trends_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'repos': repos,
                'analysis': analysis
            }, f, indent=2, ensure_ascii=False)

        # 保存分析报告
        report_file = self.report_dir / f"report_{timestamp}.txt"
        report = self.generate_report(repos, analysis)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n💾 数据已保存:")
        print(f"  原始数据: {data_file}")
        print(f"  分析报告: {report_file}")

        return data_file


def main():
    """主函数"""
    print("=" * 70)
    print("🔍 GitHub趋势情报系统 - MVP")
    print("=" * 70)
    print()
    print("⚠️  谨慎实施原则:")
    print("  • 只采集Python语言的高质量项目")
    print("  • 聚焦lingflow相关的技术领域")
    print("  • 提供分析和建议，不自动应用")
    print("  • 随时可以停止或调整")
    print()

    # 采集器
    collector = GitHubTrendCollector()

    # 采集趋势
    repos = collector.collect_trends()

    if not repos:
        print("\n❌ 未采集到任何数据，请检查:")
        print("  1. 网络连接")
        print("   2. GitHub Token配置 (可选)")
        print("  3. API限额")
        return

    # 分析相关性
    print(f"\n🔍 分析lingflow相关性...")
    analyzer = lingflowRelevanceAnalyzer()

    analysis = {
        'high_value': [],
        'medium_value': [],
        'low_value': []
    }

    for repo in repos:
        score = analyzer.calculate_relevance(repo)
        category = analyzer.categorize(repo, score)

        repo['relevance_score'] = score
        repo['relevance_category'] = category
        repo['relevance_reason'] = analyzer.explain_relevance(repo, score)

        analysis[category].append(repo)

    # 按分数排序
    for category in analysis:
        analysis[category].sort(key=lambda x: x['relevance_score'], reverse=True)

    # 生成汇报
    reporter = TrendReporter()
    report = reporter.generate_report(repos, analysis)
    print(report)

    # 保存数据
    reporter.save_data(repos, analysis)

    print("\n✅ 情报系统运行完成！")


if __name__ == "__main__":
    main()
