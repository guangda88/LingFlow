import pytest

from lingflow.code_review.core.scorer import QualityScorer, ScorerError
from lingflow.code_review.core.severity import DIMENSION_WEIGHTS, Severity, SeverityWeight


class TestScorerError:
    def test_is_exception(self):
        assert issubclass(ScorerError, Exception)

    def test_raise(self):
        with pytest.raises(ScorerError):
            raise ScorerError("test")


class TestQualityScorerInit:
    def test_default_weights(self):
        s = QualityScorer()
        assert s.dimension_weights == DIMENSION_WEIGHTS.copy()

    def test_custom_weights(self):
        s = QualityScorer(dimension_weights={"quality": 0.5, "security": 0.5})
        assert s.dimension_weights == {"quality": 0.5, "security": 0.5}

    def test_invalid_weights_zero(self):
        with pytest.raises(ValueError):
            QualityScorer(dimension_weights={"a": 0})

    def test_invalid_weights_negative(self):
        with pytest.raises(ValueError):
            QualityScorer(dimension_weights={"a": -1})


class TestCalculateScore:
    def test_no_dimensions_key(self):
        s = QualityScorer()
        assert s.calculate_score({}) == 0.0

    def test_no_issues(self):
        s = QualityScorer(dimension_weights={"quality": 1.0})
        result = {"dimensions": {"quality": {"issues": [], "suggestions": []}}}
        score = s.calculate_score(result)
        assert score == 5.0

    def test_with_critical_issue(self):
        s = QualityScorer(dimension_weights={"security": 1.0})
        result = {"dimensions": {"security": {"issues": [{"severity": "critical"}], "suggestions": []}}}
        score = s.calculate_score(result)
        assert score < 5.0

    def test_with_high_issue(self):
        s = QualityScorer(dimension_weights={"quality": 1.0})
        result = {"dimensions": {"quality": {"issues": [{"severity": "high"}], "suggestions": []}}}
        score = s.calculate_score(result)
        assert 0 <= score < 5.0

    def test_with_multiple_issues(self):
        s = QualityScorer(dimension_weights={"quality": 1.0})
        result = {
            "dimensions": {
                "quality": {"issues": [{"severity": "high"}, {"severity": "medium"}, {"severity": "low"}], "suggestions": []}
            }
        }
        score = s.calculate_score(result)
        assert score < 5.0

    def test_with_suggestions(self):
        s = QualityScorer(dimension_weights={"quality": 1.0})
        result = {"dimensions": {"quality": {"issues": [], "suggestions": [{"priority": "medium"}]}}}
        score = s.calculate_score(result)
        assert score < 5.0

    def test_unknown_severity(self):
        s = QualityScorer(dimension_weights={"quality": 1.0})
        result = {"dimensions": {"quality": {"issues": [{"severity": "unknown_severity"}], "suggestions": []}}}
        score = s.calculate_score(result)
        assert isinstance(score, float)

    def test_unknown_priority(self):
        s = QualityScorer(dimension_weights={"quality": 1.0})
        result = {"dimensions": {"quality": {"issues": [], "suggestions": [{"priority": "unknown_priority"}]}}}
        score = s.calculate_score(result)
        assert isinstance(score, float)

    def test_multiple_dimensions(self):
        s = QualityScorer(dimension_weights={"quality": 0.5, "security": 0.5})
        result = {
            "dimensions": {
                "quality": {"issues": [], "suggestions": []},
                "security": {"issues": [], "suggestions": []},
            }
        }
        score = s.calculate_score(result)
        assert score == 5.0

    def test_score_floor_zero(self):
        s = QualityScorer(dimension_weights={"quality": 1.0})
        result = {"dimensions": {"quality": {"issues": [{"severity": "critical"}] * 20, "suggestions": []}}}
        score = s.calculate_score(result)
        assert score >= 0.0

    def test_weights_not_matching(self):
        s = QualityScorer(dimension_weights={"other_dim": 1.0})
        result = {"dimensions": {"quality": {"issues": [], "suggestions": []}}}
        score = s.calculate_score(result)
        assert score == 0.0

    def test_updates_score_in_data(self):
        s = QualityScorer(dimension_weights={"quality": 1.0})
        result = {"dimensions": {"quality": {"issues": [], "suggestions": []}}}
        s.calculate_score(result)
        assert result["dimensions"]["quality"]["score"] == 5.0


