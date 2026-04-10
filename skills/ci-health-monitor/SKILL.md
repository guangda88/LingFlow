---
name: ci-health-monitor
version: 1.0.0
layer: L2
group: common_services
description: |
  CI 健康监控 — 解析 CI 输出，分类失败原因，生成修复建议。
  CI health monitor — parses CI output, classifies failures, generates fix suggestions.
triggers:
  - ci
  - ci health
  - ci health monitor
  - ci诊断
  - pipeline
  - workflow失败
depends_on: []
---

# CI Health Monitor

## 概述

CI 健康监控技能，用于诊断和修复 CI 失败。

## 触发条件

- CI pipeline 失败
- 需要诊断 CI 问题
- 定期 CI 健康检查

## 执行流程

### 1. 收集 CI 输出

从以下来源收集 CI 输出：
- `gh run list` / `gh run view` (GitHub Actions)
- 本地 `ci_simulate.py` 输出
- `.github/workflows/` 配置文件

### 2. 分类失败

| 类别 | 关键词 | 严重度 |
|------|--------|--------|
| 格式 | `black`, `isort`, `format` | 低 |
| 类型 | `mypy`, `type`, `Incompatible` | 中 |
| 测试 | `FAILED`, `ERROR`, `assert` | 中 |
| 安全 | `bandit`, `security`, `BXXX` | 高 |
| 依赖 | `ModuleNotFoundError`, `ImportError` | 高 |
| 收集 | `collection`, `cannot collect` | 阻断 |

### 3. 生成修复建议

对每种失败类型：
1. 提取精确的文件名和行号
2. 生成修复命令（如 `black --line-length=127 <file>`)
3. 对于复杂问题，生成最小复现脚本

### 4. 健康报告

```
CI Health Report — <date>
━━━━━━━━━━━━━━━━━━━━━━━
Status: 🟢 GREEN / 🟡 YELLOW / 🔴 RED
- Format: ✅ PASS
- Lint: ⚠️ 3 warnings
- Types: ✅ PASS
- Tests: ✅ 142/142 passed
- Security: ✅ No issues
```

## Checklist

- [ ] CI 输出已收集
- [ ] 失败已分类
- [ ] 修复建议已生成
- [ ] 健康报告已输出
