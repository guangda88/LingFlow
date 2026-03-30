"""
LingFlow Token Estimator

精确估算消息的 token 数量，支持多种 LLM 模型
"""

import tiktoken
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenEstimate:
    """Token 估算结果"""
    token_count: int
    model: str
    encoding: str
    estimated: bool = False  # 是否为估算值


class TokenEstimator:
    """Token 估算器"""

    # 支持的模型和对应的编码
    MODEL_ENCODINGS = {
        # Claude 模型（使用 cl100k_base 作为近似）
        "claude-sonnet-4": "cl100k_base",
        "claude-opus-4": "cl100k_base",
        "claude-haiku-4": "cl100k_base",
        "claude-3-5-sonnet": "cl100k_base",
        "claude-3-opus": "cl100k_base",
        "claude-3-haiku": "cl100k_base",

        # GPT 模型
        "gpt-4": "cl100k_base",
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-3.5-turbo": "cl100k_base",

        # 其他模型
        "text-davinci-003": "p50k_base",
        "code-davinci-002": "p50k_base",

        # 默认
        "default": "cl100k_base"
    }

    def __init__(self, model: str = "default"):
        """
        初始化 Token 估算器

        Args:
            model: 模型名称
        """
        self.model = model
        self.encoding_name = self._get_encoding(model)
        self.encoding = self._load_encoding()
        logger.info(f"TokenEstimator initialized for {model} with {self.encoding_name}")

    def _get_encoding(self, model: str) -> str:
        """获取模型对应的编码名称"""
        return self.MODEL_ENCODINGS.get(model, self.MODEL_ENCODINGS["default"])

    def _load_encoding(self):
        """加载 tiktoken 编码"""
        try:
            return tiktoken.get_encoding(self.encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load encoding {self.encoding_name}: {e}")
            # 回退到默认编码
            return tiktoken.get_encoding("cl100k_base")

    def estimate(
        self,
        text: str,
        model: Optional[str] = None
    ) -> TokenEstimate:
        """
        估算文本的 token 数量

        Args:
            text: 输入文本
            model: 模型名称（可选，覆盖初始化时的模型）

        Returns:
            Token 估算结果
        """
        if not text:
            return TokenEstimate(
                token_count=0,
                model=model or self.model,
                encoding=self.encoding_name
            )

        try:
            # 使用指定的编码进行计数
            encoding = self.encoding
            if model and model != self.model:
                encoding_name = self._get_encoding(model)
                encoding = tiktoken.get_encoding(encoding_name)

            tokens = encoding.encode(text)
            token_count = len(tokens)

            return TokenEstimate(
                token_count=token_count,
                model=model or self.model,
                encoding=encoding_name if model else self.encoding_name,
                estimated=False
            )

        except Exception as e:
            logger.error(f"Error estimating tokens: {e}")
            # 回退到字符估算（粗略估算：1 token ≈ 4 characters）
            estimated_count = len(text) // 4
            return TokenEstimate(
                token_count=estimated_count,
                model=model or self.model,
                encoding=self.encoding_name,
                estimated=True
            )

    def estimate_messages(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> TokenEstimate:
        """
        估算消息列表的 token 数量

        Args:
            messages: 消息列表，每条消息包含 role 和 content
            model: 模型名称（可选）

        Returns:
            Token 估算结果
        """
        total_tokens = 0

        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "")

            # 估算消息内容的 tokens
            content_estimate = self.estimate(content, model)
            total_tokens += content_estimate.token_count

            # 添加消息格式的额外 tokens（role、分隔符等）
            # 通常每条消息额外增加约 4-6 个 tokens
            total_tokens += 4

        return TokenEstimate(
            token_count=total_tokens,
            model=model or self.model,
            encoding=self.encoding_name,
            estimated=False
        )

    def estimate_from_messages_object(
        self,
        messages: List[Dict],
        model: Optional[str] = None
    ) -> TokenEstimate:
        """
        从消息对象估算 tokens（支持更复杂的消息结构）

        Args:
            messages: 消息对象列表
            model: 模型名称（可选）

        Returns:
            Token 估算结果
        """
        total_tokens = 0

        for msg in messages:
            # 处理标准消息格式
            if "content" in msg:
                content = msg["content"]
                if isinstance(content, str):
                    total_tokens += self.estimate(content, model).token_count
                elif isinstance(content, list):
                    # 处理多模态内容
                    for item in content:
                        if item.get("type") == "text":
                            total_tokens += self.estimate(
                                item.get("text", ""), model
                            ).token_count

            # 添加额外开销（role、格式等）
            total_tokens += 4

        return TokenEstimate(
            token_count=total_tokens,
            model=model or self.model,
            encoding=self.encoding_name
        )

    def batch_estimate(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[TokenEstimate]:
        """
        批量估算多个文本的 token 数量

        Args:
            texts: 文本列表
            model: 模型名称（可选）

        Returns:
            Token 估算结果列表
        """
        return [self.estimate(text, model) for text in texts]

    def get_model_info(self, model: Optional[str] = None) -> Dict[str, any]:
        """
        获取模型信息

        Args:
            model: 模型名称（可选）

        Returns:
            模型信息字典
        """
        model_name = model or self.model
        encoding_name = self._get_encoding(model_name)

        return {
            "model": model_name,
            "encoding": encoding_name,
            "supported": encoding_name in self.MODEL_ENCODINGS.values()
        }


# 全局实例
_estimators: Dict[str, TokenEstimator] = {}


def get_token_estimator(model: str = "default") -> TokenEstimator:
    """
    获取 Token 估算器实例（单例模式）

    Args:
        model: 模型名称

    Returns:
        Token 估算器实例
    """
    if model not in _estimators:
        _estimators[model] = TokenEstimator(model)
    return _estimators[model]


__all__ = [
    "TokenEstimator",
    "TokenEstimate",
    "get_token_estimator"
]
