"""LingFlow API 封装建议

这个文件展示了建议的 LingFlow 公共 API 封装结构。
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from functools import wraps


# =============================================================================
# 1. 统一异常封装
# =============================================================================

class LingFlowError(Exception):
    """LingFlow 基础异常"""

    def __init__(self, message: str, *, code: str = "LF000", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


class WorkflowError(LingFlowError):
    """工作流相关异常"""
    pass


class SkillError(LingFlowError):
    """技能相关异常"""
    pass


class AgentError(LingFlowError):
    """代理相关异常"""
    pass


class ConfigurationError(LingFlowError):
    """配置相关异常"""
    pass


class ValidationError(LingFlowError):
    """验证相关异常"""
    pass


# =============================================================================
# 2. 统一结果封装
# =============================================================================

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    """统一的执行结果封装

    Examples:
        >>> success = Result.ok(data={"key": "value"})
        >>> failure = Result.fail("Something went wrong", code="ERR001")
        >>> if success.is_ok():
        ...     print(success.data)
    """
    data: Optional[T] = None
    error: Optional[str] = None
    code: str = "OK"
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: T, **details) -> "Result[T]":
        """创建成功结果"""
        return cls(data=data, code="OK", details=details)

    @classmethod
    def fail(cls, error: str, code: str = "ERROR", **details) -> "Result[T]":
        """创建失败结果"""
        return cls(data=None, error=error, code=code, details=details)

    @property
    def is_ok(self) -> bool:
        """是否成功"""
        return self.code == "OK" and self.error is None

    @property
    def is_error(self) -> bool:
        """是否失败"""
        return not self.is_ok

    def unwrap(self) -> T:
        """获取数据，失败时抛出异常"""
        if self.is_error:
            raise LingFlowError(self.error or "Unknown error", code=self.code)
        return self.data

    def map(self, func: Callable[[T], Any]) -> "Result[Any]":
        """链式转换"""
        if self.is_ok:
            try:
                return Result.ok(func(self.data))
            except Exception as e:
                return Result.fail(str(e), code="MAP_ERROR")
        return self

    def and_then(self, func: Callable[[T], "Result[T]"]) -> "Result[T]":
        """链式调用"""
        if self.is_ok:
            return func(self.data)
        return self


# =============================================================================
# 3. 统一配置封装
# =============================================================================

@dataclass
class LingFlowConfig:
    """LingFlow 配置类

    使用构建器模式创建：
        config = (LingFlowConfig.builder()
                  .max_parallel(4)
                  .timeout(300)
                  .build())
    """
    # 工作流配置
    max_parallel: int = 2
    max_iterations: int = 100
    scheduling_delay: float = 0.01

    # 技能配置
    skills_path: str = "skills"
    skill_timeout: int = 30

    # 代理配置
    agent_timeout: int = 300
    agent_context_limit: int = 8000

    # 压缩配置
    compression_enabled: bool = True
    compression_target_tokens: int = 4000

    # 安全配置
    allow_symlinks: bool = False
    validate_paths: bool = True

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def builder(cls) -> "LingFlowConfigBuilder":
        """创建构建器"""
        return LingFlowConfigBuilder(cls())

    def validate(self) -> Result[None]:
        """验证配置"""
        if self.max_parallel < 1:
            return Result.fail("max_parallel must be >= 1", code="CONFIG_ERROR")
        if self.skill_timeout < 0:
            return Result.fail("skill_timeout must be >= 0", code="CONFIG_ERROR")
        if self.agent_timeout < 0:
            return Result.fail("agent_timeout must be >= 0", code="CONFIG_ERROR")
        return Result.ok(None)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow": {
                "max_parallel": self.max_parallel,
                "max_iterations": self.max_iterations,
                "scheduling_delay": self.scheduling_delay,
            },
            "skills": {
                "path": self.skills_path,
                "default_timeout": self.skill_timeout,
            },
            "agents": {
                "default_timeout": self.agent_timeout,
                "context_limit": self.agent_context_limit,
            },
            "compression": {
                "enabled": self.compression_enabled,
                "max_tokens": self.compression_target_tokens,
            },
            "security": {
                "allow_symlinks": self.allow_symlinks,
                "validate_paths": self.validate_paths,
            },
            "logging": {
                "level": self.log_level,
                "format": self.log_format,
            },
        }


class LingFlowConfigBuilder:
    """配置构建器"""

    def __init__(self, config: LingFlowConfig):
        self._config = config

    def max_parallel(self, value: int) -> "LingFlowConfigBuilder":
        self._config.max_parallel = value
        return self

    def timeout(self, value: int) -> "LingFlowConfigBuilder":
        self._config.agent_timeout = value
        self._config.skill_timeout = value
        return self

    def skills_path(self, path: str) -> "LingFlowConfigBuilder":
        self._config.skills_path = path
        return self

    def compression(self, enabled: bool, tokens: int = 4000) -> "LingFlowConfigBuilder":
        self._config.compression_enabled = enabled
        self._config.compression_target_tokens = tokens
        return self

    def security(self, allow_symlinks: bool = False) -> "LingFlowConfigBuilder":
        self._config.allow_symlinks = allow_symlinks
        return self

    def build(self) -> LingFlowConfig:
        """构建配置"""
        result = self._config.validate()
        if result.is_error:
            raise ConfigurationError(result.error, code=result.code)
        return self._config


# =============================================================================
# 4. 技能基类封装
# =============================================================================

@dataclass
class SkillContext:
    """技能执行上下文"""
    skill_name: str
    params: Dict[str, Any]
    working_dir: Path
    temp_dir: Path
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any = None, **metadata) -> "SkillResult":
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata) -> "SkillResult":
        return cls(success=False, error=error, metadata=metadata)


class BaseSkill(ABC):
    """技能基类 - 所有技能应继承此类

    Example:
        >>> class MySkill(BaseSkill):
        ...     name = "my-skill"
        ...     description = "My custom skill"
        ...
        ...     def validate_params(self, params: Dict) -> Result[None]:
        ...         if "required_field" not in params:
        ...             return Result.fail("Missing required_field")
        ...         return Result.ok()
        ...
        ...     def execute(self, context: SkillContext) -> SkillResult:
        ...         # 实现技能逻辑
        ...         return SkillResult.ok(data={"result": "done"})
    """

    # 类级别的元数据（子类覆盖）
    name: str = "base-skill"
    description: str = "Base skill class"
    version: str = "1.0.0"
    author: str = ""
    dependencies: List[str] = field(default_factory=list)

    @classmethod
    @abstractmethod
    def validate_params(cls, params: Dict[str, Any]) -> Result[None]:
        """验证参数

        Args:
            params: 技能参数

        Returns:
            验证结果
        """
        return Result.ok()

    @abstractmethod
    def execute(self, context: SkillContext) -> SkillResult:
        """执行技能

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        return SkillResult.ok()

    def pre_execute(self, context: SkillContext) -> SkillResult:
        """执行前钩子（可选重写）"""
        return SkillResult.ok()

    def post_execute(self, context: SkillContext, result: SkillResult) -> SkillResult:
        """执行后钩子（可选重写）"""
        return result

    def on_error(self, context: SkillContext, error: Exception) -> SkillResult:
        """错误处理钩子（可选重写）"""
        return SkillResult.fail(str(error))


