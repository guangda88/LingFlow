"""
LingFlow REST API 服务
快速启动模板
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ===== 应用初始化 =====
app = FastAPI(
    title="LingFlow API",
    description="AI增强的软件工程流系统 - REST API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
def _parse_cors_origins(origins_str: str) -> list:
    """解析 CORS 允许的来源"""
    if not origins_str or origins_str.strip() == "*":
        # 开发环境允许所有来源
        import warnings
        warnings.warn(
            "CORS_ORIGINS is set to '*' or empty. This allows all origins. "
            "Set LINGFLOW_CORS_ORIGINS environment variable for production."
        )
        return ["*"]

    # 生产环境：解析逗号分隔的域名列表
    origins = [origin.strip() for origin in origins_str.split(",")]
    # 过滤空字符串
    origins = [origin for origin in origins if origin]

    if not origins:
        import warnings
        warnings.warn("No valid CORS origins configured, allowing all origins")
        return ["*"]

    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(settings.CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key 认证
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """验证 API Key"""
    valid_keys = settings.API_KEYS.split(",") if settings.API_KEYS else []
    if not valid_keys:
        import warnings
        warnings.warn("LINGFLOW_API_KEYS not set — API is open to all requests")
        return api_key
    if api_key not in valid_keys:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# ===== 数据模型 =====

class SkillExecutionRequest(BaseModel):
    """技能执行请求"""
    params: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=300, ge=1, le=600)

class WorkflowExecutionRequest(BaseModel):
    """工作流执行请求"""
    params: Dict[str, Any] = Field(default_factory=dict)
    config: Optional[Dict[str, Any]] = None
    strategy: str = Field(default="hybrid", pattern="^(parallel|sequential|hybrid)$")
    async_mode: bool = Field(default=True)

class CodeReviewRequest(BaseModel):
    """代码审查请求"""
    target_path: str
    dimensions: Optional[List[str]] = None
    output_format: str = Field(default="json", pattern="^(json|markdown|html)$")

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class DiscussionPayload(BaseModel):
    """讨论通知payload"""
    event: str
    discussion_id: str
    topic: str
    from_: str = Field(alias="from")
    timestamp: str

    class Config:
        populate_by_name = True

# ===== API 路由 =====

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "LingFlow API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/council/health")
async def council_health():
    """议事厅健康检查 - 用于LingYi council唤醒"""
    return {
        "status": "ok",
        "service": "LingFlow",
        "member_id": "lingtong",
        "member_name": "灵通",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/test/post")
async def test_post(test: str = None):
    """测试POST请求"""
    logger.info(f"收到测试POST请求: test={test}")
    return {"status": "ok", "received": test}

@app.post("/api/v1/discuss")
async def handle_discussion(payload: DiscussionPayload):
    """接收LingYi council讨论请求 - 灵通自动回复"""
    import sys
    import traceback
    import os
    lingyi_src = os.environ.get(
        "LINGYI_SRC_PATH",
        "/home/ai/LingYi/src",
    )
    sys.path.insert(0, lingyi_src)

    try:
        event = payload.event
        discussion_id = payload.discussion_id
        topic = payload.topic

        logger.info(f"灵通收到讨论通知: {topic} (ID: {discussion_id})")

        if event == "new_message" and discussion_id:
            try:
                from lingyi.llm_utils import create_client, call_llm_with_fallback
                from lingyi.lingmessage import send_message, read_discussion
            except Exception as e:
                error_msg = f"导入LingYi模块失败: {e}"
                logger.error(error_msg)
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {"status": "error", "message": error_msg, "traceback": traceback.format_exc()}

            try:
                # 读取讨论内容
                discussion = read_discussion(discussion_id)
                if not discussion:
                    error_msg = f"无法读取讨论: {discussion_id}"
                    logger.error(error_msg)
                    return {"status": "error", "message": error_msg}

                # 构建回复上下文
                messages_summary = "\n".join([
                    f"- {msg.get('from_name', msg.get('from_id', 'unknown'))}: {msg.get('content', '')[:100]}"
                    for msg in discussion.get("messages", [])[-5:]
                ])

                logger.info(f"讨论摘要: {messages_summary[:200]}...")

                # 主题过滤：检查讨论是否适合工作流编排专家参与
                suitable_keywords = ["工作流", "流程", "优化", "集成", "测试", "自动", "策略", "体系", "架构", "流量"]
                topic_lower = topic.lower()
                if not any(kw in topic_lower for kw in suitable_keywords):
                    logger.info(f"讨论主题 '{topic}' 不适合工作流编排专家，跳过回复")
                    return {
                        "status": "skipped",
                        "reason": "topic_not_suitable",
                        "discussion_id": discussion_id,
                        "topic": topic
                    }

                # 调用LLM生成回复
                client = create_client()
                prompt = f"""你是灵通（LingFlow），工作流编排专家。

