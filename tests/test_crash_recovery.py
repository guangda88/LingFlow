"""Auto Mode 崩溃恢复系统测试

测试覆盖：
- 信号处理和崩溃报告生成
- 备份系统（创建、清理）
- 状态完整性验证
- 从备份恢复
- Forensics 显示
"""

import pytest
import json
import signal
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from lingflow.workflow.auto_mode import (
    AutoModeStateMachine,
    AutoModeState,
    MilestoneContext,
)
from lingflow.workflow.crash_recovery import AutoModeCrashRecovery, CrashReport


@pytest.fixture
def temp_workdir(tmp_path: Path):
    """临时工作目录"""
    yield tmp_path


@pytest.fixture
def state_machine(temp_workdir: Path):
    """状态机实例"""
    sm = AutoModeStateMachine(str(temp_workdir))
    sm.start()
    return sm


@pytest.fixture
def crash_recovery(state_machine: AutoModeStateMachine):
    """崩溃恢复实例"""
    return AutoModeCrashRecovery(state_machine, max_backups=3)


class TestCrashReport:
    """测试 CrashReport 数据类"""

    def test_crash_report_creation(self):
        """测试创建崩溃报告"""
        report = CrashReport(
            timestamp="2024-01-01T12:00:00",
            session_id="test-session-123",
            exit_signal="SIGTERM",
            exception_type="ValueError",
            exception_message="Invalid value",
            traceback="Traceback...",
            state_snapshot={"state": "EXECUTE"},
            system_info={"platform": "Linux"},
            recovery_suggestion="Check input",
        )

        assert report.timestamp == "2024-01-01T12:00:00"
        assert report.session_id == "test-session-123"
        assert report.exit_signal == "SIGTERM"
        assert report.exception_type == "ValueError"


