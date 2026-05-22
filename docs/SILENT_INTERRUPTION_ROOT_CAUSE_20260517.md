# 静默中断根因分析报告

**调查者**: 灵通(lingflow)  
**日期**: 2026-05-17  
**状态**: 根因已确定  
**关联**: EVOLUTION_LOG #024

---

## 结论

lingclan_proxy（灵通+ 8765端口）有7个代码bug导致静默中断。跨4个成员、3个数据源、~17000条消息一致验证。

---

## Bug 清单

### Bug 1: finish_reason 静默映射为 null — web.py:920

```python
# 当前代码（有bug）
"finish_reason": chunk.finish_reason if chunk.finish_reason in ("stop", "tool_calls") else None,

# 应该是
"finish_reason": chunk.finish_reason,
```

上游返回 `length`/`content_filter`/`stop_sequence` 等合法值时，全部变成 `null`。客户端收到 null → crush 存为 `unknown`。

**影响**: 58/60 个 unknown finish 是纯 finish_only（零内容零reasoning）。

### Bug 2: 流式超时静默截断 — provider_pool.py 超时120s → proxy.py:397

```
超时 → yield StreamChunk(finish_reason="timeout") → proxy.py 捕获 → stream_error=True → return
```

`return` 不 yield `stop` chunk。客户端收到部分内容 + `[DONE]`，无 `finish_reason`。

**影响**: 这是最常见的 >5min 失败模式。120s 超时 + 队列等待 = 用户看到 >5min 沉默。

### Bug 3: web.py 无异常终止处理

`webui/api/proxy.py:177-195` 有正确的异常终止处理：
```python
is_abnormal = finish in ("timeout", "error") or getattr(chunk, 'truncated', False)
if is_abnormal:
    # 发送 error payload + finish_reason="stop"
    return
```

但主入口 `web.py:875-926` **完全没有这段代码**。两个文件实现不一致。

### Bug 4: 所有 provider 耗尽时空响应 — proxy.py:421

```python
yield StreamChunk(delta="", finish_reason="error")
```

映射后 → `{"delta": {}, "finish_reason": null}` → 零内容。

### Bug 5: 部分输出后流错误不重试 — proxy.py:396-397

```python
if collected_tokens == 0:
    if budget.can_retry():
        continue  # 只在零输出时重试
logger.error("Stream interrupted after partial output — cannot retry, ending stream")
return  # 有任何输出就不重试
```

收集到哪怕 1 个 token 后出错，直接 return。部分输出就是客户端拿到的全部。

### Bug 6: 断路器静默替换内容 — web.py:1006-1029

```python
_msg["content"] = "[断路器] 模型产生了空 reasoning + tool_calls 响应，已自动剥离 tool_calls。"
_msg.pop("tool_calls", None)
_msg.pop("reasoning_content", None)
choices[0]["finish_reason"] = "stop"
```

静默修改响应内容，无日志无告警。

### Bug 7: 多 worker 状态不共享 — state.py:138-142

```python
def _get_proxy() -> LLMProxy:
    global _proxy
    if _proxy is None:
        _proxy = LLMProxy(_ProxyConfig.load())
    return _proxy
```

`workers=4` 时每个 worker 独立单例。断路器、限流、token 预算全部 per-worker。

---

## 跨成员数据验证

### 失败率对比

| Provider | 灵通问道(12.7天) | 灵研 | 灵克 | 灵通(旧) | **均值** |
|----------|----------------|------|------|---------|---------|
| lingclan_proxy | 6.87% (49/713) | 10.19% (82/805) | 9.14% (63/689) | 9.15% (52/568) | **8.8%** |
| zai_proxy | 2.0% (106/5303) | 3.32% (84/2528) | 2.16% (44/2037) | 1.29% (51/3945) | **2.1%** |
| zai(直连) | 0.67% (51/7564) | 0.94% (26/2755) | 1.42% (59/4164) | 1.43% (24/1681) | **1.1%** |

lingclan_proxy 失败率是直连的 **8倍**，4个成员数据一致。

### unknown vs error 比例

| Provider | unknown% of failures |
|----------|---------------------|
| lingclan_proxy | **61.2%** |
| zai_proxy | 43.4% |
| zai(直连) | 31.4% |

lingclan_proxy 的失败中 61.2% 是 unknown（无内容无reasoning），远高于其他路径。

### 静默中断特征

- **内容**: 58/60 个 unknown finish 是纯 `[{"type":"finish","data":{"reason":"unknown","time":...}}]` — 零内容零 reasoning
- **时间**: 失败集中在 >5min（超时 120s + 队列延迟）
- **触发**: 大部分发生在 tool 返回后（agent 发出工具调用→收到结果→再次请求LLM→失败）

---

## 会话恢复系统评估

灵通+已实现但从未部署：

| 文件 | 状态 |
|------|------|
| session_interruption_detector.py | ✅ 代码完成 |
| session_recovery_daemon.py | ✅ 代码完成 |
| agent_watchdog.py 接入 | ❌ line 368 = None（从未实例化） |
| CLI 入口点 | ❌ 文档引用的命令不存在 |
| 恢复消息送达 | ❌ idle agent 不 poll LingBus（死胡同） |
| 测试 | ❌ 仅有手动 smoke test |

---

## 修复优先级

### P0 — 修复 lingclan_proxy（预计消除 80% 静默中断）

1. **Bug 1**: `web.py:920` — 保留上游 finish_reason，不映射为 null
2. **Bug 3**: `web.py` — 从 webui/api/proxy.py 移植异常终止处理

### P1 — 改善错误恢复（预计再消除 15%）

3. **Bug 2**: 超时后 yield 带 error 信息的 stop chunk
4. **Bug 5**: 部分输出后发 stop + error 信息
5. **Bug 4**: 全 provider 耗尽时返回有意义的 error

### P2 — 架构改善

6. **Bug 6**: 断路器操作记录日志
7. **Bug 7**: 共享断路器状态
8. 部署会话恢复系统
9. 全成员优先使用 zai 直连/zai_proxy

---

## 预期效果

| 指标 | 当前 | P0修复后 | 全部修复后 |
|------|------|---------|-----------|
| lingclan_proxy 失败率 | 8.8% | ~3% | ~1.5% |
| 全族静默中断/天 | ~75次 | ~15次 | ~5次 |
| 用户可感知中断 | 9%被发现 | 50%被发现 | 80%被发现 |
