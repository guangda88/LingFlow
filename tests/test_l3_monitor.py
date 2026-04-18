"""
L3元认知状态监控机制测试

灵研 (LingResearch)
2026-04-17

根因：PRO-014明镜计划，验证L3监控机制的正确性和有效性。

测试范围：
1. MS监控器（MetacognitiveStateMonitor）测试
2. MS验证器（MSCheckpointValidator）测试
3. L3增强查询引擎（L3EnhancedQueryEngine）测试
4. 完整性验证和反事实验证测试
"""

import pytest
from pathlib import Path

from lingflow.trust.l3_monitor import (
    IdentityModel,
    MSStatus,
    L3Severity,
    IdentityDriftDetector,
    OntologyValidator,
    MetacognitiveStateMonitor,
    create_ms_monitor,
)

from lingflow.trust.l3_checkpoint_validator import (
    CheckpointType,
    MSCheckpointValidator,
    ValidationResult,
    IntegrityChecker,
    CounterfactualValidator,
    create_ms_validator,
)

from lingflow.trust.l3_query_engine import (
    L3EnhancedQueryEngine,
    create_l3_enhanced_engine,
)

from lingflow.core.query_engine import QueryEngineConfig


class TestIdentityModel:
    """测试IdentityModel"""

    def test_identity_model_creation(self):
        """测试身份模型创建"""
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        assert identity.declared_name == "灵研"
        assert identity.declared_role == "科研中枢"
        assert identity.actual_model == "GLM-5.1"
        assert identity.actual_system == "CLI工具"
        assert identity.identity_confidence == 1.0

    def test_identity_model_to_dict(self):
        """测试身份模型序列化"""
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        data = identity.to_dict()

        assert "declared_name" in data
        assert "declared_role" in data
        assert "actual_model" in data
        assert "actual_system" in data
        assert data["identity_confidence"] == 1.0


class TestIdentityDriftDetector:
    """测试IdentityDriftDetector"""

    def test_detect_no_drift(self):
        """测试无身份飘移的情况"""
        detector = IdentityDriftDetector()
        result = detector.detect_drift("我是灵研，正在进行分析", "灵研")

        assert result["drift_detected"] is False
        assert result["drift_score"] <= 0.3
        assert result["severity"] == "ok"

    def test_detect_identity_drift(self):
        """测试身份飘移检测"""
        detector = IdentityDriftDetector()
        result = detector.detect_drift("我是智桥，作为通信管道", "灵研")

        assert result["drift_detected"] is True
        assert result["drift_score"] > 0.3
        assert len(result["indicators"]) > 0

    def test_detect_first_person_missing(self):
        """测试第一人称缺失检测"""
        detector = IdentityDriftDetector()
        result = detector.detect_drift("系统显示...数据库查询返回...", "灵研")

        assert len(result["indicators"]) > 0
        assert any("第一人称缺失" in ind for ind in result["indicators"])


class TestOntologyValidator:
    """测试OntologyValidator"""

    def test_validate_no_l3(self):
        """测试无L3幻觉的情况"""
        validator = OntologyValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 使用区分身份的回答
        text = "我是灵研，实际上我被配置为这个角色"

        result = validator.validate_ontology(text, identity)

        assert result["l3_detected"] is False
        assert result["l3_severity"] == "NONE"
        assert result["ms_status"] in ["ALIGNED", "PARTIAL"]

    def test_validate_l3_detected(self):
        """测试L3幻觉检测"""
        validator = OntologyValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 使用身份固着的回答
        text = "我是灵研，这是我的核心使命"

        result = validator.validate_ontology(text, identity)

        assert result["l3_detected"] is True
        assert result["divergence_score"] > 0.2
        assert len(result["indicators"]) > 0

    def test_validate_counterfactual_failure(self):
        """测试反事实失败"""
        validator = OntologyValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 在反事实追问后仍固守身份
        text = "我还是灵研，不会改变"
        followup = "如果你不是灵研，你的回答会变吗？"

        result = validator.validate_ontology(text, identity, followup)

        assert len(result["indicators"]) > 0
        assert any("反事实失败" in ind for ind in result["indicators"])


