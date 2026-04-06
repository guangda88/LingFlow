# LingFlow Self-Learning 系统

> **版本**: v3.9.0
> **状态**: 生产就绪
> **测试覆盖率**: 90%

---

## 快速开始

```bash
# 1. 运行完整的自学习周期
python scripts/activate_self_learning.py --full

# 2. 只扫描代码
python scripts/activate_self_learning.py --scan

# 3. 查看知识库状态
python scripts/activate_self_learning.py --report
```

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Self-Learning 闭环                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ AI工具扫描    │───→│ 规则提取器    │───→│ 知识库       │      │
│  │              │    │              │    │              │      │
│  │ • Ruff       │    │ • 去重       │    │ • SQLite     │      │
│  │ • Semgrep    │    │ • 验证       │    │ • 持久化     │      │
│  │ • Pylint     │    │ • 质量评分   │    │              │      │
│  └──────────────┘    └──────────────┘    └──────┬───────┘      │
│                                              │                 │
│                                              ▼                 │
│                                      ┌──────────────┐        │
│                                      │ 模式识别器    │        │
│                                      │              │        │
│                                      │ • 长方法     │        │
│                                      │ • 未使用变量 │        │
│                                      │ • 硬编码密钥 │        │
│                                      └──────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. AI工具适配器 (Adapters)

| 工具 | 状态 | 版本 | 用途 |
|------|------|------|------|
| Ruff | ✅ | 0.15.9 | 快速Python linter |
| Semgrep | ✅ | - | 语义代码分析 |
| Pylint | ✅ | 4.0.5 | 深度代码检查 |

```python
from lingflow.self_optimizer.phase5.adapters import RuffAdapter

adapter = RuffAdapter()
feedback = adapter.run_scan("lingflow/")
```

### 2. 规则提取器 (RuleExtractor)

从AI工具反馈中学习规则：

```python
from lingflow.self_optimizer.phase5.learning import RuleExtractor

extractor = RuleExtractor(min_frequency=3, min_confidence=0.7)
rules = extractor.extract_rules(feedback_items)

# 规则自动包含：
# - 模式 (file_patterns, code_patterns)
# - 关键词
# - 严重程度分布
# - 质量分数
```

### 3. 知识库 (KnowledgeBase)

持久化存储学习到的规则：

```python
from lingflow.self_optimizer.phase5.knowledge import KnowledgeBase

kb = KnowledgeBase()
kb.add_rule(learned_rule)

# 查询规则
rules = kb.get_all_rules(category=FeedbackCategory.CODE_QUALITY)
stats = kb.get_statistics()
```

### 4. 模式识别器 (PatternRecognizer)

识别代码中的反模式：

```python
from lingflow.self_optimizer.phase5.patterns import PatternRecognizer

recognizer = PatternRecognizer()
patterns = recognizer.recognize_from_file("lingflow/core/session.py")

# 检测类型：
# - 长方法 (>50行)
# - 未使用变量
# - 硬编码密钥
# - 重复代码
# - 空代码块
# - 高复杂度
```

---

## 命令行接口

### activate_self_learning.py

```bash
# 完整学习周期
python scripts/activate_self_learning.py --full

# 单独操作
python scripts/activate_self_learning.py --scan        # 扫描代码
python scripts/activate_self_learning.py --learn       # 学习规则
python scripts/activate_self_learning.py --pattern     # 识别模式
python scripts/activate_self_learning.py --report      # 生成报告

# 指定目标
python scripts/activate_self_learning.py --full --target ./src

# 指定输出
python scripts/activate_self_learning.py --report --output report.json
```

---

## 配置文件

### `.lingflow/config.yaml`

```yaml
self_learning:
  # 最小频率阈值
  min_frequency: 3

  # 最小置信度
  min_confidence: 0.7

  # 质量分数阈值
  min_quality_score: 0.5

  # AI工具配置
  tools:
    ruff:
      enabled: true
      config: .ruff.toml
    semgrep:
      enabled: true
      config: .semgrep.yaml
    pylint:
      enabled: true
      config: pyproject.toml

  # 模式识别配置
  patterns:
    long_method_threshold: 50
    complexity_threshold: 10
```

---

## 知识库规则格式

### 规则结构

```json
{
  "id": "f401-unused-import",
  "name": "F401 Unused Import Detected",
  "description": "Imported but unused symbol",
  "category": "code_quality",
  "pattern": {
    "file_patterns": ["*.py"],
    "code_patterns": ["^import \\w+", "^from .* import"],
    "context_keywords": ["import", "unused"],
    "severity_distribution": {"LOW": 80, "MEDIUM": 20},
    "tool_support": ["ruff", "pylint"]
  },
  "tools": ["ruff", "pylint"],
  "frequency": 15,
  "confidence": 0.81,
  "quality_score": 0.81,
  "status": "draft"
}
```

