"""ClusterRegistry 测试

验证集群基础设施注册表的加载、查询、验证功能。
"""

import tempfile
from pathlib import Path

import pytest

from lingflow.infrastructure.cluster import ClusterNode, ClusterRegistry, NodeRole, NodeStatus


@pytest.fixture(autouse=True)
def reset_singleton():
    ClusterRegistry.reset()
    yield
    ClusterRegistry.reset()


MINIMAL_YAML = """
cluster:
  name: 测试集群
  network_segments: []
nodes:
  - name: test-node-1
    role: primary_compute
    model: TestBox
    status: active
    ips:
      lan: 192.168.1.1
    cpu: TestCPU
    gpu:
      model: TestGPU
      vram_gb: 8
    ram_gb: 32
    storage: local
    services:
      - test-service
    notes: test
  - name: test-node-2
    role: workstation
    model: TestBox2
    status: active
    ips:
      lan: 192.168.1.2
    cpu: TestCPU2
    gpu:
      model: null
      vram_gb: 0
    ram_gb: 16
    storage: local
    services: []
    notes: ""
"""

FULL_YAML = """
cluster:
  name: 灵族集群
  network_segments:
    - name: LAN
      cidr: 192.168.31.0/24
nodes:
  - name: zhineng-ai
    role: primary_compute
    model: ZBOX-EN51660T
    status: active
    ips:
      lan: 192.168.31.99
      zerotier: 10.113.22.99
    cpu: unknown
    gpu:
      model: NVIDIA GTX 1660 Ti
      vram_gb: 6
    ram_gb: 32
    storage: local
    services:
      - Prometheus
      - Grafana
    notes: ""
  - name: zhineng-ai01
    role: distributed_compute
    model: ZBOX-EN1070-K
    status: active
    ips:
      lan: 192.168.31.208
      zerotier: 10.113.22.208
    cpu: unknown
    gpu:
      model: NVIDIA GTX 1070
      vram_gb: 8
    ram_gb: 32
    storage: local
    services:
      - PyTorch DDP
      - Ray
    notes: ""
  - name: ZhinengServer
    role: database_server
    model: DELL R730
    status: active
    ips:
      lan: 192.168.31.90
    cpu: Intel Xeon
    gpu:
      model: null
      vram_gb: 0
    ram_gb: 64
    storage: ECC
    services:
      - Gitea
    notes: ""
"""


