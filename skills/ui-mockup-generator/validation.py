"""ui-mockup-generator 技能参数验证 - 使用 Pydantic 进行输入验证"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any


class UIComponentSpec(BaseModel):
    """UI 组件规格"""
    type: str = Field(..., description="组件类型")
    props: Dict[str, Any] = Field(default_factory=dict, description="组件属性")


class UIMockupParams(BaseModel):
    """UI 原型生成器参数验证模型"""

    requirement: str = Field(
        ...,
        min_length=1,
        description="需求描述（自然语言）"
    )
    components: Optional[List[UIComponentSpec]] = Field(
        None,
        description="组件列表（可选，如未提供则从需求解析）"
    )
    theme: str = Field(
        default="default",
        description="主题名称"
    )
    responsive: bool = Field(
        default=True,
        description="是否生成响应式样式"
    )
    title: str = Field(
        default="UI Mockup",
        min_length=1,
        max_length=200,
        description="页面标题"
    )
    output_dir: Optional[str] = Field(
        None,
        description="输出目录路径"
    )

    @validator('theme')
    def validate_theme(cls, v):
        """验证主题名称"""
        valid_themes = ['default', 'dark', 'nature', 'sunset']
        if v not in valid_themes:
            raise ValueError(f"theme 必须是 {valid_themes} 之一，收到: {v}")
        return v

    @validator('components')
    def validate_components(cls, v):
        """验证组件列表"""
        if v is not None:
            valid_component_types = [
                'button', 'input', 'card', 'navbar', 'form',
                'grid', 'hero', 'table', 'modal', 'footer'
            ]
            for component in v:
                if component.type not in valid_component_types:
                    raise ValueError(
                        f"不支持的组件类型: {component.type}。"
                        f"支持的类型: {valid_component_types}"
                    )
        return v

    @validator('title')
    def validate_title(cls, v):
        """验证标题不包含特殊字符"""
        import re
        # 检查是否有潜在危险的 HTML/JS 字符
        if '<script' in v.lower() or 'javascript:' in v.lower():
            raise ValueError("标题不能包含脚本标签或 javascript: 协议")
        return v

    class Config:
        """Pydantic 配置"""
        extra = 'allow'
        schema_extra = {
            'example': {
                'requirement': 'Create a login page with navbar and hero section',
                'theme': 'default',
                'responsive': True,
                'title': 'Login Page',
                'output_dir': './output'
            }
        }
