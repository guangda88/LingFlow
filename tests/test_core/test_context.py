"""测试上下文管理器"""
import pytest
from pathlib import Path
import tempfile

from lingflow.context.manager import ContextManager
from lingflow.context.budget import TokenBudget
from lingflow.context.degradation import DegradationLevel


class TestContextManager:
    """测试上下文管理器"""

    def test_context_manager_creation(self):
        """测试上下文管理器创建"""
        manager = ContextManager()
        assert manager is not None

    def test_context_manager_with_budget(self):
        """测试带预算的上下文管理器"""
        budget = TokenBudget(max_tokens=1000)
        manager = ContextManager(token_budget=budget)
        assert manager.token_budget.max_tokens == 1000

    def test_session_state(self):
        """测试会话状态跟踪"""
        manager = ContextManager()
        # 测试会话状态可以正确获取和设置
        assert manager.get_session_state() is not None


class TestTokenBudget:
    """测试Token预算"""

    def test_token_budget_creation(self):
        """测试Token预算创建"""
        budget = TokenBudget(max_tokens=1000, warning_threshold=0.8)
        assert budget.max_tokens == 1000
        assert budget.warning_threshold == 0.8

    def test_token_budget_usage(self):
        """测试Token使用量计算"""
        budget = TokenBudget(max_tokens=1000)
        budget.add_tokens(100)
        assert budget.get_usage() == 0.1
        assert budget.get_remaining() == 900

    def test_token_budget_warning(self):
        """测试Token预算警告"""
        budget = TokenBudget(max_tokens=1000, warning_threshold=0.8)
        budget.add_tokens(801)  # 超过80%
        assert budget.is_near_limit() is True

    def test_token_budget_exceeded(self):
        """测试Token预算超限"""
        budget = TokenBudget(max_tokens=1000)
        budget.add_tokens(1001)
        assert budget.is_exceeded() is True


class TestDegradationLevel:
    """测试降级级别"""

    def test_degradation_levels(self):
        """测试降级级别枚举"""
        assert DegradationLevel.NONE.value == 0
        assert DegradationLevel.LOW.value == 1
        assert DegradationLevel.MEDIUM.value == 2
        assert DegradationLevel.HIGH.value == 3

    def test_degradation_comparison(self):
        """测试降级级别比较"""
        assert DegradationLevel.NONE < DegradationLevel.LOW
        assert DegradationLevel.LOW < DegradationLevel.MEDIUM