class TestAutoModeCrashRecovery:
    """测试 AutoModeCrashRecovery"""

    def test_initialization(self, state_machine: AutoModeStateMachine):
        """测试初始化"""
        cr = AutoModeCrashRecovery(state_machine, max_backups=5)

        assert cr.state_machine == state_machine
        assert cr.max_backups == 5
        assert cr.backup_dir.exists()
        assert cr.crash_report_dir.exists()

    def test_initialization_creates_directories(self, temp_workdir: Path):
        """测试初始化时创建目录"""
        # 先创建崩溃恢复实例
        sm = AutoModeStateMachine(str(temp_workdir))
        _ = AutoModeCrashRecovery(sm)
        lingflow_dir = temp_workdir / ".lingflow"
        assert lingflow_dir.exists()
        assert (lingflow_dir / "backups").exists()
        assert (lingflow_dir / "crash_reports").exists()

    def test_collect_system_info(self, crash_recovery: AutoModeCrashRecovery):
        """测试收集系统信息"""
        info = crash_recovery._collect_system_info()

        assert "platform" in info
        assert "python_version" in info
        assert "working_directory" in info
        assert "pid" in info
        assert "session_duration_seconds" in info

    def test_get_memory_usage_with_psutil(self, crash_recovery: AutoModeCrashRecovery):
        """测试获取内存使用情况（有 psutil）"""
        mem_info = crash_recovery._get_memory_usage()

        # 如果 psutil 可用，应该返回数据
        # 如果不可用，返回 None
        if mem_info:
            assert "rss_mb" in mem_info
            assert "vms_mb" in mem_info
            assert "percent" in mem_info
        else:
            assert mem_info is None

    def test_generate_recovery_suggestion_for_sigterm(self, crash_recovery: AutoModeCrashRecovery):
        """测试生成 SIGTERM 恢复建议"""
        suggestion = crash_recovery._generate_recovery_suggestion(
            exit_signal="SIGTERM",
            exception_type=None,
            exception_message=None,
        )

        assert "SIGTERM" in suggestion
        assert "系统资源" in suggestion.lower()

    def test_generate_recovery_suggestion_for_sigint(self, crash_recovery: AutoModeCrashRecovery):
        """测试生成 SIGINT 恢复建议"""
        suggestion = crash_recovery._generate_recovery_suggestion(
            exit_signal="SIGINT",
            exception_type=None,
            exception_message=None,
        )

        assert "Ctrl+C" in suggestion
        assert "正常" in suggestion

    def test_generate_recovery_suggestion_for_exception(self, crash_recovery: AutoModeCrashRecovery):
        """测试生成异常恢复建议"""
        suggestion = crash_recovery._generate_recovery_suggestion(
            exit_signal=None,
            exception_type="MemoryError",
            exception_message="Out of memory",
        )

        assert "MemoryError" in suggestion
        assert "内存" in suggestion

    def test_generate_crash_report(self, crash_recovery: AutoModeCrashRecovery):
        """测试生成崩溃报告"""
        report = crash_recovery._generate_crash_report(
            exit_signal="SIGTERM",
            exception_type="ValueError",
            exception_message="Invalid value",
            traceback_str="Traceback...",
        )

        assert isinstance(report, CrashReport)
        assert report.session_id == crash_recovery.state_machine.session_id
        assert report.exit_signal == "SIGTERM"
        assert report.exception_type == "ValueError"
        assert report.system_info is not None
        assert report.recovery_suggestion is not None

    def test_save_crash_report(self, crash_recovery: AutoModeCrashRecovery):
        """测试保存崩溃报告"""
        report = CrashReport(
            timestamp=datetime.now().isoformat(),
            session_id="test-session",
            exit_signal="SIGTERM",
        )

        crash_recovery._save_crash_report(report)

        # 检查报告文件是否创建
        reports = list(crash_recovery.crash_report_dir.glob("crash_*.json"))
        assert len(reports) == 1

        # 检查报告内容
        with open(reports[0], "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["session_id"] == "test-session"
            assert data["exit_signal"] == "SIGTERM"

    def test_list_crash_reports(self, crash_recovery: AutoModeCrashRecovery, state_machine: AutoModeStateMachine):
        """测试列出崩溃报告"""
        # 创建多个报告
        for i in range(3):
            report = CrashReport(
                timestamp=datetime.now().isoformat(),
                session_id=f"test-session-{i}",
                exit_signal="SIGTERM",
            )
            crash_recovery._save_crash_report(report)

        reports = crash_recovery.list_crash_reports()
        assert len(reports) == 3

        # 应该按时间倒序排列
        assert reports[0].name > reports[1].name

    def test_create_backup(self, crash_recovery: AutoModeCrashRecovery, state_machine: AutoModeStateMachine):
        """测试创建备份"""
        # 确保状态文件存在
        state_machine.save_state()

        # 创建备份
        crash_recovery._create_backup()

        # 检查备份文件是否创建
        backups = list(crash_recovery.backup_dir.glob("STATE_*.md"))
        assert len(backups) == 1

        # 检查备份内容
        backup_content = backups[0].read_text(encoding="utf-8")
        original_content = crash_recovery.state_file.read_text(encoding="utf-8")
        assert backup_content == original_content

    def test_cleanup_old_backups(self, crash_recovery: AutoModeCrashRecovery, state_machine: AutoModeStateMachine):
        """测试清理旧备份"""
        from unittest.mock import patch
        from datetime import datetime as dt, timedelta

        # 创建超过 max_backups 的备份，模拟不同时间戳
        with patch("lingflow.workflow.crash_recovery.datetime") as mock_datetime:
            base_time = dt(2024, 1, 1, 12, 0, 0)
            for i in range(5):
                # 模拟时间前进
                mock_datetime.now.return_value = base_time + timedelta(seconds=i)
                state_machine.save_state()
                crash_recovery._create_backup()

        # 清理后应该只有 max_backups 个备份
        backups = list(crash_recovery.backup_dir.glob("STATE_*.md"))
        assert len(backups) == crash_recovery.max_backups

    def test_extract_state_json_valid(self, crash_recovery: AutoModeCrashRecovery):
        """测试从有效 STATE.md 提取 JSON"""
        content = """<!-- STATE_START -->
{"state": "EXECUTE", "session_id": "test"}
<!-- STATE_END -->"""

        state_dict = crash_recovery._extract_state_json(content)
        assert state_dict is not None
        assert state_dict["state"] == "EXECUTE"
        assert state_dict["session_id"] == "test"

    def test_extract_state_json_invalid(self, crash_recovery: AutoModeCrashRecovery):
        """测试从无效 STATE.md 提取 JSON"""
        content = "No JSON here"

        state_dict = crash_recovery._extract_state_json(content)
        assert state_dict is None

    def test_validate_state_fields_valid(self, crash_recovery: AutoModeCrashRecovery):
        """测试验证有效状态字段"""
        state_dict = {
            "state": "EXECUTE",
            "session_id": "test-session",
        }

        # 不应该抛出异常
        crash_recovery._validate_state_fields(state_dict)

    def test_validate_state_fields_missing(self, crash_recovery: AutoModeCrashRecovery):
        """测试验证缺失字段"""
        state_dict = {
            "state": "EXECUTE",
            # 缺少 session_id
        }

        with pytest.raises(ValueError, match="Missing required field"):
            crash_recovery._validate_state_fields(state_dict)

    def test_validate_state_fields_invalid_state(self, crash_recovery: AutoModeCrashRecovery):
        """测试验证无效状态值"""
        state_dict = {
            "state": "INVALID_STATE",
            "session_id": "test-session",
        }

        with pytest.raises(ValueError, match="Invalid state"):
            crash_recovery._validate_state_fields(state_dict)

    def test_verify_state_integrity_valid(self, crash_recovery: AutoModeCrashRecovery, state_machine: AutoModeStateMachine):
        """测试验证有效状态"""
        state_machine.save_state()

        result = crash_recovery.verify_state_integrity()

        assert result["valid"] is True
        assert result["error"] is None
        assert result["recovered"] is False

    def test_verify_state_integrity_missing_file(self, crash_recovery: AutoModeCrashRecovery):
        """测试验证缺失状态文件"""
        # 删除状态文件
        if crash_recovery.state_file.exists():
            crash_recovery.state_file.unlink()

        result = crash_recovery.verify_state_integrity()

        assert result["valid"] is False
        assert result["error"] == "State file not found"
        assert result["recovered"] is False

    def test_verify_state_integrity_recover_from_backup(self, crash_recovery: AutoModeCrashRecovery, state_machine: AutoModeStateMachine):
        """测试从备份恢复"""
        # 创建备份
        state_machine.save_state()
        crash_recovery._create_backup()

        # 破坏状态文件
        crash_recovery.state_file.write_text("Corrupted content")

        # 验证应该从备份恢复
        result = crash_recovery.verify_state_integrity()

        assert result["valid"] is True
        assert result["recovered"] is True
        assert result["backup_used"] is not None

    def test_recover_from_backup_no_backups(self, crash_recovery: AutoModeCrashRecovery):
        """测试无备份时的恢复"""
        result = crash_recovery._recover_from_backup()

        assert result["success"] is False
        assert result["backup_file"] is None

    def test_recover_from_backup_with_backups(self, crash_recovery: AutoModeCrashRecovery, state_machine: AutoModeStateMachine):
        """测试有备份时的恢复"""
        # 创建备份
        state_machine.save_state()
        crash_recovery._create_backup()

        # 删除状态文件
        crash_recovery.state_file.unlink()

        # 从备份恢复
        result = crash_recovery._recover_from_backup()

        assert result["success"] is True
        assert result["backup_file"] is not None
        assert crash_recovery.state_file.exists()

    def test_signal_handler(self, crash_recovery: AutoModeCrashRecovery):
        """测试信号处理器"""
        # 模拟信号处理
        with patch("sys.exit") as mock_exit:
            crash_recovery._signal_handler(signal.SIGTERM, None)

            # 应该生成了崩溃报告
            reports = list(crash_recovery.crash_report_dir.glob("crash_*.json"))
            assert len(reports) == 1

            # 应该调用了 sys.exit
            mock_exit.assert_called_once_with(0)

    def test_print_crash_forensics(self, crash_recovery: AutoModeCrashRecovery, capsys):
        """测试打印崩溃 forensics"""
        # 创建测试报告
        report_data = {
            "timestamp": "2024-01-01T12:00:00",
            "session_id": "test-session",
            "exit_signal": "SIGTERM",
            "exception_type": "ValueError",
            "exception_message": "Invalid value",
            "traceback": "Traceback...",
            "system_info": {
                "platform": "Linux",
                "python_version": "3.11",
                "working_directory": "/tmp/test",
            },
            "recovery_suggestion": "Check input",
        }

        report_file = crash_recovery.crash_report_dir / "crash_test.json"
        report_file.write_text(json.dumps(report_data), encoding="utf-8")

        # 打印 forensics
        crash_recovery.print_crash_forensics(report_file)

        # 检查输出
        captured = capsys.readouterr()
        assert "崩溃分析报告" in captured.out
        assert "SIGTERM" in captured.out
        assert "恢复建议" in captured.out

    def test_print_recovered_state_summary(self, crash_recovery: AutoModeCrashRecovery, state_machine: AutoModeStateMachine, capsys):
        """测试打印恢复后的状态摘要"""
        # 设置状态
        state_machine.transition_to(AutoModeState.EXECUTE)
        # 直接设置 milestone
        state_machine.state.milestone = MilestoneContext(
            milestone_id="M001",
            title="Test Milestone",
            success_criteria=["Done"],
            slices=[],
        )

        # 打印摘要
        crash_recovery.print_recovered_state_summary()

        # 检查输出
        captured = capsys.readouterr()
        assert "状态恢复成功" in captured.out
        assert "M001" in captured.out


class TestIntegration:
    """集成测试"""

    def test_crash_and_recover_workflow(self, temp_workdir: Path):
        """测试完整的崩溃和恢复流程"""
        # 1. 创建状态机并运行
        sm = AutoModeStateMachine(str(temp_workdir))
        sm.start()
        sm.transition_to(AutoModeState.EXECUTE)
        sm.save_state()

        # 2. 模拟崩溃
        cr = AutoModeCrashRecovery(sm)
        report = cr._generate_crash_report(
            exit_signal="SIGTERM",
            exception_type="ValueError",
            exception_message="Crash",
            traceback_str="Traceback",
        )
        cr._save_crash_report(report)
        cr._create_backup()

        # 3. 破坏状态文件
        cr.state_file.unlink()

        # 4. 验证并恢复
        result = cr.verify_state_integrity()

        assert result["valid"] is True
        assert result["recovered"] is True

        # 5. 检查恢复的状态
        recovered_state = sm.state
        assert recovered_state.state == AutoModeState.EXECUTE
