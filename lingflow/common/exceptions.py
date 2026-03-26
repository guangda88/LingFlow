"""LingFlow 异常模块"""

from typing import Any, Dict, Optional


class LingFlowError(Exception):
    """LingFlow 基础异常

    支持错误码和详细信息。
    """

    DEFAULT_CODE = "LF_ERROR"

    def __init__(
        self,
        message: str,
        code: str = DEFAULT_CODE,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化异常。

        Args:
            message: 错误消息
            code: 错误码（默认为 LF_ERROR）
            details: 额外详细信息
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        """返回格式化的错误字符串。"""
        return f"[{self.code}] {self.message}"


class SkillError(LingFlowError):
    """技能相关异常"""


class SkillNotFoundError(SkillError):
    """技能不存在异常"""


class SkillLoadError(SkillError):
    """技能加载异常"""


class SkillExecutionError(SkillError):
    """技能执行异常"""


class WorkflowError(LingFlowError):
    """工作流相关异常"""


class WorkflowValidationError(WorkflowError):
    """工作流验证异常"""


class WorkflowExecutionError(WorkflowError):
    """工作流执行异常"""


class AgentError(LingFlowError):
    """代理相关异常"""


class AgentNotFoundError(AgentError):
    """代理不存在异常"""


class AgentExecutionError(AgentError):
    """代理执行异常"""


class CompressionError(LingFlowError):
    """压缩相关异常"""


class ConfigurationError(LingFlowError):
    """配置相关异常"""


class ValidationError(LingFlowError):
    """验证相关异常"""
