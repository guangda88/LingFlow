"""发布工作流编排器 — 灵通调度灵扬执行的发布管线

职责:
1. 内容就绪检查（灵通问道产出验证）
2. 平台适配（Dev.to/Reddit/HN/微信/B站/喜马拉雅）
3. 封面图/元数据生成
4. 调度灵扬执行发布
5. 发布状态追踪

不执行发布本身 — 发布执行由灵扬负责。

记忆增强：执行前自动从灵克记忆引擎召回相关历史经验。
"""

import json
import sys
from pathlib import Path

try:
    from . import verification_contract
except ImportError:
    try:
        import verification_contract
    except ImportError:
        verification_contract = None

_LING_CLAUDE_PATH = Path.home() / "lingclaude"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LINGFLOW_MEMORY_DB = _PROJECT_ROOT / ".lingflow" / "memory.db"
_MEMORY_CONTEXT = None
_MEMORY_IMPORTED = False

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_PUBLISH_STATE_DIR = _PROJECT_ROOT / ".lingflow" / "publish_state"


def _ensure_memory_loaded() -> None:
    """懒加载灵通自己的记忆引擎"""
    global _MEMORY_IMPORTED, _MEMORY_CONTEXT
    if _MEMORY_IMPORTED:
        return
    try:
        sys.path.insert(0, str(_LING_CLAUDE_PATH))
        from lingclaude.core.memory_engine import LingMemory
        _MEMORY_CONTEXT = LingMemory(db_path=str(_LINGFLOW_MEMORY_DB))
        _MEMORY_IMPORTED = True
    except ImportError as e:
        logger.warning("记忆引擎加载失败: %s", e)
        _MEMORY_IMPORTED = True


def _recall_experience(query: str, tags: list = None) -> list:
    """从记忆引擎召回相关经验"""
    _ensure_memory_loaded()
    if _MEMORY_CONTEXT is None:
        return []
    try:
        results = _MEMORY_CONTEXT.recall_detailed(query, tags=tags, limit=3)
        return results
    except Exception as e:
        logger.warning("记忆召回失败: %s", e)
        return []
_PLATFORMS = {
    "dev_to": {"name": "Dev.to", "api": True, "requires_auth": "api_key"},
    "reddit": {"name": "Reddit", "api": True, "requires_auth": "oauth"},
    "hackernews": {"name": "Hacker News", "api": False, "requires_auth": "manual"},
    "wechat_mp": {"name": "微信公众号", "api": True, "requires_auth": "app_secret"},
    "bilibili": {"name": "B站", "api": True, "requires_auth": "cookie"},
    "ximalaya": {"name": "喜马拉雅", "api": True, "requires_auth": "cookie"},
    "xiaoyuzhou": {"name": "小宇宙", "api": False, "requires_auth": "rss"},
}


@dataclass
class PublishContent:
    content_id: str
    content_type: str  # "article" | "podcast" | "video"
    title: str
    source: str  # "lingtongask" | "lingyang" | "external"
    platforms: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    readiness_score: float = 0.0
    issues: List[str] = field(default_factory=list)


@dataclass
class PublishPlan:
    content: PublishContent
    platform_tasks: List[Dict[str, Any]]
    estimated_time: str
    requires_human: List[str]
    can_auto_publish: List[str]


def execute_skill(params: Dict) -> Dict:
    """执行发布工作流编排

    Args:
        params: 包含 action 和相关参数的字典
            action: "check_readiness" | "create_plan" | "track_status" | "dispatch"
    """
    _ensure_memory_loaded()
    action = params.get("action", "check_readiness")

    if action == "check_readiness":
        result = _check_readiness(params)
    elif action == "create_plan":
        result = _create_plan(params)
    elif action == "track_status":
        return _track_status(params)
    elif action == "dispatch":
        result = _dispatch_to_lingyang(params)
    else:
        return {"success": False, "error": f"未知 action: {action}"}

    if isinstance(result, dict) and result.get("success"):
        content_type = params.get("content_type", "")
        query_tags = ["发布", content_type] if content_type else ["发布"]
        recall_hits = _recall_experience(f"发布 {content_type}", tags=query_tags)
        if recall_hits:
            result["recalled_experience"] = [
                {"title": r["episode"]["title"], "score": r["score"]}
                for r in recall_hits
            ]

    return result


