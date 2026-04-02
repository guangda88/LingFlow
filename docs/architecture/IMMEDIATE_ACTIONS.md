# LingFlow 生态演进 - 立即行动清单

**基于**: 《LingFlow 生态架构演进白皮书》
**日期**: 2026-04-02
**状态**: 执行中

---

## ✅ 已完成（基于白皮书建议）

### 1. 技能索引仓库（第一阶段：轻量级）
- ✅ 创建 `/home/ai/lingflow-skills-index`
- ✅ 定义 `skill.yaml` Schema（JSON Schema 格式）
- ✅ 实现扫描脚本 `scripts/scan.py`
- ✅ GitHub Action 自动更新 workflow
- ✅ README 和使用文档

**架构决策**:
- 采用 **GitHub + JSON 索引**（白皮书建议）
- 不自建平台，验证生态活力
- 利用 GitHub 社交优势

### 2. 两周冲刺计划
- ✅ 调整为务实 MVP（之前 14 周太激进）
- ✅ 聚焦 3 个核心任务：
  1. REST API MVP
  2. GitHub Action `quality-gate`
  3. 技能市场索引

### 3. 技术决策记录（ADR）
- ✅ ADR-001: 技能市场采用 GitHub 索引
- ✅ ADR-002: Web 设计器选择 React Flow
- ✅ ADR-003: 告警系统使用 Prometheus
- ✅ ADR-004: 任务队列分两阶段

---

## 🎯 本周行动（Week 1）

### 优先级 1: GitHub Action `quality-gate`（白皮书：首要突破口）

**为什么优先**：
- CI/CD 是开发者高频场景
- 能快速提升 LingFlow 可见度
- 复用 Docker 镜像，实现简单

**任务**:
```
□ 创建 actions/quality-gate/ 目录
□ 编写 action.yml（Docker 运行）
□ 实现 PR 评论功能（entrypoint.sh）
□ 在私有仓库测试
□ 发布到 GitHub Marketplace
```

**预期时间**: 1 天

---

### 优先级 2: REST API 核心端点（白皮书：接入层先行）

**只实现 8 个核心端点**（白皮书建议）:
```python
# 技能系统（4 个）
GET    /api/v1/skills
GET    /api/v1/skills/{name}
POST   /api/v1/skills/{name}/execute
POST   /api/v1/skills/batch

# 工作流（2 个）
GET    /api/v1/workflows
POST   /api/v1/workflows/{id}/run

# 代码审查（1 个）
POST   /api/v1/review

# 情报系统（1 个）
GET    /api/v1/intelligence/github
```

**关键简化**（白皮书建议）:
- ✅ 工作流用**同步模式**（暂不异步）
- ✅ 任务队列用**内存队列**（暂不用 Redis）
- ✅ 认证用**API Key**（暂不 JWT）

**预期时间**: 2 天

---

### 优先级 3: 技能索引公开

**任务**:
```
□ 在 GitHub 创建 lingflow/skills-index 组织
□ 推送 index.json 和扫描脚本
□ 配置 GitHub Action
□ 创建第一个示例技能仓库
□ 更新 CLI 支持 search/install 命令
```

**预期时间**: 1 天

---

## 📅 下周行动（Week 2）

### Day 6-7: 完善与测试
```
□ 添加 /metrics 端点（Prometheus 格式）
□ 编写 5 个集成示例
□ 完整的 OpenAPI 文档
□ 错误处理和日志
```

### Day 8-9: 公开发布
```
□ REST API 部署到 Railway
□ Docker 镜像推送到 Docker Hub
□ GitHub Action 发布到 Marketplace
□ 技能索引仓库公开
```

### Day 10: 宣发
```
□ 更新主 README（4 种使用方式）
□ 发布技术文章（白皮书建议）
□ 准备 demo 视频
```

---

## 📊 成功指标（白皮书标准）

### 技术指标
- ✅ REST API 响应时间 < 200ms (P95)
- ✅ Docker 镜像大小 < 200MB
- ✅ 所有端点可手动测试

### 社区指标
- ✅ GitHub Action 被 10+ 仓库使用
- ✅ 技能市场有 5+ 贡献技能
- ✅ GitHub Stars 增长 50%

---

## 🔧 技术栈确认（白皮书建议）

| 模块 | 技术选型 | 理由 |
|------|----------|------|
| REST API | FastAPI | 轻量、异步、自动文档 |
| 容器 | Docker（多阶段） | 多用途、体积小 |
| 任务队列 | 内存队列 | Phase 1 先简单，Phase 3 再 Celery |
| 告警 | Prometheus 导出 | 不自研，用成熟方案 |
| 工作流设计器 | React Flow | 与 YAML 对齐，不用 Node-RED |
| 技能市场 | GitHub + JSON | 轻量级，零运维 |

---

## 🤝 需要您的决策

### 1. 技能索引仓库位置
**选项 A**: 在主组织下 `lingflow/skills-index`
**选项 B**: 独立组织 `lingflow-skills`

**建议**: A（简化管理）

### 2. GitHub Action 账号
需要发布到 GitHub Marketplace，是否使用 `lingflow` 组织账号？

### 3. REST API 部署
**选项 A**: Railway（推荐，简单）
**选项 B**: Render
**选项 C**: AWS ECS

**建议**: A（快速验证）

### 4. 技能市场域名
**选项 A**: 使用 GitHub Pages（lingflow.dev/skills）
**选项 B**: 独立域名

**建议**: A（零成本）

---

## 📝 学习与调整

基于白皮书反馈，我已经纠正了：

### 之前的错误
1. ❌ 14 周计划太长 → ✅ 2 周 MVP
2. ❌ 技能市场想自建 → ✅ GitHub 索引
3. ❌ 告警想自研 → ✅ Prometheus
4. ❌ Web 设计器考虑 Node-RED → ✅ React Flow
5. ❌ 忽略 GitHub Actions → ✅ 首要突破口

### 保留的正确
1. ✅ REST API 是桥梁
2. ✅ Docker 多用途
3. ✅ 分层架构
4. ✅ 优先级划分

---

## 🚀 下一步行动

**我建议立即开始**（按白皮书优先级）：

1. **今天**：完成 GitHub Action `quality-gate`
   ```bash
   cd actions/quality-gate
   # 我已经创建了基础结构
   ```

2. **明天**：完成 REST API 8 个核心端点
   ```bash
   cd lingflow-api/app
   # 聚焦核心，不扩展
   ```

3. **后天**：公开技能索引仓库
   ```bash
   # 推送到 GitHub
   ```

**您希望我优先完成哪个？**
- A. GitHub Action（1 天，最快见效）
- B. REST API 核心端点（2 天，基础设施）
- C. 技能索引公开（1 天，生态启动）
- D. 其他？

---

**基于白皮书的务实方案**

*"众智混元，万法灵通"*
