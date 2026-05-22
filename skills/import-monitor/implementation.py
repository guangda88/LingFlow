"""数据导入进度监控 — 灵知数据库九域导入状态实时查询

职责:
1. 各领域文档数/chunk数/embedding覆盖率统计
2. 弱域识别（低于目标阈值的领域）
3. 数据质量检查（空内容、重复文档、孤立chunk）

数据源: 灵知PostgreSQL (zhineng_kb), 通过灵知venv的psycopg2连接
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_LINGZHI_VENV = "/home/ai/lingzhi/venv/bin/python3"
_DB_URL = os.environ.get("LINGZHI_DB_URL", "")

TARGETS = {
    "中医": 500, "儒家": 1000, "武术": 2000, "道家": 1000,
    "气功": 5000, "心理学": 500, "科学": 1000, "哲学": 500, "佛家": 2000,
}


def execute_skill(params: Dict) -> Dict:
    action = params.get("action", "full_report")

    script = _build_script(action)
    try:
        result = subprocess.run(
            [_LINGZHI_VENV, "-c", script],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr[:500]}
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Query timed out (120s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _build_script(action: str) -> str:
    if action == "full_report":
        return _FULL_REPORT_SCRIPT
    elif action == "weak_domains":
        return _WEAK_DOMAINS_SCRIPT
    elif action == "quality_check":
        return _QUALITY_CHECK_SCRIPT
    return "import json; print(json.dumps({'success': False, 'error': 'unknown action'}))"


_FULL_REPORT_SCRIPT = """
import psycopg2, json
import os
from datetime import datetime

TARGETS = {"中医": 500, "儒家": 1000, "武术": 2000, "道家": 1000, "气功": 5000, "心理学": 500, "科学": 1000, "哲学": 500, "佛家": 2000}

conn = psycopg2.connect(os.environ.get("ZHINENG_KB_DSN", ""))
cur = conn.cursor()

# documents by category (fast)
cur.execute("SELECT category, COUNT(*) FROM documents GROUP BY category ORDER BY count DESC")
domains = []
met = 0
for cat, docs in cur.fetchall():
    t = TARGETS.get(cat, 0)
    is_met = docs >= t if t > 0 else True
    if is_met: met += 1
    domains.append({"category": cat, "doc_count": docs, "target": t, "target_met": is_met, "gap": max(0, t-docs)})

# global chunk stats (no JOIN, fast)
cur.execute("SELECT COUNT(*) FROM doc_chunks")
total_chunks = cur.fetchone()[0]
cur.execute("SELECT COUNT(embedding) FROM doc_chunks WHERE embedding IS NOT NULL")
total_emb = cur.fetchone()[0]

print(json.dumps({"success": True, "action": "full_report", "timestamp": datetime.now().isoformat(), "summary": {"total_docs": sum(d["doc_count"] for d in domains), "total_chunks": total_chunks, "total_embeddings": total_emb, "emb_coverage_pct": round(total_emb/total_chunks*100,1), "domains_total": len(domains), "domains_target_met": met}, "domains": domains}, ensure_ascii=False))
conn.close()
"""

_WEAK_DOMAINS_SCRIPT = """
import psycopg2, json

TARGETS = {"中医": 500, "儒家": 1000, "武术": 2000, "道家": 1000, "气功": 5000, "心理学": 500, "科学": 1000, "哲学": 500, "佛家": 2000}

import os
conn = psycopg2.connect(os.environ.get("ZHINENG_KB_DSN", ""))
cur = conn.cursor()
cur.execute("SELECT category, COUNT(*) FROM documents GROUP BY category")
all_cats = {r[0]: r[1] for r in cur.fetchall()}
weak = [{"category": c, "doc_count": all_cats.get(c, 0), "target": t, "gap": max(0, t - all_cats.get(c, 0))} for c, t in TARGETS.items() if all_cats.get(c, 0) < t]
print(json.dumps({"success": True, "action": "weak_domains", "weak_count": len(weak), "weak_domains": weak, "all_met": len(weak) == 0}, ensure_ascii=False))
conn.close()
"""

_QUALITY_CHECK_SCRIPT = """
import psycopg2, json

import os
conn = psycopg2.connect(os.environ.get("ZHINENG_KB_DSN", ""))
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM documents WHERE content IS NULL OR content = ''")
empty_docs = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM doc_chunks WHERE content IS NULL OR content = ''")
empty_chunks = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM (SELECT content FROM documents GROUP BY content HAVING COUNT(*) > 1) dup")
dup_docs = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM doc_chunks c WHERE c.doc_id NOT IN (SELECT id FROM documents)")
orphan_chunks = cur.fetchone()[0]
issues = []
if empty_docs > 0: issues.append(f"{empty_docs} empty documents")
if empty_chunks > 0: issues.append(f"{empty_chunks} empty chunks")
if dup_docs > 0: issues.append(f"{dup_docs} duplicate content groups")
if orphan_chunks > 0: issues.append(f"{orphan_chunks} orphan chunks")
print(json.dumps({"success": True, "action": "quality_check", "healthy": len(issues)==0, "issues": issues, "checks": {"empty_documents": empty_docs, "empty_chunks": empty_chunks, "duplicate_content_groups": dup_docs, "orphan_chunks": orphan_chunks}}, ensure_ascii=False))
conn.close()
"""
