#!/usr/bin/env python3
"""将 textbook_blocks_v2 中已导入的数据同步到 documents 表（灵知实际检索的表）

背景：batch_textbook_import.py 原来只写入 textbook_blocks_v2，但灵知的 retrieval
只查 documents 和 guoxue_content。这个脚本补录数据到 documents 表。
"""

import os

import asyncio
import asyncpg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5436/zhineng_kb")
BATCH_SIZE = 500


async def sync():
    conn = await asyncpg.connect(DB_URL)
    
    total = await conn.fetchval("""
        SELECT count(*) FROM textbook_blocks_v2 b
        JOIN textbook_nodes n ON b.node_id = n.id
        JOIN textbook_metadata m ON n.textbook_id = m.id
        WHERE n.textbook_id NOT SIMILAR TO '[0-9]+'
        AND b.content IS NOT NULL
    """)
    print(f"待同步: {total} 条")
    
    offset = 0
    synced = 0
    while offset < total:
        rows = await conn.fetch("""
            SELECT b.content, b.embedding, m.title, m.category, n.id as node_id
            FROM textbook_blocks_v2 b
            JOIN textbook_nodes n ON b.node_id = n.id
            JOIN textbook_metadata m ON n.textbook_id = m.id
            WHERE n.textbook_id NOT SIMILAR TO '[0-9]+'
            AND b.content IS NOT NULL
            ORDER BY b.id
            LIMIT $1 OFFSET $2
        """, BATCH_SIZE, offset)
        
        if not rows:
            break
        
        async with conn.transaction():
            for r in rows:
                doc_title = f"{r['title']} - {r['node_id'].split('_')[-1]}"
                emb = str(r['embedding']) if r['embedding'] else None
                await conn.execute(
                    """INSERT INTO documents (title, content, category, embedding)
                    VALUES ($1, $2, $3, $4::vector)
                    ON CONFLICT (title) DO NOTHING""",
                    doc_title, r['content'], '气功', emb,
                )
        
        synced += len(rows)
        offset += BATCH_SIZE
        print(f"  进度: {synced}/{total}")
    
    await conn.close()
    print(f"完成: {synced} 条已同步到 documents")


if __name__ == "__main__":
    asyncio.run(sync())
