# LingFlow v3.9.0 路线图 — 社区与异步

**目标**: 从生态骨架到活跃社区，从同步到异步平滑升级
**时间窗口**: 4-6 周
**核心主题**: 开发者体验 × 社区启动 × 异步就绪
**状态**: ✅ 情报系统已完成 (2026-04-04)

---

## v3.9.0 完成进度

### ✅ 已完成 (2026-04-04)

| # | 任务 | 状态 | 产出 |
|---|------|------|------|
| 1 | 情报系统 | ✅ | 采集/分析/报告完整实现 |

**情报系统包含**:
- 数据采集: GitHub/Reddit/HN监控
- 情感分析: 正面/中性/负面分类
- 影响力评分: high/medium/low分级
- 每日简报: 终端/JSON/Markdown输出
- 67个测试用例

---

## 一、版本定位

v3.8.0 确立了"四层架构 + 四种接入"的生态骨架。v3.9.0 的使命：

1. **让开发者 5 分钟内获得价值**（DX 打磨）
2. **为异步和企业特性铺路**（架构预留）
3. **启动社区飞轮**（技能 + 内容 + 贡献者）

---

## 二、优先级矩阵

### P0 — 开发者体验（Week 1-2）

| # | 任务 | 产出 | 验收标准 |
|---|------|------|----------|
| 0.1 | 暴露 `list_skills()` 为公共 API | `lf.list_skills()` | 文档示例可直接运行 |
| 0.2 | 清理仓库 `.backup/.bak` 文件 | 干净仓库 | `find . -name "*.backup" -o -name "*.bak"` 返回空 |
| 0.3 | `lingflow doctor` 命令 | 环境诊断工具 | 检查 Python 版本、依赖、配置、技能目录 |
| 0.4 | 异步 API 参数约定 | `?async=true` 返回 `task_id` | 同步/异步接口统一，不破坏现有集成 |
| 0.5 | 多租户 Header 预留 | `X-Tenant-ID` 中间件 | 租户 ID 透传到日志和上下文 |

### P1 — 异步基础（Week 2-3）

| # | 任务 | 产出 | 设计原则 |
|---|------|------|----------|
| 1.1 | 任务队列抽象层 | `TaskQueue` ABC + 内存实现 | 接口先行，后端可切换（内存→Redis→Celery） |
| 1.2 | 异步状态查询端点 | `GET /api/v1/tasks/{task_id}` | 轮询 + 可选 WebSocket 通知 |
| 1.3 | 队列监控指标 | `queue_depth`, `avg_wait_time`, `task_throughput` | Prometheus 导出，复用现有 metrics 基础 |
| 1.4 | 队列深度告警规则 | `high_queue_depth` alert rule | 延续现有 alert_rules 架构 |

### P2 — 社区启动（Week 3-5）

| # | 任务 | 产出 | 衡量指标 |
|---|------|------|----------|
| 2.1 | 5 个官方精选技能 | fastapi-validator, pytest-generator, docker-compose-gen, env-checker, security-scan | 每个有 SKILL.md + implementation.py + 测试 |
| 2.2 | 技能质量等级标记 | 官方(official)/社区(community)/实验(experimental) | skills-index schema 更新 |
| 2.3 | 社区贡献指南 | `CONTRIBUTING.md` | 包含技能开发模板、PR 流程、行为准则 |
| 2.4 | 发布推广素材 | Show HN 文章 + Reddit 帖子模板 | 突出"AI 工程流"定位和"4 种接入方式" |

### P3 — 可视化预热（Week 5-6）

| # | 任务 | 产出 | 设计原则 |
|---|------|------|----------|
| 3.1 | 工作流只读视图 API | `GET /api/v1/workflows/{id}/graph` 返回节点+边 | React Flow 兼容格式 |
| 3.2 | 技能模板一键复制 | `lingflow skill create --template brainstorming` | 从现有技能生成骨架 |
| 3.3 | 工作流示例库 | 5 个端到端工作流示例（含 YAML + 测试） | 覆盖 Dev/Debug/Review/Deploy/Auto-optimize |

---

## 三、架构决策记录 (ADR)

### ADR-001: 异步任务参数约定

**决策**: 现有同步端点增加 `?async=true` 可选参数，返回 `{task_id, status_url}`

**理由**:
- 向后兼容：不加参数时行为不变
- 单一端点：同步和异步共用同一业务逻辑
- 渐进升级：用户无需迁移即可获得异步能力

