"""environment-manager 技能参数验证 - 使用 Pydantic 进行输入验证"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from pathlib import Path


class EnvironmentManagerParams(BaseModel):
    """环境配置管理器参数验证模型"""

    action: str = Field(
        default="detect",
        description="操作类型"
    )
    project_dir: str = Field(
        ...,
        min_length=1,
        description="项目目录路径"
    )
    env_file: Optional[str] = Field(
        None,
        description="环境文件路径"
    )
    config_type: Optional[str] = Field(
        None,
        description="配置类型（用于 validate 操作）"
    )
    output_format: str = Field(
        default="json",
        description="输出格式"
    )

    @validator('action')
    def validate_action(cls, v):
        """验证操作类型"""
        valid_actions = ['detect', 'generate', 'validate', 'audit']
        if v not in valid_actions:
            raise ValueError(f"action 必须是 {valid_actions} 之一，收到: {v}")
        return v

    @validator('project_dir')
    def validate_project_dir(cls, v):
        """验证项目目录路径"""
        path = Path(v)
        # 基本路径格式验证（不检查是否存在，因为在执行时才检查）
        if not str(v).strip():
            raise ValueError("project_dir 不能为空")
        return v

    @validator('config_type')
    def validate_config_type(cls, v):
        """验证配置类型"""
        if v is not None:
            valid_types = ['database', 'api', 'logging']
            if v not in valid_types:
                raise ValueError(f"config_type 必须是 {valid_types} 之一，收到: {v}")
        return v

    @validator('output_format')
    def validate_output_format(cls, v):
        """验证输出格式"""
        valid_formats = ['json', 'env', 'yaml']
        if v not in valid_formats:
            raise ValueError(f"output_format 必须是 {valid_formats} 之一，收到: {v}")
        return v

    @validator('config_type', pre=True, always=True)
    def validate_config_type_for_action(cls, v, values):
        """验证 validate 操作需要 config_type"""
        action = values.get('action')
        if action == 'validate' and not v:
            raise ValueError("当 action 为 'validate' 时，必须指定 config_type")
        return v

    class Config:
        """Pydantic 配置"""
        extra = 'allow'
        schema_extra = {
            'example': {
                'action': 'detect',
                'project_dir': './my-project',
                'env_file': '.env',
                'output_format': 'json'
            }
        }
