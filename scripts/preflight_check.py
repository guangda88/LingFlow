"""
灵通 数据库操作前置检查清单

使用方法：在对任何外部数据库执行写操作之前，必须调用 preflight_check()
这是强制性的，不是可选的。
"""

import os

import asyncpg
import asyncio
from typing import Dict, List, Optional


async def preflight_check(conn: asyncpg.Connection, table: str, columns: List[str] = None) -> dict:
    """写入数据库前强制执行的前置检查

    Returns:
        dict: {
            'columns': {col_name: data_type},
            'check_constraints': [constraint definitions],
            'valid_values': {col_name: [valid values]} for enum-like columns,
            'foreign_keys': [{column, references_table, references_column}],
            'sequence_max': {serial_col: current_max} for serial columns,
        }
    """
    info = {'table': table}

    # 1. Column types
    cols = await conn.fetch("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = $1 ORDER BY ordinal_position
    """, table)
    info['columns'] = {c['column_name']: c['data_type'] for c in cols}

    # 2. Check constraints
    constraints = await conn.fetch("""
        SELECT conname, pg_get_constraintdef(oid) as definition
        FROM pg_constraint
        WHERE conrelid = $1::regclass AND contype = 'c'
    """, table)
    info['check_constraints'] = [{'name': c['conname'], 'definition': c['definition']} for c in constraints]

    # 3. Extract valid values from CHECK constraints containing ARRAY
    info['valid_values'] = {}
    for c in constraints:
        defn = c['definition']
        if 'ARRAY[' in defn:
            import re
            col_match = re.search(r'\((\w+)\)', defn)
            vals = re.findall(r"'([^']*)'", defn.split('ARRAY[')[1])
            if col_match and vals:
                info['valid_values'][col_match.group(1)] = vals

    # 4. Foreign keys
    fks = await conn.fetch("""
        SELECT
            kcu.column_name,
            ccu.table_name AS references_table,
            ccu.column_name AS references_column
        FROM information_schema.key_column_usage kcu
        JOIN information_schema.table_constraints tc ON kcu.constraint_name = tc.constraint_name
        JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_name = $1 AND tc.constraint_type = 'FOREIGN KEY'
    """, table)
    info['foreign_keys'] = [dict(f) for f in fks]

    # 5. Serial column max values
    info['sequence_max'] = {}
    for c in cols:
        if 'nextval' in (c['column_default'] or ''):
            seq = c['column_default'].split("'")[1] if "'" in c['column_default'] else ''
            col = c['column_name']
            if seq:
                ALLOWED_TABLES = {"documents", "textbook_nodes", "textbook_blocks_v2"}
                if table not in ALLOWED_TABLES:
                    raise ValueError(f"Invalid table name: {table}")
                if col not in info['columns']:
                    raise ValueError(f"Invalid column name: {col}")
                safe_table = await conn.fetchval("SELECT quote_ident($1)", table)
                safe_col = await conn.fetchval("SELECT quote_ident($1)", col)
                max_val = await conn.fetchval(
                    "SELECT MAX(" + safe_col + ") FROM " + safe_table
                )
                info['sequence_max'][col] = max_val

    return info


def format_preflight(info: dict) -> str:
    """格式化输出检查结果"""
    lines = [f"=== Preflight: {info['table']} ==="]
    lines.append(f"Columns: {info['columns']}")
    if info['check_constraints']:
        lines.append("Check constraints:")
        for c in info['check_constraints']:
            lines.append(f"  {c['name']}: {c['definition']}")
    if info['valid_values']:
        lines.append("Valid values:")
        for col, vals in info['valid_values'].items():
            lines.append(f"  {col}: {vals}")
    if info['foreign_keys']:
        lines.append("Foreign keys:")
        for fk in info['foreign_keys']:
            lines.append(f"  {fk['column_name']} -> {fk['references_table']}.{fk['references_column']}")
    if info['sequence_max']:
        lines.append(f"Sequence max: {info['sequence_max']}")
    return '\n'.join(lines)


if __name__ == "__main__":
    async def demo():
        conn = await asyncpg.connect(os.environ.get("DATABASE_URL", "postgresql://localhost:5436/zhineng_kb"))
        for table in ["documents", "textbook_nodes", "textbook_blocks_v2"]:
            info = await preflight_check(conn, table)
            print(format_preflight(info))
            print()
        await conn.close()

    asyncio.run(demo())
