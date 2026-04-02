# 警惕过度开发 - 项目原则

**日期**: 2026-03-31
**版本**: 1.0
**状态**: ✅ 已写入项目开发规则

---

## 原则声明

> **警惕过度开发**是LingFlow项目的核心开发原则之一。

---

## 已更新文档

### 1. `docs/reports/DEVELOPMENT_RULES.md`

**更新位置1**: V3.5 核心原则表
```markdown
| **警惕过度开发** | 简洁设计，避免不必要的抽象和复杂度 |
```

**更新位置2**: 禁止事项 - 警惕过度开发（新增章节）

包含以下内容：
- 什么是过度开发
- 识别过度开发的信号
- 审计标准（基于2026-03-31审计）
- 实用主义开发准则
- YOLO模式经验

---

## 核心内容摘要

### 识别过度开发的信号

1. 🚩 文件行数过大 (>500行)
2. 🚩 函数过长 (>50行)
3. 🚩 过多的抽象类和接口
4. 🚩 不必要的配置项
5. 🚩 过度使用设计模式

### 审计标准

- 代码复杂度评分: Phase 4 ≤ 3/10, Phase 5 ≤ 6/10
- 平均文件行数: < 400行
- 长函数比例: < 10%
- 抽象层数: ≤ 3层

### YOLO模式经验 (2026-03-31)

- ✅ 快速原型验证降低风险
- ✅ 先实现核心功能，再优化
- ✅ 简单测试足以保证质量
- ✅ 避免完美主义拖延进度
- ✅ **6小时完成10-12周工作量 (280-336x加速)**

---

## 示例

### ❌ 过度开发

```python
class AbstractAdapterFactory(ABC):
    """工厂的工厂接口 - 过度抽象"""
    @abstractmethod
    def create_factory(self) -> 'AdapterFactory':
        pass

class AdapterFactory(ABC):
    """抽象适配器工厂"""
    @abstractmethod
    def create_adapter(self) -> 'Adapter':
        pass
```

### ✅ 简洁实用

```python
def create_adapter(tool_type: str) -> 'Adapter':
    """创建适配器 - 简单直接"""
    if tool_type == "semgrep":
        return SemgrepAdapter()
    elif tool_type == "ruff":
        return RuffAdapter()
    raise ValueError(f"Unknown tool: {tool_type}")
```

---

## 名言

> **"完美是优秀的敌人。"** - Voltaire
>
> **"过早优化是万恶之源。"** - Donald Knuth
>
> **"简单是终极的复杂。"** - Leonardo da Vinci

---

**生效日期**: 2026-03-31
**适用范围**: 全体开发人员

众智混元，万法灵通 ⚡🚀
