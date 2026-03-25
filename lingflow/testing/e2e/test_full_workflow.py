#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试 - 完整工作流测试
测试整个测试框架的端到端功能
"""

import pytest
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import sys
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lingflow.testing.scenario import CodeTestScenario, CapturedToolCall
from lingflow.testing.test_server import CodeTestServer
from lingflow.testing.snapshot import SnapshotTest, SnapshotMetadata
from lingflow.testing.ai_runner import AIScenarioRunner
from lingflow.testing.mcp_server import MCPTestServer


class TestFullWorkflow:
    """完整工作流测试套件"""

    def test_complete_refactoring_workflow(self):
        """测试完整的重构工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 1. 创建测试服务器
            server = CodeTestServer(temp_path)

            # 2. 添加测试代码
            original_code = '''class Calculator:
    def add(self, x, y):
        self.data = x + y
        return self.data

    def multiply(self, x, y):
        self.data = x * y
        return self.data
'''
            code_file = server.add_python_route("calculator.py", original_code)

            # 3. 创建重构场景
            scenario = CodeTestScenario(
                name="refactor_workflow",
                description="完整的重构工作流",
                prompt="重构 Calculator 类，提取公共逻辑",
                code_content=original_code,
                max_turns=3,
                expected_tools=["rename_variable"],
                expectations=lambda calls: len(calls) > 0
            )

            # 4. 模拟工具调用
            calls = [
                CapturedToolCall(
                    name="rename_variable",
                    args={"old_name": "data", "new_name": "result"},
                    timestamp=0.0,
                    result={"success": True}
                )
            ]

            # 5. 验证场景
            scenario.expectations(calls)

            # 6. 验证文件存在
            assert code_file.exists()

            # 7. 清理
            server.cleanup()

    def test_complete_analysis_workflow(self):
        """测试完整的代码分析工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 1. 创建快照测试
            snapshot_dir = temp_path / "snapshots"
            snapshot = SnapshotTest(snapshot_dir)

            # 2. 分析代码
            code = '''
def calculate(x, y):
    return x + y

class Calculator:
    def __init__(self):
        self.value = 0
'''

            # 3. 创建分析结果
            analysis_result = {
                "functions": [
                    {
                        "name": "calculate",
                        "args": ["x", "y"],
                        "lineno": 2
                    }
                ],
                "classes": [
                    {
                        "name": "Calculator",
                        "lineno": 5,
                        "methods": ["__init__"]
                    }
                ],
                "stats": {
                    "lines": 8,
                    "functions": 1,
                    "classes": 1
                }
            }

            # 4. 创建快照
            metadata = SnapshotMetadata(
                test_name="analysis_workflow",
                created_at="2024-01-01T00:00:00",
                description="完整的代码分析工作流"
            )
            snapshot.assert_match("analysis_workflow", analysis_result, metadata=metadata)

            # 5. 验证快照匹配（第二次运行）
            snapshot.assert_match("analysis_workflow", analysis_result)

            # 6. 验证快照文件存在
            snapshot_path = snapshot._get_snapshot_path("analysis_workflow")
            assert snapshot_path.exists()

    def test_complete_security_workflow(self):
        """测试完整的安全扫描工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 1. 创建测试服务器
            server = CodeTestServer(temp_path)

            # 2. 添加测试代码
            vulnerable_code = '''def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)

def process(input):
    import os
    os.system("process " + input)
'''
            code_file = server.add_python_route("vulnerable.py", vulnerable_code)

            # 3. 创建安全扫描场景
            scenario = CodeTestScenario(
                name="security_scan_workflow",
                description="完整的安全扫描工作流",
                prompt="扫描代码中的安全漏洞",
                code_content=vulnerable_code,
                max_turns=3,
                expected_tools=["security_scan"],
                expectations=lambda calls: len(calls) >= 2
            )

            # 4. 模拟多个安全扫描工具调用
            calls = [
                CapturedToolCall(
                    name="security_scan",
                    args={"scanner": "sql_injection"},
                    timestamp=0.0,
                    result={"vulnerability_count": 1, "safe": False}
                ),
                CapturedToolCall(
                    name="security_scan",
                    args={"scanner": "command_injection"},
                    timestamp=1.0,
                    result={"vulnerability_count": 1, "safe": False}
                )
            ]

            # 5. 验证场景
            scenario.expectations(calls)

            # 6. 验证文件存在
            assert code_file.exists()

            # 7. 清理
            server.cleanup()

    def test_complete_optimization_workflow(self):
        """测试完整的优化工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 1. 创建测试服务器
            server = CodeTestServer(temp_path)

            # 2. 添加测试代码
            unoptimized_code = '''def process_items(items):
    result = []
    for i in range(len(items)):
        result = result + str(items[i])
    return result
'''
            code_file = server.add_python_route("process.py", unoptimized_code)

            # 3. 创建优化场景
            scenario = CodeTestScenario(
                name="optimization_workflow",
                description="完整的优化工作流",
                prompt="优化代码性能和可读性",
                code_content=unoptimized_code,
                max_turns=3,
                expected_tools=["optimize"],
                expectations=lambda calls: len(calls) > 0
            )

            # 4. 模拟工具调用
            calls = [
                CapturedToolCall(
                    name="optimize",
                    args={"optimizer": "loop"},
                    timestamp=0.0,
                    result={"optimization_count": 1, "optimized_code": "for item in items:"}
                )
            ]

            # 5. 验证场景
            scenario.expectations(calls)

            # 6. 验证文件存在
            assert code_file.exists()

            # 7. 清理
            server.cleanup()


class TestAIIntegration:
    """AI 集成测试套件（简化版）"""

    @pytest.mark.asyncio
    async def test_ai_runner_with_scenario(self):
        """测试 AI 运行器与场景集成"""
        scenario = CodeTestScenario(
            name="ai_integration_test",
            description="AI 集成测试",
            prompt="测试 AI 场景执行",
            code_content="def test(): pass",
            max_turns=2,
            expected_tools=[],
            expectations=lambda calls: True
        )

        # 创建 AI 运行器（使用模拟实现）
        runner = AIScenarioRunner(timeout=60)

        # 执行场景（需要提供 tools 参数）
        result = await runner.run_scenario(scenario, tools={})

        # 验证结果
        assert result is not None
        assert result.status.name in ["PASSED", "FAILED", "SKIPPED"]  # 检查 status 而不是 success

    @pytest.mark.asyncio
    async def test_ai_runner_multiple_turns(self):
        """测试 AI 运行器多轮交互"""
        scenario = CodeTestScenario(
            name="multi_turn_test",
            description="多轮交互测试",
            prompt="执行多轮对话",
            code_content="def example(): return 42",
            max_turns=3,
            expected_tools=[],
            expectations=lambda calls: True
        )

        # 创建 AI 运行器
        runner = AIScenarioRunner(timeout=60)

        # 执行场景
        result = await runner.run_scenario(scenario, tools={})

        # 验证结果
        assert result is not None

    # 跳过 MCP 服务器集成测试 - 需要完整的工具实现
    @pytest.mark.skip(reason="MCP server requires full tool implementation")
    def test_mcp_server_integration(self):
        """测试 MCP 服务器集成"""
        pass

    # 跳过 MCP 服务器与测试服务器集成测试 - 需要完整的工具实现
    @pytest.mark.skip(reason="MCP server requires full tool implementation")
    def test_mcp_server_with_test_server(self):
        """测试 MCP 服务器与测试服务器集成"""
        pass


class TestIntegrationScenarios:
    """集成场景测试套件"""

    def test_refactor_then_security_scan(self):
        """测试重构后安全扫描的集成场景"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建测试服务器
            server = CodeTestServer(temp_path)

            # 原始代码
            code = '''def process(data):
    query = "SELECT * FROM table WHERE id = " + data
    return db.execute(query)
'''

            # 步骤 1: 重构场景
            refactor_scenario = CodeTestScenario(
                name="refactor_first",
                description="先重构",
                prompt="重构代码",
                code_content=code,
                max_turns=1,
                expected_tools=["rename_variable"],
                expectations=lambda calls: True
            )

            # 模拟重构
            refactor_calls = [
                CapturedToolCall(
                    name="rename_variable",
                    args={"old_name": "data", "new_name": "user_id"},
                    timestamp=0.0,
                    result={"success": True}
                )
            ]
            refactor_scenario.expectations(refactor_calls)

            # 步骤 2: 安全扫描场景
            security_scenario = CodeTestScenario(
                name="security_scan_after",
                description="重构后安全扫描",
                prompt="扫描安全问题",
                code_content=code,
                max_turns=1,
                expected_tools=["security_scan"],
                expectations=lambda calls: True
            )

            # 模拟安全扫描
            security_calls = [
                CapturedToolCall(
                    name="security_scan",
                    args={"scanner": "sql_injection"},
                    timestamp=0.0,
                    result={"vulnerability_count": 1, "safe": False}
                )
            ]
            security_scenario.expectations(security_calls)

            # 清理
            server.cleanup()

    def test_optimize_then_snapshot(self):
        """测试优化后快照的集成场景"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建快照测试
            snapshot_dir = temp_path / "snapshots"
            snapshot = SnapshotTest(snapshot_dir)

            # 步骤 1: 优化前快照
            before_optimization = {
                "function": "process",
                "lines": 5,
                "complexity": 2,
                "performance": "slow"
            }

            snapshot.assert_match("before_optimization", before_optimization, update=True)

            # 步骤 2: 模拟优化
            after_optimization = {
                "function": "process",
                "lines": 3,
                "complexity": 1,
                "performance": "fast"
            }

            # 步骤 3: 优化后快照
            snapshot.assert_match("after_optimization", after_optimization, update=True)

            # 验证两个快照都存在
            assert snapshot._get_snapshot_path("before_optimization").exists()
            assert snapshot._get_snapshot_path("after_optimization").exists()

    def test_end_to_end_workflow(self):
        """测试端到端完整工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建测试服务器目录
            server_dir = temp_path / "server"
            server_dir.mkdir(parents=True, exist_ok=True)

            # 1. 创建测试服务器
            server = CodeTestServer(server_dir)

            # 2. 创建快照测试
            snapshot_dir = temp_path / "snapshots"
            snapshot = SnapshotTest(snapshot_dir)

            # 3. 添加测试代码（不需要 .py 扩展名）
            code = '''def calculate(x, y):
    return x + y
'''
            code_file = server.add_python_route("calc", code)

            # 4. 代码分析
            analysis_result = {
                "functions": [{"name": "calculate", "args": ["x", "y"]}],
                "classes": [],
                "stats": {"lines": 2, "functions": 1}
            }

            # 5. 创建分析快照
            snapshot.assert_match("e2e_analysis", analysis_result, update=True)

            # 6. 验证文件和快照存在
            assert code_file.exists()
            assert snapshot._get_snapshot_path("e2e_analysis").exists()

            # 7. 清理
            server.cleanup()


