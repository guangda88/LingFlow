"""api-doc-generator 技能参数验证 - 使用 Pydantic 进行输入验证"""

from pydantic import BaseModel, Field, validator
from typing import Optional


class APIDocParams(BaseModel):
    """API 文档生成器参数验证模型"""

    input: str = Field(..., min_length=1, description="输入文件或目录路径")
    output: Optional[str] = Field(None, description="输出文件路径")
    format: str = Field(
        default="yaml",
        description="输出格式 (yaml 或 json)"
    )
    framework: str = Field(
        default="auto",
        description="框架类型 (fastapi, flask, auto)"
    )
    title: str = Field(
        default="API Documentation",
        min_length=1,
        max_length=200,
        description="API 文档标题"
    )
    version: str = Field(
        default="1.0.0",
        description="API 版本号"
    )
    base_url: Optional[str] = Field(
        None,
        description="基础 URL"
    )

    @validator('format')
    def validate_format(cls, v):
        """验证输出格式"""
        valid_formats = ['yaml', 'json']
        if v not in valid_formats:
            raise ValueError(f"format 必须是 {valid_formats} 之一，收到: {v}")
        return v

    @validator('framework')
    def validate_framework(cls, v):
        """验证框架类型"""
        valid_frameworks = ['fastapi', 'flask', 'auto']
        if v not in valid_frameworks:
            raise ValueError(f"framework 必须是 {valid_frameworks} 之一，收到: {v}")
        return v

    @validator('version')
    def validate_version(cls, v):
        """验证版本号格式"""
        import re
        if not re.match(r'^\d+\.\d+\.\d+', v):
            raise ValueError(f"version 必须符合语义化版本格式 (x.y.z)，收到: {v}")
        return v

    @validator('base_url')
    def validate_base_url(cls, v):
        """验证基础 URL 格式"""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError(f"base_url 必须以 http:// 或 https:// 开头，收到: {v}")
        return v

    class Config:
        """Pydantic 配置"""
        extra = 'allow'  # 允许额外字段，保持向后兼容
        schema_extra = {
            'example': {
                'input': './my_app',
                'output': './api-docs/openapi.yaml',
                'format': 'yaml',
                'framework': 'auto',
                'title': 'My API Documentation',
                'version': '1.0.0',
                'base_url': 'https://api.example.com'
            }
        }