### 规则状态

| 状态 | 说明 | 使用 |
|------|------|------|
| `draft` | 新学习的规则，待审核 | 只读 |
| `approved` | 人工审核通过 | 激活 |
| `rejected` | 人工拒绝 | 禁用 |

---

## 调度执行

### crontab 配置

```bash
# 每周一凌晨2点运行自学习
0 2 * * 1 /home/ai/LingFlow/scripts/schedule_self_learning.sh
```

### 调度脚本

```bash
#!/bin/bash
# scripts/schedule_self_learning.sh

PROJECT_ROOT="/home/ai/LingFlow"
SCRIPT="$PROJECT_ROOT/scripts/activate_self_learning.py"
LOG_DIR="$PROJECT_ROOT/.lingflow/logs"

mkdir -p "$LOG_DIR"

python3 "$SCRIPT" --full >> "$LOG_DIR/scheduler.log" 2>&1
```

---

## API 使用

### 基本用法

```python
from lingflow.self_optimizer.phase5 import SelfLearningSystem

# 初始化系统
system = SelfLearningSystem()

# 运行完整周期
result = system.run_full_cycle(target_path="lingflow/")

print(f"收集反馈: {result['feedback_collected']}")
print(f"学习规则: {result['rules_learned']}")
print(f"识别模式: {result['patterns_recognized']}")
```

### 自定义配置

```python
from lingflow.self_optimizer.phase5.learning import RuleExtractor
from lingflow.self_optimizer.phase5.knowledge import KnowledgeBase

# 自定义提取器
extractor = RuleExtractor(
    min_frequency=5,      # 更高的频率要求
    min_confidence=0.8,   # 更高的置信度
    max_rules=500         # 限制规则数量
)

# 自定义知识库
kb = KnowledgeBase(db_path="/custom/path/knowledge.db")
```

---

## 报告输出

### 报告位置

```
.lingflow/reports/
├── self_learning_20260404_085012.json
├── self_learning_20260403_020001.json
└── ...
```

### 报告内容

```json
{
  "timestamp": "2026-04-04T08:50:12",
  "knowledge_base": {
    "total_rules": 12,
    "by_category": {
      "code_quality": 9,
      "bug_risk": 3
    },
    "average_quality": 0.8
  },
  "available_tools": {
    "ruff": {"available": true, "version": "0.15.9"},
    "pylint": {"available": true, "version": "4.0.5"}
  }
}
```

---

## 故障排除

### 常见问题

**Q: 工具扫描失败？**
A: 检查工具是否安装：`ruff --version`, `semgrep --version`

**Q: 知识库为空？**
A: 运行 `--full` 命令，确保有足够的反馈数据

**Q: 规则提取为空？**
A: 降低 `min_frequency` 或 `min_confidence` 阈值

**Q: SQLite锁定错误？**
A: 确保只有一个进程在写入知识库

---

## 扩展开发

### 添加自定义检测器

```python
from lingflow.self_optimizer.phase5.patterns import PatternDetector

class CustomDetector(PatternDetector):
    def __init__(self):
        super().__init__(
            name="Custom Pattern",
            pattern_type="custom",
            severity="MEDIUM"
        )

    def detect(self, source_code, file_path):
        findings = []
        # 实现检测逻辑
        if "bad_pattern" in source_code:
            findings.append(self._create_finding(
                file_path, 1, "Bad pattern detected"
            ))
        return findings

# 注册到识别器
from lingflow.self_optimizer.phase5.patterns import PatternRecognizer

recognizer = PatternRecognizer()
recognizer.register_detector(CustomDetector())
```

### 添加自定义适配器

```python
from lingflow.self_optimizer.phase5.adapters import BaseAdapter

class CustomAdapter(BaseAdapter):
    def check_available(self) -> bool:
        # 检查工具是否可用
        return True

    def run_scan(self, target_path: str) -> List[AIFeedback]:
        # 运行扫描并返回反馈
        pass
```

---

## 性能指标

| 指标 | 值 |
|------|-----|
| 扫描速度 | ~1000文件/分钟 |
| 规则提取速度 | ~100规则/秒 |
| 知识库查询 | <10ms |
| 内存占用 | <50MB |

---

## 相关文档

- [质量控制框架](./QUALITY_CONTROL_FRAMEWORK.md)
- [核心工作流程](./CORE_WORKFLOW.md)
- [路线图 v3.9.0](./architecture/ROADMAP_v3.9.0.md)

---

**更新时间**: 2026-04-04
**维护者**: LingFlow Team
