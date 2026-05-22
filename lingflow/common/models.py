"""lingflow 数据模型"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStatus(Enum):
    """代理状态枚举

    定义代理在生命周期中的三种状态：
    - IDLE: 代理空闲，可以接受新任务
    - BUSY: 代理正在执行任务
    - FAILED: 代理执行失败
    """

    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"


class TaskPriority(Enum):
    """任务优先级枚举

    定义任务的优先级，数值越小优先级越高：
    - CRITICAL: 关键任务，最高优先级 (0)
    - HIGH: 高优先级任务 (1)
    - NORMAL: 普通优先级任务 (2)
    - LOW: 低优先级任务 (3)
    """

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class TaskSource(Enum):
    """任务来源枚举

    区分任务是用户指令还是 AI 自驱生成：
    - USER: 用户直接指令（最高优先级，跳过自驱门控）
    - SELF_GENERATED: AI 自驱生成的任务（需要经过五道门控）
    """

    USER = "user"
    SELF_GENERATED = "self_generated"


class RiskLevel(Enum):
    """任务风险等级枚举

    自驱任务的风险评估等级：
    - LOW: 只读操作，不影响系统（grep、view、glob）
    - MEDIUM: 写操作但在当前项目内（edit、write）
    - HIGH: 外部操作/跨项目/系统级（git push、curl、rm -rf）
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AgentConfig:
    """代理配置数据类

    定义代理的配置参数，包括名称、能力、任务限制等。

    Attributes:
        name: 代理名称
        description: 代理描述
        capabilities: 代理能力列表
        max_tasks: 最大并发任务数，默认为1
        context_limit: 上下文限制（token数），默认为8000
        timeout: 任务超时时间（秒），默认为300
        parallel_safe: 是否支持并行执行，默认为True
    """

    name: str
    description: str
    capabilities: List[str]
    max_tasks: int = 1
    context_limit: int = 8000
    timeout: int = 300
    parallel_safe: bool = True


@dataclass
class Task:
    """任务数据类

    定义待执行的任务，包括ID、名称、描述、优先级等信息。

    Attributes:
        task_id: 任务唯一标识符
        name: 任务名称
        description: 任务描述
        priority: 任务优先级
        agent_type: 指定代理类型，默认为空（表示任意兼容代理）
        dependencies: 任务依赖列表，默认为空
        context: 任务上下文数据，默认为空字典
        is_read_only: 是否为只读任务（只读任务可完全并行，写任务需串行），默认为True
        source: 任务来源（用户指令/自驱生成），默认为 USER
        user_confirmation: 用户是否确认过此任务（自驱任务默认为False），诚实标注
        tap_check_result: TAP锚定协议检查结果
        risk_level: 风险评估等级
    """

    task_id: str
    name: str
    description: str
    priority: TaskPriority
    agent_type: str = ""
    project: str = ""
    working_dir: str = ""
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    is_read_only: bool = True
    source: TaskSource = TaskSource.USER
    user_confirmation: bool = False
    tap_check_result: Optional[Dict[str, Any]] = None
    risk_level: RiskLevel = RiskLevel.LOW


@dataclass
class TaskResult:
    """任务执行结果数据类

    记录任务执行的结果，包括成功状态、输出、错误和执行时间。

    Attributes:
        task_id: 任务唯一标识符
        success: 执行是否成功
        output: 成功时的输出内容
        error: 失败时的错误信息
        execution_time: 执行时间（秒）
        agent_used: 执行任务的代理名称
    """

    task_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_used: Optional[str] = None
