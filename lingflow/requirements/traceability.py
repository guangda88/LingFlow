"""需求追溯模块

跟踪需求从创建到实现的全生命周期，支持需求状态管理和追溯。

Version: 1.0
Date: 2026-03-27
"""

import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RequirementStatus(str, Enum):
    """需求状态"""

    DRAFT = "draft"  # 草稿
    PROPOSED = "proposed"  # 已提出
    APPROVED = "approved"  # 已批准
    IN_PROGRESS = "in_progress"  # 进行中
    IMPLEMENTED = "implemented"  # 已实现
    VERIFIED = "verified"  # 已验证
    RELEASED = "released"  # 已发布
    CANCELLED = "cancelled"  # 已取消


class RequirementPriority(str, Enum):
    """需求优先级"""

    CRITICAL = "critical"  # 关键
    HIGH = "high"  # 高
    MEDIUM = "medium"  # 中
    LOW = "low"  # 低


@dataclass
class Requirement:
    """需求数据模型"""

    id: str  # 需求 ID
    title: str  # 需求标题
    description: str  # 需求描述
    status: RequirementStatus = RequirementStatus.DRAFT
    priority: RequirementPriority = RequirementPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 追溯信息
    parent_id: Optional[str] = None  # 父需求 ID
    child_ids: List[str] = field(default_factory=list)  # 子需求 IDs
    depends_on: List[str] = field(default_factory=list)  # 依赖的需求 IDs
    blocks: List[str] = field(default_factory=list)  # 被此需求阻塞的需求 IDs

    # 实现追溯
    feature_branch: Optional[str] = None  # 功能分支
    commits: List[str] = field(default_factory=list)  # 相关提交
    pull_requests: List[str] = field(default_factory=list)  # PR IDs
    tasks: List[str] = field(default_factory=list)  # 任务 IDs

    # 验证追溯
    test_cases: List[str] = field(default_factory=list)  # 测试用例 IDs
    acceptance_criteria: List[str] = field(default_factory=list)  # 验收标准

    # 标签和分类
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    epic: Optional[str] = None  # 所属史诗

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换枚举为字符串
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        # 转换日期时间
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Requirement":
        """从字典创建"""
        # 转换字符串为枚举
        data["status"] = RequirementStatus(data.get("status", "draft"))
        data["priority"] = RequirementPriority(data.get("priority", "medium"))
        # 转换日期时间
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


