# Phase 5 AI学习系统设计文档

## 系统概述

lingflow Phase 5 AI学习系统将从外部AI工具（如SonarQube、CodeQL、Pylint、Bandit等）的反馈中学习改进规则，自动提取、验证和应用AI工具的最佳实践。

### 核心目标

- 从多种AI工具的反馈中学习改进规则
- 自动提取、验证和应用最佳实践
- 保证规则应用的安全性（零破坏）
- 建立可回滚的人工审核机制
- 符合现有代码风格和规范

## 系统架构

### 1. AI反馈接口（AIFeedback Interface）

#### 支持的AI工具类型

```python
class ToolType(Enum):
    STATIC_ANALYZER = "static_analyzer"  # 静态分析工具
    CODE_REVIEW = "code_review"          # 代码审查工具
    SECURITY_SCANNER = "security_scanner"  # 安全扫描工具
    PERFORMANCE_ANALYZER = "performance_analyzer"  # 性能分析工具
    LINTING = "linting"  # 代码规范检查工具
```

#### 标准化反馈格式

```json
{
  "tool_name": "SonarQube",
  "tool_type": "static_analyzer",
  "version": "9.9",
  "timestamp": "2026-03-31T10:00:00Z",
  "project": "lingflow",
  "source": "external",
  "feedback_items": [
    {
      "rule_id": "S1481",
      "rule_name": "Remove this unused private method",
      "category": "code_smell",
      "severity": "MAJOR",
      "line": 45,
      "column": 5,
      "message": "Remove this unused private method 'calculateComplexity'",
      "file_path": "src/main.py",
      "snippet": "def calculateComplexity(self):",
      "suggestion": "Remove the unused method",
      "confidence": 0.95,
      "type": "CODE_QUALITY"
    }
  ]
}
```

#### 反馈优先级排序机制

```python
class FeedbackPriority(Enum):
    CRITICAL = 4    # 安全漏洞、严重性能问题
    HIGH = 3       # 重要代码质量问题
    MEDIUM = 2     # 次要问题、改进建议
    LOW = 1        # 代码风格、文档相关

def calculate_priority(item: FeedbackItem) -> int:
    """计算反馈优先级"""
    base_score = {
        "SECURITY": 4,
        "CRITICAL": 4,
        "HIGH": 3,
        "MAJOR": 3,
        "MINOR": 2,
        "INFO": 1
    }.get(item.severity, 2)

    # 根据工具可信度调整
    tool_weight = {
        "SonarQube": 1.0,
        "CodeQL": 1.0,
        "Pylint": 0.9,
        "Bandit": 1.0,
        "ESLint": 0.8
    }.get(item.tool_name, 0.7)

    # 考虑重复率
    frequency_weight = min(item.frequency / 5.0, 1.0)

    return base_score * tool_weight * frequency_weight
```

### 2. 规则学习引擎（Rule Learning Engine）

#### 规则提取和模式识别

```python
class RuleExtractor:
    def extract_patterns(self, feedback_items: List[FeedbackItem]) -> List[LearnedRule]:
        """从反馈项中提取模式"""
        patterns = {}

        # 按规则ID分组
        for item in feedback_items:
            if item.rule_id not in patterns:
                patterns[item.rule_id] = []
            patterns[item.rule_id].append(item)

        # 生成规则模式
        learned_rules = []
        for rule_id, items in patterns.items():
            pattern = self._analyze_pattern(items)
            rule = LearnedRule(
                id=rule_id,
                pattern=pattern,
                frequency=len(items),
                tools=[item.tool_name for item in items],
                avg_confidence=sum(item.confidence for item in items) / len(items)
            )
            learned_rules.append(rule)

        return learned_rules

    def _analyze_pattern(self, items: List[FeedbackItem]) -> Dict:
        """分析反馈模式"""
        # 统计分布
        file_types = Counter([item.file_path.split('.')[-1] for item in items])
        severities = Counter([item.severity for item in items])

        # 分析代码模式
        code_patterns = []
        for item in items:
            if hasattr(item, 'snippet'):
                pattern = self._extract_code_pattern(item.snippet)
                code_patterns.append(pattern)

        return {
            "file_types": dict(file_types),
            "severity_distribution": dict(severities),
            "code_patterns": code_patterns,
            "contextual_keywords": self._extract_keywords(items)
        }
```

