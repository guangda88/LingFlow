# LingFlow SQLite 上下文管理设计

**日期**: 2026-03-30
**灵感来源**: Crush 上下文管理的 SQLite 实现
**目标**: 借鉴成熟设计，增强 LingFlow 的上下文管理能力

---

## 🎯 设计目标

### 为什么借鉴 Crush 的 SQLite 设计？

```
✅ 成熟稳定
  - 经过实际项目验证
  - 处理了大量真实场景
  - 稳定性有保障

✅ 高性能
  - SQLite 嵌入式数据库
  - 零配置部署
  - 优秀的读写性能

✅ 可追溯
  - 完整的消息历史
  - 元数据管理
  - 便于调试和分析

✅ 易集成
  - 单文件数据库
  - 标准 SQL 接口
  - 跨平台兼容
```

---

## 📊 数据库设计

### 核心表结构

```sql
-- 1. 会话表 (conversations)
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,  -- 会话唯一标识
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,  -- JSON 格式的元数据
    total_tokens INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0
);

CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- 2. 消息表 (messages)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    importance_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    compressed BOOLEAN DEFAULT FALSE,
    metadata TEXT,  -- JSON 格式的元数据
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_importance ON messages(importance_score);
CREATE INDEX idx_messages_compressed ON messages(compressed);

-- 3. 上下文状态表 (context_states)
CREATE TABLE context_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL UNIQUE,
    current_tokens INTEGER DEFAULT 0,
    threshold_tokens INTEGER DEFAULT 150000,
    compression_level INTEGER DEFAULT 0,  -- 0-5
    last_compression_at TIMESTAMP,
    last_compression_ratio REAL DEFAULT 0.0,
    metadata TEXT,  -- JSON 格式的元数据
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_context_states_conversation_id ON context_states(conversation_id);

-- 4. 压缩历史表 (compression_history)
CREATE TABLE compression_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    before_tokens INTEGER NOT NULL,
    after_tokens INTEGER NOT NULL,
    compression_ratio REAL NOT NULL,
    messages_removed INTEGER DEFAULT 0,
    compression_strategy TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT,  -- JSON 格式的详细信息
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_compression_history_conversation_id ON compression_history(conversation_id);
CREATE INDEX idx_compression_history_created_at ON compression_history(created_at);

-- 5. 评分历史表 (scoring_history)
CREATE TABLE scoring_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    importance_score REAL NOT NULL,
    relevance_score REAL DEFAULT 0.0,
    time_score REAL DEFAULT 0.0,
    quality_score REAL DEFAULT 0.0,
    scoring_method TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT,  -- JSON 格式的详细信息
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

CREATE INDEX idx_scoring_history_message_id ON scoring_history(message_id);
CREATE INDEX idx_scoring_history_created_at ON scoring_history(created_at);
```

---

## 🔧 Python 实现

### SQLite 管理器

```python
"""
LingFlow SQLite 上下文管理器

借鉴 Crush 的成熟设计，提供高性能的上下文管理
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
                WHERE conversation_id = ?
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
```

---

## 🚀 使用示例

```python
# 示例 1: 创建会话和添加消息
manager = get_context_manager(":memory:")

# 创建会话
conv = manager.create_conversation(
    session_id="test_session_001",
    metadata={"user": "test_user", "project": "lingflow"}
)

# 添加消息
msg1 = Message(
    role="user",
    content="Hello, how are you?",
    token_count=7,
    importance_score=0.5
)
manager.add_message(conv.id, msg1)

msg2 = Message(
    role="assistant",
    content="I'm doing well, thank you!",
    token_count=8,
    importance_score=0.6
)
manager.add_message(conv.id, msg2)

# 示例 2: 获取上下文状态
state = manager.get_context_state(conv.id)
print(f"Current tokens: {state['current_tokens']}")
print(f"Threshold: {state['threshold_tokens']}")

# 示例 3: 消息评分
manager.update_message_score(
    message_id=msg1.id,
    score=0.8,
    details={"relevance": 0.9, "quality": 0.7}
)

# 示例 4: 压缩上下文
low_importance_msgs = manager.get_low_importance_messages(conv.id, limit=5)
if low_importance_msgs:
    # 记录压缩
    manager.record_compression(
        conv_id=conv.id,
        before_tokens=state['current_tokens'],
        after_tokens=state['current_tokens'] - sum(m.token_count for m in low_importance_msgs),
        messages_removed=len(low_importance_msgs),
        strategy="tiered_compression",
        details={"level": 1}
    )

    # 标记为已压缩
    manager.mark_messages_compressed([m.id for m in low_importance_msgs])

# 示例 5: 获取统计信息
stats = manager.get_statistics(conv.id)
print(f"Total messages: {stats['messages']['total']}")
print(f"Total tokens: {stats['messages']['total_tokens']}")
print(f"Compression ratio: {stats['compression']['avg_ratio']:.2%}")
```

