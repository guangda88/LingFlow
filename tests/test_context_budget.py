#!/usr/bin/env python3
"""上下文预算管理器测试

测试 ContextBudgetManager 的各项功能:
1. 预算级别判定（SAFE/MODERATE/WARNING/CRITICAL/EMERGENCY）
2. 安全阈值计算
3. 压缩/交接决策
4. Agent 预算分配
"""

import pytest
from lingflow.context.budget import (
    ContextBudgetManager,
    BudgetLevel,
    BudgetStatus,
)


class TestBudgetLevels:
    """预算级别判定测试"""

    def test_safe_level(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(20000)
        assert status.level == BudgetLevel.SAFE
        assert status.usage_ratio == 0.2

    def test_moderate_level(self):
        bm = ContextBudgetManager(max_tokens=100000)
        # 30% * 0.75 = 22.5%, but moderate starts at safety_ratio*0.75 = 30%
        # moderate: >= safety_ratio*0.75 and < safety_ratio
        status = bm.check_budget(35000)
        assert status.level == BudgetLevel.MODERATE

    def test_warning_level(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(45000)
        assert status.level == BudgetLevel.WARNING

    def test_critical_level(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(65000)
        assert status.level == BudgetLevel.CRITICAL

    def test_emergency_level(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(85000)
        assert status.level == BudgetLevel.EMERGENCY

    def test_exact_boundary_warning(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(40000)
        assert status.level == BudgetLevel.WARNING

    def test_exact_boundary_critical(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(60000)
        assert status.level == BudgetLevel.CRITICAL

    def test_exact_boundary_emergency(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(80000)
        assert status.level == BudgetLevel.EMERGENCY

    def test_zero_tokens(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(0)
        assert status.level == BudgetLevel.SAFE
        assert status.usage_ratio == 0.0

    def test_full_tokens(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(100000)
        assert status.level == BudgetLevel.EMERGENCY


class TestBudgetThresholds:
    """阈值计算测试"""

    def test_safe_budget(self):
        bm = ContextBudgetManager(max_tokens=180000, safety_ratio=0.4)
        assert bm.safe_budget == 72000

    def test_warning_budget(self):
        bm = ContextBudgetManager(max_tokens=180000)
        assert bm.warning_budget == 72000

    def test_critical_budget(self):
        bm = ContextBudgetManager(max_tokens=180000)
        assert bm.critical_budget == 108000

    def test_emergency_budget(self):
        bm = ContextBudgetManager(max_tokens=180000)
        assert bm.emergency_budget == 144000

    def test_custom_safety_ratio(self):
        bm = ContextBudgetManager(max_tokens=100000, safety_ratio=0.3)
        assert bm.safe_budget == 30000


class TestCompactAndHandoff:
    """压缩/交接决策测试"""

    def test_should_compact_below_threshold(self):
        bm = ContextBudgetManager(max_tokens=100000)
        assert bm.should_compact(30000) is False

    def test_should_compact_above_threshold(self):
        bm = ContextBudgetManager(max_tokens=100000)
        assert bm.should_compact(45000) is True

    def test_should_handoff_below_threshold(self):
        bm = ContextBudgetManager(max_tokens=100000)
        assert bm.should_handoff(70000) is False

    def test_should_handoff_above_threshold(self):
        bm = ContextBudgetManager(max_tokens=100000)
        assert bm.should_handoff(85000) is True


class TestTargetTokens:
    """压缩目标计算测试"""

    def test_target_when_safe(self):
        bm = ContextBudgetManager(max_tokens=100000)
        assert bm.get_target_tokens(20000) == 20000

    def test_target_when_warning(self):
        bm = ContextBudgetManager(max_tokens=100000)
        target = bm.get_target_tokens(50000)
        assert target < 50000
        assert target > 0

    def test_target_when_critical(self):
        bm = ContextBudgetManager(max_tokens=100000)
        target = bm.get_target_tokens(70000)
        warning_target = bm.get_target_tokens(50000)
        assert target < warning_target


class TestAgentBudgetAllocation:
    """Agent 预算分配测试"""

    def test_default_allocation(self):
        bm = ContextBudgetManager(max_tokens=180000, agent_context_limit=8000)
        budget = bm.allocate_agent_budget("implementation")
        assert budget > 0
        assert budget <= bm.safe_budget

    def test_critical_priority_gets_more(self):
        bm = ContextBudgetManager(max_tokens=180000, agent_context_limit=8000)
        critical = bm.allocate_agent_budget("agent", priority=0)
        normal = bm.allocate_agent_budget("agent", priority=2)
        assert critical >= normal

    def test_low_priority_gets_less(self):
        bm = ContextBudgetManager(max_tokens=180000, agent_context_limit=8000)
        normal = bm.allocate_agent_budget("agent", priority=2)
        low = bm.allocate_agent_budget("agent", priority=3)
        assert low <= normal

    def test_no_overflow(self):
        bm = ContextBudgetManager(max_tokens=180000, agent_context_limit=8000)
        budget = bm.allocate_agent_budget("agent", priority=0)
        assert budget <= bm.safe_budget


class TestBudgetStatusDict:
    """BudgetStatus 序列化测试"""

    def test_to_dict(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.check_budget(50000)
        d = status.to_dict()
        assert "level" in d
        assert "current_tokens" in d
        assert "max_tokens" in d
        assert "usage_ratio" in d
        assert "recommended_action" in d
        assert d["level"] in ["safe", "moderate", "warning", "critical", "emergency"]

    def test_get_status(self):
        bm = ContextBudgetManager(max_tokens=100000)
        status = bm.get_status(50000)
        assert "budget_status" in status
        assert "safe_budget" in status
        assert "warning_budget" in status


class TestTokenEstimation:
    """Token 估算集成测试"""

    def test_estimate_text(self):
        bm = ContextBudgetManager()
        tokens = bm.estimate_text_tokens("Hello, world!")
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_empty(self):
        bm = ContextBudgetManager()
        assert bm.estimate_text_tokens("") == 0

    def test_estimate_chinese(self):
        bm = ContextBudgetManager()
        tokens = bm.estimate_text_tokens("你好世界")
        assert tokens > 0
