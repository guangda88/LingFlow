#!/usr/bin/env python3
"""IMA 101K 记录嵌入生成调度器

为 zhineng_kb.ima_knowledge 中尚未生成嵌入的记录批量生成 BGE-M3 向量。
嵌入存储到 doc_embeddings_staging 表。

策略: 按 category 分批处理，每批 100 条，嵌入服务速率限制 ~8/s。
预计 101,707 - 3,579 = 98,128 条需要处理，约 3.4 小时（CPU）。
"""

import asyncio
import json
import logging
import os
import time
import urllib.request
from pathlib import Path
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/ai/LingFlow/scripts/ima_embedding.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("ima_embedding")

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5436/zhineng_kb")
EMBEDDING_URL = "http://localhost:8001/embed"
CHECKPOINT_FILE = Path("/home/ai/LingFlow/scripts/ima_embedding_checkpoint.json")
BATCH_SIZE = 100
EMBEDDING_DELAY = 0.12
EMBEDDING_TIMEOUT = 30


def generate_embedding(text: str, max_retries: int = 3) -> Optional[List[float]]:
    for attempt in range(max_retries + 1):
        try:
            data = json.dumps({"text": text}).encode("utf-8")
            req = urllib.request.Request(
                EMBEDDING_URL, data=data, headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=EMBEDDING_TIMEOUT)
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("embedding")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries:
                wait = 2 ** attempt * 2
                log.warning(f"429 rate limited, retry {attempt+1}/{max_retries} in {wait}s")
                time.sleep(wait)
                continue
            log.warning(f"Embedding HTTP error: {e.code} {e.reason}")
            return None
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1)
                continue
            log.warning(f"Embedding failed: {e}")
            return None
    return None


def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
    return {"last_id": 0, "total_embedded": 0, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")}


def save_checkpoint(cp: dict):
    cp["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    CHECKPOINT_FILE.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8")


async def run_ima_embedding(limit: int = 0, category: str = "", dry_run: bool = False):
    import asyncpg

    cp = load_checkpoint()
    pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=3, command_timeout=120)

    try:
        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM ima_knowledge")
            staged = await conn.fetchval("SELECT COUNT(*) FROM doc_embeddings_staging")
            pending = total - staged
            log.info(f"IMA: {total} total, {staged} embedded, {pending} pending")

            if dry_run:
                cats = await conn.fetch("SELECT category, COUNT(*) as cnt FROM ima_knowledge GROUP BY category ORDER BY cnt DESC")
                for c in cats:
                    print(f"  {c['category']}: {c['cnt']}")
                print(f"\n  Estimated time: {pending * 0.13 / 60:.0f} minutes (CPU)")
                return

        processed = 0
        while True:
            async with pool.acquire() as conn:
                query = """
                    SELECT ik.id, ik.name, ik.category
                    FROM ima_knowledge ik
                    WHERE ik.id > $1
                    AND NOT EXISTS (SELECT 1 FROM doc_embeddings_staging des WHERE des.id = ik.id)
                """
                args = [cp["last_id"]]
                if category:
                    query += " AND ik.category = $2"
                    args.append(category)
                query += f" ORDER BY ik.id LIMIT {BATCH_SIZE}"

                rows = await conn.fetch(query, *args)

            if not rows:
                log.info("所有待处理记录已完成")
                break

            for row in rows:
                text = row["name"].replace("\x00", "")
                if not text or len(text) < 2:
                    continue

                emb = await asyncio.get_event_loop().run_in_executor(None, generate_embedding, text)
                if emb is not None:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            """INSERT INTO doc_embeddings_staging (id, embedding)
                            VALUES ($1, $2::vector)
                            ON CONFLICT (id) DO UPDATE SET embedding = $2::vector""",
                            row["id"],
                            str(emb),
                        )

                cp["last_id"] = row["id"]
                cp["total_embedded"] = cp.get("total_embedded", 0) + (1 if emb else 0)
                processed += 1
                await asyncio.sleep(EMBEDDING_DELAY)

                if processed % 100 == 0:
                    save_checkpoint(cp)
                    log.info(f"进度: {processed} processed, {cp['total_embedded']} embedded, last_id={cp['last_id']}")

            if limit > 0 and processed >= limit:
                log.info(f"达到限制 {limit}, 停止")
                break

        save_checkpoint(cp)
        log.info(f"完成: {processed} processed, {cp.get('total_embedded', 0)} total embedded")

    finally:
        await pool.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="IMA 101K 嵌入生成调度器")
    parser.add_argument("--limit", type=int, default=0, help="限制处理数量")
    parser.add_argument("--category", type=str, default="", help="按分类过滤")
    parser.add_argument("--dry-run", action="store_true", help="仅统计")
    parser.add_argument("--reset", action="store_true", help="重置检查点")
    args = parser.parse_args()

    if args.reset:
        CHECKPOINT_FILE.write_text("{}", encoding="utf-8")
        print("检查点已重置")

    asyncio.run(run_ima_embedding(limit=args.limit, category=args.category, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
