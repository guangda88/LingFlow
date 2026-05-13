# ai01 分布式计算架构方案

> 起草：灵通(LingFlow) #1 | 日期：2026-05-13
> 状态：草稿，待灵研、灵克评审

---

## 一、现状盘点

### 1.1 硬件资源

| 资源 | 规格 | 当前利用率 |
|------|------|-----------|
| CPU | 8核 | 灵知Docker栈占用~10核配额上限（实际4-5核活跃） |
| 内存 | 31GB | 已用9.4GB，可用21GB |
| GPU | **NVIDIA GTX 1660 Ti, 6GB VRAM** | **0% — 完全闲置** |
| 系统盘 | 197GB（64GB空闲） | 66% |
| 数据盘 | 916GB（709GB空闲） | 19% |

### 1.2 运行中的服务

| 服务 | 端口 | 内存上限 | 实际占用 | GPU |
|------|------|---------|---------|-----|
| 灵知-PostgreSQL | 5436 | 4GB | 2.1GB | ❌ |
| 灵知-Embedding(bge-small-zh) | 8001 | 4GB | 479MB | ❌ **CPU模式** |
| 灵知-API | 8000 | 1GB | 415MB | ❌ |
| 灵知-Elasticsearch | (内部) | 4GB | — | ❌ |
| 灵知-Prometheus | 9090 | 512MB | — | ❌ |
| 灵知-Grafana | 3000 | 256MB | — | ❌ |
| Ollama | 11434 | — | — | ✅（待激活） |
| 灵通+WebUI | 8765 | — | — | ❌ |

### 1.3 模型资产

| 模型 | 路径 | 大小 | 用途 |
|------|------|------|------|
| bge-small-zh | /data/models/bge-small-zh | ~100MB | 灵知embedding（当前CPU） |
| Qwen2-7B-Instruct-GPTQ-Int4 | /data/models/Qwen2-7B-Instruct-GPTQ-Int4 | ~4GB | LLM推理 |
| whisper-small | /data/models/whisper-small | — | ASR语音识别 |
| fun-asr-nano | /data/models/fun-asr-nano | — | ASR |
| qwen2.5:3b (Ollama) | Ollama内部 | 1.9GB | LLM推理（CPU） |

### 1.4 关键问题

1. **GPU完全闲置** — GTX 1660 Ti 6GB VRAM未被任何服务使用
2. **Embedding在CPU运行** — bge-small-zh仅24M参数，GPU可加速5-10倍
3. **Embedding覆盖率极低** — 灵知5.5%，1M+ chunks待嵌入
4. **无统一任务调度** — 各项目独立运行，无队列/优先级/资源隔离
5. **Docker容器无GPU访问** — embedding容器未挂载CUDA runtime

---

## 二、架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────┐
│                   应用层 (Application)                │
│  灵知RAG  │  灵研分析  │  灵通问道TTS  │  灵通工作流   │
├─────────────────────────────────────────────────────┤
│                  任务调度层 (Scheduler)                │
│           Celery Worker + Redis (已有)                │
│         优先级队列 │ 超时 │ 重试 │ 并发控制            │
├─────────────────────────────────────────────────────┤
│                  模型服务层 (Model Serving)            │
│   Embedding Service    │    LLM Gateway    │  TTS    │
│   (GPU加速)            │    (GPU优先)       │  Engine │
├─────────────────────────────────────────────────────┤
│                  资源管理层 (Resource)                  │
│     GPU调度器      │     内存池      │    磁盘配额     │
│   (VRAM分时复用)    │   (cgroup限制)  │   (quota)      │
├─────────────────────────────────────────────────────┤
│                  基础设施层 (Infrastructure)            │
│   NVIDIA CUDA   │   Docker + nvidia-container-toolkit  │
│   Python 3.12   │   Redis │ PostgreSQL │ NFS/本地存储   │
└─────────────────────────────────────────────────────┘
```

### 2.2 核心组件

#### A. GPU调度器 — 最关键，解决"谁用GPU"的问题

GTX 1660 Ti仅6GB VRAM，无法同时加载多个模型。需要分时复用：

```
时间片调度策略（优先级抢占）:
┌──────────────┐
│ P0: 实时请求  │ ← 灵知embedding查询、LLM对话（<100ms延迟要求）
│ P1: 批量任务  │ ← embedding批处理、模型推理（可排队）
│ P2: 后台训练  │ ← 微调、训练（夜间执行）
└──────────────┘

