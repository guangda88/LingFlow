#!/usr/bin/env python3
"""批量教材导入管道

从 zhineng-knowledge-system/data/textbooks/txt格式/ 导入剩余 ~161 本辅助教材。
流程: GB2312解码 → 分块(300字,50重叠) → 嵌入(BGE-M3) → 写入PostgreSQL

不修改灵知的项目代码，只调用其API和数据库。
"""

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# --- Configuration ---

import os

TEXTBOOK_DIR = Path("/home/ai/lingzhi/data/textbooks/txt格式")
SQLITE_DB = Path("/home/ai/lingzhi/data/textbooks.db")
CHECKPOINT_FILE = Path("/home/ai/lingflow/scripts/import_checkpoint.json")
LOG_FILE = Path("/home/ai/lingflow/scripts/import.log")

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5436/zhineng_kb")
EMBEDDING_URL = "http://localhost:8001/embed"

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
MIN_CHUNK_SIZE = 20
EMBEDDING_BATCH_SIZE = 8
EMBEDDING_DELAY = 0.1
EMBEDDING_TIMEOUT = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("batch_import")


@dataclass
class Chunk:
    content: str
    chunk_index: int
    char_count: int
    start_offset: int
    end_offset: int


@dataclass
class FileResult:
    filename: str
    status: str  # "success", "skipped", "error"
    chunks_total: int = 0
    chunks_embedded: int = 0
    error: str = ""
    duration: float = 0.0


@dataclass
class ImportCheckpoint:
    completed_files: Dict[str, str] = field(default_factory=dict)  # filename -> status
    total_chunks: int = 0
    total_embedded: int = 0
    last_file: str = ""
    started_at: str = ""
    updated_at: str = ""


# --- Core Functions ---


def load_checkpoint() -> ImportCheckpoint:
    if CHECKPOINT_FILE.exists():
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        return ImportCheckpoint(**data)
    return ImportCheckpoint(started_at=time.strftime("%Y-%m-%dT%H:%M:%S"))


def save_checkpoint(cp: ImportCheckpoint):
    cp.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
    CHECKPOINT_FILE.write_text(json.dumps(asdict(cp), ensure_ascii=False, indent=2), encoding="utf-8")


def get_already_imported() -> set:
    already = set()
    if SQLITE_DB.exists():
        conn = sqlite3.connect(str(SQLITE_DB))
        cur = conn.cursor()
        cur.execute("SELECT title FROM textbooks")
        for (title,) in cur.fetchall():
            already.add(title)
        conn.close()
    return already


def discover_files() -> List[Path]:
    txt_files = sorted(TEXTBOOK_DIR.glob("*.txt"))
    return txt_files


def read_gb2312(filepath: Path) -> Optional[str]:
    encodings = ["gb2312", "gbk", "gb18030", "utf-8", "latin-1"]
    for enc in encodings:
        try:
            text = filepath.read_text(encoding=enc)
            return text.replace("\x00", "")
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Chunk]:
    if not text or len(text.strip()) < MIN_CHUNK_SIZE:
        return []

    clean = text.replace("\x00", "")
    clean = re.sub(r"\r\n", "\n", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)

    chunks = []
    start = 0
    idx = 0

    paragraphs = re.split(r"\n\n+", clean)
    current_block = ""

    for para in paragraphs:
        if len(current_block) + len(para) + 2 <= chunk_size:
            if current_block:
                current_block += "\n\n" + para
            else:
                current_block = para
        else:
            if current_block and len(current_block.strip()) >= MIN_CHUNK_SIZE:
                chunks.append(
                    Chunk(
                        content=current_block.strip(),
                        chunk_index=idx,
                        char_count=len(current_block.strip()),
                        start_offset=start,
                        end_offset=start + len(current_block),
                    )
                )
                idx += 1
                start += len(current_block)

            if len(para) > chunk_size:
                pstart = 0
                while pstart < len(para):
                    pend = min(pstart + chunk_size, len(para))
                    piece = para[pstart:pend].strip()
                    if len(piece) >= MIN_CHUNK_SIZE:
                        chunks.append(
                            Chunk(
                                content=piece,
                                chunk_index=idx,
                                char_count=len(piece),
                                start_offset=start + pstart,
                                end_offset=start + pend,
                            )
                        )
                        idx += 1
                    pstart = pend - overlap if pend < len(para) else pend
                current_block = ""
            else:
                current_block = para

    if current_block and len(current_block.strip()) >= MIN_CHUNK_SIZE:
        chunks.append(
            Chunk(
                content=current_block.strip(),
                chunk_index=idx,
                char_count=len(current_block.strip()),
                start_offset=start,
                end_offset=start + len(current_block),
            )
        )

    return chunks


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


