import tempfile

from lingflow.code_review.core.reporter import ReportGenerator


class TestReportGenerator:
    def test_generate_text(self):
        r = ReportGenerator("text")
        result = r.generate(
            {
                "overall_score": 4.5,
                "dimensions": {
                    "quality": {"score": 4.0, "issues": ["issue1", "issue2"]},
                    "security": {"score": 5.0, "issues": []},
                },
                "reviewed_files": ["a.py", "b.py"],
            }
        )
        assert "4.50" in result
        assert "quality" in result

    def test_generate_text_no_score(self):
        r = ReportGenerator("text")
        result = r.generate({"reviewed_files": ["a.py"]})
        assert "审查文件数" in result

    def test_generate_json(self):
        r = ReportGenerator("json")
        data = {"overall_score": 3.0}
        result = r.generate(data)
        assert '"overall_score"' in result

    def test_generate_markdown(self):
        r = ReportGenerator("markdown")
        result = r.generate(
            {
                "overall_score": 4.0,
                "dimensions": {
                    "quality": {"score": 4.0, "issues": ["bad code"]},
                },
            }
        )
        assert "# 代码审查报告" in result
        assert "quality" in result
        assert "bad code" in result

    def test_generate_markdown_no_issues(self):
        r = ReportGenerator("markdown")
        result = r.generate(
            {
                "overall_score": 5.0,
                "dimensions": {"perf": {"score": 5.0, "issues": []}},
            }
        )
        assert "perf" in result

    def test_save_to_file(self):
        r = ReportGenerator()
        with tempfile.TemporaryDirectory() as tmpdir:
            from pathlib import Path

            path = Path(tmpdir) / "sub" / "report.txt"
            r.save_to_file("report content", path)
            assert path.read_text() == "report content"

    def test_generate_filename(self):
        r = ReportGenerator()
        name = r.generate_filename("review")
        assert name.startswith("review_")
        assert len(name) > 10

    def test_default_format_text(self):
        r = ReportGenerator()
        result = r.generate({"overall_score": 3.0})
        assert "总体评分" in result
