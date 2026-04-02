"""对话摘要生成器

提供对话历史摘要功能。
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationSummarizer:
    """对话摘要生成器

    将多条对话消息压缩成简洁的摘要。
    """

    def __init__(self, max_summary_length: int = 500):
        """初始化摘要生成器

        Args:
            max_summary_length: 最大摘要长度（字符数）
        """
        self.max_summary_length = max_summary_length

    def summarize(
        self,
        messages: List[Dict],
        focus: Optional[str] = None
    ) -> str:
        """生成对话摘要

        Args:
            messages: 要摘要的消息列表
            focus: 可选的摘要焦点（如 "code", "errors"）

        Returns:
            摘要文本
        """
        if not messages:
            return ""

        # 提取关键信息
        key_points = self._extract_key_points(messages, focus)

        # 生成摘要
        summary = self._generate_summary(key_points)

        # 截断到最大长度
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length - 3] + "..."

        return summary

    def summarize_by_topic(
        self,
        messages: List[Dict],
        topic: str
    ) -> str:
        """按主题生成摘要

        Args:
            messages: 消息列表
            topic: 主题关键词

        Returns:
            主题摘要
        """
        # 过滤相关消息
        relevant = [
            m for m in messages
            if topic.lower() in str(m).lower()
        ]

        if not relevant:
            return f"No discussion about {topic}"

        return self.summarize(relevant, focus=topic)

    def _extract_key_points(
        self,
        messages: List[Dict],
        focus: Optional[str] = None
    ) -> List[str]:
        """提取关键点

        Args:
            messages: 消息列表
            focus: 焦点主题

        Returns:
            关键点列表
        """
        key_points = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if not content:
                continue

            # 提取用户的问题
            if role == "user":
                # 提取问题（通常以问号结尾或包含疑问词）
                question_indicators = ["?", "？", "如何", "怎么", "what", "how", "why"]
                if any(indicator in content for indicator in question_indicators):
                    key_points.append(f"Q: {content[:100]}...")

            # 提取助手的要点
            elif role == "assistant":
                # 提取代码块
                if "```" in content:
                    code_blocks = content.split("```")[1::2]
                    for block in code_blocks[:2]:  # 最多2个代码块
                        key_points.append(f"Code: {block[:50]}...")

                # 提取关键词句
                if focus and focus.lower() in content.lower():
                    # 提取包含焦点词的句子
                    sentences = content.split(".")
                    for sent in sentences:
                        if focus.lower() in sent.lower():
                            key_points.append(f"Point: {sent.strip()[:100]}")
                            break

        return key_points[:10]  # 最多10个关键点

    def _generate_summary(self, key_points: List[str]) -> str:
        """生成摘要文本

        Args:
            key_points: 关键点列表

        Returns:
            摘要文本
        """
        if not key_points:
            return "No key points found."

        # 简单拼接
        summary = " | ".join(key_points)

        return summary

    def create_summary_message(
        self,
        messages: List[Dict],
        focus: Optional[str] = None
    ) -> Dict:
        """创建摘要消息

        将摘要转换为标准消息格式。

        Args:
            messages: 要摘要的消息
            focus: 可选焦点

        Returns:
            摘要消息对象
        """
        summary_text = self.summarize(messages, focus)

        return {
            "role": "system",
            "content": f"[Previous conversation summary]\n{summary_text}",
            "metadata": {
                "type": "summary",
                "original_count": len(messages),
                "summary_length": len(summary_text)
            }
        }
