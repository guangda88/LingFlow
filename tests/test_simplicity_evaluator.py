import pytest
import tempfile
from pathlib import Path

from lingflow.self_optimizer.simplicity_evaluator import SimplicityEvaluator, SimplicityMetrics, fallback_evaluate


class TestSimplicityMetrics:
    def test_init(self):
        m = SimplicityMetrics(
            total_lines=100,
            code_lines=60,
            comment_lines=20,
            blank_lines=20,
            avg_line_length=45.0,
            max_line_length=120,
            long_lines_count=5,
            duplication_rate=0.1,
            complex_lines=3,
        )
        assert m.total_lines == 100
        assert m.code_lines == 60
        assert m.duplication_rate == 0.1


class TestSimplicityEvaluatorInit:
    def test_default_path(self):
        e = SimplicityEvaluator()
        assert e.target_path == Path(".")

    def test_custom_path(self):
        e = SimplicityEvaluator("/tmp")
        assert e.target_path == Path("/tmp")


class TestEvaluate:
    def test_evaluate_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = SimplicityEvaluator(tmpdir)
            score = e.evaluate({})
            assert score == 0.0

    def test_evaluate_clean_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code = "x = 1\ny = 2\nz = x + y\n"
            (Path(tmpdir) / "clean.py").write_text(code)
            e = SimplicityEvaluator(tmpdir)
            score = e.evaluate({"max_line_length": 100})
            assert isinstance(score, float)

    def test_evaluate_with_long_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code = "x = " + "a" * 200 + "\n"
            (Path(tmpdir) / "long.py").write_text(code)
            e = SimplicityEvaluator(tmpdir)
            score = e.evaluate({"max_line_length": 100})
            assert score > 0

    def test_evaluate_with_duplication_penalty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            line = "x = 1 + 2 + 3\n"
            (Path(tmpdir) / "dup.py").write_text(line * 10)
            e = SimplicityEvaluator(tmpdir)
            score_default = e.evaluate({"max_line_length": 100, "duplication_penalty": 1.0})
            score_high = e.evaluate({"max_line_length": 100, "duplication_penalty": 5.0})
            assert score_high >= score_default

    def test_evaluate_with_complexity_threshold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code = "if a and b and c:\n    pass\n"
            (Path(tmpdir) / "complex.py").write_text(code)
            e = SimplicityEvaluator(tmpdir)
            score = e.evaluate({"max_line_length": 100})
            assert isinstance(score, float)


class TestAnalyzeSimplicity:
    def test_mixed_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code = "# comment\nx = 1\n\ny = 2\n"
            (Path(tmpdir) / "mixed.py").write_text(code)
            e = SimplicityEvaluator(tmpdir)
            metrics = e._analyze_simplicity({"max_line_length": 100})
            assert metrics.total_lines == 4
            assert metrics.comment_lines == 1
            assert metrics.blank_lines == 1
            assert metrics.code_lines == 2

    def test_empty_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "empty.py").write_text("")
            e = SimplicityEvaluator(tmpdir)
            metrics = e._analyze_simplicity({"max_line_length": 100})
            assert metrics.total_lines == 0

    def test_non_python_files_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "readme.txt").write_text("hello\nworld\n")
            e = SimplicityEvaluator(tmpdir)
            metrics = e._analyze_simplicity({"max_line_length": 100})
            assert metrics.total_lines == 0


class TestCalculateDuplicationRate:
    def test_no_duplication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "unique.py").write_text("x = 1\ny = 2\nz = 3\n")
            e = SimplicityEvaluator(tmpdir)
            rate = e._calculate_duplication_rate()
            assert rate == 0.0

    def test_with_duplication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "dup.py").write_text("x = 1\nx = 1\nx = 1\n")
            e = SimplicityEvaluator(tmpdir)
            rate = e._calculate_duplication_rate()
            assert rate > 0

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = SimplicityEvaluator(tmpdir)
            rate = e._calculate_duplication_rate()
            assert rate == 0.0


class TestCountComplexLines:
    def test_no_complex_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "simple.py").write_text("x = 1\ny = 2\n")
            e = SimplicityEvaluator(tmpdir)
            count = e._count_complex_lines()
            assert count == 0

    def test_with_complex_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code = "if a and b and c:\n    pass\nfor i in range(10): for j in range(10): pass\n"
            (Path(tmpdir) / "complex.py").write_text(code)
            e = SimplicityEvaluator(tmpdir)
            count = e._count_complex_lines()
            assert count >= 1


class TestGetCurrentMetrics:
    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = SimplicityEvaluator(tmpdir)
            metrics = e.get_current_metrics()
            assert metrics["total_lines"] == 0
            assert metrics["code_lines"] == 0
            assert metrics["duplication_rate"] == 0.0

    def test_with_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("x = 1\n# comment\n\ny = 2\n")
            e = SimplicityEvaluator(tmpdir)
            metrics = e.get_current_metrics()
            assert metrics["total_lines"] == 4
            assert metrics["code_lines"] == 2
            assert "avg_line_length" in metrics
            assert "max_line_length" in metrics


class TestFindDuplicateCodeBlocks:
    def test_no_duplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "unique.py").write_text("x = 1\ny = 2\nz = 3\na = 4\nb = 5\nc = 6\n")
            e = SimplicityEvaluator(tmpdir)
            dups = e.find_duplicate_code_blocks(min_lines=3)
            assert len(dups) == 0

    def test_with_duplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            block = "x = 1\ny = 2\nz = 3\nw = 4\nv = 5\n"
            (Path(tmpdir) / "a.py").write_text(block)
            (Path(tmpdir) / "b.py").write_text(block)
            e = SimplicityEvaluator(tmpdir)
            dups = e.find_duplicate_code_blocks(min_lines=5)
            assert len(dups) >= 1
            assert dups[0]["occurrences"] >= 2
            assert dups[0]["lines"] == 5

    def test_min_lines_parameter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.py").write_text("x = 1\ny = 2\n" * 3)
            e = SimplicityEvaluator(tmpdir)
            dups3 = e.find_duplicate_code_blocks(min_lines=3)
            dups10 = e.find_duplicate_code_blocks(min_lines=10)
            assert len(dups3) >= len(dups10)

    def test_max_10_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(15):
                (Path(tmpdir) / f"f{i}.py").write_text("x = 1\ny = 2\nz = 3\na = 4\nb = 5\n")
            e = SimplicityEvaluator(tmpdir)
            dups = e.find_duplicate_code_blocks(min_lines=5)
            assert len(dups) <= 10


class TestFallbackEvaluate:
    def test_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            score = fallback_evaluate({}, target_path=tmpdir)
            assert isinstance(score, float)
            assert score == 0.0