#### 规则分类体系

```python
class RuleCategory(Enum):
    SECURITY = "security"           # 安全相关
    PERFORMANCE = "performance"     # 性能优化
    CODE_QUALITY = "code_quality"   # 代码质量
    MAINTAINABILITY = "maintainability"  # 可维护性
    BEST_PRACTICE = "best_practice"  # 最佳实践
    STYLE = "style"                # 代码风格

class LearnedRule:
    def __init__(self, id: str, pattern: Dict, frequency: int,
                 tools: List[str], avg_confidence: float):
        self.id = id
        self.pattern = pattern
        self.frequency = frequency
        self.tools = tools
        self.avg_confidence = avg_confidence
        self.category = self._classify_rule()
        self.quality_score = self._calculate_quality_score()

    def _classify_rule(self) -> RuleCategory:
        """根据模式分类规则"""
        # 基于关键词分类
        security_keywords = ['injection', 'xss', 'csrf', 'sql', 'rce']
        performance_keywords = ['memory', 'cpu', 'performance', 'slow']

        snippet_text = ' '.join(self.pattern.get('code_patterns', []))

        if any(keyword in snippet_text.lower() for keyword in security_keywords):
            return RuleCategory.SECURITY
        elif any(keyword in snippet_text.lower() for keyword in performance_keywords):
            return RuleCategory.PERFORMANCE
        elif self.pattern.get('severities', {}).get('HIGH', 0) > 0:
            return RuleCategory.CODE_QUALITY
        else:
            return RuleCategory.BEST_PRACTICE
```

#### 规则质量评分

```python
class RuleQualityScorer:
    def calculate_quality(self, rule: LearnedRule) -> float:
        """计算规则质量分数 (0-1)"""
        scores = []

        # 基于工具多样性 (0-0.3)
        diversity_score = min(len(set(rule.tools)) * 0.1, 0.3)
        scores.append(diversity_score)

        # 基于反馈频率 (0-0.3)
        frequency_score = min(rule.frequency / 10.0, 0.3)
        scores.append(frequency_score)

        # 基于置信度 (0-0.2)
        confidence_score = rule.avg_confidence * 0.2
        scores.append(confidence_score)

        # 基于模式一致性 (0-0.2)
        consistency_score = self._check_pattern_consistency(rule) * 0.2
        scores.append(consistency_score)

        return sum(scores)

    def _check_pattern_consistency(self, rule: LearnedRule) -> float:
        """检查模式一致性"""
        # 如果所有反馈都来自同一类文件，一致性更高
        file_types = rule.pattern.get('file_types', {})
        if len(file_types) == 1:
            return 1.0
        elif len(file_types) <= 3:
            return 0.8
        else:
            return 0.5
```

### 3. 规则验证系统（Rule Validation System）

#### 安全性验证机制

```python
class RuleValidator:
    def __init__(self, security_analyzer: SecurityAnalyzer):
        self.security_analyzer = security_analyzer

    def validate_rule_safety(self, rule: LearnedRule, test_files: List[str]) -> ValidationReport:
        """验证规则安全性"""
        violations = []
        applied_changes = []

        # 应用规则到测试文件
        for file_path in test_files:
            try:
                with open(file_path, 'r') as f:
                    original_code = f.read()

                # 应用规则
                modified_code = self._apply_rule(original_code, rule)

                # 检查安全性
                is_safe, security_violations = self.security_analyzer.analyze(modified_code)

                if not is_safe:
                    violations.extend(security_violations)

                # 记录变更
                if original_code != modified_code:
                    applied_changes.append({
                        'file': file_path,
                        'original': original_code,
                        'modified': modified_code,
                        'has_violations': len(security_violations) > 0
                    })

            except Exception as e:
                violations.append({
                    'type': 'APPLICATION_ERROR',
                    'message': str(e),
                    'severity': 'HIGH'
                })

        return ValidationReport(
            is_safe=len(violations) == 0,
            violations=violations,
            applied_changes=applied_changes,
            test_count=len(test_files)
        )

    def _apply_rule(self, code: str, rule: LearnedRule) -> str:
        """应用规则（示例）"""
        # 根据规则模式应用相应的修改
        if rule.category == RuleCategory.SECURITY:
            # 安全规则替换
            if 'eval(' in code:
                code = code.replace('eval(', 'ast.literal_eval(')

        return code
```

