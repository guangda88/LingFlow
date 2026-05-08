# RAG Quality Closed-Loop (RAG质量闭环)

自动评估检索质量 → 识别弱域 → 参数调优 → 验证改善的闭环技能。

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| test_set_path | string | (必填) | 测试集文件路径 (JSON/JSONL) |
| top_k | int | 10 | 检索返回数量 |
| use_vector | bool | true | 启用向量检索 |
| use_bm25 | bool | true | 启用BM25检索 |
| use_query_expansion | bool | true | 启用查询扩展 |
| search_api_url | string | http://127.0.0.1:8000/api/v1/search/hybrid | 搜索API地址 |
| dry_run | bool | false | 仅验证测试集不执行查询 |
| auto_tune | bool | false | 自动调优并重跑验证 |
| thresholds | dict | {match_rate_min: 0.30, mrr_min: 0.15} | 弱域判定阈值 |
| output_path | string | (可选) | 结果输出文件路径 |

## 输出结构

```json
{
  "success": true,
  "phase": "complete",
  "test_set_size": 852,
  "search_params": {"top_k": 10, "use_vector": true, "use_bm25": true, "use_query_expansion": true},
  "domains": ["中医", "古籍", "教材", "气功", "儒家"],
  "baseline": {
    "params": {...},
    "metrics": {"MRR@10": 0.44, "Recall@10": 0.53, ...},
    "domain_breakdown": {"古籍": {"match_rate": 0.57, "MRR@10": 0.49}, ...}
  },
  "weak_domains": [{"domain": "中医", "match_rate": 0.07, "issues": [...]}],
  "suggestions": [{"domain": "中医", "adjustments": {...}, "reasons": [...]}],
  "tuned": {
    "params": {...},
    "metrics": {...},
    "comparison": {"MRR@10": {"before": 0.44, "after": 0.46, "diff": 0.02, "improved": true}},
    "domain_comparison": {"中医": {"before_match_rate": 0.07, "after_match_rate": 0.10, "diff": 0.03}}
  },
  "elapsed_seconds": 120.5
}
```

## 用法示例

```bash
# 基线评估 + 弱域识别
python -c "
from skills.rag_quality_loop.implementation import execute_skill
result = execute_skill({
    'test_set_path': '/home/ai/zhineng-knowledge-system/data/training/qa_benchmark/test_qa.jsonl',
    'top_k': 10,
    'use_vector': True,
    'use_bm25': True,
})
print(f'弱域数: {result[\"weak_domain_count\"]}')
"

# 自动调优闭环
python -c "
from skills.rag_quality_loop.implementation import execute_skill
result = execute_skill({
    'test_set_path': '...test_qa.jsonl',
    'auto_tune': True,
    'output_path': 'skills/rag-quality-loop/results.json',
})
"
```

## 依赖

- `skills.retrieval_quality_test.implementation` — 复用测试集加载、查询执行、指标计算
- 灵知搜索API (`/api/v1/search/hybrid`)