---

## 📊 性能优化

### 1. 索引策略

```sql
-- 高频查询索引
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_importance ON messages(importance_score);
CREATE INDEX idx_messages_compressed ON messages(compressed);
```

### 2. 批量操作

```python
def batch_add_messages(self, conv_id: int, messages: List[Message]) -> List[Message]:
    """批量添加消息"""
    with self.get_connection() as conn:
        # 使用 executemany 提升性能
        message_data = [
            (
                conv_id, msg.role, msg.content, msg.token_count,
                msg.importance_score,
                json.dumps(msg.metadata) if msg.metadata else None,
                msg.compressed
            )
            for msg in messages
        ]

        conn.executemany(
            """
            INSERT INTO messages (
                conversation_id, role, content, token_count,
                importance_score, metadata, compressed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            message_data
        )

        # 更新会话统计（一次性）
        total_tokens = sum(msg.token_count for msg in messages)
        conn.execute(
            """
            UPDATE conversations
            SET total_messages = total_messages + ?,
                total_tokens = total_tokens + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (len(messages), total_tokens, conv_id)
        )

        return messages
```

### 3. 缓存机制

```python
from functools import lru_cache
import threading

class CachedSQLiteContextManager(SQLiteContextManager):
    """带缓存的上下文管理器"""

    def __init__(self, db_path: str = ":memory:", cache_size: int = 100):
        super().__init__(db_path)
        self.cache_size = cache_size
        self._cache = {}
        self._lock = threading.Lock()

    @lru_cache(maxsize=100)
    def get_conversation(self, conv_id: int) -> Optional[Conversation]:
        """带缓存的会话获取"""
        return super().get_conversation(conv_id)

    def add_message(self, conv_id: int, message: Message) -> Message:
        """添加消息后清除缓存"""
        result = super().add_message(conv_id, message)
        # 清除相关缓存
        self.get_conversation.cache_clear()
        return result
```

---

## ✅ 总结

### SQLite 上下文管理的优势

```
✅ 成熟稳定
  - 借鉴 Crush 的验证
  - SQLite 的可靠性

✅ 高性能
  - 嵌入式零配置
  - 索引优化
  - 批量操作

✅ 可追溯
  - 完整历史
  - 压缩记录
  - 评分历史

✅ 易集成
  - 单文件部署
  - 标准 SQL
  - 跨平台
```

### 与 LingFlow 的整合

```python
# 在 LingFlow 中使用 SQLite 上下文管理
class LingFlowContextManager:
    """LingFlow 上下文管理器"""

    def __init__(self, db_path: str = ":memory:"):
        self.sqlite_manager = SQLiteContextManager(db_path)
        self.token_estimator = TokenEstimator()
        self.message_scorer = MessageScorer()

    def process_message(self, conv_id: int, role: str, content: str) -> Message:
        """处理并添加消息"""
        # 估算 token
        token_count = self.token_estimator.estimate(content)

        # 评分
        score = self.message_scorer.score(content, role)

        # 创建消息
        message = Message(
            role=role,
            content=content,
            token_count=token_count,
            importance_score=score
        )

        # 添加到数据库
        return self.sqlite_manager.add_message(conv_id, message)

    def should_compress(self, conv_id: int) -> bool:
        """判断是否需要压缩"""
        state = self.sqlite_manager.get_context_state(conv_id)
        return state['current_tokens'] >= state['threshold_tokens']

    def compress_context(self, conv_id: int, strategy: str = "auto") -> Dict:
        """压缩上下文"""
        state = self.sqlite_manager.get_context_state(conv_id)
        before_tokens = state['current_tokens']

        # 获取低重要性消息
        messages = self.sqlite_manager.get_low_importance_messages(conv_id)

        # 执行压缩
        removed_tokens = sum(msg.token_count for msg in messages)
        after_tokens = before_tokens - removed_tokens

        # 记录压缩
        self.sqlite_manager.record_compression(
            conv_id=conv_id,
            before_tokens=before_tokens,
            after_tokens=after_tokens,
            messages_removed=len(messages),
            strategy=strategy
        )

        # 标记为已压缩
        self.sqlite_manager.mark_messages_compressed([msg.id for msg in messages])

        return {
            "before_tokens": before_tokens,
            "after_tokens": after_tokens,
            "reduction_ratio": removed_tokens / before_tokens,
            "messages_removed": len(messages)
        }
```

---

**设计完成**: 2026-03-30
**版本**: 1.0
**灵感**: Crush 上下文管理的 SQLite 实现
**状态**: 待整合到 MVP
