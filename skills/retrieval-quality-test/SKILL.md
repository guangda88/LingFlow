# retrieval-quality-test

检索质量测试技能 — 对灵知搜索API运行评估查询，计算 MRR@K、Recall@K、Precision@K、F1@K 指标。

## 参数

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| test_set_path | 是 | — | 测试集 JSON 文件路径 |
| top_k | 否 | 10 | 检索返回的最大结果数 |
| search_api_url | 否 | http://127.0.0.1:8765/api/v1/search | 灵知搜索 API 地址 |
| dry_run | 否 | false | 仅验证测试集格式，不实际查询 |
| baseline | 否 | {} | 基线指标 dict，用于对比（如 {"MRR@10": 0.876}） |

## 测试集格式

```json
{
  "queries": [
    {
      "query": "用户查询文本",
      "relevant_ids": ["doc_1", "doc_5"],
      "domain": "气功"
    }
  ]
}
```

或直接为数组：

```json
[
  {
    "query": "用户查询文本",
    "relevant_ids": ["doc_1", "doc_5"],
    "domain": "气功"
  }
]
```

## 输出

```json
{
  "success": true,
  "status": "complete",
  "test_set_size": 450,
  "top_k": 10,
  "metrics": {
    "num_queries": 450,
    "MRR@1": 0.72,
    "MRR@5": 0.85,
    "MRR@10": 0.88,
    "Recall@5": 0.91,
    "Recall@10": 0.95,
    "Precision@5": 0.68,
    "Precision@10": 0.52,
    "F1@5": 0.74,
    "F1@10": 0.67,
    "by_domain": {
      "气功": {"MRR@10": 0.90, "Recall@5": 0.93},
      "中医": {"MRR@10": 0.85, "Recall@5": 0.88}
    }
  },
  "comparisons": {
    "MRR@10": {"baseline": 0.876, "current": 0.88, "diff": 0.004, "improved": true}
  },
  "elapsed_seconds": 12.3
}
```

## 使用示例

```python
from lingflow import LingFlow

lf = LingFlow()

# 验证测试集格式
lf.run_skill("retrieval-quality-test", {
    "test_set_path": "/data/test_450qa.json",
    "dry_run": True
})

# 运行完整评估
lf.run_skill("retrieval-quality-test", {
    "test_set_path": "/data/test_450qa.json",
    "top_k": 10,
    "baseline": {"MRR@10": 0.876, "Recall@5": 0.910, "F1@5": 0.786}
})
```
