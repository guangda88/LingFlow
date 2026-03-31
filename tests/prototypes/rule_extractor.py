"""
规则提取概念验证原型

从AI工具反馈中提取规则和模式。
"""

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple


class ToolType(Enum):
    """工具类型"""
    STATIC_ANALYZER = "static_analyzer"
    CODE_REVIEW = "code_review"
    SECURITY_SCANNER = "security_scanner"
    LINTING = "linting"


class FeedbackCategory(Enum):
    """反馈类别"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICE = "best_practice"


class SeverityLevel(Enum):
    """严重程度"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class FeedbackItem:
    """反馈项"""
    tool_name: str
    tool_type: ToolType
    rule_id: str
    rule_name: str
    category: FeedbackCategory
    severity: SeverityLevel
    message: str
    file_path: str
    line: int
    snippet: Optional[str] = None
    suggestion: Optional[str] = None
    confidence: float = 0.8


@dataclass
class Pattern:
    """规则模式"""
    file_patterns: List[str] = field(default_factory=list)
    code_patterns: List[str] = field(default_factory=list)
    context_keywords: List[str] = field(default_factory=list)
    severity_distribution: Dict[str, int] = field(default_factory=dict)
    tool_support: List[str] = field(default_factory=list)


@dataclass
class LearnedRule:
    """学习到的规则"""
    id: str
    name: str
    description: str
    category: FeedbackCategory
    pattern: Pattern
    tools: List[str]
    frequency: int
    confidence: float
    quality_score: float = 0.0
    status: str = "draft"
    created_at: datetime = field(default_factory=datetime.now)


class RuleExtractor:
    """规则提取器"""

    def __init__(self, min_frequency: int = 3, min_confidence: float = 0.7):
        self.min_frequency = min_frequency
        self.min_confidence = min_confidence

    def extract_rules(self, feedback_items: List[FeedbackItem]) -> List[LearnedRule]:
        """从反馈项中提取规则"""
        from collections import defaultdict

        # 按规则ID分组
        rule_groups = defaultdict(list)
        for item in feedback_items:
            rule_groups[item.rule_id].append(item)

        # 提取规则
        learned_rules = []
        for rule_id, items in rule_groups.items():
            if len(items) >= self.min_frequency:
                rule = self._extract_single_rule(rule_id, items)
                if rule and rule.confidence >= self.min_confidence:
                    learned_rules.append(rule)

        return learned_rules

    def _extract_single_rule(self, rule_id: str, items: List[FeedbackItem]) -> Optional[LearnedRule]:
        """提取单个规则"""
        # 基本信息
        tool_names = list(set(item.tool_name for item in items))
        avg_confidence = sum(item.confidence for item in items) / len(items)

        # 主要类别
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
            status="draft"
        )

        # 计算质量分数
        rule.quality_score = self._calculate_quality_score(rule)

        return rule

    def _build_pattern(self, items: List[FeedbackItem]) -> Pattern:
        """构建规则模式"""
        pattern = Pattern()

        # 文件模式
        file_extensions = set()
        for item in items:
            if '.' in item.file_path:
                ext = item.file_path.split('.')[-1]
                file_extensions.add(ext)
        pattern.file_patterns = list(file_extensions)

        # 代码模式
        for item in items:
            if item.snippet:
                normalized = self._normalize_snippet(item.snippet)
                if normalized and normalized not in pattern.code_patterns:
                    pattern.code_patterns.append(normalized)

        # 上下文关键词
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
            # 移除注释
            snippet = re.sub(r'#.*', '', snippet)
            # 移除字符串
            snippet = re.sub(r'["\'][^"\']*["\']', '""', snippet)
            # 移除空白
            lines = [line.strip() for line in snippet.split('\n') if line.strip()]
            if lines:
                return lines[0][:100]  # 限制长度
        except Exception:
            pass
        return None

    def _extract_keywords(self, items: List[FeedbackItem]) -> List[str]:
        """提取关键词"""
        all_text = ' '.join([
            f"{item.message} {item.rule_name}"
            for item in items
        ]).lower()

        words = re.findall(r'\b[a-zA-Z]{4,}\b', all_text)
        word_counts = Counter(words)

        # 过滤常见词
        stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'will', 'can', 'are'}
        keywords = [word for word, count in word_counts.most_common(10)
                   if word not in stop_words and count >= 2]

        return keywords[:5]

    def _generate_rule_name(self, rule_id: str, items: List[FeedbackItem]) -> str:
        """生成规则名称"""
        message_counts = Counter(item.message for item in items)
        base_message = message_counts.most_common(1)[0][0]

        name = base_message.replace('this ', '').replace('the ', '')
        name = re.sub(r'[^\w\s]', '', name)

        if len(name) > 50:
            name = name[:47] + '...'

        return name.title()

    def _generate_description(self, items: List[FeedbackItem]) -> str:
        """生成描述"""
        base_desc = items[0].message
        tool_names = list(set(item.tool_name for item in items))
        return f"{base_desc} (Reported by {len(tool_names)} tools, {len(items)} occurrences)"

    def _calculate_quality_score(self, rule: LearnedRule) -> float:
        """计算质量分数 (0-1)"""
        scores = []

        # 工具多样性 (0-0.3)
        diversity_score = min(len(set(rule.tools)) * 0.15, 0.3)
        scores.append(diversity_score)

        # 反馈频率 (0-0.3)
        frequency_score = min(rule.frequency / 10.0, 0.3)
        scores.append(frequency_score)

        # 置信度 (0-0.2)
        confidence_score = rule.confidence * 0.2
        scores.append(confidence_score)

        # 模式一致性 (0-0.2)
        if len(rule.pattern.file_patterns) == 1:
            consistency_score = 1.0
        elif len(rule.pattern.file_patterns) <= 3:
            consistency_score = 0.8
        else:
            consistency_score = 0.5
        scores.append(consistency_score * 0.2)

        return round(sum(scores), 2)


