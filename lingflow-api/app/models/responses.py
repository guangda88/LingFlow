"""
响应模型（Pydantic）
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

# ========== 通用响应 ==========

class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = True
    message: str = "Success"
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str
    detail: Optional[str] = None

# ========== 技能系统响应 ==========

class SkillInfo(BaseModel):
    """技能信息"""
    name: str
    description: str
    version: str
    category: str
    layer: str

class SkillsListResponse(BaseModel):
    """技能列表响应"""
    total: int
    skills: List[SkillInfo]

class SkillExecutionResponse(BaseModel):
    """技能执行响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0

# ========== 工作流系统响应 ==========

class WorkflowInfo(BaseModel):
    """工作流信息"""
    workflow_id: str
    name: str
    type: str
    status: str
    priority: str
    description: str

class WorkflowsListResponse(BaseModel):
    """工作流列表响应"""
    total: int
    workflows: List[WorkflowInfo]

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    task_id: Optional[str] = None
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: TaskStatus
    progress: float = 0.0
    current_step: Optional[str] = None
    completed_steps: List[str] = Field(default_factory=list)
    failed_steps: List[str] = Field(default_factory=list)
    execution_time: float = 0.0
    result: Optional[Dict[str, Any]] = None

# ========== 代码审查响应 ==========

class ReviewDimension(BaseModel):
    """审查维度"""
    name: str
    score: float
    status: str
    issues: List[Dict[str, Any]] = Field(default_factory=list)

class CodeReviewResponse(BaseModel):
    """代码审查响应"""
    overall_score: float
    dimensions: Dict[str, ReviewDimension]
    suggestions: List[Dict[str, Any]]
    metrics: Dict[str, Any]

# ========== 情报系统响应 ==========

class RepoInfo(BaseModel):
    """仓库信息"""
    name: str
    url: str
    stars: int
    description: str
    language: Optional[str] = None
    relevance_score: float = 0.0

class IntelligenceResponse(BaseModel):
    """情报响应"""
    keywords: str
    total: int
    items: List[RepoInfo]

# ========== 需求管理响应 ==========

class RequirementInfo(BaseModel):
    """需求信息"""
    requirement_id: str
    title: str
    description: str
    status: str
    priority: str
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None

class RequirementsListResponse(BaseModel):
    """需求列表响应"""
    total: int
    requirements: List[RequirementInfo]
