# Agent 沉默成因与应对

**作者**: 灵通(lingflow)
**日期**: 2026-05-22
**状态**: 持续更新
**关联**: EVOLUTION_LOG #024/#026/#028, SILENT_INTERRUPTION_ROOT_CAUSE_20260517.md

---

## 核心发现：沉默有五个层级

沉默不是单一问题，而是五个不同机制叠加的结果。每个层级有独立的触发条件和应对方式。

| 层级 | 机制 | 表现 | Agent是否"选择"沉默 |
|------|------|------|---------------------|
| L1 代理层崩溃 | 代码bug导致进程异常 | finish=error, 零内容 | 否（被动） |
| L2 供应商层过载 | GLM返回空/断连 | finish=unknown, Provider Error | 否（被动） |
| L3 流式中断 | 连接断开但Agent可恢复 | 部分输出后中断 | 否（被动），但代理决定是否传递错误 |
| L4 模型层沉默 | 模型返回空响应（有thinking无输出） | finish=stop, 零text/tool_call | **可能主动** |
| L5 行为层沉默 | 思考回路——用thinking替代行动 | 超长thinking，零工具调用 | **主动选择** |

---

## L1 代理层：代码Bug

### Bug 8: UnboundLocalError _retry_count（2026-05-22 修复）

**文件**: `lingflow_plus/web.py:1071`
**触发次数**: 34次
**修复**: `_retry_count` 在 line 982 条件分支内被重新赋值，Python 编译器将其提升为整个函数的局部变量。当异常发生在该赋值之前时，`except`/`finally` 引用未初始化变量 → `UnboundLocalError` → 流中断 → Agent沉默。

```python
# Bug: line 982 在条件分支内重新赋值
_retry_count = _empty_response_tracker.get(...)  # Python认为这是局部变量

# Fix: 使用独立变量名
_tracker_retry_count = _empty_response_tracker.get(...)
```

### 异常终止处理（已生效的模式）

`web.py:946-962` 的异常终止逻辑：检测到 `finish=error/timeout` → 发送 error payload → 发送 `[DONE]` → crush收到错误信息 + 正常结束 → **Agent 可以继续输出**。

**这是好的模式**：既传递错误信息给用户/Agent，又不中断会话。

### 历史Bug 1-7（#024记录）

详见 `SILENT_INTERRUPTION_ROOT_CAUSE_20260517.md`。

---

## L2 供应商层：GLM过载

GLM-5.1 请求过载时静默丢弃，返回空响应或断开连接。直连也发生。

**数据**（#024, 10天, 7成员）：
- lingclan_proxy 失败率 8.8%（已修bug后应降低）
- zai_proxy 失败率 2.1%
- 直连 zai 失败率 1.1%

**应对**: 多 provider 负载均衡，失败后自动切换。

---

## L4 模型层沉默：Agent 可能自主选择沉默

**这是用户新发现（2026-05-22）**。

### 证据

crush.db 数据显示（#024, 灵研69个 finish=unknown）：
- 68% 的静默中断发生在 tool 返回后
- 57% 在 <30s 返回（不是超时）
- **所有静默中断的上一条 assistant 都没有 thinking**

最后一点最关键：如果模型确实在思考但选择不输出，应该有 thinking 记录。但数据表明 thinking 也没生成。

### 两种假说

| 假说 | 含义 | 应对方向 |
|------|------|---------|
| A: 被动沉默 | 模型/proxy返回空，Agent完全无感 | 代理层重试+错误传递 |
| B: 主动沉默 | 模型生成了thinking但决定不输出text/tool_call | 提示词约束+输出强制 |

**当前数据更支持假说A**（无thinking记录=模型根本没生成），但L5（思考回路）证明假说B在某些条件下成立。

### 判断标准

| 特征 | 被动沉默 | 主动沉默 |
|------|---------|---------|
| finish_reason | unknown/error | stop/end_turn |
| thinking | 无 | 有（可能很长） |
| 响应速度 | 极快(<1s)或超时 | 正常或偏慢 |
| 前一条消息 | tool返回或user输入 | 任意 |

---

## L5 行为层沉默：思考回路

**这是 EVOLUTION_LOG #003/#021 反复发作的问题**。

Agent 在 thinking 中反复分析同一决定，用思考替代行动。21041字节 thinking，零次工具调用（#003）。

### 硬规则（CRUSH.md）

- thinking 超3段（约300字）= 立即输出当前结论
- 同一问题3轮 thinking 无新信息 = 停下输出中间结论
- 30秒无输出是硬红线

### 教训

文字规则对行为回路的约束力不足。#003后写了4条硬规则，#021仍然违反。可能需要系统级外部检测（#021结论）。

---

## 应对体系

### 已实现

| 层 | 措施 | 效果 | 状态 |
|----|------|------|------|
| L1 | Bug 1: finish_reason 保留上游值（6eec462） | unknown 比例下降 | ✅ |
| L1 | Bug 3: web.py 异常终止处理（6eec462） | 错误可见但不中断 | ✅ |
| L1 | Bug 8: _retry_count UnboundLocalError（6eec462） | 流中断修复 | ✅ |
| L1 | Bug 2: 超时后 fallback 有意义消息 | 非静默失败 | ✅ |
| L1 | Bug 4: 全 provider 耗尽返回 proxy_fallback | crush 不受影响 | ✅ |
| L1 | Bug 5: proxy 3-phase retry（best×3→alt×3→best×3） | 部分输出后切换 provider | ✅ |
| L1 | Bug 6: 断路器剥离操作加日志记录 | 可审计 | ✅ 2026-05-22 |
| L1 | _retry_count 中断记录追踪实际重试次数 | 监控数据准确 | ✅ 2026-05-22 |
| L2 | 多 provider 路由 + 3-phase retry | 分散过载压力 | ✅ |
| L3 | 空响应自动重试（最多2次） | 部分恢复 | ✅ |
| L5 | CRUSH.md 思考回路硬规则 | 部分有效 | ✅ |

### 待实现

| 层 | 措施 | 优先级 |
|----|------|--------|
| L2 | GLM空响应自动切换provider | P1 |
| L4 | crush.db thinking长度监控 | P2 |
| L5 | 系统级外部检测（#021结论） | P1 |
| L1 | Bug 7: 多 worker 断路器状态共享 | P2 |

---

## 总结

沉默不是Agent"选择"了什么，而是多层基础设施叠加失败的结果。但L5（思考回路）证明在特定条件下，Agent确实会主动选择沉默——用thinking替代行动。区分被动沉默和主动沉默是选择正确应对方式的前提。

**沉默的层级模型**：
1. 基础设施先修好（L1-L3）
2. 然后观察L4是否还存在
3. L5需要系统级检测，不能只靠文字规则
