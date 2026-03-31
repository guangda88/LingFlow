"""
规则学习引擎

从AI工具反馈中提取模式，生成可应用的改进规则。
"""

import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path

from .feedback_interface import (
    FeedbackItem, FeedbackCategory, ToolType, SeverityLevel,
    FeedbackProcessor
)

logger = logging.getLogger(__name__)


class LearningStatus(Enum):
    """学习状态"""
    DRAFT = "draft"           # 草稿
    ANALYZING = "analyzing"   # 分析中
    VALIDATED = "validated"   # 已验证
    ACTIVE = "active"        # 活跃
    DEPRECATED = "deprecated" # 已废弃


@dataclass
class Pattern:
    """规则模式"""
    file_patterns: List[str] = field(default_factory=list)  # 匹配的文件模式
    code_patterns: List[str] = field(default_factory=list)  # 匹配的代码模式
    context_keywords: List[str] = field(default_factory=list)  # 上下文关键词
    severity_distribution: Dict[str, int] = field(default_factory=dict)  # 严重程度分布
    tool_support: List[str] = field(default_factory=list)  # 支持的工具列表


@dataclass
class LearnedRule:
    """学习到的规则"""
    id: str                                  # 规则唯一ID
    name: str                               # 规则名称
    description: str                        # 规则描述
    category: FeedbackCategory              # 规则类别
    pattern: Pattern                        # 规则模式
    tools: List[str]                        # 来源工具列表
    frequency: int                          # 出现频率
    confidence: float                       # 平均置信度
    status: LearningStatus                  # 规则状态
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.0              # 质量分数
    validation_result: Optional[Dict] = None  # 验证结果
    examples: List[Dict] = field(default_factory=list)  # 示例
    conflicts: List[str] = field(default_factory=list)  # 冲突的规则ID

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'pattern': {
                'file_patterns': self.pattern.file_patterns,
                'code_patterns': self.pattern.code_patterns,
                'context_keywords': self.pattern.context_keywords,
                'severity_distribution': self.pattern.severity_distribution,
                'tool_support': self.pattern.tool_support
            },
            'tools': self.tools,
            'frequency': self.frequency,
            'confidence': self.confidence,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'quality_score': self.quality_score,
            'validation_result': self.validation_result,
            'examples': self.examples,
            'conflicts': self.conflicts
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearnedRule':
        """从字典创建规则"""
        pattern_data = data['pattern']
        pattern = Pattern(
            file_patterns=pattern_data.get('file_patterns', []),
            code_patterns=pattern_data.get('code_patterns', []),
            context_keywords=pattern_data.get('context_keywords', []),
            severity_distribution=pattern_data.get('severity_distribution', {}),
            tool_support=pattern_data.get('tool_support', [])
        )

        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            category=FeedbackCategory(data['category']),
            pattern=pattern,
            tools=data['tools'],
            frequency=data['frequency'],
            confidence=data['confidence'],
            status=LearningStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            quality_score=data.get('quality_score', 0.0),
            validation_result=data.get('validation_result'),
            examples=data.get('examples', []),
            conflicts=data.get('conflicts', [])
        )