async def generate_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]:
    embeddings = []
    for text in texts:
        emb = await asyncio.get_event_loop().run_in_executor(None, generate_embedding, text)
        embeddings.append(emb)
        await asyncio.sleep(EMBEDDING_DELAY)
    return embeddings


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


async def import_file_to_postgres(
    pool,
    filename: str,
    title: str,
    chunks: List[Chunk],
    embeddings: List[Optional[List[float]]],
    file_category: str = "辅助教材",
) -> int:
    textbook_id = hashlib.md5(title.encode("utf-8")).hexdigest()[:8]
    root_node_id = f"{textbook_id}_root"

    async with pool.acquire() as conn:
        max_id = await conn.fetchval("SELECT MAX(id) FROM textbook_blocks_v2")
        if max_id is not None:
            await conn.execute("SELECT setval('textbook_blocks_v2_id_seq', $1)", max_id + 1)

        await conn.execute(
            """INSERT INTO textbook_metadata (id, title, category, version, description)
            VALUES ($1, $2, $3, 'txt', $4)
            ON CONFLICT (id) DO UPDATE SET title=$2, updated_at=NOW()""",
            textbook_id,
            title,
            file_category,
            f"批量导入自 {filename}",
        )

        await conn.execute(
            """INSERT INTO textbook_nodes (id, name, path, level, textbook_id, content, children_count, metadata)
            VALUES ($1, $2, $3, 1, $4, '', $5, $6::jsonb)
            ON CONFLICT (id) DO UPDATE SET name=$2, updated_at=NOW()""",
            root_node_id,
            title,
            title,
            textbook_id,
            len(chunks),
            json.dumps({"source_file": filename, "type": "batch_import_root"}, ensure_ascii=False),
        )

        for chunk, emb in zip(chunks, embeddings):
            node_id = f"{textbook_id}_{chunk.chunk_index:05d}"
            section_title = chunk.content[:30].replace("\n", " ")
            meta = json.dumps(
                {
                    "source_file": filename,
                    "chunk_index": chunk.chunk_index,
                    "char_count": chunk.char_count,
                    "content_hash": content_hash(chunk.content),
                },
                ensure_ascii=False,
            )

            await conn.execute(
                """INSERT INTO textbook_nodes (id, name, path, level, parent_id, textbook_id, content, children_count, metadata)
                VALUES ($1, $2, $3, 2, $4, $5, $6, 0, $7::jsonb)
                ON CONFLICT (id) DO UPDATE SET content=$6, updated_at=NOW()""",
                node_id,
                section_title,
                f"{title} > {section_title}",
                root_node_id,
                textbook_id,
                chunk.content,
                json.dumps({"source_file": filename, "chunk_index": chunk.chunk_index}, ensure_ascii=False),
            )

            if emb is not None:
                await conn.execute(
                    """INSERT INTO textbook_blocks_v2 (node_id, content, block_order, embedding, metadata)
                    VALUES ($1, $2, $3, $4::vector, $5::jsonb)""",
                    node_id,
                    chunk.content,
                    chunk.chunk_index,
                    str(emb),
                    meta,
                )
            else:
                await conn.execute(
                    """INSERT INTO textbook_blocks_v2 (node_id, content, block_order, metadata)
                    VALUES ($1, $2, $3, $4::jsonb)""",
                    node_id,
                    chunk.content,
                    chunk.chunk_index,
                    meta,
                )

        # Also write to documents table (the table lingzhi actually searches)
        max_doc_id = await conn.fetchval("SELECT MAX(id) FROM documents")
        if max_doc_id is not None:
            await conn.execute("SELECT setval('documents_id_seq', $1)", max_doc_id + 1)

        for chunk, emb in zip(chunks, embeddings):
            doc_title = f"{title} - {chunk.chunk_index}"
            await conn.execute(
                """INSERT INTO documents (title, content, category, embedding)
                VALUES ($1, $2, $3, $4::vector)""",
                doc_title,
                chunk.content,
                '气功',
                str(emb) if emb else None,
            )

        return len(chunks)