#### A/B测试验证

```python
class ABTester:
    def create_test_groups(self, files: List[str], rule: LearnedRule) -> Dict[str, List[str]]:
        """创建A/B测试组"""
        import random
        random.shuffle(files)

        split_point = len(files) // 2
        return {
            'control_group': files[:split_point],      # 不应用规则
            'test_group': files[split_point:]          # 应用规则
        }

    def evaluate_ab_test(self, control_results: List[Dict], test_results: List[Dict]) -> ABTestResult:
        """评估A/B测试结果"""
        # 计算质量指标改善
        control_quality = self._calculate_quality_score(control_results)
        test_quality = self._calculate_quality_score(test_results)

        improvement = (test_quality - control_quality) / control_quality

        # 计算副作用
        side_effects = self._detect_side_effects(test_results)

        return ABTestResult(
            improvement_rate=improvement,
            is_improved=improvement > 0,
            side_effects=side_effects,
            confidence=self._calculate_confidence(control_results, test_results)
        )
```

### 4. 规则应用框架（Rule Application Framework）

#### 自动应用vs人工审核

```python
class RuleApplicationManager:
    def __init__(self, auto_apply_threshold: float = 0.8):
        self.auto_apply_threshold = auto_apply_threshold

    def should_auto_apply(self, rule: LearnedRule) -> bool:
        """判断是否自动应用规则"""
        # 质量分数足够高
        if rule.quality_score < self.auto_apply_threshold:
            return False

        # 安全性已验证
        if not rule.validation_result.is_safe:
            return False

        # 不是高风险操作
        if rule.category == RuleCategory.SECURITY and rule.frequency < 3:
            return False

        return True

    def apply_rule_manually(self, rule: LearnedRule, target_files: List[str]) -> ManualReviewRequest:
        """申请人工审核"""
        return ManualReviewRequest(
            rule=rule,
            target_files=target_files,
            suggested_changes=self._generate_change_preview(rule, target_files),
            priority=self._calculate_review_priority(rule)
        )
```

#### 规则优先级调度

```python
class RuleScheduler:
    def schedule_rule_application(self, rules: List[LearnedRule]) -> Schedule:
        """调度规则应用"""
        # 按优先级排序
        sorted_rules = sorted(rules, key=lambda r: (
            r.quality_score,
            r.frequency,
            self._get_tool_weight(r.tools)
        ), reverse=True)

        # 创建调度计划
        schedule = Schedule()
        current_batch = []

        for rule in sorted_rules:
            # 检查是否可以合并到当前批次
            if self._can_merge_batch(rule, current_batch):
                current_batch.append(rule)
            else:
                # 开始新批次
                if current_batch:
                    schedule.add_batch(current_batch, self._calculate_batch_impact(current_batch))
                current_batch = [rule]

        # 添加最后一个批次
        if current_batch:
            schedule.add_batch(current_batch, self._calculate_batch_impact(current_batch))

        return schedule
```

### 5. 实施计划（分阶段）

#### 阶段1：基础设施（2-3周）
1. **实现AI反馈接口**
   - 创建标准化的反馈格式定义
   - 实现工具适配器模式
   - 集成SonarQube、CodeQL、Pylint基础支持

2. **建立规则存储**
   - 设计规则数据库模式
   - 实现规则版本控制
   - 创建规则索引系统

#### 阶段2：学习能力（3-4周）
1. **实现规则学习引擎**
   - 开发模式提取算法
   - 实现规则分类系统
   - 建立质量评分机制

2. **集成现有分析组件**
   - 复用SecurityAnalyzer
   - 整合RuleEngine
   - 扩展StructureEvaluator

#### 阶段3：验证机制（2-3周）
1. **实现验证系统**
   - 开发安全性验证
   - 实现A/B测试框架
   - 建立回滚机制

2. **人工审核工作流**
   - 创建审核界面
   - 实现审核状态跟踪
   - 集成CI/CD流程

#### 阶段4：应用框架（2-3周）
1. **实现应用管理**
   - 开发自动应用逻辑
   - 实现人工审核流程
   - 创建优先级调度

2. **集成到现有系统**
   - 集成自优化系统
   - 添加CLI命令
   - 创建监控仪表板

