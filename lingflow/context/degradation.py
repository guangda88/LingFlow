"""长上下文退化检测器

检测 LLM 在长上下文工作中的性能退化，识别四种主要失效模式:
1. Context Poisoning — 错误信息污染后续推理
2. Attention Dilution — 关键信息被海量上下文淹没
3. Instruction Drift — 指令遵从度下降
4. Repetition Collapse — 重复输出或循环行为
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class DegradationType(Enum):
    """退化类型"""
    CONTEXT_POISONING = "context_poisoning"
    ATTENTION_DILUTION = "attention_dilution"
    INSTRUCTION_DRIFT = "instruction_drift"
    REPETITION_COLLAPSE = "repetition_collapse"
    NONE = "none"


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class DegradationReport:
    """退化检测报告"""
    health: HealthStatus
    score: float  # 0.0 (完全退化) ~ 1.0 (健康)
    detected_types: List[DegradationType] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "health": self.health.value,
            "score": round(self.score, 3),
            "detected_types": [t.value for t in self.detected_types],
            "details": self.details,
            "recommendations": self.recommendations,
        }


class DegradationDetector:
    """长上下文退化检测器

    通过分析最近的消息历史，检测 LLM 性能退化的早期信号。
    """

    REPETITION_THRESHOLD = 0.7
    MIN_MESSAGES_FOR_ANALYSIS = 3
    ERROR_RATE_THRESHOLD = 0.5
    INSTRUCTION_KEYWORDS = {
        "must", "should", "require", "ensure", "never",
        "always", "需要", "必须", "确保", "不要",
    }

    def __init__(
        self,
        repetition_threshold: float = 0.7,
        error_rate_threshold: float = 0.5,
        window_size: int = 10,
    ):
        """初始化退化检测器

        Args:
            repetition_threshold: 重复检测阈值 (0-1)
            error_rate_threshold: 错误率阈值 (0-1)
            window_size: 分析窗口大小（最近 N 条消息）
        """
        self.repetition_threshold = repetition_threshold
        self.error_rate_threshold = error_rate_threshold
        self.window_size = window_size

    def check_repetition(self, messages: List[Dict[str, str]]) -> Tuple[bool, float]:
        """检测重复崩溃

        Args:
            messages: 最近的消息列表

        Returns:
            (是否检测到重复, 相似度分数)
        """
        if len(messages) < self.MIN_MESSAGES_FOR_ANALYSIS:
            return False, 0.0

        recent = messages[-self.window_size:]
        assistant_msgs = [m for m in recent if m.get("role") == "assistant"]

        if len(assistant_msgs) < 2:
            return False, 0.0

        similarities = []
        for i in range(1, len(assistant_msgs)):
            sim = self._compute_similarity(
                assistant_msgs[i - 1].get("content", ""),
                assistant_msgs[i].get("content", ""),
            )
            similarities.append(sim)

        if not similarities:
            return False, 0.0

        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity >= self.repetition_threshold, avg_similarity

    def check_instruction_drift(
        self,
        instructions: List[str],
        messages: List[Dict[str, str]],
    ) -> Tuple[bool, float]:
        """检测指令漂移

        检查最近消息是否偏离了给定的指令。

        Args:
            instructions: 原始指令列表
            messages: 最近消息列表

        Returns:
            (是否检测到漂移, 漂移分数)
        """
        if not instructions or len(messages) < self.MIN_MESSAGES_FOR_ANALYSIS:
            return False, 0.0

        recent = messages[-self.window_size:]
        assistant_msgs = [m for m in recent if m.get("role") == "assistant"]

        if not assistant_msgs:
            return False, 0.0

        instruction_text = " ".join(instructions).lower()
        instruction_words = set(instruction_text.split()) & self.INSTRUCTION_KEYWORDS

        if not instruction_words:
            return False, 0.0

        drift_scores = []
        for msg in assistant_msgs[-3:]:
            content = msg.get("content", "").lower()
            overlap = sum(1 for w in instruction_words if w in content)
            adherence = overlap / len(instruction_words) if instruction_words else 0
            drift_scores.append(1.0 - adherence)

        avg_drift = sum(drift_scores) / len(drift_scores)
        return avg_drift > 0.7, avg_drift

    def check_error_rate(self, messages: List[Dict[str, str]]) -> Tuple[bool, float]:
        """检测错误率是否异常升高

        Args:
            messages: 最近消息列表

        Returns:
            (是否错误率过高, 错误率)
        """
        if len(messages) < self.MIN_MESSAGES_FOR_ANALYSIS:
            return False, 0.0

        recent = messages[-self.window_size:]
        assistant_msgs = [m for m in recent if m.get("role") == "assistant"]

        if not assistant_msgs:
            return False, 0.0

        error_indicators = [
            "error", "exception", "traceback", "failed", "failure",
            "错误", "失败", "异常",
        ]

        error_count = 0
        for msg in assistant_msgs:
            content = msg.get("content", "").lower()
            if any(indicator in content for indicator in error_indicators):
                error_count += 1

        error_rate = error_count / len(assistant_msgs)
        return error_rate >= self.error_rate_threshold, error_rate

    def get_health_score(self, messages: List[Dict[str, str]]) -> DegradationReport:
        """获取综合健康评分

        Args:
            messages: 最近消息列表

        Returns:
            退化检测报告
        """
        if len(messages) < self.MIN_MESSAGES_FOR_ANALYSIS:
            return DegradationReport(
                health=HealthStatus.HEALTHY,
                score=1.0,
                details={"reason": "insufficient_data"},
            )

        scores: Dict[str, float] = {}
        detected: List[DegradationType] = []
        recommendations: List[str] = []

        # 检测重复崩溃
        is_repetition, sim_score = self.check_repetition(messages)
        scores["repetition"] = 1.0 - sim_score
        if is_repetition:
            detected.append(DegradationType.REPETITION_COLLAPSE)
            recommendations.append("检测到重复输出，建议压缩上下文或重新开始会话")

        # 检测错误率
        is_high_error, error_rate = self.check_error_rate(messages)
        scores["error_rate"] = 1.0 - error_rate
        if is_high_error:
            detected.append(DegradationType.ATTENTION_DILUTION)
            recommendations.append("错误率异常升高，可能存在上下文信息过载")

        # 检测指令漂移 (使用通用指令)
        is_drift, drift_score = self.check_instruction_drift(
            list(self.INSTRUCTION_KEYWORDS), messages
        )
        scores["instruction_drift"] = 1.0 - drift_score
        if is_drift:
            detected.append(DegradationType.INSTRUCTION_DRIFT)
            recommendations.append("检测到指令遵从度下降，建议重新明确任务目标")

        # 综合评分 (加权平均)
        weights = {"repetition": 0.4, "error_rate": 0.35, "instruction_drift": 0.25}
        total_weight = sum(
            weights.get(k, 0) for k in scores
        )
        overall_score = (
            sum(scores.get(k, 1.0) * weights.get(k, 0) for k in scores)
            / total_weight
            if total_weight > 0
            else 1.0
        )

        if overall_score < 0.4:
            health = HealthStatus.CRITICAL
            recommendations.append("严重退化，强烈建议进行会话交接")
        elif overall_score < 0.7:
            health = HealthStatus.DEGRADED
            if not recommendations:
                recommendations.append("性能有所下降，建议压缩上下文")
        else:
            health = HealthStatus.HEALTHY

        return DegradationReport(
            health=health,
            score=overall_score,
            detected_types=detected,
            details={
                "repetition_score": round(sim_score, 3),
                "error_rate": round(error_rate, 3),
                "drift_score": round(drift_score, 3),
                "component_scores": {k: round(v, 3) for k, v in scores.items()},
            },
            recommendations=recommendations,
        )

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度（基于 N-gram Jaccard）"""
        if not text1 or not text2:
            return 0.0

        ngrams1 = self._get_ngrams(text1, 3)
        ngrams2 = self._get_ngrams(text2, 3)

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)

        return intersection / union if union > 0 else 0.0

    def _get_ngrams(self, text: str, n: int = 3) -> set:
        """提取文本的字符级 N-gram"""
        words = text.lower().split()
        if len(words) < n:
            return {tuple(words)} if words else set()
        return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}