class RuleExtractor:
    """规则提取器"""

    def __init__(self):
        self.min_frequency = 3  # 最小出现频率
        self.min_confidence = 0.7  # 最小置信度

    def extract_rules(self, feedback_items: List[FeedbackItem]) -> List[LearnedRule]:
        """从反馈项中提取规则"""
        # 按规则ID分组
        rule_groups = defaultdict(list)
        for item in feedback_items:
            rule_groups[item.rule_id].append(item)

        # 提取每个规则的模式
        learned_rules = []
        for rule_id, items in rule_groups.items():
            if len(items) >= self.min_frequency:
                rule = self._extract_single_rule(rule_id, items)
                if rule and rule.confidence >= self.min_confidence:
                    learned_rules.append(rule)

        logger.info(f"Extracted {len(learned_rules)} rules from {len(feedback_items)} feedback items")
        return learned_rules

    def _extract_single_rule(self, rule_id: str, items: List[FeedbackItem]) -> Optional[LearnedRule]:
        """提取单个规则"""
        try:
            # 基本信息
            tool_names = list(set(item.tool_name for item in items))
            avg_confidence = sum(item.confidence for item in items) / len(items)

            # 转换主要出现的类别
            category_counts = Counter(item.category for item in items)
            primary_category = category_counts.most_common(1)[0][0]

            # 构建模式
            pattern = self._build_pattern(items)

            # 创建规则
            rule = LearnedRule(
                id=rule_id,
                name=self._generate_rule_name(rule_id, items),
                description=self._generate_description(items),
                category=primary_category,
                pattern=pattern,
                tools=tool_names,
                frequency=len(items),
                confidence=avg_confidence,
                status=LearningStatus.DRAFT
            )

            # 添加示例
            rule.examples = items[:3]  # 最多3个示例

            return rule

        except Exception as e:
            logger.error(f"Failed to extract rule {rule_id}: {e}")
            return None

    def _build_pattern(self, items: List[FeedbackItem]) -> Pattern:
        """构建规则模式"""
        pattern = Pattern()

        # 文件模式
        file_extensions = set()
        file_paths = [item.file_path for item in items]
        for path in file_paths:
            if '.' in path:
                ext = path.split('.')[-1]
                file_extensions.add(ext)

        pattern.file_patterns = list(file_extensions)

        # 代码模式
        code_patterns = []
        for item in items:
            if item.snippet:
                # 提取关键代码片段
                snippet = self._normalize_snippet(item.snippet)
                if snippet:
                    code_patterns.append(snippet)

        # 使用TF-IDF提取关键词
        pattern.context_keywords = self._extract_keywords(items)

        # 严重程度分布
        severity_counts = Counter(item.severity.value for item in items)
        pattern.severity_distribution = dict(severity_counts)

        # 工具支持
        pattern.tool_support = list(set(item.tool_name for item in items))

        return pattern

    def _normalize_snippet(self, snippet: str) -> Optional[str]:
        """标准化代码片段"""
        try:
            # 移除注释和字符串
            snippet = re.sub(r'#.*', '', snippet)
            snippet = re.sub(r'["\'][^"\']*["\']', '""', snippet)

            # 移除空白行
            lines = [line.strip() for line in snippet.split('\n') if line.strip()]

            # 提取第一行关键代码
            if lines:
                return lines[0]

        except Exception:
            pass

        return None

    def _extract_keywords(self, items: List[FeedbackItem]) -> List[str]:
        """提取上下文关键词"""
        all_text = ' '.join([
            f"{item.message} {item.rule_name} {item.snippet or ''}"
            for item in items
        ]).lower()

        # 提取关键词（简单版本）
        words = re.findall(r'\b[a-zA-Z]{4,}\b', all_text)
        word_counts = Counter(words)

        # 过滤常见词
        stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'will', 'can', 'are'}
        keywords = [word for word, count in word_counts.most_common(10)
                   if word not in stop_words and count >= 2]

        return keywords

    def _generate_rule_name(self, rule_id: str, items: List[FeedbackItem]) -> str:
        """生成规则名称"""
        # 使用最频繁的消息作为基础
        message_counts = Counter(item.message for item in items)
        base_message = message_counts.most_common(1)[0][0]

        # 简化并缩短
        name = base_message.replace('this ', '').replace('the ', '')
        name = re.sub(r'[^\w\s]', '', name)

        # 限制长度
        if len(name) > 50:
            name = name[:47] + '...'

        return name.title()

    def _generate_description(self, items: List[FeedbackItem]) -> str:
        """生成规则描述"""
        if not items:
            return ""

        # 使用第一个项目的基本描述
        base_desc = items[0].message

        # 添加出现频率和工具信息
        tool_names = list(set(item.tool_name for item in items))

        desc = f"{base_desc} (Reported by {len(tool_names)} tools, {len(items)} occurrences)"

        return desc


