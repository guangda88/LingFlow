# LingFlow 自优化建议报告

生成时间: 2026-04-09 21:05:04
优化目标: 结构优化
目标范围: .

---

## 当前状态分析

### 质量指标

- 结构违规: 5处
- 平均类大小: 150行
- 圈复杂度: 8.5
- 大型类数量: 3

### 主要问题

- 发现 3 个大型类（超过建议阈值）
- 结构违规: 5 处

## 优化建议

### 最佳参数配置

```yaml
# LingFlow 自优化参数配置

10
```

### 预期改进

- 结构违规: 5 → 2 (60% 改进)
- 平均类大小: 150 → 150 (0% 改进)

**优化实验**: 运行了 10 次实验
**优化耗时**: 5.0 秒

### 参数对比

| 参数 | 当前值 | 建议值 | 说明 |
|------|--------|--------|------|
| max_complexity | 默认 | 10 | 保持 |

## 实施步骤

### 选项 1: 自动应用

```bash
# 确认后自动应用优化
lingflow optimize apply --report <报告文件>
```

### 选项 2: 手动应用

1. 创建或编辑配置文件 `~/.lingflow/config.yaml`：

```yaml
# 自优化参数
structure_optimization:

  max_complexity: 10
```

2. 验证配置：
   ```bash
   lingflow review
   ```

3. 如果满意，提交更改：
   ```bash
   git add ~/.lingflow/config.yaml
   git commit -m 'opt: 应用自优化建议'
   ```

### 选项 3: 生成配置文件

```bash
# 生成新的配置文件
lingflow optimize generate-config --report <报告文件>

# 审查后手动应用
vi ~/.lingflow/config_optimized.yaml
```

---

## 优化历史

### 实验记录（前10次）

| 实验 | 参数 | 分数 |
|------|------|------|

---

*报告由 LingFlow 自动生成*
