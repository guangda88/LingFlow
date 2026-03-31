# AI学习引擎示例

本目录包含AI学习引擎的使用示例，展示如何从外部AI工具反馈中学习、验证和应用规则。

## 示例列表

### 1. learning_demo.py - 基础学习演示

展示AI学习系统的核心功能：
- 处理来自SonarQube和Pylint的反馈数据
- 从反馈中学习规则
- 计算规则质量分数和优先级
- 保存学习结果

```bash
cd ai_learning_engine/examples
python learning_demo.py
```

### 2. validation_demo.py - 规则验证演示

展示规则验证功能：
- 安全性验证（集成SecurityAnalyzer）
- 有效性验证（A/B测试）
- 生成验证报告
- 保存验证结果

```bash
cd ai_learning_engine/examples
python validation_demo.py
```

### 3. application_demo.py - 规则应用演示

展示规则应用功能：
- 自动应用和人工审核模式
- 应用请求队列管理
- 人工审核流程
- 应用进度监控

```bash
cd ai_learning_engine/examples
python application_demo.py
```

## 快速开始

1. 确保已安装所需依赖：
```bash
pip install -r ../requirements.txt
```

2. 运行示例：
```bash
cd examples
python learning_demo.py  # 先运行基础学习示例
```

## 示例输出

每个示例都会输出详细的处理过程和结果，包括：

### 学习示例输出
```
=== LingFlow AI学习系统演示 ===

1. 初始化学习引擎完成

2. 处理AI工具反馈数据...
SonarQube反馈项数: 3
Pylint反馈项数: 2
总反馈项数: 5

3. 从反馈中学习规则...
学习到的规则数: 2

规则ID: S1481
名称: Remove Unused Method
类别: code_quality
质量分数: 0.85
...
```

### 验证示例输出
```
=== 规则验证系统演示 ===

1. 初始化验证管理器

2. 创建了 3 个测试规则

3. 开始验证规则...

验证规则: Remove eval Usage
--------------------------------------------------

验证类型: safety
状态: passed
是否安全: 是
测试数量: 10
通过测试: 10
执行时间: 2.35秒
```

### 应用示例输出
```
=== 规则应用框架演示 ===

1. 初始化应用管理器

2. 创建了 2 个测试规则和 2 个测试文件

3. 提交应用请求...

规则 Remove Unused Functions 应用请求ID: xxx
状态: queued
模式: manual_review
优先级: 75
```

## 自定义扩展

### 添加新的工具适配器

```python
from ai_learning_engine import ToolAdapter

class CustomToolAdapter(ToolAdapter):
    def can_handle(self, tool_name: str) -> bool:
        return tool_name.lower() == 'my-tool'

    def parse_feedback(self, raw_data: Dict[str, Any]) -> List[FeedbackItem]:
        # 实现自定义解析逻辑
        pass

# 注册适配器
processor = FeedbackProcessor()
processor.register_adapter(CustomToolAdapter())
```

### 自定义规则应用器

```python
from ai_learning_engine.rule_application_framework import RuleApplier

class CustomRuleApplier(RuleApplier):
    def apply_rule(self, rule: LearnedRule, file_path: str) -> Tuple[bool, str]:
        # 实现自定义应用逻辑
        pass

    def get_rule_diff(self, rule: LearnedRule, file_path: str) -> str:
        # 实现自定义差异生成
        pass
```

## 注意事项

1. 示例中使用的数据是模拟数据，实际使用时需要替换为真实的AI工具反馈数据。

2. 验证和示例过程中会创建临时文件和目录，示例运行后会自动清理。

3. 对于生产环境使用，建议添加更多的错误处理和日志记录。

4. 可以根据需要调整验证参数和应用阈值。