"""
请求模型（Pydantic）
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

# ========== 技能系统请求 ==========

class SkillExecutionRequest(BaseModel):
    """技能执行请求"""
    params: Dict[str, Any] = Field(default_factory=dict, description="技能参数")
    timeout: int = Field(default=300, ge=1, le=600, description="超时时间（秒）")

class SkillBatchRequest(BaseModel):
    """批量技能执行请求"""
    tasks: List[Dict[str, Any]] = Field(..., description="任务列表 [{name, params}, ...]")
    max_workers: int = Field(default=4, ge=1, le=10, description="最大并发数")


# ========== 工作流系统请求 ==========

class WorkflowExecutionRequest(BaseModel):
    """工作流执行请求"""
    params: Dict[str, Any] = Field(default_factory=dict, description="工作流参数")
    config: Optional[Dict[str, Any]] = Field(default=None, description="工作流配置")
    strategy: str = Field(default="hybrid", pattern="^(parallel|sequential|hybrid)$", description="执行策略")


# ========== 代码审查请求 ==========

class CodeReviewRequest(BaseModel):
    """代码审查请求"""
    target_path: str = Field(..., description="目标文件或目录")
    dimensions: Optional[List[str]] = Field(default=None, description="审查维度")
    output_format: str = Field(default="json", pattern="^(json|markdown|html)$", description="输出格式")


# ========== 情报系统请求 ==========

class IntelligenceRequest(BaseModel):
    """情报查询请求"""
    keywords: str = Field(..., description="关键词（逗号分隔）")
    language: Optional[str] = Field(default=None, description="编程语言过滤")


# ========== 需求管理请求 ==========

class CreateRequirementRequest(BaseModel):
    """创建需求请求"""
    title: str = Field(..., min_length=1, max_length=200, description="需求标题")
    description: str = Field(..., min_length=1, description="需求描述")
    priority: str = Field(default="normal", pattern="^(critical|high|normal|low)$", description="优先级")
    category: str = Field(default="feature", pattern="^(feature|bug|improvement|task)$", description="分类")
    tags: List[str] = Field(default_factory=list, description="标签")

class UpdateRequirementRequest(BaseModel):
    """更新需求请求"""
    status: Optional[str] = Field(None, pattern="^(pending|approved|rejected|in_progress|completed)$", description="状态")
    priority: Optional[str] = Field(None, pattern="^(critical|high|normal|low)$", description="优先级")
    description: Optional[str] = Field(None, min_length=1, description="需求描述")

class LinkRequirementRequest(BaseModel):
    """关联需求请求"""
    branch_name: str = Field(..., description="Git 分支名称")