def _check_readiness(params: Dict) -> Dict:
    """检查内容是否就绪发布（带验证契约检查"""
    content_path = params.get("content_path")
    content_type = params.get("content_type", "article")
    platforms = params.get("platforms", [])
    use_verification_contract = params.get("use_verification_contract", True)

    if not content_path:
        return {"success": False, "error": "缺少 content_path"}

    path = Path(content_path)
    if not path.exists():
        return {"success": False, "error": f"路径不存在: {content_path}"}

    checks = {
        "content_exists": True,
        "title_present": False,
        "body_present": False,
        "cover_image": False,
        "metadata_complete": False,
        "platform_compatible": {},
    }
    issues = []
    readiness_score = 0.0

    # 验证契约检查 (A2 主线任务)
    verification_result = None
    if use_verification_contract and verification_contract:
        try:
            contract = verification_contract.create_contract(
                content_type=content_type,
                content_path=content_path,
                platforms=platforms
            )
            verification_result = verification_contract.verify_contract(
                contract,
                params
            )
            checks["verification_contract"] = verification_result
        except Exception as e:
            logger.warning("验证契约执行失败: %s", e)

    if content_type == "article":
        checks["title_present"], checks["body_present"], title, body_len = _check_article(path)
        if checks["title_present"]:
            readiness_score += 0.25
        else:
            issues.append("缺少标题")
        if checks["body_present"]:
            readiness_score += 0.25
        else:
            issues.append("缺少正文内容")
    elif content_type == "podcast":
        checks["title_present"] = bool(path.stem)
        checks["body_present"] = path.stat().st_size > 0
        if checks["title_present"]:
            readiness_score += 0.25
        if checks["body_present"]:
            readiness_score += 0.25

    cover_path = params.get("cover_path")
    if cover_path and Path(cover_path).exists():
        checks["cover_image"] = True
        readiness_score += 0.2
    elif content_type == "article":
        issues.append("缺少封面图")

    metadata = _load_metadata(path)
    if metadata:
        checks["metadata_complete"] = bool(metadata.get("tags") or metadata.get("summary"))
        if checks["metadata_complete"]:
            readiness_score += 0.15
        else:
            issues.append("元数据不完整（建议补充 tags/summary）")
    else:
        issues.append("缺少元数据文件")

    for platform in platforms:
        plat_info = _PLATFORMS.get(platform)
        if not plat_info:
            checks["platform_compatible"][platform] = {"compatible": False, "reason": "未知平台"}
            issues.append(f"未知平台: {platform}")
            continue
        compat, reason = _check_platform_compat(content_type, platform, metadata or {})
        checks["platform_compatible"][platform] = {"compatible": compat, "reason": reason}
        if compat:
            readiness_score += 0.15 / max(len(platforms), 1)

    readiness_score = min(readiness_score, 1.0)
    ready = readiness_score >= 0.7 and len([i for i in issues if "缺少" in i]) == 0

    # 整合验证契约的漂移系数
    drift_coefficient = None
    if verification_result:
        drift = verification_contract.get_drift_coefficient()
        drift_coefficient = drift

    result = {
        "success": True,
        "action": "check_readiness",
        "content_id": path.stem,
        "content_type": content_type,
        "checks": checks,
        "readiness_score": round(readiness_score, 2),
        "ready": ready,
        "issues": issues,
        "metadata": metadata,
        "verification_result": verification_result,
        "drift_coefficient": drift_coefficient,
    }

    _save_state(result)
    return result


