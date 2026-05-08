"""knowledge-embed 技能实现 — 向量化并写入数据库

Phase 0 验证结论：
- Embedding批量接口: POST /embed_batch {"texts": [...]} → {"embeddings": [[...],[...]]}
- 单条接口: POST /embed {"text": "..."} → {"embedding": [...]}
- documents表: id(serial), title, content, category, source_file, metadata(jsonb)
- doc_chunks表: id(serial), doc_id(FK→documents.id), chunk_index, content,
  start_offset, end_offset, embedding(vector), char_count
- 唯一约束: (doc_id, chunk_index)
- 外键: doc_id REFERENCES documents(id) ON DELETE CASCADE
"""

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_EMBEDDING_URL = "http://localhost:8001"
_DEFAULT_DB_URL = os.environ.get("DATABASE_URL", "")


def embed_chunks(params: dict[str, Any]) -> dict[str, Any]:
    chunks = params.get("chunks")
    if not chunks:
        return {"error": "请提供 chunks 参数（由 knowledge-chunk 输出）"}

    doc_title = params.get("doc_title", "unknown")
    doc_content = params.get("doc_content", "")
    category = params.get("category", "气功")
    source_file = params.get("source_file")
    embedding_url = params.get("embedding_url", _DEFAULT_EMBEDDING_URL)
    db_url = params.get("db_url", _DEFAULT_DB_URL)
    batch_size = params.get("batch_size", 16)
    dry_run = params.get("dry_run", False)

    try:
        import httpx
    except ImportError:
        return {"error": "需要安装 httpx: pip install httpx"}

    try:
        import asyncpg
    except ImportError:
        return {"error": "需要安装 asyncpg: pip install asyncpg"}

    async def _run():
        if dry_run:
            return _dry_run(chunks, doc_title, batch_size)

        embedded = 0
        failed = 0
        batch_count = 0

        conn = await asyncpg.connect(db_url)
        try:
            doc_id = await _ensure_document(
                conn, doc_title, doc_content, category, source_file
            )

            async with httpx.AsyncClient(timeout=60.0) as client:
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i : i + batch_size]
                    batch_count += 1

                    contents = [
                        c["content"] if isinstance(c, dict) else str(c)
                        for c in batch
                    ]

                    try:
                        resp = await client.post(
                            f"{embedding_url}/embed_batch",
                            json={"texts": contents},
                        )
                        resp.raise_for_status()
                        vectors = resp.json().get("embeddings", [])
                    except Exception as e:
                        logger.warning(
                            "Embedding batch %d failed: %s", batch_count, e
                        )
                        failed += len(batch)
                        continue

                    if not vectors or len(vectors) != len(batch):
                        logger.warning(
                            "Embedding batch %d returned %d vectors for %d texts",
                            batch_count,
                            len(vectors) if vectors else 0,
                            len(batch),
                        )
                        failed += len(batch)
                        continue

                    for j, (chunk, vector) in enumerate(zip(batch, vectors)):
                        content = contents[j]
                        start_offset = (
                            chunk.get("start") if isinstance(chunk, dict) else None
                        )
                        end_offset = (
                            chunk.get("end") if isinstance(chunk, dict) else None
                        )
                        chunk_idx = (
                            chunk.get("index", i + j)
                            if isinstance(chunk, dict)
                            else i + j
                        )
                        try:
                            await conn.execute(
                                """
                                INSERT INTO doc_chunks
                                    (doc_id, chunk_index, content, start_offset,
                                     end_offset, embedding)
                                VALUES ($1, $2, $3, $4, $5, $6::vector)
                                ON CONFLICT (doc_id, chunk_index) DO UPDATE
                                SET content = $3, start_offset = $4,
                                    end_offset = $5, embedding = $6::vector
                                """,
                                doc_id,
                                chunk_idx,
                                content,
                                start_offset,
                                end_offset,
                                _format_vector(vector),
                            )
                            embedded += 1
                        except Exception as e:
                            logger.warning(
                                "DB insert failed for chunk %d: %s", chunk_idx, e
                            )
                            failed += 1
        finally:
            await conn.close()

        return {
            "embedded": embedded,
            "failed": failed,
            "doc_title": doc_title,
            "doc_id": doc_id,
            "batch_count": batch_count,
        }

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, _run()).result()
        else:
            result = loop.run_until_complete(_run())
    except RuntimeError:
        result = asyncio.run(_run())

    return result


async def _ensure_document(
    conn, title: str, content: str, category: str, source_file: str | None
) -> int:
    existing = await conn.fetchrow(
        "SELECT id FROM documents WHERE title = $1",
        title,
    )
    if existing:
        return existing["id"]

    row = await conn.fetchrow(
        """
        INSERT INTO documents (title, content, category, source_file, metadata)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        title,
        content,
        category,
        source_file,
        json.dumps({"imported_by": "lingflow-knowledge-pipeline"}),
    )
    return row["id"]


def _format_vector(vector: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vector) + "]"


def _dry_run(
    chunks: list, doc_title: str, batch_size: int
) -> dict[str, Any]:
    total = len(chunks)
    total_batches = (total + batch_size - 1) // batch_size
    return {
        "dry_run": True,
        "doc_title": doc_title,
        "total_chunks": total,
        "batch_count": total_batches,
        "batch_size": batch_size,
        "sample_chunk": (
            chunks[0] if chunks else None
        ),
    }


def execute_skill(params: dict[str, Any]) -> dict[str, Any]:
    return embed_chunks(params)
