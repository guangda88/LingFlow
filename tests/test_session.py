import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from lingflow.context.session import save_context, load_context, print_recovery, SESSION_FILE


class TestSaveContext:
    def test_save_basic(self, tmp_path):
        session_file = tmp_path / "session.json"
        with patch("lingflow.context.session.SESSION_FILE", session_file):
            save_context("test summary")
            assert session_file.exists()
            data = json.loads(session_file.read_text())
            assert data["summary"] == "test summary"
            assert data["tasks"] == []
            assert data["next_steps"] == []
            assert "timestamp" in data

    def test_save_with_tasks(self, tmp_path):
        session_file = tmp_path / "session.json"
        with patch("lingflow.context.session.SESSION_FILE", session_file):
            tasks = [{"name": "task1", "done": True}, {"name": "task2", "done": False}]
            save_context("summary", tasks=tasks)
            data = json.loads(session_file.read_text())
            assert len(data["tasks"]) == 2

    def test_save_with_next_steps(self, tmp_path):
        session_file = tmp_path / "session.json"
        with patch("lingflow.context.session.SESSION_FILE", session_file):
            save_context("summary", next_steps=["step1", "step2"])
            data = json.loads(session_file.read_text())
            assert len(data["next_steps"]) == 2

    def test_creates_parent_dirs(self, tmp_path):
        session_file = tmp_path / "sub" / "dir" / "session.json"
        with patch("lingflow.context.session.SESSION_FILE", session_file):
            save_context("test")
            assert session_file.exists()


class TestLoadContext:
    def test_load_existing(self, tmp_path):
        session_file = tmp_path / "session.json"
        data = {"timestamp": "2026-01-01", "summary": "test", "tasks": [], "next_steps": []}
        session_file.write_text(json.dumps(data))
        with patch("lingflow.context.session.SESSION_FILE", session_file):
            result = load_context()
            assert result["summary"] == "test"

    def test_load_nonexistent(self, tmp_path):
        session_file = tmp_path / "nonexistent.json"
        with patch("lingflow.context.session.SESSION_FILE", session_file):
            result = load_context()
            assert result is None


class TestPrintRecovery:
    def test_no_context(self, tmp_path, capsys):
        session_file = tmp_path / "session.json"
        with patch("lingflow.context.session.SESSION_FILE", session_file):
            print_recovery()
            captured = capsys.readouterr()
            assert "没有找到" in captured.out

    def test_with_context(self, tmp_path, capsys):
        session_file = tmp_path / "session.json"
        data = {
            "timestamp": "2026-01-01T00:00:00",
            "summary": "test summary",
            "tasks": [{"name": "task1", "done": True}, {"name": "task2", "done": False}],
            "next_steps": ["step1"],
        }
        session_file.write_text(json.dumps(data))
        with patch("lingflow.context.session.SESSION_FILE", session_file):
            print_recovery()
            captured = capsys.readouterr()
            assert "test summary" in captured.out
            assert "task1" in captured.out
            assert "step1" in captured.out

    def test_empty_tasks_and_steps(self, tmp_path, capsys):
        session_file = tmp_path / "session.json"
        data = {
            "timestamp": "2026-01-01",
            "summary": "summary only",
            "tasks": [],
            "next_steps": [],
        }
        session_file.write_text(json.dumps(data))
        with patch("lingflow.context.session.SESSION_FILE", session_file):
            print_recovery()
            captured = capsys.readouterr()
            assert "summary only" in captured.out
