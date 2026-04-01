#!/usr/bin/env python3
"""
npm趋势情报系统 - MVP版本

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


class NPMTrendCollector:
    """npm趋势采集器 - MVP版本"""

    def __init__(self):
        """初始化采集器"""
        # 关注的关键词（JavaScript/TypeScript相关）
        self.keywords = [
            "static-analysis",
            "code-quality",
            "linter",
            "code-formatter",
            "ast",
            "ast-parser",
            "code-refactoring",
            "testing",
            "test-runner",
            "coverage",
            "code-review",
            "ai",
            "llm",
            "agent"
        ]

        # 质量过滤（保守策略）
        self.min_weekly_downloads = 1000  # 最低周下载量
        self.min_dependents = 5  # 最少依赖数
        self.recent_days = 90  # 只看最近三个月的活跃包

        # npm API配置
        self.npm_registry = "https://registry.npmjs.org"
        self.npm_downloads = "https://api.npmjs.org/downloads"

    def search_packages(self, keyword: str, size: int = 20) -> List[Dict]:
        """搜索npm包

        Args:
            keyword: 搜索关键词
            size: 返回结果数量

        Returns:
            包列表
        """
        try:
            url = f"{self.npm_registry}/-/v1/search"
            params = {
                'text': keyword,
                'size': size
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get('objects', [])
            else:
                print(f"⚠️  API请求失败: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return []

    def get_package_downloads(self, package_name: str, period: str = "last-week") -> int:
        """获取包下载量

        Args:
            package_name: 包名
            period: 时间段 (last-week, last-month, last-year)

        Returns:
            下载量
        """
        try:
            url = f"{self.npm_downloads}/point/{period}/{package_name}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('downloads', 0)
            else:
                return 0

        except Exception as e:
            print(f"⚠️  获取下载量失败: {e}")
            return 0

    def collect_trends(self) -> List[Dict[str, Any]]:
        """采集npm趋势"""

        print(f"\n🔍 开始采集npm趋势...")
        print(f"关键词: {', '.join(self.keywords[:3])}...")
        print(f"最低周下载: {self.min_weekly_downloads}")
        print(f"最低依赖数: {self.min_dependents}")

        all_packages = []
        seen_packages = set()  # 去重

        for keyword in self.keywords:
            print(f"\n  搜索: {keyword}")

            packages = self.search_packages(keyword)

            for pkg_data in packages:
                package = pkg_data.get('package', {})
                package_name = package.get('name')

                # 去重
                if package_name in seen_packages:
                    continue
                seen_packages.add(package_name)

                # 提取关键信息
                pkg_info = {
                    'name': package_name,
                    'version': package.get('version'),
                    'description': package.get('description') or "无描述",
                    'keywords': package.get('keywords', []),
                    'author': package.get('publisher', {}).get('username', 'Unknown'),
                    'license': package.get('license', 'Unknown'),
                    'url': f"https://www.npmjs.com/package/{package_name}",
                    'repository': package.get('links', {}).get('repository', ''),
                    'homepage': package.get('links', {}).get('homepage', ''),
                    'weekly_downloads': pkg_data.get('downloads', {}).get('weekly', 0),
                    'monthly_downloads': pkg_data.get('downloads', {}).get('monthly', 0),
                    'dependents': int(pkg_data.get('dependents', 0)),
                    'updated_at': pkg_data.get('updated'),
                    'search_score': pkg_data.get('searchScore', 0),
                    'keyword': keyword,
                    'collected_at': datetime.now().isoformat()
                }

                # 质量过滤
                # 1. 下载量过滤
                if pkg_info['weekly_downloads'] < self.min_weekly_downloads:
                    continue

                # 2. 依赖数过滤
                if pkg_info['dependents'] < self.min_dependents:
                    continue

                # 3. 更新时间过滤
                if pkg_info['updated_at']:
                    try:
                        updated = datetime.fromisoformat(pkg_info['updated_at'].replace('Z', '+00:00'))
                        days_ago = (datetime.now(updated.tzinfo) - updated).days
                        if days_ago > self.recent_days:
                            continue  # 太旧的包跳过
                    except:
                        pass

                all_packages.append(pkg_info)

            print(f"    找到 {len(packages)} 个包")

        print(f"\n✅ 采集完成: 共 {len(all_packages)} 个包")

        return all_packages


class LingFlowRelevanceAnalyzer:
    """LingFlow相关性分析器 - npm版本"""

    def __init__(self):
        # 核心关键词（高权重）
        self.core_keywords = {
            'static-analysis': 100,
            'code-quality': 95,
            'linter': 90,
            'ast': 85,
            'parser': 75,
            'code-refactoring': 90,
            'ai': 80,
            'llm': 85,
            'agent': 75
        }

        # 相关技术（中权重）
        self.tech_keywords = {
            'testing': 60,
            'coverage': 55,
            'code-review': 70,
            'formatter': 65,
            'syntax': 50,
            'parsing': 60
        }

        # JavaScript生态（低权重）
        self.ecosystem_keywords = {
            'javascript': 20,
            'typescript': 25,
            'node': 20,
            'library': 20,
            'tool': 25
        }

    def calculate_relevance(self, pkg: Dict) -> int:
        """计算相关性分数 (0-100)"""

        score = 0

        # 名称、描述、关键词文本
        text = f"{pkg['name']} {pkg.get('description', '')} {' '.join(pkg.get('keywords', []))}".lower()

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

        # 下载量加分（对数增长）
        weekly_downloads = pkg.get('weekly_downloads', 0)
        if weekly_downloads >= 1000000:
            score += 35  # 100万+超级流行
        elif weekly_downloads >= 500000:
            score += 30  # 50万-100万
        elif weekly_downloads >= 100000:
            score += 25  # 10万-50万
        elif weekly_downloads >= 50000:
            score += 20  # 5万-10万
        elif weekly_downloads >= 10000:
            score += 15  # 1万-5万
        elif weekly_downloads >= 5000:
            score += 10  # 5千-1万
        elif weekly_downloads >= 1000:
            score += 5   # 1千-5千

        # 依赖数加分
        dependents = pkg.get('dependents', 0)
        if dependents >= 10000:
            score += 25  # 1万+依赖
        elif dependents >= 5000:
            score += 20  # 5千-1万
        elif dependents >= 1000:
            score += 15  # 1千-5千
        elif dependents >= 100:
            score += 10  # 100-1千
        elif dependents >= 10:
            score += 5   # 10-100

        # 最近更新加分
        if pkg.get('updated_at'):
            try:
                updated = datetime.fromisoformat(pkg['updated_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now() - updated).days
                if days_ago < 7:
                    score += 15  # 一周内有更新
                elif days_ago < 30:
                    score += 10  # 一个月内有更新
            except:
                pass

        return min(score, 100)

    def categorize(self, pkg: Dict, score: int) -> str:
        """分类项目"""
        if score >= 80:
            return "high_value"
        elif score >= 50:
            return "medium_value"
        else:
            return "low_value"

    def explain_relevance(self, pkg: Dict, score: int) -> str:
        """解释相关性原因"""
        reasons = []

        text = f"{pkg['name']} {pkg.get('description', '')} {' '.join(pkg.get('keywords', []))}".lower()

        # 找匹配的关键词
        for keyword, weight in self.core_keywords.items():
            if keyword.lower() in text:
                reasons.append(f"核心关键词'{keyword}'")

        if score > 50 and pkg.get('weekly_downloads', 0) > 10000:
            reasons.append(f"高下载量({pkg['weekly_downloads']:,}/周)")

        if score > 50 and pkg.get('dependents', 0) > 100:
            reasons.append(f"高依赖数({pkg['dependents']})")

        if reasons:
            return "；".join(reasons)
        else:
            return "一般相关性"


class TrendReporter:
    """趋势汇报生成器"""

    def __init__(self):
        self.report_dir = Path(".lingflow/reports/npm_trends")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, packages: List[Dict], analysis: Dict) -> str:
        """生成汇报"""

        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("📦 npm趋势情报报告")
        report_lines.append("=" * 70)
        report_lines.append(f"采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_lines.append(f"包数量: {len(packages)}")
        report_lines.append("")

        # 高价值发现
        high_value = analysis.get('high_value', [])
        if high_value:
            report_lines.append("🔥 高价值发现:")
            for i, item in enumerate(high_value, 1):
                report_lines.append(f"\n  [{i}] {item['name']}")
                report_lines.append(f"     📥 {item['weekly_downloads']:,} 下载/周")
                report_lines.append(f"     🔗 依赖数: {item['dependents']}")
                report_lines.append(f"     📝 {item['description'][:80]}...")
                report_lines.append(f"     🔗 {item['url']}")
                report_lines.append(f"     💡 {item.get('relevance', 'N/A')}")

        # 中等价值
        medium_value = analysis.get('medium_value', [])
        if medium_value:
            report_lines.append(f"\n📊 中等价值项目:")
            report_lines.append(f"  发现 {len(medium_value)} 个相关项目")
            for item in medium_value[:5]:  # 只显示前5个
                report_lines.append(f"  • {item['name']} ({item['weekly_downloads']:,}/周)")

        # 统计信息
        report_lines.append(f"\n📈 统计摘要:")
        report_lines.append(f"  高价值项目: {len(high_value)} 个")
        report_lines.append(f"  中等价值项目: {len(medium_value)} 个")
        report_lines.append(f"  总采集项目: {len(packages)} 个")

        # 建议
        report_lines.append(f"\n💡 建议行动:")
        if high_value:
            report_lines.append("  1. 深入研究高价值包的功能和API")
            report_lines.append("  2. 查看其README和文档")
            report_lines.append("  3. 评估是否可用于LingFlow的TypeScript/JavaScript部分")
        else:
            report_lines.append("  本次未发现特别高价值的包")

        report_lines.append(f"\n📚 完整数据已保存到: {self.report_dir}/")
        report_lines.append("=" * 70)

        return "\n".join(report_lines)

    def save_data(self, packages: List[Dict], analysis: Dict) -> Path:
        """保存数据到文件"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存原始数据
        data_file = self.report_dir / f"trends_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'packages': packages,
                'analysis': analysis
            }, f, indent=2, ensure_ascii=False)

        # 保存分析报告
        report_file = self.report_dir / f"report_{timestamp}.txt"
        report = self.generate_report(packages, analysis)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n💾 数据已保存:")
        print(f"  原始数据: {data_file}")
        print(f"  分析报告: {report_file}")

        return data_file


