"""LingFlow Skills 自定义异常模块

本模块定义了 LingFlow 框架中各 Skills 的自定义异常类型。
使用自定义异常可以提供更精确的错误处理和更清晰的错误信息。

使用示例:
    from skills.exceptions import APIDocError, UIMockupError

    try:
        generate_api_documentation(code)
    except APIDocError as e:
        logger.error(f"API 文档生成失败: {e}")
    except SyntaxError as e:
        logger.error(f"代码语法错误: {e}")
"""


class LingFlowSkillError(Exception):
    """LingFlow Skills 基础异常类

    所有 Skills 特定异常的基类。
    用于捕获和处理 Skills 执行过程中的通用错误。
    """

    def __init__(self, message: str, skill_name: str = ""):
        """初始化异常

        Args:
            message: 错误信息
            skill_name: 技能名称 (可选)
        """
        self.skill_name = skill_name
        self.message = message
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误信息"""
        if self.skill_name:
            return f"[{self.skill_name}] {self.message}"
        return self.message


class APIDocError(LingFlowSkillError):
    """API 文档生成器异常

    在 API 文档生成过程中发生错误时抛出。
    包括代码扫描、路由解析、类型提取等操作错误。
    """

    def __init__(self, message: str):
        super().__init__(message, "api-doc-generator")


class UIMockupError(LingFlowSkillError):
    """UI 原型生成器异常

    在 UI 原型生成过程中发生错误时抛出。
    包括组件解析、模板渲染、样式生成等操作错误。
    """

    def __init__(self, message: str):
        super().__init__(message, "ui-mockup-generator")


class DatabaseSchemaError(LingFlowSkillError):
    """数据库设计器异常

    在数据库模式设计过程中发生错误时抛出。
    包括实体识别、关系分析、DDL 生成等操作错误。
    """

    def __init__(self, message: str):
        super().__init__(message, "database-schema-designer")


class CICDError(LingFlowSkillError):
    """CI/CD 编排器异常

    在 CI/CD 流水线配置生成过程中发生错误时抛出。
    包括平台配置、工作流生成、验证等操作错误。
    """

    def __init__(self, message: str):
        super().__init__(message, "ci-cd-orchestrator")


class DeploymentError(LingFlowSkillError):
    """部署自动化异常

    在部署配置生成过程中发生错误时抛出。
    包括 Dockerfile 生成、K8s 配置、蓝绿部署等操作错误。
    """

    def __init__(self, message: str):
        super().__init__(message, "deployment-automation")


class EnvironmentManagerError(LingFlowSkillError):
    """环境管理器异常

    在环境配置管理过程中发生错误时抛出。
    包括环境检测、配置验证、安全审计等操作错误。
    """

    def __init__(self, message: str):
        super().__init__(message, "environment-manager")
