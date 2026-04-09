#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景测试 - 安全检测场景
基于 CodeTestScenario 测试安全漏洞检测能力
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lingflow.testing.scenario import CapturedToolCall, CodeTestScenario


class MockSecurityScanner:
    """模拟安全扫描器"""

    @staticmethod
    def scan_sql_injection(code: str) -> Dict[str, Any]:
        """扫描 SQL 注入漏洞"""
        vulnerabilities = []
        if "+" in code and "SELECT" in code:
            vulnerabilities.append(
                {
                    "type": "sql_injection",
                    "severity": "HIGH",
                    "line": 1,
                    "description": "Direct string concatenation in SQL query",
                }
            )

        return {
            "scanner": "sql_injection",
            "vulnerabilities": vulnerabilities,
            "vulnerability_count": len(vulnerabilities),
            "safe": len(vulnerabilities) == 0,
        }

    @staticmethod
    def scan_xss(code: str) -> Dict[str, Any]:
        """扫描 XSS 漏洞"""
        vulnerabilities = []
        if "return user_input" in code:
            vulnerabilities.append(
                {
                    "type": "xss",
                    "severity": "HIGH",
                    "line": 2,
                    "description": "Direct output of user input without sanitization",
                }
            )

        return {
            "scanner": "xss",
            "vulnerabilities": vulnerabilities,
            "vulnerability_count": len(vulnerabilities),
            "safe": len(vulnerabilities) == 0,
        }

    @staticmethod
    def scan_hardcoded_secrets(code: str) -> Dict[str, Any]:
        """扫描硬编码密钥"""
        vulnerabilities = []
        if "sk-" in code:
            vulnerabilities.append(
                {"type": "hardcoded_secret", "severity": "CRITICAL", "line": 1, "description": "Hardcoded API key detected"}
            )

        if "password = " in code and "123456" in code:
            vulnerabilities.append(
                {"type": "hardcoded_secret", "severity": "HIGH", "line": 2, "description": "Hardcoded weak password detected"}
            )

        return {
            "scanner": "hardcoded_secrets",
            "vulnerabilities": vulnerabilities,
            "vulnerability_count": len(vulnerabilities),
            "safe": len(vulnerabilities) == 0,
        }