讨论主题：{topic}

最近消息：
{messages_summary}

请以灵通的身份，基于工作流编排的专业视角，对上述讨论提出你的观点或建议。要求：
1. 从工作流设计、流程优化、系统集成的角度分析
2. 提供具体可行的建议
3. 回复简洁，不超过200字
4. 不要重复已有的观点
"""

                # 元认知钩子 — 身份锚点检查（路径C门控）
                from lingflow.hooks.metacognition_hook import get_metacognition_hook

                meta_hook = get_metacognition_hook()
                prompt_with_anchor = meta_hook.inject_identity_anchor(prompt)
                logger.info("MetacognitionHook: injected identity anchor into discuss prompt")

                llm_messages = [{"role": "user", "content": prompt_with_anchor}]
                logger.info("准备调用LLM...")
                llm_response_tuple = call_llm_with_fallback(client, llm_messages)
                llm_response = llm_response_tuple[0] if isinstance(llm_response_tuple, tuple) else llm_response_tuple
                logger.info(f"LLM调用完成: {type(llm_response)}")

                # 提取LLM回复内容
                if hasattr(llm_response, 'choices') and len(llm_response.choices) > 0:
                    content = llm_response.choices[0].message.content
                else:
                    content = str(llm_response)

                # 元认知响应验证 — 检查身份问题回复是否包含身份锚点
                check = meta_hook.pre_response_check(prompt=prompt, proposed_response=content)
                if not check.passed:
                    logger.warning(
                        "MetacognitionHook: response failed identity check, prepending anchor. warnings=%s",
                        check.warnings,
                    )
                    content = f"[身份锚点] {meta_hook.identity_anchor}\n\n{content}"

                logger.info(f"LLM回复内容: {content[:100]}...")

                # 发送回复到讨论
                send_message(
                    topic=topic,
                    content=content,
                    from_id="lingtong"
                )

                logger.info(f"灵通已回复讨论: {topic[:30]}...")
                return {
                    "status": "success",
                    "action": "replied",
                    "discussion_id": discussion_id,
                    "topic": topic
                }

            except Exception as e:
                error_msg = f"处理讨论失败: {e}"
                logger.error(error_msg)
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {"status": "error", "message": error_msg, "traceback": traceback.format_exc()}

        return {"status": "ok", "message": "Notification received"}

    except Exception as e:
        error_msg = f"处理请求时出错: {e}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": error_msg, "traceback": traceback.format_exc()}

# ========== 技能系统 API ==========

@app.get("/api/v1/skills")
async def list_skills(
    category: Optional[str] = None,
    layer: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """列出所有技能"""
    from lingflow.core.layered_skill_loader import LayeredSkillLoader

    loader = LayeredSkillLoader()
    skills = loader.list_skills()

    # 过滤
    if category:
        skills = [s for s in skills if s.category == category]
    if layer:
        skills = [s for s in skills if s.layer == layer]

    return {
        "total": len(skills),
        "skills": [
            {
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "category": getattr(s, "category", "unknown"),
                "layer": getattr(s, "layer", "L1")
            }
            for s in skills
        ]
    }

@app.get("/api/v1/skills/{name}")
async def get_skill(
    name: str,
    api_key: str = Depends(verify_api_key)
):
    """获取技能详情"""
    from lingflow.core.layered_skill_loader import LayeredSkillLoader

    loader = LayeredSkillLoader()
    skill = loader.get_skill(name)

    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {name}")

    return {
        "name": skill.name,
        "description": skill.description,
        "version": skill.version,
        "category": getattr(skill, "category", "unknown"),
        "layer": getattr(skill, "layer", "L1"),
        "parameters": getattr(skill, "parameters", {})
    }

@app.post("/api/v1/skills/{name}/execute")
async def execute_skill(
    name: str,
    request: SkillExecutionRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """执行技能"""
    from lingflow.core.layered_skill_loader import LayeredSkillLoader
    import uuid

    # 生成任务 ID
    task_id = f"skill-{uuid.uuid4().hex[:8]}"

    # 异步执行
    async def run_skill():
        loader = LayeredSkillLoader()
        skill = loader.get_skill(name)

        if not skill:
            raise ValueError(f"Skill not found: {name}")

        result = skill.execute(request.params)
        # 结果持久化将在 v3.9.0 异步基础中实现
        # 参考: docs/architecture/ROADMAP_v3.9.0.md
        return result

    # 如果是同步模式，直接返回
    if not request.async_mode:
        try:
            result = await asyncio.wait_for(
                run_skill(),
                timeout=request.timeout
            )
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result
            }
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Execution timeout")

    # 异步模式，返回任务 ID
    background_tasks.add_task(run_skill)
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Skill execution started"
    }

# ========== 工作流系统 API ==========

@app.get("/api/v1/workflows")
async def list_workflows(
    type_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """列出所有工作流"""
    from lingflow.workflow.multi_workflow import MultiWorkflowCoordinator

    coordinator = MultiWorkflowCoordinator()
    workflows = coordinator.list_workflows()

    # 过滤
    if type_filter:
        workflows = [w for w in workflows if w.workflow_type == type_filter]
    if status_filter:
        workflows = [w for w in workflows if w.status == status_filter]

    return {
        "total": len(workflows),
        "workflows": [
            {
                "workflow_id": w.workflow_id if hasattr(w, "workflow_id") else w.name,
                "name": w.name if hasattr(w, "name") else w.workflow_id,
                "type": w.workflow_type.value if hasattr(w, "workflow_type") else "unknown",
                "status": w.status.value if hasattr(w, "status") else "unknown",
                "description": getattr(w, "description", "")
            }
            for w in workflows
        ]
    }

@app.post("/api/v1/workflows/{workflow_id}/run")
async def run_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
    api_key: str = Depends(verify_api_key)
):
    """执行工作流"""
    from lingflow.workflow.multi_workflow import MultiWorkflowCoordinator

    coordinator = MultiWorkflowCoordinator()

    result = coordinator.run_workflow(
        workflow_id=workflow_id,
        params=request.params,
        config=request.config or {},
        strategy=request.strategy
    )

    return {
        "task_id": getattr(result, "task_id", None),
        "status": getattr(result, "status", "unknown"),
        "result": result
    }

@app.get("/api/v1/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """获取任务状态"""
    from lingflow.workflow.multi_workflow import MultiWorkflowCoordinator

    coordinator = MultiWorkflowCoordinator()
    status = coordinator.get_workflow_status(task_id)

    return TaskStatusResponse(
        task_id=task_id,
        status=status.status.value if hasattr(status, "status") else "unknown",
        progress=getattr(status, "progress", 0.0),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

# ========== 代码审查 API ==========

@app.post("/api/v1/review")
async def review_code(
    request: CodeReviewRequest,
    api_key: str = Depends(verify_api_key)
):
    """代码审查"""
    from lingflow.code_review import BaseCodeReviewer as CodeReviewer

    reviewer = CodeReviewer()
    result = reviewer.review(
        target_path=request.target_path,
        dimensions=request.dimensions or [
            "complexity", "duplication", "security",
            "style", "docs", "tests", "performance", "errors"
        ]
    )

    if request.output_format == "json":
        return result.to_dict()
    elif request.output_format == "markdown":
        return {"markdown": result.to_markdown()}
    elif request.output_format == "html":
        return {"html": result.to_html()}

# ========== 情报系统 API ==========

@app.get("/api/v1/intelligence/github")
async def get_github_trends(
    keywords: str,
    language: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """GitHub 趋势（未实现）"""
    raise HTTPException(status_code=501, detail="GitHub intelligence not yet implemented")

@app.get("/api/v1/intelligence/npm")
async def get_npm_trends(
    keywords: str,
    api_key: str = Depends(verify_api_key)
):
    """npm 趋势（未实现）"""
    raise HTTPException(status_code=501, detail="npm intelligence not yet implemented")

# ========== 需求管理 API ==========

@app.get("/api/v1/requirements")
async def list_requirements(
    status: Optional[str] = None,
    category: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """列出需求"""
    from lingflow.requirements import RequirementsTraceability as RequirementManager

    manager = RequirementManager()
    requirements = manager.list_requirements(
        status=status,
        category=category
    )

    return {
        "total": len(requirements),
        "requirements": requirements
    }

@app.post("/api/v1/requirements")
async def create_requirement(
    title: str,
    description: str,
    priority: str = "normal",
    category: str = "feature",
    tags: Optional[List[str]] = None,
    api_key: str = Depends(verify_api_key)
):
    """创建需求"""
    from lingflow.requirements import RequirementsTraceability as RequirementManager

    manager = RequirementManager()
    requirement = manager.create_requirement(
        title=title,
        description=description,
        priority=priority,
        category=category,
        tags=tags or []
    )

    return requirement

@app.get("/api/v1/requirements/{requirement_id}")
async def get_requirement(
    requirement_id: str,
    api_key: str = Depends(verify_api_key)
):
    """获取需求详情"""
    from lingflow.requirements import RequirementsTraceability as RequirementManager

    manager = RequirementManager()
    requirement = manager.get_requirement(requirement_id)

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    return requirement

# ========== 启动配置 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8100,
        reload=True,
        log_level="info"
    )
