#!/usr/bin/env python3
"""Batch embed doc_chunks into doc_embeddings_staging.

Usage:
  python3 batch_embed_chunks.py --categories 武术,心理学,儒家,气功,科学 --batch-size 100
  python3 batch_embed_chunks.py --categories 道家 --batch-size 100
  python3 batch_embed_chunks.py --dry-run --categories 佛家
"""
import argparse
import asyncio
import json
import logging
import time

import os

import asyncpg
import httpx

DB_URL = os.environ.get("ZHINENG_DB_URL", "")
EMBED_URL = os.environ.get("EMBED_SERVICE_URL", "http://localhost:8001") + "/embed_batch"
MODEL = "BGE-M3"
LOG_FILE = "/tmp/batch_embed_chunks.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger(__name__)


async def get_unembedded(conn, categories, limit=None):
    query = """
    SELECT dc.id, dc.content
    FROM doc_chunks dc
    JOIN documents d ON dc.doc_id = d.id
    WHERE d.category = ANY($1::text[])
      AND dc.content IS NOT NULL
      AND dc.id NOT IN (SELECT id FROM doc_embeddings_staging)
    ORDER BY dc.id
    """
    args = [categories]
    if limit:
        query += " LIMIT $2"
        args.append(limit)
    return await conn.fetch(query, *args, timeout=300)


async def embed_batch(client, texts):
    r = await client.post(EMBED_URL, json={"texts": texts, "model": MODEL}, timeout=60)
    r.raise_for_status()
    return r.json()["embeddings"]


async def insert_embeddings(conn, rows):
    if not rows:
        return
    await conn.executemany(
        """
        INSERT INTO doc_embeddings_staging (id, embedding)
        VALUES ($1, $2)
        ON CONFLICT (id) DO UPDATE SET embedding = $2
        """,
        rows,
        timeout=120,
    )


async def run(categories, batch_size, dry_run):
    conn = await asyncpg.connect(DB_URL, timeout=30, statement_cache_size=0)
    client = httpx.AsyncClient(timeout=60)

    chunks = await get_unembedded(conn, categories)
    total = len(chunks)
    log.info(f"Found {total:,} unembedded chunks for {categories}")

    if dry_run:
        log.info("DRY RUN - exiting")
        await conn.close()
        return

    done = 0
    failed = 0
    start = time.time()

    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]
        texts = [r["content"] for r in batch]
        ids = [r["id"] for r in batch]

        for retry in range(3):
            try:
                embeddings = await embed_batch(client, texts)
                rows = [(ids[j], str(embeddings[j])) for j in range(len(ids))]
                await insert_embeddings(conn, rows)
                done += len(batch)
                break
            except Exception as e:
                log.warning(f"Batch {i//batch_size} retry {retry}: {e}")
                if retry == 2:
                    failed += len(batch)
                    log.error(f"Batch {i//batch_size} FAILED permanently")
                await asyncio.sleep(2)

        elapsed = time.time() - start
        rate = done / elapsed if elapsed > 0 else 0
        if done % 1000 == 0 or done == total:
            log.info(f"Progress: {done}/{total} ({done/total*100:.1f}%) rate={rate:.1f}/s failed={failed}")

    elapsed = time.time() - start
    log.info(f"DONE: {done}/{total} embedded, {failed} failed, {elapsed:.0f}s")

    await client.aclose()
    await conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", required=True, help="Comma-separated categories")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    categories = [c.strip() for c in args.categories.split(",")]
    asyncio.run(run(categories, args.batch_size, args.dry_run))


if __name__ == "__main__":
    main()
