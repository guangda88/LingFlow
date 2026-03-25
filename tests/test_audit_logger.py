"""
测试安全审计日志记录器
"""

import json
import os
import tempfile
from pathlib import Path
from lingflow.common.audit_logger import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    SecurityAuditLogger,
    get_audit_logger,
    log_skill_execution,
    log_config_change,
    log_access_violation,
)


class TestAuditEvent:
    """测试 AuditEvent 类"""

    def test_initialization(self):
        """测试初始化"""
        event = AuditEvent(
            event_type=AuditEventType.SKILL_EXECUTION,
            severity=AuditSeverity.INFO,
            message="Test message",
        )

        assert event.event_type == AuditEventType.SKILL_EXECUTION
        assert event.severity == AuditSeverity.INFO
        assert event.message == "Test message"
        assert event.user is None
        assert event.resource is None
        assert event.details == {}

    def test_initialization_with_all_params(self):
        """测试完整参数初始化"""
        event = AuditEvent(
            event_type=AuditEventType.SKILL_EXECUTION,
            severity=AuditSeverity.ERROR,
            message="Failed execution",
            user="test_user",
            resource="skill:test",
            details={"error": "timeout"},
            source="coordinator",
        )

        assert event.event_type == AuditEventType.SKILL_EXECUTION
        assert event.severity == AuditSeverity.ERROR
        assert event.message == "Failed execution"
        assert event.user == "test_user"
        assert event.resource == "skill:test"
        assert event.details == {"error": "timeout"}
        assert event.source == "coordinator"

    def test_to_dict(self):
        """测试转换为字典"""
        event = AuditEvent(
            event_type=AuditEventType.SKILL_EXECUTION,
            severity=AuditSeverity.INFO,
            message="Test",
            user="user1",
            resource="resource1",
        )

        result = event.to_dict()

        assert result["event_type"] == "skill_execution"
        assert result["severity"] == "INFO"
        assert result["message"] == "Test"
        assert result["user"] == "user1"
        assert result["resource"] == "resource1"
        assert "timestamp" in result

    def test_to_json(self):
        """测试转换为 JSON"""
        event = AuditEvent(
            event_type=AuditEventType.SKILL_EXECUTION,
            severity=AuditSeverity.INFO,
            message="Test",
        )

        json_str = event.to_json()
        result = json.loads(json_str)

        assert result["event_type"] == "skill_execution"
        assert result["severity"] == "INFO"
        assert result["message"] == "Test"


