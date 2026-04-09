"""
Phase 5 AI工具适配器测试

测试适配器的基本功能和集成。
"""

import tempfile
from pathlib import Path

import pytest

from lingflow.self_optimizer.phase5.adapters import (
    AIToolAdapter,
    PylintAdapter,
    RuffAdapter,
    SemgrepAdapter,
    get_adapter,
    get_available_adapters,
)
from lingflow.self_optimizer.phase5.models import (
    FeedbackCategory,
    FeedbackSeverity,
    FeedbackSource,
)


class TestAdapters:
    """测试适配器基本功能"""

    def test_adapter_factory(self):
        """测试适配器工厂"""
        # 测试Semgrep适配器
        semgrep = get_adapter(FeedbackSource.SEMGREP)
        assert semgrep is not None
        assert isinstance(semgrep, SemgrepAdapter)

        # 测试Ruff适配器
        ruff = get_adapter(FeedbackSource.RUFF)
        assert ruff is not None
        assert isinstance(ruff, RuffAdapter)

        # 测试Pylint适配器
        pylint = get_adapter(FeedbackSource.PYLINT)
        assert pylint is not None
        assert isinstance(pylint, PylintAdapter)

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        config = {"timeout": 100, "max_issues": 500}

        adapter = SemgrepAdapter(config)
        assert adapter.timeout == 100
        assert adapter.max_issues == 500
        assert adapter.enabled is True

    def test_semgrep_adapter_check_available(self):
        """测试Semgrep可用性检查"""
        adapter = SemgrepAdapter()
        available = adapter.check_available()

        # 只验证不抛出异常
        assert isinstance(available, bool)

    def test_ruff_adapter_check_available(self):
        """测试Ruff可用性检查"""
        adapter = RuffAdapter()
        available = adapter.check_available()

        # 只验证不抛出异常
        assert isinstance(available, bool)

    def test_pylint_adapter_check_available(self):
        """测试Pylint可用性检查"""
        adapter = PylintAdapter()
        available = adapter.check_available()

        # 只验证不抛出异常
        assert isinstance(available, bool)

    def test_adapter_with_disabled_config(self):
        """测试禁用配置"""
        config = {"enabled": False}
        adapter = SemgrepAdapter(config)

        assert adapter.enabled is False

    def test_semgrep_parse_severity(self):
        """测试Semgrep严重程度解析"""
        adapter = SemgrepAdapter()

        assert adapter._parse_severity("error") == FeedbackSeverity.HIGH
        assert adapter._parse_severity("warning") == FeedbackSeverity.MEDIUM
        assert adapter._parse_severity("info") == FeedbackSeverity.INFO
        assert adapter._parse_severity("critical") == FeedbackSeverity.CRITICAL

    def test_ruff_parse_severity(self):
        """测试Ruff严重程度解析"""
        adapter = RuffAdapter()

        assert adapter._parse_ruff_severity("E501") == FeedbackSeverity.MEDIUM
        assert adapter._parse_ruff_severity("F401") == FeedbackSeverity.MEDIUM
        assert adapter._parse_ruff_severity("S123") == FeedbackSeverity.HIGH

    def test_pylint_parse_severity(self):
        """测试Pylint严重程度解析"""
        adapter = PylintAdapter()

        assert adapter._parse_pylint_severity("error", "E1101") == FeedbackSeverity.HIGH
        assert adapter._parse_pylint_severity("warning", "W0212") == FeedbackSeverity.MEDIUM
        assert adapter._parse_pylint_severity("fatal", "F0001") == FeedbackSeverity.CRITICAL

    def test_get_available_adapters(self):
        """测试获取可用适配器"""
        adapters = get_available_adapters()

        # 验证返回的是列表
        assert isinstance(adapters, list)

        # 验证所有元素都是适配器实例
        for adapter in adapters:
            assert isinstance(adapter, AIToolAdapter)


class TestAdapterIntegration:
    """测试适配器集成"""

    def test_adapter_with_sample_code(self):
        """测试适配器处理示例代码"""
        # 创建临时文件
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
import os
import sys

def unused_function():
    x = 1
    y = 2
    return x + y

def test():
    pass
""")

            # 测试Ruff适配器
            ruff = RuffAdapter()
            if ruff.check_available():
                feedback = ruff.run_scan(str(tmpdir))
                # 验证返回列表
                assert isinstance(feedback, list)

    def test_semgrep_with_json_output(self):
        """测试Semgrep JSON输出解析"""
        adapter = SemgrepAdapter()

        # 模拟Semgrep JSON输出
        mock_output = """{
    "results": [
        {
            "check_id": "python.flask.security.xss-detected",
            "path": "test.py",
            "start": {"line": 10, "col": 5},
            "end": {"line": 10, "col": 20},
            "extra": {
                "message": "Possible XSS detected",
                "severity": "ERROR",
                "lines": "return render_template_string(user_input)"
            }
        }
    ]
}"""

        feedback = adapter._parse_semgrep_output(mock_output, ".")
        assert len(feedback) == 1
        assert feedback[0].source == FeedbackSource.SEMGREP
        assert feedback[0].category == FeedbackCategory.SECURITY

    def test_ruff_with_json_output(self):
        """测试Ruff JSON输出解析"""
        adapter = RuffAdapter()

        # 模拟Ruff JSON输出
        mock_output = """[
    {
        "code": "F401",
        "message": "unused import",
        "location": {
            "row": 1,
            "column": 0
        },
        "end_location": {
            "row": 1,
            "column": 10
        },
        "path": "test.py"
    }
]"""

        feedback = adapter._parse_ruff_output(mock_output)
        assert len(feedback) == 1
        assert feedback[0].source == FeedbackSource.RUFF
        assert feedback[0].rule_id == "F401"


if __name__ == "__main__":  # pragma: no cover
    # 运行测试
    pytest.main([__file__, "-v"])