@dataclass
class TraceEvent:
    """追溯事件"""

    id: str
    requirement_id: str
    event_type: str  # status_change, commit_added, pr_merged, etc.
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class RequirementsTraceability:
    """需求追溯管理器

    功能：
    - 需求生命周期管理
    - 需求依赖关系跟踪
    - 实现追溯（分支、提交、PR）
    - 状态变更历史
    - 需求报表
    """

    def __init__(self, storage_path: Optional[str] = None):
        """初始化需求追溯管理器

        Args:
            storage_path: 存储路径，默认为 .lingflow/requirements.json
        """
        if storage_path is None:
            storage_path = ".lingflow/requirements.json"

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 需求存储
        self._requirements: Dict[str, Requirement] = {}

        # 追溯事件
        self._events: List[TraceEvent] = []

        # 锁
        self._lock = threading.RLock()

        # 加载已有数据
        self._load()

    def _load(self):
        """从文件加载数据"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 加载需求
                for req_data in data.get("requirements", []):
                    req = Requirement.from_dict(req_data)
                    self._requirements[req.id] = req

                # 加载事件
                for event_data in data.get("events", []):
                    event = TraceEvent(**event_data)
                    if isinstance(event.timestamp, str):
                        event.timestamp = datetime.fromisoformat(event.timestamp)
                    self._events.append(event)

                logger.info(f"加载了 {len(self._requirements)} 个需求和 {len(self._events)} 个事件")
            except Exception as e:
                logger.error(f"加载数据失败: {e}")

    def _save(self):
        """保存数据到文件"""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "requirements": [req.to_dict() for req in self._requirements.values()],
                "events": [
                    {
                        "id": e.id,
                        "requirement_id": e.requirement_id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp.isoformat(),
                        "description": e.description,
                        "metadata": e.metadata,
                    }
                    for e in self._events
                ],
            }

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def create_requirement(
        self, id: str, title: str, description: str, priority: RequirementPriority = RequirementPriority.MEDIUM, **kwargs
    ) -> Requirement:
        """创建新需求

        Args:
            id: 需求 ID
            title: 需求标题
            description: 需求描述
            priority: 优先级
            **kwargs: 其他属性

        Returns:
            创建的需求
        """
        with self._lock:
            if id in self._requirements:
                raise ValueError(f"需求 {id} 已存在")

            req = Requirement(id=id, title=title, description=description, priority=priority, **kwargs)
            self._requirements[id] = req

            # 记录事件
            self._add_event(req.id, "created", f"创建需求: {title}")

            self._save()
            logger.info(f"创建需求: {id} - {title}")
            return req

    def get_requirement(self, id: str) -> Optional[Requirement]:
        """获取需求"""
        return self._requirements.get(id)

    def update_requirement(self, id: str, **kwargs) -> Optional[Requirement]:
        """更新需求

        Args:
            id: 需求 ID
            **kwargs: 要更新的字段

        Returns:
            更新后的需求，不存在则返回 None
        """
        with self._lock:
            if id not in self._requirements:
                return None

            req = self._requirements[id]

            # 记录状态变更
            if "status" in kwargs and kwargs["status"] != req.status:
                old_status = req.status.value
                new_status = kwargs["status"].value if isinstance(kwargs["status"], RequirementStatus) else kwargs["status"]
                self._add_event(id, "status_change", f"状态变更: {old_status} -> {new_status}")

            # 更新字段
            for key, value in kwargs.items():
                if hasattr(req, key):
                    setattr(req, key, value)

            req.updated_at = datetime.now()
            self._save()
            return req

    def delete_requirement(self, id: str) -> bool:
        """删除需求"""
        with self._lock:
            if id not in self._requirements:
                return False

            del self._requirements[id]
            self._add_event(id, "deleted", f"删除需求: {id}")
            self._save()
            return True

    def list_requirements(
        self,
        status: Optional[RequirementStatus] = None,
        priority: Optional[RequirementPriority] = None,
        category: Optional[str] = None,
        epic: Optional[str] = None,
    ) -> List[Requirement]:
        """列出需求

        Args:
            status: 过滤状态
            priority: 过滤优先级
            category: 过滤分类
            epic: 过滤史诗

        Returns:
            需求列表
        """
        requirements = list(self._requirements.values())

        # 应用过滤
        if status:
            requirements = [r for r in requirements if r.status == status]
        if priority:
            requirements = [r for r in requirements if r.priority == priority]
        if category:
            requirements = [r for r in requirements if r.category == category]
        if epic:
            requirements = [r for r in requirements if r.epic == epic]

        return requirements

    # === 实现追溯 ===

    def link_to_branch(self, requirement_id: str, branch: str) -> bool:
        """链接到功能分支"""
        return self.update_requirement(requirement_id, feature_branch=branch) is not None

    def add_commit(self, requirement_id: str, commit_hash: str) -> bool:
        """添加提交记录"""
        req = self.get_requirement(requirement_id)
        if not req:
            return False

        if commit_hash not in req.commits:
            req.commits.append(commit_hash)
            req.updated_at = datetime.now()
            self._add_event(requirement_id, "commit_added", f"添加提交: {commit_hash[:8]}")
            self._save()
        return True

    def add_pull_request(self, requirement_id: str, pr_id: str) -> bool:
        """添加 PR 记录"""
        req = self.get_requirement(requirement_id)
        if not req:
            return False

        if pr_id not in req.pull_requests:
            req.pull_requests.append(pr_id)
            req.updated_at = datetime.now()
            self._add_event(requirement_id, "pr_added", f"添加 PR: {pr_id}")
            self._save()
        return True

    def add_task(self, requirement_id: str, task_id: str) -> bool:
        """关联任务"""
        req = self.get_requirement(requirement_id)
        if not req:
            return False

        if task_id not in req.tasks:
            req.tasks.append(task_id)
            req.updated_at = datetime.now()
            self._save()
        return True

    def add_test_case(self, requirement_id: str, test_case_id: str) -> bool:
        """添加测试用例"""
        req = self.get_requirement(requirement_id)
        if not req:
            return False

        if test_case_id not in req.test_cases:
            req.test_cases.append(test_case_id)
            req.updated_at = datetime.now()
            self._add_event(requirement_id, "test_added", f"添加测试: {test_case_id}")
            self._save()
        return True

    # === 依赖管理 ===

    def add_dependency(self, requirement_id: str, depends_on: str) -> bool:
        """添加依赖关系"""
        req = self.get_requirement(requirement_id)
        if not req:
            return False

        if depends_on not in req.depends_on:
            req.depends_on.append(depends_on)
            # 更新被依赖需求的 blocks 列表
            dep_req = self.get_requirement(depends_on)
            if dep_req and requirement_id not in dep_req.blocks:
                dep_req.blocks.append(requirement_id)
            req.updated_at = datetime.now()
            self._add_event(requirement_id, "dependency_added", f"添加依赖: {depends_on}")
            self._save()
        return True

    # === 报表 ===

    def get_traceability_report(self, requirement_id: str) -> Dict[str, Any]:
        """获取需求追溯报告"""
        req = self.get_requirement(requirement_id)
        if not req:
            return {"error": "需求不存在"}

        # 获取相关事件
        events = [e for e in self._events if e.requirement_id == requirement_id]

        return {
            "requirement": req.to_dict(),
            "events": [
                {"type": e.event_type, "timestamp": e.timestamp.isoformat(), "description": e.description} for e in events
            ],
            "summary": {
                "commits_count": len(req.commits),
                "pull_requests_count": len(req.pull_requests),
                "tasks_count": len(req.tasks),
                "test_cases_count": len(req.test_cases),
                "dependencies_count": len(req.depends_on),
                "blocks_count": len(req.blocks),
            },
        }

    def get_status_summary(self) -> Dict[str, int]:
        """获取状态统计"""
        summary = {}
        for status in RequirementStatus:
            count = len(self.list_requirements(status=status))
            summary[status.value] = count
        return summary

    def _add_event(self, requirement_id: str, event_type: str, description: str, metadata: Dict[str, Any] = None):
        """添加追溯事件"""
        event = TraceEvent(
            id=f"{requirement_id}_{event_type}_{int(datetime.now().timestamp())}",
            requirement_id=requirement_id,
            event_type=event_type,
            description=description,
            metadata=metadata or {},
        )
        self._events.append(event)


# 全局单例
_traceability: Optional[RequirementsTraceability] = None
_traceability_lock = threading.Lock()


def get_traceability() -> RequirementsTraceability:
    """获取需求追溯管理器单例"""
    global _traceability
    if _traceability is None:
        with _traceability_lock:
            if _traceability is None:
                _traceability = RequirementsTraceability()
    return _traceability


# 便捷函数
def create_requirement(id: str, title: str, description: str, **kwargs) -> Requirement:
    """创建需求"""
    return get_traceability().create_requirement(id, title, description, **kwargs)


def get_requirement(id: str) -> Optional[Requirement]:
    """获取需求"""
    return get_traceability().get_requirement(id)


def update_requirement(id: str, **kwargs) -> Optional[Requirement]:
    """更新需求"""
    return get_traceability().update_requirement(id, **kwargs)


def list_requirements(**filters) -> List[Requirement]:
    """列出需求"""
    return get_traceability().list_requirements(**filters)


def link_to_branch(requirement_id: str, branch: str) -> bool:
    """链接到功能分支"""
    return get_traceability().link_to_branch(requirement_id, branch)


def add_commit(requirement_id: str, commit_hash: str) -> bool:
    """添加提交记录"""
    return get_traceability().add_commit(requirement_id, commit_hash)


def get_traceability_report(requirement_id: str) -> Dict[str, Any]:
    """获取追溯报告"""
    return get_traceability().get_traceability_report(requirement_id)