class TestGetScoreBreakdown:
    def test_with_scores(self):
        s = QualityScorer(dimension_weights={"quality": 1.0})
        result = {"dimensions": {"quality": {"score": 4.0, "issues": [], "suggestions": []}}}
        breakdown = s.get_score_breakdown(result)
        assert breakdown["quality"] == 4.0

    def test_missing_score_defaults_zero(self):
        s = QualityScorer()
        result = {"dimensions": {"quality": {"issues": []}}}
        breakdown = s.get_score_breakdown(result)
        assert breakdown["quality"] == 0.0

    def test_empty_dimensions(self):
        s = QualityScorer()
        breakdown = s.get_score_breakdown({"dimensions": {}})
        assert breakdown == {}


class TestGetScoreGrade:
    def test_grade_a(self):
        s = QualityScorer()
        assert s.get_score_grade(4.5) == "A"
        assert s.get_score_grade(5.0) == "A"
        assert s.get_score_grade(4.7) == "A"

    def test_grade_b(self):
        s = QualityScorer()
        assert s.get_score_grade(4.0) == "B"
        assert s.get_score_grade(4.4) == "B"

    def test_grade_c(self):
        s = QualityScorer()
        assert s.get_score_grade(3.0) == "C"
        assert s.get_score_grade(3.9) == "C"

    def test_grade_d(self):
        s = QualityScorer()
        assert s.get_score_grade(2.0) == "D"
        assert s.get_score_grade(2.9) == "D"

    def test_grade_f(self):
        s = QualityScorer()
        assert s.get_score_grade(0.0) == "F"
        assert s.get_score_grade(1.9) == "F"


class TestGetScoreEmoji:
    def test_emoji_star5(self):
        s = QualityScorer()
        assert s.get_score_emoji(4.5) == "\u2b50\u2b50\u2b50\u2b50\u2b50"

    def test_emoji_star4(self):
        s = QualityScorer()
        assert s.get_score_emoji(4.0) == "\u2b50\u2b50\u2b50\u2b50"

    def test_emoji_star3(self):
        s = QualityScorer()
        assert s.get_score_emoji(3.0) == "\u2b50\u2b50\u2b50"

    def test_emoji_star2(self):
        s = QualityScorer()
        assert s.get_score_emoji(2.0) == "\u2b50\u2b50"

    def test_emoji_star1(self):
        s = QualityScorer()
        assert s.get_score_emoji(1.0) == "\u2b50"

    def test_emoji_fail(self):
        s = QualityScorer()
        assert s.get_score_emoji(0.5) == "\u274c"


class TestDimensionWeightManagement:
    def test_get_dimension_weight(self):
        s = QualityScorer(dimension_weights={"quality": 0.3})
        assert s.get_dimension_weight("quality") == 0.3

    def test_get_missing_dimension(self):
        s = QualityScorer()
        assert s.get_dimension_weight("nonexistent") == 0.0

    def test_set_dimension_weight(self):
        s = QualityScorer(dimension_weights={"quality": 0.5})
        s.set_dimension_weight("quality", 0.8)
        assert s.get_dimension_weight("quality") == 0.8

    def test_set_new_dimension_weight(self):
        s = QualityScorer()
        s.set_dimension_weight("new_dim", 1.0)
        assert s.get_dimension_weight("new_dim") == 1.0

    def test_set_invalid_weight(self):
        s = QualityScorer()
        with pytest.raises(ValueError):
            s.set_dimension_weight("quality", 0)
        with pytest.raises(ValueError):
            s.set_dimension_weight("quality", -1)

    def test_get_all_dimensions(self):
        s = QualityScorer()
        dims = s.get_all_dimensions()
        assert isinstance(dims, list)
        assert len(dims) > 0
