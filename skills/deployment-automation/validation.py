"""deployment-automation 技能参数验证 - 使用 Pydantic 进行输入验证"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any
from pathlib import Path


class DeploymentAutomationParams(BaseModel):
    """部署自动化参数验证模型"""

    action: str = Field(
        default="full",
        description="操作类型"
    )
    project_type: str = Field(
        default="python",
        description="项目类型"
    )
    app_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="应用名称"
    )
    port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="应用端口"
    )
    output_dir: str = Field(
        default="./deployment",
        description="输出目录"
    )
    deployment_strategy: str = Field(
        default="rolling",
        description="部署策略"
    )
    module_name: Optional[str] = Field(
        None,
        description="Python 模块名（用于 Python 项目）"
    )
    container_port: Optional[int] = Field(
        None,
        ge=1,
        le=65535,
        description="容器端口"
    )
    replicas: int = Field(
        default=3,
        ge=1,
        le=100,
        description="副本数量"
    )
    health_path: str = Field(
        default="/health",
        description="健康检查路径"
    )
    environment: str = Field(
        default="production",
        description="部署环境"
    )
    ci_platform: str = Field(
        default="gitlab",
        description="CI 平台"
    )
    max_revisions: int = Field(
        default=10,
        ge=1,
        le=50,
        description="最大版本数"
    )

    # 可选的复杂类型
    k8s_options: Optional[Dict[str, Any]] = Field(
        None,
        description="Kubernetes 选项"
    )
    env_vars: Optional[Dict[str, str]] = Field(
        None,
        description="环境变量"
    )
    config_data: Optional[Dict[str, str]] = Field(
        None,
        description="配置数据"
    )
    blue_green_options: Optional[Dict[str, Any]] = Field(
        None,
        description="蓝绿部署选项"
    )
    image_name: Optional[str] = Field(
        None,
        description="镜像名称"
    )

    @validator('action')
    def validate_action(cls, v):
        """验证操作类型"""
        valid_actions = [
            'generate_dockerfile', 'generate_k8s', 'blue_green_deploy',
            'rollback', 'generate_ci', 'full'
        ]
        if v not in valid_actions:
            raise ValueError(f"action 必须是 {valid_actions} 之一，收到: {v}")
        return v

    @validator('project_type')
    def validate_project_type(cls, v):
        """验证项目类型"""
        valid_types = ['python', 'nodejs', 'go', 'java', 'static']
        if v not in valid_types:
            raise ValueError(f"project_type 必须是 {valid_types} 之一，收到: {v}")
        return v

    @validator('app_name')
    def validate_app_name(cls, v):
        """验证应用名称符合 Kubernetes 命名规范"""
        import re
        # Kubernetes 命名规范：小写字母、数字、连字符，最多 63 字符
        if not re.match(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$', v):
            raise ValueError(
                f"app_name 必须符合 Kubernetes 命名规范："
                f"小写字母、数字、连字符，以字母或数字开头和结尾"
            )
        return v

    @validator('health_path')
    def validate_health_path(cls, v):
        """验证健康检查路径"""
        if not v.startswith('/'):
            raise ValueError(f"health_path 必须以 / 开头，收到: {v}")
        return v

    @validator('deployment_strategy')
    def validate_deployment_strategy(cls, v):
        """验证部署策略"""
        valid_strategies = ['rolling', 'blue_green', 'canary']
        if v not in valid_strategies:
            raise ValueError(f"deployment_strategy 必须是 {valid_strategies} 之一，收到: {v}")
        return v

    @validator('environment')
    def validate_environment(cls, v):
        """验证环境名称"""
        valid_environments = ['development', 'staging', 'production']
        if v not in valid_environments:
            raise ValueError(f"environment 必须是 {valid_environments} 之一，收到: {v}")
        return v

    @validator('ci_platform')
    def validate_ci_platform(cls, v):
        """验证 CI 平台"""
        valid_platforms = ['github', 'gitlab', 'jenkins']
        if v not in valid_platforms:
            raise ValueError(f"ci_platform 必须是 {valid_platforms} 之一，收到: {v}")
        return v

    @validator('container_port', pre=True, always=True)
    def set_container_port(cls, v, values):
        """如果未指定 container_port，使用 port 的值"""
        if v is None:
            return values.get('port', 8080)
        return v

    class Config:
        """Pydantic 配置"""
        extra = 'allow'
        schema_extra = {
            'example': {
                'action': 'full',
                'project_type': 'python',
                'app_name': 'myapp',
                'port': 8080,
                'output_dir': './deployment',
                'deployment_strategy': 'rolling',
                'replicas': 3
            }
        }
