"""Auto Mode Worktree 隔离策略

参考 GSD 的 Worktree Isolation：
- 每个 milestone 在独立的 git worktree 中执行
- 防止主分支被污染
- 支持并行开发（不同 milestone 在不同 worktree）
- 完成后合并回主分支

设计原则：
- Worktree 是可选的（没有 git 仓库时降级为目录隔离）
- 自动检测 git 环境
- Worktree 生命周期：create → use → complete → merge/cleanup
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WorktreeInfo:
    """Worktree 信息"""

    worktree_path: str
    branch_name: str
    milestone_id: str
    created_at: str = ""
    status: str = "active"  # active, merged, abandoned


class AutoModeWorktree:
    """Auto Mode Worktree 管理器

    管理里程碑级别的 git worktree 隔离。
    """

    def __init__(self, repo_root: str):
        """初始化 worktree 管理器

        Args:
            repo_root: Git 仓库根目录
        """
        self.repo_root = Path(repo_root)
        self._is_git_repo = self._detect_git_repo()
        self._worktrees: Dict[str, WorktreeInfo] = {}

    def _detect_git_repo(self) -> bool:
        """检测是否在 git 仓库中

        Returns:
            是否是 git 仓库
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=5,
            )
            return result.returncode == 0 and "true" in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @property
    def is_git_repo(self) -> bool:
        """是否在 git 仓库中"""
        return self._is_git_repo

    def create_worktree(self, milestone_id: str, branch_name: Optional[str] = None) -> Dict[str, Any]:
        """为 milestone 创建 worktree

        Args:
            milestone_id: Milestone ID
            branch_name: 分支名（默认 auto/{milestone_id}）

        Returns:
            创建结果
        """
        if not self._is_git_repo:
            return self._create_fallback_directory(milestone_id)

        if branch_name is None:
            branch_name = f"auto/{milestone_id.lower()}"

        worktree_path = self.repo_root.parent / f"{self.repo_root.name}-{milestone_id.lower()}"

        if worktree_path.exists():
            logger.info(f"Worktree 目录已存在: {worktree_path}")
            self._worktrees[milestone_id] = WorktreeInfo(
                worktree_path=str(worktree_path),
                branch_name=branch_name,
                milestone_id=milestone_id,
                status="active",
            )
            return {"success": True, "path": str(worktree_path), "branch": branch_name, "existing": True}

        try:
            result = subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(f"创建 worktree 失败: {result.stderr}")
                return self._create_fallback_directory(milestone_id)

            info = WorktreeInfo(
                worktree_path=str(worktree_path),
                branch_name=branch_name,
                milestone_id=milestone_id,
            )
            self._worktrees[milestone_id] = info

            logger.info(f"Worktree 创建成功: {worktree_path} (branch: {branch_name})")
            return {"success": True, "path": str(worktree_path), "branch": branch_name}

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error(f"创建 worktree 异常: {e}")
            return self._create_fallback_directory(milestone_id)

    def get_worktree_path(self, milestone_id: str) -> Optional[str]:
        """获取 milestone 的 worktree 路径

        Args:
            milestone_id: Milestone ID

        Returns:
            Worktree 路径，不存在返回 None
        """
        if milestone_id in self._worktrees:
            return self._worktrees[milestone_id].worktree_path

        worktree_path = self.repo_root.parent / f"{self.repo_root.name}-{milestone_id.lower()}"
        if worktree_path.exists():
            return str(worktree_path)

        return None

    def complete_worktree(self, milestone_id: str, merge: bool = False, target_branch: str = "master") -> Dict[str, Any]:
        """完成 worktree（合并并清理）

        Args:
            milestone_id: Milestone ID
            merge: 是否合并到目标分支
            target_branch: 目标分支

        Returns:
            完成结果
        """
        if milestone_id not in self._worktrees:
            return {"success": False, "error": f"No worktree for milestone {milestone_id}"}

        info = self._worktrees[milestone_id]

        if merge and self._is_git_repo:
            merge_result = self._merge_branch(info.branch_name, target_branch)
            if not merge_result["success"]:
                return merge_result

        # 清理 worktree
        if self._is_git_repo:
            self._remove_worktree(info.worktree_path)

        info.status = "merged" if merge else "abandoned"
        logger.info(f"Worktree 完成: {milestone_id} (merged={merge})")

        return {"success": True, "merged": merge, "branch": info.branch_name}

    def list_worktrees(self) -> List[Dict[str, Any]]:
        """列出所有 worktree

        Returns:
            Worktree 信息列表
        """
        if not self._is_git_repo:
            return [
                {
                    "milestone_id": info.milestone_id,
                    "path": info.worktree_path,
                    "status": info.status,
                    "type": "directory",
                }
                for info in self._worktrees.values()
            ]

        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=10,
            )

            if result.returncode != 0:
                return []

            worktrees = []
            current = {}
            for line in result.stdout.strip().split("\n"):
                if line.startswith("worktree "):
                    if current:
                        worktrees.append(current)
                    current = {"path": line.split(" ", 1)[1]}
                elif line.startswith("branch "):
                    current["branch"] = line.split(" ", 1)[1]
                elif line == "bare":
                    current["bare"] = True

            if current:
                worktrees.append(current)

            return worktrees

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

    def _merge_branch(self, source_branch: str, target_branch: str) -> Dict[str, Any]:
        """合并分支

        Args:
            source_branch: 源分支
            target_branch: 目标分支

        Returns:
            合并结果
        """
        try:
            # 切换到目标分支
            subprocess.run(
                ["git", "checkout", target_branch],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=10,
            )

            # 合并
            result = subprocess.run(
                ["git", "merge", source_branch, "--no-edit"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=60,
            )

            if result.returncode != 0:
                # 合并冲突，回退
                subprocess.run(
                    ["git", "merge", "--abort"],
                    capture_output=True,
                    cwd=str(self.repo_root),
                    timeout=10,
                )
                return {"success": False, "error": f"Merge conflict: {result.stderr}"}

            logger.info(f"分支合并成功: {source_branch} → {target_branch}")
            return {"success": True}

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return {"success": False, "error": str(e)}

    def _remove_worktree(self, worktree_path: str) -> Dict[str, Any]:
        """移除 worktree

        Args:
            worktree_path: Worktree 路径

        Returns:
            移除结果
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "remove", worktree_path],
                capture_output=True,
                text=True,
                cwd=str(self.repo_root),
                timeout=15,
            )

            if result.returncode != 0:
                logger.warning(f"移除 worktree 失败: {result.stderr}")
                return {"success": False, "error": result.stderr}

            return {"success": True}

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return {"success": False, "error": str(e)}

    def _create_fallback_directory(self, milestone_id: str) -> Dict[str, Any]:
        """创建降级目录（无 git 时使用）

        Args:
            milestone_id: Milestone ID

        Returns:
            创建结果
        """
        fallback_dir = self.repo_root / ".lingflow" / "worktrees" / milestone_id.lower()
        fallback_dir.mkdir(parents=True, exist_ok=True)

        self._worktrees[milestone_id] = WorktreeInfo(
            worktree_path=str(fallback_dir),
            branch_name=f"auto/{milestone_id.lower()}",
            milestone_id=milestone_id,
            status="active",
        )

        logger.info(f"降级目录创建: {fallback_dir}")
        return {"success": True, "path": str(fallback_dir), "type": "directory", "fallback": True}
