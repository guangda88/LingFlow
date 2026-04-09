"""LingFlow E2E 测试模块

提供端到端测试能力。

推荐: 直接使用 Chrome DevTools MCP 服务器，无需额外包装。

使用示例:
    # 在 Claude Code 中直接调用 MCP 工具
    # 无需 Python 代码
"""

# Carbonyl 已弃用 - 仅保留作为参考
from lingflow.testing.e2e.carbonyl_runner import (
    CarbonylRunner,
    CarbonylTestConfig,
    TestResult,
    get_carbonyl_runner,
    run_carbonyl_test,
)

# 简单的 MCP 客户端包装（可选）
from lingflow.testing.e2e.devtools_client import DevToolsClient, MCPResult, quick_test

__all__ = [
    "DevToolsClient",
    "MCPResult",
    "quick_test",
    # 已弃用
    "CarbonylRunner",
    "CarbonylTestConfig",
    "TestResult",
    "get_carbonyl_runner",
    "run_carbonyl_test",
]