def main():
    """主函数"""
    print("=" * 70)
    print("🔍 npm趋势情报系统 - MVP")
    print("=" * 70)
    print()
    print("⚠️  谨慎实施原则:")
    print("  • 只采集高质量、活跃维护的npm包")
    print("  • 聚焦JavaScript/TypeScript相关的工具库")
    print("  • 提供分析和建议，不自动应用")
    print("  • 随时可以停止或调整")
    print()

    # 采集器
    collector = NPMTrendCollector()

    # 采集趋势
    packages = collector.collect_trends()

    if not packages:
        print("\n❌ 未采集到任何数据，请检查:")
        print("  1. 网络连接")
        print("  2. npm registry API状态")
        return

    # 分析相关性
    print(f"\n🔍 分析LingFlow相关性...")
    analyzer = LingFlowRelevanceAnalyzer()

    analysis = {
        'high_value': [],
        'medium_value': [],
        'low_value': []
    }

    for pkg in packages:
        score = analyzer.calculate_relevance(pkg)
        category = analyzer.categorize(pkg, score)

        pkg['relevance_score'] = score
        pkg['relevance_category'] = category
        pkg['relevance_reason'] = analyzer.explain_relevance(pkg, score)

        analysis[category].append(pkg)

    # 按分数排序
    for category in analysis:
        analysis[category].sort(key=lambda x: x['relevance_score'], reverse=True)

    # 生成汇报
    reporter = TrendReporter()
    report = reporter.generate_report(packages, analysis)
    print(report)

    # 保存数据
    reporter.save_data(packages, analysis)

    print("\n✅ 情报系统运行完成！")


if __name__ == "__main__":
    main()
