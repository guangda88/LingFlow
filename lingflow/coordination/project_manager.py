"""多项目管理器

管理多个项目上下文，包括路径、终端会话、Git 状态等。
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PROJECT_REGISTRY_PATH = Path.home() / ".lingflow" / "projects.json"


@dataclass
class ProjectContext:
    """项目上下文

    Attributes:
        name: 项目别名
        path: 项目根目录绝对路径
        description: 项目描述
        tags: 项目标签
        terminal_session: 灵犀终端会话 ID（运行时绑定）
    """

    name: str
    path: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    terminal_session: Optional[str] = None

    def is_valid(self) -> bool:
        """检查项目路径是否存在且为 Git 仓库"""
        p = Path(self.path)
        return p.is_dir() and (p / ".git").is_dir()

    def git_status(self) -> Dict[str, Any]:
        """获取项目 Git 状态"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain=v1", "--branch"],
                capture_output=True,
                text=True,
                cwd=self.path,
                timeout=10,
            )
            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
            branch = "unknown"
            dirty = 0
            for line in lines:
                if line.startswith("## "):
                    parts = line[3:].split("...")
                    branch = parts[0]
                elif line and not line.startswith("##"):
                    dirty += 1
            return {"branch": branch, "dirty_files": dirty, "valid": True}
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.warning(f"Failed to get git status for {self.name}: {e}")
            return {"branch": "unknown", "dirty_files": 0, "valid": False}


class ProjectManager:
    """多项目管理器

    负责项目注册、查询、状态检查。
    持久化到 ~/.lingflow/projects.json。
    """

    def __init__(self, registry_path: Optional[str] = None):
        self._projects: Dict[str, ProjectContext] = {}
        self._registry_path = Path(registry_path) if registry_path else PROJECT_REGISTRY_PATH
        self._load()

    def register(self, name: str, path: str, description: str = "", tags: Optional[List[str]] = None) -> ProjectContext:
        """注册项目

        Args:
            name: 项目别名（唯一）
            path: 项目根目录
            description: 描述
            tags: 标签

        Returns:
            注册的项目上下文

        Raises:
            ValueError: 路径不存在
        """
        abs_path = str(Path(path).resolve())
        if not Path(abs_path).is_dir():
            raise ValueError(f"Project path does not exist: {abs_path}")

        ctx = ProjectContext(
            name=name,
            path=abs_path,
            description=description,
            tags=tags or [],
        )
        self._projects[name] = ctx
        self._save()
        logger.info(f"Registered project: {name} -> {abs_path}")
        return ctx

    def unregister(self, name: str) -> bool:
        """取消注册项目"""
        if name in self._projects:
            del self._projects[name]
            self._save()
            logger.info(f"Unregistered project: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[ProjectContext]:
        """获取项目上下文"""
        return self._projects.get(name)

    def list(self) -> List[ProjectContext]:
        """列出所有项目"""
        return list(self._projects.values())

    def status(self, name: str) -> Dict[str, Any]:
        """获取项目完整状态"""
        ctx = self._projects.get(name)
        if not ctx:
            return {"error": f"Project not found: {name}"}
        git = ctx.git_status()
        return {
            "name": ctx.name,
            "path": ctx.path,
            "description": ctx.description,
            "tags": ctx.tags,
            "terminal_session": ctx.terminal_session,
            "git": git,
            "valid": ctx.is_valid(),
        }

    def dashboard(self) -> List[Dict[str, Any]]:
        """获取所有项目状态摘要"""
        return [self.status(name) for name in self._projects]

    def bind_session(self, name: str, session_id: str) -> None:
        """绑定灵犀终端会话"""
        ctx = self._projects.get(name)
        if ctx:
            ctx.terminal_session = session_id
            self._save()

    def _save(self) -> None:
        """持久化到 JSON"""
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        for name, ctx in self._projects.items():
            data[name] = {
                "name": ctx.name,
                "path": ctx.path,
                "description": ctx.description,
                "tags": ctx.tags,
            }
        with open(self._registry_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load(self) -> None:
        """从 JSON 加载"""
        if not self._registry_path.exists():
            return
        try:
            with open(self._registry_path) as f:
                data = json.load(f)
            for name, info in data.items():
                self._projects[name] = ProjectContext(
                    name=info["name"],
                    path=info["path"],
                    description=info.get("description", ""),
                    tags=info.get("tags", []),
                )
            logger.info(f"Loaded {len(self._projects)} projects from {self._registry_path}")
        except (json.JSONDecodeError, OSError, KeyError) as e:
            logger.warning(f"Failed to load project registry: {e}")
