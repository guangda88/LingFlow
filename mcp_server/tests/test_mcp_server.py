"""LingFlow MCP Server 测试

测试 MCP 服务器的各项功能
"""

import pytest
import asyncio
from pathlib import Path


@pytest.fixture
def server():
    """创建服务器实例"""
    from lingflow_mcp import create_server

    return create_server()


class TestToolRegistry:
    """测试工具注册表"""

    def test_list_tools(self, server):
        """测试列出所有工具"""
        tools = server.tool_registry.get_mcp_tools()

        # 验证工具数量
        assert len(tools) > 0

        # 验证工具结构
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    def test_skill_tools_registered(self, server):
        """测试技能工具已注册"""
        tool_names = [t.name for t in server.tool_registry.get_mcp_tools()]

        assert "list_skills" in tool_names
        assert "run_skill" in tool_names

    def test_intelligence_tools_registered(self, server):
        """测试情报工具已注册"""
        tool_names = [t.name for t in server.tool_registry.get_mcp_tools()]

        assert "get_github_trends" in tool_names
        assert "get_npm_trends" in tool_names

    def test_code_review_tools_registered(self, server):
        """测试代码审查工具已注册"""
        tool_names = [t.name for t in server.tool_registry.get_mcp_tools()]

        assert "review_code" in tool_names


class TestSkillExecution:
    """测试技能执行"""

    @pytest.mark.asyncio
    async def test_list_skills(self, server):
        """测试列出技能"""
        result = await server._execute_tool("list_skills", {})

        assert result["success"] is True
        assert "skills" in result
        assert isinstance(result["skills"], list)

    @pytest.mark.asyncio
    async def test_list_skills_with_filter(self, server):
        """测试过滤技能"""
        result = await server._execute_tool(
            "list_skills",
            {"layer": "L1"}
        )

        assert result["success"] is True
        # 验证只返回 L1 技能（如果有）


class TestCodeReview:
    """测试代码审查"""

    @pytest.mark.asyncio
    async def test_review_code(self, server, tmp_path):
        """测试代码审查"""
        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def hello():
    print("Hello, World!")
""")

        # 执行审查
        result = await server._execute_tool(
            "review_code",
            {"target_path": str(test_file)}
        )

        assert result["success"] is True
        assert "report" in result


class TestAsyncTasks:
    """测试异步任务"""

    @pytest.mark.asyncio
    async def test_async_task_creation(self, server):
        """测试异步任务创建"""
        # 创建异步任务（工作流）
        result = await server._execute_tool(
            "run_workflow",
            {
                "workflow_id": "test_workflow",
                "params": {}
            }
        )

        # 验证返回了 task_id
        assert "task_id" in result
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_task_status_query(self, server):
        """测试任务状态查询"""
        # 创建任务
        task_result = await server._execute_tool(
            "run_workflow",
            {"workflow_id": "test_workflow"}
        )

        task_id = task_result["task_id"]

        # 查询状态
        status = await server._execute_tool(
            "get_task_status",
            {"task_id": task_id}
        )

        assert "task_id" in status
        assert "status" in status


class TestMCPIntegration:
    """测试 MCP 集成"""

    def test_server_initialization(self):
        """测试服务器初始化"""
        from lingflow_mcp import create_server

        server = create_server()

        assert server is not None
        assert server.server is not None

    def test_config_loading(self):
        """测试配置加载"""
        from lingflow_mcp.config import ServerConfig

        config = ServerConfig.from_env()

        assert config is not None
        assert config.work_dir is not None


@pytest.mark.integration
class TestRealExecution:
    """集成测试：真实执行（需要完整 LingFlow 环境）"""

    @pytest.mark.asyncio
    async def test_full_skill_execution(self, server):
        """测试完整的技能执行流程"""
        # 列出技能
        skills = await server._execute_tool("list_skills", {})

        if skills["success"] and len(skills["skills"]) > 0:
            # 执行第一个技能
            first_skill = skills["skills"][0]["name"]

            result = await server._execute_tool(
                "run_skill",
                {
                    "skill_name": first_skill,
                    "params": {}
                }
            )

            # 验证结果
            assert "success" in result
            assert "skill" in result


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