#### 阶段5：优化和扩展（2周）
1. **性能优化**
   - 优化规则处理性能
   - 实现增量更新
   - 添加缓存机制

2. **扩展功能**
   - 支持更多AI工具
   - 添加自定义规则
   - 实现规则市场

## 技术实现细节

### 数据库设计

```sql
CREATE TABLE learned_rules (
    id VARCHAR(50) PRIMARY KEY,
    rule_json JSON,
    category ENUM('security', 'performance', 'code_quality', 'maintainability', 'best_practice', 'style'),
    quality_score FLOAT,
    frequency INT,
    tools JSON,
    pattern JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    status ENUM('draft', 'validated', 'active', 'deprecated')
);

CREATE TABLE rule_validation_results (
    id UUID PRIMARY KEY,
    rule_id VARCHAR(50) REFERENCES learned_rules(id),
    test_files JSON,
    is_safe BOOLEAN,
    violations JSON,
    applied_changes JSON,
    validation_timestamp TIMESTAMP
);

CREATE TABLE manual_review_requests (
    id UUID PRIMARY KEY,
    rule_id VARCHAR(50) REFERENCES learned_rules(id),
    requested_by VARCHAR(50),
    status ENUM('pending', 'approved', 'rejected'),
    reviewer_notes TEXT,
    review_timestamp TIMESTAMP
);
```

### API设计

```python
# 注册新的AI工具反馈
POST /api/v1/feedback/register-tool
{
    "tool_name": "SonarQube",
    "tool_type": "static_analyzer",
    "version": "9.9",
    "config": {...}
}

# 提交反馈数据
POST /api/v1/feedback/submit
{
    "tool_name": "SonarQube",
    "feedback_items": [...]
}

# 获取学习到的规则
GET /api/v1/rules?page=1&limit=20&category=security

# 验证规则
POST /api/v1/rules/{rule_id}/validate
{
    "test_files": [...],
    "validation_type": "safety"
}

# 申请人工审核
POST /api/v1/rules/{rule_id}/review-request
{
    "target_files": [...],
    "notes": "请审核此规则的应用"
}
```

## 风险控制

### 安全保证措施

1. **零破坏保证**
   - 所有规则应用前必须通过安全性验证
   - 实现代码沙箱测试
   - 保持完整的变更历史记录

2. **回滚机制**
   - 每个规则应用都有对应的回滚脚本
   - 支持一键回滚到应用前的状态
   - 记录回滚原因和结果

3. **人工审核**
   - 高风险规则必须人工审核
   - 实现分级审核机制
   - 审核过程完全可追溯

### 质量控制

1. **规则质量评分**
   - 基于工具多样性、频率、置信度
   - 定期重新评估规则质量
   - 自动淘汰低质量规则

2. **渐进式部署**
   - 从测试环境开始
   - 逐步推广到生产环境
   - 监控部署效果

## 监控和维护

### 性能监控

```python
class Monitoring:
    def track_rule_application(self, rule_id: str, execution_time: float, success: bool):
        """跟踪规则应用性能"""
        metrics = {
            'rule_id': rule_id,
            'timestamp': datetime.now(),
            'execution_time': execution_time,
            'success': success,
            'memory_usage': psutil.Process().memory_info().rss
        }
        self._store_metrics(metrics)

    def track_system_health(self):
        """监控系统健康状态"""
        health_metrics = {
            'active_rules': len(self.get_active_rules()),
            'validation_success_rate': self._calculate_validation_success_rate(),
            'average_application_time': self._calculate_avg_application_time(),
            'error_rate': self._calculate_error_rate()
        }
        return health_metrics
```

### 定期维护

1. **规则审计**
   - 每月审查规则效果
   - 清理无效或过时规则
   - 更新阈值和参数

2. **工具更新**
   - 跟踪AI工具版本更新
   - 适配新版本的反馈格式
   - 更新规则库

## 总结

Phase 5 AI学习系统设计通过标准化的接口、智能的规则学习、严格的安全验证和灵活的应用机制，实现了从多种AI工具反馈中自动学习改进规则的能力。系统设计注重安全性、可维护性和可扩展性，确保能够持续改进代码质量，同时保证零破坏的风险控制。

该系统将与现有的lingflow自优化系统深度集成，形成一个完整的代码质量提升闭环，为开发团队提供智能化的代码改进建议和自动化修复能力。