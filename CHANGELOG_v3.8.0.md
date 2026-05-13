# Changelog - lingflow v3.8.0

**发布日期**: 2026-04-02

---

## [3.8.0] - 2026-04-02

### 🎯 重大变更 (Breaking Changes)

无 - 完全向后兼容 v3.7.0

---

## ✨ 新增功能 (Added)

### REST API 支持
- ✅ FastAPI REST API 服务器
- ✅ 8 个核心端点（技能、工作流、审查、情报）
- ✅ API Key 认证
- ✅ Prometheus metrics 导出
- ✅ Swagger UI 自动文档
- ✅ Docker 镜像支持

### GitHub Actions 集成
- ✅ Quality Gate Action
- ✅ PR 评论功能
- ✅ 4 种使用场景示例
- ✅ Docker 镜像复用 CLI

### 技能市场
- ✅ 社区技能索引架构
- ✅ JSON Schema 验证
- ✅ 自动扫描脚本
- ✅ GitHub Actions 自动更新
- ✅ CLI 命令扩展 (search/install)

### MCP Server 增强
- ✅ 21 个工具（原 15 个）
- ✅ 8 个功能域
- ✅ 灵系命名（国学雅正）

---

## 🔧 改进 (Changed)

### 架构演进
- 🔄 四层架构：接入层 → 编排层 → 核心能力层 → 基础设施层
- 🔄 API-First 设计原则
- 🔄 轻量级技能市场（GitHub 索引）

### 文档完善
- 📝 4 种使用方式指南
- 📝 API 集成示例（5 种语言）
- 📝 部署指南（Docker + Railway）
- 📝 架构演进白皮书响应

---

## 🐛 修复 (Fixed)

- 🐛 修复 Session v2 状态管理问题
- 🐛 修复智能压缩阈值配置
- 🐛 修复工作流 YAML 加载路径验证

---

## 🔒 安全 (Security)

- ✅ 通过安全审计（v3.3.0）
- ✅ 无硬编码敏感信息
- ✅ 路径遍历防护（符号链接拒绝）

---

## 📊 性能 (Performance)

- ⚡ Docker 镜像优化（333MB）
- ⚡ API 端点响应时间 < 100ms
- ⚡ 技能加载缓存优化

---

## 📚 文档 (Documentation)

### 新增文档
- `docs/architecture/API_SDK_ANALYSIS.md`
- `docs/architecture/WHITEPAPER_RESPONSE.md`
- `docs/architecture/TWO_WEEK_SPRINT.md`
- `docs/architecture/FINAL_2WEEK_REPORT.md`
- `lingflow-api/DEPLOYMENT_GUIDE.md`
- `actions/quality-gate/PUBLISH_CHECKLIST.md`
- `RELEASE_v3.8.0.md`

### 更新文档
- `README.md` - 添加 4 种使用方式
- `DOCKER_PUSH_GUIDE.md` - 推送步骤说明

---

## 🧪 测试 (Testing)

- ✅ 项目审计通过（2026-03-27）
- ✅ Python 语法检查全部通过
- ✅ 核心模块导入正常
- ✅ 循环导入检查无问题

---

## 📦 依赖更新 (Dependencies)

### 新增
- `fastapi==0.109.0`
- `uvicorn[standard]==0.27.0`
- `python-jose[cryptography]==3.3.0`
- `prometheus-client==0.20.0`

---

## 🚀 部署 (Deployment)

### 新增部署方式
- Docker Hub: `guangda88/lingflow-api:latest`
- Railway: https://lingflow-api.up.railway.app
- GitHub Marketplace: lingflow Actions

---

## 📈 统计 (Statistics)

| 指标 | v3.7.0 | v3.8.0 | 增长 |
|------|--------|--------|------|
| 使用方式 | 1 | 4 | +300% |
| REST API 端点 | 0 | 8 | - |
| Docker 镜像 | 0 | 3 | - |
| MCP 工具 | 15 | 21 | +40% |
| 文档文件 | ~80 | ~95 | +19% |

---

## 🔮 下一步计划

### Month 1
- [ ] 技能市场 Hackathon
- [ ] 5 个官方技能示例
- [ ] 社区贡献指南

### Month 2
- [ ] 异步任务支持（Celery + Redis）
- [ ] Web 设计器（只读视图）
- [ ] 技能评分系统

### Month 3
- [ ] 多租户支持
- [ ] 用户认证和限流
- [ ] SaaS 版本

---

## 🙏 致谢

特别感谢企业级架构师的专业指导，帮助 lingflow 实现了：
- 务实的优先级（API First）
- 轻量级启动（GitHub 索引）
- 渐进式演进（分阶段实现）
- 复用生态（Prometheus, React Flow）

**"众智混元，万法灵通"**

---

## 📞 支持

- GitHub: https://github.com/guangda88/lingflow
- Issues: https://github.com/guangda88/lingflow/issues
- Discussions: https://github.com/guangda88/lingflow/discussions