class RuleDeduplicator:
    """规则去重器"""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, rules: List[LearnedRule]) -> List[LearnedRule]:
        """去重规则"""
        unique_rules = []
        seen_hashes: Set[str] = set()

        for rule in rules:
            rule_hash = self._compute_rule_hash(rule)

            # 检查是否有相似规则
            is_duplicate = False
            for seen_hash in seen_hashes:
                if self._are_similar(rule_hash, seen_hash):
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_rules.append(rule)
                seen_hashes.add(rule_hash)

        return unique_rules

    def _compute_rule_hash(self, rule: LearnedRule) -> str:
        """计算规则哈希"""
        # 基于关键词和模式计算哈希
        keywords_str = ' '.join(sorted(rule.pattern.context_keywords))
        patterns_str = ' '.join(sorted(rule.pattern.code_patterns))

        combined = f"{rule.category.value}:{keywords_str}:{patterns_str}"
        return combined.lower().replace(' ', '')

    def _are_similar(self, hash1: str, hash2: str) -> bool:
        """检查哈希是否相似"""
        # 简单实现：检查包含关系
        return hash1 in hash2 or hash2 in hash1


class SecurityRuleExtractor(RuleExtractor):
    """安全规则提取器 - 示例实现"""

    def extract_rules(self, feedback_items: List[FeedbackItem]) -> List[LearnedRule]:
        """提取安全规则"""
        # 只处理安全类别的反馈
        security_items = [
            item for item in feedback_items
            if item.category == FeedbackCategory.SECURITY
        ]

        # 使用父类方法提取
        rules = super().extract_rules(security_items)

        # 为安全规则添加特殊标记
        for rule in rules:
            rule.status = "security_verified"

        return rules

    def _extract_keywords(self, items: List[FeedbackItem]) -> List[str]:
        """提取安全相关关键词"""
        keywords = super()._extract_keywords(items)

        # 添加安全特定关键词
        security_keywords = ['injection', 'xss', 'csrf', 'sql', 'auth', 'crypto']
        for kw in security_keywords:
            if any(kw in item.message.lower() for item in items) and kw not in keywords:
                keywords.append(kw)

        return keywords[:7]