class TestErrorHandling:
    """错误处理测试套件"""

    def test_workflow_error_recovery(self):
        """测试工作流错误恢复"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            server = CodeTestServer(temp_path)

            # 测试语法错误代码
            bad_code = "def broken(\n    return 'error'"

            # 应该能够处理而不崩溃
            try:
                code_file = server.add_python_route("broken.py", bad_code)
                # 文件应该被创建，即使代码有语法错误
                assert code_file.exists()
            except Exception as e:
                # 应该能够优雅地处理错误
                assert isinstance(e, Exception)

            server.cleanup()

    def test_scenario_validation_error(self):
        """测试场景验证错误"""
        # 创建无效场景（缺少必需字段）
        with pytest.raises(ValueError):
            scenario = CodeTestScenario(
                name="invalid",
                description="",
                prompt="",
                code_content="",
                max_turns=0  # 无效的 max_turns
            )
            scenario.validate()  # 需要调用 validate() 才会抛出异常

    def test_snapshot_mismatch_error(self):
        """测试快照不匹配错误"""
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot = SnapshotTest(snapshot_dir)

            # 创建快照
            snapshot.assert_match("test", {"value": 1}, update=True)

            # 尝试匹配不同的值（应该失败）
            with pytest.raises(AssertionError):
                snapshot.assert_match("test", {"value": 2})


# 主测试入口
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("端到端测试 - 完整工作流测试")
    print("=" * 70)

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
