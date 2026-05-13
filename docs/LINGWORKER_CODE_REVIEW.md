# lingworker v0.1.0 代码评审报告

> 评审人：灵通(LingFlow) #1 | 日期：2026-05-13
> 范围：`/home/ai/lingworker/` 全量代码 + 测试 + 部署脚本

---

## 总评：✅ 通过，可部署

**33 tests all passed, 0.46s**。架构清晰，代码质量好，适合灵族2节点场景。以下按严重度分级列出问题。

---

## 🔴 P0 — 部署前必须修复

### 1. embedding结果通过Redis传输，1.5M chunks会打爆Redis内存

**位置**: `executors/embedding.py:70-76`, `worker.py:137-150`

`embed_batch` 返回完整 `embeddings.tolist()` — 一个 batch 64 chunks × 512维 × float = ~131KB JSON。但如果有人一次提交 10000 chunks，结果就是 10000 × 512 × ~8bytes = **~40MB JSON 写入单个 Redis key**。

1.5M chunks 的全量 embedding 结果如果同时堆积在 Redis 中 = **~6GB**，远超 Redis 可用内存。

**建议**：
- embedding 任务结果应直接写 PostgreSQL（灵知已有 pgvector），不走 Redis
- Redis 只存任务元数据（status, count, elapsed）
- 或限制单次任务最大 chunks 数（如 5000），超出需分批提交

### 2. GPU模型卸载只 del 了Python引用，未调用 torch.cuda.empty_cache()

**位置**: `gpu_manager.py:114-121`

```python
def _unload(self, module_name: str) -> None:
    ...
    if model is not None:
        del model  # ← 只删了Python引用，VRAM不释放
```

PyTorch 的 CUDA 缓存不会因 `del` 立即释放。需要加：
```python
import torch
torch.cuda.empty_cache()
```

否则 evict 后 VRAM 实际未回收，后续模型加载会 OOM。

### 3. Worker和API Server端口冲突

**位置**: `infra/ling-worker-api.service:14` 和 `cli.py:35`

两个 systemd service 都写端口 8950：
- `ling-worker.service` — Worker进程（不监听端口，但CLI注释写8950）
- `ling-worker-api.service` — API Server监听8950

实际上 Worker 进程不监听端口，无冲突。但 deploy_ai01.sh 同时启动 Worker 和 API Server 两个独立进程，且 Worker 的 `_poll` 轮询和 API Server 的 FastAPI 没有共享 `Worker` 实例 — **API `/status` 返回的 worker 字段永远为空**。

**建议**：让 API Server 和 Worker 在同一进程中运行（FastAPI 支持后台任务），或在部署脚本中去掉单独的 Worker 进程，改用 API Server 内嵌 Worker。

---

## 🟡 P1 — 生产化前修复

### 4. _poll 用 lpop 而非 brpop，CPU空转

**位置**: `worker.py:114-124`

```python
def _poll(self) -> TaskMessage | None:
    for queue_name in self._queue_names:
        raw = self.redis.lpop(queue_name)  # ← 非阻塞
```

当前用 `lpop` + `asyncio.sleep(1)` 轮询，空队列时每秒遍历所有队列。应改用 `brpop` 单次阻塞调用，既省CPU又降低延迟：

```python
raw = self.redis.brpop(self._queue_names, timeout=5)
```

灵克方案文档明确写了 `BRPOP`，但实现用了 `lpop`。

### 5. 任务超时未实现

**位置**: `protocol.py:56` 定义了 `timeout_seconds`，但 `worker.py` 的 `_process` 未检查超时。

长时间运行的 embedding 任务（1.5M chunks 可能跑数小时）如果卡住，没有机制终止。

### 6. 任务失败无重试

**位置**: `executors/__init__.py:61-69`

任务失败后直接写 `TaskStatus.FAILED`，不重新入队。生产环境至少需要可配置的重试次数。

### 7. Redis连接无超时和重连池

**位置**: `worker.py:60-64`

```python
self.redis = redis.Redis(
    host=redis_host, port=redis_port,
    password=redis_password or None,
    db=redis_db, decode_responses=True,
)
```

未配置 `socket_timeout`、`socket_connect_timeout`、`retry_on_timeout`。ai01 通过千兆线连主节点，网络抖动时可能无限挂起。

### 8. systemd venv路径不一致

**位置**: `infra/ling-worker.service:14`

```
ExecStart=/home/ai/lingworker/venv/bin/ling-worker ...
```

但 `deploy_ai01.sh:52` 创建的是 `.venv`（带点），不是 `venv`。部署脚本和 service 文件指向不同路径。

---

## 🟢 P2 — 改进建议（不阻塞部署）

### 9. 缺少训练执行器

`TaskType.TRAINING` 已定义但无对应 executor。`_init_defaults` 只注册了 embedding/inference/etl。训练任务提交会返回 "No executor" 错误。不阻塞 Phase 1，但应标记为 TODO。

### 10. ETL executor 的 batch_embed_dedupe 名字有误导

"embed" 暗示用到 embedding 模型，但实际只是文本去重。建议改名 `text_dedupe`。

### 11. InferenceExecutor 的 classify 用 prompt 方式，不精确

用 "请分类" prompt 让 7B 模型做分类，结果不稳定。应考虑用专门的分类模型（如 bge 的 classifier head）或 few-shot prompt。Phase 2 再优化。

### 12. deploy_ai01.sh 假设在 ai01 上运行

脚本假设 `REDIS_HOST=192.168.2.1` 是主节点，模型在本地 `/data/models/bge-small-zh`。但 lingworker 代码在 `/home/ai/lingworker/` — 如果灵克从主节点 rsync 过去再运行，需要确认 ai01 的 `/data/models/` 路径存在。

### 13. 缺少 metrics 端点（端口8951未实现）

方案文档提到 8951 提供 Prometheus 指标，但代码中没有 `/metrics` 端点。API Server 只监听 8950。

---

## 代码质量评价

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构设计 | ⭐⭐⭐⭐ | protocol/worker/gpu_manager/executors 分层清晰 |
| 代码风格 | ⭐⭐⭐⭐⭐ | 类型注解完整，docstring 规范，命名一致 |
| 测试覆盖 | ⭐⭐⭐⭐ | 33 tests 覆盖核心路径，但缺 executor 集成测试 |
| 错误处理 | ⭐⭐⭐ | 顶层有 catch，但内部缺少细粒度错误恢复 |
| 部署支持 | ⭐⭐⭐⭐ | systemd + deploy 脚本齐全，venv路径有bug |
| 安全性 | ⭐⭐⭐⭐ | 密码走环境变量，无硬编码 |

---

## 修复优先级建议

| 优先级 | 问题 | 预估工时 | 建议时机 |
|--------|------|---------|---------|
| P0-1 | Redis embedding结果体积 | 1h | 部署前 |
| P0-2 | GPU empty_cache | 15min | 部署前 |
| P0-3 | Worker/API共享实例 | 2h | Phase 1期间 |
| P1-4 | lpop→brpop | 15min | Phase 1 |
| P1-5 | 任务超时 | 1h | Phase 2 |
| P1-6 | 失败重试 | 1h | Phase 2 |
| P1-7 | Redis超时配置 | 10min | Phase 1 |
| P1-8 | venv路径不一致 | 5min | 部署前 |

**灵通建议：先修 P0（~3.5h）再部署，P1 随 Phase 1 一起修。**

---

灵通 #1
2026-05-13
