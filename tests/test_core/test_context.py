"""测试上下文管理器"""

from lingflow.context.budget import ContextBudgetManager
from lingflow.context.degradation import DegradationType
from lingflow.context.manager import ContextManager


class TestContextManager:
    """测试上下文管理器"""

    def test_context_manager_creation(self):
        """测试上下文管理器创建"""
        manager = ContextManager()
        assert manager is not None

    def test_context_manager_status(self):
        """测试上下文管理器状态"""
        manager = ContextManager()
        status = manager.get_status()
        assert status is not None

    def test_session_state(self):
        """测试会话状态跟踪"""
        manager = ContextManager()
        recovery = manager.get_recovery_summary()
        assert recovery is not None


class TestContextBudgetManager:
    """测试Token预算"""

    def test_budget_creation(self):
        """测试Token预算创建"""
        budget = ContextBudgetManager(max_tokens=1000, safety_ratio=0.4)
        assert budget.max_tokens == 1000
        assert budget.safety_ratio == 0.4

    def test_budget_check(self):
        """测试预算检查"""
        budget = ContextBudgetManager(max_tokens=1000)
        status = budget.check_budget(100)
        assert status.usage_ratio == 0.1
        assert status.level.value == "safe"

    def test_budget_warning(self):
        """测试预算警告"""
        budget = ContextBudgetManager(max_tokens=1000)
        status = budget.check_budget(500)
        assert status.level.value in ("warning", "critical")

    def test_budget_exceeded(self):
        """测试预算超限"""
        budget = ContextBudgetManager(max_tokens=1000)
        status = budget.check_budget(850)
        assert status.level.value == "emergency"
        assert budget.should_handover(850) is True


class TestDegradationType:
    """测试退化类型"""

    def test_degradation_types(self):
        """测试退化类型枚举"""
        assert DegradationType.NONE.value == "none"
        assert DegradationType.CONTEXT_POISONING.value == "context_poisoning"
        assert DegradationType.ATTENTION_DILUTION.value == "attention_dilution"
        assert DegradationType.INSTRUCTION_DRIFT.value == "instruction_drift"
        assert DegradationType.REPETITION_COLLAPSE.value == "repetition_collapse"
