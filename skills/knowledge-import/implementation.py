"""knowledge-import 技能实现 — 扫描并验证知识库源文件"""

import chardet
from pathlib import Path
from typing import Any


_SUPPORTED_EXTENSIONS = {
    "txt": [".txt"],
    "pdf": [".pdf"],
    "docx": [".docx", ".doc"],
}


def _detect_encoding(file_path: Path) -> str:
    try:
        raw = file_path.read_bytes()[:8192]
        result = chardet.detect(raw)
        return result.get("encoding", "utf-8") or "utf-8"
    except Exception:
        return "utf-8"


def _is_processed(file_name: str, processed_dir: Path | None) -> bool:
    if processed_dir is None or not processed_dir.exists():
        return False
    stem = Path(file_name).stem
    for p in processed_dir.iterdir():
        if p.stem.startswith(stem) or stem.startswith(p.stem):
            return True
    return False


def scan_files(params: dict[str, Any]) -> dict[str, Any]:
    source_dir = params.get("source_dir")
    if not source_dir:
        return {"error": "请指定 source_dir 参数"}

    source_path = Path(source_dir).expanduser()
    if not source_path.exists():
        return {"error": f"源目录不存在: {source_dir}"}

    formats = params.get("formats", ["txt"])
    processed_dir = params.get("processed_dir")
    processed_path = Path(processed_dir).expanduser() if processed_dir else None
    recursive = params.get("recursive", True)

    extensions: set[str] = set()
    for fmt in formats:
        extensions.update(_SUPPORTED_EXTENSIONS.get(fmt, [f".{fmt}"]))

    files: list[dict[str, Any]] = []
    skipped = 0

    glob_method = source_path.rglob if recursive else source_path.glob
    for fp in sorted(glob_method("*")):
        if not fp.is_file():
            continue
        if fp.suffix.lower() not in extensions:
            continue

        file_name = fp.name
        if _is_processed(file_name, processed_path):
            skipped += 1
            continue

        info: dict[str, Any] = {
            "path": str(fp),
            "name": file_name,
            "size": fp.stat().st_size,
            "format": fp.suffix.lstrip(".").lower(),
        }
        if fp.suffix.lower() == ".txt":
            info["encoding"] = _detect_encoding(fp)
        files.append(info)

    return {
        "files": files,
        "total": len(files) + skipped,
        "skipped": skipped,
        "new": len(files),
    }


def execute_skill(params: dict[str, Any]) -> dict[str, Any]:
    return scan_files(params)
