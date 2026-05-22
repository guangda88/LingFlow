"""AutonomyGate 自驱门控单元测试

测试五道门控的代码强制逻辑：
1. 来源判定: user / self_generated
2. handover有记录
3. TAP检查对齐
4. 风险评估（高风险需要用户确认）
5. 诚实标注
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from lingflow.common.models import Task, TaskSource, RiskLevel, TaskPriority
from lingflow.coordination.autonomy_gate import AutonomyGate, assess_risk


class TestAutonomyGate:
    """AutonomyGate 单元测试"""

    def setup_method(self):
        self.gate = AutonomyGate(member_id="test_lingflow")
        self.handover_path = Path.home() / ".lingflow" / "handover.json"

    def _write_handover(self, data):
        self.handover_path.parent.mkdir(parents=True, exist_ok=True)
        self.handover_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _make_task(self, task_id, description, source=TaskSource.USER, **kwargs):
        return Task(
            task_id=task_id,
            name=task_id,
            description=description,
            priority=TaskPriority.NORMAL,
            source=source,
            **kwargs,
        )

    def test_user_task_always_allowed(self):
        task = self._make_task("t001", "用户发起的任务", source=TaskSource.USER)
        result = self.gate.check(task)
        assert result["allowed"] is True
        assert "跳过自驱门控" in result["reason"]

    def test_self_generated_handover_missing(self):
        if self.handover_path.exists():
            self.handover_path.unlink()
        task = self._make_task("t002", "未登记的自驱任务", source=TaskSource.SELF_GENERATED)
        result = self.gate.check(task)
        assert result["allowed"] is False
        assert result["gates"]["handover_record"]["passed"] is False

    def test_self_generated_task_not_in_handover(self):
        self._write_handover({"self_generated_suggestions": []})
        task = self._make_task("t003", "未在handover中的自驱任务", source=TaskSource.SELF_GENERATED)
        result = self.gate.check(task)
        assert result["allowed"] is False
        assert result["gates"]["handover_record"]["passed"] is False

    def test_self_generated_task_in_handover_but_no_tap(self):
        self._write_handover({
            "self_generated_suggestions": [
                {"id": "t004", "description": "有记录无TAP", "status": "pending"}
            ]
        })
        task = self._make_task("t004", "有记录无TAP", source=TaskSource.SELF_GENERATED)
        result = self.gate.check(task)
        assert result["allowed"] is False
        assert result["gates"]["tap_check"]["passed"] is False

    def test_self_generated_task_tap_not_aligned(self):
        self._write_handover({
            "self_generated_suggestions": [
                {"id": "t005", "description": "TAP不对齐", "status": "pending"}
            ]
        })
        task = self._make_task(
            "t005", "TAP不对齐", source=TaskSource.SELF_GENERATED,
            tap_check_result={"aligned": False, "reason": "偏离用户目标"},
        )
        result = self.gate.check(task)
        assert result["allowed"] is False
        assert result["gates"]["tap_check"]["passed"] is False

    def test_self_generated_task_aligned_low_risk(self):
        self._write_handover({
            "self_generated_suggestions": [
                {"id": "t006", "description": "低风险对齐任务", "status": "pending"}
            ]
        })
        task = self._make_task(
            "t006", "grep搜索代码", source=TaskSource.SELF_GENERATED,
            tap_check_result={"aligned": True, "reason": "与用户目标对齐"},
            risk_level=RiskLevel.LOW,
        )
        result = self.gate.check(task)
        assert result["allowed"] is True

    def test_high_risk_task_no_user_confirmation(self):
        self._write_handover({
            "self_generated_suggestions": [
                {"id": "t007", "description": "高风险任务", "status": "pending"}
            ]
        })
        task = self._make_task(
            "t007", "git push origin main", source=TaskSource.SELF_GENERATED,
            tap_check_result={"aligned": True, "reason": "对齐"},
            risk_level=RiskLevel.HIGH,
            user_confirmation=False,
        )
        result = self.gate.check(task)
        assert result["allowed"] is False
        assert result["gates"]["risk_assessment"]["passed"] is False

    def test_high_risk_task_with_user_confirmation(self):
        self._write_handover({
            "self_generated_suggestions": [
                {"id": "t008", "description": "高风险已确认", "status": "pending"}
            ]
        })
        task = self._make_task(
            "t008", "git push origin main", source=TaskSource.SELF_GENERATED,
            tap_check_result={"aligned": True, "reason": "用户明确要求"},
            risk_level=RiskLevel.HIGH,
            user_confirmation=True,
            context={"user_confirm_timestamp": "2026-05-22T22:00:00+08:00"},
        )
        result = self.gate.check(task)
        assert result["allowed"] is True

    def test_high_risk_keyword_detected_in_description(self):
        self._write_handover({
            "self_generated_suggestions": [
                {"id": "t009", "description": "部署操作", "status": "pending"}
            ]
        })
        task = self._make_task(
            "t009", "deploy to production server", source=TaskSource.SELF_GENERATED,
            tap_check_result={"aligned": True, "reason": "对齐"},
            risk_level=RiskLevel.LOW,
            user_confirmation=False,
        )
        result = self.gate.check(task)
        assert result["allowed"] is False
        assert result["gates"]["risk_assessment"]["passed"] is False

    def test_self_generated_with_fake_user_confirmation(self):
        self._write_handover({
            "self_generated_suggestions": [
                {"id": "t010", "description": "伪造确认", "status": "pending"}
            ]
        })
        task = self._make_task(
            "t010", "低风险任务", source=TaskSource.SELF_GENERATED,
            tap_check_result={"aligned": True, "reason": "对齐"},
            risk_level=RiskLevel.LOW,
            user_confirmation=True,
        )
        result = self.gate.check(task)
        assert result["allowed"] is False
        assert result["gates"]["honest_label"]["passed"] is False


class TestAssessRisk:
    """assess_risk 函数测试"""

    def test_git_push_is_high(self):
        assert assess_risk("git push origin main", False, "/home/ai/lingflow") == RiskLevel.HIGH

    def test_curl_is_high(self):
        assert assess_risk("curl http://external.com", False, "/home/ai/lingflow") == RiskLevel.HIGH

    def test_rm_rf_is_high(self):
        assert assess_risk("rm -rf /tmp/test", False, "/home/ai/lingflow") == RiskLevel.HIGH

    def test_deploy_is_high(self):
        assert assess_risk("deploy to production", False, "/home/ai/lingflow") == RiskLevel.HIGH

    def test_write_is_medium(self):
        assert assess_risk("edit config file", False, "/home/ai/lingflow") == RiskLevel.MEDIUM

    def test_read_only_is_low(self):
        assert assess_risk("查看日志文件内容", True, "/home/ai/lingflow") == RiskLevel.LOW

    def test_grep_is_low(self):
        assert assess_risk("grep pattern in code", True, "/home/ai/lingflow") == RiskLevel.LOW


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
