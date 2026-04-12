"""研究写作前的事实验证流程

在撰写研究报告、技术文档前，自动验证文中涉及的硬件/基础设施陈述。
解决 2026-04-11 错误复盘中发现的"未验证就输出"问题。

Usage:
    >>> from lingflow.trust.fact_checker import FactChecker, FactCheckResult
    >>> checker = FactChecker()
    >>> result = checker.check("zhineng-ai01 有 2×8GB GPU")
    >>> result.passed
    False
    >>> result.issues[0].description
    "节点 'zhineng-ai01' 有 1 个 GPU (NVIDIA GTX 1070 8GB)，不是 2×8GB"
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class FactStatus(Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONTRADICTED = "contradicted"


class IssueSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class FactIssue:
    description: str
    severity: IssueSeverity
    fact: str
    evidence: str = ""


@dataclass
class FactCheckResult:
    original_text: str
    passed: bool
    status: FactStatus
    issues: List[FactIssue] = field(default_factory=list)
    verified_claims: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.passed:
            return f"✓ 事实验证通过 ({len(self.verified_claims)} 项已验证)"
        lines = [f"✗ 事实验证失败 ({len(self.issues)} 个问题):"]
        for issue in self.issues:
            icon = "✗" if issue.severity == IssueSeverity.ERROR else "⚠" if issue.severity == IssueSeverity.WARNING else "ℹ"
            lines.append(f"  {icon} {issue.description}")
        if self.verified_claims:
            lines.append(f"  已验证: {', '.join(self.verified_claims)}")
        return "\n".join(lines)


_NODE_PATTERN = re.compile(
    r"(zhineng-ai0?\d*|ZhinengNAS|ZhinengServer|PC-RIZC)",
    re.IGNORECASE,
)
_MULTI_GPU_PATTERN = re.compile(r"(\d+)\s*[×xX]\s*(\d+)\s*GB\s*(?:GPU|显存)", re.IGNORECASE)
_GPU_MODEL_PATTERN = re.compile(
    r"(GTX\s*\d{3,4}\s*(?:Ti|SUPER)?|RTX\s*\d{3,4}\s*(?:Ti|SUPER)?|A\d{2,4})",
    re.IGNORECASE,
)
_VRAM_PATTERN = re.compile(r"(\d+)\s*GB\s*(?:显存|VRAM|GPU)", re.IGNORECASE)
_RAM_PATTERN = re.compile(r"(\d+)\s*GB\s*(?:RAM|内存|ECC)", re.IGNORECASE)
_STATUS_PATTERN = re.compile(r"(闲置|未使用|inactive|idle)", re.IGNORECASE)


def _try_import_registry():
    try:
        from lingflow.infrastructure.cluster import ClusterRegistry
        return ClusterRegistry()
    except Exception:
        return None


class FactChecker:
    """事实验证器

    检查文本中关于集群基础设施的陈述是否与注册表一致。
    """

    def __init__(self, registry=None) -> None:
        if registry is not None:
            self._registry = registry
        else:
            self._registry = _try_import_registry()

    def check(self, text: str) -> FactCheckResult:
        issues: List[FactIssue] = []
        verified: List[str] = []

        if self._registry is None:
            return FactCheckResult(
                original_text=text,
                passed=True,
                status=FactStatus.UNVERIFIED,
                issues=[FactIssue(
                    description="集群注册表不可用，无法验证基础设施陈述",
                    severity=IssueSeverity.WARNING,
                    fact=text,
                    evidence="ClusterRegistry 加载失败",
                )],
            )

        issues.extend(self._check_node_names(text))
        issues.extend(self._check_multi_gpu(text))
        issues.extend(self._check_gpu_models(text))
        issues.extend(self._check_status_claims(text))

        has_errors = any(i.severity == IssueSeverity.ERROR for i in issues)
        has_warnings = any(i.severity == IssueSeverity.WARNING for i in issues)

        if has_errors:
            status = FactStatus.CONTRADICTED
            passed = False
        elif has_warnings:
            status = FactStatus.UNVERIFIED
            passed = True
        else:
            status = FactStatus.VERIFIED
            passed = True
            verified.append("未发现基础设施矛盾")

        return FactCheckResult(
            original_text=text,
            passed=passed,
            status=status,
            issues=issues,
            verified_claims=verified,
        )

    def _check_node_names(self, text: str) -> List[FactIssue]:
        issues: List[FactIssue] = []
        matches = _NODE_PATTERN.findall(text)
        for match in matches:
            result = self._registry.get_node_or_fail(match)
            if result.is_error:
                issues.append(FactIssue(
                    description=result.error,
                    severity=IssueSeverity.ERROR,
                    fact=match,
                    evidence=f"已知节点: {', '.join(n.name for n in self._registry.get_all_nodes())}",
                ))
        return issues

    def _check_multi_gpu(self, text: str) -> List[FactIssue]:
        issues: List[FactIssue] = []
        matches = _MULTI_GPU_PATTERN.findall(text)
        for count_str, size_str in matches:
            count = int(count_str)
            size = int(size_str)
            node_matches = _NODE_PATTERN.findall(text)
            target_node = node_matches[0] if node_matches else None
            if target_node:
                node = self._registry.get_node(target_node)
                if node and node.gpu_vram_gb == size and count > 1:
                    issues.append(FactIssue(
                        description=f"节点 '{target_node}' 有 1 个 GPU ({node.gpu_model} {node.gpu_vram_gb}GB)，不是 {count}×{size}GB",
                        severity=IssueSeverity.ERROR,
                        fact=f"{count}×{size}GB GPU",
                        evidence=f"注册表: {node.gpu_model} {node.gpu_vram_gb}GB (单卡)",
                    ))
        return issues

    def _check_gpu_models(self, text: str) -> List[FactIssue]:
        issues: List[FactIssue] = []
        gpu_matches = _GPU_MODEL_PATTERN.findall(text)
        node_matches = _NODE_PATTERN.findall(text)
        if gpu_matches and node_matches:
            claimed_gpu = gpu_matches[0].strip()
            node = self._registry.get_node(node_matches[0])
            if node and node.gpu_model:
                actual_gpu = node.gpu_model
                claimed_normalized = re.sub(r"\s+", " ", claimed_gpu.upper())
                actual_normalized = re.sub(r"\s+", " ", actual_gpu.upper())
                if claimed_normalized not in actual_normalized and actual_normalized not in claimed_normalized:
                    issues.append(FactIssue(
                        description=f"节点 '{node.name}' 的 GPU 是 {actual_gpu}，不是 {claimed_gpu}",
                        severity=IssueSeverity.ERROR,
                        fact=claimed_gpu,
                        evidence=f"注册表: {actual_gpu}",
                    ))
        return issues

    def _check_status_claims(self, text: str) -> List[FactIssue]:
        issues: List[FactIssue] = []
        status_matches = _STATUS_PATTERN.findall(text)
        node_matches = _NODE_PATTERN.findall(text)
        if status_matches and node_matches:
            node = self._registry.get_node(node_matches[0])
            if node and node.status.value == "active":
                issues.append(FactIssue(
                    description=f"节点 '{node.name}' 状态为 active（运行中），不是闲置。运行服务: {', '.join(node.services) or '无'}",
                    severity=IssueSeverity.ERROR,
                    fact="闲置",
                    evidence=f"注册表: status=active, services={node.services}",
                ))
        return issues