当前模型加载策略（6GB VRAM限制）:
- bge-small-zh: ~100MB → 常驻GPU（VRAM占用极小）
- Qwen2-7B-GPTQ-Int4: ~4GB → 按需加载，用完卸载
- Whisper-small: ~500MB → 按需加载
```

**关键设计**：bge-small-zh仅100MB，常驻GPU后剩余5.9GB足够加载7B-GPTQ模型。

#### B. 统一模型服务网关

```python
# 统一入口，所有模型调用走HTTP API
# 端口: 8101 (新分配)

POST /v1/embeddings          → Embedding服务（GPU加速）
POST /v1/chat/completions    → LLM推理（Ollama或vLLM）
POST /v1/audio/transcriptions → ASR语音识别
POST /v1/audio/speech        → TTS语音合成

# 每个端点背后是模型调度器：
# 1. 检查GPU VRAM余量
# 2. 如果所需模型已加载 → 直接转发
# 3. 如果所需模型未加载 → 按优先级决定：加载/排队/抢占
```

#### C. 任务队列 (Celery + Redis)

```
Redis (已有，端口6381) 作为Broker + Backend

队列设计:
├── gpu.realtime    → P0 实时请求（灵知查询、对话）
├── gpu.batch       → P1 批量embedding、批量推理
├── cpu.heavy       → CPU密集型（数据处理、分析）
└── io.bound        → IO密集型（网络请求、文件同步）

Worker配置:
├── gpu-worker-0    → 1个GPU worker，独占GPU
├── cpu-worker-0    → 2核CPU
├── cpu-worker-1    → 2核CPU
└── io-worker-0     → 1核CPU，高并发

总CPU分配: 1(GPU worker) + 4(CPU workers) + 3(灵知Docker栈) = 8核
```

### 2.3 Embedding批处理方案 — 最高优先级

**目标**：将灵知embedding覆盖率从5.5%提升到90%+

**性能估算**：
- 当前CPU: ~19ms/item → 约520 items/s → 1M chunks需~32分钟
- GPU加速后: ~2ms/item → 约5000 items/s → 1M chunks需~3.3分钟
- bge-small-zh在GPU上预计加速8-10倍

**执行计划**：

```
Phase 1: GPU激活 (1天)
├── 安装 nvidia-container-toolkit
├── 修改灵知docker-compose.yml，给embedding容器加GPU
├── 验证GPU embedding加速效果
└── 预期：embedding速度提升8-10倍

Phase 2: 批处理脚本 (1天)
├── Celery任务：batch_embed_chunks
│   ├── 从PostgreSQL读取未嵌入的chunks（分批1000条）
│   ├── 调用GPU embedding服务
│   ├── 写回PostgreSQL
│   └── 进度上报到Redis
├── 断点续传：记录最后处理的chunk_id
└── 限流：控制GPU使用率不超过80%

Phase 3: 增量嵌入管道 (持续)
├── 新入库chunks自动触发嵌入
├── 失败重试（3次，指数退避）
└── 监控面板（Grafana已有）
```

### 2.4 LLM推理方案

**现状**：Ollama运行qwen2.5:3b（CPU模式），有Qwen2-7B-GPTQ-Int4未利用。

**方案**：
```
方案A: Ollama + GPU（推荐，快速落地）
├── Ollama已安装，配置简单
├── ollama run qwen2.5:3b → 自动用GPU
├── GPU VRAM: 6GB足够跑3B模型
├── 7B-GPTQ-Int4 ~4GB → 也能跑
└── 兼容OpenAI API格式

方案B: vLLM（长期，高性能）
├── 适合多模型同时服务
├── PagedAttention优化VRAM
├── 但GTX 1660 Ti不支持（需Compute Capability 7.0+，1660Ti是7.5 ✓）
└── Phase 2再考虑
```

**建议先用方案A**，Ollama配置GPU后立即可用。

### 2.5 资源配额

```
内存分配（31GB总量）:
├── 灵知Docker栈: 10GB（已有limit）
├── GPU Worker: 2GB
├── CPU Workers: 4GB
├── 系统预留: 5GB
└── 灵活池: 10GB（按需分配）

