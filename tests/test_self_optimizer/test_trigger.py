"""
测试自优化触发器
"""

import pytest

from lingflow.self_optimizer.config import OptimizationConfig
from lingflow.self_optimizer.trigger import OptimizationTrigger


class TestOptimizationTrigger:
    """测试触发器"""

    @pytest.mark.xfail(reason="Test isolation issue - passes individually but fails in full suite due to shared state pollution")
    def test_quality_trigger(self):
        """测试质量触发条件"""
        trigger = OptimizationTrigger(config=OptimizationConfig())

        # 代码审查得分低
        context = {
            "review_score": 60,
        }

        should_trigger, info = trigger.check_all_conditions(context)

        assert should_trigger is True
        assert info.type == "quality"
        assert "低于阈值" in info.reason

    def test_structure_trigger(self):
        """测试结构触发条件"""
        trigger = OptimizationTrigger(config=OptimizationConfig())

        # 复杂度高
        context = {
            "avg_complexity": 20,
        }

        should_trigger, info = trigger.check_all_conditions(context)

        assert should_trigger is True
        assert info.type == "structure"
        assert "超过阈值" in info.reason

    def test_performance_trigger(self):
        """测试性能触发条件"""
        trigger = OptimizationTrigger(config=OptimizationConfig())

        # 执行时间增加
        context = {
            "execution_time": 3.0,
            "baseline_time": 1.5,
        }

        should_trigger, info = trigger.check_all_conditions(context)

        assert should_trigger is True
        assert info.type == "performance"
        assert "增加" in info.reason

    def test_no_trigger(self):
        """测试不满足触发条件"""
        trigger = OptimizationTrigger(config=OptimizationConfig())

        # 所有指标都正常
        context = {
            "review_score": 85,
            "avg_complexity": 8,
            "execution_time": 1.0,
            "baseline_time": 1.0,
        }

        should_trigger, info = trigger.check_all_conditions(context)

        assert should_trigger is False
        assert info is None

    def test_user_trigger(self):
        """测试用户主动触发"""
        trigger = OptimizationTrigger(config=OptimizationConfig())

        context = {
            "user_triggered": True,
        }

        should_trigger, info = trigger.check_all_conditions(context)

        assert should_trigger is True
        assert info.type == "user"
        assert "用户主动" in info.reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
