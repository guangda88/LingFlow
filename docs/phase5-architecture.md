# LingFlow Phase 5: AI工具学习系统架构设计

**版本**: v1.0
**日期**: 2026-03-31
**状态**: 架构设计

---

## 目录

1. [系统概述](#系统概述)
2. [设计目标](#设计目标)
3. [AI代码审查工具研究](#ai代码审查工具研究)
4. [反馈学习机制](#反馈学习机制)
5. [规则提取与模式识别](#规则提取与模式识别)
6. [自动应用AI建议](#自动应用ai建议)
7. [安全性与可回滚性](#安全性与可回滚性)
8. [系统架构](#系统架构)
9. [接口设计](#接口设计)
10. [实施路线图](#实施路线图)
11. [集成策略](#集成策略)

---

## 系统概述

Phase 5 AI工具学习系统旨在让LingFlow从外部AI代码分析工具（如SonarQube、CodeQL、Semgrep等）中学习，提取有价值的规则和模式，并将这些知识自动集成到LingFlow的代码审查和优化流程中。

### 核心理念

**"从AI中学习，让AI变得更智能"**

系统通过以下循环实现持续改进：
```
外部AI工具 → 反馈收集 → 规则提取 → 模式识别 → 知识集成 → 应用验证 → 效果评估
     ↑                                                                              ↓
     └──────────────────────────── 持续学习循环 ←─────────────────────────────────┘
```

### 与现有系统的关系

```
┌─────────────────────────────────────────────────────────────────┐
│                        LingFlow 系统                             │
├─────────────────────────────────────────────────────────────────┤
│  现有组件:                                                        │
│  ├── code-review技能 (8维代码审查)                               │
│  ├── self_optimizer (参数优化)                                  │
│  ├── requirements/traceability (需求追溯)                       │
│  └── workflow/orchestrator (工作流编排)                          │
├─────────────────────────────────────────────────────────────────┤
│  Phase 5 新增组件:                                               │
│  ├── AI工具适配器层              │
│  │   ├── SonarQube适配器                                          │
│  │   ├── CodeQL适配器                                            │
│  │   ├── Semgrep适配器                                           │
│  │   └── 自定义AI工具接口                                        │
│  ├── 反馈学习引擎        │
│  │   ├── 反馈收集器                                                │
│  │   ├── 规则提取器                                                │
│  │   ├── 模式识别器                                                │
│  │   └── 知识验证器                                                │
│  ├── 知识库              │
│  │   ├── 规则存储                                                  │
│  │   ├── 模式存储                                                  │
│  │   └── 学习历史                                                  │
│  └── 自动应用系统          │
│      ├── 建议生成器                                                │
│      ├── 变更应用器                                                │
│      ├── 安全检查器                                                │
│      └── 回滚管理器                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 设计目标

### 主要目标

1. **学习能力**: 从多种AI代码分析工具中提取有价值的知识
2. **规则提取**: 将AI工具的反馈转化为可执行的代码审查规则
3. **模式识别**: 识别代码中的反模式和最佳实践
4. **自动应用**: 安全地自动应用AI建议
5. **可回滚性**: 所有变更都可以轻松回滚
6. **持续改进**: 通过反馈循环不断提升系统智能

### 非目标

- 不替代现有的代码审查技能，而是增强它们
- 不直接依赖外部AI服务的API（避免供应商锁定）
- 不存储敏感代码或违反隐私的数据

---

## AI代码审查工具研究

### 主流工具对比

| 工具 | 类型 | 优势 | 劣势 | 集成难度 |
|------|------|------|------|----------|
| **SonarQube** | 综合分析 | 成熟稳定，规则丰富 | 需要本地部署 | 中 |
| **CodeQL** | 语义分析 | 深度漏洞检测 | 学习曲线陡 | 高 |
| **Semgrep** | 模式匹配 | 轻量快速，自定义规则 | 误报率较高 | 低 |
| **Pylint** | Python专项 | Python深度集成 | 仅限Python | 低 |
| **Ruff** | Python linter | 极快，现代设计 | 规则较少 | 低 |
| **ESLint** | JavaScript | JS生态标准 | 仅限JS | 低 |

### 推荐集成策略

**Phase 5.1: 基础工具集成**
- **Semgrep**: 快速集成，支持自定义规则
- **Ruff**: Python代码质量，速度极快
- **Pylint**: 成熟的Python分析

**Phase 5.2: 高级工具集成**
- **SonarQube**: 企业级代码质量平台
- **CodeQL**: 深度安全分析

### 工具能力矩阵

```
能力分类:
┌─────────────────┬─────────┬─────────┬─────────┬─────────┐
│ 工具能力         │Semgrep │ Ruff    │ Pylint  │SonarQube│
├─────────────────┼─────────┼─────────┼─────────┼─────────┤
│ 安全漏洞检测     │    ★★★ │    ★★   │   ★★    │   ★★★★ │
│ 代码质量分析     │   ★★★  │   ★★★★  │  ★★★★  │  ★★★★★ │
│ 性能问题识别     │   ★★   │   ★★★   │  ★★★   │  ★★★★  │
│ 最佳实践建议     │  ★★★  │  ★★★★  │  ★★★★  │  ★★★★★ │
│ 自定义规则支持   │ ★★★★★ │   ★★   │   ★★   │  ★★★★  │
│ 执行速度         │ ★★★★  │ ★★★★★  │  ★★★   │  ★★    │
│ 学习曲线         │ ★★    │   ★★    │  ★★★   │  ★★★★  │
└─────────────────┴─────────┴─────────┴─────────┴─────────┘
```

---

## 反馈学习机制

### 反馈收集架构

```python
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class FeedbackSource(Enum):
    """反馈来源"""
    SEMGREP = "semgrep"
    RUFF = "ruff"
    PYLINT = "pylint"
    SONARQUBE = "sonarqube"
    CODEQL = "codeql"
    CUSTOM = "custom"

class FeedbackSeverity(Enum):
    """反馈严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class FeedbackCategory(Enum):
    """反馈分类"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICE = "best_practice"
    BUG_RISK = "bug_risk"

@dataclass
class AIFeedback:
    """AI工具反馈数据模型"""
    id: str                          # 唯一标识
    source: FeedbackSource           # 来源工具
    category: FeedbackCategory       # 问题类别
    severity: FeedbackSeverity       # 严重程度
    rule_id: Optional[str]           # 规则ID
    message: str                     # 反馈消息
    file_path: str                   # 文件路径
    line_no: int                     # 行号
    column_no: Optional[int]         # 列号
    code_snippet: Optional[str]      # 代码片段
    suggestion: Optional[str]        # 修复建议
    metadata: Dict[str, Any]         # 额外元数据
    timestamp: datetime              # 时间戳
    verified: bool = False           # 是否已验证
    applied: bool = False            # 是否已应用

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source": self.source.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "rule_id": self.rule_id,
            "message": self.message,
            "file_path": self.file_path,
            "line_no": self.line_no,
            "suggestion": self.suggestion,
            "verified": self.verified,
            "applied": self.applied
        }
```

### 反馈收集器

```python
class FeedbackCollector:
    """AI反馈收集器

    从各种AI代码分析工具收集反馈，并统一格式化。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.adapters: Dict[FeedbackSource, AIToolAdapter] = {}
        self._initialize_adapters()

    def _initialize_adapters(self):
        """初始化工具适配器"""
        # Semgrep
        if self.config.get("tools.semgrep.enabled", False):
            self.adapters[FeedbackSource.SEMGREP] = SemgrepAdapter(
                self.config.get("tools.semgrep", {})
            )

        # Ruff
        if self.config.get("tools.ruff.enabled", False):
            self.adapters[FeedbackSource.RUFF] = RuffAdapter(
                self.config.get("tools.ruff", {})
            )

        # Pylint
        if self.config.get("tools.pylint.enabled", False):
            self.adapters[FeedbackSource.PYLINT] = PylintAdapter(
                self.config.get("tools.pylint", {})
            )

    def collect(
        self,
        target_path: str,
        sources: Optional[List[FeedbackSource]] = None
    ) -> List[AIFeedback]:
        """收集AI反馈

        Args:
            target_path: 目标代码路径
            sources: 指定要使用的工具，None表示使用所有已配置的工具

        Returns:
            收集到的反馈列表
        """
        all_feedback = []

        # 确定要使用的工具
        if sources is None:
            sources = list(self.adapters.keys())

        # 从每个工具收集反馈
        for source in sources:
            if source not in self.adapters:
                continue

            try:
                adapter = self.adapters[source]
                feedback = adapter.analyze(target_path)
                all_feedback.extend(feedback)
            except Exception as e:
                logger.error(f"从 {source.value} 收集反馈失败: {e}")

        return all_feedback

    def collect_incremental(
        self,
        changed_files: List[str],
        sources: Optional[List[FeedbackSource]] = None
    ) -> List[AIFeedback]:
        """增量收集反馈（仅针对变更的文件）"""
        all_feedback = []

        for file_path in changed_files:
            feedback = self.collect(file_path, sources)
            all_feedback.extend(feedback)

        return all_feedback
```

### AI工具适配器接口

```python
from abc import ABC, abstractmethod

class AIToolAdapter(ABC):
    """AI工具适配器基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tool_name = self.__class__.__name__

    @abstractmethod
    def analyze(self, target_path: str) -> List[AIFeedback]:
        """分析目标路径并返回反馈

        Args:
            target_path: 要分析的文件或目录路径

        Returns:
            标准化的反馈列表
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查工具是否可用"""
        pass

    @abstractmethod
    def get_version(self) -> Optional[str]:
        """获取工具版本"""
        pass

    def parse_output(self, raw_output: str) -> List[AIFeedback]:
        """解析工具输出为标准反馈格式"""
        pass


class SemgrepAdapter(AIToolAdapter):
    """Semgrep适配器"""

    def is_available(self) -> bool:
        """检查Semgrep是否可用"""
        try:
            result = subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def analyze(self, target_path: str) -> List[AIFeedback]:
        """运行Semgrep分析"""
        # 构建命令
        cmd = [
            "semgrep",
            "--config", "auto",
            "--json",
            "--output", "-",  # 输出到stdout
            target_path
        ]

        # 执行
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.get("timeout", 300)
            )

            # 解析JSON输出
            return self._parse_semgrep_json(result.stdout)

        except subprocess.TimeoutExpired:
            logger.error("Semgrep分析超时")
            return []
        except Exception as e:
            logger.error(f"Semgrep分析失败: {e}")
            return []

    def _parse_semgrep_json(self, json_output: str) -> List[AIFeedback]:
        """解析Semgrep JSON输出"""
        try:
            data = json.loads(json_output)
            results = data.get("results", [])

            feedback_list = []
            for result in results:
                feedback = AIFeedback(
                    id=self._generate_id(result),
                    source=FeedbackSource.SEMGREP,
                    category=self._map_category(result.get("extra", {}).get("metadata", {})),
                    severity=self._map_severity(result.get("extra", {}).get("severity")),
                    rule_id=result.get("check_id"),
                    message=result.get("message", ""),
                    file_path=result.get("path", ""),
                    line_no=result.get("start", {}).get("line", 0),
                    column_no=result.get("start", {}).get("col"),
                    code_snippet=self._extract_code_snippet(result),
                    suggestion=self._generate_suggestion(result),
                    metadata=result.get("extra", {}),
                    timestamp=datetime.now()
                )
                feedback_list.append(feedback)

            return feedback_list

        except json.JSONDecodeError as e:
            logger.error(f"解析Semgrep JSON失败: {e}")
            return []


class RuffAdapter(AIToolAdapter):
    """Ruff适配器 - 极快的Python linter"""

    def analyze(self, target_path: str) -> List[AIFeedback]:
        """运行Ruff分析"""
        cmd = [
            "ruff",
            "check",
            "--output-format=json",
            target_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.get("timeout", 60)
            )

            return self._parse_ruff_json(result.stdout)

        except Exception as e:
            logger.error(f"Ruff分析失败: {e}")
            return []

    def _parse_ruff_json(self, json_output: str) -> List[AIFeedback]:
        """解析Ruff JSON输出"""
        try:
            data = json.loads(json_output)
            feedback_list = []

            for error in data:
                feedback = AIFeedback(
                    id=self._generate_id(error),
                    source=FeedbackSource.RUFF,
                    category=self._map_ruff_code(error.get("code")),
                    severity=self._map_ruff_severity(error.get("code")),
                    rule_id=error.get("code"),
                    message=error.get("message", ""),
                    file_path=error.get("filename", ""),
                    line_no=error.get("location", {}).get("row", 0),
                    column_no=error.get("location", {}).get("column"),
                    suggestion=self._get_ruff_fix(error),
                    metadata={
                        "fix": error.get("fix"),
                        "end_location": error.get("end_location")
                    },
                    timestamp=datetime.now()
                )
                feedback_list.append(feedback)

            return feedback_list

        except Exception as e:
            logger.error(f"解析Ruff JSON失败: {e}")
            return []
```

---

## 规则提取与模式识别

### 规则提取引擎

```python
class RuleExtractor:
    """从AI反馈中提取可执行规则

    目标：将一次性的AI反馈转化为可重用的代码审查规则。
    """

    def __init__(self, knowledge_base: 'KnowledgeBase'):
        self.knowledge_base = knowledge_base
        self.extractors = {
            FeedbackCategory.SECURITY: SecurityRuleExtractor(),
            FeedbackCategory.PERFORMANCE: PerformanceRuleExtractor(),
            FeedbackCategory.CODE_QUALITY: CodeQualityRuleExtractor(),
        }

    def extract_rules(
        self,
        feedback_list: List[AIFeedback]
    ) -> List['ExtractedRule']:
        """从反馈中提取规则

        Args:
            feedback_list: AI反馈列表

        Returns:
            提取的规则列表
        """
        rules = []

        # 按类别分组
        grouped = self._group_by_category(feedback_list)

        # 对每个类别提取规则
        for category, feedbacks in grouped.items():
            extractor = self.extractors.get(category)
            if extractor:
                category_rules = extractor.extract(feedbacks)
                rules.extend(category_rules)

        # 去重和验证
        rules = self._deduplicate_rules(rules)
        rules = self._validate_rules(rules)

        return rules

    def _group_by_category(
        self,
        feedback_list: List[AIFeedback]
    ) -> Dict[FeedbackCategory, List[AIFeedback]]:
        """按类别分组反馈"""
        grouped = {}
        for feedback in feedback_list:
            category = feedback.category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(feedback)
        return grouped


@dataclass
class ExtractedRule:
    """提取的规则"""
    id: str                          # 规则ID
    name: str                        # 规则名称
    category: FeedbackCategory       # 规则类别
    description: str                 # 描述
    pattern: str                     # 代码模式（AST或正则）
    severity: FeedbackSeverity       # 默认严重程度
    suggestion_template: str         # 建议模板
    confidence: float                # 置信度 (0-1)
    source_feedback_ids: List[str]   # 来源反馈ID
    created_at: datetime             # 创建时间
    verified: bool = False           # 是否已验证
    enabled: bool = True             # 是否启用

    def to_lingflow_rule(self) -> Dict[str, Any]:
        """转换为LingFlow代码审查规则"""
        return {
            "rule_id": self.id,
            "name": self.name,
            "category": self.category.value,
            "severity": self.severity.value,
            "pattern": self.pattern,
            "suggestion": self.suggestion_template,
            "confidence": self.confidence,
            "enabled": self.enabled
        }


class SecurityRuleExtractor:
    """安全规则提取器"""

    def extract(self, feedbacks: List[AIFeedback]) -> List[ExtractedRule]:
        """提取安全规则"""
        rules = []

        # 分析常见安全问题模式
        patterns = {
            "hardcoded_secrets": {
                "patterns": [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                ],
                "severity": FeedbackSeverity.HIGH,
                "suggestion": "使用环境变量或密钥管理服务存储敏感信息"
            },
            "sql_injection": {
                "patterns": [
                    r'execute\(["\'].*SELECT.*FROM.*["\']',
                ],
                "severity": FeedbackSeverity.CRITICAL,
                "suggestion": "使用参数化查询防止SQL注入"
            },
            "eval_usage": {
                "patterns": [
                    r'\beval\(',
                ],
                "severity": FeedbackSeverity.HIGH,
                "suggestion": "避免使用eval()，考虑使用更安全的替代方案"
            },
        }

        # 从反馈中提取规则
        for feedback in feedbacks:
            # 检查是否匹配已知模式
            for rule_name, rule_info in patterns.items():
                if self._matches_pattern(feedback, rule_info["patterns"]):
                    rule = ExtractedRule(
                        id=f"security_{rule_name}_{hash(feedback.message)}",
                        name=f"Security: {rule_name.replace('_', ' ').title()}",
                        category=FeedbackCategory.SECURITY,
                        description=feedback.message,
                        pattern=rule_info["patterns"][0],  # 主模式
                        severity=rule_info["severity"],
                        suggestion_template=rule_info["suggestion"],
                        confidence=self._calculate_confidence(feedback),
                        source_feedback_ids=[feedback.id],
                        created_at=datetime.now()
                    )
                    rules.append(rule)

        return rules

    def _matches_pattern(self, feedback: AIFeedback, patterns: List[str]) -> bool:
        """检查反馈是否匹配模式"""
        for pattern in patterns:
            if re.search(pattern, feedback.message, re.IGNORECASE):
                return True
        return False

    def _calculate_confidence(self, feedback: AIFeedback) -> float:
        """计算置信度"""
        # 基于多个因素计算置信度
        confidence = 0.5

        # 来自多个来源的反馈增加置信度
        if feedback.rule_id:
            confidence += 0.2

        # 有具体建议增加置信度
        if feedback.suggestion:
            confidence += 0.2

        # 有代码片段增加置信度
        if feedback.code_snippet:
            confidence += 0.1

        return min(1.0, confidence)
```

### 模式识别引擎

```python
class PatternRecognizer:
    """代码模式识别器

    识别代码中的反模式和最佳实践。
    """

    def __init__(self):
        self.pattern_detectors = [
            LongMethodDetector(),
            GodClassDetector(),
            FeatureEnvyDetector(),
            DuplicatedCodeDetector(),
            ComplexConditionDetector(),
        ]

    def recognize_patterns(
        self,
        file_path: str,
        source_code: str
    ) -> List['CodePattern']:
        """识别代码模式

        Args:
            file_path: 文件路径
            source_code: 源代码

        Returns:
            识别到的模式列表
        """
        patterns = []

        # 解析AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return patterns

        # 运行所有检测器
        for detector in self.pattern_detectors:
            detected = detector.detect(file_path, source_code, tree)
            patterns.extend(detected)

        return patterns


@dataclass
class CodePattern:
    """代码模式"""
    id: str
    name: str
    type: str  # "anti_pattern" or "best_practice"
    category: str
    description: str
    file_path: str
    locations: List[Dict[str, int]]  # [{"line": X, "column": Y}]
    severity: FeedbackSeverity
    suggestion: str
    confidence: float


class LongMethodDetector:
    """长方法检测器 - 反模式"""

    def detect(
        self,
        file_path: str,
        source_code: str,
        tree: ast.AST
    ) -> List[CodePattern]:
        """检测过长的函数"""
        patterns = []
        threshold = 50  # 行数阈值

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 计算函数行数
                lines = node.end_lineno - node.lineno if node.end_lineno else 0

                if lines > threshold:
                    pattern = CodePattern(
                        id=f"long_method_{node.name}_{hash(node.lineno)}",
                        name="Long Method",
                        type="anti_pattern",
                        category="code_quality",
                        description=f"函数 '{node.name}' 过长 ({lines} 行)",
                        file_path=file_path,
                        locations=[{"line": node.lineno, "column": node.col_offset}],
                        severity=FeedbackSeverity.MEDIUM,
                        suggestion=f"考虑将函数 '{node.name}' 拆分为更小的函数",
                        confidence=0.8
                    )
                    patterns.append(pattern)

        return patterns


class GodClassDetector:
    """上帝类检测器 - 反模式"""

    def detect(
        self,
        file_path: str,
        source_code: str,
        tree: ast.AST
    ) -> List[CodePattern]:
        """检测上帝类（承担过多责任的类）"""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 计算类的责任数量
                method_count = len([
                    n for n in node.body
                    if isinstance(n, ast.FunctionDef)
                ])

                # 计算类的行数
                lines = node.end_lineno - node.lineno if node.end_lineno else 0

                # 检查是否是上帝类
                if method_count > 15 or lines > 300:
                    pattern = CodePattern(
                        id=f"god_class_{node.name}_{hash(node.lineno)}",
                        name="God Class",
                        type="anti_pattern",
                        category="architecture",
                        description=f"类 '{node.name}' 承担过多责任 ({method_count} 方法, {lines} 行)",
                        file_path=file_path,
                        locations=[{"line": node.lineno, "column": node.col_offset}],
                        severity=FeedbackSeverity.HIGH,
                        suggestion=f"考虑将类 '{node.name}' 拆分为多个职责单一的小类",
                        confidence=0.7
                    )
                    patterns.append(pattern)

        return patterns
```

---

## 自动应用AI建议

### 建议应用架构

```python
class SuggestionApplier:
    """AI建议自动应用器

    安全地自动应用AI工具的代码改进建议。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        safety_checker: 'SafetyChecker',
        rollback_manager: 'RollbackManager'
    ):
        self.config = config
        self.safety_checker = safety_checker
        self.rollback_manager = rollback_manager
        self.appliers = {
            "simple_fix": SimpleFixApplier(),
            "refactor": RefactorApplier(),
            "security": SecurityFixApplier(),
        }

    def apply_suggestions(
        self,
        suggestions: List[AIFeedback],
        auto_apply: bool = False
    ) -> 'ApplyResult':
        """应用AI建议

        Args:
            suggestions: AI建议列表
            auto_apply: 是否自动应用（否则需要确认）

        Returns:
            应用结果
        """
        result = ApplyResult()

        # 创建检查点
        checkpoint = self.rollback_manager.create_checkpoint()

        try:
            # 按优先级排序
            sorted_suggestions = self._prioritize_suggestions(suggestions)

            for suggestion in sorted_suggestions:
                # 安全检查
                safety_check = self.safety_checker.check(suggestion)
                if not safety_check.is_safe:
                    result.skipped.append({
                        "suggestion": suggestion,
                        "reason": safety_check.reason
                    })
                    continue

                # 确认应用
                if not auto_apply:
                    if not self._confirm_application(suggestion):
                        result.skipped.append({
                            "suggestion": suggestion,
                            "reason": "用户拒绝"
                        })
                        continue

                # 应用建议
                apply_result = self._apply_single_suggestion(suggestion)
                if apply_result.success:
                    result.applied.append(apply_result)
                else:
                    result.failed.append(apply_result)

                    # 如果失败率过高，回滚
                    if len(result.failed) / len(suggestions) > 0.3:
                        logger.warning("失败率过高，执行回滚")
                        self.rollback_manager.rollback(checkpoint)
                        result.rolled_back = True
                        break

        except Exception as e:
            logger.error(f"应用建议时出错: {e}")
            self.rollback_manager.rollback(checkpoint)
            result.rolled_back = True
            result.error = str(e)

        return result

    def _prioritize_suggestions(
        self,
        suggestions: List[AIFeedback]
    ) -> List[AIFeedback]:
        """按优先级排序建议"""
        priority_order = {
            FeedbackSeverity.CRITICAL: 0,
            FeedbackSeverity.HIGH: 1,
            FeedbackSeverity.MEDIUM: 2,
            FeedbackSeverity.LOW: 3,
            FeedbackSeverity.INFO: 4,
        }

        return sorted(
            suggestions,
            key=lambda s: priority_order.get(s.severity, 5)
        )

    def _apply_single_suggestion(
        self,
        suggestion: AIFeedback
    ) -> 'SingleApplyResult':
        """应用单个建议"""
        # 选择合适的应用器
        applier_type = self._determine_applier_type(suggestion)
        applier = self.appliers.get(applier_type)

        if not applier:
            return SingleApplyResult(
                success=False,
                suggestion=suggestion,
                error="未找到合适的应用器"
            )

        # 应用
        return applier.apply(suggestion)

    def _determine_applier_type(self, suggestion: AIFeedback) -> str:
        """确定应用器类型"""
        if suggestion.category == FeedbackCategory.SECURITY:
            return "security"
        elif suggestion.code_snippet and suggestion.suggestion:
            return "simple_fix"
        else:
            return "refactor"


@dataclass
class ApplyResult:
    """应用结果"""
    applied: List['SingleApplyResult'] = field(default_factory=list)
    failed: List['SingleApplyResult'] = field(default_factory=list)
    skipped: List[Dict[str, Any]] = field(default_factory=list)
    rolled_back: bool = False
    error: Optional[str] = None

    def get_summary(self) -> str:
        """获取摘要"""
        return f"""
应用结果:
  成功: {len(self.applied)}
  失败: {len(self.failed)}
  跳过: {len(self.skipped)}
  回滚: {'是' if self.rolled_back else '否'}
"""


@dataclass
class SingleApplyResult:
    """单个建议应用结果"""
    success: bool
    suggestion: AIFeedback
    modified_files: List[str] = field(default_factory=list)
    error: Optional[str] = None
```

### 简单修复应用器

```python
class SimpleFixApplier:
    """简单修复应用器

    应用简单的、低风险的代码修复。
    """

    def apply(self, suggestion: AIFeedback) -> SingleApplyResult:
        """应用修复"""
        try:
            file_path = suggestion.file_path

            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 应用修复
            modified = False
            if suggestion.metadata.get("fix"):
                # 使用工具提供的修复
                modified = self._apply_tool_fix(lines, suggestion)
            elif suggestion.suggestion:
                # 使用建议的修复
                modified = self._apply_suggested_fix(lines, suggestion)

            if modified:
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                return SingleApplyResult(
                    success=True,
                    suggestion=suggestion,
                    modified_files=[file_path]
                )
            else:
                return SingleApplyResult(
                    success=False,
                    suggestion=suggestion,
                    error="未能应用修复"
                )

        except Exception as e:
            return SingleApplyResult(
                success=False,
                suggestion=suggestion,
                error=str(e)
            )

    def _apply_tool_fix(
        self,
        lines: List[str],
        suggestion: AIFeedback
    ) -> bool:
        """应用工具提供的修复"""
        fix_data = suggestion.metadata.get("fix")

        # Ruff格式的修复
        if isinstance(fix_data, dict):
            # 应用修复
            # ... 实现细节 ...
            return True

        return False

    def _apply_suggested_fix(
        self,
        lines: List[str],
        suggestion: AIFeedback
    ) -> bool:
        """应用建议的修复"""
        # 简单的文本替换
        # ... 实现细节 ...
        return True
```

---

## 安全性与可回滚性

### 安全检查器

```python
class SafetyChecker:
    """变更安全检查器

    确保自动应用的变更是安全的。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.checks = [
            FileSizeCheck(),
            TestCoverageCheck(),
            BreakingChangeCheck(),
            SensitiveDataCheck(),
        ]

    def check(self, suggestion: AIFeedback) -> 'SafetyCheckResult':
        """执行安全检查

        Args:
            suggestion: 要检查的AI建议

        Returns:
            安全检查结果
        """
        results = []

        for check in self.checks:
            result = check.check(suggestion)
            results.append(result)

        # 聚合结果
        is_safe = all(r.is_safe for r in results)
        reasons = [r.reason for r in results if not r.is_safe]

        return SafetyCheckResult(
            is_safe=is_safe,
            reasons=reasons,
            details=results
        )


class FileSizeCheck:
    """文件大小检查"""

    def check(self, suggestion: AIFeedback) -> SafetyCheckResult:
        """检查修改后的文件大小"""
        max_increase_percent = 20  # 最多增加20%

        # 获取当前文件大小
        try:
            file_size = Path(suggestion.file_path).stat().st_size

            # 估算修改后大小
            estimated_increase = len(suggestion.suggestion or "")
            new_size = file_size + estimated_increase

            if new_size > file_size * (1 + max_increase_percent / 100):
                return SafetyCheckResult(
                    is_safe=False,
                    reason=f"文件大小将增加超过 {max_increase_percent}%"
                )
        except Exception:
            pass

        return SafetyCheckResult(is_safe=True)


class TestCoverageCheck:
    """测试覆盖率检查"""

    def check(self, suggestion: AIFeedback) -> SafetyCheckResult:
        """检查是否会影响测试覆盖率"""
        # 检查文件是否有对应的测试
        file_path = Path(suggestion.file_path)

        # 查找测试文件
        test_file = self._find_test_file(file_path)

        if test_file and test_file.exists():
            return SafetyCheckResult(is_safe=True)
        else:
            return SafetyCheckResult(
                is_safe=False,
                reason=f"没有找到对应的测试文件: {file_path.name}"
            )

    def _find_test_file(self, source_file: Path) -> Optional[Path]:
        """查找对应的测试文件"""
        # 尝试常见的测试文件位置
        test_patterns = [
            f"test_{source_file.stem}.py",
            f"{source_file.stem}_test.py",
        ]

        for pattern in test_patterns:
            test_file = source_file.parent / "tests" / pattern
            if test_file.exists():
                return test_file

        return None


@dataclass
class SafetyCheckResult:
    """安全检查结果"""
    is_safe: bool
    reason: Optional[str] = None
    details: List[Any] = field(default_factory=list)
```

### 回滚管理器

```python
class RollbackManager:
    """回滚管理器

    管理代码变更的回滚。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.checkpoints_dir = Path(config.get("checkpoints_dir", ".lingflow/checkpoints"))
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.current_checkpoint: Optional['Checkpoint'] = None

    def create_checkpoint(self) -> 'Checkpoint':
        """创建检查点

        在应用变更前创建检查点，用于回滚。
        """
        checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = self.checkpoints_dir / checkpoint_id

        # 创建检查点目录
        checkpoint_path.mkdir(exist_ok=True)

        # 备份当前状态
        backup_data = {
            "id": checkpoint_id,
            "created_at": datetime.now().isoformat(),
            "files": {}
        }

        # 备份所有相关文件
        for file_path in self._get_tracked_files():
            file_backup = self._backup_file(file_path, checkpoint_path)
            if file_backup:
                backup_data["files"][str(file_path)] = file_backup

        # 保存检查点元数据
        metadata_file = checkpoint_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(backup_data, f, indent=2)

        checkpoint = Checkpoint(
            id=checkpoint_id,
            path=checkpoint_path,
            metadata=backup_data
        )

        self.current_checkpoint = checkpoint
        return checkpoint

    def rollback(self, checkpoint: 'Checkpoint') -> bool:
        """回滚到指定检查点"""
        try:
            # 恢复文件
            for file_path, backup_info in checkpoint.metadata["files"].items():
                self._restore_file(file_path, backup_info, checkpoint.path)

            logger.info(f"已回滚到检查点 {checkpoint.id}")
            return True

        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return False

    def _backup_file(self, file_path: Path, checkpoint_dir: Path) -> Optional[Dict]:
        """备份单个文件"""
        try:
            if not file_path.exists():
                return None

            # 创建相对路径
            rel_path = file_path.relative_to(Path.cwd())
            backup_path = checkpoint_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件
            shutil.copy2(file_path, backup_path)

            return {
                "backup_path": str(backup_path),
                "original_path": str(file_path),
                "hash": self._calculate_hash(file_path)
            }

        except Exception as e:
            logger.error(f"备份文件失败 {file_path}: {e}")
            return None

    def _restore_file(
        self,
        original_path: str,
        backup_info: Dict,
        checkpoint_dir: Path
    ) -> bool:
        """恢复文件"""
        try:
            backup_path = Path(backup_info["backup_path"])
            original = Path(original_path)

            if backup_path.exists():
                shutil.copy2(backup_path, original)
                return True

        except Exception as e:
            logger.error(f"恢复文件失败 {original_path}: {e}")
            return False

    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        import hashlib
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def _get_tracked_files(self) -> List[Path]:
        """获取需要跟踪的文件列表"""
        # 从git获取已跟踪的文件
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return [Path(f) for f in result.stdout.splitlines()]
        except Exception:
            pass

        # 降级：扫描Python文件
        return list(Path.cwd().rglob("*.py"))


@dataclass
class Checkpoint:
    """检查点"""
    id: str
    path: Path
    metadata: Dict[str, Any]

    def get_age(self) -> timedelta:
        """获取检查点年龄"""
        created_at = datetime.fromisoformat(self.metadata["created_at"])
        return datetime.now() - created_at
```

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI工具学习系统                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    反馈收集层                               │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐             │   │
│  │  │ Semgrep    │ │   Ruff     │ │  Pylint    │             │   │
│  │  │  Adapter   │ │  Adapter   │ │  Adapter   │             │   │
│  │  └────────────┘ └────────────┘ └────────────┘             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    学习引擎层                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ 规则提取器    │  │ 模式识别器    │  │ 知识验证器    │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    知识库层                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │  规则存储    │  │  模式存储    │  │  学习历史    │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    应用层                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ 建议生成器    │  │  变更应用器    │  │ 安全检查器    │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    集成层                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ code-review  │  │  self_opt    │  │  工作流集成    │      │   │
│  │  │    技能      │  │   imizer     │  │              │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 数据流

```
外部AI工具 → 适配器 → 标准化反馈 → 学习引擎 → 知识库
                                              ↓
 LingFlow系统 ← 集成层 ← 应用层 ← 安全检查 ← 建议生成
                                              ↑
                                           用户确认
```

---

## 接口设计

### 主接口

```python
class AIToolLearningSystem:
    """AI工具学习系统主类"""

    def __init__(self, config: Dict[str, Any]):
        """初始化系统"""
        self.config = config

        # 初始化组件
        self.feedback_collector = FeedbackCollector(config)
        self.rule_extractor = RuleExtractor(...)
        self.pattern_recognizer = PatternRecognizer()
        self.suggestion_applier = SuggestionApplier(...)
        self.safety_checker = SafetyChecker(config)
        self.rollback_manager = RollbackManager(config)

        # 初始化知识库
        self.knowledge_base = KnowledgeBase(config)

    def learn_from_tools(
        self,
        target_path: str,
        tools: Optional[List[str]] = None
    ) -> 'LearningResult':
        """从AI工具学习

        Args:
            target_path: 目标代码路径
            tools: 要使用的工具列表，None表示使用所有配置的工具

        Returns:
            学习结果
        """
        # 1. 收集反馈
        feedback_list = self.feedback_collector.collect(target_path, tools)

        # 2. 提取规则
        rules = self.rule_extractor.extract_rules(feedback_list)

        # 3. 识别模式
        patterns = []
        for feedback in feedback_list:
            file_patterns = self.pattern_recognizer.recognize_patterns(
                feedback.file_path,
                feedback.code_snippet or ""
            )
            patterns.extend(file_patterns)

        # 4. 验证和保存
        validated_rules = self._validate_and_save_rules(rules)
        validated_patterns = self._validate_and_save_patterns(patterns)

        # 5. 生成建议
        suggestions = self._generate_suggestions(
            validated_rules,
            validated_patterns,
            feedback_list
        )

        return LearningResult(
            feedback_count=len(feedback_list),
            rules_learned=len(validated_rules),
            patterns_recognized=len(validated_patterns),
            suggestions_generated=len(suggestions),
            suggestions=suggestions
        )

    def apply_learned_improvements(
        self,
        auto_apply: bool = False
    ) -> ApplyResult:
        """应用学习到的改进

        Args:
            auto_apply: 是否自动应用（否则需要确认）

        Returns:
            应用结果
        """
        # 获取待应用的建议
        suggestions = self.knowledge_base.get_pending_suggestions()

        # 应用建议
        result = self.suggestion_applier.apply_suggestions(
            suggestions,
            auto_apply=auto_apply
        )

        # 更新知识库状态
        if result.rolled_back:
            self.knowledge_base.mark_suggestions_failed(suggestions)
        else:
            self.knowledge_base.mark_suggestions_applied(
                result.applied
            )

        return result

    def get_learned_rules(self) -> List[ExtractedRule]:
        """获取学习到的规则"""
        return self.knowledge_base.get_all_rules()

    def get_recognized_patterns(self) -> List[CodePattern]:
        """获取识别到的模式"""
        return self.knowledge_base.get_all_patterns()
```

### CLI接口

```python
import click

@click.group()
def ai_learn():
    """AI工具学习系统命令"""
    pass

@ai_learn.command()
@click.option("--target", "-t", default=".", help="目标路径")
@click.option("--tools", help="要使用的工具（逗号分隔）")
@click.option("--apply", is_flag=True, help="自动应用建议")
def learn(target, tools, apply):
    """从AI工具学习"""
    from lingflow.self_optimizer.phase5 import AIToolLearningSystem

    tool_list = tools.split(",") if tools else None

    system = AIToolLearningSystem(config={})

    # 学习
    result = system.learn_from_tools(target, tool_list)

    click.echo(f"""
学习完成:
  收集反馈: {result.feedback_count}
  提取规则: {result.rules_learned}
  识别模式: {result.patterns_recognized}
  生成建议: {result.suggestions_generated}
    """)

    # 应用
    if apply and result.suggestions:
        if click.confirm("是否应用这些建议？"):
            apply_result = system.apply_learned_improvements(auto_apply=True)
            click.echo(f"""
应用结果:
  成功: {len(apply_result.applied)}
  失败: {len(apply_result.failed)}
  跳过: {len(apply_result.skipped)}
            """)

@ai_learn.command()
def rules():
    """显示学习到的规则"""
    system = AIToolLearningSystem(config={})
    rules = system.get_learned_rules()

    click.echo("学习到的规则:")
    for rule in rules:
        status = "✓" if rule.enabled else "✗"
        click.echo(f"  {status} {rule.name}: {rule.description}")

@ai_learn.command()
def patterns():
    """显示识别到的模式"""
    system = AIToolLearningSystem(config={})
    patterns = system.get_recognized_patterns()

    click.echo("识别到的模式:")
    for pattern in patterns:
        click.echo(f"  - {pattern.name}: {pattern.description}")
```

---

## 实施路线图

### 阶段1: 基础架构 (Week 1-2)

**目标**: 建立基础架构和适配器

**任务**:
1. 创建 `lingflow/self_optimizer/phase5/` 模块
2. 实现数据模型 (AIFeedback, ExtractedRule, CodePattern)
3. 实现Semgrep适配器
4. 实现Ruff适配器
5. 实现基础反馈收集器

**交付物**:
- 模块骨架
- 2个工具适配器
- 单元测试

### 阶段2: 学习引擎 (Week 3-4)

**目标**: 实现规则提取和模式识别

**任务**:
1. 实现规则提取引擎
2. 实现模式识别引擎
3. 实现知识库
4. 实现知识验证器

**交付物**:
- 规则提取器
- 模式识别器
- 知识库实现

### 阶段3: 应用系统 (Week 5-6)

**目标**: 实现安全的应用系统

**任务**:
1. 实现安全检查器
2. 实现回滚管理器
3. 实现建议应用器
4. 实现建议生成器

**交付物**:
- 安全检查系统
- 回滚系统
- 应用系统

### 阶段4: 集成 (Week 7-8)

**目标**: 与现有系统集成

**任务**:
1. 集成到code-review技能
2. 集成到self_optimizer
3. 实现CLI命令
4. 编写文档

**交付物**:
- 集成代码
- CLI命令
- 用户文档

### 阶段5: 优化与部署 (Week 9-10)

**目标**: 优化和部署

**任务**:
1. 性能优化
2. 更多工具适配器
3. 生产测试
4. 发布

**交付物**:
- 性能优化
- 生产版本

---

## 集成策略

### 与code-review技能集成

```python
# 扩展现有的code-review技能
def review_code_with_ai(params):
    """使用AI增强的代码审查"""
    # 1. 运行现有审查
    original_result = review_code(params)

    # 2. 从AI工具学习
    ai_system = AIToolLearningSystem(config={})
    learning_result = ai_system.learn_from_tools(
        params.get("files", ["."])
    )

    # 3. 合并结果
    enhanced_result = merge_results(original_result, learning_result)

    return enhanced_result
```

### 与self_optimizer集成

```python
# 将学到的规则集成到优化器
class EnhancedOptimizer:
    """增强的优化器"""

    def __init__(self):
        self.base_optimizer = SynchronousOptimizer()
        self.ai_system = AIToolLearningSystem(config={})

    def optimize(self, request):
        # 1. 运行基础优化
        result = self.base_optimizer.optimize(request)

        # 2. 从AI工具学习额外规则
        ai_rules = self.ai_system.get_learned_rules()

        # 3. 应用AI规则优化参数
        enhanced_params = apply_ai_rules(result.best_params, ai_rules)

        return OptimizationResult(
            best_params=enhanced_params,
            ...
        )
```

---

## 配置示例

```yaml
# ~/.lingflow/ai_learning_config.yaml

# 工具配置
tools:
  semgrep:
    enabled: true
    timeout: 300
    rules:
      - "security"
      - "performance"

  ruff:
    enabled: true
    timeout: 60
    select:
      - "E"    # pycodestyle errors
      - "W"    # pycodestyle warnings
      - "F"    # pyflakes
      - "C90"  # mccabe complexity

  pylint:
    enabled: false  # 较慢，默认关闭

# 学习配置
learning:
  min_confidence: 0.7      # 最低置信度阈值
  max_rules_per_category: 50  # 每个类别最多规则数
  auto_verify: true        # 自动验证规则

# 应用配置
application:
  auto_apply: false        # 默认不自动应用
  safety_checks:
    - "file_size"
    - "test_coverage"
    - "breaking_change"
  max_consecutive_failures: 3  # 最多连续失败数

# 回滚配置
rollback:
  enabled: true
  checkpoints_dir: ".lingflow/checkpoints"
  max_checkpoints: 10
  auto_rollback_on_failure: true
```

---

**文档版本**: v1.0
**最后更新**: 2026-03-31
**维护者**: LingFlow团队
