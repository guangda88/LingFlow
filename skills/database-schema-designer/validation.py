"""database-schema-designer 技能参数验证 - 使用 Pydantic 进行输入验证"""

from pydantic import BaseModel, Field, validator
from typing import Optional


class DatabaseSchemaParams(BaseModel):
    """数据库架构设计器参数验证模型"""

    requirement: str = Field(
        ...,
        min_length=1,
        description="业务需求描述文本"
    )
    database_type: str = Field(
        default="mysql",
        description="数据库类型"
    )
    naming_convention: str = Field(
        default="snake_case",
        description="命名约定"
    )
    include_timestamps: bool = Field(
        default=True,
        description="是否包含时间戳字段"
    )
    include_soft_delete: bool = Field(
        default=False,
        description="是否包含软删除字段"
    )

    @validator('database_type')
    def validate_database_type(cls, v):
        """验证数据库类型"""
        valid_types = ['mysql', 'postgresql', 'sqlite', 'mssql', 'oracle']
        if v.lower() not in valid_types:
            raise ValueError(f"database_type 必须是 {valid_types} 之一，收到: {v}")
        return v.lower()

    @validator('naming_convention')
    def validate_naming_convention(cls, v):
        """验证命名约定"""
        valid_conventions = ['snake_case', 'camelCase', 'PascalCase']
        if v not in valid_conventions:
            raise ValueError(f"naming_convention 必须是 {valid_conventions} 之一，收到: {v}")
        return v

    @validator('requirement')
    def validate_requirement(cls, v):
        """验证需求描述不为空且不只有空白字符"""
        if not v.strip():
            raise ValueError("requirement 不能为空或只包含空白字符")
        return v

    class Config:
        """Pydantic 配置"""
        extra = 'allow'
        schema_extra = {
            'example': {
                'requirement': '设计一个电商系统，包含用户、订单、产品实体',
                'database_type': 'mysql',
                'naming_convention': 'snake_case',
                'include_timestamps': True,
                'include_soft_delete': False
            }
        }
