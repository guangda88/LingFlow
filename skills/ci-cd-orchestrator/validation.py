"""ci-cd-orchestrator 技能参数验证 - 使用 Pydantic 进行输入验证"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any


class CICDOrchestratorParams(BaseModel):
    """CI/CD 流水线编排器参数验证模型"""

    action: str = Field(
        default="generate",
        description="操作类型"
    )
    platform: str = Field(
        default="github",
        description="CI/CD 平台"
    )
    language: str = Field(
        default="python",
        description="编程语言"
    )
    stages: Optional[List[str]] = Field(
        default=['test', 'build'],
        description="要启用的阶段"
    )
    deploy_target: Optional[str] = Field(
        None,
        description="部署目标"
    )
    output_file: Optional[str] = Field(
        None,
        description="输出文件路径"
    )
    config_path: Optional[str] = Field(
        None,
        description="配置文件路径（用于 validate 操作）"
    )
    custom_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="自定义配置"
    )

    @validator('action')
    def validate_action(cls, v):
        """验证操作类型"""
        valid_actions = ['generate', 'validate', 'list', 'help']
        if v not in valid_actions:
            raise ValueError(f"action 必须是 {valid_actions} 之一，收到: {v}")
        return v

    @validator('platform')
    def validate_platform(cls, v):
        """验证 CI/CD 平台"""
        valid_platforms = ['github', 'jenkins', 'gitlab', 'azure', 'circleci']
        if v not in valid_platforms:
            raise ValueError(f"platform 必须是 {valid_platforms} 之一，收到: {v}")
        return v

    @validator('language')
    def validate_language(cls, v):
        """验证编程语言"""
        valid_languages = ['python', 'javascript', 'go', 'rust', 'java']
        if v not in valid_languages:
            raise ValueError(f"language 必须是 {valid_languages} 之一，收到: {v}")
        return v

    @validator('stages')
    def validate_stages(cls, v):
        """验证阶段列表"""
        if v is not None:
            valid_stages = ['test', 'build', 'deploy']
            for stage in v:
                if stage not in valid_stages:
                    raise ValueError(f"stage 必须是 {valid_stages} 之一，收到: {stage}")
        return v

    @validator('deploy_target')
    def validate_deploy_target(cls, v):
        """验证部署目标"""
        if v is not None:
            valid_targets = ['docker', 'kubernetes', 'serverless', 'static']
            if v not in valid_targets:
                raise ValueError(f"deploy_target 必须是 {valid_targets} 之一，收到: {v}")
        return v

    @validator('stages', pre=True)
    def validate_deploy_stage_consistency(cls, v, values):
        """验证 deploy 阶段需要 deploy_target"""
        if v and 'deploy' in v:
            deploy_target = values.get('deploy_target')
            if not deploy_target:
                raise ValueError("当 stages 包含 'deploy' 时，必须指定 deploy_target")
        return v

    class Config:
        """Pydantic 配置"""
        extra = 'allow'
        schema_extra = {
            'example': {
                'action': 'generate',
                'platform': 'github',
                'language': 'python',
                'stages': ['test', 'build', 'deploy'],
                'deploy_target': 'docker',
                'output_file': '.github/workflows/ci.yml'
            }
        }
