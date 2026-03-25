#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具定义的严格类型系统
基于 Chrome DevTools MCP 的 Zod 验证模式
"""

from typing import Protocol, TypedDict, Any, Optional, List, Dict
from enum import Enum
from dataclasses import dataclass, field
from abc import abstractmethod
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """工具类别

    参考 Chrome DevTools MCP 的工具分类
    """
    ANALYSIS = "analysis"         # 分析类工具
    GENERATION = "generation"     # 代码生成工具
    REFACTORING = "refactoring"   # 重构工具
    TESTING = "testing"           # 测试工具
    REVIEW = "review"             # 审查工具
    DEBUGGING = "debugging"       # 调试工具
    OPTIMIZATION = "optimization" # 优化工具
    AUTOMATION = "automation"     # 自动化工具


class ToolAnnotation(TypedDict):
    """工具注解

    包含工具的元数据和配置信息
    """
    title: str                  # 工具标题
    category: ToolCategory       # 工具类别
    read_only: bool             # 是否为只读工具（不修改系统状态）
    modifies_code: bool         # 是否修改代码
    requires_isolation: bool    # 是否需要隔离环境
    destructive: bool          # 是否为破坏性操作（无法回滚）


@dataclass
class ToolMetadata:
    """工具元数据"""
    version: str = "1.0.0"
    author: str = "LingFlow Team"
    created_at: str = ""
    updated_at: str = ""
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


class ToolRequest(BaseModel):
    """工具请求模型

    使用 Pydantic 进行自动验证
    """
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    context: Optional[Dict[str, Any]] = Field(default=None, description="额外上下文")

    @validator('name')
    def name_must_be_non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('工具名称不能为空')
        return v.lower().replace('-', '_')


class ToolResponse(BaseModel):
    """工具响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Any] = Field(default=None, description="返回数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    execution_time: float = Field(..., description="执行时间（秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"result": "test passed"},
                "error": None,
                "execution_time": 0.123
            }
        }


class TestContext(BaseModel):
    """测试上下文

    包含测试执行的环境信息
    """
    test_name: str
    test_id: str
    temp_dir: str
    start_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    captured_calls: List[Dict[str, Any]] = Field(default_factory=list)


class ToolDefinition(Protocol):
    """代码测试工具定义协议

    参考 Chrome DevTools MCP 的工具定义模式
    所有测试工具必须实现此协议
    """
    # 基础属性
    name: str
    description: str
    annotations: ToolAnnotation

    # 可选属性
    metadata: Optional[ToolMetadata]

    # 抽象方法
    @abstractmethod
    async def handle(
        self,
        request: ToolRequest,
        response: ToolResponse,
        context: TestContext
    ) -> None:
        """处理工具调用

        Args:
            request: 工具请求
            response: 工具响应（将被填充）
            context: 测试上下文
        """
        ...

    @abstractmethod
    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """验证工具参数

        Args:
            arguments: 参数字典

        Returns:
            是否有效
        """
        ...


class BaseTool(ToolDefinition):
    """工具基类

    提供工具的基本实现
    """

    def __init__(
        self,
        name: str,
        description: str,
        annotations: ToolAnnotation,
        metadata: Optional[ToolMetadata] = None
    ):
        """初始化工具

        Args:
            name: 工具名称
            description: 工具描述
            annotations: 工具注解
            metadata: 工具元数据
        """
        self.name = name
        self.description = description
        self.annotations = annotations
        self.metadata = metadata

        logger.debug(f"✓ 工具注册: {name}")

    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """验证工具参数（默认实现）

        子类可以重写此方法提供更严格的验证
        """
        try:
            # 基本验证：参数必须是字典
            if not isinstance(arguments, dict):
                logger.warning(f"参数必须是字典: {type(arguments)}")
                return False

            # 检查是否需要特定参数
            if hasattr(self, 'required_params'):
                for param in self.required_params:
                    if param not in arguments:
                        logger.warning(f"缺少必需参数: {param}")
                        return False

            return True
        except Exception as e:
            logger.error(f"参数验证失败: {e}")
            return False

    async def handle(
        self,
        request: ToolRequest,
        response: ToolResponse,
        context: TestContext
    ) -> None:
        """处理工具调用（默认实现）

        子类必须重写此方法
        """
        raise NotImplementedError(
            f"工具 {self.name} 必须实现 handle 方法"
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            工具信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "annotations": self.annotations,
            "metadata": self.metadata.to_dict() if self.metadata else None
        }


# 预定义工具示例