class TestSecurityAuditLogger:
    """测试 SecurityAuditLogger 类"""

    def test_initialization_default(self):
        """测试默认参数初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)
            assert logger.logger is not None
            assert len(logger.logger.handlers) > 0

    def test_initialization_with_file(self):
        """测试指定文件路径初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = SecurityAuditLogger(log_file=log_file)
            assert logger.log_file == Path(log_file)

    def test_log_event(self):
        """测试记录事件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            event = AuditEvent(
                event_type=AuditEventType.SKILL_EXECUTION,
                severity=AuditSeverity.INFO,
                message="Test event",
            )

            # 不应该抛出异常
            logger.log_event(event)

            # 验证事件被记录到历史
            assert len(logger._event_history) == 1
            assert logger._event_history[0]["message"] == "Test event"

    def test_log_skill_execution_success(self):
        """测试记录成功的技能执行"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_skill_execution(
                skill_name="test_skill",
                user="user1",
                success=True,
                duration=1.5,
            )

            assert len(logger._event_history) == 1
            event = logger._event_history[0]
            assert event["event_type"] == "skill_execution"
            assert event["severity"] == "INFO"
            assert event["user"] == "user1"
            assert event["details"]["success"] is True
            assert event["details"]["duration"] == 1.5

    def test_log_skill_execution_failure(self):
        """测试记录失败的技能执行"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_skill_execution(
                skill_name="test_skill",
                user="user1",
                success=False,
                duration=0.5,
            )

            assert len(logger._event_history) == 1
            event = logger._event_history[0]
            assert event["severity"] == "ERROR"
            assert event["details"]["success"] is False

    def test_log_config_change(self):
        """测试记录配置更改"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            old_config = {"key1": "value1", "key2": "value2"}
            new_config = {"key1": "value1", "key2": "new_value", "key3": "value3"}

            logger.log_config_change(
                old_config=old_config,
                new_config=new_config,
                user="admin",
                source="cli",
            )

            assert len(logger._event_history) == 1
            event = logger._event_history[0]
            assert event["event_type"] == "config_change"
            assert event["user"] == "admin"
            assert event["source"] == "cli"
            assert "changes" in event["details"]
            assert len(event["details"]["changes"]) == 2  # key2 changed, key3 added

    def test_log_access_violation(self):
        """测试记录访问违规"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_access_violation(
                resource="secret_file.txt",
                user="unauthorized_user",
                operation="read",
                reason="Insufficient permissions",
            )

            assert len(logger._event_history) == 1
            event = logger._event_history[0]
            assert event["event_type"] == "access_violation"
            assert event["severity"] == "WARNING"
            assert event["user"] == "unauthorized_user"
            assert event["resource"] == "secret_file.txt"
            assert event["details"]["operation"] == "read"
            assert event["details"]["reason"] == "Insufficient permissions"

    def test_log_sandbox_violation(self):
        """测试记录沙箱违规"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_sandbox_violation(
                skill_name="malicious_skill",
                violation_type="unsafe_import",
                details={"imported_module": "os"},
            )

            assert len(logger._event_history) == 1
            event = logger._event_history[0]
            assert event["event_type"] == "sandbox_violation"
            assert event["severity"] == "ERROR"
            assert event["resource"] == "skill:malicious_skill"
            assert event["details"]["violation_type"] == "unsafe_import"
            assert event["details"]["imported_module"] == "os"

    def test_log_permission_denied(self):
        """测试记录权限拒绝"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_permission_denied(
                resource="admin_panel",
                required_permission="admin",
                user="regular_user",
            )

            assert len(logger._event_history) == 1
            event = logger._event_history[0]
            assert event["event_type"] == "permission_denied"
            assert event["severity"] == "WARNING"
            assert event["user"] == "regular_user"
            assert event["details"]["required_permission"] == "admin"

    def test_get_event_history_all(self):
        """测试获取所有事件历史"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_skill_execution("skill1")
            logger.log_skill_execution("skill2")
            logger.log_access_violation("resource1")

            events = logger.get_event_history()
            assert len(events) == 3

    def test_get_event_history_filtered_by_type(self):
        """测试按类型过滤事件历史"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_skill_execution("skill1")
            logger.log_access_violation("resource1")
            logger.log_skill_execution("skill2")

            events = logger.get_event_history(event_type=AuditEventType.SKILL_EXECUTION)
            assert len(events) == 2
            assert all(e["event_type"] == "skill_execution" for e in events)

    def test_get_event_history_filtered_by_severity(self):
        """测试按严重性过滤事件历史"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_skill_execution("skill1", success=True)
            logger.log_skill_execution("skill2", success=False)
            logger.log_skill_execution("skill3", success=True)

            events = logger.get_event_history(severity=AuditSeverity.ERROR)
            assert len(events) == 1
            assert events[0]["severity"] == "ERROR"

    def test_get_event_history_filtered_by_user(self):
        """测试按用户过滤事件历史"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_skill_execution("skill1", user="user1")
            logger.log_skill_execution("skill2", user="user2")
            logger.log_skill_execution("skill3", user="user1")

            events = logger.get_event_history(user="user1")
            assert len(events) == 2
            assert all(e["user"] == "user1" for e in events)

    def test_get_event_history_with_limit(self):
        """测试限制返回的事件数量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            for i in range(10):
                logger.log_skill_execution(f"skill{i}")

            events = logger.get_event_history(limit=5)
            assert len(events) == 5

    def test_get_security_summary_empty(self):
        """测试获取空的安全摘要"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            summary = logger.get_security_summary()
            assert summary["total_events"] == 0
            assert summary["by_type"] == {}
            assert summary["by_severity"] == {}
            assert summary["recent_critical"] == []

    def test_get_security_summary_with_events(self):
        """测试获取包含事件的安全摘要"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            logger.log_skill_execution("skill1", success=True)
            logger.log_skill_execution("skill2", success=False)
            logger.log_access_violation("resource1")
            logger.log_sandbox_violation("skill3", "unsafe")

            summary = logger.get_security_summary()

            assert summary["total_events"] == 4
            assert summary["by_type"]["skill_execution"] == 2
            assert summary["by_type"]["access_violation"] == 1
            assert summary["by_type"]["sandbox_violation"] == 1
            assert summary["by_severity"]["INFO"] == 1
            assert summary["by_severity"]["ERROR"] == 2
            assert summary["by_severity"]["WARNING"] == 1

    def test_event_history_max_size(self):
        """测试事件历史最大大小限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)

            # 记录超过最大大小的事件
            for i in range(1500):
                logger.log_skill_execution(f"skill{i}")

            # 应该只保留最近的 1000 个事件
            assert len(logger._event_history) == 1000

    def test_log_file_creation(self):
        """测试日志文件创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "audit"
            logger = SecurityAuditLogger(log_dir=str(log_dir))

            logger.log_skill_execution("test_skill")

            # 验证日志文件存在
            assert (log_dir / "security_audit.log").exists()
            assert (log_dir / "security_audit_detailed.log").exists()


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_audit_logger_singleton(self):
        """测试获取单例审计日志记录器"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        assert logger1 is logger2

    def test_log_skill_execution_convenience(self):
        """测试便捷函数记录技能执行"""
        # 重置全局实例
        import lingflow.common.audit_logger as audit_module
        audit_module._audit_logger = None

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)
            audit_module._audit_logger = logger

            log_skill_execution("test_skill", user="user1", success=True)

            assert len(logger._event_history) == 1
            assert logger._event_history[0]["event_type"] == "skill_execution"

    def test_log_config_change_convenience(self):
        """测试便捷函数记录配置更改"""
        # 重置全局实例
        import lingflow.common.audit_logger as audit_module
        audit_module._audit_logger = None

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)
            audit_module._audit_logger = logger

            old_config = {"key": "old"}
            new_config = {"key": "new"}

            log_config_change(old_config, new_config, user="admin")

            assert len(logger._event_history) == 1
            assert logger._event_history[0]["event_type"] == "config_change"

    def test_log_access_violation_convenience(self):
        """测试便捷函数记录访问违规"""
        # 重置全局实例
        import lingflow.common.audit_logger as audit_module
        audit_module._audit_logger = None

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SecurityAuditLogger(log_dir=tmpdir)
            audit_module._audit_logger = logger

            log_access_violation("resource1", user="user1", operation="read")

            assert len(logger._event_history) == 1
            assert logger._event_history[0]["event_type"] == "access_violation"
