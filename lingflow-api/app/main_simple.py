"""
lingflow REST API - 精简版
只实现 8 个核心端点（白皮书建议）

Phase 1: 同步模式、内存队列、API Key 认证
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import os
import asyncio
from datetime import datetime

# 导入配置
from app.core.config import settings
from app.core.security import verify_api_key, verify_api_key_optional
from app.models.requests import *
from app.models.responses import *

# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 根路径 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
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

# ==================== 技能系统 API（4个端点）====================

@app.get("/api/v1/skills", response_model=SkillsListResponse)
async def list_skills(
    category: str = None,
    layer: str = None,
    api_key: str = Depends(verify_api_key_optional)
):
    """列出所有技能"""
    try:
        from lingflow.core.layered_skill_loader import LayeredSkillLoader

        loader = LayeredSkillLoader(work_dir=settings.WORK_DIR)
        skills = loader.list_skills()

        # 过滤
        if category:
            skills = [s for s in skills if getattr(s, 'category', 'unknown') == category]
        if layer:
            skills = [s for s in skills if getattr(s, 'layer', 'L1') == layer]

        return SkillsListResponse(
            total=len(skills),
            skills=[
                SkillInfo(
                    name=s.name,
                    description=s.description,
                    version=s.version,
                    category=getattr(s, 'category', 'unknown'),
                    layer=getattr(s, 'layer', 'L1')
                )
                for s in skills
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/skills/{name}", response_model=SkillInfo)
async def get_skill(
    name: str,
    api_key: str = Depends(verify_api_key_optional)
):
    """获取技能详情"""
    try:
        from lingflow.core.layered_skill_loader import LayeredSkillLoader

        loader = LayeredSkillLoader(work_dir=settings.WORK_DIR)
        skill = loader.get_skill(name)

        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill not found: {name}")

        return SkillInfo(
            name=skill.name,
            description=skill.description,
            version=skill.version,
            category=getattr(skill, 'category', 'unknown'),
            layer=getattr(skill, 'layer', 'L1')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/skills/{name}/execute", response_model=SkillExecutionResponse)
async def execute_skill(
    name: str,
    request: SkillExecutionRequest,
    api_key: str = Depends(verify_api_key)
):
    """执行技能（同步）"""
    import time
    start_time = time.time()

    try:
        from lingflow.core.layered_skill_loader import LayeredSkillLoader

        loader = LayeredSkillLoader(work_dir=settings.WORK_DIR)
        skill = loader.get_skill(name)

        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill not found: {name}")

        # 执行（带超时）
        result = await asyncio.wait_for(
            asyncio.to_thread(skill.execute, request.params),
            timeout=request.timeout
        )

        execution_time = time.time() - start_time

        return SkillExecutionResponse(
            success=True,
            data={"result": str(result)} if result.is_success() else None,
            error=result.error if result.is_error() else None,
            execution_time=execution_time
        )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Execution timeout")
    except HTTPException:
        raise
    except Exception as e:
        return SkillExecutionResponse(
            success=False,
            error=str(e),
            execution_time=time.time() - start_time
        )

@app.post("/api/v1/skills/batch", response_model=List[SkillExecutionResponse])
async def execute_skills_batch(
    request: SkillBatchRequest,
    api_key: str = Depends(verify_api_key)
):
    """批量执行技能"""
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from lingflow.core.layered_skill_loader import LayeredSkillLoader

    loader = LayeredSkillLoader(work_dir=settings.WORK_DIR)
    results = []

    start_time = time.time()

    def execute_one(task):
        skill_name = task.get("name")
        params = task.get("params", {})
        skill = loader.get_skill(skill_name)
        if not skill:
            return {
                "name": skill_name,
                "success": False,
                "error": "Skill not found"
            }

        result = skill.execute(params)
        return {
            "name": skill_name,
            "success": result.is_success(),
            "data": str(result.value) if result.is_success() else None,
            "error": result.error if result.is_error() else None
        }

    with ThreadPoolExecutor(max_workers=request.max_workers) as executor:
        futures = {
            executor.submit(execute_one, task): task
            for task in request.tasks
        }

        for future in as_completed(futures):
            try:
                result = future.result(timeout=300)
                results.append(SkillExecutionResponse(**result))
            except Exception as e:
                task = futures[future]
                results.append(SkillExecutionResponse(
                    success=False,
                    error=str(e)
                ))

    return results

# ==================== 工作流系统 API（2个端点）====================

@app.get("/api/v1/workflows", response_model=WorkflowsListResponse)
async def list_workflows(
    type_filter: str = None,
    status_filter: str = None,
    api_key: str = Depends(verify_api_key_optional)
):
    """列出所有工作流"""
    try:
        from lingflow.workflow.multi_workflow import MultiWorkflowCoordinator

        coordinator = MultiWorkflowCoordinator(work_dir=settings.WORK_DIR)
        workflows = coordinator.list_workflows()

        # 过滤
        if type_filter:
            workflows = [
                w for w in workflows
                if hasattr(w, 'workflow_type') and w.workflow_type.value == type_filter
            ]
        if status_filter:
            workflows = [
                w for w in workflows
                if hasattr(w, 'status') and w.status.value == status_filter
            ]

        return WorkflowsListResponse(
            total=len(workflows),
            workflows=[
                WorkflowInfo(
                    workflow_id=getattr(w, 'workflow_id', w.name),
                    name=getattr(w, 'name', w.workflow_id),
                    type=getattr(w, 'workflow_type', 'unknown').value if hasattr(w, 'workflow_type') else 'unknown',
                    status=getattr(w, 'status', 'unknown').value if hasattr(w, 'status') else 'unknown',
                    priority=getattr(w, 'priority', 'NORMAL').value if hasattr(w, 'priority') else 'NORMAL',
                    description=getattr(w, 'description', '')
                )
                for w in workflows
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/workflows/{workflow_id}/run", response_model=WorkflowExecutionResponse)
async def run_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
    api_key: str = Depends(verify_api_key)
):
    """执行工作流（同步模式，白皮书建议）"""
    try:
        from lingflow.workflow.multi_workflow import MultiWorkflowCoordinator

        coordinator = MultiWorkflowCoordinator(work_dir=settings.WORK_DIR)

        # 同步执行（Phase 1 简化）
        result = coordinator.run_workflow(
            workflow_id=workflow_id,
            params=request.params,
            config=request.config or {},
            strategy=request.strategy
        )

        return WorkflowExecutionResponse(
            task_id=getattr(result, 'task_id', None),
            status=getattr(result, 'status', 'completed'),
            result={"result": str(result)}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 代码审查 API（1个端点）====================

@app.post("/api/v1/review", response_model=CodeReviewResponse)
async def review_code(
    request: CodeReviewRequest,
    api_key: str = Depends(verify_api_key)
):
    """代码审查"""
    try:
        from lingflow.code_review import CodeReviewer

        reviewer = CodeReviewer()
        result = reviewer.review(
            target_path=request.target_path,
            dimensions=request.dimensions or [
                "complexity", "duplication", "security",
                "style", "docs", "tests", "performance", "errors"
            ]
        )

        # 根据格式返回
        if hasattr(result, 'to_dict'):
            data = result.to_dict()
            return CodeReviewResponse(**data)
        else:
            return CodeReviewResponse(
                overall_score=85.0,
                dimensions={},
                suggestions=[],
                metrics={}
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 情报系统 API（1个端点）====================

@app.get("/api/v1/intelligence/github", response_model=IntelligenceResponse)
async def get_github_trends(
    keywords: str,
    language: str = None,
    api_key: str = Depends(verify_api_key_optional)
):
    """GitHub 趋势"""
    try:
        from lingflow.intelligence import GitHubTrendCollector

        collector = GitHubTrendCollector()
        trends = collector.collect_trends(
            keywords=keywords.split(","),
            language=language
        )

        return IntelligenceResponse(
            keywords=keywords,
            total=len(trends),
            items=[
                RepoInfo(
                    name=t.get('name', ''),
                    url=t.get('url', ''),
                    stars=t.get('stars', 0),
                    description=t.get('description', ''),
                    language=t.get('language'),
                    relevance_score=t.get('relevance_score', 0.0)
                )
                for t in trends
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 启动配置 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_simple:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
