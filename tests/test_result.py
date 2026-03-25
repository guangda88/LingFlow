"""Unit tests for lingflow.core.types module."""

import pytest

from lingflow.core.types import LingFlowError, Result


class TestLingFlowError:
    """Test LingFlowError exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = LingFlowError("Test error")
        assert error.message == "Test error"
        assert error.code == "LF_ERROR"
        assert error.details == {}

    def test_error_with_code(self):
        """Test error with custom code."""
        error = LingFlowError("Test error", code="CUSTOM_ERROR")
        assert error.code == "CUSTOM_ERROR"

    def test_error_with_details(self):
        """Test error with details."""
        details = {"file": "test.py", "line": 10}
        error = LingFlowError("Test error", details=details)
        assert error.details == details

    def test_error_str_representation(self):
        """Test error string representation."""
        error = LingFlowError("Test error", code="TEST")
        assert str(error) == "[TEST] Test error"

    def test_error_raise(self):
        """Test raising LingFlowError."""
        with pytest.raises(LingFlowError) as exc_info:
            raise LingFlowError("Test error")
        assert str(exc_info.value) == "[LF_ERROR] Test error"


class TestResult:
    """Test Result type."""

    def test_result_ok_creation(self):
        """Test creating a successful Result."""
        result = Result.ok(42)
        assert result.success
        assert result.data == 42
        assert result.error is None
        assert result.is_ok
        assert not result.is_error

    def test_result_ok_with_details(self):
        """Test creating a successful Result with details."""
        result = Result.ok(42, timestamp="2024-01-01")
        assert result.success
        assert result.data == 42
        assert result.details == {"timestamp": "2024-01-01"}

    def test_result_fail_creation(self):
        """Test creating a failed Result."""
        result = Result.fail("Test error")
        assert not result.success
        assert result.data is None
        assert result.error == "Test error"
        assert result.is_error
        assert not result.is_ok

    def test_result_fail_with_code(self):
        """Test creating a failed Result with code."""
        result = Result.fail("Test error", code="ERROR_CODE")
        assert result.code == "ERROR_CODE"

    def test_result_fail_with_details(self):
        """Test creating a failed Result with details."""
        result = Result.fail("Test error", code="ERROR_CODE", file="test.py")
        assert result.details == {"file": "test.py"}

    def test_result_ok_string_data(self):
        """Test Result with string data."""
        result = Result.ok("Hello")
        assert result.data == "Hello"

    def test_result_ok_dict_data(self):
        """Test Result with dict data."""
        data = {"key": "value"}
        result = Result.ok(data)
        assert result.data == data

    def test_result_ok_list_data(self):
        """Test Result with list data."""
        data = [1, 2, 3]
        result = Result.ok(data)
        assert result.data == data

    def test_result_ok_none_data(self):
        """Test Result with None data (success with no data)."""
        result = Result.ok(None)
        assert result.success
        assert result.data is None

    def test_result_to_dict_success(self):
        """Test converting successful Result to dict."""
        result = Result.ok(42, extra="info")
        result_dict = result.to_dict()
        assert result_dict == {
            "success": True,
            "data": 42,
            "error": None,
            "code": "",
            "details": {"extra": "info"},
        }

    def test_result_to_dict_failure(self):
        """Test converting failed Result to dict."""
        result = Result.fail("Error message", code="ERR", context="test")
        result_dict = result.to_dict()
        assert result_dict == {
            "success": False,
            "data": None,
            "error": "Error message",
            "code": "ERR",
            "details": {"context": "test"},
        }

    def test_result_repr_success(self):
        """Test Result.__repr__ for success."""
        result = Result.ok(42)
        assert repr(result) == "Result.ok(42)"

    def test_result_repr_failure(self):
        """Test Result.__repr__ for failure."""
        result = Result.fail("Error", code="ERR")
        assert repr(result) == "Result.fail(Error, code=ERR)"

    def test_result_equality_success(self):
        """Test Result equality for success."""
        result1 = Result.ok(42)
        result2 = Result.ok(42)
        assert result1 == result2

    def test_result_inequality_success(self):
        """Test Result inequality for success."""
        result1 = Result.ok(42)
        result2 = Result.ok(43)
        assert result1 != result2

    def test_result_equality_failure(self):
        """Test Result equality for failure."""
        result1 = Result.fail("Error", code="ERR")
        result2 = Result.fail("Error", code="ERR")
        assert result1 == result2

    def test_result_inequality_failure(self):
        """Test Result inequality for failure."""
        result1 = Result.fail("Error1")
        result2 = Result.fail("Error2")
        assert result1 != result2

    def test_result_equality_mixed(self):
        """Test Result equality between success and failure."""
        result1 = Result.ok(42)
        result2 = Result.fail("Error")
        assert result1 != result2

    def test_result_not_equal_non_result(self):
        """Test Result comparison with non-Result object."""
        result = Result.ok(42)
        assert result != 42

    def test_result_generic_type_int(self):
        """Test Result with int type."""
        result: Result[int] = Result.ok(42)
        assert isinstance(result.data, int)

    def test_result_generic_type_str(self):
        """Test Result with str type."""
        result: Result[str] = Result.ok("hello")
        assert isinstance(result.data, str)

    def test_result_generic_type_dict(self):
        """Test Result with dict type."""
        result: Result[dict] = Result.ok({"key": "value"})
        assert isinstance(result.data, dict)

    def test_result_properties_readonly(self):
        """Test that Result properties are set correctly."""
        result = Result.ok(42)
        assert result._data == 42
        assert result._error is None

        fail_result = Result.fail("Error")
        assert fail_result._data is None
        assert fail_result._error == "Error"
