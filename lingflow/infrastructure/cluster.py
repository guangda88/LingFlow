"""集群基础设施注册表

从 config/cluster.yaml 加载集群节点信息，提供查询接口。
所有硬件/网络/服务引用必须通过此模块，禁止硬编码或猜测。

设计动机: 2026-04-11 错误复盘发现，AI 因缺乏基础设施知识库而虚构了
节点名称(GPU型号、节点数量、服务状态等)，违反数据真实性原则。
此模块是"让不知道变成不可能"的代码修复。

Usage:
    >>> from lingflow.infrastructure import ClusterRegistry
    >>> registry = ClusterRegistry()
    >>> node = registry.get_node("zhineng-ai01")
    >>> node.gpu_model
    'NVIDIA GTX 1070'
    >>> node.gpu_vram_gb
    8
    >>> registry.find_nodes(gpu_vram_gte=8)
    [ClusterNode(name='zhineng-ai01', ...)]
"""

import yaml
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from lingflow.core.types import Result


class NodeRole(Enum):
    PRIMARY_COMPUTE = "primary_compute"
    DISTRIBUTED_COMPUTE = "distributed_compute"
    STORAGE_GATEWAY = "storage_gateway"
    DATABASE_SERVER = "database_server"
    WORKSTATION = "workstation"


class NodeStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


@dataclass
class ClusterNode:
    """集群节点

    Attributes:
        name: 节点主机名
        role: 节点角色
        model: 硬件型号
        status: 当前状态
        ips: 各网络接口的 IP 地址
        cpu: CPU 型号
        gpu_model: GPU 型号（无 GPU 则为 None）
        gpu_vram_gb: GPU 显存（GB，无 GPU 则为 0）
        ram_gb: 内存（GB）
        storage: 存储描述
        services: 运行中的服务列表
        notes: 备注
    """

    name: str
    role: NodeRole
    model: str
    status: NodeStatus
    ips: Dict[str, str] = field(default_factory=dict)
    cpu: str = "unknown"
    gpu_model: Optional[str] = None
    gpu_vram_gb: int = 0
    ram_gb: int = 0
    storage: str = ""
    services: List[str] = field(default_factory=list)
    notes: str = ""

    @property
    def has_gpu(self) -> bool:
        return self.gpu_model is not None and self.gpu_vram_gb > 0

    @property
    def primary_ip(self) -> Optional[str]:
        return self.ips.get("lan")

    def can_train_model_vram(self, required_vram_gb: int) -> bool:
        return self.gpu_vram_gb >= required_vram_gb

    def __repr__(self) -> str:
        gpu_info = f", gpu={self.gpu_model} {self.gpu_vram_gb}GB" if self.has_gpu else ""
        return f"ClusterNode(name='{self.name}', role={self.role.value}, ram={self.ram_gb}GB{gpu_info})"


_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "cluster.yaml"


