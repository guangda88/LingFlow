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
    """Session管理器

    管理会话状态、消息历史和 token 使用量。
    """

    def __init__(self, session_dir: Path = Path(".lingflow/sessions")):
        """初始化 SessionManager

        Args:
            session_dir: 会话存储目录路径
        """
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._current_messages = []
        self._current_input_tokens = 0
        self._current_output_tokens = 0

    def add_message(self, message: str, input_tokens: int = 0, output_tokens: int = 0):
        """添加消息到当前会话

        Args:
            message: 消息内容
            input_tokens: 输入 token 数量
            output_tokens: 输出 token 数量
        """
        self._current_messages.append(message)
        self._current_input_tokens += input_tokens
        self._current_output_tokens += output_tokens

    def create_snapshot(self, session_id: str = None) -> SessionSnapshot:
        """创建当前会话快照

        Args:
            session_id: 会话 ID，如果为 None 则自动生成

        Returns:
            SessionSnapshot: 会话快照对象
        """
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
        """保存当前会话到文件

        Args:
            session_id: 会话 ID，如果为 None 则自动生成

        Returns:
            Path: 保存的会话文件路径
        """
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
        """获取当前会话使用摘要

        Returns:
            Dict[str, Any]: 包含消息数量、token 使用量的摘要
        """
        return {
            'message_count': len(self._current_messages),
            'input_tokens': self._current_input_tokens,
            'output_tokens': self._current_output_tokens,
            'total_tokens': self._current_input_tokens + self._current_output_tokens
        }
