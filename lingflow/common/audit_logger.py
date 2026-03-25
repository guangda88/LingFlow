"""
LingFlow 安全审计日志记录器

记录安全相关事件，包括：
- 技能执行
- 配置更改
- 访问违规
- 沙箱违规
- 权限检查

审计日志用于安全事件追踪和合规性检查。
"""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class AuditEventType(Enum):
    """审计事件类型"""
    SKILL_EXECUTION = "skill_execution"
    CONFIG_CHANGE = "config_change"
    ACCESS_VIOLATION = "access_violation"
    SANDBOX_VIOLATION = "sandbox_violation"
    PERMISSION_DENIED = "permission_denied"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"


class AuditSeverity(Enum):
    """审计事件严重性"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditEvent:
    """审计事件"""

    def __init__(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        message: str,
        timestamp: Optional[datetime] = None,
        user: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ):
        """
        初始化审计事件

        Args:
            event_type: 事件类型
            severity: 严重性级别
            message: 事件消息
            timestamp: 事件时间戳（默认为当前时间）
            user: 用户标识
            resource: 受影响的资源
            details: 事件详细信息
            source: 事件来源
        """
        self.event_type = event_type
        self.severity = severity
        self.message = message
        self.timestamp = timestamp or datetime.utcnow()
        self.user = user
        self.resource = resource
        self.details = details or {}
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() + "Z",
            "user": self.user,
            "resource": self.resource,
            "details": self.details,
            "source": self.source,
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class SecurityAuditLogger:
    """安全审计日志记录器"""

    def __init__(
        self,
        log_file: Optional[str] = None,
        log_dir: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ):
        """
        初始化安全审计日志记录器

        Args:
            log_file: 日志文件路径（可选）
            log_dir: 日志目录（默认为 .lingflow/audit）
            enable_console: 是否输出到控制台
            enable_file: 是否输出到文件
            max_file_size: 最大文件大小（字节）
            backup_count: 备份文件数量
        """
        self.logger = logging.getLogger("lingflow.security_audit")
        self.logger.setLevel(logging.INFO)

        # 清除现有的处理器
        self.logger.handlers.clear()

        # 设置格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # 控制台处理器
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # 文件处理器
        if enable_file:
            # 确定日志文件路径
            if log_file:
                self.log_file = Path(log_file)
            else:
                log_dir_path = Path(log_dir or ".lingflow/audit")
                log_dir_path.mkdir(parents=True, exist_ok=True)
                self.log_file = log_dir_path / "security_audit.log"

            # 使用 RotatingFileHandler 自动轮转日志
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # 存储事件历史（内存中）
        self._event_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000

    def log_event(self, event: AuditEvent) -> None:
        """
        记录审计事件

        Args:
            event: 审计事件
        """
        # 记录到日志
        log_message = f"[{event.event_type.value}] {event.message}"
        if event.user:
            log_message += f" (user: {event.user})"
        if event.resource:
            log_message += f" (resource: {event.resource})"

        if event.severity == AuditSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif event.severity == AuditSeverity.ERROR:
            self.logger.error(log_message)
        elif event.severity == AuditSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # 记录详细信息到单独的日志文件
        if hasattr(self, 'log_file'):
            json_log_file = self.log_file.parent / f"{self.log_file.stem}_detailed{self.log_file.suffix}"
            with open(json_log_file, 'a', encoding='utf-8') as f:
                f.write(event.to_json() + "\n")

        # 存储到历史记录
        self._event_history.append(event.to_dict())
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)

    def log_skill_execution(
        self,
        skill_name: str,
        user: Optional[str] = None,
        success: bool = True,
        duration: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录技能执行

        Args:
            skill_name: 技能名称
            user: 用户标识
            success: 是否成功
            duration: 执行时长（秒）
            details: 详细信息
        """
        severity = AuditSeverity.INFO if success else AuditSeverity.ERROR
        message = f"Skill execution: {skill_name} - {'Success' if success else 'Failed'}"

        event = AuditEvent(
            event_type=AuditEventType.SKILL_EXECUTION,
            severity=severity,
            message=message,
            user=user,
            resource=f"skill:{skill_name}",
            details={
                "success": success,
                "duration": duration,
                **(details or {}),
            },
            source="coordinator",
        )

        self.log_event(event)

    def log_config_change(
        self,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
        user: Optional[str] = None,
        source: Optional[str] = None,
    ) -> None:
        """
        记录配置更改

        Args:
            old_config: 旧配置
            new_config: 新配置
            user: 用户标识
            source: 更改来源
        """
        # 计算变更
        changes = []
        for key in set(old_config.keys()) | set(new_config.keys()):
            if key not in old_config:
                changes.append(f"Added: {key} = {new_config[key]}")
            elif key not in new_config:
                changes.append(f"Removed: {key} = {old_config[key]}")
            elif old_config[key] != new_config[key]:
                changes.append(f"Changed: {key} from {old_config[key]} to {new_config[key]}")

        event = AuditEvent(
            event_type=AuditEventType.CONFIG_CHANGE,
            severity=AuditSeverity.INFO,
            message=f"Configuration changed: {len(changes)} field(s) modified",
            user=user,
            resource="config",
            details={
                "changes": changes,
                "old_config": old_config,
                "new_config": new_config,
            },
            source=source or "system",
        )

        self.log_event(event)

    def log_access_violation(
        self,
        resource: str,
        user: Optional[str] = None,
        operation: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录访问违规

        Args:
            resource: 受保护的资源
            user: 用户标识
            operation: 尝试的操作
            reason: 拒绝原因
            details: 详细信息
        """
        message = f"Access violation: {operation or 'Unknown operation'} on {resource}"
        if reason:
            message += f" - {reason}"

        event = AuditEvent(
            event_type=AuditEventType.ACCESS_VIOLATION,
            severity=AuditSeverity.WARNING,
            message=message,
            user=user,
            resource=resource,
            details={
                "operation": operation,
                "reason": reason,
                **(details or {}),
            },
            source="security",
        )

        self.log_event(event)

    def log_sandbox_violation(
        self,
        skill_name: str,
        violation_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录沙箱违规

        Args:
            skill_name: 技能名称
            violation_type: 违规类型
            details: 详细信息
        """
        event = AuditEvent(
            event_type=AuditEventType.SANDBOX_VIOLATION,
            severity=AuditSeverity.ERROR,
            message=f"Sandbox violation: {violation_type} in skill {skill_name}",
            resource=f"skill:{skill_name}",
            details={
                "violation_type": violation_type,
                **(details or {}),
            },
            source="sandbox",
        )

        self.log_event(event)

    def log_permission_denied(
        self,
        resource: str,
        required_permission: str,
        user: Optional[str] = None,
    ) -> None:
        """
        记录权限拒绝

        Args:
            resource: 受保护的资源
            required_permission: 需要的权限
            user: 用户标识
        """
        event = AuditEvent(
            event_type=AuditEventType.PERMISSION_DENIED,
            severity=AuditSeverity.WARNING,
            message=f"Permission denied: requires '{required_permission}' for {resource}",
            user=user,
            resource=resource,
            details={
                "required_permission": required_permission,
            },
            source="security",
        )

        self.log_event(event)

    def get_event_history(
        self,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        user: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取事件历史

        Args:
            event_type: 事件类型过滤
            severity: 严重性过滤
            user: 用户过滤
            limit: 返回数量限制

        Returns:
            事件列表
        """
        events = self._event_history

        # 过滤
        if event_type:
            events = [e for e in events if e["event_type"] == event_type.value]
        if severity:
            events = [e for e in events if e["severity"] == severity.value]
        if user:
            events = [e for e in events if e["user"] == user]

        # 限制数量
        if limit:
            events = events[-limit:]

        return events

    def get_security_summary(self) -> Dict[str, Any]:
        """
        获取安全摘要

        Returns:
            安全摘要统计
        """
        total_events = len(self._event_history)
        if total_events == 0:
            return {
                "total_events": 0,
                "by_type": {},
                "by_severity": {},
                "recent_critical": [],
            }

        # 按类型统计
        by_type: Dict[str, int] = {}
        for event in self._event_history:
            event_type = event["event_type"]
            by_type[event_type] = by_type.get(event_type, 0) + 1

        # 按严重性统计
        by_severity: Dict[str, int] = {}
        for event in self._event_history:
            severity = event["severity"]
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # 最近的严重事件
        recent_critical = [
            e for e in self._event_history[-10:]
            if e["severity"] in [AuditSeverity.ERROR.value, AuditSeverity.CRITICAL.value]
        ]

        return {
            "total_events": total_events,
            "by_type": by_type,
            "by_severity": by_severity,
            "recent_critical": recent_critical,
        }


# 全局实例
_audit_logger: Optional[SecurityAuditLogger] = None


def get_audit_logger() -> SecurityAuditLogger:
    """获取全局审计日志记录器实例"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = SecurityAuditLogger()
    return _audit_logger


def log_skill_execution(
    skill_name: str,
    user: Optional[str] = None,
    success: bool = True,
    duration: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """便捷函数：记录技能执行"""
    get_audit_logger().log_skill_execution(
        skill_name=skill_name,
        user=user,
        success=success,
        duration=duration,
        details=details,
    )


def log_config_change(
    old_config: Dict[str, Any],
    new_config: Dict[str, Any],
    user: Optional[str] = None,
    source: Optional[str] = None,
) -> None:
    """便捷函数：记录配置更改"""
    get_audit_logger().log_config_change(
        old_config=old_config,
        new_config=new_config,
        user=user,
        source=source,
    )


def log_access_violation(
    resource: str,
    user: Optional[str] = None,
    operation: Optional[str] = None,
    reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """便捷函数：记录访问违规"""
    get_audit_logger().log_access_violation(
        resource=resource,
        user=user,
        operation=operation,
        reason=reason,
        details=details,
    )