# 测试数据
def create_sample_feedback() -> List[FeedbackItem]:
    """创建示例反馈数据"""
    return [
        FeedbackItem(
            tool_name="Semgrep",
            tool_type=ToolType.SECURITY_SCANNER,
            rule_id="python.lang.security.audit.semgrep",
            rule_name="Hardcoded password detected",
            category=FeedbackCategory.SECURITY,
            severity=SeverityLevel.HIGH,
            message="Hardcoded password detected in source code",
            file_path="src/auth.py",
            line=45,
            snippet="password = 'admin123'",
            suggestion="Use environment variables for credentials",
            confidence=0.95
        ),
        FeedbackItem(
            tool_name="Bandit",
            tool_type=ToolType.SECURITY_SCANNER,
            rule_id="B105:hardcoded_password_string",
            rule_name="Possible hardcoded password",
            category=FeedbackCategory.SECURITY,
            severity=SeverityLevel.HIGH,
            message="Possible hardcoded password: 'admin123'",
            file_path="src/auth.py",
            line=45,
            snippet="password = 'admin123'",
            suggestion="Use a secure credential manager",
            confidence=0.90
        ),
        FeedbackItem(
            tool_name="Semgrep",
            tool_type=ToolType.SECURITY_SCANNER,
            rule_id="python.lang.security.audit.semgrep",
            rule_name="Hardcoded password detected",
            category=FeedbackCategory.SECURITY,
            severity=SeverityLevel.HIGH,
            message="Hardcoded password detected",
            file_path="src/config.py",
            line=12,
            snippet="db_pass = 'secret456'",
            suggestion="Use environment variables",
            confidence=0.92
        ),
        FeedbackItem(
            tool_name="Ruff",
            tool_type=ToolType.LINTING,
            rule_id="F401",
            rule_name="Unused import",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.LOW,
            message="Unused import 'os'",
            file_path="src/utils.py",
            line=3,
            snippet="import os",
            suggestion="Remove unused import",
            confidence=0.85
        ),
        FeedbackItem(
            tool_name="Ruff",
            tool_type=ToolType.LINTING,
            rule_id="F401",
            rule_name="Unused import",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.LOW,
            message="Unused import 'json'",
            file_path="src/helpers.py",
            line=5,
            snippet="import json",
            suggestion="Remove unused import",
            confidence=0.85
        ),
        FeedbackItem(
            tool_name="Ruff",
            tool_type=ToolType.LINTING,
            rule_id="F401",
            rule_name="Unused import",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.LOW,
            message="Unused import 'sys'",
            file_path="src/main.py",
            line=2,
            snippet="import sys",
            suggestion="Remove unused import",
            confidence=0.88
        ),
        FeedbackItem(
            tool_name="SonarQube",
            tool_type=ToolType.STATIC_ANALYZER,
            rule_id="python:S1186",
            rule_name="Empty function",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.MEDIUM,
            message="Add a nested comment explaining why this function is empty",
            file_path="src/models.py",
            line=78,
            snippet="def empty_method(self): pass",
            suggestion="Remove or implement this method",
            confidence=0.80
        ),
        FeedbackItem(
            tool_name="Pylint",
            tool_type=ToolType.LINTING,
            rule_id="W0612",
            rule_name="Unused variable",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.LOW,
            message="Unused variable 'data'",
            file_path="src/process.py",
            line=34,
            snippet="data = fetch_data()",
            suggestion="Remove or use this variable",
            confidence=0.75
        ),
        FeedbackItem(
            tool_name="Pylint",
            tool_type=ToolType.LINTING,
            rule_id="W0612",
            rule_name="Unused variable",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.LOW,
            message="Unused variable 'result'",
            file_path="src/api.py",
            line=56,
            snippet="result = calculate()",
            suggestion="Remove or use this variable",
            confidence=0.78
        ),
        FeedbackItem(
            tool_name="Pylint",
            tool_type=ToolType.LINTING,
            rule_id="W0612",
            rule_name="Unused variable",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.LOW,
            message="Unused variable 'temp'",
            file_path="src/cache.py",
            line=23,
            snippet="temp = get_temp()",
            suggestion="Remove or use this variable",
            confidence=0.76
        ),
    ]


