# LingFlow MCP Server v1.3.0

将 LingFlow v3.7.0 的工程流能力封装为 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) 服务器，使 AI 助手（Claude Desktop、Cursor 等）可直接调用 LingFlow 功能。

**版本**: v1.3.0 (Phase 3 完成)
**状态**: ✅ 生产就绪
**工具数量**: 21 个
**功能域**: 8 个
**测试通过率**: 80% (Phase 3), 100% (Phase 1+2)

## 🎯 什么是 MCP？

MCP 是 Anthropic 推出的标准化协议，允许 AI 应用通过统一接口调用外部工具。将 LingFlow 封装为 MCP 服务器后：

- ✅ **零集成接入**：任何支持 MCP 的 AI 客户端可直接使用
- ✅ **自然语言交互**：无需学习命令行语法
- ✅ **生态融合**：可与其他 MCP 服务器协同工作

## 🚀 快速开始

### 安装

```bash
# 从 PyPI 安装 LingFlow
pip install lingflow-core

# 安装 MCP SDK
pip install mcp

# 安装 LingFlow MCP Server
cd mcp_server
pip install -e .
```

### 启动服务器

```bash
# 基础启动
lingflow-mcp run

# 自定义配置
lingflow-mcp run --work-dir /path/to/project --log-level DEBUG
```

### 查看可用工具

```bash
lingflow-mcp tools
```

### 测试连接

```bash
lingflow-mcp test
```

## 🛠️ 可用工具

### Phase 1: 高优先级工具 (P0) ✅

| 工具名称 | 描述 | 分类 |
|---------|------|------|
| `list_skills` | 列出所有可用技能（8个内置） | 查询 |
| `run_skill` | 执行指定技能 | 执行 |
| `review_code` | 8维度代码审查 | 审查 |
| `get_github_trends` | 采集 GitHub 趋势项目 | 情报 |
| `get_npm_trends` | 采集 npm 趋势包 | 情报 |

### Phase 2: 中优先级工具 (P1) ✅

**工作流管理**:
| 工具名称 | 描述 | 新增 |
|---------|------|------|
| `list_workflows` | 列出所有工程流（15+），支持过滤 | ⭐ |
| `run_workflow` | 执行工程流（异步，支持3种策略） | ⭐ |
| `get_workflow_status` | 获取工作流详细状态 | 🆕 |

**需求管理**:
| 工具名称 | 描述 | 新增 |
|---------|------|------|
| `create_requirement` | 创建需求（支持分类和标签） | ⭐ |
| `get_requirement` | 获取需求详情 | ✅ |
| `update_requirement` | 更新需求信息 | 🆕 |
| `list_requirements` | 列出需求（支持过滤和分页） | 🆕 |
| `link_requirement_to_branch` | 关联需求到 Git 分支 | 🆕 |

**异步任务**:
| 工具名称 | 描述 | 新增 |
|---------|------|------|
| `get_task_status` | 查询异步任务状态 | ✅ |
| `list_tasks` | 列出所有异步任务 | 🆕 |

**总计**: **15 个工具**

### Phase 3: 运维监控工具 (P2) ✅

**测试运行**:
| 工具名称 | 描述 | 新增 |
|---------|------|------|
| `run_tests` | 运行测试套件（支持单元/集成测试） | ⭐ |
| `get_coverage` | 获取测试覆盖率（支持多种格式） | ⭐ |
| `generate_test_report` | 生成测试报告（Markdown/JSON/HTML） | ⭐ |

**运维监控**:
| 工具名称 | 描述 | 新增 |
|---------|------|------|
| `get_health_status` | 系统健康检查（磁盘/内存/CPU） | ⭐ |
| `get_metrics` | 性能指标（CPU/内存/磁盘/进程） | ⭐ |
| `detect_anomaly` | 异常检测（基于历史数据和阈值） | ⭐ |

**工具总数**: **21 个** (Phase 1: 5, Phase 2: 10, Phase 3: 6)

