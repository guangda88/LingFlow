# lingflow 技术债务清理计划 v2

**日期**: 2026-04-03
**基于**: 宪章与原则审计报告
**状态**: 执行中

---

## 一、清理目标

| 指标 | 当前 | 目标 | 改进 |
|------|------|------|------|
| 版本一致性 | ❌ 混乱 | ✅ 统一 | 100% |
| 文档数量 | 385 | <200 | -48% |
| TODO注释 | 7 | 0 | -100% |
| 测试覆盖率 | 50% | 70% | +40% |

---

## 二、P0 - 立即执行 (今天)

### P0-1: 版本统一

**问题**: 版本号在多个文档中不一致

**行动**:
```bash
# 1. 确认当前版本
grep -r "__version__" lingflow/bootstrap.py  # 3.8.0

# 2. 更新文档版本号
# - PRINCIPLES_V4.md → PRINCIPLES.md (去除版本号)
# - MVP_PLAN.md → 更新状态为"已完成"或"进行中"
# - V4.0_OPTIMIZATION_PLAN.md → 移动到 archive/

# 3. 创建版本策略
```

**文件**: `docs/VERSIONING.md` (新建)

```markdown
# lingflow 版本策略

## 当前版本: v3.8.0

## 版本规则

- **主版本**: 重大架构变更
- **次版本**: 新功能
- **补丁版本**: Bug修复

## 文档版本

文档不使用版本号后缀，单一来源:
- `PRINCIPLES.md` - 总是最新
- `ROADMAP.md` - 总是最新
- `ARCHITECTURE.md` - 总是最新

过时版本移动到 `docs/archive/`
```

### P0-2: MVP计划状态更新

**问题**: MVP_PLAN.md状态为"待审查"，但代码已是v3.8.0

**行动**:
- [ ] 审查MVP计划完成度
- [ ] 更新状态：`进行中` / `已完成` / `已取消`
- [ ] 如果已完成，创建完成报告

### P0-3: 过时文档归档

**问题**: V4.0_OPTIMIZATION_PLAN.md状态为"待实施"，但与最新原则冲突

**行动**:
```bash
mkdir -p docs/archive/plans/
mv docs/reports/optimization/LINGFLOW_V4.0_OPTIMIZATION_PLAN.md \
   docs/archive/plans/
```

---

## 三、P1 - 2周内完成

### P1-1: 清理TODO注释

**位置**: 7处TODO/FIXME

**行动**:
```bash
# 查找所有TODO
grep -rn "TODO\|FIXME\|XXX\|HACK" lingflow/ --include="*.py"

# 逐个处理：
# 1. 如果可修复 → 立即修复
# 2. 如果需要Issue → 创建GitHub Issue
# 3. 如果过时 → 删除
```

### P1-2: 文档整理

**目标**: 385个文档 → <200个

**策略**:
1. **删除重复**: 同一内容的多份拷贝
2. **归档过时**: 移动到archive/
3. **合并相关**: 多个小文档合并为一个
4. **创建索引**: INDEX.md帮助导航

**行动**:
```bash
# 1. 创建文档索引
cat > docs/INDEX.md << 'EOF'
# lingflow 文档索引

## 核心文档
- [README](../README.md) - 项目介绍
- [CHARTER](CHARTER.md) - 宪章
- [PRINCIPLES](PRINCIPLES.md) - 开发原则
- [ROADMAP](ROADMAP.md) - 路线图

## 架构
- [架构概述](architecture/README.md)
- [四层架构](architecture/four-layers.md)

## API文档
- [核心API](api/core.md)
- [CLI](api/cli.md)

## 技能开发
- [技能指南](skills/README.md)
- [技能模板](skills/template.md)

## 归档
- [过时文档](archive/README.md)
EOF

# 2. 归档过时文档
mkdir -p docs/archive/{v3.5,v3.6,v3.7,v3.8}

# 3. 按日期归档
find docs/reports/archive -name "*.md" -mtime +90 | \
  xargs -I {} mv {} docs/archive/legacy/
```

### P1-3: 测试覆盖率提升

**目标**: 50% → 70%

**策略**:
1. 识别未测试的核心模块
2. 添加单元测试
3. 添加集成测试

**优先模块**:
- `lingflow/core/` - 核心逻辑
- `lingflow/compression/` - 压缩系统
- `lingflow/context/` - 上下文管理

---

## 四、P2 - 持续改进

### P2-1: 魔法数字消除

**问题**: 代码中存在未定义的数字常量

**行动**:
```python
# 之前
if len(items) > 10:
    ...

# 之后
MAX_ITEMS = 10
if len(items) > MAX_ITEMS:
    ...
```

### P2-2: 性能基准测试

**问题**: 缺少性能基准，无法检测退化

**行动**:
```python
# 创建 tests/benchmarks/
# - test_compression_benchmark.py
# - test_context_benchmark.py
# - test_query_benchmark.py
```

---

## 五、执行时间表

| 周次 | 任务 | 产出 |
|------|------|------|
| Week 1 (4/3-4/10) | P0全部完成 | 版本统一，文档归档 |
| Week 2 (4/10-4/17) | P1-1, P1-2 | TODO清理，文档整理 |
| Week 3-4 (4/17-5/1) | P1-3 | 测试覆盖率70% |
| 持续 | P2-1, P2-2 | 代码质量改进 |

---

## 六、检查清单

### 每日检查
- [ ] 新代码无TODO/FIXME
- [ ] 新功能有测试
- [ ] 文档已更新

### 每周检查
- [ ] 技术债数量减少
- [ ] 测试覆盖率增加
- [ ] 代码审查分数

### 发布前检查
- [ ] 所有P0债务已清偿
- [ ] 文档版本一致
- [ ] 测试全部通过

---

## 七、成功标准

**短期 (2周)**:
- [x] 审计报告完成
- [ ] P0债务100%完成
- [ ] TODO注释清零

**中期 (1个月)**:
- [ ] P1债务100%完成
- [ ] 测试覆盖率70%
- [ ] 文档数量<200

**长期 (持续)**:
- [ ] 新债务及时发现
- [ ] 代码质量持续提升
- [ ] 文档保持更新

---

## 八、债务追踪

| ID | 描述 | 优先级 | 状态 | 负责人 | 截止日期 |
|----|------|--------|------|--------|----------|
| P0-1 | 版本统一 | P0 | 进行中 | - | 2026-04-03 |
| P0-2 | MVP状态更新 | P0 | 待开始 | - | 2026-04-03 |
| P0-3 | 文档归档 | P0 | 待开始 | - | 2026-04-03 |
| P1-1 | TODO清理 | P1 | 待开始 | - | 2026-04-10 |
| P1-2 | 文档整理 | P1 | 待开始 | - | 2026-04-17 |
| P1-3 | 测试覆盖率 | P1 | 待开始 | - | 2026-05-01 |

---

**计划版本**: 2.0
**创建日期**: 2026-04-03
**最后更新**: 2026-04-03
**下次审查**: 2026-04-10