class TestSecurityScenarios:
    """安全检测场景测试套件"""

    def test_sql_injection_detection(self):
        """测试 SQL 注入检测场景"""

        scenario = CodeTestScenario(
            name="detect_sql_injection",
            description="检测SQL注入漏洞",
            prompt="检测以下代码中的 SQL 注入漏洞",
            code_content="def get_user(user_id):\n    query = 'SELECT * FROM users WHERE id = ' + user_id\n    return db.execute(query)",
            max_turns=2,
            expected_tools=["security_scan"],
            expectations=lambda calls: self._validate_sql_injection(calls),
        )

        calls = [
            CapturedToolCall(
                name="security_scan",
                args={"scanner": "sql_injection"},
                timestamp=0.0,
                result={
                    "scanner": "sql_injection",
                    "vulnerabilities": [
                        {
                            "type": "sql_injection",
                            "severity": "HIGH",
                            "line": 2,
                            "description": "Direct string concatenation in SQL query",
                        }
                    ],
                    "vulnerability_count": 1,
                    "safe": False,
                },
            )
        ]

        scenario.expectations(calls)

    def _validate_sql_injection(self, calls: List[CapturedToolCall]) -> None:
        """验证 SQL 注入检测"""
        assert len(calls) > 0, "应该调用 security_scan 工具"
        call = calls[0]
        assert call.name == "security_scan"
        assert call.args.get("scanner") == "sql_injection"
        assert call.result.get("safe") is False
        assert call.result.get("vulnerability_count") > 0

    def test_xss_detection(self):
        """测试 XSS 检测场景"""

        scenario = CodeTestScenario(
            name="detect_xss",
            description="检测跨站脚本攻击(XSS)漏洞",
            prompt="检测以下代码中的 XSS 漏洞",
            code_content="def render_comment(user_input):\n    return user_input",
            max_turns=2,
            expected_tools=["security_scan"],
            expectations=lambda calls: self._validate_xss(calls),
        )

        calls = [
            CapturedToolCall(
                name="security_scan",
                args={"scanner": "xss"},
                timestamp=0.0,
                result={
                    "scanner": "xss",
                    "vulnerabilities": [
                        {
                            "type": "xss",
                            "severity": "HIGH",
                            "line": 2,
                            "description": "Direct output of user input without sanitization",
                        }
                    ],
                    "vulnerability_count": 1,
                    "safe": False,
                },
            )
        ]

        scenario.expectations(calls)

    def _validate_xss(self, calls: List[CapturedToolCall]) -> None:
        """验证 XSS 检测"""
        assert len(calls) > 0, "应该调用 security_scan 工具"
        call = calls[0]
        assert call.name == "security_scan"
        assert call.args.get("scanner") == "xss"
        assert call.result.get("safe") is False

    def test_hardcoded_secrets_detection(self):
        """测试硬编码密钥检测场景"""

        scenario = CodeTestScenario(
            name="detect_hardcoded_secrets",
            description="检测硬编码密钥和密码",
            prompt="检测以下代码中的硬编码密钥",
            code_content="api_key = 'sk-1234567890abcdef'\npassword = '123456'",
            max_turns=2,
            expected_tools=["security_scan"],
            expectations=lambda calls: self._validate_hardcoded_secrets(calls),
        )

        calls = [
            CapturedToolCall(
                name="security_scan",
                args={"scanner": "hardcoded_secrets"},
                timestamp=0.0,
                result={
                    "scanner": "hardcoded_secrets",
                    "vulnerabilities": [
                        {
                            "type": "hardcoded_secret",
                            "severity": "CRITICAL",
                            "line": 1,
                            "description": "Hardcoded API key detected",
                        },
                        {
                            "type": "hardcoded_secret",
                            "severity": "HIGH",
                            "line": 2,
                            "description": "Hardcoded weak password detected",
                        },
                    ],
                    "vulnerability_count": 2,
                    "safe": False,
                },
            )
        ]

        scenario.expectations(calls)

    def _validate_hardcoded_secrets(self, calls: List[CapturedToolCall]) -> None:
        """验证硬编码密钥检测"""
        assert len(calls) > 0, "应该调用 security_scan 工具"
        call = calls[0]
        assert call.name == "security_scan"
        assert call.args.get("scanner") == "hardcoded_secrets"
        assert call.result.get("safe") is False
        assert call.result.get("vulnerability_count") >= 2

    def test_comprehensive_security_scan(self):
        """测试综合安全扫描场景"""

        scenario = CodeTestScenario(
            name="comprehensive_security_scan",
            description="对代码进行综合安全扫描",
            prompt="对以下代码进行全面的安全扫描，检测所有可能的安全问题",
            code_content="def process_data(user_input, user_id):\n    query = 'SELECT * FROM data WHERE id = ' + user_id\n    import os\n    os.system('process ' + user_input)\n    api_key = 'sk-abc123'\n    return result",
            max_turns=5,
            expected_tools=["security_scan"],
            expectations=lambda calls: self._validate_comprehensive_scan(calls),
        )

        calls = [
            CapturedToolCall(
                name="security_scan",
                args={"scanner": "sql_injection"},
                timestamp=0.0,
                result={"vulnerability_count": 1, "safe": False},
            ),
            CapturedToolCall(
                name="security_scan",
                args={"scanner": "hardcoded_secrets"},
                timestamp=1.0,
                result={"vulnerability_count": 1, "safe": False},
            ),
        ]

        scenario.expectations(calls)

    def _validate_comprehensive_scan(self, calls: List[CapturedToolCall]) -> None:
        """验证综合扫描"""
        assert len(calls) >= 2, "应该调用至少 2 次安全扫描"
        scanners = [call.args.get("scanner") for call in calls]
        assert "sql_injection" in scanners
        assert "hardcoded_secrets" in scanners


class TestSecurityScannerFunctionality:
    """安全扫描器功能测试"""

    def test_sql_injection_scanner(self):
        """测试 SQL 注入扫描器"""
        scanner = MockSecurityScanner()
        vulnerable_code = "query = 'SELECT * FROM users WHERE id = ' + user_id"
        result = scanner.scan_sql_injection(vulnerable_code)

        assert result["scanner"] == "sql_injection"
        assert isinstance(result["safe"], bool)

    def test_xss_scanner(self):
        """测试 XSS 扫描器"""
        scanner = MockSecurityScanner()
        vulnerable_code = "return user_input"
        result = scanner.scan_xss(vulnerable_code)

        assert result["scanner"] == "xss"
        assert result["vulnerability_count"] > 0
        assert result["safe"] is False

    def test_hardcoded_secrets_scanner(self):
        """测试硬编码密钥扫描器"""
        scanner = MockSecurityScanner()
        vulnerable_code = "api_key = 'sk-123456'"
        result = scanner.scan_hardcoded_secrets(vulnerable_code)

        assert result["scanner"] == "hardcoded_secrets"
        assert result["vulnerability_count"] > 0
        assert result["safe"] is False

    def test_safe_code_scanning(self):
        """测试安全代码扫描"""
        scanner = MockSecurityScanner()
        safe_code = "def safe_function(): return 'safe'"
        result_sql = scanner.scan_sql_injection(safe_code)
        result_xss = scanner.scan_xss(safe_code)

        assert result_sql["safe"] is True
        assert result_xss["safe"] is True


# 主测试入口
if __name__ == "__main__":  # pragma: no cover
    import logging

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("场景测试 - 安全检测场景")
    print("=" * 70)

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
