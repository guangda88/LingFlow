"""
规则提取和学习引擎

从AI工具反馈中提取、学习和优化规则。
YOLO模式：基于原型快速生产化
"""

import re
from collections import Counter
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

from .models import (
    FeedbackItem,
    LearnedRule,
    Pattern,
    FeedbackCategory,
    SeverityLevel,
    ToolType
)


class RuleExtractor:
    """规则提取器 - 从反馈中学习规则"""

    def __init__(
        self,
        min_frequency: int = 3,
        min_confidence: float = 0.7,
        max_rules: int = 1000
    ):
        self.min_frequency = min_frequency
        self.min_confidence = min_confidence
        self.max_rules = max_rules
        self._extracted_count = 0

    def extract_rules(
        self,
        feedback_items: List[FeedbackItem],
        category: Optional[FeedbackCategory] = None
    ) -> List[LearnedRule]:
        """从反馈项中提取规则

        Args:
            feedback_items: 反馈项列表
            category: 可选的类别过滤

        Returns:
            提取的规则列表
        """
        from collections import defaultdict

        # 过滤类别
        if category:
            feedback_items = [
                item for item in feedback_items
                if item.category == category
            ]

        # 按规则ID分组
        rule_groups = defaultdict(list)
        for item in feedback_items:
            # 规范化规则ID
            rule_id = self._normalize_rule_id(item.rule_id)
            rule_groups[rule_id].append(item)

        # 提取规则
        learned_rules = []
        for rule_id, items in rule_groups.items():
            if len(items) >= self.min_frequency:
                rule = self._extract_single_rule(rule_id, items)
                if rule and rule.confidence >= self.min_confidence:
                    learned_rules.append(rule)
                    self._extracted_count += 1

                    # 限制最大规则数
                    if self._extracted_count >= self.max_rules:
                        break

        # 按质量分数排序
        learned_rules.sort(key=lambda r: r.quality_score, reverse=True)

        return learned_rules

    def _normalize_rule_id(self, rule_id: str) -> str:
        """规范化规则ID"""
        # 移除特殊字符，统一格式
        rule_id = re.sub(r'[^\w.-]', '_', rule_id)
        return rule_id.lower().strip()

    def _extract_single_rule(
        self,
        rule_id: str,
        items: List[FeedbackItem]
    ) -> Optional[LearnedRule]:
        """提取单个规则"""
        try:
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
                confidence=round(avg_confidence, 2),
                status="draft",
                created_at=datetime.now()
            )

            # 计算质量分数
            rule.quality_score = self._calculate_quality_score(rule)

            return rule

        except Exception as e:
            # 静默失败，记录但不中断
            return None

    def _build_pattern(self, items: List[FeedbackItem]) -> Pattern:
        """构建规则模式"""
        pattern = Pattern()

        # 文件模式
        file_extensions = set()
        file_paths = set()
        for item in items:
            if '.' in item.file_path:
                ext = item.file_path.split('.')[-1]
                file_extensions.add(f"*.{ext}")
            file_paths.add(item.file_path)

        pattern.file_patterns = list(file_extensions)

        # 代码模式
        seen_patterns = set()
        for item in items:
            if item.snippet:
                normalized = self._normalize_snippet(item.snippet)
                if normalized and normalized not in seen_patterns:
                    pattern.code_patterns.append(normalized)
                    seen_patterns.add(normalized)

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
            snippet = re.sub(r'//.*', '', snippet)

            # 移除字符串字面量
            snippet = re.sub(r'["\'][^"\']*["\']', '""', snippet)

            # 移除多余空白
            lines = [line.strip() for line in snippet.split('\n') if line.strip()]

            if lines:
                # 返回第一行，限制长度
                return lines[0][:100]
        except Exception:
            pass
        return None

    def _extract_keywords(self, items: List[FeedbackItem]) -> List[str]:
        """提取关键词"""
        all_text = ' '.join([
            f"{item.message} {item.rule_name} {item.suggestion or ''}"
            for item in items
        ]).lower()

        # 提取单词
        words = re.findall(r'\b[a-zA-Z_]{4,}\b', all_text)
        word_counts = Counter(words)

        # 过滤停用词
        stop_words = {
            'this', 'that', 'with', 'from', 'have', 'been', 'will',
            'can', 'are', 'were', 'been', 'being', 'should', 'could',
            'would', 'their', 'there', 'where', 'which', 'about'
        }

        keywords = [
            word for word, count in word_counts.most_common(15)
            if word not in stop_words and count >= 2
        ]

        return keywords[:7]

    def _generate_rule_name(self, rule_id: str, items: List[FeedbackItem]) -> str:
        """生成规则名称"""
        message_counts = Counter(item.message for item in items)
        base_message = message_counts.most_common(1)[0][0]

        # 清理消息
        name = base_message.replace('this ', '').replace('the ', '')
        name = re.sub(r'[^\w\s-]', '', name)
        name = name.strip().title()

        # 限制长度
        if len(name) > 60:
            name = name[:57] + '...'

        return name

    def _generate_description(self, items: List[FeedbackItem]) -> str:
        """生成规则描述"""
        base_desc = items[0].message
        tool_names = list(set(item.tool_name for item in items))
        occurrence_text = f"{len(items)} occurrence{'s' if len(items) > 1 else ''}"

        return (
            f"{base_desc} "
            f"(Detected by {len(tool_names)} tool{'s' if len(tool_names) > 1 else ''}, "
            f"{occurrence_text})"
        )

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


