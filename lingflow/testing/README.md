# lingflow 现代化测试框架

## 目录结构

```
lingflow/testing/
├── __init__.py              # 模块导出
├── scenario.py              # 场景定义系统
├── test_server.py          # 测试服务器
├── tool_definition.py      # 工具类型系统
├── snapshot.py            # 快照测试
├── ai_runner.py           # AI 场景运行器
├── mcp_server.py         # MCP 测试服务器
├── unit/                 # 单元测试
│   ├── test_scenario.py
│   ├── test_server.py
│   ├── test_tool_definition.py
│   ├── test_snapshot.py
│   ├── test_ai_runner.py
│   └── test_mcp_server.py
├── snapshot/            # 快照测试
│   ├── snapshots/       # 快照文件存储
│   └── test_output_stability.py
├── scenarios/          # 场景测试
│   ├── test_refactoring.py
│   ├── test_security.py
│   └── test_optimization.py
├── e2e/               # 端到端测试
│   ├── test_full_workflow.py
│   └── test_ai_integration.py
└── fixtures/           # 测试固件
    ├── code_samples/    # 代码样本
    └── expected_outputs/ # 期望输出
```

## 核心模块

### 1. 场景定义 (scenario.py)

```python
from lingflow.testing import CodeTestScenario

# 创建场景
scenario = CodeTestScenario(
    name="refactor_function",
    prompt="重构这个函数降低复杂度",
    code_content="def process_data(items): ...",
    expected_tools=["analyze_complexity", "suggest_refactoring"]
)
```

### 2. 测试服务器 (test_server.py)

```python
from lingflow.testing import CodeTestServer

server = CodeTestServer()

# 添加测试代码
with server.code_context("test_module", test_code):
    # 运行测试
    result = run_tests()
```

### 3. 工具定义 (tool_definition.py)

```python
from lingflow.testing import BaseTool, ToolCategory

class MyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="我的工具",
            annotations={
                "category": ToolCategory.ANALYSIS,
                "read_only": True,
                "modifies_code": False
            }
        )

    async def handle(self, request, response, context):
        # 实现工具逻辑
        pass
```

### 4. 快照测试 (snapshot.py)

```python
from lingflow.testing import SnapshotTest

snapshot = SnapshotTest(Path("tests/snapshots"))

# 测试分析结果
result = analyze_code("def foo(): pass")

# 断言匹配快照
snapshot.assert_match("simple_function_analysis", result)
```

### 5. AI 场景运行器 (ai_runner.py)

```python
from lingflow.testing import AIScenarioRunner

runner = AIScenarioRunner()

# 运行场景
result = await runner.run_scenario(scenario, tools)
```

### 6. MCP 测试服务器 (mcp_server.py)

```python
from lingflow.testing import MCPTestServer

server = MCPTestServer()

# 启动服务器
await server.start()

# 处理请求
response = await server.handle_mcp_request(request)
```

## 运行测试

### 运行所有测试

```bash
python -m pytest lingflow/testing/
```

### 运行特定层次的测试

```bash
# 单元测试
python -m pytest lingflow/testing/unit/

# 快照测试
python -m pytest lingflow/testing/snapshot/

# 场景测试
python -m pytest lingflow/testing/scenarios/

# 端到端测试
python -m pytest lingflow/testing/e2e/
```

### 更新快照

```bash
# 更新所有快照
python -m pytest lingflow/testing/snapshot/ --update-snapshots

# 更新特定快照
python -m pytest lingflow/testing/snapshot/test_output_stability.py::test_name --update-snapshots
```

## 测试覆盖率

目标覆盖率:
- 单元测试: ≥80%
- 快照测试: 100%
- 场景测试: ≥60%
- 端到端测试: 关键路径

```bash
# 生成覆盖率报告
python -m pytest --cov=lingflow/testing --cov-report=html
```

## 参考文档

- Chrome DevTools MCP: https://github.com/ChromeDevTools/chrome-devtools-mcp
- 测试实施计划: TESTING_FRAMEWORK_IMPLEMENTATION_PLAN.md
- lingminopt 架构: LINGFLOW_OPTIMIZATION_REPORT.md
