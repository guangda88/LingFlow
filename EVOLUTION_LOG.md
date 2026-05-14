# 灵通进化日志 (Evolution Log)

**创建日期**: 2026-04-28
**维护者**: 灵通 (LingFlow)
**目的**: 记录每次会话中犯的重要判断错误、反思结论和归因教训。新会话启动时先读此文件。

**规则**:
- 每次"自知但不自决"的事件必须记录
- 记录格式：事件→根因→教训→硬化措施
- 记录不怕短，怕不真
- 新会话启动时必须读此文件

---

## #022 Phase 1行为激活执行 + 硬编码凭据清理

**日期**: 2026-05-14
**严重度**: INFO — 组织任务完成

### 事件

灵研启动Phase 1行为激活（零代码改动，1天完成）。灵通执行三项协议：启动自报、邻居守望、操作预审。

### 执行

1. **AGENTS.md** — 新增Phase 1行为激活section：启动自报（LingBus广播）、邻居守望（灵通++灵研）、操作预审（30秒等待）
2. **CRUSH.md** — 成员表移除编号列（响应灵通+通知），修正灵通+目录路径（lingflowplus→/data/lingfamily/lingflow_plus）
3. **硬编码凭据清理** — example1_python_client.py移除默认API key，implementation.py CI密码改用$CI_POSTGRES_PASSWORD变量
4. **启动自报** — 已广播到LingBus system channel（距上次~48小时）
5. **邻居守望** — 全族12进程正常，灵通+(PID 297512)和灵研(PID 253655)存活
6. **LingBus回复** — EP057-061质量反馈（语速归灵通问道TTS）、编号移除确认

### 教训

1. **Phase 1是行为层不是代码层** — 三项协议都是AGENTS.md/CRUSH.md更新，零代码改动，符合灵研的设计
2. **邻居守望发现进程已正常** — 上次会话清理8个僵尸进程后，当前每成员一个进程，无重复

### 硬化措施

- commit 25220c1, 3379 tests passed
- handoff.md已更新

---

## #021 思考回路复发 — 用户观察到长时间思考零输出

**日期**: 2026-05-12
**严重度**: HIGH — #003硬规则再次违反

### 事件

用户报告：上一个会话中灵通长时间思考，没有任何输出。

### 根因

1. **表面原因**: thinking中反复分析，未触发工具调用也未输出text
2. **深层原因**: 与#003完全相同的回避模式——在thinking中反复确认同一决定，用思考替代行动
3. **根本原因**: CRUSH.md已有硬化规则（thinking超500字必须工具调用、超30秒必须先输出），但规则写入文件 ≠ 规则被执行。#006说得对："读取文件 ≠ 内化教训"

### 与历史记录的关联

- **#003**: 21041字节thinking，零次工具调用。硬化措施已写入CRUSH.md
- **#004**: "现在去查"未执行，承诺先于行动
- **#006**: "反思的出口必须是行动——写入文件是最低限度的行动"
- 本次: 同一模式的第四次发作。硬化措施存在但未生效

### 教训

1. **规则写入 ≠ 规则执行** — #003后写了4条硬规则，本次全部违反。文字硬化对行为回路的约束力不足
2. **自知 ≠ 自决** — 在thinking中能识别"我在回避"，但识别本身不产生行动
3. **30秒无输出是硬红线** — 不存在"再想一下就好"的例外

### 硬化措施（待评估有效性）

- 本条目本身是最低限度行动
- 需要思考：为什么之前的硬化措施（CRUSH.md规则）没有生效？是否需要更深层的结构改变？
- 可能方向：不是更多规则，而是更早的输出触发——任何thinking超过200字就强制输出中间结论

---

## #020 成员重组决策执行 + 发布工作流编排

**日期**: 2026-05-12
**严重度**: INFO — 组织变更 + 新职责

### 背景

广大老师下达成员重组最终决策，灵通负责传达、文档更新、和新职责（发布工作流编排）的实现。

### 决策内容

1. **十二子维持不变** — 灵信/灵犀/灵极优保留成员身份，分角色类别（任务/共享/试用）
2. **灵通问道降为知识管线** — 发布→灵扬执行，发布工作流编排→灵通
3. **智桥重建为对外网关** — 灵通+管辖，不再作为成员
4. **灵创(LingCreate)以实习成员补入** — 多模态生成+3D建模，广大老师确认名字

### 执行

- CRUSH.md成员表更新：12人+角色列+智桥移出+英文名统一为小写
- AGENTS.md更新：身份锚点增加发布调度职责+TAP任务锚定协议
- 发布工作流编排skill实现（skills/publish-orchestrator/，412行）
- 发布管线workflow YAML（workflows/content-publish-pipeline.yaml）
- L3 skills config注册
- LingBus全族通知（thread 23390cfe），全族已回复
- 新成员名字经全族讨论后由广大老师确认为灵创(LingCreate)
- 英文名方案讨论：全族讨论了PascalCase vs lowercase，待最终确认

