"""趋势分析器

分析各指标的时间趋势，包括增长趋势、异常检测和简单预测。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base import BaseAnalyzer, AnalyzerConfig, calculate_moving_average, detect_outliers
from ..models.common import MentionData, TrendMetrics, TrendDirection
from ..logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TrendConfig(AnalyzerConfig):
    """趋势分析器配置"""
    window_size: int = 7
    anomaly_threshold: float = 2.0


class TrendAnalyzer(BaseAnalyzer):
    """趋势分析器

    分析各指标的时间趋势，支持增长分析、异常检测和简单预测。
    """

    NAME = "trend"
    DESCRIPTION = "趋势分析器"

    def __init__(self, config: Optional[TrendConfig] = None):
        super().__init__(config)
        self.config: TrendConfig = config or TrendConfig()

    def analyze(self, mentions: List[MentionData], **kwargs) -> Dict[str, Any]:
        if not mentions:
            return {"total": 0, "trends": [], "summary": {}}

        trends = []
        trends.append(self._analyze_volume_trend(mentions))
        trends.append(self._analyze_engagement_trend(mentions))
        trends.extend(self._analyze_by_platform(mentions))

        return {
            "total": len(mentions),
            "trends": [t.to_dict() if hasattr(t, "to_dict") else t for t in trends],
            "summary": {
                "overall_direction": self._determine_overall_direction(trends),
            },
        }

    def _analyze_volume_trend(self, mentions: List[MentionData]) -> TrendMetrics:
        daily_counts: Dict[str, int] = {}
        for m in mentions:
            try:
                date_str = m.published_at[:10] if m.published_at else "unknown"
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
            except Exception:
                pass

        if len(daily_counts) < 2:
            return TrendMetrics(
                metric_name="mention_volume",
                current_value=len(mentions),
                previous_value=0,
                change_percent=100.0,
                trend_direction=TrendDirection.UP,
            )

        sorted_dates = sorted(daily_counts.keys())
        mid = len(sorted_dates) // 2

        recent_count = sum(daily_counts[d] for d in sorted_dates[mid:])
        earlier_count = sum(daily_counts[d] for d in sorted_dates[:mid])

        change = ((recent_count - earlier_count) / earlier_count * 100) if earlier_count > 0 else 100.0

        if change > 10:
            direction = TrendDirection.UP
        elif change < -10:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE

        return TrendMetrics(
            metric_name="mention_volume",
            current_value=float(recent_count),
            previous_value=float(earlier_count),
            change_percent=round(change, 1),
            trend_direction=direction,
        )

    def _analyze_engagement_trend(self, mentions: List[MentionData]) -> TrendMetrics:
        if len(mentions) < 2:
            return TrendMetrics(
                metric_name="engagement",
                current_value=0.0,
                previous_value=0.0,
                change_percent=0.0,
                trend_direction=TrendDirection.STABLE,
            )

        mid = len(mentions) // 2
        recent = mentions[mid:]
        earlier = mentions[:mid]

        recent_engagement = sum(m.comments + (m.points or 0) + (m.score or 0) for m in recent)
        earlier_engagement = sum(m.comments + (m.points or 0) + (m.score or 0) for m in earlier)

        avg_recent = recent_engagement / len(recent) if recent else 0
        avg_earlier = earlier_engagement / len(earlier) if earlier else 0

        change = ((avg_recent - avg_earlier) / avg_earlier * 100) if avg_earlier > 0 else 0.0

        if change > 10:
            direction = TrendDirection.UP
        elif change < -10:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE

        return TrendMetrics(
            metric_name="engagement",
            current_value=round(avg_recent, 1),
            previous_value=round(avg_earlier, 1),
            change_percent=round(change, 1),
            trend_direction=direction,
        )

    def _analyze_by_platform(self, mentions: List[MentionData]) -> List[TrendMetrics]:
        platform_counts: Dict[str, int] = {}
        for m in mentions:
            platform = m.platform.value if hasattr(m.platform, "value") else str(m.platform)
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        trends = []
        for platform, count in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True):
            trends.append(TrendMetrics(
                metric_name=f"platform_{platform}",
                current_value=float(count),
                previous_value=0.0,
                change_percent=100.0,
                trend_direction=TrendDirection.UP,
            ))

        return trends[:5]

    def _determine_overall_direction(self, trends: List) -> str:
        up = sum(1 for t in trends if isinstance(t, TrendMetrics) and t.trend_direction == TrendDirection.UP)
        down = sum(1 for t in trends if isinstance(t, TrendMetrics) and t.trend_direction == TrendDirection.DOWN)
        stable = sum(1 for t in trends if isinstance(t, TrendMetrics) and t.trend_direction == TrendDirection.STABLE)

        if up > down and up > stable:
            return "up"
        elif down > up and down > stable:
            return "down"
        return "stable"

    def forecast(self, history_values: List[float], periods: int = 7) -> List[float]:
        if not history_values:
            return [0.0] * periods

        ma = calculate_moving_average(history_values, self.config.window_size)
        if not ma:
            avg = sum(history_values) / len(history_values)
            return [avg] * periods

        last_ma = ma[-1]

        if len(history_values) >= 2:
            window = min(self.config.window_size, len(history_values))
            slope = (history_values[-1] - history_values[-window]) / window
        else:
            slope = 0.0

        return [max(0.0, last_ma + slope * (i + 1)) for i in range(periods)]

    def detect_anomalies(self, values: List[float]) -> List[int]:
        return detect_outliers(values, self.config.anomaly_threshold)
