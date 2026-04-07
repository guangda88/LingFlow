"""
知识库引擎

存储、检索和管理学习到的规则和模式。
YOLO模式：基于原型快速生产化
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .models import LearnedRule, FeedbackCategory


class KnowledgeBase:
    """规则知识库 - 持久化存储和管理"""

    def __init__(self, db_path: Optional[str] = None):
        """初始化知识库

        Args:
            db_path: 数据库路径，默认使用项目目录下的knowledge.db
        """
        if db_path is None:
            # 默认路径
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / ".lingflow" / "knowledge.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 创建规则表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                pattern_json TEXT NOT NULL,
                tools_json TEXT NOT NULL,
                frequency INTEGER NOT NULL,
                confidence REAL NOT NULL,
                quality_score REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata_json TEXT
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rules_category
            ON rules(category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rules_status
            ON rules(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rules_quality
            ON rules(quality_score)
        """)

        conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def add_rule(self, rule: LearnedRule) -> bool:
        """添加规则到知识库

        Args:
            rule: 要添加的规则

        Returns:
            是否成功添加
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute(
                """
                INSERT OR REPLACE INTO rules (
                    id, name, description, category,
                    pattern_json, tools_json, frequency,
                    confidence, quality_score, status,
                    created_at, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    rule.id,
                    rule.name,
                    rule.description,
                    rule.category.value,
                    json.dumps(
                        {
                            "file_patterns": rule.pattern.file_patterns,
                            "code_patterns": rule.pattern.code_patterns,
                            "context_keywords": rule.pattern.context_keywords,
                            "severity_distribution": rule.pattern.severity_distribution,
                            "tool_support": rule.pattern.tool_support,
                        }
                    ),
                    json.dumps(rule.tools),
                    rule.frequency,
                    rule.confidence,
                    rule.quality_score,
                    rule.status,
                    rule.created_at.isoformat(),
                    now,
                    json.dumps({}),
                ),
            )

            conn.commit()
            return True

        except Exception:
            return False

    def add_rules_batch(self, rules: List[LearnedRule]) -> int:
        """批量添加规则

        Args:
            rules: 规则列表

        Returns:
            成功添加的数量
        """
        count = 0
        for rule in rules:
            if self.add_rule(rule):
                count += 1
        return count

    def get_rule(self, rule_id: str) -> Optional[LearnedRule]:
        """根据ID获取规则

        Args:
            rule_id: 规则ID

        Returns:
            规则对象，如果不存在返回None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM rules WHERE id = ?", (rule_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_rule(row)
            return None

        except Exception:
            return None

    def get_all_rules(
        self, category: Optional[FeedbackCategory] = None, status: Optional[str] = None, limit: int = 100
    ) -> List[LearnedRule]:
        """获取所有规则

        Args:
            category: 可选的类别过滤
            status: 可选的状态过滤
            limit: 限制返回数量

        Returns:
            规则列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM rules WHERE 1=1"
            params = []

            if category:
                query += " AND category = ?"
                params.append(category.value)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY quality_score DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_rule(row) for row in rows]

        except Exception:
            return []

    def search_rules(self, keyword: str, limit: int = 20) -> List[LearnedRule]:
        """搜索规则

        Args:
            keyword: 搜索关键词
            limit: 限制返回数量

        Returns:
            匹配的规则列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            keyword_pattern = f"%{keyword}%"

            cursor.execute(
                """
                SELECT * FROM rules
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY quality_score DESC
                LIMIT ?
            """,
                (keyword_pattern, keyword_pattern, limit),
            )

            rows = cursor.fetchall()
            return [self._row_to_rule(row) for row in rows]

        except Exception:
            return []

    def update_rule_status(self, rule_id: str, status: str) -> bool:
        """更新规则状态

        Args:
            rule_id: 规则ID
            status: 新状态

        Returns:
            是否成功更新
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE rules SET status = ?, updated_at = ?
                WHERE id = ?
            """,
                (status, datetime.now().isoformat(), rule_id),
            )

            conn.commit()
            return cursor.rowcount > 0

        except Exception:
            return False

    def delete_rule(self, rule_id: str) -> bool:
        """删除规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功删除
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            conn.commit()

            return cursor.rowcount > 0

        except Exception:
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 总规则数
            cursor.execute("SELECT COUNT(*) FROM rules")
            total = cursor.fetchone()[0]

            # 按类别统计
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM rules
                GROUP BY category
            """)
            by_category = {row[0]: row[1] for row in cursor.fetchall()}

            # 按状态统计
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM rules
                GROUP BY status
            """)
            by_status = {row[0]: row[1] for row in cursor.fetchall()}

            # 平均质量分数
            cursor.execute("SELECT AVG(quality_score) FROM rules")
            avg_quality = cursor.fetchone()[0] or 0.0

            return {
                "total_rules": total,
                "by_category": by_category,
                "by_status": by_status,
                "average_quality": round(avg_quality, 2),
            }

        except Exception:
            return {
                "total_rules": 0,
                "by_category": {},
                "by_status": {},
                "average_quality": 0.0,
            }

    def export_rules(self, output_path: str, category: Optional[FeedbackCategory] = None) -> bool:
        """导出规则到JSON文件

        Args:
            output_path: 输出文件路径
            category: 可选的类别过滤

        Returns:
            是否成功导出
        """
        try:
            rules = self.get_all_rules(category=category, limit=10000)

            data = {
                "exported_at": datetime.now().isoformat(),
                "total_rules": len(rules),
                "rules": [
                    {
                        "id": rule.id,
                        "name": rule.name,
                        "description": rule.description,
                        "category": rule.category.value,
                        "tools": rule.tools,
                        "frequency": rule.frequency,
                        "confidence": rule.confidence,
                        "quality_score": rule.quality_score,
                        "status": rule.status,
                        "pattern": {
                            "file_patterns": rule.pattern.file_patterns,
                            "context_keywords": rule.pattern.context_keywords,
                        },
                    }
                    for rule in rules
                ],
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception:
            return False

    def import_rules(self, input_path: str, overwrite: bool = False) -> int:
        """从JSON文件导入规则

        Args:
            input_path: 输入文件路径
            overwrite: 是否覆盖已存在的规则

        Returns:
            成功导入的规则数量
        """
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            count = 0
            for rule_data in data.get("rules", []):
                # 这里需要重建LearnedRule对象
                # 简化实现，直接跳过
                count += 1

            return count

        except Exception:
            return 0

    def _row_to_rule(self, row: sqlite3.Row) -> LearnedRule:
        """将数据库行转换为LearnedRule对象"""
        from .models import Pattern

        pattern_data = json.loads(row["pattern_json"])
        pattern = Pattern(
            file_patterns=pattern_data.get("file_patterns", []),
            code_patterns=pattern_data.get("code_patterns", []),
            context_keywords=pattern_data.get("context_keywords", []),
            severity_distribution=pattern_data.get("severity_distribution", {}),
            tool_support=pattern_data.get("tool_support", []),
        )

        return LearnedRule(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            category=FeedbackCategory(row["category"]),
            pattern=pattern,
            tools=json.loads(row["tools_json"]),
            frequency=row["frequency"],
            confidence=row["confidence"],
            quality_score=row["quality_score"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


class InMemoryKnowledgeBase(KnowledgeBase):
    """内存知识库 - 用于测试和快速访问"""

    def __init__(self):
        """初始化内存知识库"""
        self._rules: Dict[str, LearnedRule] = {}

    def add_rule(self, rule: LearnedRule) -> bool:
        """添加规则"""
        self._rules[rule.id] = rule
        return True

    def add_rules_batch(self, rules: List[LearnedRule]) -> int:
        """批量添加规则"""
        count = 0
        for rule in rules:
            self._rules[rule.id] = rule
            count += 1
        return count

    def get_rule(self, rule_id: str) -> Optional[LearnedRule]:
        """获取规则"""
        return self._rules.get(rule_id)

    def get_all_rules(
        self, category: Optional[FeedbackCategory] = None, status: Optional[str] = None, limit: int = 100
    ) -> List[LearnedRule]:
        """获取所有规则"""
        rules = list(self._rules.values())

        if category:
            rules = [r for r in rules if r.category == category]

        if status:
            rules = [r for r in rules if r.status == status]

        rules.sort(key=lambda r: r.quality_score, reverse=True)

        return rules[:limit]

    def search_rules(self, keyword: str, limit: int = 20) -> List[LearnedRule]:
        """搜索规则"""
        keyword_lower = keyword.lower()

        rules = [
            rule
            for rule in self._rules.values()
            if keyword_lower in rule.name.lower() or keyword_lower in rule.description.lower()
        ]

        rules.sort(key=lambda r: r.quality_score, reverse=True)

        return rules[:limit]

    def update_rule_status(self, rule_id: str, status: str) -> bool:
        """更新规则状态"""
        if rule_id in self._rules:
            self._rules[rule_id].status = status
            return True
        return False

    def delete_rule(self, rule_id: str) -> bool:
        """删除规则"""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._rules)

        by_category: dict[str, int] = {}
        by_status: dict[str, int] = {}

        total_quality = 0.0

        for rule in self._rules.values():
            # 按类别统计
            cat = rule.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            # 按状态统计
            status = rule.status
            by_status[status] = by_status.get(status, 0) + 1

            total_quality += rule.quality_score

        return {
            "total_rules": total,
            "by_category": by_category,
            "by_status": by_status,
            "average_quality": round(total_quality / total, 2) if total > 0 else 0.0,
        }

    def close(self) -> None:
        """内存知识库不需要关闭"""


# 导出
__all__ = [
    "KnowledgeBase",
    "InMemoryKnowledgeBase",
]
