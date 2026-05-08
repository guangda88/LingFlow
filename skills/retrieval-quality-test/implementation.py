"""检索质量测试技能 — 对灵知搜索API运行评估并计算 MRR/Recall/Precision/F1"""

import json
import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("retrieval-quality-test")


def _load_test_set(params: dict[str, Any]) -> dict[str, Any]:
    source = params.get("test_set_path")
    if not source:
        return {"error": "请指定 test_set_path 参数（JSON/JSONL文件路径）"}

    path = Path(source).expanduser()
    if not path.exists():
        return {"error": f"测试集文件不存在: {source}"}

    if path.suffix == ".jsonl":
        return _load_jsonl(path)

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {"error": f"读取测试集失败: {e}"}

    if isinstance(data, list):
        queries = data
    elif isinstance(data, dict):
        queries = data.get("queries", data.get("test_set", []))
    else:
        return {"error": "测试集格式无效：期望包含 queries 数组的 JSON"}

    validated = []
    for i, q in enumerate(queries):
        if "query" not in q or "relevant_ids" not in q:
            return {"error": f"第 {i + 1} 条缺少 'query' 或 'relevant_ids' 字段"}
        validated.append({
            "query": q["query"],
            "relevant_ids": q["relevant_ids"],
            "domain": q.get("domain", "unknown"),
        })

    return {"queries": validated, "total": len(validated)}


def _load_jsonl(path: Path) -> dict[str, Any]:
    queries = []
    try:
        with open(path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                if "query" not in d:
                    return {"error": f"JSONL第{line_no}行缺少 'query' 字段"}
                rid = d.get("doc_id") or d.get("relevant_ids")
                if rid is None:
                    return {"error": f"JSONL第{line_no}行缺少 'doc_id' 或 'relevant_ids'"}
                relevant = [str(rid)] if not isinstance(rid, list) else [str(x) for x in rid]
                queries.append({
                    "query": d["query"],
                    "relevant_ids": relevant,
                    "domain": d.get("category", d.get("domain", "unknown")),
                    "answer": d.get("answer", ""),
                })
    except (json.JSONDecodeError, OSError) as e:
        return {"error": f"读取JSONL失败（行{line_no if 'line_no' in dir() else '?'}）: {e}"}
    return {"queries": queries, "total": len(queries)}


def _save_checkpoint(checkpoint_path: str | None, results: list[dict[str, Any]], qi: int, total: int) -> None:
    if not checkpoint_path:
        return
    cp = Path(checkpoint_path)
    cp.parent.mkdir(parents=True, exist_ok=True)
    tmp = cp.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"completed": qi + 1, "total": total, "results": results}, f, ensure_ascii=False)
    tmp.replace(cp)
    log.info("checkpoint: %d/%d saved", qi + 1, total)


def _load_checkpoint(checkpoint_path: str | None) -> list[dict[str, Any]]:
    if not checkpoint_path:
        return []
    cp = Path(checkpoint_path)
    if not cp.exists():
        return []
    try:
        with open(cp, encoding="utf-8") as f:
            data = json.load(f)
        results = data.get("results", [])
        log.info("checkpoint: resumed from %d/%d", data.get("completed", 0), data.get("total", 0))
        return results
    except (json.JSONDecodeError, OSError) as e:
        log.warning("checkpoint: load failed, starting fresh: %s", e)
        return []


