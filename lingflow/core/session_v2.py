"""LingFlow v2 Session管理 - 基于Claude Code设计"""

from dataclasses import dataclass, field
from typing import Tuple, Dict, Any
from pathlib import Path
import json
from datetime import datetime
import uuid

@dataclass(frozen=True)
class SessionSnapshot:
    """不可变的Session快照（Claude Code风格）"""
    session_id: str
    messages: Tuple[str, ...]
    input_tokens: int
    output_tokens: int
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class SessionManager:
    """Session管理器"""

    def __init__(self, session_dir: Path = Path(".lingflow/sessions")):
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._current_messages = []
        self._current_input_tokens = 0
        self._current_output_tokens = 0

    def add_message(self, message: str, input_tokens: int = 0, output_tokens: int = 0):
        self._current_messages.append(message)
        self._current_input_tokens += input_tokens
        self._current_output_tokens += output_tokens

    def create_snapshot(self, session_id: str = None) -> SessionSnapshot:
        if session_id is None:
            session_id = str(uuid.uuid4())

        return SessionSnapshot(
            session_id=session_id,
            messages=tuple(self._current_messages),
            input_tokens=self._current_input_tokens,
            output_tokens=self._current_output_tokens,
            created_at=datetime.now().isoformat()
        )

    def save_session(self, session_id: str = None) -> Path:
        snapshot = self.create_snapshot(session_id)
        session_path = self.session_dir / f"{snapshot.session_id}.json"

        with open(session_path, 'w') as f:
            json.dump({
                'session_id': snapshot.session_id,
                'messages': snapshot.messages,
                'input_tokens': snapshot.input_tokens,
                'output_tokens': snapshot.output_tokens,
                'created_at': snapshot.created_at,
                'metadata': snapshot.metadata
            }, f, indent=2)

        return session_path

    def get_usage_summary(self) -> Dict[str, Any]:
        return {
            'message_count': len(self._current_messages),
            'input_tokens': self._current_input_tokens,
            'output_tokens': self._current_output_tokens,
            'total_tokens': self._current_input_tokens + self._current_output_tokens
        }