## 📖 使用示例

### 在 Claude Desktop 中使用

1. 配置 Claude Desktop：

编辑 `~claude_desktop_config.json`（macOS/Linux）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

```json
{
  "mcpServers": {
    "lingflow": {
      "command": "lingflow-mcp",
      "args": ["run"]
    }
  }
}
```

2. 重启 Claude Desktop

3. 在对话中使用：

```
用户: 列出所有开发类工作流

Claude: [自动调用 list_workflows(type_filter="dev")]
返回: 3 个开发工作流

用户: 执行功能开发工作流

Claude: [自动调用 run_workflow(workflow_id="feature-dev")]
返回: task_id=workflow_abc123, 状态=pending

用户: 创建一个新需求

Claude: [自动调用 create_requirement(...)]
返回: requirement_id=req-456
```

### 工作流管理示例

```python
import asyncio
from lingflow_mcp import create_server

async def workflow_example():
    server = create_server()

    # 列出所有工作流
    workflows = await server._execute_tool(
        "list_workflows",
        {"type_filter": "dev"}
    )
    print(f"开发工作流: {workflows['total']} 个")

    # 执行工作流
    result = await server._execute_tool(
        "run_workflow",
        {
            "workflow_id": "feature-development",
            "params": {"feature": "user-auth"},
            "strategy": "hybrid"
        }
    )
    print(f"任务 ID: {result['task_id']}")

    # 查询状态
    status = await server._execute_tool(
        "get_workflow_status",
        {"workflow_id": "feature-development"}
    )
    print(f"状态: {status['workflow']['status']}")

asyncio.run(workflow_example())
```

### 需求管理示例

```python
async def requirement_example():
    server = create_server()

    # 创建需求
    req = await server._execute_tool(
        "create_requirement",
        {
            "title": "添加用户认证",
            "description": "实现 OAuth2.0 登录功能",
            "priority": "high",
            "category": "feature",
            "tags": ["security", "auth"]
        }
    )
    req_id = req["requirement_id"]

    # 更新需求
    await server._execute_tool(
        "update_requirement",
        {
            "requirement_id": req_id,
            "status": "approved"
        }
    )

    # 关联到分支
    await server._execute_tool(
        "link_requirement_to_branch",
        {
            "requirement_id": req_id,
            "branch_name": "feature/user-auth"
        }
    )

    print(f"需求 {req_id} 已创建并关联到分支")

asyncio.run(requirement_example())
```

## 🔧 配置选项

### 环境变量

| 变量名 | 描述 | 默认值 |
|-------|------|--------|
| `LINGFLOW_WORK_DIR` | 工作目录 | 当前目录 |
| `GITHUB_TOKEN` | GitHub API Token | - |
| `NPM_TOKEN` | npm Token | - |
| `LINGFLOW_LOG_LEVEL` | 日志级别 | INFO |
| `LINGFLOW_READ_ONLY` | 只读模式 | false |

### CLI 参数

```bash
lingflow-mcp run [OPTIONS]

选项:
  --host TEXT          监听地址（默认: localhost）
  --port INTEGER       监听端口（默认: 8000）
  --work-dir PATH      工作目录
  --log-level TEXT     日志级别（INFO/DEBUG/WARNING/ERROR）
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────┐
│  AI Client (Claude Desktop, Cursor)     │
└─────────────────┬───────────────────────┘
                  │ MCP Protocol (stdio)
┌─────────────────▼───────────────────────┐
│     LingFlow MCP Server v1.3.0          │
│  ┌───────────────────────────────────┐  │
│  │  Tool Registry (21 tools)        │  │
│  │  - Skills (2)                    │  │
│  │  - Code Review (1)               │  │
│  │  - Intelligence (2)              │  │
│  │  - Workflows (3)                 │  │
│  │  - Requirements (5)              │  │
│  │  - Task Management (2)           │  │
│  │  - Testing (3) ⭐                │  │
│  │  - Monitoring (3) ⭐              │  │
│  └─────────────┬─────────────────────┘  │
│                │                         │
│  ┌─────────────▼─────────────────────┐  │
│  │  LingFlow Core (v3.7.0)           │  │
│  │  - 33 skills                      │  │
│  │  - 15+ workflows                  │  │
│  │  - Code review                    │  │
│  │  - Intelligence system            │  │
│  │  - Requirements traceability      │  │
│  │  - Test automation                │  │
│  │  - System monitoring              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 🔄 异步任务支持

对于长时间运行的工具（如工作流执行），MCP 服务器支持异步模式：

1. **提交任务**：立即返回 `task_id`
2. **查询状态**：使用 `get_task_status` 查询进度
3. **列表任务**：使用 `list_tasks` 查看所有任务

```python
# 提交异步任务
result = await server._execute_tool(
    "run_workflow",
    {"workflow_id": "feature-development"}
)

