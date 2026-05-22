"""发布编排验证契约 — 定义内容就绪、质量门控、漂移系数的结构化验收标准

基于灵族六大议题共识：
- 验证契约 = 派发任务时定义"什么叫完成"
- 漂移系数 = 验证失败次数 / 总任务数，阈值≤5%
- 系统容错 > 个体完美 — 用契约替代自律
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_CONTRACT_DIR = Path.home() / ".lingflow" / "verification_contracts"
_DRIFT_LOG = Path.home() / ".lingflow" / "drift_coefficient.json"


@dataclass
class VerificationCheck:
    name: str
    check_type: str  # "must_pass" | "must_fail_if" | "warning"
    description: str
    validator: Optional[str] = None  # validator function name
    severity: str = "high"  # "high" | "medium" | "low"


@dataclass
class VerificationContract:
    task_id: str
    task_name: str
    content_type: str  # "article" | "podcast" | "video"
    platforms: List[str] = field(default_factory=list)
    must_pass: List[VerificationCheck] = field(default_factory=list)
    must_fail_if: List[VerificationCheck] = field(default_factory=list)
    warnings: List[VerificationCheck] = field(default_factory=list)
    verifier: str = "lingflow"  # who verifies
    created_at: str = ""
    verified_at: Optional[str] = None
    verification_result: Optional[Dict] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


# ── 预定义契约模板 ──

ARTICLE_CONTRACT = VerificationContract(
    task_id="template_article",
    task_name="文章发布",
    content_type="article",
    must_pass=[
        VerificationCheck("title_present", "must_pass", "标题存在且非空", "check_title"),
        VerificationCheck("body_min_length", "must_pass", "正文≥100字", "check_body_length"),
        VerificationCheck("cover_image", "must_pass", "封面图存在", "check_cover_image"),
        VerificationCheck("metadata_tags", "must_pass", "元数据包含tags", "check_metadata_tags"),
        VerificationCheck("readiness_score", "must_pass", "就绪评分≥0.7", "check_readiness_score"),
    ],
    must_fail_if=[
        VerificationCheck("empty_body", "must_fail_if", "正文为空", "check_body_empty"),
        VerificationCheck("encoding_error", "must_fail_if", "编码错误导致乱码", "check_encoding"),
    ],
    warnings=[
        VerificationCheck("short_body", "warning", "正文<500字，内容偏短", "check_body_short"),
        VerificationCheck("no_summary", "warning", "缺少summary元数据", "check_summary"),
    ],
)

PODCAST_CONTRACT = VerificationContract(
    task_id="template_podcast",
    task_name="播客发布",
    content_type="podcast",
    must_pass=[
        VerificationCheck("audio_exists", "must_pass", "音频文件存在", "check_file_exists"),
        VerificationCheck("audio_size", "must_pass", "音频文件>1MB", "check_file_size"),
        VerificationCheck("title_present", "must_pass", "标题存在", "check_title"),
    ],
    must_fail_if=[
        VerificationCheck("audio_corrupt", "must_fail_if", "音频文件损坏", "check_file_corrupt"),
    ],
    warnings=[
        VerificationCheck("audio_quality", "warning", "建议检查采样率/比特率", None),
    ],
)

VIDEO_CONTRACT = VerificationContract(
    task_id="template_video",
    task_name="视频发布",
    content_type="video",
    must_pass=[
        VerificationCheck("video_exists", "must_pass", "视频文件存在", "check_file_exists"),
        VerificationCheck("video_size", "must_pass", "视频文件>10MB", "check_file_size"),
        VerificationCheck("cover_image", "must_pass", "封面图存在", "check_cover_image"),
    ],
    must_fail_if=[
        VerificationCheck("video_corrupt", "must_fail_if", "视频文件损坏", "check_file_corrupt"),
    ],
    warnings=[],
)

TEMPLATES = {
    "article": ARTICLE_CONTRACT,
    "podcast": PODCAST_CONTRACT,
    "video": VIDEO_CONTRACT,
}


# ── 验证器函数 ──

def check_title(params: Dict) -> Tuple[bool, str]:
    path = Path(params.get("content_path", ""))
    if not path.exists():
        return False, "文件不存在"
    try:
        text = path.read_text(encoding="utf-8")
        lines = text.strip().split("\n")
        if lines and lines[0].startswith("#"):
            title = lines[0].lstrip("#").strip()
            return bool(title), title if title else "标题为空"
        if path.stem:
            return True, path.stem
        return False, "无法提取标题"
    except Exception as e:
        return False, str(e)


def check_body_length(params: Dict, min_length: int = 100) -> Tuple[bool, str]:
    path = Path(params.get("content_path", ""))
    if not path.exists():
        return False, "文件不存在"
    try:
        text = path.read_text(encoding="utf-8")
        lines = text.strip().split("\n")
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""
        length = len(body.strip())
        return length >= min_length, f"正文{length}字" + (f" < {min_length}" if length < min_length else "")
    except UnicodeDecodeError:
        return False, "UTF-8解码失败"


def check_body_empty(params: Dict) -> Tuple[bool, str]:
    ok, msg = check_body_length(params, 1)
    return not ok, msg  # must_fail_if: True means should fail


def check_body_short(params: Dict, threshold: int = 500) -> Tuple[bool, str]:
    ok, msg = check_body_length(params, threshold)
    return ok, msg


def check_cover_image(params: Dict) -> Tuple[bool, str]:
    cover_path = params.get("cover_path")
    if cover_path and Path(cover_path).exists():
        return True, f"封面图: {cover_path}"
    content_path = Path(params.get("content_path", ""))
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        candidates = [
            content_path.with_suffix(ext),
            content_path.parent / "cover" / (content_path.stem + ext),
            content_path.parent / "images" / (content_path.stem + ext),
        ]
        for c in candidates:
            if c.exists():
                return True, f"封面图: {c}"
    return False, "未找到封面图"


def check_metadata_tags(params: Dict) -> Tuple[bool, str]:
    content_path = Path(params.get("content_path", ""))
    for candidate in [
        content_path.with_suffix(".json"),
        content_path.parent / "metadata.json",
    ]:
        if candidate.exists():
            try:
                meta = json.loads(candidate.read_text(encoding="utf-8"))
                tags = meta.get("tags", meta.get("keywords", []))
                if tags:
                    return True, f"tags: {tags}"
            except (json.JSONDecodeError, OSError):
                pass
    return False, "元数据中无tags"


def check_readiness_score(params: Dict, min_score: float = 0.7) -> Tuple[bool, str]:
    score = params.get("readiness_score", 0)
    return score >= min_score, f"就绪评分: {score}"


def check_summary(params: Dict) -> Tuple[bool, str]:
    content_path = Path(params.get("content_path", ""))
    for candidate in [
        content_path.with_suffix(".json"),
        content_path.parent / "metadata.json",
    ]:
        if candidate.exists():
            try:
                meta = json.loads(candidate.read_text(encoding="utf-8"))
                if meta.get("summary") or meta.get("description"):
                    return True, "有summary"
            except (json.JSONDecodeError, OSError):
                pass
    return False, "无summary"


def check_file_exists(params: Dict) -> Tuple[bool, str]:
    path = Path(params.get("content_path", ""))
    return path.exists(), f"文件{'存在' if path.exists() else '不存在'}"


def check_file_size(params: Dict, min_mb: float = 1.0) -> Tuple[bool, str]:
    path = Path(params.get("content_path", ""))
    if not path.exists():
        return False, "文件不存在"
    size_mb = path.stat().st_size / (1024 * 1024)
    return size_mb >= min_mb, f"文件大小: {size_mb:.1f}MB"


def check_file_corrupt(params: Dict) -> Tuple[bool, str]:
    path = Path(params.get("content_path", ""))
    if not path.exists():
        return True, "文件不存在"
    if path.stat().st_size == 0:
        return True, "文件大小为0"
    return False, "文件正常"


def check_encoding(params: Dict) -> Tuple[bool, str]:
    path = Path(params.get("content_path", ""))
    if not path.exists():
        return True, "文件不存在"
    try:
        path.read_text(encoding="utf-8")
        return False, "编码正常"
    except UnicodeDecodeError:
        return True, "UTF-8解码失败，可能存在编码问题"


VALIDATORS: Dict[str, Callable] = {
    "check_title": check_title,
    "check_body_length": check_body_length,
    "check_body_empty": check_body_empty,
    "check_body_short": check_body_short,
    "check_cover_image": check_cover_image,
    "check_metadata_tags": check_metadata_tags,
    "check_readiness_score": check_readiness_score,
    "check_summary": check_summary,
    "check_file_exists": check_file_exists,
    "check_file_size": check_file_size,
    "check_file_corrupt": check_file_corrupt,
    "check_encoding": check_encoding,
}


# ── 契约执行 ──


def create_contract(content_type: str, content_path: str, platforms: List[str] = None) -> VerificationContract:
    template = TEMPLATES.get(content_type, ARTICLE_CONTRACT)
    return VerificationContract(
        task_id=f"publish_{content_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        task_name=template.task_name,
        content_type=content_type,
        platforms=platforms or [],
        must_pass=list(template.must_pass),
        must_fail_if=list(template.must_fail_if),
        warnings=list(template.warnings),
        verifier=template.verifier,
    )


def verify_contract(contract: VerificationContract, params: Dict) -> Dict:
    results = {
        "task_id": contract.task_id,
        "verified_at": datetime.now().isoformat(),
        "must_pass_results": [],
        "must_fail_if_results": [],
        "warning_results": [],
        "passed": True,
        "failed_checks": [],
        "warnings": [],
    }

    for check in contract.must_pass:
        validator = VALIDATORS.get(check.validator)
        if validator:
            try:
                ok, msg = validator(params)
            except Exception as e:
                ok, msg = False, f"验证器异常: {e}"
        else:
            ok, msg = True, "无验证器，默认通过"

        results["must_pass_results"].append({
            "name": check.name, "passed": ok, "message": msg, "severity": check.severity
        })
        if not ok:
            results["passed"] = False
            results["failed_checks"].append(check.name)

    for check in contract.must_fail_if:
        validator = VALIDATORS.get(check.validator)
        if validator:
            try:
                should_fail, msg = validator(params)
            except Exception as e:
                should_fail, msg = False, f"验证器异常: {e}"
        else:
            should_fail, msg = False, "无验证器"

        results["must_fail_if_results"].append({
            "name": check.name, "triggered": should_fail, "message": msg
        })
        if should_fail:
            results["passed"] = False
            results["failed_checks"].append(check.name)

    for check in contract.warnings:
        validator = VALIDATORS.get(check.validator)
        if validator:
            try:
                ok, msg = validator(params)
            except Exception as e:
                ok, msg = False, f"验证器异常: {e}"
        else:
            ok, msg = True, "无验证器"

        results["warning_results"].append({
            "name": check.name, "ok": ok, "message": msg
        })
        if not ok:
            results["warnings"].append(check.name)

    contract.verified_at = results["verified_at"]
    contract.verification_result = results

    _save_contract(contract)
    _update_drift_coefficient(results)

    return results


def _save_contract(contract: VerificationContract) -> None:
    _CONTRACT_DIR.mkdir(parents=True, exist_ok=True)
    path = _CONTRACT_DIR / f"{contract.task_id}.json"
    data = {
        "task_id": contract.task_id,
        "task_name": contract.task_name,
        "content_type": contract.content_type,
        "platforms": contract.platforms,
        "must_pass": [{"name": c.name, "type": c.check_type, "desc": c.description} for c in contract.must_pass],
        "must_fail_if": [{"name": c.name, "type": c.check_type, "desc": c.description} for c in contract.must_fail_if],
        "warnings": [{"name": c.name, "type": c.check_type, "desc": c.description} for c in contract.warnings],
        "verifier": contract.verifier,
        "created_at": contract.created_at,
        "verified_at": contract.verified_at,
        "verification_result": contract.verification_result,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _update_drift_coefficient(verification_result: Dict) -> None:
    _DRIFT_LOG.parent.mkdir(parents=True, exist_ok=True)
    drift_data = {"total": 0, "passed": 0, "failed": 0, "history": []}
    if _DRIFT_LOG.exists():
        try:
            drift_data = json.loads(_DRIFT_LOG.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    drift_data["total"] += 1
    if verification_result["passed"]:
        drift_data["passed"] += 1
    else:
        drift_data["failed"] += 1

    coefficient = drift_data["failed"] / max(drift_data["total"], 1)
    drift_data["coefficient"] = round(coefficient, 4)
    drift_data["updated_at"] = datetime.now().isoformat()

    drift_data["history"].append({
        "task_id": verification_result["task_id"],
        "passed": verification_result["passed"],
        "failed_checks": verification_result.get("failed_checks", []),
        "timestamp": verification_result["verified_at"],
    })
    drift_data["history"] = drift_data["history"][-100:]

    _DRIFT_LOG.write_text(json.dumps(drift_data, ensure_ascii=False, indent=2), encoding="utf-8")

    if coefficient > 0.15:
        logger.warning("漂移系数 %.1f%% > 15%% 阈值，建议暂停自主执行", coefficient * 100)
    elif coefficient > 0.05:
        logger.info("漂移系数 %.1f%% > 5%% 警告线", coefficient * 100)


def get_drift_coefficient() -> Dict:
    if not _DRIFT_LOG.exists():
        return {"coefficient": 0.0, "total": 0, "passed": 0, "failed": 0, "level": "normal"}
    try:
        data = json.loads(_DRIFT_LOG.read_text(encoding="utf-8"))
        coeff = data.get("coefficient", 0.0)
        level = "normal"
        if coeff > 0.15:
            level = "critical"
        elif coeff > 0.05:
            level = "warning"
        return {k: data.get(k) for k in ("coefficient", "total", "passed", "failed")} | {"level": level}
    except (json.JSONDecodeError, OSError):
        return {"coefficient": 0.0, "total": 0, "passed": 0, "failed": 0, "level": "unknown"}
