"""LingFlow 数据模型"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class AgentConfig:
    name: str
    description: str
    capabilities: List[str]
    max_tasks: int = 1
    context_limit: int = 8000
    timeout: int = 300
    parallel_safe: bool = True


@dataclass
class Task:
    task_id: str
    name: str
    description: str
    priority: TaskPriority
    agent_type: str = ""  # 指定代理类型（简化）
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    task_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_used: Optional[str] = None