class RunTestTool(BaseTool):
    """运行测试工具

    示例工具实现
    """

    required_params = ["test_name"]

    def __init__(self):
        super().__init__(
            name="run_test",
            description="运行单个测试用例",
            annotations={
                "title": "运行测试",
                "category": ToolCategory.TESTING,
                "read_only": True,
                "modifies_code": False,
                "requires_isolation": True,
                "destructive": False
            },
            metadata=ToolMetadata(
                version="1.0.0",
                author="LingFlow Team",
                tags=["testing", "execution"],
                examples=[
                    "run_test test_calculator",
                    "run_test --test_name test_foo"
                ]
            )
        )

    async def handle(
        self,
        request: ToolRequest,
        response: ToolResponse,
        context: TestContext
    ) -> None:
        """处理运行测试请求"""
        import subprocess
        import time

        test_name = request.arguments.get("test_name")
        start_time = time.time()

        try:
            # 模拟运行测试
            logger.info(f"运行测试: {test_name}")

            # 这里应该是实际的测试执行逻辑
            # result = subprocess.run(...)

            response.success = True
            response.data = {
                "test_name": test_name,
                "status": "passed",
                "duration": 0.1
            }

        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            response.success = False
            response.error = str(e)

        response.execution_time = time.time() - start_time


class AnalyzeCodeTool(BaseTool):
    """代码分析工具

    示例工具实现
    """

    required_params = ["code"]

    def __init__(self):
        super().__init__(
            name="analyze_code",
            description="分析代码质量和复杂度",
            annotations={
                "title": "代码分析",
                "category": ToolCategory.ANALYSIS,
                "read_only": True,
                "modifies_code": False,
                "requires_isolation": False,
                "destructive": False
            },
            metadata=ToolMetadata(
                version="1.0.0",
                author="LingFlow Team",
                tags=["analysis", "quality"],
                examples=[
                    "analyze_code 'def foo(): pass'",
                    "analyze_code --code 'x = 1'"
                ]
            )
        )

    async def handle(
        self,
        request: ToolRequest,
        response: ToolResponse,
        context: TestContext
    ) -> None:
        """处理代码分析请求"""
        import time
        import ast

        code = request.arguments.get("code", "")
        start_time = time.time()

        try:
            # 简单的代码分析
            tree = ast.parse(code)

            # 计算复杂度（简化版）
            complexity = sum(
                1 for node in ast.walk(tree)
                if isinstance(node, (ast.If, ast.For, ast.While))
            )

            response.success = True
            response.data = {
                "complexity": complexity,
                "lines": len(code.split('\n')),
                "functions": len([
                    node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                ])
            }

        except Exception as e:
            logger.error(f"代码分析失败: {e}")
            response.success = False
            response.error = str(e)

        response.execution_time = time.time() - start_time


def create_tool_registry() -> Dict[str, BaseTool]:
    """创建工具注册表

    Returns:
        工具名称到工具实例的映射
    """
    return {
        "run_test": RunTestTool(),
        "analyze_code": AnalyzeCodeTool(),
        # 可以添加更多工具...
    }


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("工具定义系统示例")
    print("=" * 70)

    # 创建工具注册表
    registry = create_tool_registry()
    print(f"\n✓ 已注册 {len(registry)} 个工具:")
    for name, tool in registry.items():
        print(f"  - {name}: {tool.description}")

    # 测试工具
    print("\n" + "-" * 70)
    print("测试工具执行:")
    print("-" * 70)

    async def test_tool_execution():
        # 创建测试上下文
        context = TestContext(
            test_name="test_example",
            test_id="test_001",
            temp_dir="/tmp/test",
            start_time=0.0
        )

        # 测试运行测试工具
        print("\n1. 测试 run_test 工具:")
        run_test = registry["run_test"]
        request = ToolRequest(
            name="run_test",
            arguments={"test_name": "test_calculator"}
        )
        response = ToolResponse(success=False, execution_time=0.0)

        await run_test.handle(request, response, context)

        print(f"  成功: {response.success}")
        print(f"  数据: {response.data}")
        print(f"  执行时间: {response.execution_time:.3f}s")

        # 测试代码分析工具
        print("\n2. 测试 analyze_code 工具:")
        analyze_code = registry["analyze_code"]
        request = ToolRequest(
            name="analyze_code",
            arguments={
                "code": """
def foo(x, y):
    if x > 0:
        for i in range(y):
            print(i)
    return x + y
"""
            }
        )
        response = ToolResponse(success=False, execution_time=0.0)

        await analyze_code.handle(request, response, context)

        print(f"  成功: {response.success}")
        print(f"  数据: {response.data}")
        print(f"  执行时间: {response.execution_time:.3f}s")

    asyncio.run(test_tool_execution())

    print("\n✅ 工具系统测试完成")