# 返回: {"task_id": "workflow_abc123", "status": "pending"}

# 查询状态
status = await server._execute_tool(
    "get_task_status",
    {"task_id": "workflow_abc123"}
)

# 返回: {"task_id": "workflow_abc123", "status": "running", ...}

# 列出所有运行中的任务
tasks = await server._execute_tool(
    "list_tasks",
    {"status_filter": "running"}
)
```

## 🛡️ 安全性

### 文件系统权限

MCP 服务器默认限制在工作目录内操作，可在配置中扩展：

```python
from lingflow_mcp.config import ServerConfig

config = ServerConfig(
    work_dir=Path("/my/project"),
    allowed_paths=[
        Path("/my/project"),
        Path("/shared/libs"),
    ],
    read_only=False,  # 设置为 True 只读模式
)
```

### API Token 安全

使用环境变量传递敏感信息：

```bash
export GITHUB_TOKEN="ghp_xxx"
export NPM_TOKEN="npm_xxx"
lingflow-mcp run
```

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| 工具数量 | 21 |
| 功能域 | 8 |
| 工具响应时间 | <200ms (同步) |
| 异步任务创建 | <50ms |
| 并发支持 | 10 个异步任务 |
| 内存占用 | ~70MB (基础) |
| 缓存命中率 | >80% (情报工具) |

## 🧪 测试

```bash
# 运行单元测试
cd mcp_server
pytest tests/

# 运行功能测试
python test_mcp_functionality.py

# 测试 MCP 服务器
lingflow-mcp test
```

**测试覆盖**: 100% (Phase 1 + Phase 2), 80% (Phase 3)

## 📚 文档

- [MCP 协议规范](https://spec.modelcontextprotocol.io/)
- [LingFlow 主文档](../README.md)
- [工具和功能域完整说明](TOOLS_AND_DOMAINS_GUIDE.md) - **21个工具详细说明**
- [最终完成报告](FINAL_COMPLETION_REPORT.md) - v1.3.0 总结
- [Phase 3 完成报告](PHASE3_COMPLETION_REPORT.md)
- [Phase 2 完成报告](PHASE2_COMPLETION_REPORT.md)
- [MCP 封装可行性评估](../docs/architecture/MCP_INTEGRATION_ANALYSIS.md)

## 🐛 故障排查

### 问题：MCP SDK 未安装

```bash
pip install mcp
```

### 问题：LingFlow 导入失败

```bash
pip install lingflow-core
```

### 问题：工具调用超时

增加超时时间：

```python
config = ServerConfig(
    task_timeout=600,  # 10 分钟
)
```

## 📄 许可证

MIT License - 与 LingFlow 主项目一致

## 🎉 路线图

### v2.0.0 (未来计划)
- [ ] WebSocket 支持
- [ ] 实时监控仪表板
- [ ] 云端部署版本
- [ ] 多语言支持 (JavaScript, Go)

---

**LingFlow MCP Server v1.3.0 - 众智混元，万法灵通** 🚀

*从命令行工具到 AI 生态的基础设施组件*
