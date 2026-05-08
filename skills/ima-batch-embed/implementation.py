"""IMA 知识库批量嵌入生成

从 ima_knowledge 表读取未嵌入记录，批量调用 /embed_batch，
写入 doc_embeddings_staging 表。支持断点续跑。
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
import httpx

log = logging.getLogger("ima-batch-embed")

DB_URL = os.environ.get("DATABASE_URL", "")
EMBEDDING_URL = "http://localhost:8001/embed_batch"
DEFAULT_BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
HTTP_TIMEOUT = 120.0
DB_TIMEOUT = 180


async def _fetch_pending(
    conn: asyncpg.Connection,
    last_id: int,
    batch_size: int,
    category: str,
) -> List[asyncpg.Record]:
    query = """
        SELECT ik.id, ik.name, ik.category
        FROM ima_knowledge ik
        WHERE ik.id > $1
    """
    args: list = [last_id]
    if category:
        query += " AND ik.category = $2"
        args.append(category)
    query += " ORDER BY ik.id LIMIT $%d" % (len(args) + 1)
    args.append(batch_size)
    return await conn.fetch(query, *args)


async def _embed_batch(
    texts: List[str], client: httpx.AsyncClient
) -> List[Optional[List[float]]]:
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await client.post(
                EMBEDDING_URL,
                json={"texts": texts},
                timeout=HTTP_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("embeddings", [])
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                log.warning(f"429 rate limited, retry {attempt+1}/{MAX_RETRIES} in {delay}s")
                await asyncio.sleep(delay)
                continue
            log.error(f"Embedding HTTP {e.response.status_code}: {e.response.text[:200]}")
            return [None] * len(texts)
        except Exception as e:
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1)
                continue
            log.error(f"Embedding failed: {e}")
            return [None] * len(texts)
    return [None] * len(texts)


async def _write_staging(
    conn: asyncpg.Connection,
    rows: List[asyncpg.Record],
    embeddings: List[Optional[List[float]]],
) -> int:
    written = 0
    for row, emb in zip(rows, embeddings):
        if emb is None:
            continue
        await conn.execute(
            """
            INSERT INTO doc_embeddings_staging (id, embedding)
            VALUES ($1, $2::vector)
            ON CONFLICT (id) DO UPDATE SET embedding = $2::vector
            """,
            row["id"],
            str(emb),
        )
        written += 1
    return written


async def execute_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    batch_size = params.get("batch_size", DEFAULT_BATCH_SIZE)
    limit = params.get("limit", 0)
    category = params.get("category", "")
    dry_run = params.get("dry_run", False)
    resume = params.get("resume", True)

    pool = await asyncpg.create_pool(
        DB_URL, min_size=1, max_size=3, command_timeout=DB_TIMEOUT
    )
    start_time = time.time()

    try:
        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM ima_knowledge")
            staged = await conn.fetchval("SELECT COUNT(*) FROM doc_embeddings_staging") if resume else 0
            pending = total - staged

            result = {
                "total_records": total,
                "already_staged": staged,
                "pending": pending,
                "processed": 0,
                "embedded": 0,
                "failed": 0,
                "status": "dry_run" if dry_run else "pending",
            }

            if dry_run:
                cats = await conn.fetch(
                    "SELECT category, COUNT(*) as cnt FROM ima_knowledge GROUP BY category ORDER BY cnt DESC"
                )
                result["categories"] = {r["category"]: r["cnt"] for r in cats}
                result["estimated_minutes"] = round(pending / batch_size * 1.3 / 60, 1)
                result["status"] = "dry_run"
                return result

            if pending <= 0:
                result["status"] = "complete"
                return result

        processed = 0
        embedded = 0
        failed = 0
        last_id = 0

        async with httpx.AsyncClient() as client:
            while True:
                async with pool.acquire() as conn:
                    rows = await _fetch_pending(conn, last_id, batch_size, category)

                if not rows:
                    break

                texts = []
                for row in rows:
                    text = row["name"].replace("\x00", "").strip()
                    if len(text) < 2:
                        text = "（空）"
                    texts.append(text)

                embeddings = await _embed_batch(texts, client)

                emb_count = sum(1 for e in embeddings if e is not None)
                fail_count = len(embeddings) - emb_count

                async with pool.acquire() as conn:
                    written = await _write_staging(conn, rows, embeddings)

                processed += len(rows)
                embedded += written
                failed += fail_count
                last_id = rows[-1]["id"]

                if processed % 1000 == 0 or processed == pending:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    log.info(
                        f"进度: {processed}/{pending} ({rate:.0f}/s), "
                        f"embedded={embedded}, failed={failed}"
                    )

                if 0 < limit <= processed:
                    break

        elapsed = time.time() - start_time
        result.update({
            "processed": processed,
            "embedded": embedded,
            "failed": failed,
            "elapsed_seconds": round(elapsed, 2),
            "status": "complete",
        })
        return result

    finally:
        await pool.close()