# 模式识别器
class PatternRecognizer:
    """模式识别器"""

    def __init__(self):
        self.detectors = [
            LongMethodDetector(),
            UnusedVariableDetector(),
            HardcodedSecretDetector(),
        ]

    def recognize_patterns(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """识别代码模式"""
        patterns = []

        for detector in self.detectors:
            detected = detector.detect(source_code, file_path)
            patterns.extend(detected)

        return patterns


class PatternDetector:
    """模式检测器基类"""

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测模式"""
        raise NotImplementedError


class LongMethodDetector(PatternDetector):
    """长方法检测器"""

    def __init__(self, threshold: int = 50):
        self.threshold = threshold

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测过长的方法"""
        patterns = []

        # 简单实现：统计函数行数
        lines = source_code.split('\n')
        current_function = None
        function_lines = 0
        function_start = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('def '):
                # 保存上一个函数
                if current_function and function_lines > self.threshold:
                    patterns.append({
                        'type': 'anti_pattern',
                        'name': 'Long Method',
                        'file': file_path,
                        'line': function_start,
                        'message': f"Function '{current_function}' is too long ({function_lines} lines)",
                        'severity': 'MEDIUM',
                        'confidence': 0.8
                    })

                # 开始新函数
                current_function = stripped.split('(')[0].replace('def ', '').strip()
                function_lines = 0
                function_start = i
            elif current_function:
                function_lines += 1

        # 检查最后一个函数
        if current_function and function_lines > self.threshold:
            patterns.append({
                'type': 'anti_pattern',
                'name': 'Long Method',
                'file': file_path,
                'line': function_start,
                'message': f"Function '{current_function}' is too long ({function_lines} lines)",
                'severity': 'MEDIUM',
                'confidence': 0.8
            })

        return patterns


class UnusedVariableDetector(PatternDetector):
    """未使用变量检测器"""

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测未使用的变量"""
        patterns = []

        # 简单实现：查找赋值但未使用的模式
        import re

        lines = source_code.split('\n')

        # 查找变量赋值
        for i, line in enumerate(lines, 1):
            match = re.match(r'^(\w+)\s*=\s*.+', line.strip())
            if match:
                var = match.group(1)
                # 检查变量是否在其他地方使用
                var_pattern = rf'\b{var}\b'
                uses = len(re.findall(var_pattern, source_code))

                # 如果只出现一次（赋值时），说明未使用
                if uses == 1:
                    patterns.append({
                        'type': 'anti_pattern',
                        'name': 'Unused Variable',
                        'file': file_path,
                        'line': i,
                        'message': f"Variable '{var}' is assigned but never used",
                        'severity': 'LOW',
                        'confidence': 0.7
                    })

        return patterns[:3]  # 限制返回数量


class HardcodedSecretDetector(PatternDetector):
    """硬编码密钥检测器"""

    def __init__(self):
        self.secret_patterns = {
            'password': r'password\s*=\s*["\'][^"\']+["\']',
            'api_key': r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            'secret': r'secret\s*=\s*["\'][^"\']+["\']',
        }

    def detect(self, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """检测硬编码密钥"""
        patterns = []

        for secret_name, pattern in self.secret_patterns.items():
            matches = re.finditer(pattern, source_code, re.IGNORECASE)
            for match in matches:
                line_num = source_code[:match.start()].count('\n') + 1
                patterns.append({
                    'type': 'security',
                    'name': 'Hardcoded Secret',
                    'file': file_path,
                    'line': line_num,
                    'message': f"Hardcoded {secret_name} detected",
                    'severity': 'HIGH',
                    'confidence': 0.9
                })

        return patterns


def main():
    """主测试函数"""
    print("=" * 60)
    print("规则提取概念验证")
    print("=" * 60)

    # 创建示例数据
    feedback_items = create_sample_feedback()
    print(f"\n示例反馈数量: {len(feedback_items)}")

    # 测试基础提取器
    print("\n--- 基础规则提取 ---")
    extractor = RuleExtractor(min_frequency=2, min_confidence=0.7)
    rules = extractor.extract_rules(feedback_items)
    print(f"提取的规则数量: {len(rules)}")

    for rule in rules:
        print(f"\n规则: {rule.name}")
        print(f"  ID: {rule.id}")
        print(f"  类别: {rule.category.value}")
        print(f"  频率: {rule.frequency}")
        print(f"  置信度: {rule.confidence:.2f}")
        print(f"  质量分数: {rule.quality_score:.2f}")
        print(f"  工具: {', '.join(rule.tools)}")
        print(f"  关键词: {', '.join(rule.pattern.context_keywords)}")

    # 测试去重
    print("\n--- 规则去重 ---")
    deduplicator = RuleDeduplicator()
    unique_rules = deduplicator.deduplicate(rules)
    print(f"去重前: {len(rules)}, 去重后: {len(unique_rules)}")

    # 测试安全规则提取
    print("\n--- 安全规则提取 ---")
    security_extractor = SecurityRuleExtractor(min_frequency=2, min_confidence=0.7)
    security_rules = security_extractor.extract_rules(feedback_items)
    print(f"安全规则数量: {len(security_rules)}")

    for rule in security_rules:
        print(f"\n安全规则: {rule.name}")
        print(f"  状态: {rule.status}")
        print(f"  置信度: {rule.confidence:.2f}")

    # 测试模式识别
    print("\n--- 模式识别 ---")
    recognizer = PatternRecognizer()

    # 示例代码
    sample_code = """
def very_long_function():
    x = 1
    y = 2
    z = 3
    # ... many more lines ...
    return x + y + z

password = "admin123"
api_key = "sk-1234567890"
unused_var = "test"
"""

    patterns = recognizer.recognize_patterns(sample_code, "test.py")
    print(f"识别到的模式数量: {len(patterns)}")

    for pattern in patterns:
        print(f"\n模式: {pattern['name']}")
        print(f"  类型: {pattern['type']}")
        print(f"  消息: {pattern['message']}")
        print(f"  严重度: {pattern['severity']}")
        print(f"  置信度: {pattern['confidence']:.2f}")

    # 计算提取准确率
    print("\n--- 提取准确率 ---")
    # 预期应该提取到以下规则：
    # 1. Hardcoded password (3次出现)
    # 2. Unused import (3次出现)
    # 3. Unused variable (3次出现)
    expected_rules = 3
    accuracy = len(rules) / expected_rules if expected_rules > 0 else 0
    print(f"提取准确率: {accuracy * 100:.1f}%")
    print(f"预期规则数: {expected_rules}, 实际提取: {len(rules)}")

    print("\n" + "=" * 60)
    print("概念验证完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
