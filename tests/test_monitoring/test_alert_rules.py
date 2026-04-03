"""Tests for lingflow.monitoring.alerts.rules module"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from lingflow.monitoring.alerts.rules import AlertRule, RuleRegistry, create_common_rules
from lingflow.monitoring.metrics.models import AlertSeverity, Alert


class TestAlertRule:
    """Test AlertRule class"""

    def test_create_rule(self):
        """Test creating an alert rule"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 100,
            severity=AlertSeverity.WARNING,
            message_template="Value {value} exceeds threshold",
            cooldown_seconds=300,
            enabled=True,
        )

        assert rule.name == "test_rule"
        assert rule.severity == AlertSeverity.WARNING
        assert rule.message_template == "Value {value} exceeds threshold"
        assert rule.cooldown_seconds == 300
        assert rule.enabled is True
        assert rule.last_triggered is None
        assert rule.trigger_count == 0

    def test_should_trigger_condition_met(self):
        """Test should_trigger when condition is met"""
        rule = AlertRule(
            name="high_value",
            condition=lambda m: m.get("value", 0) > 100,
            severity=AlertSeverity.WARNING,
            message_template="High value: {value}",
            cooldown_seconds=0,  # No cooldown
        )

        metrics = {"value": 150}
        should_trigger = rule.should_trigger(metrics)

        assert should_trigger is True
        assert rule.trigger_count == 1
        assert rule.last_triggered is not None

    def test_should_trigger_condition_not_met(self):
        """Test should_trigger when condition is not met"""
        rule = AlertRule(
            name="high_value",
            condition=lambda m: m.get("value", 0) > 100,
            severity=AlertSeverity.WARNING,
            message_template="High value: {value}",
        )

        metrics = {"value": 50}
        should_trigger = rule.should_trigger(metrics)

        assert should_trigger is False
        assert rule.trigger_count == 0
        assert rule.last_triggered is None

    def test_should_trigger_disabled_rule(self):
        """Test should_trigger with disabled rule"""
        rule = AlertRule(
            name="disabled_rule",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Test",
            enabled=False,
        )

        should_trigger = rule.should_trigger({})

        assert should_trigger is False

    def test_should_trigger_with_cooldown(self):
        """Test should_trigger respects cooldown period"""
        rule = AlertRule(
            name="cooldown_rule",
            condition=lambda m: m.get("value", 0) > 100,
            severity=AlertSeverity.WARNING,
            message_template="High value",
            cooldown_seconds=60,
        )

        metrics = {"value": 150}

        # First trigger
        assert rule.should_trigger(metrics) is True
        assert rule.trigger_count == 1

        # Immediate second trigger should be blocked by cooldown
        assert rule.should_trigger(metrics) is False

        # Simulate cooldown expiry
        rule.last_triggered = datetime.now() - timedelta(seconds=61)

        # Should trigger again after cooldown
        assert rule.should_trigger(metrics) is True
        assert rule.trigger_count == 2

    def test_format_message_success(self):
        """Test formatting message with valid template"""
        rule = AlertRule(
            name="test",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="CPU usage is {cpu_percent}%",
        )

        metrics = {"cpu_percent": 75.5}
        message = rule.format_message(metrics)

        assert message == "CPU usage is 75.5%"

    def test_format_message_missing_key(self):
        """Test formatting message with missing key"""
        rule = AlertRule(
            name="test",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Value is {missing_key}",
        )

        metrics = {"other_key": 100}
        message = rule.format_message(metrics)

        # Should return original template on error
        assert message == "Value is {missing_key}"

    def test_format_message_no_placeholders(self):
        """Test formatting message with no placeholders"""
        rule = AlertRule(
            name="test",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Static message",
        )

        message = rule.format_message({})
        assert message == "Static message"

    def test_create_alert(self):
        """Test creating alert from rule"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value") > 100,
            severity=AlertSeverity.WARNING,
            message_template="Value {value} is high",
        )

        metrics = {"value": 150}
        alert = rule.create_alert("test_source", metrics, alert_id="custom-alert-id")

        assert isinstance(alert, Alert)
        assert alert.id == "custom-alert-id"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.source == "test_source"
        assert alert.message == "Value 150 is high"
        assert alert.metadata["rule"] == "test_rule"
        assert alert.metadata["metrics"]["value"] == 150

    def test_create_alert_auto_id(self):
        """Test creating alert with auto-generated ID"""
        rule = AlertRule(
            name="auto_id_rule",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Test message",
        )

        alert = rule.create_alert("test", {})

        assert alert.id is not None
        assert len(alert.id) > 0
        assert isinstance(alert.id, str)


class TestRuleRegistry:
    """Test RuleRegistry class"""

    def test_init(self):
        """Test initialization"""
        registry = RuleRegistry()
        assert registry._rules == {}

    def test_register_rule(self):
        """Test registering a rule"""
        registry = RuleRegistry()
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Test",
        )

        registry.register(rule)

        assert "test_rule" in registry._rules
        assert registry._rules["test_rule"] == rule

    def test_register_multiple_rules(self):
        """Test registering multiple rules"""
        registry = RuleRegistry()

        for i in range(5):
            rule = AlertRule(
                name=f"rule_{i}",
                condition=lambda m: True,
                severity=AlertSeverity.INFO,
                message_template=f"Rule {i}",
            )
            registry.register(rule)

        assert len(registry._rules) == 5

    def test_unregister_rule_exists(self):
        """Test unregistering existing rule"""
        registry = RuleRegistry()
        rule = AlertRule(
            name="to_remove",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Remove me",
        )
        registry.register(rule)

        assert "to_remove" in registry._rules

        result = registry.unregister("to_remove")

        assert result is True
        assert "to_remove" not in registry._rules

    def test_unregister_rule_not_exists(self):
        """Test unregistering non-existent rule"""
        registry = RuleRegistry()
        result = registry.unregister("nonexistent")

        assert result is False

    def test_get_rule_exists(self):
        """Test getting existing rule"""
        registry = RuleRegistry()
        rule = AlertRule(
            name="get_test",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Test",
        )
        registry.register(rule)

        retrieved = registry.get("get_test")

        assert retrieved is not None
        assert retrieved == rule

    def test_get_rule_not_exists(self):
        """Test getting non-existent rule"""
        registry = RuleRegistry()
        retrieved = registry.get("nonexistent")

        assert retrieved is None

    def test_get_all(self):
        """Test getting all rules"""
        registry = RuleRegistry()

        rules = [
            AlertRule(name=f"rule_{i}", condition=lambda m: True, severity=AlertSeverity.INFO, message_template=f"R{i}")
            for i in range(3)
        ]

        for rule in rules:
            registry.register(rule)

        all_rules = registry.get_all()

        assert len(all_rules) == 3
        assert "rule_0" in all_rules
        assert "rule_1" in all_rules
        assert "rule_2" in all_rules

    def test_get_all_returns_copy(self):
        """Test that get_all returns a copy"""
        registry = RuleRegistry()
        rule = AlertRule(
            name="original",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Original",
        )
        registry.register(rule)

        all_rules = registry.get_all()
        all_rules["new"] = AlertRule(
            name="new",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="New",
        )

        assert "new" not in registry._rules

    def test_enable_rule(self):
        """Test enabling a rule"""
        registry = RuleRegistry()
        rule = AlertRule(
            name="toggle_rule",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Toggle",
            enabled=False,
        )
        registry.register(rule)

        assert rule.enabled is False

        result = registry.enable("toggle_rule")

        assert result is True
        assert rule.enabled is True

    def test_enable_rule_not_exists(self):
        """Test enabling non-existent rule"""
        registry = RuleRegistry()
        result = registry.enable("nonexistent")

        assert result is False

    def test_disable_rule(self):
        """Test disabling a rule"""
        registry = RuleRegistry()
        rule = AlertRule(
            name="toggle_rule",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Toggle",
            enabled=True,
        )
        registry.register(rule)

        assert rule.enabled is True

        result = registry.disable("toggle_rule")

        assert result is True
        assert rule.enabled is False

    def test_evaluate_all_no_matches(self):
        """Test evaluating all rules with no matches"""
        registry = RuleRegistry()

        rule1 = AlertRule(
            name="rule1",
            condition=lambda m: m.get("value") > 100,
            severity=AlertSeverity.WARNING,
            message_template="High value",
        )
        rule2 = AlertRule(
            name="rule2",
            condition=lambda m: m.get("value") < 0,
            severity=AlertSeverity.WARNING,
            message_template="Negative value",
        )

        registry.register(rule1)
        registry.register(rule2)

        metrics = {"value": 50}
        alerts = registry.evaluate_all(metrics, "test_source")

        assert len(alerts) == 0

    def test_evaluate_all_with_matches(self):
        """Test evaluating all rules with matches"""
        registry = RuleRegistry()

        rule1 = AlertRule(
            name="high",
            condition=lambda m: m.get("value", 0) > 100,
            severity=AlertSeverity.WARNING,
            message_template="High: {value}",
        )
        rule2 = AlertRule(
            name="low",
            condition=lambda m: m.get("value", 0) < 0,
            severity=AlertSeverity.WARNING,
            message_template="Low: {value}",
        )

        registry.register(rule1)
        registry.register(rule2)

        # Value exceeds threshold for rule1
        metrics = {"value": 150}
        alerts = registry.evaluate_all(metrics, "test")

        assert len(alerts) == 1
        assert alerts[0].metadata["rule"] == "high"
        assert "150" in alerts[0].message

    def test_evaluate_all_multiple_matches(self):
        """Test evaluating all rules with multiple matches"""
        registry = RuleRegistry()

        rule1 = AlertRule(
            name="rule1",
            condition=lambda m: m.get("cpu", 0) > 90,
            severity=AlertSeverity.WARNING,
            message_template="High CPU",
            cooldown_seconds=0,
        )
        rule2 = AlertRule(
            name="rule2",
            condition=lambda m: m.get("mem", 0) > 90,
            severity=AlertSeverity.WARNING,
            message_template="High memory",
            cooldown_seconds=0,
        )

        registry.register(rule1)
        registry.register(rule2)

        metrics = {"cpu": 95, "mem": 92}
        alerts = registry.evaluate_all(metrics, "monitor")

        assert len(alerts) == 2

    def test_evaluate_all_disabled_rules(self):
        """Test that disabled rules are not evaluated"""
        registry = RuleRegistry()

        enabled_rule = AlertRule(
            name="enabled",
            condition=lambda m: m.get("value", 0) > 50,
            severity=AlertSeverity.WARNING,
            message_template="Enabled",
            enabled=True,
        )
        disabled_rule = AlertRule(
            name="disabled",
            condition=lambda m: m.get("value", 0) > 50,
            severity=AlertSeverity.WARNING,
            message_template="Disabled",
            enabled=False,
        )

        registry.register(enabled_rule)
        registry.register(disabled_rule)

        metrics = {"value": 100}
        alerts = registry.evaluate_all(metrics, "test")

        assert len(alerts) == 1
        assert alerts[0].metadata["rule"] == "enabled"


class TestCreateCommonRules:
    """Test create_common_rules factory function"""

    def test_create_common_rules_returns_list(self):
        """Test that create_common_rules returns a list"""
        rules = create_common_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_common_rules_content(self):
        """Test content of common rules"""
        rules = create_common_rules()
        rule_names = [r.name for r in rules]

        assert "high_cpu" in rule_names
        assert "high_memory" in rule_names
        assert "high_disk" in rule_names
        assert "critical_cpu" in rule_names
        assert "critical_memory" in rule_names

    def test_common_rules_conditions(self):
        """Test that common rules have correct conditions"""
        rules = create_common_rules()

        # Find high_cpu rule
        high_cpu = next(r for r in rules if r.name == "high_cpu")

        # Should trigger when CPU > 90
        assert high_cpu.should_trigger({"cpu_percent": 95}) is True
        assert high_cpu.should_trigger({"cpu_percent": 85}) is False

    def test_common_rules_severities(self):
        """Test that common rules have correct severities"""
        rules = create_common_rules()

        high_cpu = next(r for r in rules if r.name == "high_cpu")
        critical_cpu = next(r for r in rules if r.name == "critical_cpu")
        high_disk = next(r for r in rules if r.name == "high_disk")

        assert high_cpu.severity == AlertSeverity.WARNING
        assert critical_cpu.severity == AlertSeverity.CRITICAL
        assert high_disk.severity == AlertSeverity.ERROR

    def test_common_rules_cooldowns(self):
        """Test that common rules have appropriate cooldowns"""
        rules = create_common_rules()

        high_cpu = next(r for r in rules if r.name == "high_cpu")
        critical_cpu = next(r for r in rules if r.name == "critical_cpu")
        high_disk = next(r for r in rules if r.name == "high_disk")

        assert high_cpu.cooldown_seconds == 300
        assert critical_cpu.cooldown_seconds == 120
        assert high_disk.cooldown_seconds == 600
