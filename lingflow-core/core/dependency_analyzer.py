"""
LingFlow Message Dependency Analyzer - 消息依赖分析器

分析消息之间的依赖关系，用于智能压缩
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class DependencyGraph:
    """依赖图"""
    nodes: Set[int]  # 消息索引
    edges: Set[Tuple[int, int]]  # (依赖者, 被依赖者)
    strongly_connected: List[Set[int]]  # 强连通分量


class DependencyAnalyzer:
    """消息依赖分析器"""

    def __init__(self):
        self.logger = logger

    def analyze_dependencies(self, messages: List[Dict]) -> DependencyGraph:
        """
        分析消息依赖关系

        Args:
            messages: 消息列表

        Returns:
            依赖图
        """
        if not messages:
            return DependencyGraph(nodes=set(), edges=set(), strongly_connected=[])

        # 构建依赖图
        nodes = set(range(len(messages)))
        edges = set()

        # 分析引用依赖
        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            role = msg.get("role", "")

            # 检查对前面消息的引用
            referenced = self._find_references(content, messages[:i])
            for ref_idx in referenced:
                edges.add((i, ref_idx))  # i 依赖 ref_idx

            # 检查代码块依赖
            if self._contains_code_block(content):
                # 代码块通常依赖上下文
                for j in range(max(0, i-3), i):
                    if messages[j].get("role") == "user":
                        edges.add((i, j))

        # 查找强连通分量（紧密相关的消息组）
        strongly_connected = self._find_strongly_connected(nodes, edges)

        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            strongly_connected=strongly_connected
        )

    def _find_references(self, content: str, previous_messages: List[Dict]) -> List[int]:
        """
        查找对前面消息的引用

        Args:
            content: 当前消息内容
            previous_messages: 之前的消息

        Returns:
            被引用的消息索引列表
        """
        references = []

        # 提取当前消息中的关键词
        current_keywords = set(self._extract_keywords(content))

        if not current_keywords:
            return references

        # 检查每条之前的消息
        for j, prev_msg in enumerate(previous_messages):
            prev_content = prev_msg.get("content", "")
            prev_keywords = set(self._extract_keywords(prev_content))

            # 计算关键词重叠
            overlap = current_keywords & prev_keywords

            if overlap:
                # 如果重叠度足够高，认为有引用关系
                overlap_ratio = len(overlap) / len(current_keywords)
                if overlap_ratio > 0.3:  # 30% 重叠
                    references.append(j)

        return references

    def _contains_code_block(self, content: str) -> bool:
        """检查是否包含代码块"""
        return bool(re.search(r'```[\s\S]*?```', content))

    def _extract_keywords(self, content: str) -> List[str]:
        """
        提取关键词

        Args:
            content: 文本内容

        Returns:
            关键词列表
        """
        # 移除代码块
        content = re.sub(r'```[\s\S]*?```', '', content)

        # 提取词语（简单实现）
        words = re.findall(r'\b\w{4,}\b', content.lower())

        # 过滤常见词
        stopwords = {
            'this', 'that', 'with', 'from', 'have', 'more', 'will',
            'your', 'about', 'would', 'there', 'their', 'what',
            'when', 'make', 'like', 'just', 'into', 'over', 'such'
        }

        return [w for w in words if w not in stopwords]

    def _find_strongly_connected(
        self,
        nodes: Set[int],
        edges: Set[Tuple[int, int]]
    ) -> List[Set[int]]:
        """
        查找强连通分量（Tarjan 算法）

        Args:
            nodes: 节点集合
            edges: 边集合

        Returns:
            强连通分量列表
        """
        if not nodes:
            return []

        # 构建邻接表
        graph = defaultdict(list)
        reverse_graph = defaultdict(list)

        for u, v in edges:
            graph[u].append(v)
            reverse_graph[v].append(u)

        # Tarjan 算法
        index = 0
        stack = []
        indices = {}
        lowlinks = {}
        onstack = set()
        strongly_connected = []

        def strongconnect(v):
            nonlocal index
            indices[v] = index
            lowlinks[v] = index
            index += 1
            stack.append(v)
            onstack.add(v)

            for w in graph[v]:
                if w not in indices:
                    strongconnect(w)
                    lowlinks[v] = min(lowlinks[v], lowlinks[w])
                elif w in onstack:
                    lowlinks[v] = min(lowlinks[v], indices[w])

            if lowlinks[v] == indices[v]:
                # 开始新的强连通分量
                scc = set()
                while True:
                    w = stack.pop()
                    onstack.remove(w)
                    scc.add(w)
                    if w == v:
                        break
                if len(scc) > 1:  # 只保留多节点的 SCC
                    strongly_connected.append(scc)

        for v in nodes:
            if v not in indices:
                strongconnect(v)

        return strongly_connected

    def get_critical_messages(
        self,
        messages: List[Dict],
        dependency_graph: Optional[DependencyGraph] = None
    ) -> Set[int]:
        """
        获取关键消息（不应被删除的消息）

        Args:
            messages: 消息列表
            dependency_graph: 依赖图

        Returns:
            关键消息索引集合
        """
        if dependency_graph is None:
            dependency_graph = self.analyze_dependencies(messages)

        critical = set()

        # 1. 系统消息通常是关键的
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                critical.add(i)

        # 2. 在强连通分量中的消息
        for scc in dependency_graph.strongly_connected:
            # 只要有2个消息以上的 SCC 都是关键的
            if len(scc) >= 2:
                critical.update(scc)

        # 3. 被多次引用的消息
        reference_count = defaultdict(int)
        for u, v in dependency_graph.edges:
            reference_count[v] += 1

        # 被引用超过2次的消息是关键的
        for msg_idx, count in reference_count.items():
            if count >= 2:
                critical.add(msg_idx)

        # 4. 用户的第一条和最后一条消息
        for i, msg in enumerate(messages):
            if msg.get("role") == "user":
                if i == 0 or i == len(messages) - 1:
                    critical.add(i)
                    break

        return critical

    def suggest_compression_groups(
        self,
        messages: List[Dict]
    ) -> List[Dict[str, any]]:
        """
        建议压缩分组

        Args:
            messages: 消息列表

        Returns:
            分组建议
        """
        dependency_graph = self.analyze_dependencies(messages)
        critical = self.get_critical_messages(messages, dependency_graph)

        groups = []

        # 关键组（必须保留）
        critical_group = {
            "type": "critical",
            "indices": sorted(list(critical)),
            "reason": "Critical dependencies and references",
            "removable": False
        }
        groups.append(critical_group)

        # 非关键组（可以考虑删除）
        non_critical = set(range(len(messages))) - critical
        if non_critical:
            non_critical_group = {
                "type": "removable",
                "indices": sorted(list(non_critical)),
                "reason": "Low importance, no critical dependencies",
                "removable": True
            }
            groups.append(non_critical_group)

        return groups

    def calculate_removal_impact(
        self,
        messages: List[Dict],
        remove_indices: Set[int]
    ) -> Dict[str, any]:
        """
        计算删除指定消息的影响

        Args:
            messages: 消息列表
            remove_indices: 要删除的消息索引

        Returns:
            影响分析结果
        """
        dependency_graph = self.analyze_dependencies(messages)

        # 计算会被影响的消息
        affected = set()

        for msg_idx in remove_indices:
            # 找出依赖这个消息的其他消息
            for u, v in dependency_graph.edges:
                if v == msg_idx:
                    affected.add(u)

        # 检查是否会破坏强连通分量
        broken_scc = []
        for scc in dependency_graph.strongly_connected:
            if any(idx in remove_indices for idx in scc):
                broken_scc.append(scc)

        return {
            "affected_messages": len(affected),
            "affected_indices": sorted(list(affected)),
            "broken_dependencies": len(broken_scc),
            "safe_to_remove": len(affected) == 0 and len(broken_scc) == 0,
            "impact_score": len(affected) * 1.0 + len(broken_scc) * 2.0
        }
