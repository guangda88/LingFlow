"""Auto Mode 崩溃恢复 - 状态持久化与会话Forensics

参考 GSD 的 Crash Recovery：
- 信号处理（SIGTERM/SIGINT）
- 自动备份（保留多个历史版本）
- 崩溃报告（堆栈跟踪 + 状态快照）
- 恢复验证（完整性检查）
"""

import logging
import os
import signal
import sys
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

from lingflow.workflow.auto_mode import (
    AutoModeStateMachine,
)

logger = logging.getLogger(__name__)


@dataclass
class CrashReport:
    """崩溃报告

    包含崩溃时的所有关键信息，用于forensics分析。
    """
    timestamp: str
    session_id: str
    exit_signal: Optional[str] = None
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    traceback: Optional[str] = None
    state_snapshot: Optional[Dict[str, Any]] = None
    system_info: Optional[Dict[str, Any]] = None
    recovery_suggestion: Optional[str] = None


class AutoModeCrashRecovery:
    """Auto Mode 崩溃恢复系统

    负责处理程序崩溃、自动保存状态、生成崩溃报告、
    以及启动时的恢复验证。
    """

    def __init__(self, state_machine: AutoModeStateMachine, max_backups: int = 5):
        """初始化崩溃恢复系统

        Args:
            state_machine: 状态机实例
            max_backups: 最大备份数量
        """
        self.state_machine = state_machine
        self.workdir = Path(state_machine.workdir)
        self.lingflow_dir = self.workdir / ".lingflow"
        self.max_backups = max_backups

        # 状态文件路径
        self.state_file = self.lingflow_dir / "STATE.md"
        self.backup_dir = self.lingflow_dir / "backups"
        self.crash_report_dir = self.lingflow_dir / "crash_reports"

        # 确保目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.crash_report_dir.mkdir(parents=True, exist_ok=True)

        # 注册信号处理器
        self._setup_signal_handlers()

        # 记录启动时间
        self._startup_time = datetime.now()

    def _setup_signal_handlers(self) -> None:
        """设置信号处理器

        捕获 SIGTERM, SIGINT (Ctrl+C) 等信号，自动保存状态。
        """
        signals = [signal.SIGTERM, signal.SIGINT]

        for sig in signals:
            signal.signal(sig, self._signal_handler)

        logger.info(f"已注册信号处理器: {', '.join([s.name for s in signals])}")

    def _signal_handler(self, signum, frame) -> None:
        """信号处理器

        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        signal_name = signal.Signals(signum).name

        logger.warning(f"接收到信号 {signal_name} ({signum})")

        # 生成崩溃报告
        report = self._generate_crash_report(
            exit_signal=signal_name,
            exception_type=None,
            exception_message=None,
            traceback_str=None,
        )

        # 保存崩溃报告
        self._save_crash_report(report)

        # 保存状态
        try:
            self._create_backup()
            self.state_machine.save_state()
            logger.info("状态已自动保存")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")

        # 退出
        sys.exit(0)

    def _generate_crash_report(
        self,
        exit_signal: Optional[str] = None,
        exception_type: Optional[str] = None,
        exception_message: Optional[str] = None,
        traceback_str: Optional[str] = None,
    ) -> CrashReport:
        """生成崩溃报告

        Args:
            exit_signal: 退出信号
            exception_type: 异常类型
            exception_message: 异常消息
            traceback_str: 堆栈跟踪

        Returns:
            崩溃报告
        """
        # 获取状态快照
        state_snapshot = None
        try:
            state_snapshot = self.state_machine.state.to_dict()
        except Exception as e:
            logger.warning(f"获取状态快照失败: {e}")

        # 获取系统信息
        system_info = self._collect_system_info()

        # 生成恢复建议
        recovery_suggestion = self._generate_recovery_suggestion(
            exit_signal, exception_type, exception_message
        )

        return CrashReport(
            timestamp=datetime.now().isoformat(),
            session_id=self.state_machine.session_id,
            exit_signal=exit_signal,
            exception_type=exception_type,
            exception_message=exception_message,
            traceback=traceback_str,
            state_snapshot=state_snapshot,
            system_info=system_info,
            recovery_suggestion=recovery_suggestion,
        )

    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息

        Returns:
            系统信息字典
        """
        import platform

        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "working_directory": str(self.workdir),
            "session_duration_seconds": (datetime.now() - self._startup_time).total_seconds(),
            "pid": os.getpid(),
            "memory_usage": self._get_memory_usage(),
        }

    def _get_memory_usage(self) -> Optional[Dict[str, Any]]:
        """获取内存使用情况

        Returns:
            内存使用信息
        """
        try:
            import psutil

            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()

            return {
                "rss_mb": mem_info.rss / 1024 / 1024,
                "vms_mb": mem_info.vms / 1024 / 1024,
                "percent": process.memory_percent(),
            }
        except ImportError:
            logger.warning("psutil not available, memory info skipped")
            return None
        except Exception as e:
            logger.warning(f"获取内存信息失败: {e}")
            return None

    def _generate_recovery_suggestion(
        self,
        exit_signal: Optional[str],
        exception_type: Optional[str],
        exception_message: Optional[str],
    ) -> str:
        """生成恢复建议

        Args:
            exit_signal: 退出信号
            exception_type: 异常类型
            exception_message: 异常消息

        Returns:
            恢复建议
        """
        suggestions = []

        # 基于信号的建议
        if exit_signal == "SIGTERM":
            suggestions.append("程序被SIGTERM终止，可能是系统资源限制或用户手动终止")
            suggestions.append("检查系统资源（内存/CPU）是否充足")
        elif exit_signal == "SIGINT":
            suggestions.append("程序被Ctrl+C中断")
            suggestions.append("这是正常的用户操作，可以直接继续执行")

        # 基于异常的建议
        if exception_type:
            suggestions.append(f"异常类型: {exception_type}")
            suggestions.append(f"异常消息: {exception_message}")

            if "MemoryError" in exception_type:
                suggestions.append("内存不足，考虑增加内存限制或优化内存使用")
            elif "TimeoutError" in exception_type:
                suggestions.append("操作超时，检查网络连接或增加超时时间")
            elif "FileNotFoundError" in exception_type:
                suggestions.append("文件未找到，检查文件路径是否存在")
            elif "PermissionError" in exception_type:
                suggestions.append("权限不足，检查文件/目录权限")

        # 通用建议
        suggestions.append("状态已自动保存，可以直接恢复执行")
        suggestions.append("如需回退，可使用逃逸舱的'回退到上一状态'功能")

        return "\n".join([f"• {s}" for s in suggestions])

    def _save_crash_report(self, report: CrashReport) -> None:
        """保存崩溃报告

        Args:
            report: 崩溃报告
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_file = self.crash_report_dir / f"crash_{timestamp}_{report.session_id}.json"

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2, ensure_ascii=False)

            logger.info(f"崩溃报告已保存: {report_file}")
        except Exception as e:
            logger.error(f"保存崩溃报告失败: {e}")

    def _create_backup(self) -> None:
        """创建状态备份

        保留最多 max_backups 个备份。
        """
        if not self.state_file.exists():
            return

        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_file = self.backup_dir / f"STATE_{timestamp}.md"

            # 复制状态文件
            shutil.copy2(self.state_file, backup_file)
            logger.info(f"状态备份已创建: {backup_file}")

            # 清理旧备份
            self._cleanup_old_backups()

        except Exception as e:
            logger.error(f"创建备份失败: {e}")

    def _cleanup_old_backups(self) -> None:
        """清理旧备份

        保留最新的 max_backups 个备份。
        """
        try:
            backups = sorted(self.backup_dir.glob("STATE_*.md"), reverse=True)

            # 删除超过 max_backups 的旧备份
            for backup in backups[self.max_backups:]:
                backup.unlink()
                logger.info(f"已删除旧备份: {backup}")

        except Exception as e:
            logger.error(f"清理备份失败: {e}")

    def verify_state_integrity(self) -> Dict[str, Any]:
        """验证状态文件完整性

        Returns:
            验证结果字典，包含:
            - valid: 是否有效
            - error: 错误信息（如果有）
            - recovered: 是否从备份恢复
            - backup_used: 使用的备份文件（如果有）
        """
        result = {
            "valid": False,
            "error": None,
            "recovered": False,
            "backup_used": None,
        }

        # 检查状态文件是否存在
        if not self.state_file.exists():
            logger.warning("状态文件不存在")
            result["error"] = "State file not found"

            # 尝试从备份恢复
            recovery = self._recover_from_backup()
            if recovery["success"]:
                result["valid"] = True
                result["recovered"] = True
                result["backup_used"] = recovery["backup_file"]

            return result

        # 尝试解析状态文件
        try:
            content = self.state_file.read_text(encoding="utf-8")

            # 提取 JSON 部分
            state_dict = self._extract_state_json(content)

            if state_dict is None:
                raise ValueError("无法从STATE.md中提取状态JSON")

            # 验证必需字段
            self._validate_state_fields(state_dict)

            result["valid"] = True
            logger.info("状态文件验证通过")

        except Exception as e:
            logger.error(f"状态文件验证失败: {e}")
            result["error"] = str(e)

            # 尝试从备份恢复
            recovery = self._recover_from_backup()
            if recovery["success"]:
                result["valid"] = True
                result["recovered"] = True
                result["backup_used"] = recovery["backup_file"]

        return result

    def _extract_state_json(self, content: str) -> Optional[Dict[str, Any]]:
        """从 STATE.md 内容中提取 JSON

        支持两种格式：
        1. <!-- STATE_START --> ... <!-- STATE_END -->
        2. ```json ... ```

        Args:
            content: STATE.md 内容

        Returns:
            状态字典，失败返回 None
        """
        import re

        # 格式1: <!-- STATE_START --> ... <!-- STATE_END -->
        pattern1 = r"<!--\s*STATE_START\s*-->\s*\n*(.*?)\s*\n*<!--\s*STATE_END\s*-->"
        match = re.search(pattern1, content, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                return None

        # 格式2: ```json ... ```
        pattern2 = r"```json\s*\n*(.*?)\s*\n*```"
        match = re.search(pattern2, content, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                return None

        # 格式3: 纯 JSON（向后兼容）
        try:
            # 尝试找到第一个 { 和最后一个 }
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"JSON解析失败: {e}")

        return None

    def _validate_state_fields(self, state_dict: Dict[str, Any]) -> None:
        """验证状态字段

        Args:
            state_dict: 状态字典

        Raises:
            ValueError: 验证失败
        """
        required_fields = ["state", "session_id"]

        for field in required_fields:
            if field not in state_dict:
                raise ValueError(f"Missing required field: {field}")

        # 验证状态值
        valid_states = ["IDLE", "PLAN", "RESEARCH", "EXECUTE", "COMPLETE", "REASSESS", "VALIDATE", "PAUSED", "DONE", "ERROR"]
        if state_dict["state"] not in valid_states:
            raise ValueError(f"Invalid state: {state_dict['state']}")

    def _recover_from_backup(self) -> Dict[str, Any]:
        """从备份恢复

        Returns:
            恢复结果，包含:
            - success: 是否成功
            - backup_file: 使用的备份文件
        """
        result = {"success": False, "backup_file": None}

        try:
            # 获取最新的备份
            backups = sorted(self.backup_dir.glob("STATE_*.md"), reverse=True)

            if not backups:
                logger.warning("没有可用的备份")
                return result

            # 使用最新的备份
            latest_backup = backups[0]
            shutil.copy2(latest_backup, self.state_file)

            logger.info(f"从备份恢复成功: {latest_backup}")

            result["success"] = True
            result["backup_file"] = str(latest_backup)

        except Exception as e:
            logger.error(f"从备份恢复失败: {e}")

        return result

    def list_crash_reports(self) -> List[Path]:
        """列出所有崩溃报告

        Returns:
            崩溃报告文件列表
        """
        return sorted(self.crash_report_dir.glob("crash_*.json"), reverse=True)

    def print_crash_forensics(self, report_file: Path) -> None:
        """打印崩溃报告（forensics分析）

        Args:
            report_file: 崩溃报告文件
        """
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                report_data = json.load(f)

            print("\n" + "=" * 70)
            print("🔍 崩溃分析报告")
            print("=" * 70)

            print(f"\n时间戳: {report_data.get('timestamp', 'N/A')}")
            print(f"Session ID: {report_data.get('session_id', 'N/A')}")

            # 退出原因
            exit_signal = report_data.get("exit_signal")
            exception_type = report_data.get("exception_type")

            print("\n📌 退出原因:")
            if exit_signal:
                print(f"  信号: {exit_signal}")
            if exception_type:
                print(f"  异常: {exception_type}")
                print(f"  消息: {report_data.get('exception_message', 'N/A')}")

            # 堆栈跟踪
            traceback = report_data.get("traceback")
            if traceback:
                print("\n📜 堆栈跟踪:")
                print(traceback[:1000])  # 限制显示长度
                if len(traceback) > 1000:
                    print("\n... (堆栈跟踪过长，已截断)")

            # 系统信息
            system_info = report_data.get("system_info")
            if system_info:
                print("\n💻 系统信息:")
                print(f"  平台: {system_info.get('platform', 'N/A')}")
                print(f"  Python: {system_info.get('python_version', 'N/A')}")
                print(f"  工作目录: {system_info.get('working_directory', 'N/A')}")

                session_duration = system_info.get("session_duration_seconds")
                if session_duration:
                    print(f"  会话时长: {session_duration:.2f}s")

                memory_usage = system_info.get("memory_usage")
                if memory_usage:
                    print(f"  内存使用: RSS={memory_usage.get('rss_mb', 'N/A')}MB, VMS={memory_usage.get('vms_mb', 'N/A')}MB")

            # 恢复建议
            recovery_suggestion = report_data.get("recovery_suggestion")
            if recovery_suggestion:
                print("\n💡 恢复建议:")
                print(recovery_suggestion)

            print("\n" + "=" * 70)

        except Exception as e:
            logger.error(f"读取崩溃报告失败: {e}")
            print(f"\n❌ 读取崩溃报告失败: {e}")

    def print_recovered_state_summary(self) -> None:
        """打印恢复后的状态摘要"""
        state = self.state_machine.state

        print("\n" + "=" * 70)
        print("✅ 状态恢复成功")
        print("=" * 70)

        print(f"\nSession ID: {self.state_machine.session_id}")
        print(f"恢复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"当前状态: {state.state}")

        if state.milestone:
            m = state.milestone
            print(f"\n📍 Milestone: {m.milestone_id} - {m.title}")
            print(f"  当前 Slice: {m.current_slice_index}/{len(m.slices)}")

        if state.slice:
            s = state.slice
            print(f"\n📝 Slice: {s.slice_id}")
            print(f"  当前 Task: {s.current_task_index}/{len(s.tasks)}")
            print(f"  已完成: {len(s.completed_tasks)}/{len(s.tasks)}")

        print("\n💡 提示:")
        print("• 状态已恢复，可以直接继续执行")
        print("• 使用逃逸舱（Ctrl+C）可查看详细信息和修改计划")
        print("• 如需回退，可在逃逸舱中选择'回退到上一状态'")

        print("\n" + "=" * 70)
