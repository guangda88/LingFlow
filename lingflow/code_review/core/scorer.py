"""
代码质量评分器 - 加权评分系统

该模块提供了加权质量评分器，用于根据不同维度和严重程度
计算代码的总体质量得分。
"""

import logging
from typing import Dict, List, Any, Optional
from .severity import Severity, SeverityWeight, DIMENSION_WEIGHTS

logger = logging.getLogger(__name__)


class ScorerError(Exception):
    """评分器异常基类"""
    pass


class QualityScorer:
    """
    加权质量评分器

    该类根据代码审查结果中的问题数量和严重程度，
    计算各维度得分和加权总体得分。

    Attributes:
        dimension_weights: 各维度的权重配置

    Examples:
        >>> scorer = QualityScorer()
        >>> result = {'dimensions': {'security': {'issues': [], 'suggestions': []}}}
        >>> score = scorer.calculate_score(result)
    """

    def __init__(self, dimension_weights: Optional[Dict[str, float]] = None):
        """
        初始化评分器

        Args:
            dimension_weights: 各维度权重配置，如果为None则使用默认权重

        Raises:
            ValueError: 如果权重配置无效
        """
        if dimension_weights is None:
            self.dimension_weights = DIMENSION_WEIGHTS.copy()
        else:
            # 验证权重配置
            total_weight = sum(dimension_weights.values())
            if total_weight <= 0:
                raise ValueError("维度权重总和必须大于0")
            self.dimension_weights = dimension_weights.copy()

        logger.debug(f"评分器初始化完成，使用 {len(self.dimension_weights)} 个维度")

    def calculate_score(self, review_result: Dict[str, Any]) -> float:
        """
        计算综合质量得分

        得分计算方式:
        - 基础分: 5.0
        - 根据问题严重程度扣分
        - 根据维度权重计算加权总分

        Args:
            review_result: 审查结果字典，必须包含 'dimensions' 键

        Returns:
            float: 综合得分 (0-5)

        Raises:
            KeyError: 如果审查结果缺少必需的键
        """
        if 'dimensions' not in review_result:
            logger.warning("审查结果缺少 'dimensions' 键，返回0分")
            return 0.0

        dimension_scores = {}

        for dimension, data in review_result.get('dimensions', {}).items():
            issues = data.get('issues', [])
            suggestions = data.get('suggestions', [])

            # 计算扣分
            penalty = 0.0

            for issue in issues:
                try:
                    severity = Severity(issue.get('severity', 'low'))
                    penalty += SeverityWeight.get_weight(severity)
                except ValueError:
                    logger.warning(f"未知的严重程度: {issue.get('severity')}")
                    penalty += 1.0  # 默认扣分

            for suggestion in suggestions:
                try:
                    priority = Severity(suggestion.get('priority', 'low'))
                    penalty += SeverityWeight.get_weight(priority)
                except ValueError:
                    logger.warning(f"未知的优先级: {suggestion.get('priority')}")
                    penalty += 0.5  # 默认扣分

            # 计算维度得分 (5分满分，不低于0)
            base_score = 5.0
            dimension_score = max(0.0, base_score - penalty)
            dimension_scores[dimension] = dimension_score

            # 更新维度数据中的得分
            data['score'] = dimension_score

        # 计算加权总分
        total_score = 0.0
        total_weight = 0.0

        for dimension, score in dimension_scores.items():
            weight = self.dimension_weights.get(dimension, 0.0)
            total_score += score * weight
            total_weight += weight

        final_score = total_score / total_weight if total_weight > 0 else 0.0

        logger.debug(f"计算得分: {final_score:.2f} (权重: {total_weight:.2f})")

        return final_score

    def get_score_breakdown(self, review_result: Dict[str, Any]) -> Dict[str, float]:
        """
        获取各维度得分明细

        Args:
            review_result: 审查结果字典

        Returns:
            Dict[str, float]: 各维度得分字典
        """
        breakdown = {}
        for dimension, data in review_result.get('dimensions', {}).items():
            breakdown[dimension] = data.get('score', 0.0)
        return breakdown

    def get_score_grade(self, score: float) -> str:
        """
        获取评分等级

        等级划分:
        - A: 4.5-5.0 (优秀)
        - B: 4.0-4.5 (良好)
        - C: 3.0-4.0 (中等)
        - D: 2.0-3.0 (及格)
        - F: 0-2.0 (不及格)

        Args:
            score: 得分 (0-5)

        Returns:
            str: 等级字母 (A-F)
        """
        if score >= 4.5:
            return "A"
        elif score >= 4.0:
            return "B"
        elif score >= 3.0:
            return "C"
        elif score >= 2.0:
            return "D"
        else:
            return "F"

    def get_score_emoji(self, score: float) -> str:
        """
        获取评分对应的 emoji

        Args:
            score: 得分 (0-5)

        Returns:
            str: emoji 字符串
        """
        if score >= 4.5:
            return "⭐⭐⭐⭐⭐"
        elif score >= 4.0:
            return "⭐⭐⭐⭐"
        elif score >= 3.0:
            return "⭐⭐⭐"
        elif score >= 2.0:
            return "⭐⭐"
        elif score >= 1.0:
            return "⭐"
        else:
            return "❌"

    def get_dimension_weight(self, dimension: str) -> float:
        """
        获取指定维度的权重

        Args:
            dimension: 维度名称

        Returns:
            float: 权重值，如果维度不存在则返回0
        """
        return self.dimension_weights.get(dimension, 0.0)

    def set_dimension_weight(self, dimension: str, weight: float) -> None:
        """
        设置指定维度的权重

        Args:
            dimension: 维度名称
            weight: 权重值 (必须大于0)

        Raises:
            ValueError: 如果权重值无效
        """
        if weight <= 0:
            raise ValueError(f"权重值必须大于0: {weight}")
        self.dimension_weights[dimension] = weight
        logger.debug(f"维度 '{dimension}' 权重设置为 {weight}")

    def get_all_dimensions(self) -> List[str]:
        """
        获取所有维度名称

        Returns:
            List[str]: 维度名称列表
        """
        return list(self.dimension_weights.keys())
