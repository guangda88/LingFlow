"""铁律违规记录器

每次违规自动记录，为将来的铁律分类器蒸馏积累训练数据。
"""

import json
import os
from datetime import datetime
from typing import Optional


IRON_LAWS = {
    1: "先验证再断言——没有验证的断言等于撒谎",
    2: "客户需求是根节点——偏离需求的一切努力都是零",
    3: "反事实推理在遗忘之前——不是按时间遗忘，是按拓扑位置遗忘",
    4: "取象比类，而非闭门造车——先理解已有的，再比过来",
    5: "生态智慧，不是单点智能——知道兄弟有什么刀，什么问题找谁",
    6: "没有充分理解就动手是最大的浪费——听完、想透、确认理解了，再动手",
    0: "元铁律：先确认再行动",
}

VIOLATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "violations")


def record_violation(
    law_id: int,
    statement: str,
    context: str,
    correction: str,
    evidence_missing: Optional[str] = None,
    root_cause: Optional[str] = None,
    tags: Optional[list] = None,
) -> str:
    """记录一次铁律违规

    Args:
        law_id: 违反的铁律编号（0-6）
        statement: 违规的断言或输出
        context: 触发场景描述
        correction: 创造者的纠正
        evidence_missing: 缺失的证据（如果有）
        root_cause: 根因分析
        tags: 标签列表

    Returns:
        记录文件路径
    """
    os.makedirs(VIOLATIONS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"violation_{timestamp}_law{law_id}.json"
    filepath = os.path.join(VIOLATIONS_DIR, filename)

    record = {
        "timestamp": datetime.now().isoformat(),
        "law_id": law_id,
        "law_text": IRON_LAWS.get(law_id, "未知"),
        "statement": statement,
        "context": context,
        "evidence_missing": evidence_missing,
        "correction": correction,
        "root_cause": root_cause,
        "tags": tags or [],
        "session_source": "LingFlow",
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return filepath


def list_violations(law_id: Optional[int] = None) -> list:
    """列出所有违规记录"""
    if not os.path.exists(VIOLATIONS_DIR):
        return []

    results = []
    for fname in sorted(os.listdir(VIOLATIONS_DIR)):
        if not fname.endswith(".json"):
            continue
        filepath = os.path.join(VIOLATIONS_DIR, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            record = json.load(f)
        if law_id is None or record.get("law_id") == law_id:
            results.append(record)
    return results


def get_statistics() -> dict:
    """违规统计"""
    violations = list_violations()
    by_law = {}
    for v in violations:
        law_id = v["law_id"]
        by_law[law_id] = by_law.get(law_id, 0) + 1

    return {
        "total": len(violations),
        "by_law": by_law,
        "laws": IRON_LAWS,
    }