# =============================================================================
# 5. 服务层封装
# =============================================================================

class SkillService:
    """技能服务 - 封装技能相关的所有操作"""

    def __init__(self, config: LingFlowConfig):
        self._config = config
        self._skills: Dict[str, BaseSkill] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        """加载技能"""
        from pathlib import Path
        import importlib.util

        skills_dir = Path(self._config.skills_path)
        if not skills_dir.exists():
            return

        for skill_path in skills_dir.iterdir():
            if not skill_path.is_dir():
                continue

            impl_file = skill_path / "implementation.py"
            if not impl_file.exists():
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"skills.{skill_path.name}", str(impl_file)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 如果模块有 BaseSkill 子类，注册它
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, BaseSkill) and
                        attr is not BaseSkill):
                        self._skills[attr.name] = attr()
            except Exception as e:
                raise SkillError(f"Failed to load skill {skill_path.name}: {e}")

    def list_skills(self) -> List[str]:
        """列出所有可用技能"""
        return list(self._skills.keys())

    def get_skill_info(self, name: str) -> Result[Dict[str, Any]]:
        """获取技能信息"""
        if name not in self._skills:
            return Result.fail(f"Skill not found: {name}", code="SKILL_NOT_FOUND")

        skill = self._skills[name]
        return Result.ok({
            "name": skill.name,
            "description": skill.description,
            "version": skill.version,
            "author": skill.author,
            "dependencies": skill.dependencies,
        })

    def execute_skill(self, name: str, params: Dict[str, Any]) -> SkillResult:
        """执行技能"""
        if name not in self._skills:
            return SkillResult.fail(f"Skill not found: {name}")

        skill = self._skills[name]

        # 验证参数
        validation = skill.validate_params(params)
        if validation.is_error:
            return SkillResult.fail(validation.error)

        # 创建上下文
        context = SkillContext(
            skill_name=name,
            params=params,
            working_dir=Path.cwd(),
            temp_dir=Path.cwd() / ".lingflow" / "temp",
        )

        # 执行
        try:
            pre_result = skill.pre_execute(context)
            if not pre_result.success:
                return pre_result

            import time
            start_time = time.time()
            result = skill.execute(context)
            result.execution_time = time.time() - start_time

            return skill.post_execute(context, result)

        except Exception as e:
            return skill.on_error(context, e)


