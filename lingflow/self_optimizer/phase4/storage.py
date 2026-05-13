"""
lingflow Phase 4: 参数持久化存储

YOLO实现：简单、快速、有效
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from lingflow.self_optimizer.phase4.data_types import ParameterVersion


class FileSystemParameterStore:
    """文件系统参数存储"""

    def __init__(self, base_path: str = ".lingflow/params"):
        """初始化存储"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 子目录
        self.versions_dir = self.base_path / "versions"
        self.index_dir = self.base_path / "index"
        self.versions_dir.mkdir(exist_ok=True)
        self.index_dir.mkdir(exist_ok=True)

        # 索引文件
        self.index_file = self.index_dir / "index.json"
        self._index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """加载索引"""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except Exception:
                return {"versions": {}, "by_params": {}, "by_project": {}}
        return {"versions": {}, "by_params": {}, "by_project": {}}

    def _save_index(self):
        """保存索引"""
        self.index_file.write_text(json.dumps(self._index, indent=2, ensure_ascii=False))

    def _compute_checksum(self, params: Dict[str, Any]) -> str:
        """计算参数校验和"""
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(params_str.encode(), usedforsecurity=False).hexdigest()

    def save(
        self,
        params: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        project: str = "default",
        parent: Optional[str] = None,
    ) -> ParameterVersion:
        """保存参数"""
        checksum = self._compute_checksum(params)
        timestamp = datetime.now()
        version_id = f"{project}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{checksum[:8]}"

        # 创建ParameterVersion
        version = ParameterVersion(
            version_id=version_id,
            params=params,
            metadata=metadata or {},
            parent_version=parent,
            created_at=timestamp,
            checksum=checksum,
        )

        # 保存版本文件
        version_file = self.versions_dir / f"{version_id}.json"
        version_data = {
            "version_id": version.version_id,
            "params": version.params,
            "metadata": version.metadata,
            "parent_version": version.parent_version,
            "created_at": version.created_at.isoformat(),
            "checksum": version.checksum,
        }
        version_file.write_text(json.dumps(version_data, indent=2, ensure_ascii=False))

        # 更新索引
        self._index["versions"][version_id] = {
            "checksum": checksum,
            "project": project,
            "created_at": timestamp.isoformat(),
            "parent": parent,
        }
        self._index["by_params"][checksum] = version_id
        if project not in self._index["by_project"]:
            self._index["by_project"][project] = []
        self._index["by_project"][project].append(version_id)

        self._save_index()
        return version

    def load(self, version_id: str) -> Optional[ParameterVersion]:
        """加载参数"""
        version_file = self.versions_dir / f"{version_id}.json"
        if not version_file.exists():
            return None

        try:
            data = json.loads(version_file.read_text())
            return ParameterVersion(
                version_id=data["version_id"],
                params=data["params"],
                metadata=data.get("metadata", {}),
                parent_version=data.get("parent_version"),
                created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
                checksum=data.get("checksum"),
            )
        except Exception:
            return None

    def find_by_params(self, params: Dict[str, Any]) -> Optional[ParameterVersion]:
        """根据参数查找版本"""
        checksum = self._compute_checksum(params)
        version_id = self._index["by_params"].get(checksum)
        if version_id:
            return self.load(version_id)
        return None

    def list_versions(self, project: Optional[str] = None, limit: int = 100) -> List[ParameterVersion]:
        """列出版本"""
        version_ids = []
        if project:
            version_ids = self._index["by_project"].get(project, [])
        else:
            version_ids = list(self._index["versions"].keys())

        # 排序（最新的在前）
        version_ids.sort(key=lambda x: self._index["versions"][x]["created_at"], reverse=True)

        versions = []
        for vid in version_ids[:limit]:
            version = self.load(vid)
            if version:
                versions.append(version)

        return versions

    def get_latest(self, project: str = "default") -> Optional[ParameterVersion]:
        """获取最新版本"""
        versions = self.list_versions(project, limit=1)
        return versions[0] if versions else None

    def delete(self, version_id: str) -> bool:
        """删除版本"""
        version = self.load(version_id)
        if not version:
            return False

        # 删除文件
        version_file = self.versions_dir / f"{version_id}.json"
        version_file.unlink(missing_ok=True)

        # 更新索引
        project = self._index["versions"].get(version_id, {}).get("project", "unknown")
        checksum = self._index["versions"].get(version_id, {}).get("checksum", "")

        if version_id in self._index["versions"]:
            del self._index["versions"][version_id]
        if checksum and checksum in self._index["by_params"]:
            del self._index["by_params"][checksum]
        if project in self._index["by_project"] and version_id in self._index["by_project"][project]:
            self._index["by_project"][project].remove(version_id)

        self._save_index()
        return True

    def get_history(self, version_id: str) -> List[ParameterVersion]:
        """获取版本历史链"""
        history = []
        current = self.load(version_id)
        while current:
            history.append(current)
            if current.parent_version:
                current = self.load(current.parent_version)
            else:
                break
        return history

    def cleanup_old_versions(self, project: str, keep: int = 10) -> int:
        """清理旧版本"""
        versions = self.list_versions(project)
        if len(versions) <= keep:
            return 0

        to_delete = versions[keep:]
        count = 0
        for version in to_delete:
            if self.delete(version.version_id):
                count += 1
        return count

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        return {
            "total_versions": len(self._index["versions"]),
            "projects": list(self._index["by_project"].keys()),
            "versions_by_project": {p: len(ids) for p, ids in self._index["by_project"].items()},
            "storage_path": str(self.base_path),
        }


# 默认存储实例
_default_store: Optional[FileSystemParameterStore] = None


def get_default_store() -> FileSystemParameterStore:
    """获取默认存储实例"""
    global _default_store
    if _default_store is None:
        _default_store = FileSystemParameterStore()
    return _default_store


def save_params(
    params: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None, project: str = "default", parent: Optional[str] = None
) -> ParameterVersion:
    """便捷函数：保存参数"""
    return get_default_store().save(params, metadata, project, parent)


def load_params(version_id: str) -> Optional[ParameterVersion]:
    """便捷函数：加载参数"""
    return get_default_store().load(version_id)


def get_latest_params(project: str = "default") -> Optional[ParameterVersion]:
    """便捷函数：获取最新参数"""
    return get_default_store().get_latest(project)


# 别名，保持向后兼容
ParameterStorage = FileSystemParameterStore
