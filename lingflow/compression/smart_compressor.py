"""LingFlow 智能上下文压缩器

提供智能化的上下文压缩功能，防止因 token 限制导致会话中断。

核心功能:
1. 精确 Token 计数 - 支持 tiktoken 和回退估算
2. 消息重要性评分 - 多维度评分系统
3. 分层压缩策略 - 保留关键信息
4. 对话摘要生成 - 智能摘要
5. 主动预警机制 - 接近限制时提醒

使用示例:
    from lingflow.compression.smart_compressor import SmartContextCompressor

    compressor = SmartContextCompressor()
    compressed = compressor.compress_messages(messages)
"""

import re
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# Token 估算器
# ============================================================================

class TokenEstimator:
    """精确 Token 计数器

    优先使用 tiktoken 进行精确计数，回退到估算模式。
    """

    # 默认比率 (不同模型有所不同)
    DEFAULT_RATIOS = {
        "gpt-4": 0.25,
        "gpt-3.5-turbo": 0.25,
        "claude-3": 0.28,  # Claude 使用不同的 tokenizer
        "default": 0.25
    }

    def __init__(self, model: str = "claude-3", use_tiktoken: bool = True):
        """初始化 Token 估算器

        Args:
            model: 模型名称，用于选择 tokenizer
            use_tiktoken: 是否尝试使用 tiktoken
        """
        self.model = model
        self._tokenizer = None
        self._use_tiktoken = use_tiktoken

        # 尝试加载 tiktoken
        if use_tiktoken:
            self._load_tiktoken()

    def _load_tiktoken(self):
        """尝试加载 tiktoken"""
        try:
            import tiktoken
            # 使用 cl100k_base (GPT-4/3.5-turbo 的编码)
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.info("使用 tiktoken 进行精确 token 计数")
        except ImportError:
            logger.debug("tiktoken 不可用，使用估算模式")
            self._use_tiktoken = False
        except Exception as e:
            logger.warning(f"tiktoken 加载失败: {e}，使用估算模式")
            self._use_tiktoken = False

    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数量

        Args:
            text: 输入文本

        Returns:
            token 数量
        """
        if not text:
            return 0

        if self._use_tiktoken and self._tokenizer:
            try:
                return len(self._tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"tiktoken 计数失败: {e}，回退到估算")

        # 回退到字符估算
        ratio = self.DEFAULT_RATIOS.get(self.model, self.DEFAULT_RATIOS["default"])
        return int(len(text) * ratio)

    def count_messages(self, messages: List[Dict[str, Any]]) -> int:
        """计算消息列表的 token 数量

        Args:
            messages: 消息列表

        Returns:
            总 token 数量
        """
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            # 消息格式开销 (role 等)
            total += 4
            total += self.count_tokens(content)
        return total

    def estimate_ratio(self, text: str, actual_tokens: int = None) -> float:
        """估算字符/token 比率

        Args:
            text: 文本样本
            actual_tokens: 实际 token 数 (如果已知)

        Returns:
            字符/token 比率
        """
        if actual_tokens and text:
            return len(text) / actual_tokens if actual_tokens > 0 else 0.25
        return self.DEFAULT_RATIOS.get(self.model, 0.25)


# ============================================================================
# 消息重要性评分
# ============================================================================

class MessageRole(Enum):
    """消息角色优先级"""
    SYSTEM = 1      # 系统消息 - 最高优先级
    USER = 2        # 用户消息
    ASSISTANT = 3   # 助手消息
    TOOL = 4        # 工具消息


@dataclass
class MessageScore:
    """消息评分结果"""
    message: Dict[str, Any]
    score: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


class MessageScorer:
    """消息重要性评分器

    根据多个维度对消息进行重要性评分:
    - 角色优先级 (system > user > assistant > tool)
    - 内容重要性 (关键词、任务相关)
    - 时间新鲜度 (最近的消息更重要)
    - 长度影响 (过短或过长的消息可能不那么重要)
    """

    # 关键词权重
    CRITICAL_KEYWORDS = [
        "must", "should", "require", "ensure", "critical", "important",
        "fix", "bug", "error", "security", "verify", "validate",
        "完成", "修复", "必须", "重要", "关键"
    ]

    TASK_KEYWORDS = [
        "task", "todo", "implement", "create", "add", "remove",
        "任务", "实现", "创建", "添加", "删除"
    ]

    def __init__(
        self,
        role_weights: Optional[Dict[MessageRole, float]] = None,
        recency_halflife: float = 3600.0,  # 1小时半衰期
        length_penalty: bool = True
    ):
        """初始化评分器

        Args:
            role_weights: 角色权重配置
            recency_halflife: 时间新鲜度半衰期 (秒)
            length_penalty: 是否对过短/过长消息应用惩罚
        """
        self.role_weights = role_weights or {
            MessageRole.SYSTEM: 1.0,
            MessageRole.USER: 0.8,
            MessageRole.ASSISTANT: 0.6,
            MessageRole.TOOL: 0.4
        }
        self.recency_halflife = recency_halflife
        self.length_penalty = length_penalty

    def score_message(
        self,
        message: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> MessageScore:
        """对单条消息评分

        Args:
            message: 消息字典
            timestamp: 消息时间戳 (可选)

        Returns:
            消息评分结果
        """
        score = 0.0
        reasons = []

        # 1. 角色评分
        role = self._get_role(message)
        role_score = self.role_weights.get(role, 0.5)
        score += role_score * 100
        reasons.append(f"角色({role.name}): {role_score * 100:.0f}")

        # 2. 内容重要性评分
        content = message.get("content", "")
        content_score = self._score_content(content)
        score += content_score
        if content_score > 0:
            reasons.append(f"内容: {content_score:.0f}")

        # 3. 时间新鲜度评分
        if timestamp:
            recency_score = self._score_recency(timestamp)
            score += recency_score
            reasons.append(f"新鲜度: {recency_score:.0f}")

        # 4. 长度调整
        if self.length_penalty:
            length_adjustment = self._adjust_for_length(content, score)
            score = max(1.0, score + length_adjustment)
            if abs(length_adjustment) > 5:
                reasons.append(f"长度调整: {length_adjustment:+.0f}")

        return MessageScore(
            message=message,
            score=score,
            reason=", ".join(reasons),
            timestamp=timestamp or datetime.now()
        )

    def score_messages(
        self,
        messages: List[Dict[str, Any]],
        timestamps: Optional[List[datetime]] = None
    ) -> List[MessageScore]:
        """对消息列表评分

        Args:
            messages: 消息列表
            timestamps: 消息时间戳列表 (可选)

        Returns:
            消息评分结果列表 (按分数降序)
        """
        scores = []
        now = datetime.now()

        for i, msg in enumerate(messages):
            ts = timestamps[i] if timestamps else now
            scores.append(self.score_message(msg, ts))

        # 按分数降序排序
        return sorted(scores, key=lambda x: x.score, reverse=True)

    def _get_role(self, message: Dict[str, Any]) -> MessageRole:
        """获取消息角色"""
        role_str = message.get("role", "user").lower()
        role_map = {
            "system": MessageRole.SYSTEM,
            "user": MessageRole.USER,
            "assistant": MessageRole.ASSISTANT,
            "tool": MessageRole.TOOL
        }
        return role_map.get(role_str, MessageRole.USER)

    def _score_content(self, content: str) -> float:
        """评分内容重要性"""
        if not content:
            return 0.0

        score = 0.0
        content_lower = content.lower()

        # 关键词评分
        for kw in self.CRITICAL_KEYWORDS:
            if kw in content_lower:
                score += 30

        for kw in self.TASK_KEYWORDS:
            if kw in content_lower:
                score += 15

        # 代码块评分 (通常包含重要信息)
        if "```" in content:
            score += 20

        # 列表项评分
        if re.search(r'^[\s]*[-*•]\s', content, re.MULTILINE):
            score += 10

        return min(score, 100)  # 最多100分

    def _score_recency(self, timestamp: datetime) -> float:
        """评分时间新鲜度"""
        now = datetime.now()
        age = (now - timestamp).total_seconds()

        if age < 0:
            age = 0

        # 指数衰减
        import math
        decay = math.exp(-age / self.recency_halflife)
        return decay * 50

    def _adjust_for_length(self, content: str, base_score: float) -> float:
        """根据长度调整分数"""
        length = len(content)

        # 过短消息 (< 50 字符) 可能是确认等
        if length < 50:
            return -20

        # 过长消息 (> 5000 字符) 可以被压缩
        if length > 5000:
            return -15

        return 0


# ============================================================================
# 分层压缩策略
# ============================================================================

class CompressionTier(Enum):
    """压缩层级"""
    KEEP_ALL = "keep_all"       # 保留全部
    KEEP_IMPORTANT = "keep_important"  # 保留重要
    COMPRESS = "compress"       # 压缩
    SUMMARIZE = "summarize"     # 摘要化
    DROP = "drop"               # 删除


@dataclass
class CompressionPlan:
    """压缩计划"""
    tiers: Dict[CompressionTier, List[MessageScore]]
    target_tokens: int
    estimated_tokens: int
    reduction_ratio: float


class TieredCompressionStrategy:
    """分层压缩策略

    根据消息评分将消息分层:
    1. TIER 0: 系统消息 - 始终保留
    2. TIER 1: 高分用户消息 - 保留
    3. TIER 2: 中等消息 - 压缩
    4. TIER 3: 低分消息 - 摘要化
    5. TIER 4: 工具消息/冗余 - 删除
    """

    def __init__(
        self,
        system_keep_ratio: float = 1.0,
        high_keep_ratio: float = 1.0,
        medium_compress_ratio: float = 0.5,
        low_summarize_ratio: float = 0.2
    ):
        """初始化分层策略

        Args:
            system_keep_ratio: 系统消息保留比例
            high_keep_ratio: 高分消息保留比例
            medium_compress_ratio: 中等消息压缩比例
            low_summarize_ratio: 低分消息摘要比例
        """
        self.system_keep_ratio = system_keep_ratio
        self.high_keep_ratio = high_keep_ratio
        self.medium_compress_ratio = medium_compress_ratio
        self.low_summarize_ratio = low_summarize_ratio

    def create_plan(
        self,
        scored_messages: List[MessageScore],
        target_tokens: int,
        token_estimator: TokenEstimator
    ) -> CompressionPlan:
        """创建压缩计划

        Args:
            scored_messages: 已评分的消息列表
            target_tokens: 目标 token 数量
            token_estimator: Token 估算器

        Returns:
            压缩计划
        """
        tiers = {
            CompressionTier.KEEP_ALL: [],
            CompressionTier.KEEP_IMPORTANT: [],
            CompressionTier.COMPRESS: [],
            CompressionTier.SUMMARIZE: [],
            CompressionTier.DROP: []
        }

        current_tokens = 0

        for scored in scored_messages:
            msg = scored.message
            tokens = token_estimator.count_tokens(msg.get("content", ""))

            # 系统消息 - 始终保留
            if msg.get("role") == "system":
                tiers[CompressionTier.KEEP_ALL].append(scored)
                current_tokens += tokens

            # 高分消息 (> 80) - 保留
            elif scored.score > 80:
                tiers[CompressionTier.KEEP_IMPORTANT].append(scored)
                current_tokens += tokens

            # 中等消息 (40-80) - 压缩
            elif scored.score > 40:
                tiers[CompressionTier.COMPRESS].append(scored)

            # 低分消息 (20-40) - 摘要
            elif scored.score > 20:
                tiers[CompressionTier.SUMMARIZE].append(scored)

            # 极低分 (< 20) - 删除
            else:
                tiers[CompressionTier.DROP].append(scored)

        estimated_tokens = current_tokens + sum(
            token_estimator.count_tokens(s.message.get("content", ""))
            for s in tiers[CompressionTier.COMPRESS]
        ) * self.medium_compress_ratio + sum(
            token_estimator.count_tokens(s.message.get("content", ""))
            for s in tiers[CompressionTier.SUMMARIZE]
        ) * self.low_summarize_ratio

        reduction_ratio = 1.0 - (estimated_tokens / max(token_estimator.count_messages([s.message for s in scored_messages]), 1))

        return CompressionPlan(
            tiers=tiers,
            target_tokens=target_tokens,
            estimated_tokens=estimated_tokens,
            reduction_ratio=reduction_ratio
        )


# ============================================================================
# 对话摘要生成器
# ============================================================================

class ConversationSummarizer:
    """对话摘要生成器

    生成对话的智能摘要，保留关键信息。
    """

    def __init__(self, max_summary_length: int = 2000):
        """初始化摘要生成器

        Args:
            max_summary_length: 最大摘要长度
        """
        self.max_summary_length = max_summary_length

    def summarize_messages(self, messages: List[Dict[str, Any]]) -> str:
        """生成消息列表的摘要

        Args:
            messages: 消息列表

        Returns:
            摘要文本
        """
        if not messages:
            return ""

        parts = []

        # 统计信息
        parts.append(f"对话摘要 (共 {len(messages)} 条消息)")

        # 提取关键信息
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        parts.append(f"- 用户消息: {len(user_messages)} 条")
        parts.append(f"- 助手消息: {len(assistant_messages)} 条")

        # 提取任务和决策
        tasks = self._extract_tasks(messages)
        if tasks:
            parts.append("\n任务:")
            for task in tasks[:5]:
                parts.append(f"  - {task}")

        # 提取关键决策
        decisions = self._extract_decisions(messages)
        if decisions:
            parts.append("\n关键决策:")
            for decision in decisions[:3]:
                parts.append(f"  - {decision}")

        # 提取错误和问题
        errors = self._extract_errors(messages)
        if errors:
            parts.append("\n问题:")
            for error in errors[:3]:
                parts.append(f"  - {error}")

        summary = "\n".join(parts)

        # 截断到最大长度
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length] + "\n... [摘要截断]"

        return summary

    def _extract_tasks(self, messages: List[Dict[str, Any]]) -> List[str]:
        """提取任务"""
        tasks = []
        for msg in messages:
            content = msg.get("content", "")
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("- [") or line.startswith("◻") or line.startswith("◼"):
                    task = re.sub(r'^[-◻◼\[\]x\s]+', '', line)
                    if task:
                        tasks.append(task[:50])
        return tasks[:5]

    def _extract_decisions(self, messages: List[Dict[str, Any]]) -> List[str]:
        """提取关键决策"""
        decisions = []
        keywords = ["决定", "决策", "选择", "采用", "decision", "chose"]
        for msg in messages:
            content = msg.get("content", "").lower()
            for kw in keywords:
                if kw in content:
                    decisions.append(content[:80])
                    break
        return decisions

    def _extract_errors(self, messages: List[Dict[str, Any]]) -> List[str]:
        """提取错误和问题"""
        errors = []
        for msg in messages:
            content = msg.get("content", "")
            if "error" in content.lower() or "错误" in content:
                # 提取错误信息
                error_match = re.search(r'(error|错误)[:：]\s*([^\n]+)', content, re.IGNORECASE)
                if error_match:
                    errors.append(error_match.group(2)[:60])
        return errors


# ============================================================================
# 智能上下文压缩器 (主类)
# ============================================================================

@dataclass
class CompressionResult:
    """压缩结果"""
    original_messages: List[Dict[str, Any]]
    compressed_messages: List[Dict[str, Any]]
    original_tokens: int
    compressed_tokens: int
    reduction_ratio: float
    strategy_used: str
    summary: str = ""
    stats: Dict[str, Any] = field(default_factory=dict)


class SmartContextCompressor:
    """智能上下文压缩器

    集成所有压缩功能的主类。

    使用流程:
    1. 使用 TokenEstimator 精确计数
    2. 使用 MessageScorer 评分消息
    3. 使用 TieredCompressionStrategy 制定计划
    4. 执行压缩
    5. 使用 ConversationSummarizer 生成摘要
    """

    # 默认配置
    DEFAULT_CONFIG = {
        "warning_threshold": 0.75,    # 75% 时警告
        "compress_threshold": 0.85,   # 85% 时压缩
        "critical_threshold": 0.95,   # 95% 时紧急压缩
        "target_ratio": 0.5,          # 目标压缩到 50%
        "keep_recent": 5,             # 保留最近 N 条完整消息
        "max_summary_length": 2000,   # 最大摘要长度
    }

    def __init__(
        self,
        max_tokens: int = 180000,
        config: Optional[Dict[str, Any]] = None,
        model: str = "claude-3"
    ):
        """初始化智能压缩器

        Args:
            max_tokens: 最大 token 数量
            config: 自定义配置
            model: 模型名称 (用于 token 估算)
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.max_tokens = max_tokens

        # 初始化组件
        self.token_estimator = TokenEstimator(model=model)
        self.message_scorer = MessageScorer()
        self.compression_strategy = TieredCompressionStrategy()
        self.summarizer = ConversationSummarizer(
            max_summary_length=self.config["max_summary_length"]
        )

        # 统计
        self._compression_count = 0
        self._total_tokens_saved = 0

    def check_and_compress(
        self,
        messages: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[CompressionResult]]:
        """检查并按需压缩

        Args:
            messages: 当前消息列表

        Returns:
            (是否执行了压缩, 压缩结果或 None)
        """
        current_tokens = self.token_estimator.count_messages(messages)
        ratio = current_tokens / self.max_tokens

        # 检查阈值
        if ratio >= self.config["critical_threshold"]:
            logger.warning(f"Token 使用率 {ratio:.1%}，执行紧急压缩")
            return True, self.compress(messages, mode="emergency")

        elif ratio >= self.config["compress_threshold"]:
            logger.info(f"Token 使用率 {ratio:.1%}，执行压缩")
            return True, self.compress(messages, mode="normal")

        elif ratio >= self.config["warning_threshold"]:
            logger.warning(f"Token 使用率 {ratio:.1%}，接近限制")

        return False, None

    def compress(
        self,
        messages: List[Dict[str, Any]],
        mode: str = "normal",
        target_ratio: Optional[float] = None
    ) -> CompressionResult:
        """压缩消息列表

        Args:
            messages: 原始消息列表
            mode: 压缩模式 (normal/aggressive/emergency)
            target_ratio: 目标压缩比例

        Returns:
            压缩结果
        """
        self._compression_count += 1

        original_tokens = self.token_estimator.count_messages(messages)
        target_ratio = target_ratio or self._get_mode_ratio(mode)
        target_tokens = int(self.max_tokens * target_ratio)

        # 对消息评分
        scored = self.message_scorer.score_messages(messages)

        # 创建压缩计划
        plan = self.compression_strategy.create_plan(
            scored,
            target_tokens,
            self.token_estimator
        )

        # 执行压缩
        compressed = self._execute_plan(plan, mode)

        compressed_tokens = self.token_estimator.count_messages(compressed)
        saved = original_tokens - compressed_tokens
        self._total_tokens_saved += saved

        # 生成摘要 (如果有被删除/摘要化的消息)
        summary = ""
        if plan.tiers[CompressionTier.SUMMARIZE] or plan.tiers[CompressionTier.DROP]:
            dropped = plan.tiers[CompressionTier.SUMMARIZE] + plan.tiers[CompressionTier.DROP]
            summary = self.summarizer.summarize_messages([s.message for s in dropped])

        return CompressionResult(
            original_messages=messages,
            compressed_messages=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_ratio=1.0 - (compressed_tokens / max(original_tokens, 1)),
            strategy_used=mode,
            summary=summary,
            stats={
                "compression_count": self._compression_count,
                "messages_removed": len(messages) - len(compressed),
                "plan_tiers": {k.value: len(v) for k, v in plan.tiers.items()}
            }
        )

    def _execute_plan(
        self,
        plan: CompressionPlan,
        mode: str
    ) -> List[Dict[str, Any]]:
        """执行压缩计划"""
        result = []

        # 1. 保留全部
        for scored in plan.tiers[CompressionTier.KEEP_ALL]:
            result.append(scored.message)

        # 2. 保留重要
        for scored in plan.tiers[CompressionTier.KEEP_IMPORTANT]:
            result.append(scored.message)

        # 3. 压缩中等消息
        compress_ratio = self._get_compress_ratio(mode)
        for scored in plan.tiers[CompressionTier.COMPRESS]:
            compressed = self._compress_message(scored.message, compress_ratio)
            if compressed:
                result.append(compressed)

        # 4. 摘要化低分消息 (仅在非紧急模式)
        if mode != "emergency" and plan.tiers[CompressionTier.SUMMARIZE]:
            messages_to_summarize = [s.message for s in plan.tiers[CompressionTier.SUMMARIZE]]
            summary = self.summarizer.summarize_messages(messages_to_summarize)
            result.append({
                "role": "system",
                "content": f"[对话摘要]\n{summary}"
            })

        # 5. 删除的 (不添加)

        return result

    def _compress_message(
        self,
        message: Dict[str, Any],
        ratio: float
    ) -> Optional[Dict[str, Any]]:
        """压缩单条消息"""
        content = message.get("content", "")
        if not content:
            return message

        target_length = int(len(content) * ratio)

        # 智能截断：保留首尾
        if len(content) > target_length:
            first_part = int(target_length * 0.3)
            last_part = target_length - first_part

            compressed = (
                content[:first_part] +
                "\n... [内容压缩] ...\n" +
                content[-last_part:]
            )
            return {**message, "content": compressed}

        return message

    def _get_mode_ratio(self, mode: str) -> float:
        """获取模式对应的目标比例"""
        ratios = {
            "normal": self.config["target_ratio"],
            "aggressive": 0.3,
            "emergency": 0.2
        }
        return ratios.get(mode, self.config["target_ratio"])

    def _get_compress_ratio(self, mode: str) -> float:
        """获取消息压缩比例"""
        ratios = {
            "normal": 0.7,
            "aggressive": 0.5,
            "emergency": 0.3
        }
        return ratios.get(mode, 0.7)

    def get_status(self) -> Dict[str, Any]:
        """获取压缩器状态"""
        return {
            "max_tokens": self.max_tokens,
            "compression_count": self._compression_count,
            "total_tokens_saved": self._total_tokens_saved,
            "config": self.config
        }


# ============================================================================
# 便捷函数
# ============================================================================

# 全局单例
_global_compressor: Optional[SmartContextCompressor] = None


def get_smart_compressor(
    max_tokens: int = 180000,
    config: Optional[Dict[str, Any]] = None
) -> SmartContextCompressor:
    """获取全局智能压缩器实例"""
    global _global_compressor
    if _global_compressor is None:
        _global_compressor = SmartContextCompressor(
            max_tokens=max_tokens,
            config=config
        )
    return _global_compressor


def compress_messages(
    messages: List[Dict[str, Any]],
    max_tokens: int = 180000
) -> List[Dict[str, Any]]:
    """压缩消息列表 (便捷函数)"""
    compressor = get_smart_compressor(max_tokens=max_tokens)
    _, result = compressor.check_and_compress(messages)
    return result.compressed_messages if result else messages


def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
    """估算消息的 token 数量 (便捷函数)"""
    compressor = get_smart_compressor()
    return compressor.token_estimator.count_messages(messages)
