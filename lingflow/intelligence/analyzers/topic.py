"""话题分析器

提取讨论中的热门话题并进行聚类。
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional

from .base import BaseAnalyzer, AnalyzerConfig
from ..models.common import MentionData
from ..logging_config import get_logger

logger = get_logger(__name__)


STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "must", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out", "off",
    "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "each", "every", "both", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "just", "because", "but",
    "and", "or", "if", "while", "about", "up", "it", "its", "this", "that",
    "these", "those", "i", "me", "my", "we", "our", "you", "your", "he",
    "him", "his", "she", "her", "they", "them", "their", "what", "which",
    "who", "whom",
})

TECH_KEYWORDS = frozenset({
    "python", "javascript", "typescript", "rust", "golang", "java",
    "react", "vue", "angular", "nextjs", "svelte",
    "docker", "kubernetes", "aws", "gcp", "azure",
    "api", "rest", "graphql", "grpc", "websocket",
    "database", "sql", "nosql", "redis", "postgresql",
    "machine", "learning", "deep", "neural", "transformer",
    "llm", "gpt", "claude", "model", "ai", "agent",
    "mcp", "tool", "framework", "library", "sdk",
    "workflow", "pipeline", "automation", "cicd", "devops",
    "testing", "pytest", "unittest", "integration",
    "cli", "terminal", "shell", "bash",
    "open", "source", "github", "git", "repository",
})


class TopicAnalyzer(BaseAnalyzer):
    """话题分析器

    从讨论中提取热门话题，进行关键词聚类。
    """

    NAME = "topic"
    DESCRIPTION = "话题分析器"

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        super().__init__(config)

    def analyze(self, mentions: List[MentionData], **kwargs) -> Dict[str, Any]:
        if not mentions:
            return {"total": 0, "topics": [], "clusters": []}

        topics = self.extract_topics(mentions)
        clusters = self.cluster_discussions(mentions)

        return {
            "total": len(mentions),
            "topics": topics,
            "clusters": [c.to_dict() if hasattr(c, "to_dict") else c for c in clusters],
        }

    def extract_topics(self, mentions: List[MentionData], top_n: int = 20) -> List[Dict[str, Any]]:
        """提取热门话题关键词

        Args:
            mentions: 提及数据列表
            top_n: 返回前N个话题

        Returns:
            话题列表，每个包含关键词、频次、来源数
        """
        keyword_sources: Dict[str, set] = {}
        keyword_count: Counter = Counter()

        for m in mentions:
            text = f"{m.title or ''} {m.content or ''}".lower()
            words = self._tokenize(text)
            unique_words = set(words)

            for word in unique_words:
                keyword_sources.setdefault(word, set()).add(m.source_id)
                keyword_count[word] += 1

        topics = []
        for keyword, count in keyword_count.most_common(top_n * 2):
            if keyword in STOP_WORDS or len(keyword) < 3:
                continue
            source_count = len(keyword_sources.get(keyword, set()))
            topics.append({
                "keyword": keyword,
                "count": count,
                "source_count": source_count,
                "is_tech": keyword in TECH_KEYWORDS,
            })
            if len(topics) >= top_n:
                break

        return topics

    def cluster_discussions(self, mentions: List[MentionData], max_clusters: int = 10) -> List[Dict[str, Any]]:
        """基于关键词共现将讨论聚类

        Args:
            mentions: 提及数据列表
            max_clusters: 最大聚类数

        Returns:
            聚类列表
        """
        mention_keywords: Dict[str, set] = {}
        for m in mentions:
            text = f"{m.title or ''} {m.content or ''}".lower()
            words = set(self._tokenize(text))
            words -= STOP_WORDS
            words = {w for w in words if len(w) >= 3}
            mention_keywords[m.source_id] = words

        keyword_to_mentions: Dict[str, List[str]] = {}
        for mid, keywords in mention_keywords.items():
            for kw in keywords:
                keyword_to_mentions.setdefault(kw, []).append(mid)

        candidate_keywords = sorted(
            keyword_to_mentions.keys(),
            key=lambda k: len(keyword_to_mentions[k]),
            reverse=True,
        )

        clusters: List[Dict[str, Any]] = []
        used_mentions: set = set()

        for keyword in candidate_keywords:
            if len(clusters) >= max_clusters:
                break

            mention_ids = set(keyword_to_mentions[keyword])
            new_mentions = mention_ids - used_mentions
            if len(new_mentions) < 2:
                continue

            all_keywords: Counter = Counter()
            for mid in new_mentions:
                all_keywords.update(mention_keywords.get(mid, set()))

            top_keywords = [kw for kw, _ in all_keywords.most_common(5) if kw != keyword]

            clusters.append({
                "name": keyword,
                "mention_count": len(new_mentions),
                "top_keywords": top_keywords[:4],
                "sample_ids": list(new_mentions)[:5],
            })
            used_mentions.update(new_mentions)

        return clusters

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        words = re.findall(r'[a-z]{2,}', text.lower())
        return words
