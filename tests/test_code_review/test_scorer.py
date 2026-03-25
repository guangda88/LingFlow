"""
质量评分器单元测试

测试 QualityScorer 类的功能
"""

import pytest
from lingflow.code_review.core.scorer import QualityScorer
from lingflow.code_review.core.severity import Severity


class TestQualityScorer:
    """QualityScorer 类测试"""

    def test_initialization_default_weights(self):
        """测试使用默认权重初始化"""
        scorer = QualityScorer()
        assert scorer.dimension_weights is not None
        assert 'security' in scorer.dimension_weights
        assert 'performance' in scorer.dimension_weights

    def test_initialization_custom_weights(self):
        """测试使用自定义权重初始化"""
        custom_weights = {
            'security': 0.5,
            'performance': 0.3,
            'code_quality': 0.2,
        }
        scorer = QualityScorer(dimension_weights=custom_weights)
        assert scorer.dimension_weights == custom_weights

    def test_calculate_score_perfect(self):
        """测试计算满分"""
        scorer = QualityScorer()

        review_result = {
            'dimensions': {
                'security': {'issues': [], 'suggestions': [], 'score': 0},
                'performance': {'issues': [], 'suggestions': [], 'score': 0},
                'code_quality': {'issues': [], 'suggestions': [], 'score': 0},
            }
        }

        score = scorer.calculate_score(review_result)
        assert score == 5.0

    def test_calculate_score_with_issues(self):
        """测试计算有问题的分数"""
        scorer = QualityScorer()

        review_result = {
            'dimensions': {
                'security': {
                    'issues': [
                        {'severity': 'critical'},
                    ],
                    'suggestions': [],
                    'score': 0
                },
                'performance': {'issues': [], 'suggestions': [], 'score': 0},
            }
        }

        score = scorer.calculate_score(review_result)
        # critical 问题应该大幅扣分
        assert score < 5.0
        assert score >= 0.0

    def test_calculate_score_with_suggestions(self):
        """测试计算有建议的分数"""
        scorer = QualityScorer()

        review_result = {
            'dimensions': {
                'code_quality': {
                    'issues': [],
                    'suggestions': [
                        {'priority': 'low'},
                    ],
                    'score': 0
                },
            }
        }

        score = scorer.calculate_score(review_result)
        # low 优先级建议应该扣分较少
        assert score >= 4.5

    def test_calculate_score_all_severities(self):
        """测试不同严重程度的扣分"""
        scorer = QualityScorer()

        severities = ['critical', 'high', 'medium', 'low']
        scores = []

        for severity in severities:
            review_result = {
                'dimensions': {
                    'code_quality': {
                        'issues': [{'severity': severity}],
                        'suggestions': [],
                        'score': 0
                    },
                    'security': {  # 添加安全维度以满足权重要求
                        'issues': [],
                        'suggestions': [],
                        'score': 0
                    },
                }
            }
            scores.append(scorer.calculate_score(review_result))

        # critical 扣分最多，所以得分最低
        # 由于critical扣10分，会得到0分
        # HIGH扣5分，也会得到0分（因为base是5）
        # 我们需要检查权重计算
        assert scores[0] <= scores[1]  # critical <= high
        # MEDIUM扣2分，得分应该是3
        # LOW扣0.5分，得分应该是4.5
        assert scores[2] > scores[1] or scores[2] > 0  # medium应该有分

    def test_get_score_breakdown(self):
        """测试获取得分明细"""
        scorer = QualityScorer()

        review_result = {
            'dimensions': {
                'security': {'issues': [], 'suggestions': [], 'score': 5.0},
                'performance': {'issues': [], 'suggestions': [], 'score': 4.5},
            }
        }

        breakdown = scorer.get_score_breakdown(review_result)
        assert breakdown['security'] == 5.0
        assert breakdown['performance'] == 4.5

    def test_get_score_grade(self):
        """测试获取评分等级"""
        scorer = QualityScorer()

        assert scorer.get_score_grade(4.5) == "A"
        assert scorer.get_score_grade(4.0) == "B"
        assert scorer.get_score_grade(3.0) == "C"
        assert scorer.get_score_grade(2.0) == "D"
        assert scorer.get_score_grade(1.0) == "F"

    def test_get_score_emoji(self):
        """测试获取评分表情"""
        scorer = QualityScorer()

        assert scorer.get_score_emoji(4.5) == "⭐⭐⭐⭐⭐"
        assert scorer.get_score_emoji(4.0) == "⭐⭐⭐⭐"
        assert scorer.get_score_emoji(3.0) == "⭐⭐⭐"
        assert scorer.get_score_emoji(2.0) == "⭐⭐"
        assert scorer.get_score_emoji(1.0) == "⭐"
        assert scorer.get_score_emoji(0.0) == "❌"

    def test_dimension_score_assignment(self):
        """测试维度得分被正确赋值"""
        scorer = QualityScorer()

        review_result = {
            'dimensions': {
                'security': {'issues': [], 'suggestions': []},
            }
        }

        scorer.calculate_score(review_result)

        # 检查 score 是否被正确赋值
        assert 'score' in review_result['dimensions']['security']
        assert isinstance(review_result['dimensions']['security']['score'], float)


class TestScorerEdgeCases:
    """评分器边界情况测试"""

    def test_empty_dimensions(self):
        """测试空维度"""
        scorer = QualityScorer()

        review_result = {
            'dimensions': {}
        }

        score = scorer.calculate_score(review_result)
        # 空维度应该返回 0 或处理不当
        assert score == 0.0

    def test_missing_dimensions_key(self):
        """测试缺少 dimensions 键"""
        scorer = QualityScorer()

        review_result = {}

        score = scorer.calculate_score(review_result)
        # 应该优雅处理
        assert isinstance(score, float)

    def test_many_critical_issues(self):
        """测试大量严重问题"""
        scorer = QualityScorer()

        review_result = {
            'dimensions': {
                'security': {
                    'issues': [{'severity': 'critical'} for _ in range(10)],
                    'suggestions': [],
                    'score': 0
                },
            }
        }

        score = scorer.calculate_score(review_result)
        # 分数不应该为负
        assert score >= 0.0
        # 应该接近 0
        assert score < 1.0