def _run_queries(
    queries: list[dict[str, Any]],
    top_k: int,
    search_api_url: str,
    use_vector: bool = True,
    use_bm25: bool = True,
    use_query_expansion: bool = True,
    max_retries: int = 1,
    delay: float = 0.1,
    checkpoint_path: str | None = None,
    checkpoint_interval: int = 50,
) -> list[dict[str, Any]]:
    import urllib.request
    import urllib.error

    results = _load_checkpoint(checkpoint_path)
    start_idx = len(results)
    if start_idx > 0:
        log.info("resuming from query %d/%d", start_idx, len(queries))

    for qi in range(start_idx, len(queries)):
        q = queries[qi]
        payload = json.dumps({
            "query": q["query"],
            "top_k": top_k,
            "use_vector": use_vector,
            "use_bm25": use_bm25,
            "use_query_expansion": use_query_expansion,
        }).encode()
        req = urllib.request.Request(
            search_api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        retrieved_ids = []
        retrieved_contents = []
        last_err = None
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    body = json.loads(resp.read().decode())
                hits = body.get("results", [])
                retrieved_ids = [str(h.get("id", h.get("doc_id", ""))) for h in hits]
                retrieved_contents = [
                    {"id": str(h.get("id", h.get("doc_id", ""))), "content": h.get("content", "")}
                    for h in hits
                ]
                last_err = None
                break
            except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
                last_err = e
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
        if last_err is not None:
            log.warning("查询失败[%d/%d] '%s': %s", qi + 1, len(queries), q["query"][:40], last_err)
            retrieved_ids = []
            retrieved_contents = []

        time.sleep(delay)

        results.append({
            "query": q["query"],
            "relevant_ids": q["relevant_ids"],
            "retrieved_ids": retrieved_ids,
            "retrieved_contents": retrieved_contents,
            "domain": q["domain"],
            "answer": q.get("answer", ""),
        })

        if (qi + 1 - start_idx) % checkpoint_interval == 0:
            _save_checkpoint(checkpoint_path, results, qi, len(queries))

    _save_checkpoint(checkpoint_path, results, len(queries) - 1, len(queries))
    return results


def _content_match(answer: str, retrieved_contents: list[dict[str, Any]]) -> tuple[bool, int]:
    if not answer or not answer.strip():
        return False, -1
    probe = answer.strip()
    for rank, item in enumerate(retrieved_contents, start=1):
        content = item.get("content", "")
        if probe in content:
            return True, rank
    return False, -1


def _has_content_match(r: dict[str, Any]) -> bool:
    return bool(r.get("answer", "").strip()) and bool(r.get("retrieved_contents"))


def _compute_mrr(results: list[dict[str, Any]], k: int) -> float:
    rr_sum = 0.0
    for r in results:
        if _has_content_match(r):
            matched, rank = _content_match(r["answer"], r["retrieved_contents"][:k])
            if matched:
                rr_sum += 1.0 / rank
        else:
            for rank, doc_id in enumerate(r["retrieved_ids"][:k], start=1):
                if doc_id in r["relevant_ids"]:
                    rr_sum += 1.0 / rank
                    break
    return rr_sum / len(results) if results else 0.0


def _compute_recall(results: list[dict[str, Any]], k: int) -> float:
    total_recall = 0.0
    for r in results:
        if _has_content_match(r):
            matched, _ = _content_match(r["answer"], r["retrieved_contents"][:k])
            total_recall += 1.0 if matched else 0.0
        else:
            if not r["relevant_ids"]:
                continue
            hits = sum(
                1 for doc_id in r["retrieved_ids"][:k]
                if doc_id in r["relevant_ids"]
            )
            total_recall += hits / len(r["relevant_ids"])
    return total_recall / len(results) if results else 0.0


def _compute_precision(results: list[dict[str, Any]], k: int) -> float:
    total_precision = 0.0
    for r in results:
        if _has_content_match(r):
            matched, _ = _content_match(r["answer"], r["retrieved_contents"][:k])
            if r["retrieved_contents"][:k]:
                total_precision += (1.0 if matched else 0.0) / min(k, len(r["retrieved_contents"]))
        else:
            if not r["retrieved_ids"][:k]:
                continue
            hits = sum(
                1 for doc_id in r["retrieved_ids"][:k]
                if doc_id in r["relevant_ids"]
            )
            total_precision += hits / len(r["retrieved_ids"][:k])
    return total_precision / len(results) if results else 0.0


def _compute_metrics(
    results: list[dict[str, Any]],
    top_k: int,
) -> dict[str, Any]:
    ks = params_k_values(top_k)
    metrics: dict[str, Any] = {"num_queries": len(results)}

    for k in ks:
        mrr = _compute_mrr(results, k)
        recall = _compute_recall(results, k)
        precision = _compute_precision(results, k)
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        metrics[f"MRR@{k}"] = round(mrr, 4)
        metrics[f"Recall@{k}"] = round(recall, 4)
        metrics[f"Precision@{k}"] = round(precision, 4)
        metrics[f"F1@{k}"] = round(f1, 4)

    by_domain: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        by_domain.setdefault(r["domain"], []).append(r)

    domain_metrics = {}
    for domain, domain_results in sorted(by_domain.items()):
        dm: dict[str, float] = {}
        for k in ks:
            dm[f"MRR@{k}"] = round(_compute_mrr(domain_results, k), 4)
            dm[f"Recall@{k}"] = round(_compute_recall(domain_results, k), 4)
        domain_metrics[domain] = dm
    metrics["by_domain"] = domain_metrics

    return metrics


def params_k_values(top_k: int) -> list[int]:
    return [k for k in [1, 3, 5, 10, 20] if k <= top_k]


def execute_skill(params: dict[str, Any]) -> dict[str, Any]:
    start_time = time.time()
    top_k = params.get("top_k", 10)
    dry_run = params.get("dry_run", False)
    search_api_url = params.get(
        "search_api_url", "http://127.0.0.1:8000/api/v1/search/hybrid"
    )

    load_result = _load_test_set(params)
    if "error" in load_result:
        return {"success": False, "error": load_result["error"]}

    queries = load_result["queries"]

    result: dict[str, Any] = {
        "success": True,
        "phase": "dry_run",
        "test_set_size": load_result["total"],
        "top_k": top_k,
        "search_api_url": search_api_url,
        "domains": sorted(set(q["domain"] for q in queries)),
        "elapsed_seconds": 0,
    }

    if dry_run:
        result["status"] = "dry_run"
        result["elapsed_seconds"] = round(time.time() - start_time, 2)
        return result

    query_results = _run_queries(
        queries, top_k, search_api_url,
        use_vector=params.get("use_vector", False),
        use_bm25=params.get("use_bm25", True),
        use_query_expansion=params.get("use_query_expansion", True),
    )
    metrics = _compute_metrics(query_results, top_k)

    result["metrics"] = metrics
    result["phase"] = "complete"
    result["status"] = "complete"
    result["elapsed_seconds"] = round(time.time() - start_time, 2)

    baseline = params.get("baseline", {})
    if baseline:
        comparisons = {}
        for metric_name, baseline_val in baseline.items():
            current_val = metrics.get(metric_name)
            if current_val is not None:
                diff = round(current_val - baseline_val, 4)
                comparisons[metric_name] = {
                    "baseline": baseline_val,
                    "current": current_val,
                    "diff": diff,
                    "improved": diff > 0,
                }
        result["comparisons"] = comparisons

    return result
