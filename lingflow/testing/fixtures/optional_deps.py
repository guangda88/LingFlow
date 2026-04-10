"""Optional dependency management for tests.

Provides a centralized way to handle optional dependencies (flask, fastapi,
websockets, etc.) so that pytest collection never fails due to missing imports.

Usage in test files:
    from lingflow.testing.fixtures.optional_deps import require

    flask = require("flask", "Flask needed for API tests")
    # flask is now the module, or the test is skipped entirely
"""

from typing import Any

import pytest


def require(module_name: str, reason: str = "") -> Any:
    """Import an optional dependency, skipping the test if unavailable.

    This uses pytest.importorskip so that:
    - During collection: the test file loads without ImportError
    - During execution: the test is skipped with a clear reason

    Args:
        module_name: The module to import (e.g. "flask", "fastapi")
        reason: Why this module is needed (shown in skip message)

    Returns:
        The imported module, or triggers a skip

    Example:
        flask = require("flask", "Flask needed for API endpoint tests")
        client = flask.Flask(__name__)
    """
    skip_reason = reason or f"Optional dependency '{module_name}' not installed"
    return pytest.importorskip(module_name, reason=skip_reason)


OPTIONAL_DEPS = {
    "flask": "Flask web framework — needed for API server tests",
    "fastapi": "FastAPI framework — needed for REST API tests",
    "websockets": "websockets library — needed for WS transport tests",
    "tiktoken": "tiktoken — needed for smart compression tests",
    "pydantic": "pydantic — needed for schema validation tests",
    "aiohttp": "aiohttp — needed for async HTTP client tests",
    "httpx": "httpx — needed for async HTTP tests",
    "celery": "celery — needed for task queue tests",
    "redis": "redis — needed for cache tests",
    "docker": "docker — needed for container tests",
}


def require_batch(*module_names: str) -> dict:
    """Import multiple optional dependencies at once.

    Args:
        *module_names: Module names to import

    Returns:
        Dict mapping module_name -> module or None (if skipped)

    Example:
        deps = require_batch("flask", "fastapi")
        flask = deps["flask"]
        fastapi = deps["fastapi"]
    """
    result = {}
    for name in module_names:
        reason = OPTIONAL_DEPS.get(name, f"Optional dependency '{name}' not installed")
        result[name] = require(name, reason)
    return result
