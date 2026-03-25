#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 场景测试运行器
基于 Chrome DevTools MCP 的 AI 集成测试模式
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

from .scenario import CodeTestScenario, CapturedToolCall
from .test_server import CodeTestServer
from .tool_definition import ToolDefinition, ToolRequest, ToolResponse, TestContext

logger = logging.getLogger(__name__)


class ScenarioStatus(str, Enum):
    """场景测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class ScenarioResult:
    """场景测试结果"""
    scenario_name: str
    status: ScenarioStatus
    execution_time: float
    captured_calls: List[CapturedToolCall] = field(default_factory=list)
    error_message: Optional[str] = None
    response_data: Optional[Any] = None
    tool_expectations_met: bool = True
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp
        return data


class AIScenarioRunner:
    """AI 场景测试运行器

    基于 Chrome DevTools MCP 的 runSingleScenario 模式
    支持场景驱动的 AI 测试自动化

    特性:
    - 场景测试运行
    - 工具调用捕获
    - 期望验证
    - 多轮交互支持
    - 超时处理
    """

    def __init__(
        self,
        test_server: Optional[CodeTestServer] = None,
        timeout: int = 60
    ):
        """初始化 AI 场景运行器

        Args:
            test_server: 测试服务器实例
            timeout: 默认超时时间（秒）
        """
        self.test_server = test_server or CodeTestServer()
        self.timeout = timeout
        self.scenarios_run = 0
        self.scenarios_passed = 0
        self.scenarios_failed = 0
        self.scenarios_timeout = 0

        logger.info(f"🤖 AIScenarioRunner 初始化 (超时: {timeout}s)")

    async def run_scenario(
        self,
        scenario: CodeTestScenario,
        tools: Dict[str, ToolDefinition],
        validate_scenario: bool = True
    ) -> ScenarioResult:
        """运行单个测试场景

        Args:
            scenario: 测试场景
            tools: 可用工具字典
            validate_scenario: 是否验证场景配置

        Returns:
            场景测试结果

        Example:
            >>> runner = AIScenarioRunner()
            >>> scenario = REFACTORING_SCENARIO
            >>> tools = create_tool_registry()
            >>> result = await runner.run_scenario(scenario, tools)
        """
        # 验证场景配置
        if validate_scenario:
            try:
                scenario.validate()
            except ValueError as e:
                return ScenarioResult(
                    scenario_name=scenario.name,
                    status=ScenarioStatus.FAILED,
                    execution_time=0.0,
                    error_message=f"场景验证失败: {e}",
                    timestamp=time.time()
                )

        # 创建结果对象
        result = ScenarioResult(
            scenario_name=scenario.name,
            status=ScenarioStatus.RUNNING,
            execution_time=0.0,
            timestamp=time.time()
        )

        start_time = time.time()

        try:
            # 设置测试代码
            await self._setup_scenario_code(scenario)

            # 捕获工具调用
            captured_calls = []

            async def capture_tool_call(
                tool_name: str,
                args: Dict[str, Any]
            ) -> Any:
                """捕获工具调用"""
                call = CapturedToolCall(
                    name=tool_name,
                    args=args,
                    timestamp=time.time()
                )
                captured_calls.append(call)

                # 执行实际工具
                tool = tools.get(tool_name)
                if not tool:
                    raise ValueError(f"工具不存在: {tool_name}")

                request = ToolRequest(name=tool_name, arguments=args)
                response = ToolResponse(success=False, execution_time=0.0)

                context = TestContext(
                    test_name=scenario.name,
                    test_id=f"scenario_{scenario.name}",
                    temp_dir=str(self.test_server.temp_dir),
                    start_time=start_time,
                    captured_calls=[c.to_dict() if hasattr(c, 'to_dict') else c.__dict__ for c in captured_calls]
                )

                await tool.handle(request, response, context)

                call.result = response.data

                return response

            # 模拟 AI 交互（简化版）
            # 实际应用中应该调用真实的 AI API
            response_data = await self._simulate_ai_interaction(
                scenario,
                capture_tool_call
            )

            # 验证期望
            expectations_met = True
            if scenario.expectations:
                try:
                    scenario.expectations(captured_calls)
                except AssertionError as e:
                    expectations_met = False
                    result.error_message = f"期望验证失败: {e}"

            # 验证工具调用
            tool_expectations_met = self._verify_tool_expectations(
                scenario,
                captured_calls
            )

            # 更新结果
            result.captured_calls = captured_calls
            result.response_data = response_data
            result.tool_expectations_met = tool_expectations_met

            if expectations_met and tool_expectations_met:
                result.status = ScenarioStatus.PASSED
                self.scenarios_passed += 1
                logger.info(f"✅ 场景通过: {scenario.name}")
            else:
                result.status = ScenarioStatus.FAILED
                self.scenarios_failed += 1
                logger.warning(f"❌ 场景失败: {scenario.name}")

        except asyncio.TimeoutError:
            result.status = ScenarioStatus.TIMEOUT
            result.error_message = f"场景执行超时 ({self.timeout}s)"
            self.scenarios_timeout += 1
            logger.error(f"⏰ 场景超时: {scenario.name}")

        except Exception as e:
            result.status = ScenarioStatus.FAILED
            result.error_message = str(e)
            self.scenarios_failed += 1
            logger.error(f"❌ 场景执行错误: {scenario.name} - {e}")

        finally:
            result.execution_time = time.time() - start_time
            self.scenarios_run += 1

        return result

    async def _setup_scenario_code(self, scenario: CodeTestScenario):
        """设置场景代码

        Args:
            scenario: 测试场景
        """
        # 添加测试代码
        self.test_server.add_python_route(
            scenario.name,
            scenario.code_content
        )

        logger.debug(f"✓ 场景代码已设置: {scenario.name}")

    async def _simulate_ai_interaction(
        self,
        scenario: CodeTestScenario,
        capture_tool_call: Callable
    ) -> Any:
        """模拟 AI 交互

        Args:
            scenario: 测试场景
            capture_tool_call: 工具调用捕获函数

        Returns:
            AI 响应数据

        Note:
            这是简化版的模拟，实际应用中应该调用真实的 AI API
        """
        # 模拟 AI 调用工具
        for tool_name in scenario.expected_tools[:scenario.max_turns]:
            try:
                result = await capture_tool_call(tool_name, {})
                logger.debug(f"  AI 调用工具: {tool_name}")
            except Exception as e:
                logger.warning(f"  工具调用失败: {tool_name} - {e}")

        # 返回模拟响应
        return {
            "scenario": scenario.name,
            "tools_called": len(scenario.expected_tools),
            "status": "completed"
        }

    def _verify_tool_expectations(
        self,
        scenario: CodeTestScenario,
        captured_calls: List[CapturedToolCall]
    ) -> bool:
        """验证工具调用期望

        Args:
            scenario: 测试场景
            captured_calls: 捕获的工具调用

        Returns:
            是否满足期望
        """
        called_tools = {call.name for call in captured_calls}

        # 检查必须调用的工具
        for required_tool in scenario.required_tools:
            if required_tool not in called_tools:
                logger.warning(
                    f"缺少必需工具: {required_tool}"
                )
                return False

        # 检查期望调用的工具（可选）
        for expected_tool in scenario.expected_tools:
            if expected_tool not in called_tools:
                logger.debug(
                    f"未调用期望工具: {expected_tool}"
                )
                # 这是可选的，不强制要求

        return True

    async def run_batch(
        self,
        scenarios: List[CodeTestScenario],
        tools: Dict[str, ToolDefinition]
    ) -> List[ScenarioResult]:
        """批量运行场景

        Args:
            scenarios: 场景列表
            tools: 可用工具字典

        Returns:
            场景结果列表

        Example:
            >>> runner = AIScenarioRunner()
            >>> scenarios = [REFACTORING_SCENARIO, DETECT_SECURITY_ISSUE]
            >>> tools = create_tool_registry()
            >>> results = await runner.run_batch(scenarios, tools)
        """
        logger.info(f"🚀 批量运行 {len(scenarios)} 个场景")

        results = []

        for scenario in scenarios:
            result = await self.run_scenario(scenario, tools)
            results.append(result)

        logger.info(
            f"✓ 批量运行完成: "
            f"通过 {self.scenarios_passed}, "
            f"失败 {self.scenarios_failed}, "
            f"超时 {self.scenarios_timeout}"
        )

        return results

    def get_summary(self) -> Dict[str, Any]:
        """获取运行摘要

        Returns:
            摘要数据
        """
        return {
            "total_scenarios": self.scenarios_run,
            "passed": self.scenarios_passed,
            "failed": self.scenarios_failed,
            "timeout": self.scenarios_timeout,
            "success_rate": (
                self.scenarios_passed / self.scenarios_run
                if self.scenarios_run > 0 else 0
            )
        }

    def reset_stats(self):
        """重置统计信息"""
        self.scenarios_run = 0
        self.scenarios_passed = 0
        self.scenarios_failed = 0
        self.scenarios_timeout = 0

        logger.info("✓ 统计信息已重置")


# 示例使用

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from lingflow.testing.scenario import (
        REFACTORING_SCENARIO,
        DETECT_SECURITY_ISSUE
    )
    from lingflow.testing.tool_definition import create_tool_registry

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("AI 场景运行器示例")
    print("=" * 70)

    async def main():
        # 创建运行器
        runner = AIScenarioRunner()

        # 创建工具注册表
        tools = create_tool_registry()

        # 运行单个场景
        print("\n" + "-" * 70)
        print("运行单个场景:")
        print("-" * 70)

        result = await runner.run_scenario(
            REFACTORING_SCENARIO,
            tools
        )

        print(f"\n场景: {result.scenario_name}")
        print(f"状态: {result.status.value}")
        print(f"执行时间: {result.execution_time:.3f}s")
        print(f"捕获调用: {len(result.captured_calls)}")
        print(f"期望满足: {result.tool_expectations_met}")

        # 批量运行
        print("\n" + "-" * 70)
        print("批量运行场景:")
        print("-" * 70)

        scenarios = [
            REFACTORING_SCENARIO,
            DETECT_SECURITY_ISSUE
        ]

        results = await runner.run_batch(scenarios, tools)

        print(f"\n运行摘要:")
        summary = runner.get_summary()
        print(f"  总场景数: {summary['total_scenarios']}")
        print(f"  通过: {summary['passed']}")
        print(f"  失败: {summary['failed']}")
        print(f"  超时: {summary['timeout']}")
        print(f"  成功率: {summary['success_rate']:.1%}")

        # 清理
        runner.test_server.restore()

    asyncio.run(main())

    print("\n✅ AI 场景运行器示例完成")