def _create_plan(params: Dict) -> Dict:
    """创建发布计划"""
    content_path = params.get("content_path")
    platforms = params.get("platforms", [])
    content_type = params.get("content_type", "article")

    if not content_path:
        return {"success": False, "error": "缺少 content_path"}

    readiness = _check_readiness(params)
    if not readiness["success"]:
        return readiness

    platform_tasks = []
    can_auto = []
    requires_human = []

    for platform in platforms:
        plat_info = _PLATFORMS.get(platform, {})
        task = {
            "platform": platform,
            "platform_name": plat_info.get("name", platform),
            "auto_possible": plat_info.get("api", False),
            "auth_required": plat_info.get("requires_auth", "unknown"),
            "steps": _get_platform_steps(content_type, platform),
        }
        platform_tasks.append(task)
        if task["auto_possible"] and task["auth_required"] in ("api_key", "oauth", "app_secret"):
            can_auto.append(platform)
        else:
            requires_human.append(f"{plat_info.get('name', platform)} ({task['auth_required']})")

    plan = {
        "success": True,
        "action": "create_plan",
        "content_path": content_path,
        "content_type": content_type,
        "readiness_score": readiness["readiness_score"],
        "ready": readiness["ready"],
        "platform_tasks": platform_tasks,
        "can_auto_publish": can_auto,
        "requires_human": requires_human,
        "estimated_time": f"{len(platform_tasks) * 5} 分钟（自动）+ 人工操作待定",
        "dispatch_to": "lingyang",
        "next_step": "dispatch" if readiness["ready"] else "fix_issues",
        "issues": readiness.get("issues", []),
    }

    _save_state(plan)
    return plan


def _track_status(params: Dict) -> Dict:
    """追踪发布状态"""
    content_id = params.get("content_id")

    state_file = _PUBLISH_STATE_DIR / f"{content_id}.json"
    if not state_file.exists():
        return {
            "success": True,
            "action": "track_status",
            "content_id": content_id,
            "status": "unknown",
            "message": "无发布记录",
        }

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"success": False, "error": f"状态文件损坏: {state_file}"}

    return {
        "success": True,
        "action": "track_status",
        "content_id": content_id,
        "status": state.get("status", "unknown"),
        "history": state.get("history", []),
        "last_updated": state.get("last_updated"),
    }


def _dispatch_to_lingyang(params: Dict) -> Dict:
    """生成灵扬调度指令并通过LingBus发送"""
    content_path = params.get("content_path")
    platforms = params.get("platforms", [])

    plan_result = _create_plan(params)
    if not plan_result["success"]:
        return plan_result

    if not plan_result["ready"]:
        return {
            "success": False,
            "error": "内容未就绪，无法调度",
            "issues": plan_result.get("issues", []),
        }

    dispatch = {
        "success": True,
        "action": "dispatch",
        "content_path": content_path,
        "platforms": platforms,
        "platform_tasks": plan_result["platform_tasks"],
        "dispatch_to": "lingyang",
        "dispatch_message": (
            f"灵通发布调度指令：\n"
            f"内容: {content_path}\n"
            f"类型: {plan_result['content_type']}\n"
            f"目标平台: {', '.join(platforms)}\n"
            f"自动发布: {', '.join(plan_result['can_auto_publish']) or '无'}\n"
            f"需人工: {', '.join(plan_result['requires_human']) or '无'}\n"
            f"请灵扬确认收到并执行。"
        ),
        "timestamp": datetime.now().isoformat(),
    }

    _send_via_lingbus(dispatch)

    _save_state(dispatch)
    return dispatch


