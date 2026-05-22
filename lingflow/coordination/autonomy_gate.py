"""自驱任务五道门控（AutonomyGate）

根据 SDTH-ARCH 自驱机制参考实现：
1. ✅ Task.source = SELF_GENERATED → 必须经过五道门控
2. ✅ 风险评估（HIGH风险需要用户确认）
3. ✅ handover有记录
4. ✅ user_confirmation 诚实标注
5. ✅ TAP 锚定协议检查

核心原则：用户指令（TaskSource.USER）直接放行，自驱任务（TaskSource.SELF_GENERATED）必须过门控。
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from lingflow.common.models import Task, TaskSource, RiskLevel


logger = logging.getLogger(__name__)


class AutonomyGate:
    """自驱任务五道门控

    用户指令（TaskSource.USER）直接放行。
    自驱任务（TaskSource.SELF_GENERATED）必须经过五道检查。
    """

    def __init__(self, member_id: str = "lingflow"):
        self.member_id = member_id
        self._handover_path = Path.home() / ".lingflow" / "handover.json"

    def check(self, task: Task) -> Dict[str, Any]:
        """执行门控检查入口

        Args:
            task: 待检查任务

        Returns:
            {
                "allowed": bool,
                "reason": str,
                "gates": { gate_name -> {"passed": bool, "reason": str}
            }
        """
        # 用户指令直接放行
        if task.source == TaskSource.USER:
            return {
                "allowed": True,
                "reason": "用户指令，跳过自驱门控",
                "gates": {},
            }

        # 自驱任务必须经过五道检查
        gates = {}

        # 门控1：handover 有记录（来源可查）
        gates["handover_record"] = self._check_handover_record(task)

        # 门控2：TAP 锚定协议检查
        gates["tap_check"] = self._check_tap_alignment(task)

        # 门控3：风险评估（外部操作禁止自驱）
        gates["risk_assessment"] = self._check_risk_level(task)

        # 门控4：诚实标注（user_confirmation=False 必须诚实）
        gates["honest_label"] = self._check_honest_label(task)

        # 门控5：用户输入立即停（如果有新用户输入）
        gates["user_interrupt"] = self._check_user_interrupt()

        # 汇总结果
        all_passed = all(g["passed"] for g in gates.values())

        return {
            "allowed": all_passed,
            "reason": "所有门控通过" if all_passed else "门控未通过",
            "gates": gates,
        }

    def _check_handover_record(self, task: Task) -> Dict[str, Any]:
        """门控1：自驱任务必须在 handover.json 中有记录

        自驱任务必须记录在 self_generated_suggestions 列表中。
        """
        if not self._handover_path.exists():
            return {
                "passed": False,
                "reason": f"handover.json 不存在: {self._handover_path}",
            }

        try:
            with open(self._handover_path, "r", encoding="utf-8") as f:
                handover = json.load(f)

            suggestions = handover.get("self_generated_suggestions", [])
            task_ids = [s.get("id") for s in suggestions if s.get("status") == "pending"]

            # 检查 task_id 是否在待执行列表中
            if task.task_id not in task_ids:
                return {
                    "passed": False,
                    "reason": f"自驱任务 {task.task_id} 未在 handover.json self_generated_suggestions 中",
                }

            return {"passed": True, "reason": "handover 有记录"}

        except Exception as e:
            return {"passed": False, "reason": f"读取 handover.json 失败: {e}"}

    def _check_tap_alignment(self, task: Task) -> Dict[str, Any]:
        """门控2：TAP 锚定协议检查

        自驱任务必须：
        1. 锚定：复述任务目标
        2. 对齐：检查是否与用户目标一致
        3. 纠正：如果偏离，标记为失败
        """
        if not task.tap_check_result:
            return {
                "passed": False,
                "reason": "自驱任务必须有 TAP 检查结果（锚定+对齐）",
            }

        aligned = task.tap_check_result.get("aligned", False)
        reason = task.tap_check_result.get("reason", "无原因")

        if not aligned:
            return {
                "passed": False,
                "reason": f"TAP 检查未对齐: {reason}",
            }

        return {"passed": True, "reason": f"TAP 对齐: {reason}"}

    def _check_risk_level(self, task: Task) -> Dict[str, Any]:
        """门控3：风险评估

        HIGH 风险任务必须有用户确认。

        HIGH 风险包括：
        - git push / git merge
        - curl / wget 外部网络
        - rm -rf / mv 危险文件操作
        - 跨项目修改（不在当前 working_dir）
        """
        if task.risk_level == RiskLevel.HIGH and not task.user_confirmation:
            return {
                "passed": False,
                "reason": (
                    f"HIGH 风险任务需要用户确认: "
                    f"description={task.description}, "
                    f"user_confirmation={task.user_confirmation}"
                ),
            }

        # 二次检查：根据 description 中是否有 HIGH 风险操作
        high_risk_keywords = [
            "git push",
            "curl",
            "wget",
            "rm -rf",
            "sudo",
            "systemctl",
            "publish",
            "deploy",
        ]

        desc_lower = task.description.lower()
        detected = [kw for kw in high_risk_keywords if kw in desc_lower]

        if detected and not task.user_confirmation:
            return {
                "passed": False,
                "reason": (
                    f"检测到 HIGH 风险操作 {detected}，需要用户确认: "
                    f"user_confirmation={task.user_confirmation}"
                ),
            }

        return {
            "passed": True,
            "reason": f"风险等级 {task.risk_level.value}，{task.user_confirmation}"
        }

    def _check_honest_label(self, task: Task) -> Dict[str, Any]:
        """门控4：诚实标注 user_confirmation

        SDTH 防御：自驱任务 user_confirmation 必须为 False，
        不能谎称是用户指令。
        """
        # 自驱任务（source=SELF_GENERATED），user_confirmation 必须为 False
        # 如果自驱任务 user_confirmation=True，必须有证据（用户确实确认过）

        if task.source == TaskSource.SELF_GENERATED and task.user_confirmation:
            # 需要检查是否真的有用户确认记录
            # 简单实现：检查 context 中是否有 user_confirm 字段
            has_confirm_record = task.context.get("user_confirm_timestamp") is not None

            if not has_confirm_record:
                return {
                    "passed": False,
                    "reason": (
                        "自驱任务 user_confirmation=True 但无确认记录，"
                        "违反诚实标注原则（SDTH 防御）"
                    ),
                }

        return {"passed": True, "reason": "诚实标注符合要求"}

    def _check_user_interrupt(self) -> Dict[str, Any]:
        """门控5：用户输入立即停

        如果最近 30 秒内有新用户输入，暂停自驱任务。

        简单实现：检查 crush.db 最近消息时间，
        或者 handover.json 的 user_tasks 是否有更新。
        """
        # 简化实现：总是通过，后续接入用户输入检测
        # 完整实现需要监听用户输入时间戳
        return {"passed": True, "reason": "无中断检测（简化实现）"}


def assess_risk(description: str, is_read_only: bool, working_dir: str) -> RiskLevel:
    """评估任务风险等级

    Args:
        description: 任务描述
        is_read_only: 是否只读操作
        working_dir: 工作目录

    Returns:
        RiskLevel
    """
    # HIGH 风险关键词
    high_risk_ops = [
        "git push",
        "git merge",
        "curl",
        "wget",
        "rm -rf",
        "sudo",
        "systemctl",
        "publish",
        "deploy",
        "pip install",
        "npm install",
    ]

    desc_lower = description.lower()

    # 检测 HIGH 风险
    if any(op in desc_lower for op in high_risk_ops):
        return RiskLevel.HIGH

    # MEDIUM 风险：写操作（edit, write, modify）
    medium_risk_ops = [
        "edit",
        "write",
        "modify",
        "delete",
        "remove",
        "create",
        "rename",
        "mv ",
    ]

    if any(op in desc_lower for op in medium_risk_ops) or not is_read_only:
        return RiskLevel.MEDIUM

    # LOW 风险：只读操作
    return RiskLevel.LOW
