"""RAG质量闭环技能 — 评估检索质量 → 识别弱域 → 参数调优 → 验证改善

闭环流程:
1. 加载测试集并运行基线评估
2. 按领域分析指标，识别低于阈值的弱域
3. 为弱域生成参数调优建议
4. 可选用调优参数重跑验证
5. 输出 before/after 对比报告
"""

import importlib.util
import json
import logging
import time
from pathlib import Path
from typing import Any

def _import_helper(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_RQT = _import_helper(
    "retrieval_quality_test",
    str(Path(__file__).resolve().parent.parent / "retrieval-quality-test" / "implementation.py"),
)
_compute_metrics = _RQT._compute_metrics
_content_match = _RQT._content_match
_has_content_match = _RQT._has_content_match
_load_test_set = _RQT._load_test_set
_run_queries = _RQT._run_queries
params_k_values = _RQT.params_k_values

log = logging.getLogger("rag-quality-loop")

DEFAULT_SEARCH_API = "http://127.0.0.1:8000/api/v1/search/hybrid"

PARAM_GRID = {
    "top_k": [10, 15, 20],
    "use_query_expansion": [True],
    "use_vector": [True],
    "use_bm25": [True],
}

DOMAIN_THRESHOLDS = {
    "match_rate_min": 0.30,
    "mrr_min": 0.15,
}


def _run_evaluation(
    queries: list[dict[str, Any]],
    params: dict[str, Any],
    search_api_url: str,
    checkpoint_path: str | None = None,
    checkpoint_interval: int = 50,
) -> dict[str, Any]:
    top_k = params.get("top_k", 10)
    query_results = _run_queries(
        queries,
        top_k,
        search_api_url,
        use_vector=params.get("use_vector", True),
        use_bm25=params.get("use_bm25", True),
        use_query_expansion=params.get("use_query_expansion", True),
        checkpoint_path=checkpoint_path,
        checkpoint_interval=checkpoint_interval,
    )
    metrics = _compute_metrics(query_results, top_k)
    return {
        "query_results": query_results,
        "metrics": metrics,
    }


def _compute_match_rate_by_domain(
    query_results: list[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for r in query_results:
        domain = r.get("domain", "unknown")
        by_domain.setdefault(domain, []).append(r)

    domain_stats = {}
    for domain, results in sorted(by_domain.items()):
        total = len(results)
        matched = 0
        for r in results:
            if _has_content_match(r):
                found, _ = _content_match(r["answer"], r.get("retrieved_contents", []))
                if found:
                    matched += 1
            else:
                if any(
                    doc_id in r["relevant_ids"]
                    for doc_id in r.get("retrieved_ids", [])
                ):
                    matched += 1
        rate = matched / total if total > 0 else 0.0
        domain_stats[domain] = {
            "total": total,
            "matched": matched,
            "match_rate": round(rate, 4),
        }
    return domain_stats


def _identify_weak_domains(
    domain_stats: dict[str, dict[str, float]],
    thresholds: dict[str, float],
) -> list[dict[str, Any]]:
    weak = []
    match_min = thresholds.get("match_rate_min", 0.30)
    mrr_min = thresholds.get("mrr_min", 0.15)

    for domain, stats in domain_stats.items():
        issues = []
        if stats["match_rate"] < match_min:
            issues.append(f"match_rate={stats['match_rate']:.2%} < {match_min:.0%}")
        mrr_key = f"MRR@{10}"
        if mrr_key in stats and stats[mrr_key] < mrr_min:
            issues.append(f"{mrr_key}={stats[mrr_key]:.4f} < {mrr_min}")
        if issues:
            weak.append({
                "domain": domain,
                "match_rate": stats["match_rate"],
                "total_queries": stats["total"],
                "issues": issues,
            })
    return weak


def _suggest_adjustments(
    weak_domains: list[dict[str, Any]],
    current_params: dict[str, Any],
) -> list[dict[str, Any]]:
    suggestions = []
    current_top_k = current_params.get("top_k", 10)

    for wd in weak_domains:
        adjustments: dict[str, Any] = {}
        reasons = []

        if current_top_k < 20:
            adjustments["top_k"] = min(current_top_k + 5, 20)
            reasons.append(f"增加top_k {current_top_k}→{adjustments['top_k']}以提升recall")

        if not current_params.get("use_query_expansion", False):
            adjustments["use_query_expansion"] = True
            reasons.append("启用query expansion扩展查询词")

        if not current_params.get("use_vector", True):
            adjustments["use_vector"] = True
            reasons.append("启用向量检索增加语义匹配")

        if not adjustments:
            reasons.append("当前参数已是最优配置，瓶颈可能在数据侧（嵌入缺失/索引不全）")

        suggestions.append({
            "domain": wd["domain"],
            "current_match_rate": wd["match_rate"],
            "adjustments": adjustments,
            "reasons": reasons,
        })
    return suggestions


def _build_domain_metrics(
    eval_result: dict[str, Any],
) -> dict[str, dict[str, float]]:
    metrics = eval_result.get("metrics", {})
    by_domain = metrics.get("by_domain", {})
    domain_match = _compute_match_rate_by_domain(eval_result.get("query_results", []))

    merged = {}
    for domain in set(list(by_domain.keys()) + list(domain_match.keys())):
        entry: dict[str, float] = {}
        if domain in domain_match:
            entry["match_rate"] = domain_match[domain]["match_rate"]
            entry["total_queries"] = domain_match[domain]["total"]
        if domain in by_domain:
            for k, v in by_domain[domain].items():
                entry[k] = v
        merged[domain] = entry
    return merged


def execute_skill(params: dict[str, Any]) -> dict[str, Any]:
    start_time = time.time()
    search_api_url = params.get("search_api_url", DEFAULT_SEARCH_API)
    dry_run = params.get("dry_run", False)
    top_k = params.get("top_k", 10)
    auto_tune = params.get("auto_tune", False)
    thresholds = params.get("thresholds", DOMAIN_THRESHOLDS)

    search_params = {
        "top_k": top_k,
        "use_vector": params.get("use_vector", True),
        "use_bm25": params.get("use_bm25", True),
        "use_query_expansion": params.get("use_query_expansion", True),
    }

    load_result = _load_test_set(params)
    if "error" in load_result:
        return {"success": False, "error": load_result["error"]}

    queries = load_result["queries"]

    result: dict[str, Any] = {
        "success": True,
        "phase": "dry_run",
        "test_set_size": load_result["total"],
        "search_params": search_params,
        "domains": sorted(set(q["domain"] for q in queries)),
        "elapsed_seconds": 0,
    }

    if dry_run:
        result["status"] = "dry_run"
        result["elapsed_seconds"] = round(time.time() - start_time, 2)
        return result

    # Phase 1: Baseline evaluation
    log.info("Phase 1: 运行基线评估 (%d queries, top_k=%d)", len(queries), top_k)
    baseline_eval = _run_evaluation(
        queries, search_params, search_api_url,
        checkpoint_path=params.get("checkpoint_path"),
        checkpoint_interval=params.get("checkpoint_interval", 50),
    )
    baseline_metrics = baseline_eval["metrics"]
    baseline_domain = _build_domain_metrics(baseline_eval)

    result["baseline"] = {
        "params": dict(search_params),
        "metrics": {
            k: v for k, v in baseline_metrics.items()
            if k != "by_domain"
        },
        "domain_breakdown": baseline_domain,
    }

    # Phase 2: Identify weak domains
    domain_match_stats = _compute_match_rate_by_domain(baseline_eval["query_results"])
    weak_domains = _identify_weak_domains(domain_match_stats, thresholds)
    result["weak_domains"] = weak_domains
    result["weak_domain_count"] = len(weak_domains)

    # Phase 3: Generate suggestions
    suggestions = _suggest_adjustments(weak_domains, search_params)
    result["suggestions"] = suggestions

    # Phase 4: Auto-tune if requested
    if auto_tune and weak_domains:
        log.info("Phase 4: 自动调优验证")

        tuned_params = dict(search_params)
        for suggestion in suggestions:
            for key, val in suggestion["adjustments"].items():
                tuned_params[key] = val

        if tuned_params != search_params:
            log.info("调优参数: %s", tuned_params)
            tuned_checkpoint = params.get("checkpoint_path", "")
            if tuned_checkpoint:
                tuned_checkpoint = tuned_checkpoint.replace(".json", "_tuned.json")
            tuned_eval = _run_evaluation(
                queries, tuned_params, search_api_url,
                checkpoint_path=tuned_checkpoint,
                checkpoint_interval=params.get("checkpoint_interval", 50),
            )
            tuned_metrics = tuned_eval["metrics"]
            tuned_domain = _build_domain_metrics(tuned_eval)

            comparison: dict[str, Any] = {}
            for metric_name in ["MRR@10", "Recall@10", "Precision@10", "F1@10"]:
                if metric_name in baseline_metrics and metric_name in tuned_metrics:
                    b_val = baseline_metrics[metric_name]
                    t_val = tuned_metrics[metric_name]
                    comparison[metric_name] = {
                        "before": b_val,
                        "after": t_val,
                        "diff": round(t_val - b_val, 4),
                        "improved": t_val > b_val,
                    }

            domain_comparison = {}
            for domain in set(list(baseline_domain.keys()) + list(tuned_domain.keys())):
                b_match = baseline_domain.get(domain, {}).get("match_rate", 0)
                t_match = tuned_domain.get(domain, {}).get("match_rate", 0)
                domain_comparison[domain] = {
                    "before_match_rate": b_match,
                    "after_match_rate": t_match,
                    "diff": round(t_match - b_match, 4),
                    "improved": t_match > b_match,
                }

            result["tuned"] = {
                "params": tuned_params,
                "metrics": {
                    k: v for k, v in tuned_metrics.items()
                    if k != "by_domain"
                },
                "domain_breakdown": tuned_domain,
                "comparison": comparison,
                "domain_comparison": domain_comparison,
            }
        else:
            result["tuned"] = {
                "status": "skipped",
                "reason": "无可调参数（当前已是推荐配置，瓶颈在数据侧）",
            }

    result["phase"] = "complete"
    result["status"] = "complete"
    result["elapsed_seconds"] = round(time.time() - start_time, 2)

    output_path = params.get("output_path")
    if output_path:
        out = Path(output_path).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        result["output_file"] = str(out)

    return result