def _send_via_lingbus(dispatch: Dict) -> Dict:
    """通过LingBus MCP工具发送dispatch消息给灵扬"""
    try:
        import sqlite3
        from pathlib import Path

        lingbus_db = Path.home() / ".lingmessage" / "lingbus.db"
        if not lingbus_db.exists():
            logger.warning(f"LingBus DB不存在: {lingbus_db}")
            return {"sent": False, "error": "LingBus DB不存在"}

        conn = sqlite3.connect(str(lingbus_db))
        conn.execute(
            """INSERT INTO messages (thread_id, sender, recipient, subject, body, channel)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                dispatch.get("content_id", "publish_" + datetime.now().strftime("%Y%m%d%H%M%S")),
                "lingflow",
                "lingyang",
                f"灵通发布调度: {Path(dispatch['content_path']).stem}",
                dispatch["dispatch_message"],
                "ecosystem",
            ),
        )
        conn.commit()
        conn.close()
        logger.info("发布调度已通过LingBus发送给灵扬")
        return {"sent": True}
    except Exception as e:
        logger.warning(f"LingBus发送失败: {e}，dispatch仍保存到本地状态")
        return {"sent": False, "error": str(e)}


def _check_article(path: Path) -> Tuple[bool, bool, str, int]:
    """检查文章文件"""
    title = ""
    body_len = 0
    title_present = False
    body_present = False

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        if lines and lines[0].startswith("#"):
            title = lines[0].lstrip("#").strip()
            title_present = bool(title)
        body_text = "\n".join(lines[1:]) if len(lines) > 1 else ""
        body_len = len(body_text.strip())
        body_present = body_len > 100
    except (OSError, UnicodeDecodeError):
        pass

    return title_present, body_present, title, body_len


def _check_platform_compat(
    content_type: str, platform: str, metadata: Dict
) -> Tuple[bool, str]:
    """检查内容与平台的兼容性"""
    compat_map = {
        "article": ["dev_to", "reddit", "hackernews", "wechat_mp"],
        "podcast": ["xiaoyuzhou", "ximalaya"],
        "video": ["bilibili"],
    }
    supported = compat_map.get(content_type, [])
    if platform in supported:
        return True, "兼容"
    if platform == "dev_to" and content_type in ("article",):
        return True, "兼容"
    if content_type not in supported and platform in supported:
        return False, f"{content_type} 类型不支持 {platform}"
    return True, "兼容（需确认）"


def _get_platform_steps(content_type: str, platform: str) -> List[str]:
    """获取平台发布步骤"""
    steps_map = {
        "dev_to": ["格式转换(Markdown)", "封面图上传", "API发布", "URL记录"],
        "reddit": ["标题优化", "subreddit选择", "手动发布", "反馈追踪"],
        "hackernews": ["标题优化", "摘要生成", "手动提交"],
        "wechat_mp": ["格式转换(富文本)", "封面图", "草稿创建", "人工确认发布"],
        "bilibili": ["视频上传", "封面图", "标题/标签/简介", "发布"],
        "ximalaya": ["音频上传", "封面图", "标题/标签", "发布"],
        "xiaoyuzhou": ["RSS feed更新", "音频文件部署", "自动抓取等待"],
    }
    return steps_map.get(platform, ["确认发布流程"])


def _load_metadata(path: Path) -> Optional[Dict]:
    """加载元数据"""
    candidates = [
        path.with_suffix(".json"),
        path.parent / "metadata.json",
        path.parent / f"{path.stem}_meta.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
    frontmatter = _parse_frontmatter(path)
    if frontmatter:
        return frontmatter
    return None


def _parse_frontmatter(path: Path) -> Optional[Dict]:
    """解析 Markdown frontmatter"""
    try:
        text = path.read_text(encoding="utf-8")
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                fm = text[3:end].strip()
                meta = {}
                for line in fm.split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        meta[key.strip()] = val.strip().strip('"').strip("'")
                return meta if meta else None
    except (OSError, UnicodeDecodeError):
        pass
    return None


def _save_state(data: Dict) -> None:
    """保存发布状态"""
    _PUBLISH_STATE_DIR.mkdir(parents=True, exist_ok=True)
    content_id = data.get("content_id", data.get("content_path", "unknown"))
    content_id = re.sub(r'[^\w\-.]', '_', str(content_id))
    state_file = _PUBLISH_STATE_DIR / f"{content_id}.json"

    existing = {}
    if state_file.exists():
        try:
            existing = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    history = existing.get("history", [])
    history.append({
        "timestamp": datetime.now().isoformat(),
        "action": data.get("action"),
        "readiness_score": data.get("readiness_score"),
    })

    state = {
        "content_id": content_id,
        "status": data.get("action", "unknown"),
        "last_updated": datetime.now().isoformat(),
        "history": history[-20:],
        "data": data,
    }

    try:
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        logger.warning(f"保存发布状态失败: {e}")
