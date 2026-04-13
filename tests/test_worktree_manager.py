"""Auto Mode Worktree 隔离策略测试

测试覆盖：
- Git 仓库检测
- Worktree 创建（有/无 git）
- Worktree 路径获取
- Worktree 完成和清理
- 降级目录（无 git 环境）
- 分支合并
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from lingflow.workflow.worktree_manager import AutoModeWorktree


@pytest.fixture
def temp_workdir(tmp_path: Path):
    """临时工作目录"""
    yield tmp_path


class TestGitDetection:
    """测试 Git 仓库检测"""

    def test_detect_git_repo_true(self, temp_workdir: Path):
        """测试检测到 git 仓库"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="true\n")
            wt = AutoModeWorktree(str(temp_workdir))
            assert wt.is_git_repo is True

    def test_detect_git_repo_false(self, temp_workdir: Path):
        """测试检测不到 git 仓库"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stdout="")
            wt = AutoModeWorktree(str(temp_workdir))
            assert wt.is_git_repo is False

    def test_detect_git_repo_no_git(self, temp_workdir: Path):
        """测试没有 git 命令"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            wt = AutoModeWorktree(str(temp_workdir))
            assert wt.is_git_repo is False


class TestWorktreeCreation:
    """测试 Worktree 创建"""

    def test_create_worktree_git(self, temp_workdir: Path):
        """测试在 git 仓库中创建 worktree"""
        with patch("subprocess.run") as mock_run:
            # 第一次调用: _detect_git_repo
            # 第二次调用: git worktree add
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="true\n"),
                MagicMock(returncode=0, stdout=""),
            ]

            wt = AutoModeWorktree(str(temp_workdir))
            result = wt.create_worktree("M001")

            assert result["success"] is True
            assert "branch" in result
            assert result["branch"] == "auto/m001"

    def test_create_worktree_custom_branch(self, temp_workdir: Path):
        """测试自定义分支名"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="true\n"),
                MagicMock(returncode=0, stdout=""),
            ]

            wt = AutoModeWorktree(str(temp_workdir))
            result = wt.create_worktree("M001", branch_name="feature/test")

            assert result["success"] is True
            assert result["branch"] == "feature/test"

    def test_create_worktree_git_failure(self, temp_workdir: Path):
        """测试 git worktree add 失败时降级"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="true\n"),
                MagicMock(returncode=1, stderr="error: branch already exists"),
            ]

            wt = AutoModeWorktree(str(temp_workdir))
            result = wt.create_worktree("M001")

            # 应该降级到目录
            assert result["success"] is True
            assert result.get("fallback") is True

    def test_create_worktree_no_git(self, temp_workdir: Path):
        """测试无 git 时创建降级目录"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            wt = AutoModeWorktree(str(temp_workdir))
            result = wt.create_worktree("M001")

            assert result["success"] is True
            assert result.get("fallback") is True
            assert result["type"] == "directory"

            # 检查目录是否创建
            fallback_dir = temp_workdir / ".lingflow" / "worktrees" / "m001"
            assert fallback_dir.exists()


class TestWorktreePath:
    """测试 Worktree 路径获取"""

    def test_get_worktree_path_from_cache(self, temp_workdir: Path):
        """测试从缓存获取路径"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            wt = AutoModeWorktree(str(temp_workdir))
            wt.create_worktree("M001")

            path = wt.get_worktree_path("M001")
            assert path is not None

    def test_get_worktree_path_from_disk(self, temp_workdir: Path):
        """测试从磁盘检测路径"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="true\n")
            wt = AutoModeWorktree(str(temp_workdir))

            # 创建预期的目录
            worktree_dir = temp_workdir.parent / f"{temp_workdir.name}-m001"
            worktree_dir.mkdir()

            path = wt.get_worktree_path("M001")
            assert path is not None
            assert "m001" in path

    def test_get_worktree_path_not_found(self, temp_workdir: Path):
        """测试路径不存在"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            wt = AutoModeWorktree(str(temp_workdir))
            path = wt.get_worktree_path("M999")
            assert path is None


class TestWorktreeCompletion:
    """测试 Worktree 完成"""

    def test_complete_without_merge(self, temp_workdir: Path):
        """测试完成但不合并"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="true\n"),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout=""),
            ]

            wt = AutoModeWorktree(str(temp_workdir))
            wt.create_worktree("M001")

            result = wt.complete_worktree("M001", merge=False)
            assert result["success"] is True
            assert result["merged"] is False

    def test_complete_with_merge(self, temp_workdir: Path):
        """测试完成并合并"""
        with patch("subprocess.run") as mock_run:
            # _detect, worktree add, checkout, merge, remove
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="true\n"),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout=""),
            ]

            wt = AutoModeWorktree(str(temp_workdir))
            wt.create_worktree("M001")

            result = wt.complete_worktree("M001", merge=True, target_branch="master")
            assert result["success"] is True
            assert result["merged"] is True

    def test_complete_merge_conflict(self, temp_workdir: Path):
        """测试合并冲突"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="true\n"),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=1, stderr="CONFLICT"),
                MagicMock(returncode=0, stdout=""),
            ]

            wt = AutoModeWorktree(str(temp_workdir))
            wt.create_worktree("M001")

            result = wt.complete_worktree("M001", merge=True)
            assert result["success"] is False
            assert "conflict" in result["error"].lower()

    def test_complete_unknown_milestone(self, temp_workdir: Path):
        """测试完成未知的 milestone"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            wt = AutoModeWorktree(str(temp_workdir))

            result = wt.complete_worktree("M999")
            assert result["success"] is False


class TestWorktreeList:
    """测试 Worktree 列表"""

    def test_list_worktrees_git(self, temp_workdir: Path):
        """测试在 git 仓库中列出 worktree"""
        with patch("subprocess.run") as mock_run:
            porcelain_output = "worktree /home/user/repo\nbranch refs/heads/master\n\nworktree /home/user/repo-m001\nbranch refs/heads/auto/m001\n"
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="true\n"),
                MagicMock(returncode=0, stdout=porcelain_output),
            ]

            wt = AutoModeWorktree(str(temp_workdir))
            worktrees = wt.list_worktrees()

            assert len(worktrees) == 2

    def test_list_worktrees_no_git(self, temp_workdir: Path):
        """测试无 git 时列出 worktree"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            wt = AutoModeWorktree(str(temp_workdir))
            wt.create_worktree("M001")

            worktrees = wt.list_worktrees()
            assert len(worktrees) == 1
            assert worktrees[0]["type"] == "directory"

    def test_list_worktrees_empty(self, temp_workdir: Path):
        """测试空 worktree 列表"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            wt = AutoModeWorktree(str(temp_workdir))
            worktrees = wt.list_worktrees()
            assert worktrees == []


class TestFallbackDirectory:
    """测试降级目录"""

    def test_fallback_directory_creation(self, temp_workdir: Path):
        """测试降级目录创建"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            wt = AutoModeWorktree(str(temp_workdir))
            result = wt.create_worktree("M002")

            assert result["fallback"] is True
            fallback_path = temp_workdir / ".lingflow" / "worktrees" / "m002"
            assert fallback_path.exists()

    def test_fallback_directory_reuse(self, temp_workdir: Path):
        """测试降级目录复用"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            wt = AutoModeWorktree(str(temp_workdir))

            result1 = wt.create_worktree("M003")
            result2 = wt.create_worktree("M003")

            assert result1["success"] is True
            assert result2["success"] is True
            assert result1["path"] == result2["path"]
