# lingflow 封装与仓库清单

**更新日期**: 2026-04-03
**版本**: v3.8.0
**状态**: 生产就绪

---

## 📦 远程仓库

| 远程名 | 地址 | 用途 |
|--------|------|------|
| **github** | `git@github.com:guangda88/lingflow.git` | 主仓库（SSH） |
| **origin** | `http://zhinenggitea.iepose.cn/guangda/lingflow.git` | 内部Gitea镜像 |

**分支状态**:
- 当前分支: `master`
- 本地提交: `8681816`
- 远程状态: 领先 `origin/master` 1 个提交

---

## 🔧 4种封装形式

| 封装 | 命令/入口 | 版本 | 文件数 | PyPI | 状态 |
|------|----------|------|--------|------|------|
| **CLI** | `lingflow` | v3.8.0 | 7 py | lingflow-core | ✅ 已跟踪 |
| **REST API** | `docker run lingflow-api` | v1.0.0-alpha | 33 文件 | - | ✅ 已跟踪 |
| **MCP Server** | `lingflow-mcp` | v1.3.0 | 29 文件 | lingflow-mcp | ✅ 已跟踪 |
| **GitHub Actions** | `uses: lingflow/actions/quality-gate@v1` | v1.0 | 7 文件 | - | ✅ 已跟踪 |

---

## 1. CLI 封装

### 基本信息

```
位置: lingflow/cli/
入口: lingflow (通过 project.scripts 配置)
PyPI: pip install lingflow-core
版本: v3.8.0
```

### 文件结构

```
lingflow/cli/
├── __init__.py       # 主入口，Click CLI 组装
├── __main__.py       # CLI 启动点
├── analyze.py        # analyze 命令 - 代码分析
├── optimize.py       # optimize 命令 - 代码优化
├── learn.py          # learn 命令 - 学习功能
├── test.py           # test 命令 - 测试执行
└── feedback.py       # feedback 命令 - 反馈收集
```

### 使用方式

```bash
# 安装
pip install lingflow-core

# 列出技能
lingflow list-skills

# 执行技能
lingflow run code-review --target ./src

# 运行优化
lingflow optimize structure --target ./
```

### 配置入口点

```toml
[project.scripts]
lingflow = "lingflow.cli.__main__:cli"
```

---

## 2. REST API 封装

### 基本信息

```
位置: lingflow-api/
端口: 8000
Docker: guangda88/lingflow-api
版本: v1.0.0-alpha (开发中)
```

### 文件结构

```
lingflow-api/
├── app/
│   ├── main.py           # FastAPI 应用主入口
│   ├── main_simple.py    # 简化版本
│   ├── api/              # API 路由
│   │   └── v1/           # v1 版本 API
│   │       ├── skills.py
│   │       ├── workflows.py
│   │       ├── review.py
│   │       └── intelligence.py
│   ├── core/             # 核心模块
│   │   ├── config.py      # 配置
│   │   ├── security.py    # 安全认证
│   │   ├── logging.py     # 日志
│   │   ├── metrics.py     # 指标
│   │   └── middleware.py  # 中间件
│   └── models/           # 数据模型
│       ├── requests.py
│       └── responses.py
├── Dockerfile            # 容器镜像
├── docker-compose.yml    # 完整部署
├── requirements.txt      # 依赖
├── start.sh              # 启动脚本
└── tests/                # API 测试
```

### API 端点

```
GET  /api/v1/skills                    # 列出技能
POST /api/v1/skills/{name}/execute     # 执行技能
GET  /api/v1/workflows                 # 列出工作流
POST /api/v1/workflows/{name}/run      # 执行工作流
GET  /api/v1/tasks/{task_id}           # 查询任务状态
POST /api/v1/review                    # 代码审查
GET  /api/v1/intelligence/github       # GitHub 趋势
GET  /api/v1/intelligence/npm          # npm 趋势
```

### 使用方式

```bash
# Docker 启动
docker run -p 8000:8000 guangda88/lingflow-api

# Docker Compose
docker-compose up -d

# 访问文档
http://localhost:8000/docs
```

---

## 3. MCP Server 封装

### 基本信息

```
位置: mcp_server/
入口: lingflow-mcp run
PyPI: pip install mcp
版本: v1.3.0 (Phase 3 完成)
工具数: 21 个
功能域: 8 个
```

### 文件结构

```
mcp_server/
├── lingflow_mcp/
│   ├── __init__.py
│   ├── server.py          # MCP 服务器主逻辑
│   ├── tools/              # 工具实现
│   │   ├── skills.py       # 技能工具
│   │   ├── workflows.py    # 工作流工具
│   │   ├── review.py       # 审查工具
│   │   ├── requirements.py # 需求工具
│   │   ├── intelligence.py # 情报工具
│   │   └── ...
│   └── cli.py              # 命令行入口
├── tests/
│   ├── test_mcp_functionality.py
│   └── test_phase3.py
├── pyproject.toml          # 包配置
└── README.md               # 使用文档
```

### 工具列表 (灵系命名)

