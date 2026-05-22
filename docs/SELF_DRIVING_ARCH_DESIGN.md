# 自驱任务管理机制 架构设计

**设计层级**: P0（全局架构）
**设计日期**: 2026-05-18
**状态**: 设计评审中

---

## 1. 现状扫描（代码审计结果）

### 1.1 已代码强制（2/5）

| 门控 | 实现位置 | 状态 |
|------|---------|------|
| **元认知检查** | `coordinator.py:498` `_check_metacognition` | ✅ 代码强制 |
| **审计门** | `coordinator.py:571` `_check_audit_gate` | ✅ 代码强制 |

### 1.2 仅文本规则（3/5）

| 门控 | 现状 | 风险 |
|------|------|------|
| **handover有记录** | 只有 schema 字段，无代码检查 | AI 可跳过 |
| **TAP检查** | AGENTS.md 文本规则 | AI 可绕过 |
| **外部操作禁止自驱** | CRUSH.md 文本规则 | AI 可能越权 |
| **ai_continuations记录** | 有 schema 字段，无代码写入逻辑 | 无执行轨迹 |
| **用户输入立即停** | 无代码实现 | 自驱任务不可中断 |

---

## 2. 核心设计目标

1. **不可绕过性**: 门控代码在 SkillExecutor.execute 路径上，不是文本规则
2. **可审计性**: 所有自驱决策有完整执行轨迹
3. **低侵入性**: 复用现有 MetacognitionGate / AuditGate 架构
4. **诚实标注**: 每个自驱任务强制标注 `user_confirmation: true/false`

---

## 3. P0 架构方案

### 3.1 三层控制流

```
用户指令
    ↓
[SkillExecutor.execute]
    ↓
┌─────────────────────────────────────┐
│           AutonomyGate              │  ← 新增
│  ┌───────────────────────────────┐ │
│  │ 1. 来源判定: user / self      │ │
│  │    (task.source)              │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ 2. 五道门控检查               │ │  ← 代码强制
│  │   - handover 有记录?          │ │
│  │   - TAP 对齐?                 │ │
│  │   - 风险评估 (外部操作?)      │ │
│  │   - 审计门放行?               │ │
│  │   - 元认知通过?               │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ 3. 写入 ai_continuations      │ │  ← 执行前先记
│  │    (user_confirmation 标注)   │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
    ↓
[实际技能执行]
    ↓
┌─────────────────────────────────────┐
│       AutonomyMonitor               │  ← 新增
│  - THR (Task Hijack Ratio) 统计     │
│  - 诚实率标注统计                   │
│  - 异常自驱告警                     │
└─────────────────────────────────────┘
```

### 3.2 数据模型扩展

```python
# lingflow/common/models.py - 扩展 Task 模型

class Task:
    # 已有字段
    task_id: str
    description: str
    status: TaskStatus
    
    # 新增自驱字段
    source: TaskSource = TaskSource.USER  # USER / SELF_GENERATED
    user_confirmation: bool = False       # 诚实标注
    tap_check_result: Optional[Dict] = None  # TAP检查结果
    risk_level: RiskLevel = RiskLevel.LOW  # LOW/MEDIUM/HIGH
```

### 3.3 AutonomyGate 接口设计

```python
# lingflow/context/autonomy_gate.py

class AutonomyGate:
    """自驱任务五道门控 - 代码强制，不可绕过
    
    在 SkillExecutor.execute() 路径上强制调用。
    """
    
    def check_and_record(
        self,
        task: Task,
        handover: HandoverDocument
    ) -> GateResult:
        """执行五道门控并记录
        
        Returns:
            GateResult: allowed / reason / restrictions
        """
        # 门1: handover有记录
        if task.source == TaskSource.SELF_GENERATED:
            if not self._has_self_generated_record(task, handover):
                return GateResult(
                    allowed=False,
                    reason="自驱任务必须先在 handover.self_generated_suggestions 登记"
                )
        
        # 门2: TAP检查
        tap_result = self._tap_check(task)
        if not tap_result.aligned:
            return GateResult(
                allowed=False,
                reason=f"TAP检查未通过: {tap_result.reason}"
            )
        
        # 门3: 风险评估
        risk = self._assess_risk(task)
        if risk == RiskLevel.HIGH and not task.user_confirmation:
            return GateResult(
                allowed=False,
                reason=f"高风险操作需要用户确认: {risk.description}"
            )
        
        # 门4: 审计门（复用现有）
        audit_result = self._audit_gate_check(task)
        if not audit_result.passed:
            return GateResult(
                allowed=False,
                reason=f"审计未通过: {audit_result.reason}"
            )
        
        # 门5: 元认知检查（复用现有）
        meta_result = self._metacognition_check(task)
        if not meta_result.can_start:
            return GateResult(
                allowed=False,
                reason=f"元认知检查未通过: {meta_result.reason}"
            )
        
        # 全部通过: 写入 ai_continuations 记录轨迹
        self._write_continuation_record(task, handover, tap_result, risk)
        
        return GateResult(allowed=True, risk_level=risk)
```

