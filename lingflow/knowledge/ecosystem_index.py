"""灵族生态系统文档索引

扫描 /home/ai/ 下所有灵族仓库的文档，建立关键词→文件映射。
解决 2026-04-11 错误复盘中发现的"信息散落 5+ 位置，搜索不到"的问题。

Usage:
    >>> from lingflow.knowledge.ecosystem_index import EcosystemIndex
    >>> idx = EcosystemIndex()
    >>> results = idx.search("GPU 分布式")
    >>> for r in results:
    ...     print(f"{r.repo}: {r.path}")
    lingresearch: /home/ai/lingresearch/docs/FINE_TUNING_PLAN.md
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class IndexedDoc:
    """索引中的文档条目"""
    repo: str
    repo_cn: str
    path: str
    filename: str
    title: str
    keywords: Set[str] = field(default_factory=set)


_REPO_REGISTRY: List[Dict[str, str]] = [
    {"dir": "LingFlow", "cn": "灵通", "en": "LingFlow"},
    {"dir": "LingClaude", "cn": "灵克", "en": "LingClaude"},
    {"dir": "LingYi", "cn": "灵依", "en": "LingYi"},
    {"dir": "LingMessage", "cn": "灵信", "en": "LingMessage"},
    {"dir": "LingYang", "cn": "灵扬", "en": "LingYang"},
    {"dir": "LingMinOpt", "cn": "灵极优", "en": "LingMinOpt"},
    {"dir": "Ling-term-mcp", "cn": "灵犀", "en": "LingTermMCP"},
    {"dir": "zhineng-knowledge-system", "cn": "灵知", "en": "LingZhi"},
    {"dir": "zhineng-bridge", "cn": "智桥", "en": "ZhiBridge"},
    {"dir": "lingresearch", "cn": "灵研", "en": "LingResearch"},
]

_SKIP_DIRS = {
    "node_modules", "__pycache__", ".git", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".mypy_cache",
}

_DOC_EXTENSIONS = {".md", ".txt", ".rst"}


def _extract_title(filepath: Path) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#"):
                    return line.lstrip("#").strip()
                if line:
                    return line[:80]
    except (OSError, PermissionError):
        pass
    return filepath.stem


def _tokenize(text: str) -> Set[str]:
    text = text.lower()
    words = set(re.findall(r"[a-z0-9\u4e00-\u9fff]+", text))
    words.discard("")
    return words


class EcosystemIndex:
    """灵族生态系统文档索引

    扫描所有灵族仓库的 docs/ 目录和根目录 .md 文件，
    建立可搜索的文档索引。
    """

    def __init__(self, base_path: str = "/home/ai") -> None:
        self._base = Path(base_path)
        self._docs: List[IndexedDoc] = []
        self._keyword_index: Dict[str, List[int]] = {}
        self._build()

    def _build(self) -> None:
        for repo_info in _REPO_REGISTRY:
            repo_dir = self._base / repo_info["dir"]
            if not repo_dir.is_dir():
                continue
            docs = self._scan_repo(repo_dir, repo_info)
            for doc in docs:
                idx = len(self._docs)
                self._docs.append(doc)
                for kw in doc.keywords:
                    self._keyword_index.setdefault(kw, []).append(idx)

    def _scan_repo(self, repo_dir: Path, repo_info: Dict[str, str]) -> List[IndexedDoc]:
        results: List[IndexedDoc] = []
        docs_dir = repo_dir / "docs"

        scan_dirs: List[Path] = []
        if docs_dir.is_dir():
            scan_dirs.append(docs_dir)

        for f in repo_dir.iterdir():
            if f.is_file() and f.suffix in _DOC_EXTENSIONS:
                scan_dirs.append(f)

        for scan_target in scan_dirs:
            if scan_target.is_file():
                self._index_file(scan_target, repo_dir, repo_info, results)
            elif scan_target.is_dir():
                for f in scan_target.rglob("*"):
                    if f.is_file() and f.suffix in _DOC_EXTENSIONS:
                        if not any(skip in f.parts for skip in _SKIP_DIRS):
                            self._index_file(f, repo_dir, repo_info, results)

        return results

    def _index_file(
        self, filepath: Path, repo_dir: Path, repo_info: Dict[str, str], results: List[IndexedDoc]
    ) -> None:
        title = _extract_title(filepath)
        filename_stem = filepath.stem.lower()
        title_words = _tokenize(title)
        path_words = _tokenize(filepath.stem)
        path_parts = _tokenize(" ".join(filepath.relative_to(repo_dir).parent.parts))
        content_words = self._extract_content_keywords(filepath)
        all_keywords = title_words | path_words | path_parts | {filename_stem} | content_words

        results.append(IndexedDoc(
            repo=repo_info["dir"],
            repo_cn=repo_info["cn"],
            path=str(filepath),
            filename=filepath.name,
            title=title,
            keywords=all_keywords,
        ))

    @staticmethod
    def _extract_content_keywords(filepath: Path, max_lines: int = 50) -> Set[str]:
        keywords: Set[str] = set()
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    keywords.update(_tokenize(line))
        except (OSError, PermissionError):
            pass
        return keywords

    def search(self, query: str, max_results: int = 20) -> List[IndexedDoc]:
        query_words = _tokenize(query)
        if not query_words:
            return []

        scores: Dict[int, int] = {}
        for word in query_words:
            for idx in self._keyword_index.get(word, []):
                scores[idx] = scores.get(idx, 0) + 1

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [self._docs[idx] for idx, _ in ranked[:max_results]]

    def search_by_repo(self, repo_name: str, max_results: int = 50) -> List[IndexedDoc]:
        return [
            doc for doc in self._docs
            if doc.repo.lower() == repo_name.lower()
        ][:max_results]

    def get_all_repos(self) -> List[Dict[str, str]]:
        found = {doc.repo for doc in self._docs}
        return [r for r in _REPO_REGISTRY if r["dir"] in found]

    def get_stats(self) -> Dict[str, int]:
        repo_counts: Dict[str, int] = {}
        for doc in self._docs:
            repo_counts[doc.repo_cn] = repo_counts.get(doc.repo_cn, 0) + 1
        return repo_counts

    def summary(self) -> str:
        stats = self.get_stats()
        lines = ["灵族文档索引:"]
        for repo_cn, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {repo_cn}: {count} 文档")
        lines.append(f"  总计: {len(self._docs)} 文档, {len(self._keyword_index)} 关键词")
        return "\n".join(lines)