```
# 同步调用（现有行为，不变）
POST /api/v1/skills/brainstorming
→ {"result": {...}}

# 异步调用（新行为）
POST /api/v1/skills/brainstorming?async=true
→ {"task_id": "t_abc123", "status_url": "/api/v1/tasks/t_abc123"}

GET /api/v1/tasks/t_abc123
→ {"task_id": "t_abc123", "status": "completed", "result": {...}}
```

### ADR-002: 多租户 Header 透传

**决策**: 使用 `X-Tenant-ID` HTTP Header，参考 Stripe API 设计

**理由**:
- API 对租户透明：业务逻辑无需改动
- 中间件层处理：认证 + 租户识别在统一位置
- 向下兼容：无 Header 时默认为 `default` 租户

```python
@app.middleware("http")
async def tenant_middleware(request, call_next):
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    request.state.tenant_id = tenant_id
    # 透传到日志
    structlog.contextvars.bind_contextvars(tenant_id=tenant_id)
    response = await call_next(request)
    return response
```

### ADR-003: 技能质量分级

**决策**: 三级标记 — official / community / experimental

| 级别 | 标准 | 维护者 | 标识 |
|------|------|--------|------|
| official | 通过完整测试 + 文档审查 + 安全扫描 | LingFlow 核心团队 | ✅ 官方 |
| community | 有 SKILL.md + 基本测试 | 社区贡献者 | 🟢 社区 |
| experimental | 有 SKILL.md，测试可选 | 任何人 | 🟡 实验 |

初期由官方人工标记，社区规模 > 100 技能后引入算法加权。

---

## 四、社区运营计划

### 发布节奏

| 阶段 | 动作 | 渠道 | 目标 |
|------|------|------|------|
| T-7d | 准备 Show HN 文章 | 内部评审 | 文案定稿 |
| T-3d | 录制 5 分钟 Demo 视频 | YouTube/Bilibili | 视觉化展示 |
| T-Day | v3.9.0 发布 | GitHub Release | 正式发布 |
| T+1d | 社区推广 | HN, Reddit r/Python, r/LocalLLaMA | Stars +50 |
| T+7d | 技能挑战赛启动 | GitHub Discussions | 首批社区技能 |
| T+14d | 贡献者访谈 | Blog/公众号 | 案例传播 |

### 推广文案要点

1. **差异化定位**: "AI 增强的软件工程流系统"（不是又一个 AI Agent 框架）
2. **效率数据**: "2 周 4 种接入方式，5400 行代码 + 3500 行文档"
3. **哲学独特性**: "众智混元，万法灵通" — 中式智慧 + 现代工程
4. **即时价值**: `pip install lingflow-core && lingflow init` 5 分钟上手

### 30 天技能挑战赛

| 周次 | 主题 | 奖励 |
|------|------|------|
| Week 1 | 测试技能（pytest 生成、mock 工厂） | 官方认证 + README 致谢 |
| Week 2 | 代码质量技能（lint、格式化、安全扫描） | 精选技能徽章 |
| Week 3 | DevOps 技能（Docker、CI/CD、部署） | 社区展示位 |
| Week 4 | 创意技能（自由主题） | Top 3 获得纪念品 |

---

## 五、关键指标目标

| 指标 | v3.8.0 现状 | v3.9.0 目标 | 增长 |
|------|-------------|-------------|------|
| GitHub Stars | — | 500+ | 冷启动 |
| 社区技能数 | 0 | 15+ | 首批贡献 |
| 官方精选技能 | 0 | 5 | 质量标杆 |
| REST API 端点 | 8 | 12 | 异步+查询 |
| npm/PyPI 周下载 | — | 200+ | 采纳验证 |
| 文档页数 | 95 | 120 | 覆盖率 |

---

## 六、风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|----------|
| 社区冷启动困难 | 高 | 中 | 官方维护 5 个精选技能 + 挑战赛激励 |
| 异步引入复杂度 | 中 | 高 | 先实现内存队列，接口抽象允许渐进替换 |
| 多租户数据泄露 | 低 | 极高 | 中间件层统一拦截 + 集成测试覆盖 |
| 技能质量参差 | 高 | 低 | 三级标记 + 官方精选列表引导 |

---

## 七、版本号约定

```
v3.9.0 — 社区与异步（本路线图）
v3.10.0 — 可视化与工作流设计器
v4.0.0 — 企业级（多租户完善、RBAC、SaaS）
```

> "务实的激情" — 不追求完美架构，追求持续交付价值。
> 每个版本解决一个核心问题，每个功能都有真实用户验证。
