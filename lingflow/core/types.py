"""lingflow Core Types

This module provides standardized types for the lingflow framework.
"""

from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


class Result(Generic[T]):
    """Result type for handling success/failure states.

    Simplified design following DEVELOPMENT_RULES.md:
    - Only 5 members: ok(), fail(), is_ok, is_error, to_dict()
    - No unwrap() or unwrap_or() methods (removed for simplicity)
    - Type-safe with generic T parameter
    """

    def __init__(
        self,
        data: Optional[T],
        error: Optional[str],
        code: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Result.

        Args:
            data: Success data (if success)
            error: Error message (if failure)
            code: Error code
            details: Additional details
        """
        self._data = data
        self._error = error
        self._code = code
        self._details = details or {}

    @property
    def success(self) -> bool:
        """Check if result is successful."""
        return self._error is None

    @property
    def is_ok(self) -> bool:
        """Alias for success."""
        return self.success

    @property
    def is_error(self) -> bool:
        """Check if result is an error."""
        return not self.success

    @property
    def data(self) -> Optional[T]:
        """Get the success data."""
        return self._data

    @property
    def error(self) -> Optional[str]:
        """Get the error message."""
        return self._error

    @property
    def code(self) -> str:
        """Get the error code."""
        return self._code

    @property
    def details(self) -> Dict[str, Any]:
        """Get additional details."""
        return self._details

    @classmethod
    def ok(cls, data: T, **details: Any) -> "Result[T]":
        """Create a successful result.

        Args:
            data: Success data
            **details: Additional details

        Returns:
            Successful Result
        """
        return cls(data=data, error=None, code="", details=details)

    @classmethod
    def fail(
        cls,
        error: str,
        code: str = "",
        **details: Any,
    ) -> "Result[T]":
        """Create a failed result.

        Args:
            error: Error message
            code: Error code
            **details: Additional details

        Returns:
            Failed Result
        """
        return cls(data=None, error=error, code=code, details=details)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Result to dictionary for backward compatibility.

        Returns:
            Dictionary representation
        """
        return {
            "success": self.success,
            "data": self._data,
            "error": self._error,
            "code": self._code,
            "details": self._details,
        }

    def __repr__(self) -> str:
        if self.success:
            return f"Result.ok({self._data})"
        return f"Result.fail({self._error}, code={self._code})"

    def __eq__(self, other: object) -> bool:
        """Compare two Results."""
        if not isinstance(other, Result):
            return False
        return self._data == other._data and self._error == other._error and self._code == other._code
