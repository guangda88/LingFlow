"""
LingFlow SQLite Context Manager

基于 Crush 上下文管理的成熟设计，提供高性能的上下文管理
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """消息数据结构"""
    role: str
    content: str
    token_count: int = 0
    importance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    compressed: bool = False
    id: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "token_count": self.token_count,
            "importance_score": self.importance_score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "compressed": self.compressed,
            "id": self.id
        }


@dataclass
class Conversation:
    """会话数据结构"""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None

    @property
    def total_tokens(self) -> int:
        return sum(msg.token_count for msg in self.messages)

    @property
    def total_messages(self) -> int:
        return len(self.messages)


class SQLiteContextManager:
    """SQLite 上下文管理器"""

    def __init__(self, db_path: str = ":memory:"):
        """
        初始化上下文管理器

        Args:
            db_path: 数据库路径，默认为内存数据库
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def initialize_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            # 创建会话表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    total_tokens INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0
                )
            """)

            # 创建消息表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    importance_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    compressed BOOLEAN DEFAULT FALSE,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)

            # 创建上下文状态表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL UNIQUE,
                    current_tokens INTEGER DEFAULT 0,
                    threshold_tokens INTEGER DEFAULT 150000,
                    compression_level INTEGER DEFAULT 0,
                    last_compression_at TIMESTAMP,
                    last_compression_ratio REAL DEFAULT 0.0,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)

            # 创建压缩历史表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compression_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    before_tokens INTEGER NOT NULL,
                    after_tokens INTEGER NOT NULL,
                    compression_ratio REAL NOT NULL,
                    messages_removed INTEGER DEFAULT 0,
                    compression_strategy TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)

            # 创建评分历史表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scoring_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    importance_score REAL NOT NULL,
                    relevance_score REAL DEFAULT 0.0,
                    time_score REAL DEFAULT 0.0,
                    quality_score REAL DEFAULT 0.0,
                    scoring_method TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
                )
            """)

            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_importance ON messages(importance_score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_compressed ON messages(compressed)")

            logger.info(f"Database initialized at {self.db_path}")

    def create_conversation(self, session_id: str, metadata: Optional[Dict] = None) -> Conversation:
        """
        创建新会话

        Args:
            session_id: 会话唯一标识
            metadata: 元数据

        Returns:
            会话对象
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO conversations (session_id, metadata)
                VALUES (?, ?)
                """,
                (session_id, json.dumps(metadata) if metadata else None)
            )
            conv_id = cursor.lastrowid

            # 创建上下文状态
            conn.execute(
                """
                INSERT INTO context_states (conversation_id, threshold_tokens)
                VALUES (?, ?)
                """,
                (conv_id, 150000)  # 默认阈值 150K tokens
            )

            return self.get_conversation(conv_id)

    def get_conversation(self, conv_id: int) -> Optional[Conversation]:
        """
        获取会话

        Args:
            conv_id: 会话 ID

        Returns:
            会话对象或 None
        """
        with self.get_connection() as conn:
            # 获取会话信息
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conv_id,)
            ).fetchone()

            if not row:
                return None

            # 获取消息
            msg_rows = conn.execute(
                """
                SELECT * FROM messages
                WHERE conversation_id = ? AND compressed = FALSE
                ORDER BY created_at ASC
                """,
                (conv_id,)
            ).fetchall()

            messages = [
                Message(
                    role=row["role"],
                    content=row["content"],
                    token_count=row["token_count"],
                    importance_score=row["importance_score"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                    compressed=row["compressed"],
                    id=row["id"]
                )
                for row in msg_rows
            ]

            return Conversation(
                session_id=row["session_id"],
                messages=messages,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                id=row["id"]
            )

    def get_conversation_by_session(self, session_id: str) -> Optional[Conversation]:
        """
        通过会话 ID 获取会话

        Args:
            session_id: 会话唯一标识

        Returns:
            会话对象或 None
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM conversations WHERE session_id = ?",
                (session_id,)
            ).fetchone()

            if row:
                return self.get_conversation(row["id"])
            return None

    def add_message(self, conv_id: int, message: Message) -> Message:
        """
        添加消息到会话

        Args:
            conv_id: 会话 ID
            message: 消息对象

        Returns:
            添加后的消息对象（包含 ID）
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO messages (
                    conversation_id, role, content, token_count,
                    importance_score, metadata, compressed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conv_id,
                    message.role,
                    message.content,
                    message.token_count,
                    message.importance_score,
                    json.dumps(message.metadata) if message.metadata else None,
                    message.compressed
                )
            )
            message.id = cursor.lastrowid

            # 更新会话统计
            conn.execute(
                """
                UPDATE conversations
                SET total_messages = total_messages + 1,
                    total_tokens = total_tokens + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (message.token_count, conv_id)
            )

            # 更新上下文状态
            conn.execute(
                """
                UPDATE context_states
                SET current_tokens = current_tokens + ?
                WHERE conversation_id = ?
                """,
                (message.token_count, conv_id)
            )

            return message

    def get_context_state(self, conv_id: int) -> Optional[Dict[str, Any]]:
        """
        获取上下文状态

        Args:
            conv_id: 会话 ID

        Returns:
            上下文状态字典
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM context_states WHERE conversation_id = ?",
                (conv_id,)
            ).fetchone()

            if row:
                return {
                    "current_tokens": row["current_tokens"],
                    "threshold_tokens": row["threshold_tokens"],
                    "compression_level": row["compression_level"],
                    "last_compression_at": row["last_compression_at"],
                    "last_compression_ratio": row["last_compression_ratio"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                }
            return None

    def update_message_score(self, message_id: int, score: float, details: Optional[Dict] = None):
        """
        更新消息评分

        Args:
            message_id: 消息 ID
            score: 重要性评分
            details: 评分详情
        """
        with self.get_connection() as conn:
            # 更新消息评分
            conn.execute(
                """
                UPDATE messages
                SET importance_score = ?
                WHERE id = ?
                """,
                (score, message_id)
            )

            # 记录评分历史
            conn.execute(
                """
                INSERT INTO scoring_history (
                    message_id, importance_score, scoring_method, details
                )
                VALUES (?, ?, 'multi_dimensional', ?)
                """,
                (message_id, score, json.dumps(details) if details else None)
            )

    def get_low_importance_messages(self, conv_id: int, limit: int = 10) -> List[Message]:
        """
        获取低重要性消息

        Args:
            conv_id: 会话 ID
            limit: 返回数量

        Returns:
            消息列表
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM messages
                WHERE conversation_id = ? AND compressed = FALSE
                ORDER BY importance_score ASC
                LIMIT ?
                """,
                (conv_id, limit)
            ).fetchall()

            return [
                Message(
                    role=row["role"],
                    content=row["content"],
                    token_count=row["token_count"],
                    importance_score=row["importance_score"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                    compressed=row["compressed"],
                    id=row["id"]
                )
                for row in rows
            ]

    def mark_messages_compressed(self, message_ids: List[int]):
        """
        标记消息为已压缩

        Args:
            message_ids: 消息 ID 列表
        """
        if not message_ids:
            return

        with self.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE messages
                SET compressed = TRUE
                WHERE id IN ({','.join('?' * len(message_ids))})
                """,
                message_ids
            )

    def record_compression(
        self,
        conv_id: int,
        before_tokens: int,
        after_tokens: int,
        messages_removed: int,
        strategy: str,
        details: Optional[Dict] = None
    ):
        """
        记录压缩历史

        Args:
            conv_id: 会话 ID
            before_tokens: 压缩前 token 数
            after_tokens: 压缩后 token 数
            messages_removed: 删除的消息数
            strategy: 压缩策略
            details: 详细信息
        """
        compression_ratio = (before_tokens - after_tokens) / before_tokens if before_tokens > 0 else 0

        with self.get_connection() as conn:
            # 记录压缩历史
            conn.execute(
                """
                INSERT INTO compression_history (
                    conversation_id, before_tokens, after_tokens,
                    compression_ratio, messages_removed, compression_strategy, details
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conv_id,
                    before_tokens,
                    after_tokens,
                    compression_ratio,
                    messages_removed,
                    strategy,
                    json.dumps(details) if details else None
                )
            )

            # 更新上下文状态
            conn.execute(
                """
                UPDATE context_states
                SET current_tokens = ?,
                    compression_level = compression_level + 1,
                    last_compression_at = CURRENT_TIMESTAMP,
                    last_compression_ratio = ?
                WHERE conversation_id = ?
                """,
                (after_tokens, compression_ratio, conv_id)
            )

    def get_compression_history(self, conv_id: int, limit: int = 10) -> List[Dict]:
        """
        获取压缩历史

        Args:
            conv_id: 会话 ID
            limit: 返回数量

        Returns:
            压缩历史列表
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM compression_history
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (conv_id, limit)
            ).fetchall()

            return [
                {
                    "before_tokens": row["before_tokens"],
                    "after_tokens": row["after_tokens"],
                    "compression_ratio": row["compression_ratio"],
                    "messages_removed": row["messages_removed"],
                    "strategy": row["compression_strategy"],
                    "created_at": row["created_at"],
                    "details": json.loads(row["details"]) if row["details"] else {}
                }
                for row in rows
            ]

    def get_statistics(self, conv_id: int) -> Dict[str, Any]:
        """
        获取会话统计信息

        Args:
            conv_id: 会话 ID

        Returns:
            统计信息字典
        """
        with self.get_connection() as conn:
            # 基础统计
            conv_row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?",
                (conv_id,)
            ).fetchone()

            if not conv_row:
                return {}

            # 消息统计
            msg_stats = conn.execute(
                """
                SELECT
                    COUNT(*) as total_messages,
                    SUM(token_count) as total_tokens,
                    AVG(importance_score) as avg_importance,
                    COUNT(CASE WHEN compressed = TRUE THEN 1 END) as compressed_messages
                FROM messages
                WHERE conversation_id = ?
                """,
                (conv_id,)
            ).fetchone()

            # 压缩统计
            compression_stats = conn.execute(
                """
                SELECT
                    COUNT(*) as total_compressions,
                    AVG(compression_ratio) as avg_ratio,
                    SUM(messages_removed) as total_removed
                FROM compression_history
                WHERE conversation_id = ?
                """,
                (conv_id,)
            ).fetchone()

            return {
                "conversation": {
                    "id": conv_row["id"],
                    "session_id": conv_row["session_id"],
                    "created_at": conv_row["created_at"],
                    "updated_at": conv_row["updated_at"]
                },
                "messages": {
                    "total": msg_stats["total_messages"] or 0,
                    "total_tokens": msg_stats["total_tokens"] or 0,
                    "avg_importance": msg_stats["avg_importance"] or 0,
                    "compressed": msg_stats["compressed_messages"] or 0
                },
                "compression": {
                    "total_compressions": compression_stats["total_compressions"] or 0,
                    "avg_ratio": compression_stats["avg_ratio"] or 0,
                    "total_removed": compression_stats["total_removed"] or 0
                }
            }


# 全局实例
_context_manager: Optional[SQLiteContextManager] = None


def get_context_manager(db_path: str = ":memory:") -> SQLiteContextManager:
    """
    获取上下文管理器实例

    Args:
        db_path: 数据库路径

    Returns:
        上下文管理器实例
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = SQLiteContextManager(db_path)
        _context_manager.initialize_database()
    return _context_manager


__all__ = [
    "SQLiteContextManager",
    "Message",
    "Conversation",
    "get_context_manager"
]
