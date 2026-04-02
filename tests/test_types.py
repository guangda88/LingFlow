"""Result[T] type tests"""

import pytest
from lingflow.core.types import Result


class TestResultOk:
    def test_basic(self):
        r = Result.ok(42)
        assert r.success is True
        assert r.is_ok is True
        assert r.is_error is False
        assert r.data == 42
        assert r.error is None
        assert r.code == ""

    def test_with_string(self):
        r = Result.ok("hello")
        assert r.data == "hello"

    def test_with_dict(self):
        r = Result.ok({"key": "val"})
        assert r.data == {"key": "val"}

    def test_with_none_data(self):
        r = Result.ok(None)
        assert r.success is True
        assert r.data is None

    def test_with_details(self):
        r = Result.ok(1, extra="info")
        assert r.details == {"extra": "info"}


class TestResultFail:
    def test_basic(self):
        r = Result.fail("something went wrong")
        assert r.success is False
        assert r.is_ok is False
        assert r.is_error is True
        assert r.error == "something went wrong"
        assert r.data is None

    def test_with_code(self):
        r = Result.fail("err", code="E001")
        assert r.code == "E001"

    def test_with_details(self):
        r = Result.fail("err", context="debug info")
        assert r.details == {"context": "debug info"}


class TestResultToDict:
    def test_ok_to_dict(self):
        r = Result.ok(42)
        d = r.to_dict()
        assert d["success"] is True
        assert d["data"] == 42
        assert d["error"] is None
        assert d["code"] == ""

    def test_fail_to_dict(self):
        r = Result.fail("bad", code="E1")
        d = r.to_dict()
        assert d["success"] is False
        assert d["error"] == "bad"
        assert d["code"] == "E1"


class TestResultRepr:
    def test_ok_repr(self):
        r = Result.ok(42)
        assert "Result.ok" in repr(r)
        assert "42" in repr(r)

    def test_fail_repr(self):
        r = Result.fail("oops", code="X")
        assert "Result.fail" in repr(r)
        assert "oops" in repr(r)


class TestResultEquality:
    def test_equal_ok(self):
        a = Result.ok(1)
        b = Result.ok(1)
        assert a == b

    def test_not_equal_ok(self):
        a = Result.ok(1)
        b = Result.ok(2)
        assert a != b

    def test_equal_fail(self):
        a = Result.fail("e", code="C")
        b = Result.fail("e", code="C")
        assert a == b

    def test_not_equal_types(self):
        a = Result.ok(1)
        b = Result.fail("1")
        assert a != b

    def test_not_equal_to_non_result(self):
        r = Result.ok(1)
        assert r != 1
        assert r != "not a result"
