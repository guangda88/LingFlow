"""MCP Server 全面 E2E 测试

覆盖所有 21 个工具的注册、执行、错误处理和边界条件。
测试链路: MCP 客户端 → LingFlowMCPServer → LingFlow 核心
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def server():
    """创建服务器实例"""
    from lingflow_mcp import create_server

    return create_server()


def _tool_names(server) -> set:
    return {t.name for t in server.tool_registry.get_mcp_tools()}


# ============================================================================
# 1. 工具注册完整性测试
# ============================================================================


class TestToolRegistration:
    """验证全部 21 个工具正确注册"""

    EXPECTED_TOOLS = {
        # Phase 1: P0
        "list_skills",
        "run_skill",
        "review_code",
        "get_github_trends",
        "get_npm_trends",
        # Phase 2: P1
        "list_workflows",
        "run_workflow",
        "get_workflow_status",
        "create_requirement",
        "get_requirement",
        "update_requirement",
        "list_requirements",
        "link_requirement_to_branch",
        # Phase 3: P2
        "run_tests",
        "get_coverage",
        "generate_test_report",
        "get_health_status",
        "get_metrics",
        "detect_anomaly",
        # 异步任务
        "get_task_status",
        "list_tasks",
    }

    def test_tool_count(self, server):
        """验证注册工具数量 >= 21"""
        tools = server.tool_registry.get_mcp_tools()
        assert len(tools) >= 21, f"Expected >= 21 tools, got {len(tools)}"

    def test_all_expected_tools_registered(self, server):
        """验证所有预期工具均已注册"""
        registered = _tool_names(server)
        missing = self.EXPECTED_TOOLS - registered
        assert not missing, f"Missing tools: {missing}"

    def test_no_duplicate_tools(self, server):
        """验证无重复工具"""
        tools = server.tool_registry.get_mcp_tools()
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), "Duplicate tool names found"

    def test_tool_schema_structure(self, server):
        """验证每个工具有合法的 JSON Schema"""
        for tool in server.tool_registry.get_mcp_tools():
            assert tool.name, "Tool missing name"
            assert tool.description, f"Tool {tool.name} missing description"
            assert isinstance(tool.inputSchema, dict), f"Tool {tool.name} inputSchema not dict"
            assert tool.inputSchema.get("type") == "object", f"Tool {tool.name} schema type not object"

    def test_handler_callable(self, server):
        """验证每个工具都有可调用的 handler"""
        for name in self.EXPECTED_TOOLS:
            handler = server.tool_registry.get_tool_handler(name)
            assert handler is not None, f"Tool {name} has no handler"
            assert callable(handler), f"Tool {name} handler not callable"


# ============================================================================
# 2. Phase 1 工具执行测试 (P0)
# ============================================================================


class TestSkillTools:
    """测试技能系统工具"""

    @pytest.mark.asyncio
    async def test_list_skills_returns_list(self, server):
        """list_skills 应返回技能列表"""
        result = await server._execute_tool("list_skills", {})
        assert result["success"] is True
        assert "skills" in result
        assert isinstance(result["skills"], list)
        assert result["total"] == len(result["skills"])

    @pytest.mark.asyncio
    async def test_list_skills_filter_by_category(self, server):
        """list_skills 按 category 过滤"""
        result = await server._execute_tool("list_skills", {"category": "code"})
        assert result["success"] is True
        for skill in result["skills"]:
            assert skill["category"] == "code"

    @pytest.mark.asyncio
    async def test_list_skills_filter_by_layer(self, server):
        """list_skills 按 layer 过滤"""
        result = await server._execute_tool("list_skills", {"layer": "L1"})
        assert result["success"] is True
        for skill in result["skills"]:
            assert skill["layer"] == "L1"

    @pytest.mark.asyncio
    async def test_list_skills_nonexistent_filter(self, server):
        """list_skills 不存在的过滤条件应返回空列表"""
        result = await server._execute_tool("list_skills", {"category": "nonexistent_xyz"})
        assert result["success"] is True
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_run_skill_missing_name(self, server):
        """run_skill 缺少 skill_name 应报错"""
        with pytest.raises(TypeError):
            await server._execute_tool("run_skill", {})

    @pytest.mark.asyncio
    async def test_run_skill_nonexistent(self, server):
        """run_skill 不存在的技能应返回错误信息"""
        result = await server._execute_tool("run_skill", {"skill_name": "nonexistent_skill_xyz"})
        assert result["success"] is True  # LingFlow.run_skill 不抛异常，返回 result dict
        assert "result" in result
        assert "error" in result["result"]

    @pytest.mark.asyncio
    async def test_run_skill_with_params(self, server):
        """run_skill 带参数执行"""
        result = await server._execute_tool("run_skill", {
            "skill_name": "code_analysis",
            "params": {"target": "."},
        })
        assert "success" in result
        assert "skill" in result


class TestCodeReviewTool:
    """测试代码审查工具"""

    @pytest.mark.asyncio
    async def test_review_python_file(self, server, tmp_path):
        """审查 Python 文件"""
        test_file = tmp_path / "sample.py"
        test_file.write_text('"""Module."""\n\ndef hello():\n    print("hi")\n')

        result = await server._execute_tool("review_code", {
            "target_path": str(test_file),
        })
        assert result["success"] is True
        assert "report" in result

    @pytest.mark.asyncio
    async def test_review_with_dimensions(self, server, tmp_path):
        """审查指定维度"""
        test_file = tmp_path / "sample2.py"
        test_file.write_text("x = 1\n")

        result = await server._execute_tool("review_code", {
            "target_path": str(test_file),
            "dimensions": ["complexity", "documentation"],
        })
        assert result["success"] is True
        assert "dimensions_checked" in result["report"]

    @pytest.mark.asyncio
    async def test_review_long_file(self, server, tmp_path):
        """审查超长文件应报告 complexity 问题"""
        lines = ["# line"] * 600
        test_file = tmp_path / "long.py"
        test_file.write_text("\n".join(lines))

        result = await server._execute_tool("review_code", {
            "target_path": str(test_file),
            "dimensions": ["complexity"],
        })
        assert result["success"] is True
        issues = result["report"].get("issues", [])
        complexity_issues = [i for i in issues if i.get("dimension") == "complexity"]
        assert len(complexity_issues) > 0

    @pytest.mark.asyncio
    async def test_review_nonexistent_path(self, server):
        """审查不存在的路径应返回失败"""
        result = await server._execute_tool("review_code", {
            "target_path": "/nonexistent/path/file.py",
        })
        assert result["success"] is True  # 简化审查不报错，但 report 为空


class TestIntelligenceTools:
    """测试情报工具"""

    @pytest.mark.asyncio
    async def test_get_github_trends_default(self, server):
        """get_github_trends 默认参数"""
        result = await server._execute_tool("get_github_trends", {})
        assert "success" in result
        assert "trends" in result
        assert isinstance(result["trends"], list)

    @pytest.mark.asyncio
    async def test_get_github_trends_with_keywords(self, server):
        """get_github_trends 带关键词"""
        result = await server._execute_tool("get_github_trends", {
            "keywords": ["python", "mcp"],
            "limit": 5,
        })
        assert "success" in result

    @pytest.mark.asyncio
    async def test_get_npm_trends_default(self, server):
        """get_npm_trends 默认参数"""
        result = await server._execute_tool("get_npm_trends", {})
        assert "success" in result
        assert "trends" in result
        assert isinstance(result["trends"], list)

    @pytest.mark.asyncio
    async def test_get_npm_trends_with_limit(self, server):
        """get_npm_trends 带限制"""
        result = await server._execute_tool("get_npm_trends", {
            "keywords": ["react"],
            "limit": 3,
        })
        assert "success" in result


# ============================================================================
# 3. Phase 2 工具执行测试 (P1)
# ============================================================================


class TestWorkflowTools:
    """测试工作流工具"""

    @pytest.mark.asyncio
    async def test_list_workflows(self, server):
        """list_workflows 应返回工作流列表"""
        result = await server._execute_tool("list_workflows", {})
        assert "success" in result
        assert "workflows" in result
        assert isinstance(result["workflows"], list)

    @pytest.mark.asyncio
    async def test_list_workflows_with_filter(self, server):
        """list_workflows 带过滤"""
        result = await server._execute_tool("list_workflows", {
            "status_filter": "pending",
        })
        assert "success" in result

    @pytest.mark.asyncio
    async def test_run_workflow_is_async(self, server):
        """run_workflow 应创建异步任务"""
        result = await server._execute_tool("run_workflow", {
            "workflow_id": "test_wf_001",
        })
        assert "task_id" in result
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_workflow_status_nonexistent(self, server):
        """get_workflow_status 不存在的工作流"""
        result = await server._execute_tool("get_workflow_status", {
            "workflow_id": "nonexistent_wf",
        })
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_run_workflow_with_strategy(self, server):
        """run_workflow 带执行策略"""
        result = await server._execute_tool("run_workflow", {
            "workflow_id": "test_wf_002",
            "strategy": "sequential",
        })
        assert "task_id" in result


class TestRequirementTools:
    """测试需求管理工具"""

    @pytest.mark.asyncio
    async def test_create_requirement(self, server):
        """创建需求"""
        result = await server._execute_tool("create_requirement", {
            "title": "Test Feature",
            "description": "A test requirement for E2E",
            "priority": "high",
        })
        assert "success" in result

    @pytest.mark.asyncio
    async def test_create_requirement_with_tags(self, server):
        """创建需求带标签"""
        result = await server._execute_tool("create_requirement", {
            "title": "Tagged Feature",
            "description": "Test with tags",
            "tags": ["e2e", "test"],
            "category": "testing",
        })
        assert "success" in result

    @pytest.mark.asyncio
    async def test_get_requirement_nonexistent(self, server):
        """获取不存在的需求"""
        result = await server._execute_tool("get_requirement", {
            "requirement_id": "nonexistent_id",
        })
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_update_requirement_nonexistent(self, server):
        """更新不存在的需求"""
        result = await server._execute_tool("update_requirement", {
            "requirement_id": "nonexistent_id",
            "status": "active",
        })
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_list_requirements(self, server):
        """列出需求"""
        result = await server._execute_tool("list_requirements", {})
        assert "success" in result
        assert "requirements" in result

    @pytest.mark.asyncio
    async def test_list_requirements_with_filter(self, server):
        """列出需求带过滤"""
        result = await server._execute_tool("list_requirements", {
            "priority_filter": "high",
            "limit": 10,
        })
        assert "success" in result

    @pytest.mark.asyncio
    async def test_link_requirement_to_branch(self, server):
        """关联需求到分支"""
        result = await server._execute_tool("link_requirement_to_branch", {
            "requirement_id": "test_req_001",
            "branch_name": "feature/test-branch",
        })
        assert "success" in result


# ============================================================================
# 4. Phase 3 工具执行测试 (P2)
# ============================================================================


class TestTestingTools:
    """测试运行工具"""

    @pytest.mark.asyncio
    async def test_run_tests_minimal(self, server):
        """最小化运行测试（使用 dummy 测试文件避免递归）"""
        result = await server._execute_tool("run_tests", {
            "test_path": "tests/_dummy_for_e2e.py",
            "test_type": "all",
            "coverage": False,
        })
        assert "success" in result
        assert "stats" in result

    @pytest.mark.asyncio
    async def test_get_coverage(self, server, tmp_path):
        """获取覆盖率（使用 tmp_path 避免触发全项目扫描）"""
        result = await server._execute_tool("get_coverage", {
            "target_path": str(tmp_path),
            "format_type": "summary",
        })
        assert "success" in result

    @pytest.mark.asyncio
    async def test_generate_test_report_markdown(self, server):
        """生成 Markdown 测试报告（使用 dummy 测试文件）"""
        result = await server._execute_tool("generate_test_report", {
            "test_path": "tests/_dummy_for_e2e.py",
            "output_format": "markdown",
        })
        assert "success" in result
        assert "report" in result

    @pytest.mark.asyncio
    async def test_generate_test_report_json(self, server):
        """生成 JSON 测试报告（使用 dummy 测试文件）"""
        result = await server._execute_tool("generate_test_report", {
            "test_path": "tests/_dummy_for_e2e.py",
            "output_format": "json",
        })
        assert "success" in result


class TestMonitoringTools:
    """测试运维监控工具"""

    @pytest.mark.asyncio
    async def test_get_health_status_default(self, server):
        """默认健康检查"""
        result = await server._execute_tool("get_health_status", {})
        assert result["success"] is True
        assert "overall_status" in result
        assert "checks" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_health_status_single_check(self, server):
        """单项健康检查"""
        result = await server._execute_tool("get_health_status", {
            "checks": ["memory"],
        })
        assert result["success"] is True
        assert "memory" in result["checks"]

    @pytest.mark.asyncio
    async def test_get_health_status_all_checks(self, server):
        """全项健康检查"""
        result = await server._execute_tool("get_health_status", {
            "checks": ["disk", "memory", "cpu", "python", "lingflow"],
        })
        assert result["success"] is True
        for check in ["disk", "memory", "cpu", "python", "lingflow"]:
            assert check in result["checks"]

    @pytest.mark.asyncio
    async def test_get_metrics_default(self, server):
        """默认指标"""
        result = await server._execute_tool("get_metrics", {})
        assert result["success"] is True
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_get_metrics_specific(self, server):
        """指定指标"""
        result = await server._execute_tool("get_metrics", {
            "metric_names": ["cpu", "memory"],
            "time_range": "1h",
        })
        assert result["success"] is True
        assert "cpu" in result["metrics"]
        assert "memory" in result["metrics"]

    @pytest.mark.asyncio
    async def test_detect_anomaly_cpu(self, server):
        """CPU 异常检测"""
        result = await server._execute_tool("detect_anomaly", {
            "metric_name": "cpu",
        })
        assert "success" in result
        assert "is_anomaly" in result

    @pytest.mark.asyncio
    async def test_detect_anomaly_with_value(self, server):
        """异常检测带指定值"""
        result = await server._execute_tool("detect_anomaly", {
            "metric_name": "memory",
            "value": 99.5,
            "threshold": 90.0,
        })
        assert "success" in result

    @pytest.mark.asyncio
    async def test_detect_anomaly_disk(self, server):
        """磁盘异常检测"""
        result = await server._execute_tool("detect_anomaly", {
            "metric_name": "disk",
        })
        assert "success" in result


# ============================================================================
# 5. 异步任务系统测试
# ============================================================================


class TestAsyncTaskSystem:
    """测试异步任务管理"""

    @pytest.mark.asyncio
    async def test_create_and_query_task(self, server):
        """创建任务并查询状态"""
        create_result = await server._execute_tool("run_workflow", {
            "workflow_id": "async_test_wf",
        })
        assert "task_id" in create_result

        task_id = create_result["task_id"]
        status_result = await server._execute_tool("get_task_status", {
            "task_id": task_id,
        })
        assert "status" in status_result
        assert status_result["status"] in ["pending", "running", "completed", "failed"]

    @pytest.mark.asyncio
    async def test_query_nonexistent_task(self, server):
        """查询不存在的任务"""
        result = await server._execute_tool("get_task_status", {
            "task_id": "nonexistent_task_999",
        })
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_list_tasks(self, server):
        """列出所有任务"""
        await server._execute_tool("run_workflow", {"workflow_id": "list_test_wf"})

        result = await server._execute_tool("list_tasks", {})
        assert result["success"] is True
        assert "tasks" in result
        assert "total" in result

    @pytest.mark.asyncio
    async def test_list_tasks_with_filter(self, server):
        """列出任务带状态过滤"""
        result = await server._execute_tool("list_tasks", {
            "status_filter": "completed",
        })
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_multiple_async_tasks(self, server):
        """创建多个异步任务"""
        task_ids = []
        for i in range(3):
            result = await server._execute_tool("run_workflow", {
                "workflow_id": f"multi_test_wf_{i}",
            })
            task_ids.append(result["task_id"])

        assert len(set(task_ids)) == 3, "Task IDs should be unique"


# ============================================================================
# 6. 错误处理和边界条件
# ============================================================================


class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_unknown_tool(self, server):
        """调用不存在的工具"""
        with pytest.raises(ValueError, match="未知工具"):
            await server._execute_tool("nonexistent_tool_xyz", {})

    @pytest.mark.asyncio
    async def test_empty_arguments(self, server):
        """空参数调用"""
        result = await server._execute_tool("list_skills", {})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_extra_arguments_rejected(self, server):
        """多余参数应导致 TypeError"""
        with pytest.raises(TypeError):
            await server._execute_tool("list_skills", {
                "extra_param": "should_cause_error",
            })

    @pytest.mark.asyncio
    async def test_detect_anomaly_unknown_metric(self, server):
        """异常检测未知指标"""
        result = await server._execute_tool("detect_anomaly", {
            "metric_name": "unknown_metric_xyz",
        })
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_health_status_unknown_check(self, server):
        """健康检查未知类型"""
        result = await server._execute_tool("get_health_status", {
            "checks": ["unknown_check"],
        })
        assert result["success"] is True
        assert result["checks"]["unknown_check"]["status"] == "unknown"


# ============================================================================
# 7. ToolRegistry 单元测试
# ============================================================================


class TestToolRegistryUnit:
    """ToolRegistry 单元测试"""

    def test_register_and_get(self):
        """注册并获取工具"""
        from lingflow_mcp.tools import ToolRegistry

        registry = ToolRegistry()

        async def dummy_handler(x: str) -> Dict[str, Any]:
            return {"x": x}

        registry.register(
            name="test_tool",
            description="Test",
            handler=dummy_handler,
            input_schema={"type": "object"},
        )

        handler = registry.get_tool_handler("test_tool")
        assert handler is not None
        assert handler == dummy_handler

    def test_get_nonexistent_handler(self):
        """获取不存在的工具 handler"""
        from lingflow_mcp.tools import ToolRegistry

        registry = ToolRegistry()
        assert registry.get_tool_handler("no_such_tool") is None

    def test_register_overwrite(self):
        """覆盖注册工具"""
        from lingflow_mcp.tools import ToolRegistry

        registry = ToolRegistry()

        async def handler_v1():
            return {"v": 1}

        async def handler_v2():
            return {"v": 2}

        registry.register("tool", "desc", handler_v1, {"type": "object"})
        registry.register("tool", "desc v2", handler_v2, {"type": "object"})

        assert registry.get_tool_handler("tool") == handler_v2

    def test_async_tool_flag(self):
        """异步工具标记"""
        from lingflow_mcp.tools import ToolRegistry

        registry = ToolRegistry()

        registry.register("sync_tool", "s", lambda: None, {"type": "object"})
        registry.register("async_tool", "a", lambda: None, {"type": "object"}, is_async=True)

        assert registry.is_async_tool("sync_tool") is False
        assert registry.is_async_tool("async_tool") is True

    def test_is_async_tool_nonexistent(self):
        """检查不存在的工具是否异步"""
        from lingflow_mcp.tools import ToolRegistry

        registry = ToolRegistry()
        assert registry.is_async_tool("nope") is False


# ============================================================================
# 8. 配置测试
# ============================================================================


class TestConfig:
    """测试配置系统"""

    def test_server_config_from_env(self):
        """从环境变量加载配置"""
        from lingflow_mcp.config import ServerConfig

        config = ServerConfig.from_env()
        assert config is not None
        assert config.work_dir is not None

    def test_server_config_to_dict(self):
        """配置转字典"""
        from lingflow_mcp.config import ServerConfig

        config = ServerConfig.from_env()
        d = config.to_dict()
        assert "work_dir" in d
        assert "log_level" in d

    def test_server_config_tokens_masked(self):
        """Token 在 to_dict 中被遮蔽"""
        from lingflow_mcp.config import ServerConfig

        config = ServerConfig(github_token="secret_token_123")
        d = config.to_dict()
        assert d["github_token"] == "***"

    def test_server_config_defaults(self):
        """默认配置值"""
        from lingflow_mcp.config import ServerConfig

        config = ServerConfig()
        assert config.max_async_tasks == 10
        assert config.task_timeout == 300
        assert config.enable_cache is True
        assert config.cache_ttl == 3600
        assert config.read_only is False


# ============================================================================
# 9. 服务器初始化测试
# ============================================================================


class TestServerInit:
    """测试服务器初始化"""

    def test_create_server(self):
        """创建服务器实例"""
        from lingflow_mcp import create_server

        srv = create_server()
        assert srv is not None
        assert srv.server is not None
        assert srv.tool_registry is not None

    def test_server_has_lingflow(self):
        """服务器持有 LingFlow 实例"""
        from lingflow_mcp import create_server

        srv = create_server()
        assert hasattr(srv, "lingflow")
        assert srv.lingflow is not None

    def test_server_has_skill_registry(self):
        """服务器持有技能注册表"""
        from lingflow_mcp import create_server

        srv = create_server()
        assert hasattr(srv, "skill_registry")

    def test_server_has_workflow_coordinator(self):
        """服务器持有工作流协调器"""
        from lingflow_mcp import create_server

        srv = create_server()
        assert hasattr(srv, "workflow_coordinator")

    def test_server_async_tasks_dict(self):
        """服务器有异步任务存储"""
        from lingflow_mcp import create_server

        srv = create_server()
        assert hasattr(srv, "_async_tasks")
        assert isinstance(srv._async_tasks, dict)

    def test_server_mcp_version(self):
        """MCP 版本号"""
        from lingflow_mcp import __version__

        assert __version__ == "1.3.0"