class RuleClassifier:
    """规则分类器"""

    def classify_rule(self, rule: LearnedRule) -> FeedbackCategory:
        """分类规则"""
        # 基于类别
        if rule.pattern.severity_distribution.get('CRITICAL', 0) > 0:
            return FeedbackCategory.SECURITY

        # 基于关键词
        all_text = ' '.join([
            rule.name,
            rule.description,
            ' '.join(rule.pattern.context_keywords)
        ]).lower()

        security_keywords = ['security', 'injection', 'xss', 'csrf', 'sql', 'rce', 'auth']
        performance_keywords = ['performance', 'memory', 'cpu', 'slow', 'latency', 'throughput']

        if any(keyword in all_text for keyword in security_keywords):
            return FeedbackCategory.SECURITY
        elif any(keyword in all_text for keyword in performance_keywords):
            return FeedbackCategory.PERFORMANCE
        elif any(tool in rule.tools for tool in ['Pylint', 'ESLint']):
            return FeedbackCategory.CODE_QUALITY
        elif any(tool in rule.tools for tool in ['SonarQube']):
            return FeedbackCategory.MAINTAINABILITY

        return FeedbackCategory.BEST_PRACTICE


class RuleQualityScorer:
    """规则质量评分器"""

    def calculate_quality(self, rule: LearnedRule) -> float:
        """计算规则质量分数 (0-1)"""
        scores = []

        # 1. 工具多样性 (0-0.3)
        diversity_score = min(len(set(rule.tools)) * 0.15, 0.3)
        scores.append(diversity_score)

        # 2. 反馈频率 (0-0.2)
        frequency_score = min(rule.frequency / 20.0, 0.2)
        scores.append(frequency_score)

        # 3. 置信度 (0-0.2)
        confidence_score = rule.confidence * 0.2
        scores.append(conferscore)

        # 4. 模式一致性 (0-0.15)
        consistency_score = self._check_pattern_consistency(rule) * 0.15
        scores.append(consistency_score)

        # 5. 覆盖范围 (0-0.15)
        coverage_score = self._check_file_coverage(rule) * 0.15
        scores.append(coverage_score)

        return round(sum(scores), 2)

    def _check_pattern_consistency(self, rule: LearnedRule) -> float:
        """检查模式一致性"""
        # 如果反馈来自同一类文件，一致性较高
        if len(rule.pattern.file_patterns) == 1:
            return 1.0
        elif len(rule.pattern.file_patterns) <= 3:
            return 0.8
        else:
            return 0.5

    def _check_file_coverage(self, rule: LearnedRule) -> float:
        """检查文件覆盖范围"""
        # 根据类别评估适当的文件类型覆盖
        if rule.category == FeedbackCategory.SECURITY:
            # 安全规则应该覆盖所有类型
            expected_coverage = 0.9
        elif rule.category == FeedbackCategory.PERFORMANCE:
            # 性能规则主要关注核心文件
            expected_coverage = 0.7
        else:
            # 其他规则适中覆盖
            expected_coverage = 0.5

        # 计算实际覆盖
        file_types_covered = len(rule.pattern.file_patterns)
        max_file_types = 10  # 假设最多10种文件类型

        actual_coverage = min(file_types_covered / max_file_types, 1.0)

        return actual_coverage * expected_coverage


class ConflictDetector:
    """冲突检测器"""

    def detect_conflicts(self, rules: List[LearnedRule]) -> Dict[str, List[str]]:
        """检测规则之间的冲突"""
        conflicts = defaultdict(list)

        for i, rule1 in enumerate(rules):
            for j, rule2 in enumerate(rules[i+1:], i+1):
                if self._rules_conflict(rule1, rule2):
                    conflicts[rule1.id].append(rule2.id)
                    conflicts[rule2.id].append(rule1.id)

        return dict(conflicts)

    def _rules_conflict(self, rule1: LearnedRule, rule2: LearnedRule) -> bool:
        """检查两个规则是否冲突"""
        # 相同类别的规则可能有冲突
        if rule1.category != rule2.category:
            return False

        # 检查代码模式冲突
        patterns1 = set(rule1.pattern.code_patterns)
        patterns2 = set(rule2.pattern.code_patterns)

        # 如果模式完全相反，认为是冲突
        opposite_patterns = {
            ('if ', 'else:'),
            ('try:', 'except'),
            ('for ', 'while ')
        }

        for p1, p2 in opposite_patterns:
            if p1 in patterns1 and p2 in patterns2:
                return True

        # 如果适用场景高度重叠但建议相反
        if self._high_overlap(rule1, rule2):
            # 检查建议是否冲突
            if self._opposite_suggestions(rule1, rule2):
                return True

        return False

    def _high_overlap(self, rule1: LearnedRule, rule2: LearnedRule) -> bool:
        """检查规则适用场景是否高度重叠"""
        # 文件类型重叠
        files_overlap = len(set(rule1.pattern.file_patterns) &
                          set(rule2.pattern.file_patterns))
        total_files = len(set(rule1.pattern.file_patterns) |
                         set(rule2.pattern.file_patterns))

        file_ratio = files_overlap / total_files if total_files > 0 else 0

        # 工具重叠
        tools_overlap = len(set(rule1.tools) & set(rule2.tools))

        return file_ratio > 0.7 and tools_overlap > 0

    def _opposite_suggestions(self, rule1: LearnedRule, rule2: LearnedRule) -> bool:
        """检查建议是否相反"""
        # 简单实现：检查关键词
        opposite_keywords = {
            ('add', 'remove'),
            ('create', 'delete'),
            ('enable', 'disable'),
            ('increase', 'decrease')
        }

        keywords1 = set(' '.join(rule1.pattern.context_keywords).lower().split())
        keywords2 = set(' '.join(rule2.pattern.context_keywords).lower().split())

        for opp1, opp2 in opposite_keywords:
            if opp1 in keywords1 and opp2 in keywords2:
                return True

        return False