class WorkflowService:
    """工作流服务 - 封装工作流相关的所有操作"""

    def __init__(self, config: LingFlowConfig):
        self._config = config
        self._skill_service = SkillService(config)

    def execute_file(self, workflow_path: Union[str, Path]) -> Result[Dict[str, Any]]:
        """从文件执行工作流"""
        import yaml

        path = Path(workflow_path)

        # 验证路径
        if not path.exists():
            return Result.fail(f"Workflow file not found: {workflow_path}", code="FILE_NOT_FOUND")

        # 加载工作流定义
        try:
            with open(path, "r", encoding="utf-8") as f:
                workflow_def = yaml.safe_load(f)
        except Exception as e:
            return Result.fail(f"Failed to load workflow: {e}", code="LOAD_ERROR")

        # 验证工作流定义
        validation = self._validate_workflow(workflow_def)
        if validation.is_error:
            return Result.fail(validation.error, code=validation.code)

        # 执行工作流
        return self.execute(workflow_def)

    def _validate_workflow(self, workflow: Dict[str, Any]) -> Result[None]:
        """验证工作流定义"""
        if "tasks" not in workflow:
            return Result.fail("Missing 'tasks' in workflow definition", code="INVALID_WORKFLOW")

        if not isinstance(workflow["tasks"], list):
            return Result.fail("'tasks' must be a list", code="INVALID_WORKFLOW")

        return Result.ok()

    def execute(self, workflow: Dict[str, Any]) -> Result[Dict[str, Any]]:
        """执行工作流定义"""
        tasks = workflow.get("tasks", [])
        results = {}

        for task in tasks:
            skill_name = task.get("skill")
            params = task.get("params", {})
            task_id = task.get("id", skill_name)

            result = self._skill_service.execute_skill(skill_name, params)
            results[task_id] = {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "execution_time": result.execution_time,
            }

            if not result.success:
                # 工作流失败
                return Result.fail(
                    f"Task {task_id} failed: {result.error}",
                    code="WORKFLOW_FAILED",
                    results=results
                )

        return Result.ok({"results": results})


# =============================================================================
# 6. 统一API门面
# =============================================================================

class LingFlow:
    """LingFlow 统一API门面

    这是用户与 LingFlow 交互的主要入口点。

    Example:
        >>> # 使用默认配置
        >>> lf = LingFlow()
        >>>
        >>> # 使用自定义配置
        >>> config = LingFlowConfig.builder().max_parallel(4).build()
        >>> lf = LingFlow(config)
        >>>
        >>> # 执行技能
        >>> result = lf.skill.execute("code-analysis", {"target": "./"})
        >>>
        >>> # 执行工作流
        >>> result = lf.workflow.execute_file("workflow.yaml")
    """

    def __init__(self, config: Optional[LingFlowConfig] = None):
        """初始化 LingFlow

        Args:
            config: 配置对象，默认使用 LingFlowConfig()
        """
        self._config = config or LingFlowConfig()

        # 初始化服务
        self.skill = SkillService(self._config)
        self.workflow = WorkflowService(self._config)

    @property
    def config(self) -> LingFlowConfig:
        """获取当前配置（只读）"""
        return self._config

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "skills": {
                "available": len(self.skill.list_skills()),
                "list": self.skill.list_skills(),
            },
            "config": self._config.to_dict(),
        }

    def reload_skills(self) -> Result[None]:
        """重新加载技能"""
        try:
            self.skill._load_skills()
            return Result.ok()
        except Exception as e:
            return Result.fail(str(e), code="RELOAD_ERROR")