class ClusterRegistry:
    """集群基础设施注册表

    从 YAML 配置文件加载集群信息，提供查询接口。
    单例模式，全局共享同一实例。

    Example:
        >>> registry = ClusterRegistry()
        >>> registry.get_node("zhineng-ai")
        ClusterNode(name='zhineng-ai', ...)
        >>> registry.get_gpu_nodes()
        [ClusterNode(name='zhineng-ai', ...), ClusterNode(name='zhineng-ai01', ...)]
        >>> registry.find_nodes(gpu_vram_gte=8)
        [ClusterNode(name='zhineng-ai01', ...)]
    """

    _instance: Optional["ClusterRegistry"] = None
    _nodes: Dict[str, ClusterNode] = field(default_factory=dict)
    _cluster_meta: Dict = field(default_factory=dict)

    def __new__(cls, config_path: Optional[Path] = None) -> "ClusterRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[Path] = None) -> None:
        if self._initialized:
            return
        path = config_path or _DEFAULT_CONFIG_PATH
        self._nodes: Dict[str, ClusterNode] = {}
        self._cluster_meta: Dict = {}
        self._load(path)
        self._initialized = True

    def _load(self, config_path: Path) -> None:
        if not config_path.exists():
            raise FileNotFoundError(f"集群配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"集群配置文件为空: {config_path}")

        self._cluster_meta = data.get("cluster", {})

        for node_data in data.get("nodes", []):
            node = self._parse_node(node_data)
            self._nodes[node.name] = node

    @staticmethod
    def _parse_node(data: Dict) -> ClusterNode:
        gpu = data.get("gpu", {})
        return ClusterNode(
            name=data["name"],
            role=NodeRole(data.get("role", "workstation")),
            model=data.get("model", "unknown"),
            status=NodeStatus(data.get("status", "unknown")),
            ips=data.get("ips", {}),
            cpu=data.get("cpu", "unknown"),
            gpu_model=gpu.get("model"),
            gpu_vram_gb=gpu.get("vram_gb", 0),
            ram_gb=data.get("ram_gb", 0),
            storage=data.get("storage", ""),
            services=data.get("services", []),
            notes=data.get("notes", ""),
        )

    def get_node(self, name: str) -> Optional[ClusterNode]:
        return self._nodes.get(name)

    def get_node_or_fail(self, name: str) -> Result[ClusterNode]:
        node = self._nodes.get(name)
        if node is None:
            known = ", ".join(sorted(self._nodes.keys()))
            return Result.fail(
                f"节点 '{name}' 不在注册表中。已知节点: {known}",
                code="NODE_NOT_FOUND",
            )
        return Result.ok(node)

    def get_all_nodes(self) -> List[ClusterNode]:
        return list(self._nodes.values())

    def get_gpu_nodes(self) -> List[ClusterNode]:
        return [n for n in self._nodes.values() if n.has_gpu]

    def find_nodes(
        self,
        gpu_vram_gte: Optional[int] = None,
        ram_gte: Optional[int] = None,
        role: Optional[NodeRole] = None,
        status: Optional[NodeStatus] = None,
        has_service: Optional[str] = None,
    ) -> List[ClusterNode]:
        results = self.get_all_nodes()
        if gpu_vram_gte is not None:
            results = [n for n in results if n.gpu_vram_gb >= gpu_vram_gte]
        if ram_gte is not None:
            results = [n for n in results if n.ram_gb >= ram_gte]
        if role is not None:
            results = [n for n in results if n.role == role]
        if status is not None:
            results = [n for n in results if n.status == status]
        if has_service is not None:
            results = [n for n in results if has_service in n.services]
        return results

    def get_cluster_name(self) -> str:
        return self._cluster_meta.get("name", "")

    def get_network_segments(self) -> List[Dict]:
        return self._cluster_meta.get("network_segments", [])

    def validate_claim(self, claim: str) -> Result[str]:
        """验证关于集群的陈述是否与注册表一致

        Args:
            claim: 待验证的陈述，如 "zhineng-ai01 有 2×8GB GPU"

        Returns:
            Result.ok(verified_description) 或 Result.fail(reason)
        """
        import re

        node_pattern = r"(zhineng-\w+|Zhineng\w+|PC-\w+)"
        vram_pattern = r"(\d+)\s*[×xX]\s*(\d+)\s*GB"
        gpu_count_pattern = r"(\d+)\s*[×xX]\s*(GTX|RTX|GPU)"

        nodes_mentioned = re.findall(node_pattern, claim, re.IGNORECASE)
        for node_name in nodes_mentioned:
            normalized = node_name.lower()
            if normalized not in {n.lower() for n in self._nodes}:
                return Result.fail(
                    f"节点 '{node_name}' 不存在。已知节点: {', '.join(sorted(self._nodes.keys()))}",
                    code="CLAIM_NODE_NOT_FOUND",
                )

        vram_matches = re.findall(vram_pattern, claim)
        for count_str, size_str in vram_matches:
            return Result.fail(
                f"声称有 {count_str}×{size_str}GB GPU，但集群中没有任何多 GPU 节点。"
                f"请使用 ClusterRegistry 查询确切 GPU 配置。",
                code="CLAIM_MULTI_GPU_SUSPECT",
            )

        gpu_count_matches = re.findall(gpu_count_pattern, claim, re.IGNORECASE)
        for count_str, _ in gpu_count_matches:
            count = int(count_str)
            if count > 1:
                return Result.fail(
                    f"声称有 {count} 个 GPU，但集群中没有任何多 GPU 节点。",
                    code="CLAIM_MULTI_GPU_SUSPECT",
                )

        return Result.ok("验证通过，未发现明显矛盾")

    def summary(self) -> str:
        lines = [f"集群: {self.get_cluster_name()}", ""]
        for node in self.get_all_nodes():
            gpu = f" | GPU: {node.gpu_model} {node.gpu_vram_gb}GB" if node.has_gpu else ""
            services = f" | 服务: {', '.join(node.services)}" if node.services else ""
            lines.append(
                f"  {node.name} ({node.role.value}) | {node.model} | RAM: {node.ram_gb}GB{gpu}{services}"
            )
        return "\n".join(lines)

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