| 中文名 | 工具名称 | 功能 | 分类 |
|--------|----------|------|------|
| 灵艺 | `list_skills` | 列出所有可用技能 | 查询 |
| 灵行 | `run_skill` | 执行指定技能 | 执行 |
| 灵鉴 | `review_code` | 8维度代码审查 | 审查 |
| 灵探 | `get_github_trends` | 采集 GitHub 趋势项目 | 情报 |
| 灵觉 | `get_npm_trends` | 采集 npm 趋势包 | 情报 |
| 灵流 | `list_workflows` | 列出所有工程流 | 工作流 |
| 灵运 | `run_workflow` | 执行工程流 | 工作流 |
| 灵踪 | `get_workflow_status` | 获取工作流状态 | 工作流 |
| 灵愿 | `create_requirement` | 创建需求 | 需求 |
| 灵览 | `get_requirement` | 获取需求详情 | 需求 |
| 灵新 | `update_requirement` | 更新需求 | 需求 |
| 灵录 | `list_requirements` | 列出需求 | 需求 |
| 灵归 | `optimize_code` | 代码优化 | 优化 |
| 灵知 | `get_optimization_status` | 获取优化状态 | 优化 |
| 灵启 | `start_optimization` | 启动优化任务 | 优化 |
| 灵析 | `analyze_codebase` | 分析代码库 | 分析 |
| 灵图 | `generate_architecture_diagram` | 生成架构图 | 分析 |
| 灵测 | `run_tests` | 运行测试 | 测试 |
| 灵策 | `generate_test_plan` | 生成测试计划 | 测试 |
| 灵告 | `get_test_report` | 获取测试报告 | 测试 |
| 灵议 | `generate_fix_suggestions` | 生成修复建议 | 修复 |

### 使用方式

```bash
# 安装
pip install mcp

# 启动服务器
lingflow-mcp run

# 查看工具
lingflow-mcp tools

# 测试连接
lingflow-mcp test
```

### Claude Desktop 配置

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

---

## 4. GitHub Actions 封装

### 基本信息

```
位置: actions/quality-gate/
版本: v1.0
Marketplace: lingflow/actions/quality-gate
```

### 文件结构

```
actions/quality-gate/
├── action.yml              # Action 定义
├── Dockerfile              # 容器镜像
├── entrypoint.sh           # 启动脚本
├── README.md               # 使用文档
├── RELEASE_CHECKLIST.md    # 发布清单
├── test-action.sh          # 本地测试脚本
└── examples/               # 示例工作流
    └── basic-workflow.yml
```

### 使用方式

```yaml
name: lingflow Quality Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  lingflow-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run lingflow Review
        uses: lingflow/actions/quality-gate@v1
        with:
          command: review
          path: ./src
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `command` | 否 | `review` | lingflow 命令 |
| `path` | 否 | `.` | 目标路径 |
| `github_token` | 是 | `${{ github.token }}` | GitHub Token |
| `api_key` | 否 | - | lingflow API Key |
| `fail_on_error` | 否 | `false` | 发现问题是否失败 |
| `output_format` | 否 | `markdown` | 输出格式 |

---

## 🏷️ PyPI 发布

### 已发布包

| 包名 | 版本 | 安装命令 |
|------|------|----------|
| `lingflow-core` | v3.8.0 | `pip install lingflow-core` |
| `lingflow-mcp` | v1.3.0 | `pip install mcp` |

### 发布脚本

```bash
# scripts/publish_to_pypi.sh
python -m build
twine upload dist/*
```

---

## 📊 Git 标签

```
v1.3.0
v3.1.0
v3.2.0
v3.3.0
v3.5.0
v3.5.6
v3.7.0
v3.8.0
```

---

## 📝 最新提交

```
8681816 feat: 系统 — 封装确认 + 文档清理 + CLI测试
0c4bbd9 refactor: 全面代码质量提升 — 安全加固+测试精简+文档归档
309586d refactor: comprehensive code quality improvements (P0-P2)
c1465ee test: long session validation of degradation detection
64fa1d0 test: increase coverage from 57% to 70% with 290+ new tests
88d619c fix: lint cleanup for degradation mitigation modules
6566a50 feat: long-context degradation mitigation system
13ac7bc release: v3.8.0 - AI 生态平台
8c725ab feat: lingflow MCP Server v1.3.0 - 完整实现与发布
2769cbe feat: PyPI publishing setup for v3.7.0
```

---

## 🚀 推送命令

```bash
# 推送到 GitHub
git push github master

# 推送到内部 Gitea
git push origin master

# 推送所有标签
git push github --tags
git push origin --tags

# 发布新版本
git tag -a v3.9.0 -m "v3.9.0 - 社区与异步"
git push github v3.9.0
```

---

## 📁 封装目录文件统计

| 目录 | Python 文件 | 总文件数 | Git 跟踪 |
|------|-------------|----------|----------|
| `lingflow/cli/` | 7 | 7 | 7 |
| `lingflow-api/` | 16 | 33 | 33 |
| `mcp_server/` | 14 | 34 | 29 |
| `actions/quality-gate/` | 0 | 7 | 7 |

---

## 🔗 相关链接

- **GitHub**: https://github.com/guangda88/lingflow
- **Issues**: https://github.com/guangda88/lingflow/issues
- **Discussions**: https://github.com/guangda88/lingflow/discussions
- **内部 Gitea**: http://zhinenggitea.iepose.cn/guangda/lingflow

---

**文档维护**: 请在新增封装或版本更新时同步更新此文档

**最后更新**: 2026-04-03
**维护者**: lingflow Team
