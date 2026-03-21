"""LingFlow 异常模块"""

class LingFlowError(Exception):
    """LingFlow 基础异常"""
    pass

class SkillError(LingFlowError):
    """技能相关异常"""
    pass

class SkillNotFoundError(SkillError):
    """技能不存在异常"""
    pass

class SkillLoadError(SkillError):
    """技能加载异常"""
    pass

class SkillExecutionError(SkillError):
    """技能执行异常"""
    pass

class WorkflowError(LingFlowError):
    """工作流相关异常"""
    pass

class WorkflowValidationError(WorkflowError):
    """工作流验证异常"""
    pass

class WorkflowExecutionError(WorkflowError):
    """工作流执行异常"""
    pass

class AgentError(LingFlowError):
    """代理相关异常"""
    pass

class AgentNotFoundError(AgentError):
    """代理不存在异常"""
    pass

class AgentExecutionError(AgentError):
    """代理执行异常"""
    pass

class CompressionError(LingFlowError):
    """压缩相关异常"""
    pass

class ConfigurationError(LingFlowError):
    """配置相关异常"""
    pass

class ValidationError(LingFlowError):
    """验证相关异常"""
    pass