class RuleLearningEngine:
    """规则学习引擎主类"""

    def __init__(self):
        self.extractor = RuleExtractor()
        self.classifier = RuleClassifier()
        self.quality_scorer = RuleQualityScorer()
        self.conflict_detector = ConflictDetector()
        self.processor = FeedbackProcessor()

    def learn_from_feedback(self, feedback_items: List[FeedbackItem]) -> List[LearnedRule]:
        """从反馈中学习规则"""
        logger.info(f"Learning from {len(feedback_items)} feedback items")

        # 1. 提取规则
        rules = self.extractor.extract_rules(feedback_items)

        # 2. 分类规则
        for rule in rules:
            rule.category = self.classifier.classify_rule(rule)

        # 3. 计算质量分数
        for rule in rules:
            rule.quality_score = self.quality_scorer.calculate_quality(rule)

        # 4. 检测冲突
        conflicts = self.conflict_detector.detect_conflicts(rules)
        for rule_id, conflicting_rules in conflicts.items():
            for rule in rules:
                if rule.id == rule_id:
                    rule.conflicts = conflicting_rules
                    break

        # 5. 更新状态
        for rule in rules:
            rule.status = LearningStatus.VALIDATED if rule.quality_score > 0.7 else LearningStatus.DRAFT

        logger.info(f"Learned {len(rules)} rules with average quality score: {sum(r.quality_score for r in rules)/len(rules):.2f}")
        return rules

    def save_rules(self, rules: List[LearnedRule], file_path: str):
        """保存规则到文件"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_rules': len(rules),
            'rules': [rule.to_dict() for rule in rules]
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(rules)} rules to {file_path}")

    def load_rules(self, file_path: str) -> List[LearnedRule]:
        """从文件加载规则"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            rules = []
            for rule_data in data.get('rules', []):
                rules.append(LearnedRule.from_dict(rule_data))

            return rules
        except Exception as e:
            logger.error(f"Error loading rules from {file_path}: {e}")
            return []


def main():
    """测试规则学习引擎"""
    # 创建模拟反馈数据
    feedback_items = [
        FeedbackItem(
            tool_name="SonarQube",
            tool_type=ToolType.STATIC_ANALYZER,
            rule_id="S1116",
            rule_name="Empty function should be a comment",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.MEDIUM,
            message="Remove this empty method and replace with a comment if needed",
            file_path="src/main.py",
            line=123,
            snippet="def empty_method(self):",
            suggestion="Consider adding a comment instead"
        ),
        # 添加更多测试数据...
    ]

    # 学习规则
    engine = RuleLearningEngine()
    rules = engine.learn_from_feedback(feedback_items)

    # 输出结果
    for rule in rules:
        print(f"\nRule: {rule.name}")
        print(f"Quality Score: {rule.quality_score}")
        print(f"Category: {rule.category}")
        print(f"Tools: {', '.join(rule.tools)}")
        print(f"Pattern: {rule.pattern.code_patterns[:2]}")

    # 保存规则
    engine.save_rules(rules, 'learned_rules.json')


if __name__ == '__main__':
    main()