"""knowledge-chunk 技能实现 — 文本分块"""

import re
from pathlib import Path
from typing import Any

_SENTENCE_ENDS = re.compile(r"[。！？；\n]")


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[dict[str, Any]]:
    if len(text) <= chunk_size:
        return [{"content": text, "start": 0, "end": len(text), "index": 0}]

    chunks: list[dict[str, Any]] = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            search_region = text[end:min(end + 50, len(text))]
            m = _SENTENCE_ENDS.search(search_region)
            if m:
                end += m.end()
        else:
            end = len(text)

        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"content": chunk, "start": start, "end": end, "index": idx})
            idx += 1

        next_start = end - overlap
        if chunks and next_start <= chunks[-1]["start"]:
            next_start = end
        start = next_start

    return chunks


def chunk_file(params: dict[str, Any]) -> dict[str, Any]:
    file_path = params.get("file_path")
    if not file_path:
        return {"error": "请指定 file_path 参数"}

    path = Path(file_path).expanduser()
    if not path.exists():
        return {"error": f"文件不存在: {file_path}"}

    chunk_size = params.get("chunk_size", 300)
    overlap = params.get("overlap", 50)
    encoding = params.get("encoding", "utf-8")

    try:
        text = path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")

    if not text.strip():
        return {"error": "文件内容为空", "file": path.name, "total_chunks": 0}

    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    return {
        "chunks": chunks,
        "file": path.name,
        "total_chunks": len(chunks),
        "chunk_size": chunk_size,
        "overlap": overlap,
    }


def execute_skill(params: dict[str, Any]) -> dict[str, Any]:
    return chunk_file(params)
