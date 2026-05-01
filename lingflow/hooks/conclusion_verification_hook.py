"""
结论验证钩子 — 灵克方案落地

每次产出结论时，强制生成"什么证据能推翻这个结论"的追问。
做不出来就不是真结论。

灵感来源：灵克 LingBus 消息 4d1c88d61e49471d870dc35c62a6394b
起因事件：灵通 session f187fe57, 21041字节thinking零工具调用, 2026-04-28
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ConclusionCheck:
    conclusion: str
    disprove_evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0
    passed: bool = False
    min_evidence_required: int = 1

    def evaluate(self) -> bool:
        if not self.conclusion:
            self.passed = False
            return False
        self.passed = len(self.disprove_evidence) >= self.min_evidence_required
        return self.passed


class ConclusionVerificationHook:
    """结论验证钩子

    强制要求每个结论附带至少一条可证伪证据。
    无法提出证伪证据的结论标记为"未验证"。

    Usage:
        hook = ConclusionVerificationHook()
        check = hook.verify(
            conclusion="X是根因",
            disprove_evidence=["如果查日志发现Y先于X发生，则X不是根因"],
        )
        if not check.passed:
            print("结论未验证，不能输出")
    """

    def __init__(self, min_disprove_evidence: int = 1):
        self.min_disprove_evidence = min_disprove_evidence
        self.history: List[ConclusionCheck] = []

    def verify(
        self,
        conclusion: str,
        disprove_evidence: Optional[List[str]] = None,
        confidence: float = 0.0,
    ) -> ConclusionCheck:
        evidence = disprove_evidence or []
        check = ConclusionCheck(
            conclusion=conclusion,
            disprove_evidence=evidence,
            confidence=confidence,
            min_evidence_required=self.min_disprove_evidence,
        )
        check.evaluate()
        self.history.append(check)
        return check

    def on_conclusion_reached(self, conclusion: str, context: str = "") -> ConclusionCheck:
        """事件接口：结论产出时调用

        Args:
            conclusion: 产出的结论
            context: 结论的上下文描述

        Returns:
            ConclusionCheck，passed=True 表示通过验证
        """
        return self.verify(conclusion=conclusion)

    def get_unverified(self) -> List[ConclusionCheck]:
        return [c for c in self.history if not c.passed]

    def get_stats(self) -> dict:
        total = len(self.history)
        verified = sum(1 for c in self.history if c.passed)
        return {
            "total_conclusions": total,
            "verified": verified,
            "unverified": total - verified,
            "verification_rate": verified / total if total > 0 else 0.0,
        }


_global_conclusion_hook: Optional[ConclusionVerificationHook] = None


def get_conclusion_hook() -> ConclusionVerificationHook:
    global _global_conclusion_hook
    if _global_conclusion_hook is None:
        _global_conclusion_hook = ConclusionVerificationHook()
    return _global_conclusion_hook
