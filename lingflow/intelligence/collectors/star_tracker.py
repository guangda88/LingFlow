"""Star 增长追踪器 - 追踪lingflow项目的Star增长趋势

记录新增Star用户，分析增长模式。
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests


@dataclass
class StargazerData:
    """Star用户数据模型"""

    user: str = ""
    starred_at: str = ""
    collected_at: str = ""

    def to_dict(self) -> Dict:
        return {
            "user": self.user,
            "starred_at": self.starred_at,
            "collected_at": self.collected_at,
        }


class StarTracker:
    """Star增长追踪器

    追踪lingflow项目的Star增长，记录新增用户。
    """

    def __init__(self, repo: str = "guangda88/lingflow", token: Optional[str] = None):
        """初始化追踪器

        Args:
            repo: GitHub仓库
            token: GitHub Personal Access Token
        """
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN", "")

        self.api_base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

        # 数据存储
        self.data_dir = Path(".lingflow/intelligence/raw/stars")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "star_history.json"

    def get_star_count(self) -> int:
        """获取当前Star数量"""
        try:
            response = requests.get(f"{self.api_base}/repos/{self.repo}", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get("stargazers_count", 0)
        except Exception as e:
            print(f"  ❌ 获取Star数量失败: {e}")
        return 0

    def get_stargazers(self, per_page: int = 100) -> List[Dict]:
        """获取Star用户列表"""
        all_stargazers = []
        page = 1

        while True:
            try:
                # 注意: stargazers API 返回时间倒序
                response = requests.get(
                    f"{self.api_base}/repos/{self.repo}/stargazers",
                    headers=self.headers,
                    params={"page": page, "per_page": per_page},
                    timeout=30,
                )

                if response.status_code != 200:
                    break

                stargazers = response.json()
                if not stargazers:
                    break

                all_stargazers.extend(stargazers)

                # 检查是否是最后一页
                if len(stargazers) < per_page:
                    break

                page += 1
                if page > 100:  # 安全限制
                    break

            except Exception as e:
                print(f"  ❌ 获取Stargazers失败 (page {page}): {e}")
                break

        return all_stargazers

    def load_history(self) -> Dict:
        """加载历史数据"""
        if self.history_file.exists():
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "last_check": None,
            "stargazers": {},
            "history": [],
        }

    def save_history(self, data: Dict):
        """保存历史数据"""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def collect(self, max_users: int = 300) -> Dict:
        """采集Star数据

        Args:
            max_users: 最多获取用户数（避免API限流）

        Returns:
            采集结果统计
        """
        print("  ⭐ 追踪Star增长...")
        print(f"    目标仓库: {self.repo}")
        print(f"    最大用户数: {max_users}")

        # 获取当前Star数
        current_count = self.get_star_count()
        print(f"    当前Star数: {current_count}")

        # 获取Star用户列表
        stargazers = self.get_stargazers(per_page=100)
        print(f"    已获取用户数: {len(stargazers)}")

        # 加载历史数据
        history_data = self.load_history()
        old_stargazers = set(history_data.get("stargazers", {}).keys())

        # 识别新增用户
        new_stargazers = []
        for sg in stargazers[:max_users]:
            user = sg["user"]["login"]
            if user not in old_stargazers:
                new_stargazers.append(
                    {
                        "user": user,
                        "starred_at": sg["starred_at"],
                    }
                )

        # 更新stargazers映射（只保留最近的部分）
        stargazers_map = {}
        for sg in stargazers[:max_users]:
            user = sg["user"]["login"]
            stargazers_map[user] = sg["starred_at"]

        # 计算增长
        previous_count = history_data.get("star_count", 0)
        growth = current_count - previous_count

        result = {
            "timestamp": datetime.now().isoformat(),
            "repo": self.repo,
            "star_count": current_count,
            "previous_count": previous_count,
            "growth": growth,
            "new_stargazers": new_stargazers[:50],  # 最多记录50个
            "total_stargazers": len(stargazers),
            "stargazers": stargazers_map,
        }

        # 保存数据
        history_data["last_check"] = result["timestamp"]
        history_data["star_count"] = current_count
        history_data["stargazers"] = stargazers_map
        history_data["history"].append(result)

        # 只保留最近30条历史记录
        if len(history_data["history"]) > 30:
            history_data["history"] = history_data["history"][-30:]

        self.save_history(history_data)

        print(f"    新增Star: +{growth}")
        print(f"    新增用户: {len(new_stargazers)}")

        # 显示新增用户（部分）
        if new_stargazers:
            print(f"    最新用户: {', '.join([u['user'] for u in new_stargazers[:5]])}")

        return result

    def generate_trend_report(self, days: int = 30) -> Dict:
        """生成趋势报告

        Args:
            days: 统计最近N天的数据

        Returns:
            趋势报告
        """
        history_data = self.load_history()
        history = history_data.get("history", [])

        # 过滤最近N天的数据
        cutoff = datetime.now() - timedelta(days=days)
        recent_history = [h for h in history if datetime.fromisoformat(h["timestamp"]) > cutoff]

        if not recent_history:
            return {"error": "没有足够的历史数据"}

        # 计算统计
        first = recent_history[0]
        last = recent_history[-1]

        total_growth = last["star_count"] - first["star_count"]
        days_spanned = (datetime.fromisoformat(last["timestamp"]) - datetime.fromisoformat(first["timestamp"])).days

        avg_daily_growth = total_growth / days_spanned if days_spanned > 0 else 0

        # 找出最大增长日
        max_growth_day = max(recent_history, key=lambda x: x["growth"])

        return {
            "period_days": days,
            "actual_days": days_spanned,
            "first_check": first["timestamp"],
            "last_check": last["timestamp"],
            "first_count": first["star_count"],
            "last_count": last["star_count"],
            "total_growth": total_growth,
            "avg_daily_growth": round(avg_daily_growth, 1),
            "max_growth_day": {
                "date": max_growth_day["timestamp"],
                "growth": max_growth_day["growth"],
            },
            "data_points": len(recent_history),
        }


def main():
    """主函数 - 测试追踪器"""
    print("=" * 60)
    print("⭐ Star 增长追踪器")
    print("=" * 60)
    print()

    tracker = StarTracker()

    # 采集数据
    result = tracker.collect(max_users=300)

    print()
    print("📊 采集结果:")
    print(f"  当前Stars: {result['star_count']}")
    print(f"  增长: +{result['growth']}")
    print(f"  新增用户: {len(result['new_stargazers'])}")

    # 生成趋势报告
    print()
    print("📈 趋势报告:")
    trend = tracker.generate_trend_report(days=30)
    if "error" not in trend:
        print(f"  统计周期: {trend['period_days']}天")
        print(f"  实际跨度: {trend['actual_days']}天")
        print(f"  期间增长: +{trend['total_growth']}")
        print(f"  日均增长: {trend['avg_daily_growth']}")
        print(f"  数据点数: {trend['data_points']}")

    print()
    print("✅ 追踪完成")


if __name__ == "__main__":
    main()
