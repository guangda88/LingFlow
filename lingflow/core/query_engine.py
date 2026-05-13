"""lingflow QueryEngine - 基于Claude Code设计的查询处理引擎

特性:
- 配置驱动的查询处理
- 自动消息紧凑化
- Token预算控制
- 结构化输出支持
- 完整的使用追踪
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


class StopReason(Enum):
    """查询停止原因"""

    COMPLETED = "completed"
    MAX_TURNS_REACHED = "max_turns_reached"
    MAX_BUDGET_REACHED = "max_budget_reached"
    USER_CANCELLED = "user_cancelled"
    ERROR = "error"


@dataclass(frozen=True)
class QueryEngineConfig:
    """QueryEngine配置（不可变）"""

    max_turns: int = 8
    max_budget_tokens: int = 200000
    compact_after_turns: int = 12
    compact_threshold_tokens: int = 100000
    structured_output: bool = False
    structured_retry_limit: int = 2
    auto_compact: bool = True


@dataclass(frozen=True)
class TurnResult:
    """单轮查询结果（不可变）"""

    prompt: str
    output: str
    matched_tools: Tuple[str, ...]
    matched_agents: Tuple[str, ...]
    input_tokens: int
    output_tokens: int
    stop_reason: StopReason
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UsageSummary:
    """使用量摘要"""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    turn_count: int = 0

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "turn_count": self.turn_count,
        }


class MessageCompactor:
    """消息紧凑化工具"""

    @staticmethod
    def compact_messages(messages: List[str], target_tokens: int, current_tokens: int) -> Tuple[List[str], int]:
        """
        紧凑化消息列表，保留最近的重要消息

        Args:
            messages: 消息列表
            target_tokens: 目标token数
            current_tokens: 当前token数

        Returns:
            (紧凑化后的消息列表, 新的token数)
        """
        if current_tokens <= target_tokens:
            return messages, current_tokens

        # 估算策略：保留最近的70%消息
        keep_ratio = 0.7
        keep_count = max(1, int(len(messages) * keep_ratio))

        # 保留最近的消息
        compacted = messages[-keep_count:]

        # 估算新token数（假设与消息数成正比）
        new_tokens = int(current_tokens * keep_ratio)

        return compacted, new_tokens

    @staticmethod
    def summarize_messages(messages: List[str]) -> str:
        """生成消息摘要"""
        if not messages:
            return ""

        # 简单摘要策略
        summary_parts = [
            f"总消息数: {len(messages)}",
            f"最早消息: {messages[0][:50]}..." if messages else "",
            f"最近消息: {messages[-1][:50]}..." if messages else "",
        ]

        return " | ".join([p for p in summary_parts if p])


class QueryEngine:
    """查询处理引擎

    功能:
    - 管理多轮对话
    - Token预算控制
    - 自动消息紧凑化
    - 工具和Agent匹配
    """

    def __init__(self, config: QueryEngineConfig, session_id: str = None):
        self.config = config
        self.session_id = session_id or str(uuid.uuid4())
        self._messages: List[str] = []
        self._input_tokens = 0
        self._output_tokens = 0
        self._turn_count = 0
        self._compactor = MessageCompactor()
        self._history: List[TurnResult] = []

    @property
    def usage_summary(self) -> UsageSummary:
        """获取使用量摘要"""
        return UsageSummary(
            total_input_tokens=self._input_tokens, total_output_tokens=self._output_tokens, turn_count=self._turn_count
        )

    def submit(
        self,
        prompt: str,
        tools: Optional[List[str]] = None,
        agents: Optional[List[str]] = None,
        process_func: Optional[Callable[[str], str]] = None,
    ) -> TurnResult:
        """
        提交查询

        Args:
            prompt: 用户提示词
            tools: 可用工具列表
            agents: 可用Agent列表
            process_func: 处理函数（模拟LLM调用）

        Returns:
            TurnResult: 查询结果
        """
        # 1. 检查是否达到最大轮数
        if self._turn_count >= self.config.max_turns:
            return TurnResult(
                prompt=prompt,
                output="",
                matched_tools=(),
                matched_agents=(),
                input_tokens=0,
                output_tokens=0,
                stop_reason=StopReason.MAX_TURNS_REACHED,
                error=f"已达到最大轮数限制 ({self.config.max_turns})",
            )

        # 2. 检查Token预算
        if self._input_tokens + self._output_tokens >= self.config.max_budget_tokens:
            return TurnResult(
                prompt=prompt,
                output="",
                matched_tools=(),
                matched_agents=(),
                input_tokens=0,
                output_tokens=0,
                stop_reason=StopReason.MAX_BUDGET_REACHED,
                error=f"已达到Token预算限制 ({self.config.max_budget_tokens})",
            )

        # 3. 添加提示词到消息历史
        self._messages.append(f"User: {prompt}")

        # 4. 模拟处理（实际中会调用LLM）
        if process_func:
            output = process_func(prompt)
        else:
            output = self._default_process(prompt, tools, agents)

        # 5. 估算Token使用
        input_tokens = len(prompt.split())
        output_tokens = len(output.split())

        # 6. 更新统计
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self._turn_count += 1

        # 7. 添加输出到消息历史
        self._messages.append(f"Assistant: {output}")

        # 8. 匹配工具和Agent
        matched_tools = self._match_tools(prompt, tools or [])
        matched_agents = self._match_agents(prompt, agents or [])

        # 9. 创建结果
        result = TurnResult(
            prompt=prompt,
            output=output,
            matched_tools=tuple(matched_tools),
            matched_agents=tuple(matched_agents),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stop_reason=self._determine_stop_reason(),
        )

        # 10. 保存到历史
        self._history.append(result)

        # 11. 自动紧凑化（如果需要）
        if self.config.auto_compact:
            self._auto_compact_if_needed()

        return result

    def _default_process(self, prompt: str, tools: Optional[List[str]], agents: Optional[List[str]]) -> str:
        """默认处理函数（模拟）"""

        # 模拟响应
        response_parts = [f"收到您的请求: {prompt[:50]}..."]

        if tools:
            response_parts.append(f"可用工具: {', '.join(tools[:3])}")

        if agents:
            response_parts.append(f"可用Agent: {', '.join(agents[:3])}")

        response_parts.append("正在处理...")

        return " | ".join(response_parts)

    def _match_tools(self, prompt: str, tools: List[str]) -> List[str]:
        """匹配相关工具"""
        if not tools:
            return []

        # 简单关键词匹配
        matched = []
        prompt_lower = prompt.lower()

        for tool in tools:
            tool_lower = tool.lower()
            # 如果工具名出现在提示词中，认为匹配
            if tool_lower in prompt_lower:
                matched.append(tool)

        return matched

    def _match_agents(self, prompt: str, agents: List[str]) -> List[str]:
        """匹配相关Agent"""
        if not agents:
            return []

        # 简单关键词匹配
        matched = []
        prompt_lower = prompt.lower()

        for agent in agents:
            agent_lower = agent.lower()
            if agent_lower in prompt_lower:
                matched.append(agent)

        return matched

    def _determine_stop_reason(self) -> StopReason:
        """确定停止原因"""
        if self._turn_count >= self.config.max_turns:
            return StopReason.MAX_TURNS_REACHED

        total_tokens = self._input_tokens + self._output_tokens
        if total_tokens >= self.config.max_budget_tokens:
            return StopReason.MAX_BUDGET_REACHED

        return StopReason.COMPLETED

    def _auto_compact_if_needed(self):
        """如果需要，自动紧凑化消息"""
        total_tokens = self._input_tokens + self._output_tokens

        # 检查是否需要紧凑化
        should_compact = (
            self._turn_count >= self.config.compact_after_turns or total_tokens >= self.config.compact_threshold_tokens
        )

        if should_compact and len(self._messages) > 2:
            # 执行紧凑化
            target_tokens = self.config.compact_threshold_tokens // 2
            self._messages, new_tokens = self._compactor.compact_messages(self._messages, target_tokens, total_tokens)

            # 更新token统计（简化处理）
            # 注意：实际中应该使用更精确的tokenizer

    def get_compact_summary(self) -> str:
        """获取紧凑化摘要"""
        return self._compactor.summarize_messages(self._messages)

    def save_state(self, path: Optional[Path] = None) -> Path:
        """保存引擎状态"""
        if path is None:
            path = Path(".lingflow/query_engine_states") / f"{self.session_id}.json"

        path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "session_id": self.session_id,
            "config": {
                "max_turns": self.config.max_turns,
                "max_budget_tokens": self.config.max_budget_tokens,
                "compact_after_turns": self.config.compact_after_turns,
                "auto_compact": self.config.auto_compact,
            },
            "messages": self._messages,
            "usage": self.usage_summary.to_dict(),
            "history": [
                {
                    "prompt": r.prompt,
                    "output": r.output,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "stop_reason": r.stop_reason.value,
                }
                for r in self._history
            ],
            "saved_at": datetime.now().isoformat(),
        }

        with open(path, "w") as f:
            json.dump(state, f, indent=2)

        return path

    @classmethod
    def load_state(cls, path: Path) -> "QueryEngine":
        """加载引擎状态"""
        with open(path) as f:
            state = json.load(f)

        # 重建配置
        config = QueryEngineConfig(
            max_turns=state["config"]["max_turns"],
            max_budget_tokens=state["config"]["max_budget_tokens"],
            compact_after_turns=state["config"]["compact_after_turns"],
            auto_compact=state["config"]["auto_compact"],
        )

        # 创建引擎
        engine = cls(config, session_id=state["session_id"])

        # 恢复状态
        engine._messages = state["messages"]
        engine._input_tokens = state["usage"]["total_input_tokens"]
        engine._output_tokens = state["usage"]["total_output_tokens"]
        engine._turn_count = state["usage"]["turn_count"]

        return engine

    def reset(self):
        """重置引擎状态"""
        self._messages.clear()
        self._input_tokens = 0
        self._output_tokens = 0
        self._turn_count = 0
        self._history.clear()

    def get_history(self) -> List[TurnResult]:
        """获取查询历史"""
        return self._history.copy()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "session_id": self.session_id,
            "turn_count": self._turn_count,
            "message_count": len(self._messages),
            "usage": self.usage_summary.to_dict(),
            "config": {
                "max_turns": self.config.max_turns,
                "max_budget_tokens": self.config.max_budget_tokens,
                "compact_after_turns": self.config.compact_after_turns,
                "auto_compact": self.config.auto_compact,
            },
        }


# ============================================================================
# 便捷函数
# ============================================================================


def create_default_engine() -> QueryEngine:
    """创建默认配置的QueryEngine"""
    config = QueryEngineConfig()
    return QueryEngine(config)


def create_budget_conscious_engine(budget: int) -> QueryEngine:
    """创建预算敏感的QueryEngine"""
    config = QueryEngineConfig(max_budget_tokens=budget, compact_after_turns=6, auto_compact=True)  # 更早紧凑化
    return QueryEngine(config)


def create_long_conversation_engine() -> QueryEngine:
    """创建长对话QueryEngine"""
    config = QueryEngineConfig(max_turns=20, max_budget_tokens=500000, compact_after_turns=15, auto_compact=True)
    return QueryEngine(config)
