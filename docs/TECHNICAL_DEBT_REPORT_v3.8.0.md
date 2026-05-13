# lingflow v3.8.0 技术债清单

**审计日期**: 2026-04-02
**测试状态**: 1359 passed, 0 failed, 6 skipped
**审计方法**: 全量代码扫描（95+ .py 文件、API层、文档层、配置层）

---

## P0 — 发布阻塞项 (4项)

### P0.1 REST API 4个端点运行时崩溃

`lingflow-api/app/main.py` 引用不存在的类，请求时 500：

| 行号 | 导入 | 问题 |
|------|------|------|
| 284 | `from lingflow.code_review import CodeReviewer` | 类不存在，应为 `BaseCodeReviewer` |
| 311 | `from lingflow.intelligence import GitHubTrendCollector` | `lingflow.intelligence` 模块不存在 |
| 331 | `from lingflow.intelligence import NpmTrendCollector` | 同上 |
| 353 | `from lingflow.requirements import RequirementManager` | 不存在，模块导出 `RequirementsTraceability` |

**验证**:
```
lingflow.code_review.CodeReviewer → MISSING
lingflow.intelligence → IMPORT ERROR (No module)
lingflow.requirements.RequirementManager → MISSING
```

### P0.2 REST API 硬编码默认密钥

`lingflow-api/app/core/config.py:21`:
```python
API_KEYS: str = "dev-key-12345"
```
未设置 `LINGFLOW_API_KEYS` 时，任何人可用此密钥。

### P0.3 bootstrap.py 版本号落后两代

`lingflow/bootstrap.py:19`:
```python
__version__ = "3.6.0"  # 实际 3.8.0
```

### P0.4 `track_context` 是空操作

`lingflow/__init__.py:82`:
```python
track_context = lambda *a, **k: None
```
用户 `from lingflow import track_context` 得到 no-op，静默吞掉所有调用。

---

## P1 — 功能缺陷 (6项)

### P1.1 双配置系统并存

| 系统 | 位置 | 使用方 |
|------|------|--------|
| `lingflowConfig` (dataclass) | `core/config.py` | 2处（core/__init__.py + 1测试） |
| `ConfigManager` (dict+env) | `common/config.py` | 4处生产代码 |

`lingflowConfig` 实质死代码但对外可见。

### P1.2 `get_smart_compressor` 导出链可能断裂

`lingflow/__init__.py:77` 调用 `from .compression import get_smart_compressor`，但 `compression/__init__.py` 的 `__all__` 未包含此函数。

### P1.3 `ai_friendly.py` 访问私有属性

`lingflow/ai_friendly.py:259`:
```python
self._coordinator.execute_skill_async(...)
```

### P1.4 9个模块零测试覆盖

| 模块 | 核心类 |
|------|--------|
| `context/` | ContextManager, SessionManager |
| `workflow/` | WorkflowOrchestrator, Cache |
| `hooks/` | AutoOptimizeHook |
| `feedback/` | FeedbackCollector |
| `utils/` | RateLimiter |
| `requirements/` | RequirementsTraceability |
| `testing/` | AIRunner |
| `bootstrap.py` | 初始化逻辑 |
| `ai_friendly.py` | AI友好接口 |

### P1.5 REST API 版本号不同步

`lingflow-api/app/main.py:80` 返回 `"version": "1.0.0"`，与主项目 `3.8.0` 不一致。

### P1.6 CORS 通配符

`lingflow-api/app/main.py:26`: `allow_origins=["*"]`，无机制阻止带通配符部署。

---

## P2 — 代码质量 (5项)

### P2.1 22处用户文档版本号过时（v3.7.0）

| 关键文件 | 行号 |
|----------|------|
| `README.md` | 97 |
| `docs/quickstart.md` | 23 |
| `docs/index.md` | 126 |
| `docs/PYPI_PUBLISHING_GUIDE.md` | 1 |
| `mcp_server/README.md` | 3 |
| `actions/quality-gate/README.md` | 152 |
| *(另有16处)* | |

### P2.2 agents.json 双格式维护

`agents/agents.json`（V1）和 `agents/agents.v2.json`（V2）共存，adapter 优先读 V2。

### P2.3 Phase 5 `__init__.py` 注释掉的导出

`lingflow/self_optimizer/phase5/__init__.py` 约40行核心代码被注释。

### P2.4 `compress_context` API 签名不一致

| 位置 | 签名 |
|------|------|
| `lingflow/__init__.py` | `compress_context()` 无参 |
| `lingflow/context/manager.py` | `compress_context(role, content, is_important)` 3参数 |

### P2.5 REST API 2个 TODO

| 行号 | 内容 |
|------|------|
| 37 | `TODO: 实现实际的 API Key 验证逻辑` |
| 173 | `TODO: 保存结果到 Redis 或数据库` |

---

## P3 — 低影响 (3项)

| # | 问题 | 说明 |
|---|------|------|
| P3.1 | 68处历史报告版本号过时 | `docs/reports/` 下，不影响功能 |
| P3.2 | `scripts/archive/` 存档脚本 | 已归档，增加仓库体积 |
| P3.3 | `.lingflow/params/` 运行时文件被 Git 跟踪 | 应加入 `.gitignore` |

---

## 汇总

| 等级 | 数量 | 预估修复时间 |
|------|------|-------------|
| P0 | 4 | 2-3h |
| P1 | 6 | 4-6h |
| P2 | 5 | 2-3h |
| P3 | 3 | 1h |
| **合计** | **18** | **9-13h** |

### 建议修复顺序

```
P0.3 bootstrap 版本     → 5分钟
P0.4 track_context      → 15分钟
P0.2 硬编码密钥         → 15分钟
P0.1 API 端点崩溃       → 1-2小时
P2.1 文档版本号         → 30分钟（批量替换）
P1.5 API 版本号同步     → 15分钟
P1.1 配置系统           → 2小时（需设计讨论）
```
