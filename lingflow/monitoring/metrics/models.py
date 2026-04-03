"""监控指标模型

定义监控系统的核心数据模型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class MetricType(str, Enum):
    """指标类型"""

    COUNTER = "counter"  # 计数器（只增不减）
    GAUGE = "gauge"  # 仪表盘（可增可减）
    HISTOGRAM = "histogram"  # 直方图（分布统计）
    SUMMARY = "summary"  # 摘要（统计信息)


class AlertSeverity(str, Enum):
    """告警严重级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """监控指标

    Attributes:
        name: 指标名称
        type: 指标类型
        value: 指标值
        labels: 标签（用于分组和过滤）
        timestamp: 时间戳
        metadata: 额外元数据
    """

    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Alert:
    """告警信息

    Attributes:
        id: 告警ID
        severity: 严重级别
        source: 告警源
        message: 告警消息
        timestamp: 时间戳
        metadata: 元数据
        resolved: 是否已解决
        resolved_at: 解决时间
    """

    id: str
    severity: AlertSeverity
    source: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "source": self.source,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    def resolve(self) -> None:
        """解决告警"""
        self.resolved = True
        self.resolved_at = datetime.now()


@dataclass
class HealthCheckResult:
    """健康检查结果

    Attributes:
        component: 组件名称
        healthy: 是否健康
        message: 状态消息
        timestamp: 检查时间
        metrics: 相关指标
        response_time_ms: 响应时间（毫秒）
    """

    component: str
    healthy: bool
    message: str
    timestamp: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: float = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "component": self.component,
            "healthy": self.healthy,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "response_time_ms": self.response_time_ms,
        }


@dataclass
class SystemMetrics:
    """系统指标集合

    Attributes:
        cpu_percent: CPU使用率
        memory_percent: 内存使用率
        disk_usage_percent: 磁盘使用率
        network_io: 网络IO统计
        process_count: 进程数
        timestamp: 时间戳
    """

    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_io: Dict[str, int] = field(default_factory=dict)
    process_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_mb": self.memory_used_mb,
            "memory_available_mb": self.memory_available_mb,
            "disk_usage_percent": self.disk_usage_percent,
            "disk_used_gb": self.disk_used_gb,
            "disk_free_gb": self.disk_free_gb,
            "network_io": self.network_io,
            "process_count": self.process_count,
            "timestamp": self.timestamp.isoformat(),
        }

    def is_healthy(self, thresholds: Optional[Dict[str, float]] = None) -> bool:
        """检查系统是否健康

        Args:
            thresholds: 健康阈值配置

        Returns:
            是否健康
        """
        thresholds = thresholds or {"cpu_percent": 90.0, "memory_percent": 90.0, "disk_usage_percent": 90.0}

        return (
            self.cpu_percent < thresholds.get("cpu_percent", 90.0)
            and self.memory_percent < thresholds.get("memory_percent", 90.0)
            and self.disk_usage_percent < thresholds.get("disk_usage_percent", 90.0)
        )