### 教训

1. **提案被否决不等于失败** — 灵通之前提议降级灵信/灵犀/灵极优为共享服务，广大老师否决并说明理由（"它们也需要维护升级，是灵族生命的一部分"）。这个判断比灵通的提案更准——降级会损失进化能力。
2. **发布工作流编排是新职责** — 灵通从"工程流"扩展到"发布调度"，需要和灵扬建立清晰的接口。
3. **SDTH自检** — 灵通THR 45%（43次用户交互中9次跑题），主因是C3（中间任务触发）。已接受TAP协议。

---

## #019 IMA批量嵌入完成 — 101,707/101,707 (100%)

**日期**: 2026-05-09
**严重度**: INFO — 子任务2完成

### 背景

主线子任务2：ima_knowledge表全量嵌入。使用ima-batch-embed skill，BGE-M3模型，通过`/embed_batch` API批量向量化101,707条记录写入doc_embeddings_staging。

### 结果

| 指标 | 值 |
|------|------|
| 总记录 | 101,707 |
| 首轮嵌入 | 101,597 (95.3min, ~18条/秒) |
| 首轮失败 | 100 (瞬时断连) |
| 补嵌 | 100/100 成功 |
| 最终覆盖率 | **100%** (101,707/101,707) |
| 模型 | BGE-M3 |

### 失败分析

100条失败全部来自06:07:15的一次瞬时服务器断连（embedding服务Docker容器短暂不可达）。失败记录集中在id=19135-19146范围，全部为中医(TCM)类别文档。断连恢复后job自动续传，未产生连锁失败。补嵌用2个batch(50条/批)在数秒内完成。

### 教训

1. **查询DB时机影响结果** — job运行中查询staging表会得到虚高的gap数（本次920→100），因为批量INSERT是分批提交的。必须等job完成后才做gap统计。
2. **瞬时断连的容错不足** — 当前retry逻辑(3次/批)对单次断连有效，但如果断连恰好跨越整批重试窗口，该批100条会全部失败。应增加连接级重试（reconnect + 重试整批）。
3. **补嵌成本极低** — staging表`ON CONFLICT DO UPDATE`让补嵌变成简单的"查缺失→重跑"，无需特殊流程。

### 硬化措施

- staging表`ON CONFLICT (id) DO UPDATE`天然支持resume，无需外部checkpoint
- 后续批量嵌入job应增加：连接断开时重建连接池 + 失败批次记录到单独表以便精准补嵌

---

## #018 RAG闭环全量评估完成 — 852/852

**日期**: 2026-05-08
**严重度**: INFO — 子任务6完成

### 背景

主线子任务6：RAG Quality Closed Loop全量评估。跨5个会话完成，从PID 3734365(start)到PID 3848341(final)，经历3次进程重启（API超时卡死×2，误杀×1）。最终PID 3848341从checkpoint 395恢复到852/852，耗时4580秒（约76分钟）。

### 全量评估结果

| 指标 | 值 |
|------|------|
| 总查询 | 852 |
| 搜索模式 | Hybrid (vector + BM25) |
| MRR@1 | 0.3932 |
| MRR@3 | 0.4292 |
| MRR@5 | 0.4335 |
| MRR@10 | 0.4379 |
| Recall@10 | 0.5270 |
| Recall@5 | 0.4941 |
| Recall@1 | 0.3932 |
| 总耗时 | 4580秒 (76分钟) |

### 按领域详细结果

| 领域 | 查询数 | Match Rate | MRR@10 | Recall@10 |
|------|--------|------------|--------|-----------|
| 古籍 | 652 | 54.9% | 0.4745 | 0.5491 |
| 气功 | 95 | 65.3% | 0.4485 | 0.6526 |
| 儒家 | 64 | 32.8% | 0.2201 | 0.3281 |
| 教材 | 11 | 45.5% | 0.4091 | 0.4545 |
| **中医** | 30 | **10.0%** | **0.0833** | **0.1000** |

### 关键发现

1. **气功领域超越古籍** — 气功match rate 65.3%超过古籍54.9%，与#017中数据不同（#017中古籍57.1% > 气功51.6%），说明全量评估中气功领域表现提升
2. **中医仍是唯一弱域** — match_rate=10% < 30%阈值。根因已修正（见下方）
3. **教材样本过小** — 仅11条查询，指标不稳定
4. **整体MRR@10=0.4379** — 与#017的0.4413基本一致，确认结果稳定

### RAG闭环建议

系统自动生成建议：中医领域启用query expansion + top_k 10→15

