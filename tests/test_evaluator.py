import os
import tempfile
from pathlib import Path

import pytest

from lingflow.self_optimizer.evaluator import StructureEvaluator, StructureMetrics, _get_code_review_module, fallback_evaluate


class TestStructureMetrics:
    def test_init(self):
        m = StructureMetrics(
            total_classes=10,
            large_classes=2,
            total_methods=50,
            complex_methods=5,
            avg_complexity=3.5,
            avg_class_size=100.0,
            avg_method_count=5.0,
            high_coupling=1,
            violations=8,
        )
        assert m.total_classes == 10
        assert m.large_classes == 2
        assert m.violations == 8


class TestStructureEvaluatorInit:
    def test_default_path(self):
        e = StructureEvaluator()
        assert e.target_path == Path(".")

    def test_custom_path(self):
        e = StructureEvaluator("/tmp")
        assert e.target_path == Path("/tmp")


class TestEvaluate:
    def test_evaluate_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = StructureEvaluator(tmpdir)
            score = e.evaluate({"max_class_size": 200, "max_method_count": 15, "max_complexity": 10})
            assert score == 0.0

    def test_evaluate_simple_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "simple.py"
            py_file.write_text("x = 1\ny = 2\n")
            e = StructureEvaluator(tmpdir)
            score = e.evaluate({"max_class_size": 200, "max_method_count": 15, "max_complexity": 10})
            assert score == 0.0

    def test_evaluate_with_large_class(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lines = ["class BigClass:"]
            for i in range(50):
                lines.append(f"    def method_{i}(self): pass")
            lines.append("")
            (Path(tmpdir) / "big.py").write_text("\n".join(lines))
            e = StructureEvaluator(tmpdir)
            score = e.evaluate({"max_class_size": 10, "max_method_count": 5, "max_complexity": 10})
            assert score > 0

    def test_evaluate_with_complex_method(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code = "class C:\n"
            code += "    def complex(self):\n"
            for i in range(20):
                code += f"        if x == {i}: pass\n"
            (Path(tmpdir) / "complex.py").write_text(code)
            e = StructureEvaluator(tmpdir)
            score = e.evaluate({"max_class_size": 200, "max_method_count": 15, "max_complexity": 5})
            assert score > 0

    def test_evaluate_syntax_error_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "bad.py").write_text("def broken(:\n  pass\n")
            (Path(tmpdir) / "good.py").write_text("x = 1\n")
            e = StructureEvaluator(tmpdir)
            score = e.evaluate({"max_class_size": 200})
            assert score == 0.0


class TestAnalyzeStructure:
    def test_no_python_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "readme.txt").write_text("hello")
            e = StructureEvaluator(tmpdir)
            metrics = e._analyze_structure({})
            assert metrics.total_classes == 0
            assert metrics.total_methods == 0

    def test_mixed_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code = (
                "class MyClass:\n"
                "    def method_a(self):\n"
                "        if True:\n"
                "            pass\n"
                "    def method_b(self):\n"
                "        return 1\n"
                "\n"
                "x = 1\n"
            )
            (Path(tmpdir) / "mixed.py").write_text(code)
            e = StructureEvaluator(tmpdir)
            metrics = e._analyze_structure({"max_class_size": 200, "max_method_count": 15, "max_complexity": 10})
            assert metrics.total_classes == 1
            assert metrics.total_methods == 2


class TestCountClassLines:
    def test_empty_class(self):
        import ast

        e = StructureEvaluator()
        node = ast.parse("class C: pass").body[0]
        result = e._count_class_lines(node, "class C: pass")
        assert isinstance(result, int)

    def test_class_with_body(self):
        import ast

        e = StructureEvaluator()
        code = "class C:\n    def m(self): pass\n"
        node = ast.parse(code).body[0]
        result = e._count_class_lines(node, code)
        assert result >= 2


class TestCalculateComplexity:
    def test_simple_function(self):
        import ast

        e = StructureEvaluator()
        node = ast.parse("def f(): pass").body[0]
        assert e._calculate_complexity(node) == 1

    def test_function_with_if(self):
        import ast

        e = StructureEvaluator()
        node = ast.parse("def f():\n    if x: pass").body[0]
        assert e._calculate_complexity(node) == 2

    def test_function_with_loop(self):
        import ast

        e = StructureEvaluator()
        node = ast.parse("def f():\n    for i in range(10): pass\n    while True: pass").body[0]
        assert e._calculate_complexity(node) == 3

    def test_function_with_boolop(self):
        import ast

        e = StructureEvaluator()
        node = ast.parse("def f():\n    if a and b and c: pass").body[0]
        c = e._calculate_complexity(node)
        assert c >= 2

    def test_function_with_try_except(self):
        import ast

        e = StructureEvaluator()
        node = ast.parse("def f():\n    try: pass\n    except: pass").body[0]
        assert e._calculate_complexity(node) == 2


class TestGetCurrentMetrics:
    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = StructureEvaluator(tmpdir)
            metrics = e.get_current_metrics()
            assert metrics["total_classes"] == 0
            assert metrics["total_methods"] == 0
            assert metrics["structure_violations"] == 0

    def test_with_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code = "class A:\n    def m(self): pass\n"
            (Path(tmpdir) / "a.py").write_text(code)
            e = StructureEvaluator(tmpdir)
            metrics = e.get_current_metrics()
            assert metrics["total_classes"] == 1
            assert metrics["total_methods"] == 1
            assert "avg_complexity" in metrics


class TestRunCodeReview:
    def test_returns_result_or_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = StructureEvaluator(tmpdir)
            result = e.run_code_review()
            assert result is None or isinstance(result, dict)


class TestGetCodeReviewModule:
    def test_module_loads(self):
        module, spec = _get_code_review_module()
        assert module is not None or spec is None


class TestFallbackEvaluate:
    def test_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            score = fallback_evaluate({"max_class_size": 200}, target_path=tmpdir)
            assert score == 0.0