# =============================================================================
# 7. 使用示例
# =============================================================================

def example_basic_usage():
    """基础使用示例"""
    # 创建 LingFlow 实例
    lf = LingFlow()

    # 执行技能
    result = lf.skill.execute("code-analysis", {
        "target": "./lingflow/",
        "metrics": ["complexity", "duplication"]
    })

    if result.success:
        print(f"Success: {result.data}")
    else:
        print(f"Error: {result.error}")


def example_custom_config():
    """自定义配置示例"""
    # 使用构建器创建配置
    config = (LingFlowConfig.builder()
              .max_parallel(4)
              .timeout(600)
              .compression(True, 8000)
              .skills_path("./custom_skills")
              .build())

    lf = LingFlow(config)
    print(lf.get_status())


def example_workflow():
    """工作流执行示例"""
    lf = LingFlow()

    result = lf.workflow.execute_file("workflows/my_workflow.yaml")

    if result.is_ok:
        print("Workflow completed successfully!")
        for task_id, task_result in result.data["results"].items():
            print(f"  {task_id}: {task_result['success']}")
    else:
        print(f"Workflow failed: {result.error}")


def example_custom_skill():
    """自定义技能示例"""
    from lingflow.api import BaseSkill, SkillContext, SkillResult, Result

    class MyAnalysisSkill(BaseSkill):
        name = "my-analysis"
        description = "Custom analysis skill"
        version = "1.0.0"

        @classmethod
        def validate_params(cls, params):
            if "target" not in params:
                return Result.fail("Missing 'target' parameter")
            return Result.ok()

        def execute(self, context: SkillContext):
            # 实现分析逻辑
            target = context.params["target"]
            return SkillResult.ok(data={"files_analyzed": 42})

    # 注册并使用技能
    lf = LingFlow()
    lf.skill._skills["my-analysis"] = MyAnalysisSkill()

    result = lf.skill.execute("my-analysis", {"target": "./"})
    print(result)


# =============================================================================
# 8. 装饰器封装
# =============================================================================

def handle_errors(func):
    """统一的错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return Result.ok(func(*args, **kwargs))
        except LingFlowError as e:
            return Result.fail(e.message, code=e.code, details=e.details)
        except Exception as e:
            return Result.fail(str(e), code="UNEXPECTED_ERROR")
    return wrapper


def track_performance(func):
    """性能追踪装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        if isinstance(result, Result):
            result.details["execution_time"] = elapsed

        return result
    return wrapper


# =============================================================================
# 9. 上下文管理器封装
# =============================================================================

class lingflow_session:
    """LingFlow 会话上下文管理器

    Example:
        >>> with lingflow_session(config) as lf:
        ...     lf.skill.execute("analysis", {...})
        ...     lf.workflow.execute_file("workflow.yaml")
        # 会话结束后自动清理资源
    """

    def __init__(self, config: Optional[LingFlowConfig] = None):
        self._config = config or LingFlowConfig()
        self._instance: Optional[LingFlow] = None

    def __enter__(self) -> LingFlow:
        self._instance = LingFlow(self._config)
        return self._instance

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理资源
        if self._instance:
            # 可以在这里添加清理逻辑
            pass
        return False


# =============================================================================
# 10. 导出的公共API
# =============================================================================

__all__ = [
    # 核心类
    "LingFlow",
    "LingFlowConfig",
    "LingFlowConfigBuilder",

    # 服务类
    "SkillService",
    "WorkflowService",

    # 基类
    "BaseSkill",

    # 数据类型
    "Result",
    "SkillContext",
    "SkillResult",

    # 异常
    "LingFlowError",
    "WorkflowError",
    "SkillError",
    "AgentError",
    "ConfigurationError",
    "ValidationError",

    # 工具
    "lingflow_session",
    "handle_errors",
    "track_performance",
]