def _write_yaml(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return Path(f.name)


class TestClusterNode:
    def test_has_gpu_true(self):
        node = ClusterNode(
            name="test", role=NodeRole.PRIMARY_COMPUTE, model="x", status=NodeStatus.ACTIVE,
            gpu_model="GTX 1070", gpu_vram_gb=8,
        )
        assert node.has_gpu is True

    def test_has_gpu_false_no_model(self):
        node = ClusterNode(
            name="test", role=NodeRole.WORKSTATION, model="x", status=NodeStatus.ACTIVE,
            gpu_model=None, gpu_vram_gb=0,
        )
        assert node.has_gpu is False

    def test_primary_ip(self):
        node = ClusterNode(
            name="test", role=NodeRole.WORKSTATION, model="x", status=NodeStatus.ACTIVE,
            ips={"lan": "192.168.1.1", "zerotier": "10.0.0.1"},
        )
        assert node.primary_ip == "192.168.1.1"

    def test_primary_ip_none(self):
        node = ClusterNode(
            name="test", role=NodeRole.WORKSTATION, model="x", status=NodeStatus.ACTIVE,
            ips={},
        )
        assert node.primary_ip is None

    def test_can_train_model_vram(self):
        node = ClusterNode(
            name="test", role=NodeRole.PRIMARY_COMPUTE, model="x", status=NodeStatus.ACTIVE,
            gpu_model="GTX 1070", gpu_vram_gb=8,
        )
        assert node.can_train_model_vram(8) is True
        assert node.can_train_model_vram(6) is True
        assert node.can_train_model_vram(10) is False


class TestClusterRegistryLoading:
    def test_load_minimal(self):
        path = _write_yaml(MINIMAL_YAML)
        registry = ClusterRegistry(config_path=path)
        assert len(registry.get_all_nodes()) == 2
        assert registry.get_cluster_name() == "测试集群"

    def test_load_full(self):
        path = _write_yaml(FULL_YAML)
        registry = ClusterRegistry(config_path=path)
        assert len(registry.get_all_nodes()) == 3
        assert registry.get_cluster_name() == "灵族集群"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            ClusterRegistry(config_path=Path("/nonexistent/cluster.yaml"))

    def test_empty_file(self):
        path = _write_yaml("")
        with pytest.raises(ValueError, match="为空"):
            ClusterRegistry(config_path=path)

    def test_singleton(self):
        path = _write_yaml(MINIMAL_YAML)
        r1 = ClusterRegistry(config_path=path)
        r2 = ClusterRegistry()
        assert r1 is r2


class TestClusterRegistryQuery:
    @pytest.fixture
    def registry(self):
        path = _write_yaml(FULL_YAML)
        return ClusterRegistry(config_path=path)

    def test_get_node_exists(self, registry):
        node = registry.get_node("zhineng-ai")
        assert node is not None
        assert node.gpu_vram_gb == 6

    def test_get_node_not_exists(self, registry):
        assert registry.get_node("zhineng-ai02") is None

    def test_get_node_or_fail(self, registry):
        result = registry.get_node_or_fail("zhineng-ai01")
        assert result.is_ok
        assert result.data.gpu_model == "NVIDIA GTX 1070"

    def test_get_node_or_fail_not_found(self, registry):
        result = registry.get_node_or_fail("zhineng-ai02")
        assert result.is_error
        assert "NODE_NOT_FOUND" == result.code

    def test_get_gpu_nodes(self, registry):
        gpus = registry.get_gpu_nodes()
        assert len(gpus) == 2
        names = {n.name for n in gpus}
        assert names == {"zhineng-ai", "zhineng-ai01"}

    def test_find_nodes_vram_gte_8(self, registry):
        nodes = registry.find_nodes(gpu_vram_gte=8)
        assert len(nodes) == 1
        assert nodes[0].name == "zhineng-ai01"

    def test_find_nodes_ram_gte_64(self, registry):
        nodes = registry.find_nodes(ram_gte=64)
        assert len(nodes) == 1
        assert nodes[0].name == "ZhinengServer"

    def test_find_nodes_by_role(self, registry):
        nodes = registry.find_nodes(role=NodeRole.DATABASE_SERVER)
        assert len(nodes) == 1
        assert nodes[0].name == "ZhinengServer"

    def test_find_nodes_by_service(self, registry):
        nodes = registry.find_nodes(has_service="Ray")
        assert len(nodes) == 1
        assert nodes[0].name == "zhineng-ai01"

    def test_find_nodes_combined(self, registry):
        nodes = registry.find_nodes(gpu_vram_gte=6, ram_gte=32)
        assert len(nodes) == 2

    def test_get_network_segments(self, registry):
        segments = registry.get_network_segments()
        assert len(segments) == 1
        assert segments[0]["cidr"] == "192.168.31.0/24"


class TestClusterRegistryValidateClaim:
    @pytest.fixture
    def registry(self):
        path = _write_yaml(FULL_YAML)
        return ClusterRegistry(config_path=path)

    def test_validate_valid_claim(self, registry):
        result = registry.validate_claim("zhineng-ai01 有 GTX 1070")
        assert result.is_ok

    def test_validate_nonexistent_node(self, registry):
        result = registry.validate_claim("zhineng-ai02 有 16GB GPU")
        assert result.is_error
        assert "不存在" in result.error

    def test_validate_multi_gpu_claim(self, registry):
        result = registry.validate_claim("zhineng-ai01 有 2×8GB GPU")
        assert result.is_error
        assert "多 GPU" in result.error

    def test_validate_neutral_claim(self, registry):
        result = registry.validate_claim("集群有5台机器")
        assert result.is_ok


class TestClusterRegistrySummary:
    def test_summary_contains_all_nodes(self):
        path = _write_yaml(FULL_YAML)
        registry = ClusterRegistry(config_path=path)
        s = registry.summary()
        assert "zhineng-ai" in s
        assert "zhineng-ai01" in s
        assert "ZhinengServer" in s
        assert "GTX 1070" in s
        assert "灵族集群" in s
