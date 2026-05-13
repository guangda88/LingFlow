"""情感分析器 - 分析关于lingflow的讨论情感

使用简单规则基线，可扩展为ML模型。
"""

import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SentimentResult:
    """情感分析结果"""

    text: str
    score: float  # -1 到 1
    label: str  # positive, neutral, negative
    confidence: float  # 0 到 1
    key_words: List[str]  # 关键词


class SentimentAnalyzer:
    """情感分析器

    使用基于规则的方法分析文本情感倾向。
    """

    # 正面词汇 (lingflow/工具相关)
    POSITIVE_WORDS = [
        # 强正面
        "awesome",
        "amazing",
        "excellent",
        "fantastic",
        "incredible",
        "outstanding",
        "useful",
        "helpful",
        "powerful",
        "great",
        "good",
        "nice",
        "cool",
        "love",
        "favorite",
        "recommend",
        "impressive",
        "solid",
        "robust",
        # 技术正面
        "well-designed",
        "intuitive",
        "clean",
        "efficient",
        "fast",
        "performant",
        "innovative",
        "cutting-edge",
        "state-of-the-art",
        "breakthrough",
        # 中文正面
        "好用",
        "强大",
        "优秀",
        "太棒了",
        "赞",
        "推荐",
        "喜欢",
    ]

    # 负面词汇
    NEGATIVE_WORDS = [
        # 强负面
        "bad",
        "terrible",
        "awful",
        "horrible",
        "poor",
        "useless",
        "broken",
        "slow",
        "buggy",
        "unreliable",
        "disappointing",
        "frustrating",
        "confusing",
        "complex",
        "difficult",
        "complicated",
        # 技术负面
        "crash",
        "error",
        "fail",
        "broken",
        "bug",
        "issue",
        "problem",
        # 中文负面
        "难用",
        "复杂",
        "慢",
        "不行",
        "有问题",
        "坏了",
        "bug",
    ]

    # 技术特征词 (用于判断是否与技术相关)
    TECH_WORDS = [
        "api",
        "cli",
        "tool",
        "framework",
        "library",
        "package",
        "install",
        "setup",
        "configure",
        "run",
        "execute",
        "code",
        "development",
        "workflow",
        "pipeline",
        "mcp",
        "agent",
        "llm",
        "ai",
        "automation",
        "文档",
        "测试",
        "部署",
        "集成",
    ]

    def __init__(self):
        """初始化分析器"""
        # 编译正则表达式
        self.positive_pattern = re.compile(
            r"\b(" + "|".join(re.escape(w) for w in self.POSITIVE_WORDS) + r")\b", re.IGNORECASE
        )
        self.negative_pattern = re.compile(
            r"\b(" + "|".join(re.escape(w) for w in self.NEGATIVE_WORDS) + r")\b", re.IGNORECASE
        )

    def analyze(self, text: str) -> SentimentResult:
        """分析文本情感

        Args:
            text: 待分析文本

        Returns:
            SentimentResult
        """
        if not text:
            return SentimentResult(text=text, score=0.0, label="neutral", confidence=0.0, key_words=[])

        # 清理文本
        clean_text = text.lower()
        words = clean_text.split()

        # 计算情感分数
        positive_matches = self.positive_pattern.findall(text)
        negative_matches = self.negative_pattern.findall(text)

        # 基础分数 (-1 到 1)
        if positive_matches or negative_matches:
            raw_score = (len(positive_matches) - len(negative_matches)) / max(len(positive_matches) + len(negative_matches), 1)
        else:
            raw_score = 0

        # 文本长度调整 (短文本更不确定)
        confidence = min(len(words) / 50.0, 1.0)

        # 标签
        if raw_score > 0.1:
            label = "positive"
        elif raw_score < -0.1:
            label = "negative"
        else:
            label = "neutral"

        # 提取关键词
        key_words: list[str] = []
        if positive_matches:
            key_words.extend(set(positive_matches))
        if negative_matches:
            key_words.extend(set(negative_matches))

        return SentimentResult(
            text=text[:100] + "..." if len(text) > 100 else text,
            score=round(raw_score, 2),
            label=label,
            confidence=round(confidence, 2),
            key_words=list(set(key_words))[:5],
        )

    def analyze_batch(self, texts: List[str]) -> Dict:
        """批量分析

        Args:
            texts: 文本列表

        Returns:
            汇总统计
        """
        results = [self.analyze(text) for text in texts]

        total = len(results)
        positive = sum(1 for r in results if r.label == "positive")
        negative = sum(1 for r in results if r.label == "negative")
        neutral = total - positive - negative

        # 计算平均分数
        avg_score = sum(r.score for r in results) / total if total > 0 else 0

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "avg_score": round(avg_score, 2),
            "positive_ratio": f"{positive / total:.1%}" if total > 0 else "0%",
            "negative_ratio": f"{negative / total:.1%}" if total > 0 else "0%",
        }

    def extract_topics(self, texts: List[str]) -> List[str]:
        """提取讨论话题

        Args:
            texts: 文本列表

        Returns:
            热门话题列表
        """
        # 简单的关键词提取
        topic_keywords: dict[str, int] = {}
        for text in texts:
            words = re.findall(r"\b[a-z]{3,}\b", text.lower())
            for word in words:
                if word in self.TECH_WORDS:
                    topic_keywords[word] = topic_keywords.get(word, 0) + 1

        # 排序并返回前10
        sorted_topics = sorted(topic_keywords.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_topics[:10]]


def main():
    """主函数 - 测试分析器"""
    print("=" * 60)
    print("💭 情感分析器")
    print("=" * 60)
    print()

    analyzer = SentimentAnalyzer()

    # 测试文本
    test_texts = [
        "lingflow is awesome! Very useful tool for automation.",
        "The documentation is confusing and hard to follow.",
        "Great project! The CLI is intuitive and powerful.",
        "Having some issues with the setup process.",
        "Solid work! This will save me a lot of time.",
        "中文测试：这个工具很好用，推荐使用。",
    ]

    print("📝 测试文本:")
    for i, text in enumerate(test_texts, 1):
        print(f"  [{i}] {text}")

    print()
    print("📊 分析结果:")
    for i, text in enumerate(test_texts, 1):
        result = analyzer.analyze(text)
        print(f"  [{i}] {result.label:8} | score: {result.score:+.2f} | {result.key_words}")

    print()
    summary = analyzer.analyze_batch(test_texts)
    print("📈 汇总统计:")
    print(f"  总数: {summary['total']}")
    print(f"  正面: {summary['positive']} ({summary['positive_ratio']})")
    print(f"  负面: {summary['negative']} ({summary['negative_ratio']})")
    print(f"  中性: {summary['neutral']}")
    print(f"  平均分: {summary['avg_score']:+.2f}")


if __name__ == "__main__":
    main()
