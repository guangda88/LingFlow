"""
LingFlow Testing Framework

简化的测试框架，移除过度抽象。
"""

from .scenario import (
    DETECT_SECURITY_ISSUE,
    OPTIMIZATION_SCENARIO,
    REFACTORING_SCENARIO,
    CapturedToolCall,
    CodeTestScenario,
    TestInteractionType,
    create_custom_scenario,
)
from .snapshot import SnapshotMetadata, SnapshotTest
from .test_server import CodeTestServer
from .tool_definition import TestContext, ToolCategory, ToolDefinition, ToolRequest, ToolResponse, create_tool_registry

__all__ = [
    # Scenario
    "CodeTestScenario",
    "CapturedToolCall",
    "TestInteractionType",
    "REFACTORING_SCENARIO",
    "DETECT_SECURITY_ISSUE",
    "OPTIMIZATION_SCENARIO",
    "create_custom_scenario",
    # Test Server
    "CodeTestServer",
    # Tool Definition
    "ToolDefinition",
    "ToolCategory",
    "ToolRequest",
    "ToolResponse",
    "TestContext",
    "create_tool_registry",
    # Snapshot
    "SnapshotTest",
    "SnapshotMetadata",
]

__version__ = "2.0.0"  # 简化版本
