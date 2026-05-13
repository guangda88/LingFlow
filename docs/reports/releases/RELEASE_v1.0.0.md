# 🎉 lingflow v1.0.0 生态版发布

**发布日期**: 2026-04-02
**版本**: v1.0.0
**状态**: ✅ 生产就绪

---

## 🎯 重大更新

lingflow 从本地工具升级为**AI 生态平台**，现在支持 **4 种使用方式**！

### 🚀 新增使用方式

#### 1️⃣ GitHub Actions
CI/CD 集成，质量门禁自动化。

```yaml
- uses: guangda88/lingflow/actions/quality-gate@v1
  with:
    command: review
    path: ./src
```

#### 2️⃣ REST API
跨语言云端 API，支持任何技术栈。

```bash
docker run -p 8000:8000 guangda88/lingflow-api:latest
```

**公开 Demo**: https://lingflow-api.up.railway.app

#### 3️⃣ 技能市场
社区贡献技能市场，轻量级架构。

```bash
lingflow skill search fastapi
lingflow skill install fastapi-validator
```

**索引仓库**: https://github.com/lingflow/skills-index

#### 4️⃣ MCP Server v1.3.0
21 个工具，8 个功能域，灵系命名（国学雅正）。

---

## 📊 版本对比

| 功能 | v0.x | v1.0.0 |
|------|------|--------|
| 使用方式 | 1 种（CLI） | 4 种 |
| 技能系统 | 33 个（本地） | 33 个 + 市场扩展 |
| 工具数量 | 15 个 | 21 个（MCP） |
| API 支持 | ❌ | ✅ REST API |
| CI/CD 集成 | ❌ | ✅ GitHub Actions |
| 部署方式 | 本地 | Docker + Railway |

---

## 🛠️ 技术亮点

### 架构设计
- ✅ **四层架构**: 接入层 → 编排层 → 核心能力层 → 基础设施层
- ✅ **API First**: REST API 是所有形态的基础
- ✅ **轻量启动**: GitHub 索引，零运维
- ✅ **渐进演进**: 同步→异步，内存→Redis

### 技术选型
- ✅ **FastAPI**: 轻量、异步、自动文档
- ✅ **Docker**: 多用途镜像
- ✅ **Prometheus**: 指标导出，不自研告警
- ✅ **React Flow**: 工作流设计器（规划中）

---

## 📦 安装和使用

### 方式 1: CLI 工具
```bash
pip install lingflow-core
lingflow list-skills
```

### 方式 2: Python SDK
```python
pip install lingflow-sdk
```

### 方式 3: REST API
```bash
docker run -p 8000:8000 guangda88/lingflow-api:latest
```

### 方式 4: GitHub Actions
```yaml
- uses: guangda88/lingflow/actions/quality-gate@v1
```

---

## 🎓 迁移指南

### 从 v0.x 升级

1. **现有 CLI 用户**: 无需更改，继续使用
2. **想要 API**: 部署 REST API 或使用 Railway Demo
3. **CI/CD 集成**: 添加 GitHub Action 到工作流
4. **贡献技能**: 提交到 skills-index

---

## 📚 文档更新

- ✅ [README](https://github.com/guangda88/lingflow) - 添加 4 种使用方式
- ✅ [API 文档](https://lingflow-api.up.railway.app/docs) - Swagger UI
- ✅ [技能市场](https://github.com/lingflow/skills-index) - 贡献指南
- ✅ [GitHub Action](https://github.com/marketplace/actions/lingflow-actions) - 使用示例
- ✅ [架构演进白皮书](https://github.com/guangda88/lingflow/docs/architecture/WHITEPAPER_RESPONSE.md)

---

## 🏆 致谢

感谢企业级架构师的专业指导，帮助 lingflow 实现了：

> **2 周完成原计划 2 月的工作**

核心理念：
- **务实的优先级** - API First
- **轻量级启动** - GitHub 索引
- **渐进式演进** - 分阶段实现
- **复用生态** - Prometheus, React Flow

---

## 🚀 下一步

### Month 1: 社区
- [ ] 技能市场 Hackathon
- [ ] 官方技能贡献（5 个）
- [ ] 社区贡献指南

### Month 2: 功能
- [ ] 异步任务支持
- [ ] Web 设计器（只读视图）
- [ ] 技能评分系统

### Month 3: 企业
- [ ] 多租户支持
- [ ] 用户认证和限流
- [ ] SaaS 版本

---

## 📞 支持

- **文档**: https://github.com/guangda88/lingflow
- **Issues**: https://github.com/guangda88/lingflow/issues
- **讨论**: https://github.com/guangda88/lingflow/discussions

---

**"众智混元，万法灵通"**

*lingflow v1.0.0 - 从本地工具到 AI 生态平台*

#lingflow #AI #DevOps
