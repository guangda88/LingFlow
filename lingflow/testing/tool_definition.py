"""测试工具定义

简化版工具定义，移除过度抽象。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable
from enum import Enum


class ToolCategory(str, Enum):
    """工具类别"""

    ANALYSIS = "analysis"
    GENERATION = "generation"
    REFACTORING = "refactoring"
    TESTING = "testing"
    REVIEW = "review"


@dataclass
class ToolRequest:
    """工具请求"""

    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResponse:
    """工具响应"""

    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class TestContext:
    """测试上下文"""

    test_name: str
    test_id: str
    temp_dir: str
    start_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolDefinition:
    """工具定义

    简化版，移除过度抽象。
    """

    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory = ToolCategory.ANALYSIS,
        handler: Optional[Callable] = None,
    ):
        """初始化工具定义

        Args:
            name: 工具名称
            description: 工具描述
            category: 工具类别
            handler: 处理函数
        """
        self.name = name
        self.description = description
        self.category = category
        self._handler = handler

    def handle(self, request: ToolRequest, response: ToolResponse, context: TestContext) -> None:
        """处理工具调用

        Args:
            request: 工具请求
            response: 工具响应（会被修改）
            context: 测试上下文
        """
        if self._handler:
            self._handler(request, response, context)
        else:
            response.success = False
            response.error = f"未实现处理器: {self.name}"


def create_tool_registry() -> Dict[str, ToolDefinition]:
    """创建工具注册表

    Returns:
        工具字典
    """
    return {}
