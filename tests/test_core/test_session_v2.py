"""Tests for lingflow.core.session_v2 module"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from lingflow.core.session_v2 import SessionManager, SessionSnapshot


class TestSessionSnapshot:
    """Test SessionSnapshot dataclass"""

    def test_create_snapshot(self):
        """Test creating a session snapshot"""
        snapshot = SessionSnapshot(
            session_id="test-session-1",
            messages=("Hello", "World"),
            input_tokens=100,
            output_tokens=50,
            created_at="2024-01-01T00:00:00",
        )
        assert snapshot.session_id == "test-session-1"
        assert snapshot.messages == ("Hello", "World")
        assert snapshot.input_tokens == 100
        assert snapshot.output_tokens == 50
        assert snapshot.created_at == "2024-01-01T00:00:00"

    def test_snapshot_is_immutable(self):
        """Test that SessionSnapshot is immutable (frozen)"""
        snapshot = SessionSnapshot(session_id="test", messages=(), input_tokens=0, output_tokens=0, created_at="")
        with pytest.raises(AttributeError):
            snapshot.session_id = "new-id"

    def test_snapshot_with_metadata(self):
        """Test snapshot with metadata"""
        metadata = {"user": "test_user", "tags": ["test", "demo"]}
        snapshot = SessionSnapshot(
            session_id="test",
            messages=(),
            input_tokens=0,
            output_tokens=0,
            created_at="",
            metadata=metadata,
        )
        assert snapshot.metadata == metadata


class TestSessionManager:
    """Test SessionManager class"""

    def test_init_default_session_dir(self, tmp_path):
        """Test initialization with default session directory"""
        manager = SessionManager(session_dir=tmp_path)
        assert manager.session_dir == tmp_path
        assert tmp_path.exists()
        assert manager._current_messages == []
        assert manager._current_input_tokens == 0
        assert manager._current_output_tokens == 0

    def test_add_message(self):
        """Test adding messages to session"""
        manager = SessionManager()
        manager.add_message("Hello", input_tokens=10, output_tokens=5)
        manager.add_message("World", input_tokens=10, output_tokens=5)

        assert len(manager._current_messages) == 2
        assert manager._current_messages == ["Hello", "World"]
        assert manager._current_input_tokens == 20
        assert manager._current_output_tokens == 10

    def test_add_message_accumulates_tokens(self):
        """Test that tokens accumulate correctly"""
        manager = SessionManager()
        manager.add_message("Msg1", input_tokens=100, output_tokens=50)
        manager.add_message("Msg2", input_tokens=200, output_tokens=100)

        assert manager._current_input_tokens == 300
        assert manager._current_output_tokens == 150

    def test_create_snapshot_without_session_id(self):
        """Test creating snapshot without providing session_id"""
        manager = SessionManager()
        manager.add_message("Test message", input_tokens=10, output_tokens=5)

        snapshot = manager.create_snapshot()

        assert snapshot.session_id is not None
        assert len(snapshot.session_id) > 0
        assert snapshot.messages == ("Test message",)
        assert snapshot.input_tokens == 10
        assert snapshot.output_tokens == 5
        assert snapshot.created_at is not None

    def test_create_snapshot_with_session_id(self):
        """Test creating snapshot with custom session_id"""
        manager = SessionManager()
        manager.add_message("Test", input_tokens=5, output_tokens=3)

        snapshot = manager.create_snapshot(session_id="custom-session-123")

        assert snapshot.session_id == "custom-session-123"
        assert snapshot.messages == ("Test",)

    def test_create_snapshot_preserves_messages_as_tuple(self):
        """Test that messages are stored as immutable tuple"""
        manager = SessionManager()
        manager.add_message("Msg1")
        manager.add_message("Msg2")

        snapshot = manager.create_snapshot()
        assert isinstance(snapshot.messages, tuple)
        assert snapshot.messages == ("Msg1", "Msg2")

    def test_save_session(self, tmp_path):
        """Test saving session to file"""
        manager = SessionManager(session_dir=tmp_path)
        manager.add_message("Hello", input_tokens=10, output_tokens=5)
        manager.add_message("World", input_tokens=15, output_tokens=8)

        session_path = manager.save_session(session_id="test-session")

        assert session_path.exists()
        assert session_path.name == "test-session.json"

    def test_save_session_creates_valid_json(self, tmp_path):
        """Test that saved session contains valid JSON"""
        manager = SessionManager(session_dir=tmp_path)
        manager.add_message("Test", input_tokens=5, output_tokens=3)

        session_path = manager.save_session(session_id="json-test")

        with open(session_path) as f:
            data = json.load(f)

        assert data["session_id"] == "json-test"
        assert data["messages"] == ["Test"]
        assert data["input_tokens"] == 5
        assert data["output_tokens"] == 3
        assert "created_at" in data

    def test_save_session_with_metadata(self, tmp_path):
        """Test saving session with default metadata"""
        manager = SessionManager(session_dir=tmp_path)
        manager.add_message("Test", input_tokens=5, output_tokens=3)

        # create_snapshot uses default metadata (empty dict)
        snapshot = manager.create_snapshot(session_id="meta-test")
        session_path = manager.save_session(session_id=snapshot.session_id)

        with open(session_path) as f:
            data = json.load(f)

        # Default metadata is empty dict
        assert data["metadata"] == {}

    def test_get_usage_summary_empty(self):
        """Test usage summary for empty session"""
        manager = SessionManager()
        summary = manager.get_usage_summary()

        assert summary["message_count"] == 0
        assert summary["input_tokens"] == 0
        assert summary["output_tokens"] == 0
        assert summary["total_tokens"] == 0

    def test_get_usage_summary_with_messages(self):
        """Test usage summary with messages"""
        manager = SessionManager()
        manager.add_message("Msg1", input_tokens=100, output_tokens=50)
        manager.add_message("Msg2", input_tokens=200, output_tokens=100)

        summary = manager.get_usage_summary()

        assert summary["message_count"] == 2
        assert summary["input_tokens"] == 300
        assert summary["output_tokens"] == 150
        assert summary["total_tokens"] == 450

    def test_get_usage_summary_total_tokens_calculation(self):
        """Test total tokens calculation"""
        manager = SessionManager()
        manager.add_message("Test", input_tokens=123, output_tokens=456)

        summary = manager.get_usage_summary()
        assert summary["total_tokens"] == 579

    def test_multiple_independent_managers(self, tmp_path):
        """Test that multiple managers maintain independent state"""
        manager1 = SessionManager(session_dir=tmp_path / "manager1")
        manager2 = SessionManager(session_dir=tmp_path / "manager2")

        manager1.add_message("Manager1", input_tokens=10, output_tokens=5)
        manager2.add_message("Manager2", input_tokens=20, output_tokens=10)

        summary1 = manager1.get_usage_summary()
        summary2 = manager2.get_usage_summary()

        assert summary1["message_count"] == 1
        assert summary2["message_count"] == 1
        assert summary1["input_tokens"] == 10
        assert summary2["input_tokens"] == 20
