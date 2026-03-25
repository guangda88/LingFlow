"""
LingFlow Modern Testing Framework
基于 Chrome DevTools MCP 项目的设计理念
"""

from .scenario import (
    CodeTestScenario,
    CapturedToolCall,
    TestInteractionType,
    REFACTORING_SCENARIO,
    DETECT_SECURITY_ISSUE,
    OPTIMIZATION_SCENARIO,
    create_custom_scenario
)
from .test_server import CodeTestServer
from .tool_definition import (
    ToolDefinition,
    BaseTool,
    ToolCategory,
    ToolAnnotation,
    ToolRequest,
    ToolResponse,
    TestContext,
    ToolMetadata,
    RunTestTool,
    AnalyzeCodeTool,
    create_tool_registry
)
from .snapshot import SnapshotTest, SnapshotMetadata
from .ai_runner import (
    AIScenarioRunner,
    ScenarioResult,
    ScenarioStatus
)
from .mcp_server import (
    MCPTestServer,
    MCPTool,
    MCPServerStatus
)

__all__ = [
    # Scenario
    'CodeTestScenario',
    'CapturedToolCall',
    'TestInteractionType',
    'REFACTORING_SCENARIO',
    'DETECT_SECURITY_ISSUE',
    'OPTIMIZATION_SCENARIO',
    'create_custom_scenario',
    # Test Server
    'CodeTestServer',
    # Tool Definition
    'ToolDefinition',
    'BaseTool',
    'ToolCategory',
    'ToolAnnotation',
    'ToolRequest',
    'ToolResponse',
    'TestContext',
    'ToolMetadata',
    'RunTestTool',
    'AnalyzeCodeTool',
    'create_tool_registry',
    # Snapshot
    'SnapshotTest',
    'SnapshotMetadata',
    # AI Runner
    'AIScenarioRunner',
    'ScenarioResult',
    'ScenarioStatus',
    # MCP Server
    'MCPTestServer',
    'MCPTool',
    'MCPServerStatus',
]

__version__ = '1.0.0'
