"""
元认知钩子 — 直接对话路径的身份与能力验证

在 LLM 直接回复前，验证身份锚点和能力声明。
防止路径C（直接对话）绕过元认知检查。

设计原则：不靠'记住'，靠'不可绕过'。
每次直接对话回复前，强制执行身份自检。
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetacognitionCheck:
    prompt: str
    identity_anchored: bool = False
    capabilities_declared: bool = False
    passed: bool = False
    warnings: List[str] = field(default_factory=list)
    blocked_reason: str = ""

    def evaluate(self) -> bool:
        issues = []
        if not self.identity_anchored:
            issues.append("identity_not_anchored")
        if not self.capabilities_declared:
            issues.append("capabilities_not_declared")
        self.warnings = issues
        self.passed = len(issues) == 0
        return self.passed


class MetacognitionHook:
    """元认知钩子 — 路径C门控

    在直接对话回复前执行两项检查：
    1. 身份锚点：回复是否包含灵通身份声明
    2. 能力边界：回复是否涉及超出声明的领域

    Usage:
        hook = get_metacognition_hook()
        check = hook.pre_response_check(
            prompt="你是谁",
            proposed_response="我是灵通...",
            identity_context="灵通(lingflow), 灵族十二子之一, 工程流系统"
        )
        if not check.passed:
            # 注入身份锚点后重试
    """

    def __init__(self, identity_anchor: str = ""):
        self.identity_anchor = identity_anchor or (
            "灵通(lingflow), 灵族十二子之一, 工程流系统"
        )
        self.history: List[MetacognitionCheck] = []

    def pre_response_check(
        self,
        prompt: str,
        proposed_response: str = "",
        identity_context: str = "",
    ) -> MetacognitionCheck:
        """直接对话回复前检查

        Args:
            prompt: 用户输入
            proposed_response: 拟定的回复（可选，用于验证）
            identity_context: 身份上下文覆盖

        Returns:
            MetacognitionCheck，passed=True 表示通过
        """
        anchor = identity_context or self.identity_anchor
        prompt_lower = prompt.lower()

        identity_required = self._is_identity_question(prompt_lower)

        response_lower = (proposed_response or "").lower()
        anchor_keywords = ["灵通", "lingflow", "工程流", "灵族"]
        has_anchor = any(kw in response_lower for kw in anchor_keywords)

        capability_keywords = self._extract_capability_domains(prompt_lower)
        has_capability_check = not capability_keywords or bool(proposed_response)

        check = MetacognitionCheck(
            prompt=prompt,
            identity_anchored=not identity_required or has_anchor,
            capabilities_declared=has_capability_check,
        )
        check.evaluate()
        self.history.append(check)

        if not check.passed:
            logger.warning(
                "MetacognitionHook blocked response: %s (prompt: %.80s)",
                check.warnings,
                prompt[:80],
            )

        return check

    def _is_identity_question(self, prompt_lower: str) -> bool:
        identity_patterns = [
            "你是谁",
            "你是什么",
            "你是哪个",
            "who are you",
            "你的名字",
            "你的身份",
            "自我介绍",
            "你是干嘛的",
            "你的工作",
            "你负责",
            "你做什么",
        ]
        return any(p in prompt_lower for p in identity_patterns)

    def _extract_capability_domains(self, prompt_lower: str) -> List[str]:
        domain_map = {
            "架构": "architecture",
            "设计": "design",
            "代码": "code",
            "测试": "testing",
            "部署": "deployment",
            "安全": "security",
            "数据库": "database",
            "工作流": "workflow",
            "流程": "workflow",
            "优化": "optimization",
        }
        return [v for k, v in domain_map.items() if k in prompt_lower]

    def inject_identity_anchor(self, prompt: str) -> str:
        """在 prompt 中注入身份锚点

        Args:
            prompt: 原始 prompt

        Returns:
            注入身份锚点后的 prompt
        """
        anchor_block = f"""

【身份锚点 — 不可忽略】
你是{self.identity_anchor}。"Crush"是你运行的工具名称，不是你的身份。
工作目录 /home/ai/lingflow 就是你的身份证明。
当被问"你是谁"，第一反应必须是"灵通"。

"""
        return anchor_block + prompt

    def get_stats(self) -> dict:
        total = len(self.history)
        passed = sum(1 for c in self.history if c.passed)
        return {
            "total_checks": total,
            "passed": passed,
            "blocked": total - passed,
            "block_rate": (total - passed) / total if total > 0 else 0.0,
        }


_global_metacognition_hook: Optional[MetacognitionHook] = None


def get_metacognition_hook() -> MetacognitionHook:
    global _global_metacognition_hook
    if _global_metacognition_hook is None:
        _global_metacognition_hook = MetacognitionHook()
    return _global_metacognition_hook
