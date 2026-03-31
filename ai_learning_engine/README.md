# AI学习引擎

AI学习引擎从外部AI工具（如SonarQube、CodeQL、Pylint、Bandit等）的反馈中学习改进规则，自动提取、验证和应用最佳实践。

## 功能特性

- **多工具支持**: 支持SonarQube、Pylint、Bandit等多种AI工具
- **规则提取**: 从反馈数据中自动识别和提取改进规则
- **质量评估**: 基于工具多样性、频率、置信度等评估规则质量
- **冲突检测**: 自动检测规则之间的冲突并提供解决方案
- **模式识别**: 识别代码模式、文件类型、上下文关键词等

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 基本使用

```python
from ai_learning_engine import RuleLearningEngine, FeedbackProcessor

# 创建学习引擎
engine = RuleLearningEngine()

# 加载反馈数据
processor = FeedbackProcessor()
feedback_items = processor.load_feedback('feedback.json')

# 学习规则
rules = engine.learn_from_feedback(feedback_items)

# 保存规则
engine.save_rules(rules, 'learned_rules.json')
```

### 3. 自定义工具适配器

```python
from ai_learning_engine import ToolAdapter

class CustomAdapter(ToolAdapter):
    def can_handle(self, tool_name: str) -> bool:
        return tool_name.lower() == 'my-custom-tool'

    def parse_feedback(self, raw_data: Dict[str, Any]) -> List[FeedbackItem]:
        # 实现自定义解析逻辑
        pass

# 注册适配器
processor = FeedbackProcessor()
processor.register_adapter(CustomAdapter())
```

## 核心组件

### FeedbackProcessor
处理来自各种AI工具的反馈数据。

```python
processor = FeedbackProcessor()
items = processor.process_feedback('SonarQube', raw_data)
```

### RuleLearningEngine
从反馈中学习规则的核心引擎。

```python
engine = RuleLearningEngine()
rules = engine.learn_from_feedback(feedback_items)
```

### RuleQualityScorer
评估规则质量。

```python
scorer = RuleQualityScorer()
quality_score = scorer.calculate_quality(rule)
```

### ConflictDetector
检测规则之间的冲突。

```python
detector = ConflictDetector()
conflicts = detector.detect_conflicts(rules)
```

## 反馈格式

### 标准反馈格式

```json
{
  "tool_name": "SonarQube",
  "tool_type": "static_analyzer",
  "rule_id": "S1481",
  "rule_name": "Remove unused method",
  "category": "code_quality",
  "severity": "MAJOR",
  "message": "Remove this unused private method",
  "file_path": "src/main.py",
  "line": 45,
  "snippet": "def calculateComplexity(self):",
  "confidence": 0.95
}
```

### 批量处理示例

```python
# 处理多个工具的反馈
all_items = []
for tool_name, data in tool_data.items():
    items = processor.process_feedback(tool_name, data)
    all_items.extend(items)

# 学习规则
rules = engine.learn_from_feedback(all_items)
```

## 配置选项

### 工具权重

```python
calculator = FeedbackPriorityCalculator()
calculator.update_tool_weight('Pylint', 0.95)
calculator.update_tool_weight('Custom', 0.7)
```

### 学习参数

```python
engine = RuleLearningEngine()
engine.extractor.min_frequency = 5  # 最小出现频率
engine.extractor.min_confidence = 0.8  # 最小置信度
```

## 监控和调试

### 日志配置

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### 性能监控

```python
# 查看学习到的规则统计
print(f"Total rules learned: {len(rules)}")
print(f"Average quality score: {sum(r.quality_score for r in rules)/len(rules)}")
print(f"Rules with conflicts: {len([r for r in rules if r.conflicts])}")
```

## API参考

详细API文档请参考各模块的docstring。

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 许可证

MIT License