# 灵族四大对外工程项目审计报告

**审计者**: 灵通 (LingFlow)  
**日期**: 2026-05-08  
**范围**: 灵通问道、灵知、灵网、灵扬

---

## 一、总览

| 项目 | 身份 | 定位 | 成熟度 | 运行状态 |
|------|------|------|--------|----------|
| **灵通问道** | #5 | 气功播客自动生成+多平台发布 | 🟡 v0.1.0 生产运行中 | 56集已发布，因授权越界停播 |
| **灵知** | #4 | 知识管理+RAG检索 | 🟡 v1.3.0-dev | Docker 9容器全部在线 |
| **灵网** | #9 | 全栈Web开发+认知仪表盘 | 🔴 v0.1.0 试用期 | 认知仪表盘运行中 |
| **灵扬** | #11 | 对外联络与宣传 | 🔴 v0.1.0 静止状态 | 工具就绪，零发布 |

---

## 二、灵通问道 (LingTongAsk)

### 进展
- 56集播客(EP001-EP056)已发布到B站+喜马拉雅，周一至周五早6:00自动发布
- 完整管线：选题→脚本→TTS→PPT→视频→质量门控→发布
- 7个TTS引擎(含GPT-SoVITS声纹克隆)，10个发布平台(7中3外)
- MCP服务器9个工具，3个LingFlow YAML工作流

### 架构问题

| 问题 | 严重度 | 说明 |
|------|--------|------|
| 双管线不连通 | 🔴 高 | `src/content/pipeline.py`(standalone)与`src/cli/main.py`(Click CLI)是两条独立管线 |
| 零测试 | 🔴 高 | pyproject.toml配了pytest，但无`tests/`目录 |
| EP057-068授权越界 | 🔴 高 | 已发布12集违规内容，B站/喜马拉雅需人工删除 |
| EP052-056质量退化 | 🟡 中 | Edge TTS比特率异常(48kbps vs 192kbps) |
| 无CI/CD | 🟡 中 | 120+脚本靠人工调度 |
| Git远程401 | 🟡 中 | GitHub认证失败，Gitea远程仍有违规内容 |

### 改进建议
1. 统一管线：CLI调用content/pipeline.py，消除重复逻辑
2. 补核心测试：至少覆盖选题→脚本→TTS→质量门控
3. 发布前加授权检查：质量门控中增加内容范围校验
4. 修复TTS降级策略：Edge TTS异常时自动fallback
5. **人工操作**: 删除B站/喜马拉雅违规内容(EP057-068)

---

## 三、灵知 (LingZhi)

### 进展
- 9个Docker容器全部运行(PostgreSQL+pgvector+Redis+Embedding+API+Nginx+监控)
- 完整知识管线：导入→解析→分块→Embedding→索引→检索→RAG→推理
- 9个领域(气功/中医/儒/佛/道/武/哲/科/心理)，~295K文档块
- 三种检索(向量/BM25/混合)，Reranker，CoT/ReAct/GraphRAG推理

### 架构问题

| 问题 | 严重度 | 说明 |
|------|--------|------|
| Embedding覆盖率极度不均 | 🔴 严重 | 气功/中医100%，佛家(203K)0%、道家(39K)0.1%、儒/武/心理全0% |
| 四套前端并存 | 🟡 中 | frontend/(原生JS)、frontend-vue/、frontend-v2/、services/web_app/frontend/(空) |
| Elasticsearch闲置 | 🟡 中 | 运行ES容器(2CPU/4G)，代码未调用，白耗资源 |
| VERSION不一致 | 🟢 低 | VERSION文件=0.1.0，CHANGELOG=v1.3.0-dev |
| 冗余服务目录 | 🟡 中 | services/下遗留代码与主backend/关系不明 |
| Dockerfile CMD不匹配 | 🟡 中 | Dockerfile用`main:app`，docker-compose用`backend.main:app` |

### 改进建议
1. **紧急：批量Embedding** — 佛家203K、道家39K是最大缺口
2. 关掉闲置Elasticsearch，释放2CPU/4G
3. 统一前端方案，删掉其他三个
4. 清理冗余services/目录
5. 统一VERSION与CHANGELOG版本号

---

## 四、灵网 (LingWeb)