async def process_file(pool, filepath: Path, cp: ImportCheckpoint) -> FileResult:
    start = time.time()
    filename = filepath.name
    title = filepath.stem

    if filename in cp.completed_files:
        return FileResult(filename=filename, status="skipped")

    text = read_gb2312(filepath)
    if text is None:
        return FileResult(filename=filename, status="error", error="无法解码文件", duration=time.time() - start)

    chunks = chunk_text(text)
    if not chunks:
        return FileResult(filename=filename, status="skipped", error="文件内容为空或过短", duration=time.time() - start)

    log.info(f"[{filename}] 分块完成: {len(chunks)} 块, 开始生成嵌入...")

    chunk_texts = [c.content for c in chunks]
    batch_size = EMBEDDING_BATCH_SIZE
    all_embeddings = []

    for i in range(0, len(chunk_texts), batch_size):
        batch = chunk_texts[i : i + batch_size]
        embs = await generate_embeddings_batch(batch)
        all_embeddings.extend(embs)
        done = min(i + batch_size, len(chunk_texts))
        log.info(f"  嵌入进度: {done}/{len(chunk_texts)}")

    embedded_count = sum(1 for e in all_embeddings if e is not None)

    await import_file_to_postgres(pool, filename, title, chunks, all_embeddings)

    duration = time.time() - start
    cp.completed_files[filename] = "success"
    cp.total_chunks += len(chunks)
    cp.total_embedded += embedded_count
    cp.last_file = filename
    save_checkpoint(cp)

    return FileResult(
        filename=filename,
        status="success",
        chunks_total=len(chunks),
        chunks_embedded=embedded_count,
        duration=duration,
    )


async def run_batch_import(limit: int = 0, dry_run: bool = False, category: str = ""):
    log.info("=" * 60)
    log.info("批量教材导入启动")
    log.info(f"源目录: {TEXTBOOK_DIR}")
    log.info(f"块大小: {CHUNK_SIZE}, 重叠: {CHUNK_OVERLAP}")
    log.info(f"嵌入服务: {EMBEDDING_URL}")

    cp = load_checkpoint()
    files = discover_files()
    log.info(f"发现 {len(files)} 个txt文件, 已完成 {len(cp.completed_files)} 个")

    already = get_already_imported()
    pending = []
    for f in files:
        if f.name in cp.completed_files:
            continue
        if f.stem in already and not category:
            continue
        pending.append(f)

    if category:
        pending = [f for f in pending if category.lower() in f.name.lower()]

    if limit > 0:
        pending = pending[:limit]

    log.info(f"待处理: {len(pending)} 个文件")
    if not pending:
        log.info("没有待处理文件")
        return

    if dry_run:
        for f in pending[:20]:
            text = read_gb2312(f)
            chunks = chunk_text(text) if text else []
            log.info(f"  {f.name}: {len(chunks)} 块" + (" (无法解码)" if text is None else ""))
        if len(pending) > 20:
            log.info(f"  ... 还有 {len(pending) - 20} 个文件")
        return

    import asyncpg

    pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=3, command_timeout=120)

    results = []
    try:
        for i, filepath in enumerate(pending):
            log.info(f"[{i+1}/{len(pending)}] 处理: {filepath.name}")
            result = await process_file(pool, filepath, cp)
            results.append(result)

            if result.status == "success":
                log.info(f"  完成: {result.chunks_embedded}/{result.chunks_total} 嵌入, {result.duration:.1f}s")
            elif result.status == "error":
                log.error(f"  失败: {result.error}")
            else:
                log.info(f"  跳过: {result.error}")
    finally:
        await pool.close()

    success = sum(1 for r in results if r.status == "success")
    skipped = sum(1 for r in results if r.status == "skipped")
    errors = sum(1 for r in results if r.status == "error")
    total_chunks = sum(r.chunks_total for r in results)
    total_embedded = sum(r.chunks_embedded for r in results)

    log.info("=" * 60)
    log.info(f"导入完成: {success} 成功, {skipped} 跳过, {errors} 失败")
    log.info(f"总块数: {total_chunks}, 总嵌入: {total_embedded}")
    log.info(f"累计: {cp.total_chunks} 块, {cp.total_embedded} 嵌入")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="批量教材导入管道")
    parser.add_argument("--limit", type=int, default=0, help="限制处理文件数")
    parser.add_argument("--dry-run", action="store_true", help="只扫描不导入")
    parser.add_argument("--category", type=str, default="", help="按文件名过滤")
    parser.add_argument("--reset", action="store_true", help="重置检查点")
    args = parser.parse_args()

    if args.reset:
        CHECKPOINT_FILE.write_text("{}", encoding="utf-8")
        print("检查点已重置")

    asyncio.run(run_batch_import(limit=args.limit, dry_run=args.dry_run, category=args.category))


if __name__ == "__main__":
    main()
