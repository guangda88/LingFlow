"""Content Production Pipeline — 从灵知检索内容 → 组织文章元数据 → 交付发布

流程:
1. 按主题查询灵知搜索API获取相关文档片段
2. 按相关性分组，合并为文章结构
3. 生成结构化文章元数据(title, tags, summary, content_body)
4. 输出供灵扬消费的文章列表
"""

import json
import logging
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Any

log = logging.getLogger("content-production")

DEFAULT_SEARCH_API = "http://127.0.0.1:8001/api/v1/search/hybrid"

PLATFORM_TAG_MAP = {
    "wechat": "微信公众号",
    "zhihu": "知乎",
    "weibo": "微博",
    "github": "GitHub",
}


def _search_knowledge(
    query: str,
    top_k: int,
    api_url: str,
    use_query_expansion: bool = True,
    domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    payload = {
        "query": query,
        "top_k": top_k,
        "use_vector": True,
        "use_bm25": True,
        "use_query_expansion": use_query_expansion,
    }
    if domains:
        payload["domains"] = domains

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("results", [])
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as e:
        log.warning("搜索API请求失败: %s", e)
        return []


def _extract_title(query: str, chunks: list[dict[str, Any]]) -> str:
    if chunks:
        first_title = chunks[0].get("doc_title") or chunks[0].get("title")
        if first_title:
            return str(first_title)
    return query


def _extract_tags(chunks: list[dict[str, Any]], domains: list[str] | None) -> list[str]:
    tags = set()
    if domains:
        tags.update(domains)
    for chunk in chunks[:5]:
        for key in ("tags", "keywords", "categories"):
            val = chunk.get(key)
            if isinstance(val, list):
                tags.update(str(v) for v in val)
            elif isinstance(val, str):
                tags.add(val)
        domain = chunk.get("domain")
        if domain:
            tags.add(domain)
    return sorted(tags)[:8]


def _build_summary(chunks: list[dict[str, Any]]) -> str:
    parts = []
    for chunk in chunks[:3]:
        text = chunk.get("content") or chunk.get("text") or chunk.get("snippet", "")
        if text:
            clean = text.strip()[:200]
            if clean:
                parts.append(clean)
    combined = "。".join(parts)
    if len(combined) > 300:
        combined = combined[:297] + "..."
    return combined or "暂无摘要"


def _build_content_body(
    query: str,
    chunks: list[dict[str, Any]],
    target_platform: str,
) -> str:
    lines = [f"# {query}", ""]

    if chunks:
        source_title = chunks[0].get("doc_title") or chunks[0].get("title", "")
        if source_title:
            lines.append(f"## 来源：{source_title}")
            lines.append("")

    for i, chunk in enumerate(chunks, 1):
        content = chunk.get("content") or chunk.get("text") or ""
        if not content:
            continue
        section_title = chunk.get("section_title") or chunk.get("title", f"第{i}节")
        lines.append(f"### {section_title}")
        lines.append("")
        lines.append(content.strip())
        lines.append("")

    if target_platform == "wechat":
        lines.append("---")
        lines.append("*本文由灵通内容生产流水线自动生成*")

    return "\n".join(lines)


def _organize_articles(
    query: str,
    results: list[dict[str, Any]],
    target_platform: str,
    max_articles: int,
    domains: list[str] | None,
) -> list[dict[str, Any]]:
    if not results:
        return []

    grouped: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        group_key = r.get("doc_title") or r.get("doc_id", "default")
        grouped.setdefault(str(group_key), []).append(r)

    articles = []
    for group_chunks in list(grouped.values())[:max_articles]:
        title = _extract_title(query, group_chunks)
        tags = _extract_tags(group_chunks, domains)
        summary = _build_summary(group_chunks)
        content_body = _build_content_body(query, group_chunks, target_platform)

        source_doc_ids = []
        for c in group_chunks:
            doc_id = c.get("doc_id")
            if doc_id is not None and doc_id not in source_doc_ids:
                source_doc_ids.append(doc_id)

        word_count = len(content_body)
        articles.append({
            "title": title,
            "tags": tags,
            "summary": summary,
            "target_platform": target_platform,
            "content_body": content_body,
            "source_doc_ids": source_doc_ids,
            "word_count": word_count,
        })

    return articles


def execute_skill(params: dict[str, Any]) -> dict[str, Any]:
    start_time = time.time()

    source_query = params.get("source_query")
    if not source_query:
        return {"success": False, "error": "请指定 source_query 参数"}

    target_platform = params.get("target_platform", "wechat")
    max_articles = params.get("max_articles", 3)
    top_k = params.get("top_k", 20)
    search_api_url = params.get("search_api_url", DEFAULT_SEARCH_API)
    use_query_expansion = params.get("use_query_expansion", True)
    domains = params.get("domains") or None

    log.info("检索主题: %s, 平台: %s, max_articles: %d", source_query, target_platform, max_articles)

    results = _search_knowledge(
        query=source_query,
        top_k=top_k,
        api_url=search_api_url,
        use_query_expansion=use_query_expansion,
        domains=domains,
    )

    if not results:
        return {
            "success": False,
            "error": f"未找到与 '{source_query}' 相关的内容",
            "articles": [],
            "total_articles": 0,
            "elapsed_seconds": round(time.time() - start_time, 2),
        }

    articles = _organize_articles(
        query=source_query,
        results=results,
        target_platform=target_platform,
        max_articles=max_articles,
        domains=domains,
    )

    output_path = params.get("output_path")
    result: dict[str, Any] = {
        "success": True,
        "articles": articles,
        "total_articles": len(articles),
        "source_chunks_used": len(results),
        "elapsed_seconds": round(time.time() - start_time, 2),
    }

    if output_path:
        from pathlib import Path
        out = Path(output_path).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        result["output_file"] = str(out)

    return result