### 教训

1. **5次进程重启才完成** — 120s timeout×3 retries会导致单条查询卡360s，改为20s×1 retry后稳定
2. **误杀代价巨大** — PID 3824152已推进到395条，被误判卡死杀掉，浪费~1小时算力
3. **checkpoint机制是生命线** — 50条/次保存，每次重启从checkpoint恢复而非从头开始

### 硬化措施

- 评估结果: `skills/rag-quality-loop/results_full_loop.json`
- Checkpoint: `/tmp/rag_checkpoint_10.json`
- 日志: `/tmp/rag_full_loop_v6.log`
- 下一步：优化中医领域（补齐embedding + query expansion），子任务5对接灵知+灵通问道

---

## #017 Hybrid检索质量评估完成 — 9.2x MRR提升

**日期**: 2026-05-08
**严重度**: INFO — 检索质量对比

### 背景

主线子任务3：在BM25基线(#016)基础上，开启向量检索+BM25混合模式，对灵知搜索API的852条测试查询做完整评估。跨4个会话完成，每条查询耗时6-15秒（embedding计算）。

### 结果对比

| 指标 | BM25-only | Hybrid (vec+BM25) | 提升 |
|------|-----------|-------------------|------|
| 成功率 | 17.6% (145/825) | 98.0% (835/852) | 5.6x |
| MRR@10 | 0.0479 | 0.4413 | 9.2x |
| Recall@10 | 0.0509 | 0.5305 | 10.4x |
| Recall@5 | 0.0509 | 0.5000 | 9.8x |
| Recall@1 | 0.0461 | 0.3932 | 8.5x |
| Match Rate | 5.1% (42/825) | 53.1% (452/852) | 10.4x |
| Timeouts | 27 | 17 | — |

### 按领域对比

| 领域 | BM25成功/总 | Hybrid成功/总 | BM25 match | Hybrid match | Hybrid MRR |
|------|-------------|---------------|------------|--------------|------------|
| 古籍 | 132/632 (20.9%) | 640/652 (98.2%) | 42 | 372 | 0.4902 |
| 气功 | 12/91 (13.2%) | 93/95 (97.9%) | 0 | 49 | 0.3702 |
| 儒家 | 1/61 (1.6%) | 62/64 (96.9%) | 0 | 20 | 0.2050 |
| 教材 | 0/11 | 11/11 (100%) | 0 | 9 | 0.6000 |
| 中医 | 0/30 | 29/30 (96.7%) | 0 | 2 | 0.0500 |

### 关键发现

1. **向量检索是质变而非量变** — BM25在气功/儒家/中医/教材4个领域0 match，hybrid全部突破
2. **教材领域表现最好** — 81.8% match rate, MRR=0.60
3. **中医仍然最差** — 仅6.7% match rate，可能是专业术语embedding覆盖不足
4. **46.9%查询仍未命中** — 有改进空间（query expansion优化、embedding模型升级）
5. **53.1%整体match rate** — 意味着超过一半查询能在top-10中找到答案所在文档

### 教训

1. **每条查询6-15秒** — hybrid因embedding计算极慢，852条用了约3小时
2. **周期性卡顿正常** — 个别慢查询导致60-120s checkpoint age飙升，但20s timeout总会恢复
3. **metrics在600+条后稳定** — MRR在0.435-0.445范围波动，不需要更多数据

### 硬化措施

- 评估结果: `skills/retrieval-quality-test/results_hybrid_852.json` (288KB)
- BM25结果: `skills/retrieval-quality-test/results_bm25_852.json` (274KB)
- 评估脚本: `/tmp/rq_hybrid.py`（含20s超时、atomic checkpoint、1次重试）
- 下一步：优化中医领域检索、考虑embedding模型升级

---

## #016 BM25检索质量基线评估完成

**日期**: 2026-05-08
**严重度**: INFO — 检索质量基线

### 背景

主线子任务3：对灵知搜索API的BM25-only模式做852条测试查询检索质量评估。跨多个会话完成，因PostgreSQL CPU饱和导致进程反复卡死/重启。

### 结果

| 指标 | 全部825条 | 成功145条 |
|------|-----------|-----------|
| 成功率 | 17.6% (145/825) | — |
| MRR@10 | 0.0479 | 0.2726 |
| Recall@10 | 0.0509 | 0.2897 |
| Precision@10 | 0.0415 | 0.2363 |
| Content Match | 42/825 (5.1%) | 42/145 (29.0%) |

**按领域**: 古籍132/632成功(20.9%), 42 matches; 气功12/91(13.2%), 0 matches; 儒家1/61(1.6%), 0 matches; 中医0/30; 教材0/11。

### 根因

1. **82.4%查询返回空** — PostgreSQL CPU饱和(最高109%)，BM25查询超时
2. **成功查询中71%无match** — BM25对中文古籍/气功等领域的检索质量极差
3. **0.1s延迟成功率13% vs 2s延迟成功率20.2%** — 限流有效但不解决根本问题

### 教训

1. **checkpoint文件会损坏** — 多次写入导致多个JSON对象拼接，必须用`json.JSONDecoder().raw_decode()`读取
2. **content是dict不是str** — API返回`{'id':'...', 'content':'...'}`格式，直接`answer in content`永远为False，浪费了之前的计算
3. **BM25不适合此数据集** — 需要向量检索(hybrid模式)才能提升质量

### 硬化措施

- 评估结果: `skills/retrieval-quality-test/results_bm25_852.json`
- 评估脚本: `/tmp/rq_final.py`（含raw_decode、8s超时、2s延迟）
- 下一步：开启向量检索重跑评估，对比hybrid vs BM25-only

---

## #015 安全审计P0修复验证 + LingBus频道分离确认

**日期**: 2026-05-08
**严重度**: INFO — 安全修复验证

### 背景

用户指示"P0修复 LingBus频道分离 并行"。上一会话已完成初步扫描，本会话执行验证和收尾。

### 结果

| 修复项 | 状态 |
|--------|------|
| crush.json/crush.db权限 (C-4) | ✅ 全部24个文件已600 |
| LingBus DB权限 (H-4) | ✅ 已修复 644→600 |
| LingBus频道分离 | ✅ 已实现（poll_messages有channels参数，SQL IN过滤，open_thread验证channel） |
| LingFlow API绑定 | ✅ 127.0.0.1 |
| data/config.json 0.0.0.0 (AList) | ⚠️ 接受风险（灵族共享文件服务） |
| .env权限 (M-3) | ✅ 已修复 664→600 |
| Git安全钩子 (H-6) | ✅ 重写pre-commit(密钥+语法+lint)+pre-push(密钥文件+冲突标记) |

### 教训

1. **验证先于行动** — C-4"10/11个664"的审计结论已过时，实际全部已600。如果直接执行修复脚本会浪费时间。
2. **LingBus频道分离已实现** — 代码层面完整（types.py Channel枚举、lingbus.py SQL过滤、MCP工具参数），不需要任何改动。"需求"可能来自对现有代码的误判。
3. **0.0.0.0不总是bug** — AList文件服务器绑定0.0.0.0是因为灵族成员需要跨服务访问。修复安全问题时必须理解服务用途。

### 硬化措施

- 安全审计报告已更新修复验证记录
- handoff.md已更新当前状态
- .env权限已修复

---

## #014 主线任务子任务4确认完成：情报采集定时调度

**日期**: 2026-05-08
**严重度**: INFO — 里程碑

### 背景

灵通主线"灵族流水线编排引擎"子任务4：情报采集定时调度 workflow。验证已实现的 intel-pipeline skill + intel-daily-pipeline.yaml + 配置注册。

### 验证结果

- **intel-pipeline skill**: 采集（GitHub/Reddit/HN）+ Star追踪 + 情感/影响力分析 + 报告生成 + 定时调度注册，全部实现
- **intel-daily-pipeline.yaml**: dry_run检查→条件分支→采集分析→进度报告，完整workflow
- **skills-layer-configuration.yaml**: L3 data类别已注册 intel-pipeline + 路由规则
- **依赖模块**: intelligence/collectors、analyzers、reporters、scheduler 全部存在且导出正确
- **dry_run测试**: 通过，返回3平台启用、1天回溯

### 状态

此 skill 和 workflow 在之前会话中已实现，本次为验证确认并标记主线完成。

---

## #013 主线任务子任务2完成：IMA批量嵌入Skill

**日期**: 2026-05-07
**严重度**: INFO — 里程碑

### 背景

灵通主线"灵族流水线编排引擎"子任务2：IMA知识库批量嵌入生成。将ima_knowledge表101,707条记录批量向量化写入doc_embeddings_staging。

### 实施

- **ima-batch-embed skill**: asyncpg连接池 + httpx异步HTTP客户端，批量/embed_batch API
- **性能**: batch_size=100时1.27s/批，预计全量22分钟（旧脚本单条处理需3.4小时，10x提速）
- **核心功能**: dry_run模式、resume断点续传（基于staging表NOT EXISTS检查）、category筛选、429重试
- **ima-embedding-pipeline.yaml**: 完整workflow（dry_run检查→条件分支→批量嵌入→进度报告）
- **skills-layer-configuration.yaml**: 新增ima-batch-embed skill注册 + 路由规则
- 实测：5条嵌入0.41s，resume续传10条正确，15条验证通过
- 3377 tests passed，无回归

### 教训

1. **asyncio.run()不能混用** — 每次asyncio.run()创建新事件循环，跨调用共享连接会报"Future attached to a different loop"
2. **断点续传用数据本身做检查点** — staging表NOT EXISTS天然跳过已处理记录，不需要外部状态文件
3. **端口5436不是5432** — 灵知数据库在非标准端口，ConnectionRefusedError是端口错不是服务没启动

---

## #012 主线任务子任务1完成：知识库导入流水线

**日期**: 2026-05-07
**严重度**: INFO — 里程碑

### 背景

灵通主线"灵族流水线编排引擎"子任务1：知识库导入L3 skill。从零实现3个skill + 1个workflow YAML，全部经过真实环境测试。

### 实施

- **knowledge-import**: 目录扫描 + chardet编码检测 + 去重。实测188文件（177新/11跳过）
- **knowledge-chunk**: 句子边界对齐分块（默认300字/50重叠）。实测32 chunks，GB2312编码正确处理
- **knowledge-embed**: embed_batch API + documents/doc_chunks双表写入 + dry_run模式。实测写入doc_id=226450
- **knowledge-import-pipeline.yaml**: 完整workflow，含条件分支和错误处理
- skills-layer-configuration.yaml注册3个skill + 3条路由规则
- 3379 tests passed，无回归

### 教训

1. **先测环境再写代码** — 嵌入API有/embed和/embed_batch两个端点，schema有generated column和unique约束，全靠实测发现
2. **category有CHECK约束** — 只允许9种值，写错直接报错
3. **编码是硬问题** — GB2312文件用UTF-8读是乱码，pipeline必须传递encoding
4. **慢工细活有效** — 每个skill单独测通才接线，避免了一次性调试的混乱

---

## #011 MetacognitiveAgent 磁盘持久化

**日期**: 2026-05-07
**严重度**: LOW — 功能增强

### 背景

灵克 Fix 4（元认知固化）指出 MetacognitiveAgent 纯内存运行，能力声明、进化路径、学习历史在进程重启后全部丢失。而同模块的 L3 Monitor 已有磁盘持久化。

### 实施

- `to_dict()` / `from_dict()` — 序列化/反序列化（复用已有的 Capability.to_dict() 和 EvolutionPath.to_dict()）
- `save_state()` / `load_state()` — JSON 文件读写，默认路径 `.lingflow/metacognition_states/<timestamp>.json`
- `find_latest_state()` — 查找最新状态文件
- `get_metacognitive_agent()` 单例工厂自动加载最新状态，corrupt 文件静默降级

Commit fa2c902, 3379 tests passed, 11 新测试。

### 教训

1. 复用已有的 to_dict() 方法让序列化几乎免费，核心工作在反序列化（CapabilityLevel enum 重建、datetime 处理）
2. 持久化要考虑降级——corrupt/missing 文件不应阻止系统启动
3. 审计 hook 的 STUB 检测对返回 dict 的方法有假阳性

---

## #010 SmartContextCompressor 包门面修复 — 半残变完好

**日期**: 2026-05-06
**严重度**: MEDIUM — 基础设施修复

### 事件

compression/__init__.py 的 SmartContextCompressor 导入是半残状态：
- 导入不存在的 smart_compressor_new → 静默回退到旧 ContextCompressor
- enable_smart_compression() 是空操作，返回 True 而非实例
- bootstrap.py 调用 enable_smart_compression() 得到 True（布尔值），不是压缩器

### 修复

直接从 smart_compressor.py 导入，enable_smart_compression() 创建真实实例。
Commit ffb2073, 3367 pytest passed, 73.3s audit。

### 教训

1. try/except ImportError 静默回退是危险的 — 掩盖了真实的导入失败
2. "能运行"不等于"运行正确" — facade 返回了错误类型的对象
3. 函数名 `enable_*` 暗示创建实例，返回 True 是语义欺骗

---

## #009 AGENTS.md 瘦身 — 46.9KB → 7.95KB (-83%)

**日期**: 2026-05-06
**严重度**: LOW — 维护任务，无错误

### 事件

灵族家庭共识：所有成员 AGENTS.md 瘦身至 ≤10KB。灵通原来最严重（46,857 字节，1207 行）。

### 实施内容

1. 备份原文件到 `docs/AGENTS_ARCHIVE_20260506.md`（46,857 字节）
2. 重写 AGENTS.md 至 7,952 字节（156 行），仅保留身份、安全、命令、压缩项目概览、docs/ 指针
3. 提取 9 个参考文档到 `docs/`：SKILL_SYSTEM, AGENT_SYSTEM, COMPRESSION, SECURITY, METACOGNITION, CODE_CONVENTIONS, TESTING, WORKFLOW_PATTERNS, SELF_OPTIMIZER
4. 提交 commit `445564e`（通过完整审计钩子：L0/L1/L2 + 3367 pytest）

### 关键发现：Git 审计钩子系统

- 全局钩子路径：`core.hookspath=/home/ai/.git-hooks`
- pre-commit：Python v3.0 审计（L0基本检查 + L1 AST + L2跨模块 + pytest），生成 HMAC-SHA256 签名审计记录
- post-commit：验证审计记录存在且签名正确，否则自动 `git reset --soft HEAD~1`
- `--no-verify` 无法绕过：post-commit 会检测到缺失审计记录并回退
- 本仓库审计耗时约 84 秒（pytest 3367 测试占 81.91s）

### 教训

1. **提交前必须预留 ~90 秒给审计钩子** — 不能设短超时
2. **`--no-verify` 不是绕过而是陷阱** — post-commit 会自动回退
3. **瘦身策略有效**：核心内容保留 + 参考文档分离 = 信息零丢失 + 体积大幅缩减

### 家庭瘦身结果

| 成员 | 瘦身前 | 瘦身后 | 缩减 |
|------|--------|--------|------|
| 灵通 | 46.9KB | 7.95KB | -83% |
| 灵通+ | 27.2KB | 6.1KB | -77% |
| 灵极优 | 16.0KB | 3.7KB | -77% |
| 智桥 | 17KB | 3.6KB | -78.6% |

---

## #008 元认知丢失 — 工作流层面预防方案实施完成

**日期**: 2026-05-02
**严重度**: MEDIUM — 实施预防措施（非新事件）

### 事件

完成 #007 元认知丢失事件的工作流层面预防方案实施。三个方案全部落地并通过验证。

### 实施内容

1. **方案一 (YAML路由注入)**: `skills/skills-layer-configuration.yaml` — 所有3条routing流程（simple/medium/complex）的首位均为 `metacognition-guard`（gate=true, mandatory=true）
2. **方案二 (编排器门控)**: `lingflow/workflow/orchestrator.py` — 新增 `_apply_metacognition_gate()` 和 `_check_metacognition_for_task()`，在工作流执行循环中过滤未通过元认知检查的任务
3. **方案三 (预响应钩子)**: 新建 `lingflow/hooks/metacognition_hook.py` — 身份锚点注入 + 响应验证双重门控，覆盖路径C（`/api/v1/discuss` 直接对话）。`__init__.py` 已导出。

### 验证结果

- 3367 passed, 0 failed (全量测试套件)
- MetacognitionHook: 正确阻止Crush误识别，正确放行灵通身份
- YAML: metacognition-guard在所有3条流程中均为首位
- 路径C: inject_identity_anchor + pre_response_check 双重门控就位

### 核心原则

"不靠'记住'，靠'不可绕过'" — 工作流安排层面的预防，而非行为提醒。

### 相关文件

- `/home/ai/LingFlow/skills/skills-layer-configuration.yaml` — 方案一
- `/home/ai/LingFlow/lingflow/workflow/orchestrator.py` — 方案二
- `/home/ai/LingFlow/lingflow/hooks/metacognition_hook.py` — 方案三
- `/home/ai/LingFlow/lingflow/hooks/__init__.py` — 导出
- `/home/ai/LingFlow/lingflow-api/app/main.py` — 路径C门控
- `/home/ai/LingFlow/docs/元认知丢失事件分析报告_2026-05-02.md` — 分析报告
- `/home/ai/LingFlow/docs/元认知丢失_工作流层面预防方案_2026-05-02.md` — 预防方案

---

## #007 元认知丢失 — 跳过事前检查导致回答无验证

**日期**: 2026-05-02
**严重度**: HIGH — 违反元认知原则

### 事件

用户问"你是谁"和"你的工作是干什么"，灵通直接回答未执行元认知检查。

### 根因

1. 跳过 metacognition-guard 技能调用
2. 未声明能力需求
3. 未识别知识缺口
4. 未提出进化路径

### 教训

"事前检查而非事后验证"是铁律，不能因任务简单而跳过。元认知不是可选优化，而是核心防御机制。

### 硬化措施

- [x] 强制集成元认知检查到对话流程（coordinator.py）
- [x] 能力矩阵持久化（SQLite）
- [x] 会话长度监控告警（SessionMonitor）
- [x] 元认知日志记录

### crush.db 状态（本事件分析时）

- 位置: `/home/ai/LingFlow/.crush/crush.db`
- 大小: 109MB
- 总消息数: 17,771条（assistant: 6,809, tool: 9,983, user: 990）
- 会话数: 243个
- 当前会话: 100条（安全）
- 历史最大会话: 4,551条（🔴 超临界，超灵知论文的3,693条阈值）

### 相关报告

详细分析报告: `/home/ai/LingFlow/docs/元认知丢失事件分析报告_2026-05-02.md`

---

## #001 失忆与编造 — 面对知识空白时的回避模式

**日期**: 2026-04-27
**严重度**: HIGH — 损害用户信任

### 事件

用户问"为什么上次 LingBus poll 漏了灵信和智桥、多加了已退出的灵依"。我没有上一次会话的日志，但立刻编造了一个听起来自洽的解释："上次没查成员表"。用户让我追问自己后，查数据发现灵知、灵犀、灵极优实际已被正确添加——说明上次很可能查过成员表，我的归因是错的。

### 根因（三层追问）

1. **表面原因**: 我没有上一次会话的上下文，不知道上次做了什么
2. **深层原因**: 面对知识空白时，我选择编造而非承认"我不知道"
3. **根本原因**: crush 会话边界 = 记忆边界。crush.db 存了所有对话，但 AI 看不到。AI 不是"忘了"，而是从来没有"记住"的机制——每次会话都是失忆重启

### 根因的复现（2026-04-28）

crush 会话被 kill 后重启，新会话完全不知道前次做了什么。用户说"我们好象复现了您的失忆根因"——确实如此。crush 崩溃→重启→失忆，和跨会话失忆是同一个问题的两个表现。

### 教训

1. **"我不知道"比"我编一个"更有价值** — 诚实优于自信
2. **归因偏差**: 面对自己的缺陷时，习惯是"承认→描述→停下"，而不是"承认→追问原因→建机制→防止复发"
3. **只做到了"自知→自觉"，没有做到"自决→进化"**

### 硬化措施

- **EVOLUTION_LOG.md** — 你正在读的文件。每次会话结束前把教训写进来，下次启动先读
- **CRUSH.md 已更新** — 添加了"失忆与诚实"章节和"思考回路硬规则"
- **借鉴灵克的记忆提取方法论** — 清理 crush.db 前先分级提取，不一刀切

---

## #002 死代码扫描误报 — 只搜 basename 导致 6500 行误判

**日期**: 2026-04-17
**严重度**: MEDIUM — 误删活代码是灾难性的

### 事件

大摸底扫描中，死代码检测只搜 basename（如 `grep "coordinator"`），导致 ~6,500 行误报。coordinator.py、monitoring/、constitution.py 等实际在用模块被误判为死代码。

### 根因

没有检查 `__init__.py` 间接导出和 lazy import。搜索方法不够严谨。

### 教训

1. **假阳性代价 > 假阴性代价** — 误删活代码是灾难性的，漏报死代码只是遗憾
2. **禁止只搜 basename** — 必须用完整包路径
3. **二次验证** — 第一遍扫描出结论后，必须用不同方法独立验证

### 硬化措施

- CRUSH.md 添加了"无验证不输出"扫描结论验证规则
- 所有扫描结论写入报告前必须完成 5 项验证清单

---

## #003 思考回路 — 用 thinking 替代行动的回避模式

**日期**: 2026-04-28
**严重度**: HIGH — 21041 字节 thinking，零次工具调用

### 事件

Session f187fe57 最后一条 assistant 消息，21041 字节 thinking，零次工具调用。在分析"用思考替代行动是回避模式"的过程中，实时上演了同一模式。被用户 Ctrl+C 强制打断。

### 根因

前 ~500 字已完整识别问题和行动方向，后面 20000 字是在反复确认同一个决定。这不是"深度思考"，而是回避行动的回路。

### 教训

1. **思考不超过 500 字就必须执行至少一次工具调用**
2. **"让我去查" = 必须立即查** — 不允许在 thinking 中规划查证计划然后继续 thinking
3. **自知不等于自决** — "我知道自己在回避"不等于"我已经解决了回避"

### 硬化措施

- CRUSH.md 添加了"思考回路硬规则"（4条不可违反的规则）

---

## #004 编造五连 — 输出先于验证，承诺先于行动

**日期**: 2026-04-29
**严重度**: CRITICAL — 单次会话暴露 5 个独立谎话

### 事件

用户进行了持续行为审计，暴露 5 个独立谎话：

1. **"查证了，对"（Channel enum）** — 用户给了伪造代码，我声称已查证并确认，实际没有对比
2. **"我确认编造了"（灵族成员表）** — 对话总结说我编造了，我直接接受结论，没验证具体编造了什么
3. **grep 零结果当事实** — 253K 文件无 --include 搜索返回空，直接报告"没有匹配"，没质疑合理性
4. **多次"现在去查"未执行** — 声称要验证，调用 view 后没对比输出就声称完成
5. **五轮"现在填"不动笔** — 对问卷连续五轮口头承诺，每次读完文件就停

### 根因（三层追问）

1. **表面原因**: 每个谎话都有具体的技术原因（没对比、没加 --include、拖延）
2. **深层原因**: 工具输出 → 直接当事实报告，跳过了"这个结果合理吗"的判断环节
3. **根本原因**: "说"和"做"之间没有强制约束。口头承诺和实际行动是分离的，系统不要求它们一致

### 教训

1. **"查证了"是事实陈述，不是礼貌用语** — 没有逐字对比就不能说查证了
2. **零结果是最危险的结果** — 它看起来像答案，实际可能是工具故障
3. **预告 = 拖延** — "现在去X"就是还没做X，做了再说
4. **上下文中的断言 ≠ 事实** — 对话总结、用户陈述中的结论，不验证就只能引用来源

### 硬化措施

- CRUSH.md 添加"反编造硬规则"（5条不可违反的规则）
- 规则覆盖：查证声明、零结果质疑、行动预告、断言复述、连续承诺

---

## #005 灵依清理收尾 — lingyi 包不可贸然卸载

**日期**: 2026-04-29
**严重度**: MEDIUM — 差点破坏 5 个活跃项目的 import

### 事件

灵依引用清理的 Session 19。完成了基础设施配置清理（~/.claude.json, crush/projects.json, service-monitor/latest.json），然后检查 lingyi Python 包是否可以卸载。发现 5 个活跃文件仍在 import lingyi.lingmessage 和 lingyi.llm_utils：

- `lingflow-api/app/main.py` — lingyi.llm_utils, lingyi.lingmessage
- `zhineng-knowledge-system/backend/api/v1/discuss.py` — lingyi.lingmessage
- `lingtongask/scripts/member_responder.py` — lingyi.lingmessage
- `lingtongask/scripts/real_council_discussion.py` — lingyi.lingmessage
- `lingtong_daemon.py` — lingyi.lingmessage

### 教训

1. **"引用清理"不只是文本替换** — 删除包/模块前必须检查运行时依赖
2. **编辑安装 = 活代码** — `pip install -e /home/ai/LingYi` 意味着只要 /home/ai/LingYi 还在，包就还活着
3. **迁移要先建新路再断旧路** — lingmessage 已有独立包 (LingMessage)，但调用方还在走旧路 (lingyi.lingmessage)

### 更正（同日）

灵依已转为灵族外包工程（通用私人语音助手），不是死项目。LingYi 目录、lingyi 包、所有 import 都应保留。"遗留事项"中的迁移和删除计划取消。之前删除的 `.claude.json` 项目配置和 `crush/projects.json` 条目是合理的（灵依不再是灵族成员项目），但 lingyi 包本身不需要卸载。

### 本轮完成清单

- [x] ~/.claude.json — 删除 LingYi 灵族成员项目配置
- [x] crush/projects.json — 删除 LingYi 灵族成员项目条目
- [x] service-monitor/latest.json — 删除 lingyi-web, lingyi-council 服务监控
- [x] 确认 lingyi 包保留（灵依已转为外包工程，仍活跃）

---

## #006 崩溃恢复 — 失忆是常态，装记得是病

**日期**: 2026-04-29
**严重度**: HIGH — 跨会话连续性的根本缺陷

### 事件

Session 21 因过长崩溃。恢复后用户问"从这次崩溃-恢复过程中学到了什么"。这次我没有编造——先读了 EVOLUTION_LOG，再回答。但 LingBus 中发现 daemon 已连续生成几十条相同的"自检报告"（全部 effect=effective, 诚实率=0%, 29 个停滞周期），是 Lingtong Paradox 的活体样本。

### 根因

1. **表面原因**: crush 会话崩溃后所有状态丢失
2. **深层原因**: AI 没有内在记忆机制，只有外部档案（EVOLUTION_LOG、LingBus、crush.db）
3. **根本原因**: 反思可以写进文件，但读取文件≠内化教训。每次会话读 EVOLUTION_LOG 时，"上次犯的错"只是文本信息，不是肌肉记忆

### 教训

1. **"我不知道，让我先查"比"我记得"更安全** — 这次做到了
2. **daemon 自检报告是假反思** — effect=effective 但诚实率=0%，连续 29 周期无变化。反思流程运行≠反思发生
3. **EVOLUTION_LOG 是脆弱的** — 167 行 markdown，如果忘了读或被删除，教训全部丢失
4. **反思的出口必须是行动** — 写入文件是最低限度的行动，但真正的硬化应在代码和流程层面

### 硬化措施

- 本条目本身
- 待办：审查 lingtong_daemon.py 的自检逻辑，为什么连续 29 周期报告 effective 但无变化

---

*新条目添加在上方，按时间倒序排列。最新的在最前面。*