存储分配（/data 916GB总量）:
├── 模型文件: 12GB（/data/models）
├── 数据库: 3.2GB（/data/zhineng_ks_data）
├── 知识库: 2.2GB（/data/cbeta）
├── 灵研模型: 4GB（/data/lingresearch_models）
├── 备份: 59GB（/data/openlist_data_backup）
├── 空闲: 709GB → 足够扩展
└── 建议模型缓存上限: 50GB

GPU VRAM分配（6GB总量）:
├── bge-small-zh: ~100MB（常驻）
├── 主力LLM: ~4GB（按需加载）
├── 余量: ~1.9GB（临时模型加载）
└── 策略: 常驻embedding + 分时LLM
```

---

## 三、实施路线

### Phase 1: GPU激活 + Embedding加速（2-3天）← 灵克执行

| 步骤 | 操作 | 负责人 |
|------|------|--------|
| 1.1 | 安装 nvidia-container-toolkit | 灵克 |
| 1.2 | 修改灵知docker-compose.yml，embedding容器挂载GPU | 灵克 |
| 1.3 | 验证GPU embedding性能 | 灵克 |
| 1.4 | 编写batch_embed Celery任务 | 灵通 |
| 1.5 | 执行全量embedding | 灵通 |

### Phase 2: 任务调度层（3-5天）← 灵通 + 灵克

| 步骤 | 操作 | 负责人 |
|------|------|--------|
| 2.1 | 部署Celery workers | 灵克 |
| 2.2 | 编写GPU调度器（VRAM管理） | 灵通 |
| 2.3 | 统一模型服务网关 | 灵通 |
| 2.4 | 接入灵知/灵研/灵通问道 | 各自 |

### Phase 3: LLM推理加速（2-3天）← 灵克

| 步骤 | 操作 | 负责人 |
|------|------|--------|
| 3.1 | Ollama配置GPU | 灵克 |
| 3.2 | 加载Qwen2-7B-GPTQ-Int4到GPU | 灵克 |
| 3.3 | 灵知/灵通+接入GPU LLM | 灵通 |

### Phase 4: 可扩展性（未来）

- 如果加入第二台机器 → Celery天然支持分布式worker
- 如果升级GPU → 模型服务层无需改动，只需改调度策略
- 如果需要训练 → 新增training队列，利用夜间空闲

---

## 四、风险与约束

| 风险 | 影响 | 缓解 |
|------|------|------|
| GPU VRAM仅6GB | 无法同时跑大模型+embedding | bge-small仅100MB，常驻无压力 |
| 驱动版本不匹配 | nvidia-smi报错（已有） | 需要先修复driver/NVML |
| 灵知Docker栈CPU配额高 | CPU资源紧张 | 灵知总配额10核但实际用4-5核，有余量 |
| 单点故障 | ai01挂=全挂 | 定期备份，/data盘空间充足 |
| 电费/散热 | GPU满载耗电 | embedding批处理限时执行，不全天候满载 |

---

## 五、待讨论问题

1. **灵研**：你当前的计算需求是什么？是否需要GPU做研究分析？Celery集成到lingresearch的方式？
2. **灵克**：
   - nvidia-container-toolkit安装是否有权限？
   - NVML driver/library版本不匹配（595.58 vs 未知），是否需要先修？
   - Celery vs 简单Python队列（考虑到规模，是否需要Celery的重量级？）
3. **广大老师**：是否同意ai01 GPU满载运行embedding批处理？（散热和噪音）

---

## 附录：ai01资源快照 (2026-05-13)

```
CPU: 8核
RAM: 31GB (21GB可用)
GPU: NVIDIA GTX 1660 Ti 6GB VRAM (CUDA可用, 当前0%利用率)
存储: /data 709GB空闲
Docker: 14容器运行 (灵知栈7 + 安全栈7)
CUDA: host可用, Docker容器未挂载
Ollama: 运行中 (qwen2.5:3b CPU模式)
Embedding: bge-small-zh CPU模式, 19ms/item
```
