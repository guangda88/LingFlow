"""告警规则模块

提供告警规则的配置和管理功能。
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..metrics.models import Alert, AlertSeverity

logger = logging.getLogger(__name__)


class AlertRule:
    """告警规则

    定义告警的触发条件、严重级别和消息模板。
    """

    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        severity: AlertSeverity,
        message_template: str,
        cooldown_seconds: int = 300,
        enabled: bool = True,
    ):
        """初始化告警规则

        Args:
            name: 规则名称
            condition: 触发条件函数
            severity: 严重级别
            message_template: 消息模板（支持格式化）
            cooldown_seconds: 冷却时间（秒）
            enabled: 是否启用
        """
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message_template = message_template
        self.cooldown_seconds = cooldown_seconds
        self.enabled = enabled
        self.last_triggered: Optional[datetime] = None
        self.trigger_count = 0

    def should_trigger(self, metrics: Dict[str, Any]) -> bool:
        """检查是否应该触发告警

        Args:
            metrics: 当前指标数据

        Returns:
            是否应该触发
        """
        if not self.enabled:
            return False

        now = datetime.now()

        # 检查冷却期
        if self.last_triggered:
            elapsed = (now - self.last_triggered).total_seconds()
            if elapsed < self.cooldown_seconds:
                return False

        # 检查条件
        if self.condition(metrics):
            self.last_triggered = now
            self.trigger_count += 1
            return True

        return False

    def format_message(self, metrics: Dict[str, Any]) -> str:
        """格式化告警消息

        Args:
            metrics: 指标数据

        Returns:
            格式化的消息
        """
        try:
            return self.message_template.format(**metrics)
        except (KeyError, ValueError) as e:
            logger.warning(f"消息格式化失败: {e}")
            return self.message_template

    def create_alert(self, source: str, metrics: Dict[str, Any], alert_id: Optional[str] = None) -> Alert:
        """创建告警对象

        Args:
            source: 告警源
            metrics: 指标数据
            alert_id: 告警ID（可选）

        Returns:
            告警对象
        """
        import uuid

        return Alert(
            id=alert_id or str(uuid.uuid4()),
            severity=self.severity,
            source=source,
            message=self.format_message(metrics),
            timestamp=datetime.now(),
            metadata={"rule": self.name, "trigger_count": self.trigger_count, "metrics": metrics},
        )


class RuleRegistry:
    """告警规则注册表

    管理所有告警规则。
    """

    def __init__(self):
        """初始化规则注册表"""
        self._rules: Dict[str, AlertRule] = {}

    def register(self, rule: AlertRule) -> None:
        """注册规则

        Args:
            rule: 告警规则
        """
        self._rules[rule.name] = rule
        logger.debug(f"注册告警规则: {rule.name}")

    def unregister(self, rule_name: str) -> bool:
        """注销规则

        Args:
            rule_name: 规则名称

        Returns:
            是否成功
        """
        if rule_name in self._rules:
            del self._rules[rule_name]
            return True
        return False

    def get(self, rule_name: str) -> Optional[AlertRule]:
        """获取规则

        Args:
            rule_name: 规则名称

        Returns:
            规则对象，不存在返回None
        """
        return self._rules.get(rule_name)

    def get_all(self) -> Dict[str, AlertRule]:
        """获取所有规则

        Returns:
            规则字典
        """
        return self._rules.copy()

    def enable(self, rule_name: str) -> bool:
        """启用规则

        Args:
            rule_name: 规则名称

        Returns:
            是否成功
        """
        rule = self.get(rule_name)
        if rule:
            rule.enabled = True
            return True
        return False

    def disable(self, rule_name: str) -> bool:
        """禁用规则

        Args:
            rule_name: 规则名称

        Returns:
            是否成功
        """
        rule = self.get(rule_name)
        if rule:
            rule.enabled = False
            return True
        return False

    def evaluate_all(self, metrics: Dict[str, Any], source: str) -> List[Alert]:
        """评估所有规则

        Args:
            metrics: 指标数据
            source: 告警源

        Returns:
            触发的告警列表
        """
        alerts = []

        for rule in self._rules.values():
            if rule.should_trigger(metrics):
                alert = rule.create_alert(source, metrics)
                alerts.append(alert)
                logger.info(f"告警触发: {rule.name} - {alert.message}")

        return alerts


# 预定义的通用规则
def create_common_rules() -> List[AlertRule]:
    """创建常用的告警规则

    Returns:
        规则列表
    """
    return [
        AlertRule(
            name="high_cpu",
            condition=lambda m: m.get("cpu_percent", 0) > 90,
            severity=AlertSeverity.WARNING,
            message_template="CPU使用率过高: {cpu_percent:.1f}%",
            cooldown_seconds=300,
        ),
        AlertRule(
            name="high_memory",
            condition=lambda m: m.get("memory_percent", 0) > 90,
            severity=AlertSeverity.WARNING,
            message_template="内存使用率过高: {memory_percent:.1f}%",
            cooldown_seconds=300,
        ),
        AlertRule(
            name="high_disk",
            condition=lambda m: m.get("disk_usage_percent", 0) > 90,
            severity=AlertSeverity.ERROR,
            message_template="磁盘使用率过高: {disk_usage_percent:.1f}%",
            cooldown_seconds=600,
        ),
        AlertRule(
            name="critical_cpu",
            condition=lambda m: m.get("cpu_percent", 0) > 95,
            severity=AlertSeverity.CRITICAL,
            message_template="CPU使用率危急: {cpu_percent:.1f}%",
            cooldown_seconds=120,
        ),
        AlertRule(
            name="critical_memory",
            condition=lambda m: m.get("memory_percent", 0) > 95,
            severity=AlertSeverity.CRITICAL,
            message_template="内存使用率危急: {memory_percent:.1f}%",
            cooldown_seconds=120,
        ),
    ]