class SecurityRuleExtractor(RuleExtractor):
    """安全规则提取器 - 专门处理安全类反馈"""

    def extract_rules(
        self,
        feedback_items: List[FeedbackItem],
        category: Optional[FeedbackCategory] = None
    ) -> List[LearnedRule]:
        """提取安全规则

        只处理安全类别的反馈，并添加安全验证标记
        """
        # 强制过滤安全类别
        security_items = [
            item for item in feedback_items
            if item.category == FeedbackCategory.SECURITY
        ]

        # 使用父类方法提取
        rules = super().extract_rules(security_items, FeedbackCategory.SECURITY)

        # 为安全规则添加特殊标记
        for rule in rules:
            rule.status = "security_verified"

        return rules

    def _extract_keywords(self, items: List[FeedbackItem]) -> List[str]:
        """提取安全相关关键词"""
        keywords = super()._extract_keywords(items)

        # 添加安全特定关键词
        security_keywords = [
            'injection', 'xss', 'csrf', 'sql', 'auth', 'crypto',
            'encryption', 'hardcoded', 'password', 'token', 'secret',
            'vulnerability', 'exploit', 'validation', 'sanitization'
        ]

        all_text = ' '.join(item.message.lower() for item in items)

        for kw in security_keywords:
            if kw in all_text and kw not in keywords:
                keywords.append(kw)

        return keywords[:10]


class RuleDeduplicator:
    """规则去重器 - 移除重复和相似的规则"""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self._deduped_count = 0

    def deduplicate(self, rules: List[LearnedRule]) -> List[LearnedRule]:
        """去重规则列表"""
        unique_rules = []
        seen_hashes: Set[str] = set()

        for rule in rules:
            rule_hash = self._compute_rule_hash(rule)

            # 检查是否有相似规则
            is_duplicate = False
            for seen_hash in seen_hashes:
                if self._are_similar(rule_hash, seen_hash):
                    is_duplicate = True
                    self._deduped_count += 1
                    break

            if not is_duplicate:
                unique_rules.append(rule)
                seen_hashes.add(rule_hash)

        return unique_rules

    def _compute_rule_hash(self, rule: LearnedRule) -> str:
        """计算规则哈希用于相似度比较"""
        # 基于类别、关键词和模式
        keywords_str = ' '.join(sorted(rule.pattern.context_keywords))
        patterns_str = ' '.join(sorted(rule.pattern.code_patterns[:3]))

        combined = (
            f"{rule.category.value}:"
            f"{keywords_str}:"
            f"{patterns_str}"
        )

        return combined.lower().replace(' ', '')

    def _are_similar(self, hash1: str, hash2: str) -> bool:
        """检查两个哈希是否相似"""
        # 简单实现：检查包含关系
        if len(hash1) < 10 or len(hash2) < 10:
            return hash1 == hash2

        # 检查一个是否包含另一个的核心部分
        if hash1 in hash2 or hash2 in hash1:
            return True

        # 计算编辑距离
        distance = self._levenshtein_distance(hash1, hash2)
        max_len = max(len(hash1), len(hash2))
        similarity = 1 - (distance / max_len)

        return similarity >= self.similarity_threshold

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]


class RuleValidator:
    """规则验证器 - 验证规则质量"""

    def __init__(
        self,
        min_quality_score: float = 0.5,
        min_tool_support: int = 1
    ):
        self.min_quality_score = min_quality_score
        self.min_tool_support = min_tool_support

    def validate(self, rule: LearnedRule) -> bool:
        """验证单个规则"""
        # 检查质量分数
        if rule.quality_score < self.min_quality_score:
            return False

        # 检查工具支持
        if len(rule.tools) < self.min_tool_support:
            return False

        # 检查模式有效性
        if not rule.pattern.file_patterns:
            return False

        # 检查类别有效性
        if not isinstance(rule.category, FeedbackCategory):
            return False

        return True

    def validate_batch(self, rules: List[LearnedRule]) -> List[LearnedRule]:
        """批量验证规则"""
        return [rule for rule in rules if self.validate(rule)]


# 导出
__all__ = [
    'RuleExtractor',
    'SecurityRuleExtractor',
    'RuleDeduplicator',
    'RuleValidator',
]
