"""测试核心类型系统"""
import pytest

from lingflow.core.types import Result


class TestResult:
    """测试Result类型"""

    def test_result_success(self):
        """测试成功结果"""
        result = Result.ok(data={"output": "result"})
        assert result.is_ok is True
        assert result.success is True
        assert result.data == {"output": "result"}
        assert result.error is None

    def test_result_failure(self):
        """测试失败结果"""
        result = Result.fail(error="Test error", code="ERR001")
        assert result.is_error is True
        assert result.error == "Test error"
        assert result.code == "ERR001"

    def test_result_to_dict(self):
        """测试结果转换为字典"""
        result = Result.ok(data={"key": "value"})
        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["data"] == {"key": "value"}

    def test_result_with_details(self):
        """测试带详情的结果"""
        result = Result.ok(data="test", detail1="value1", detail2=42)
        assert result.details == {"detail1": "value1", "detail2": 42}

    def test_result_equality(self):
        """测试结果相等性"""
        result1 = Result.ok(data="same")
        result2 = Result.ok(data="same")
        assert result1 == result2

        result3 = Result.ok(data="different")
        assert result1 != result3

    def test_result_repr(self):
        """测试结果字符串表示"""
        result_ok = Result.ok(data="test")
        assert "Result.ok" in repr(result_ok)

        result_fail = Result.fail(error="error")
        assert "Result.fail" in repr(result_fail)