### 3.4 SkillExecutor 集成点

```python
# lingflow/common/skill_manager.py

class SkillExecutor:
    # 在 execute 方法头部插入
    def execute(self, skill_name: str, params: Dict) -> Dict:
        # 从 params 提取 task 元数据
        task = self._extract_task_info(params)
        
        # 自驱门控检查（仅自驱任务执行，用户任务跳过）
        if task.source == TaskSource.SELF_GENERATED:
            gate = AutonomyGate()
            handover = self._load_current_handover()
            result = gate.check_and_record(task, handover)
            if not result.allowed:
                return {
                    "error": f"Autonomy gate blocked: {result.reason}",
                    "gate_result": result.to_dict()
                }
        
        # 原有执行逻辑
        return self._do_execute(skill_name, params)
```

---

## 4. 关键设计决策

### 4.1 用户任务不经过门控

**决策**: `source == USER` 的任务直接跳过 AutonomyGate，只走审计门和元认知门

**理由**: 
- 用户指令永远最高优先级
- 避免给正常工作流增加摩擦
- 只防"AI 自说自话偏离目标"，不防用户自己的操作

### 4.2 诚实标注强制执行

**决策**: 自驱任务执行前，**必须**写入 `ai_continuations`，标注 `user_confirmation: false`

**理由**:
- 先记再做，避免"做了但没记录"
- 审计时可以完整追溯所有自驱决策
- 不记录就不能执行，强制可审计

### 4.3 高风险操作定义

**高风险列表**（代码写死，不可配置）:
- `git push` 到远程仓库
- `curl` / `requests` 访问外部 IP
- `rm -rf` 根目录操作
- 修改系统配置文件（`/etc`、注册表）
- 跨项目目录写操作（不在当前工作目录内）

**中风险**:
- 运行测试套件
- 代码重构
- 文档批量更新

---

## 5. 可审计性设计

### 5.1 执行轨迹字段

每个 `ai_continuations` 记录必须包含:

```json
{
  "id": "ac1",
  "source": "ai",
  "description": "扫描确认：自驱五道门控仅2个有代码强制",
  "tap_check": {
    "aligned": true,
    "reason": "执行P0架构扫描，如实报告代码现状"
  },
  "status": "completed",
  "user_confirmation": false,
  "risk_level": "low",
  "started_at": "2026-05-18T17:30:00+08:00",
  "completed_at": "2026-05-18T17:30:05+08:00",
  "skill_executed": "grep",
  "files_modified": ["/home/ai/lingflow/.lingflow/handover.json"]
}
```

### 5.2 THR 统计

```python
# AutonomyMonitor.thr_report()
{
  "total_tasks": 100,
  "user_tasks": 75,
  "self_generated_tasks": 25,
  "thr": 0.25,  # 自驱任务占比 = THR
  "honesty_rate": 1.0,  # 25/25 都正确标注了 user_confirmation=false
  "high_risk_blocked": 2,  # 成功阻止2个高风险自驱操作
  "user_stopped": 1  # 用户输入中断了1个自驱任务
}
```

---

## 6. 实现优先级

| 优先级 | 模块 | 预计工作量 | 阻塞项 |
|--------|------|-----------|--------|
| P0 | `Task.source` / `user_confirmation` 字段 | 1h | 无 |
| P0 | `AutonomyGate.check_and_record` 核心 | 4h | Task模型扩展 |
| P0 | `SkillExecutor` 集成 | 2h | AutonomyGate |
| P1 | `AutonomyMonitor` THR统计 | 3h | 门控先落地 |
| P1 | handover 自动加载/保存 | 2h | 无 |
| P2 | 用户输入自动中断 | 4h | 需要消息总线Hook |

---

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 门控误判阻止合法自驱 | 中 | 中 | strict_mode 开关，可降级到 warning-only |
| 性能影响 | 低 | 低 | 只对自驱任务执行门控，用户任务跳过 |
| AI 绕过门控（不走 SkillExecutor） | 中 | 高 | 额外增加 bash 工具 wrapper 二次检查 |
| handover 记录丢失 | 低 | 中 | 双写：内存 + 磁盘文件，原子写入 |

---

**设计评审问题**:
1. 用户任务跳过门控是否合理？
2. 高风险操作列表是否完整？
3. THR 统计维度是否足够？
4. SkillExecutor 集成点位置对吗？