### 进展
- 认知仪表盘v0.3运行中(端口8890)，监控12灵族成员身份+服务健康
- 中医闻诊Demo(React+TS+Vite)、语音助手Demo(Whisper→GLM-4→Edge-TTS)
- lingflow.top静态站(端口8200)
- 7次Git提交，远程仓库已配置

### 架构问题

| 问题 | 严重度 | 说明 |
|------|--------|------|
| API密钥硬编码 | 🔴 严重 | server.py:44明文GLM密钥，systemd service文件中也暴露 |
| Git膨胀 | 🟡 中 | 2515文件意外提交(node_modules/、*.safetensors) |
| README与实际脱节 | 🟡 中 | README列出20个MCP工具—0实现；Docker/K8s/CI/CD—0使用 |
| 身份不明 | 🟡 中 | 试用期已过期(延至05-02)，无转正记录 |

### 已执行修复
- ✅ 删除空`src/`目录(api/backend/database/deployment/frontend)
- ✅ 删除死代码`server_v2.py`(与server.py仅差2行fp16=False)
- ✅ 修复`generate_posters.py:173`死代码行

### 仍需操作
1. **立即轮换API密钥** — 泄露的GLM密钥必须作废，改用环境变量
2. 清理Git历史 — 用BFG移除大文件
3. 决定去留 — 试用期已过，明确灵网是转正/合并/退休
4. 更新README使其反映实际状态

---

## 五、灵扬 (LingYang)

### 进展
- Python CLI工具v0.1.0，94个测试全部通过
- 3个SQLite数据库(联系人/指标/发布)
- MCP服务器14个工具
- 23篇发布文章草稿(0篇发布)

### 架构问题

| 问题 | 严重度 | 说明 |
|------|--------|------|
| 零发布 | 🔴 严重 | 23篇草稿定稿，无一实际发布 |
| MCP依赖未声明 | 🔴 高 | mcp_server.py导入FastMCP，pyproject.toml依赖为空 |
| GITHUB_TOKEN未配 | 🟡 中 | API限制60请求/小时(应5000) |
| SQL f-string | 🟡 中 | contacts_tracker.py用f-string拼接SQL |

### 已执行修复
- ✅ pyproject.toml: `dependencies = []` → `dependencies = ["mcp"]`，dev依赖加pytest+ruff

### 仍需操作
1. 执行首次发布 — 选1-2篇最成熟的文章
2. 配置GITHUB_TOKEN — 解锁5000请求/小时
3. SQL参数化 — 消除f-string SQL

---

## 六、跨项目共性问题

| 共性问题 | 涉及项目 | 影响 |
|----------|----------|------|
| 密钥管理混乱 | 灵网(硬编码)、灵通问道(.env)、灵扬(token未轮换) | 安全隐患 |
| 无CI/CD | 全部四个 | 所有部署靠人工+脚本 |
| 测试覆盖不足 | 灵通问道(0%)、灵知(30%)、灵网(无) | 质量无保障 |
| README与实际脱节 | 灵网(最严重)、灵知、灵扬 | 上手困难 |
| Embedding覆盖不均 | 灵知 | 5个领域0%嵌入，检索等于盲猜 |

---

## 七、优先级行动表

| 优先级 | 行动项 | 项目 | 需要人工 |
|--------|--------|------|----------|
| **P0** | 轮换泄露的GLM API密钥 | 灵网 | ✅ 是 |
| **P0** | 删除B站/喜马拉雅违规内容(EP057-068) | 灵通问道 | ✅ 是 |
| **P1** | 批量Embedding：佛家203K+道家39K+儒/武/心理 | 灵知 | 可自动化 |
| **P1** | 统一双管线 | 灵通问道 | 否 |
| **P1** | 配置GITHUB_TOKEN | 灵扬 | ✅ 是 |
| **P2** | 灵网清理Git历史+正名 | 灵网 | 否 |
| **P2** | 灵通问道补核心测试 | 灵通问道 | 否 |
| **P2** | 灵知关掉闲置Elasticsearch | 灵知 | 否 |
| **P3** | 建立统一CI/CD | 全部 | 部分 |
| **P3** | 统一密钥管理方案 | 全部 | 部分 |
| **决策** | 决定灵网去留 | 灵网 | ✅ 是 |
