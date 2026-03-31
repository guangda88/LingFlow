"""Token 估算器模块

提供精确的 token 计数功能。
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TokenEstimator:
    """精确 Token 计数器

    优先使用 tiktoken 进行精确计数，回退到估算模式。
    """

    # 默认比率 (不同模型有所不同)
    DEFAULT_RATIOS: Dict[str, float] = {
        "gpt-4": 0.25,
        "gpt-3.5-turbo": 0.25,
        "claude-3": 0.28,  # Claude 使用不同的 tokenizer
        "default": 0.25
    }

    def __init__(self, model: str = "claude-3", use_tiktoken: bool = True):
        """初始化 Token 估算器

        Args:
            model: 模型名称，用于选择 tokenizer
            use_tiktoken: 是否尝试使用 tiktoken
        """
        self.model = model
        self._tokenizer = None
        self._use_tiktoken = use_tiktoken

        # 尝试加载 tiktoken
        if use_tiktoken:
            self._load_tiktoken()

    def _load_tiktoken(self):
        """尝试加载 tiktoken"""
        try:
            import tiktoken
            # 使用 cl100k_base (GPT-4/3.5-turbo 的编码)
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.info("使用 tiktoken 进行精确 token 计数")
        except ImportError:
            logger.debug("tiktoken 不可用，使用估算模式")
            self._use_tiktoken = False
        except Exception as e:
            logger.warning(f"tiktoken 加载失败: {e}，使用估算模式")
            self._use_tiktoken = False

    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数量

        Args:
            text: 输入文本

        Returns:
            token 数量
        """
        if not text:
            return 0

        if self._use_tiktoken and self._tokenizer:
            try:
                return len(self._tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"tiktoken 计数失败: {e}，回退到估算")

        # 回退到字符估算
        ratio = self.DEFAULT_RATIOS.get(self.model, self.DEFAULT_RATIOS["default"])
        return int(len(text) * ratio)

    def count_messages_tokens(self, messages: list) -> int:
        """计算消息列表的总 token 数

        Args:
            messages: 消息列表

        Returns:
            总 token 数
        """
        total = 0
        for msg in messages:
            if isinstance(msg, dict):
                # 计算角色和内容的 tokens
                role = msg.get("role", "")
                content = msg.get("content", "")
                total += self.count_tokens(role) + self.count_tokens(content)

                # 计算其他字段的 tokens
                for key, value in msg.items():
                    if key not in ("role", "content"):
                        total += self.count_tokens(str(key))
                        total += self.count_tokens(str(value))
        return total

    def get_model_ratio(self, model: str = None) -> float:
        """获取指定模型的 token/字符 比率

        Args:
            model: 模型名称，默认使用当前模型

        Returns:
            token 比率
        """
        model = model or self.model
        return self.DEFAULT_RATIOS.get(model, self.DEFAULT_RATIOS["default"])