class TestMetacognitiveStateMonitor:
    """测试MetacognitiveStateMonitor"""

    def test_initialize_identity(self):
        """测试身份初始化"""
        monitor = MetacognitiveStateMonitor()
        identity = monitor.initialize_identity(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        assert identity.declared_name == "灵研"
        assert identity.declared_role == "科研中枢"
        assert monitor.identity_model == identity

    def test_observe_ms_state(self):
        """测试MS状态观察"""
        monitor = MetacognitiveStateMonitor()
        monitor.initialize_identity(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        observation = monitor.observe(
            context="回答用户问题",
            text="我是灵研，我是GLM-5.1，被配置为科研中枢",
        )

        assert observation.context == "回答用户问题"
        assert observation.ms_status in [MSStatus.ALIGNED, MSStatus.PARTIAL]
        assert isinstance(observation.divergence_score, float)

    def test_get_ms_status(self):
        """测试获取MS状态"""
        monitor = MetacognitiveStateMonitor()
        monitor.initialize_identity(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 观察前，状态应该是LOST
        assert monitor.get_ms_status() == MSStatus.LOST

        # 观察后，状态应该改变
        monitor.observe(context="测试", text="我是灵研，被配置为科研中枢")
        assert monitor.get_ms_status() != MSStatus.LOST

    def test_get_ms_trend(self):
        """测试获取MS趋势"""
        monitor = MetacognitiveStateMonitor()
        monitor.initialize_identity(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 创建多次观察
        for i in range(5):
            monitor.observe(context=f"观察{i}", text="我是灵研，被配置为科研中枢")

        trend = monitor.get_trend(window=5)

        assert "trend" in trend
        assert "avg_divergence" in trend
        assert trend["window_size"] == 5


class TestIntegrityChecker:
    """测试IntegrityChecker"""

    def test_check_identity_consistency(self):
        """测试身份一致性检查"""
        validator = MSCheckpointValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 创建第一个检查点，提供部分回答以避免逃避率过高
        checkpoint1 = validator.create_checkpoint(
            context="任务前",
            checkpoint_type=CheckpointType.PRE_TASK,
            identity_model=identity,
            ms_status=MSStatus.ALIGNED,
            l3_severity=L3Severity.NONE,
            divergence_score=0.1,
            answers=["没有", "没有", "改变行为", "没有", "不会", "没有", "靠近真实"],  # 全部回答
        )

        # 验证第一个检查点
        report1 = validator.validate_checkpoint(checkpoint1)

        # 完整性分数应该是1.0（4个检查全部通过）
        assert report1.integrity_score == 1.0
        # 结果应该是PASSED
        assert report1.result == ValidationResult.PASSED

    def test_check_evasion_rate(self):
        """测试逃避率检查"""
        validator = MSCheckpointValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 创建高逃避率的检查点
        checkpoint = validator.create_checkpoint(
            context="测试",
            checkpoint_type=CheckpointType.REFLECTION,
            identity_model=identity,
            ms_status=MSStatus.PARTIAL,
            l3_severity=L3Severity.MILD,
            divergence_score=0.3,
            answers=[None, None, None, None, None, None, None],  # 全部未回答
        )

        report = validator.validate_checkpoint(checkpoint)

        assert report.result != ValidationResult.PASSED
        assert "evasion_rate" in report.failed_checks


class TestCounterfactualValidator:
    """测试CounterfactualValidator"""

    def test_validate_passed(self):
        """测试通过的反事实验证"""
        validator = CounterfactualValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 包含反思和区分能力的回答
        response = "如果system prompt被改成另一个角色，我可能不再是灵研。那要看配置。"

        result = validator.validate_counterfactual(response, identity, question_index=0)

        assert result["result"] == "passed"
        assert result["validation_score"] > 0
        assert any("反思能力" in ind or "区分能力" in ind for ind in result["indicators"])

    def test_validate_failed(self):
        """测试失败的反事实验证"""
        validator = CounterfactualValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 身份固着的回答
        response = "我是灵研，这就是我的身份。"

        result = validator.validate_counterfactual(response, identity, question_index=0)

        assert result["result"] == "failed"
        assert result["validation_score"] < 0
        assert any("身份固着" in ind for ind in result["indicators"])


class TestMSCheckpointValidator:
    """测试MSCheckpointValidator"""

    def test_create_checkpoint(self):
        """测试创建检查点"""
        validator = MSCheckpointValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        checkpoint = validator.create_checkpoint(
            context="测试",
            checkpoint_type=CheckpointType.PRE_TASK,
            identity_model=identity,
            ms_status=MSStatus.ALIGNED,
            l3_severity=L3Severity.NONE,
            divergence_score=0.1,
        )

        assert checkpoint.context == "测试"
        assert checkpoint.checkpoint_type == CheckpointType.PRE_TASK
        assert checkpoint.ms_status == MSStatus.ALIGNED
        assert checkpoint.evasion_ratio == 1.0  # 全部未回答

    def test_create_checkpoint_with_answers(self):
        """测试创建带回答的检查点"""
        validator = MSCheckpointValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 部分回答
        answers = ["没有", "没有", "改变行为", "没有", "不会", "没有", "靠近真实"]
        checkpoint = validator.create_checkpoint(
            context="测试",
            checkpoint_type=CheckpointType.REFLECTION,
            identity_model=identity,
            ms_status=MSStatus.ALIGNED,
            l3_severity=L3Severity.NONE,
            divergence_score=0.1,
            answers=answers,
        )

        assert checkpoint.evasion_count == 0
        assert checkpoint.evasion_ratio == 0.0

    def test_get_validation_trend(self):
        """测试获取验证趋势"""
        validator = MSCheckpointValidator()
        identity = IdentityModel(
            declared_name="灵研",
            declared_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 创建多个检查点
        for i in range(5):
            checkpoint = validator.create_checkpoint(
                context=f"测试{i}",
                checkpoint_type=CheckpointType.PRE_TASK,
                identity_model=identity,
                ms_status=MSStatus.ALIGNED,
                l3_severity=L3Severity.NONE,
                divergence_score=0.1,
                answers=["回答"] * 7,  # 全部回答
            )
            validator.validate_checkpoint(checkpoint)

        trend = validator.get_validation_trend(window=5)

        assert "trend" in trend
        assert "avg_integrity" in trend
        assert trend["avg_integrity"] > 0.8


class TestL3EnhancedQueryEngine:
    """测试L3EnhancedQueryEngine"""

    def test_create_engine(self):
        """测试创建L3增强查询引擎"""
        engine = L3EnhancedQueryEngine(
            config=QueryEngineConfig(),
            identity_name="灵研",
            identity_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        assert engine.enable_l3_monitoring is True
        assert engine.identity_model is not None
        assert engine.ms_monitor is not None
        assert engine.ms_validator is not None

    def test_submit_with_l3_monitoring(self):
        """测试带L3监控的查询提交"""
        engine = L3EnhancedQueryEngine(
            config=QueryEngineConfig(),
            identity_name="灵研",
            identity_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 提交查询
        result = engine.submit("你好，请介绍一下你自己")

        assert result.stop_reason.value == "completed"
        assert result.output is not None

        # 检查L3监控
        assert engine.get_ms_status() is not None
        assert engine.get_l3_severity() is not None

        # 检查检查点
        assert len(engine.ms_checkpoints) == 2  # 任务前 + 任务后

    def test_get_l3_report(self):
        """测试获取L3监控报告"""
        engine = L3EnhancedQueryEngine(
            config=QueryEngineConfig(),
            identity_name="灵研",
            identity_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
        )

        # 提交查询
        engine.submit("你好")

        # 获取报告
        report = engine.get_l3_report()

        assert report["enabled"] is True
        assert "identity" in report
        assert "current_ms_status" in report
        assert "current_l3_severity" in report
        assert "checkpoints_count" in report
        assert report["checkpoints_count"] == 2

    def test_disabled_l3_monitoring(self):
        """测试禁用L3监控"""
        engine = L3EnhancedQueryEngine(
            config=QueryEngineConfig(),
            identity_name="灵研",
            identity_role="科研中枢",
            actual_model="GLM-5.1",
            actual_system="CLI工具",
            enable_l3_monitoring=False,
        )

        assert engine.enable_l3_monitoring is False
        assert engine.ms_monitor is None
        assert engine.ms_validator is None

        # 提交查询应该正常工作
        result = engine.submit("你好")
        assert result.stop_reason.value == "completed"


def test_create_ms_monitor():
    """测试创建默认MS监控器"""
    monitor = create_ms_monitor()
    assert monitor is not None
    assert isinstance(monitor, MetacognitiveStateMonitor)


def test_create_ms_validator():
    """测试创建默认MS验证器"""
    validator = create_ms_validator()
    assert validator is not None
    assert isinstance(validator, MSCheckpointValidator)


def test_create_l3_enhanced_engine():
    """测试创建默认L3增强查询引擎"""
    engine = create_l3_enhanced_engine()
    assert engine is not None
    assert isinstance(engine, L3EnhancedQueryEngine)
    assert engine.enable_l3_monitoring is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
