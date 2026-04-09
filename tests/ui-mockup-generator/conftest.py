"""Fixtures for ui-mockup-generator tests"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Import the ui-mockup-generator module (directory has hyphens so can't use normal import)
spec = importlib.util.spec_from_file_location(
    "ui_mockup_generator", Path(__file__).parent.parent.parent / "skills" / "ui-mockup-generator" / "implementation.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules["ui_mockup_generator"] = module
spec.loader.exec_module(module)

# Make module functions available to tests
generate_mockup = module.generate_mockup
parse_requirements = module.parse_requirements
extract_component_props = module.extract_component_props
generate_html = module.generate_html
generate_css = module.generate_css
render_component = module.render_component
save_mockup = module.save_mockup
execute_skill = module.execute_skill
COMPONENT_TEMPLATES = module.COMPONENT_TEMPLATES
COLOR_THEMES = module.COLOR_THEMES
RESPONSIVE_BREAKPOINTS = module.RESPONSIVE_BREAKPOINTS

from typing import Any, Dict, List


@pytest.fixture
def mock_requirement_simple():
    """Simple requirement with one component"""
    return "Create a navbar with brand MyApp"


@pytest.fixture
def mock_requirement_complex():
    """Complex requirement with multiple components"""
    return """Create a landing page with:
    - A navbar with brand TechStartup and links: Home, Products, Pricing, Contact
    - A hero section with title 'Transform Your Business' and subtitle 'AI-powered solutions'
    - A 3-column grid layout for features
    - A contact form with fields: Name, Email, Message
    """


@pytest.fixture
def mock_requirement_chinese():
    """Requirement in Chinese"""
    return "创建一个包含导航栏和卡片组件的页面，品牌是'我的应用'"


@pytest.fixture
def mock_components_list():
    """Predefined components list"""
    return [
        {"type": "navbar", "props": {"brand": "TestApp", "links": ["Home", "About"]}},
        {"type": "hero", "props": {"title": "Welcome", "subtitle": "Get Started"}},
        {"type": "button", "props": {"text": "Click Me", "style": "primary"}},
    ]


@pytest.fixture
def mock_component_button():
    """Button component"""
    return {"type": "button", "props": {"text": "Submit", "style": "primary"}}


@pytest.fixture
def mock_component_card():
    """Card component"""
    return {"type": "card", "props": {"title": "Test Card", "content": "Test Content"}}


@pytest.fixture
def mock_component_form():
    """Form component"""
    return {"type": "form", "props": {"fields": ["Name", "Email", "Password"], "submit_text": "Sign Up"}}


@pytest.fixture
def mock_component_grid():
    """Grid component"""
    return {"type": "grid", "props": {"columns": 4, "item_count": 8}}


@pytest.fixture
def mock_component_table():
    """Table component"""
    return {"type": "table", "props": {"headers": ["ID", "Name", "Status", "Date"], "row_count": 5}}


@pytest.fixture
def mock_component_modal():
    """Modal component"""
    return {"type": "modal", "props": {"id": "testModal", "title": "Test Modal"}}


@pytest.fixture
def mock_component_navbar():
    """Navbar component"""
    return {"type": "navbar", "props": {"brand": "BrandName", "links": ["Home", "About", "Services", "Contact"]}}


@pytest.fixture
def mock_component_footer():
    """Footer component"""
    return {"type": "footer", "props": {"company": "Test Inc."}}


@pytest.fixture
def mock_params_basic():
    """Basic mockup generation parameters"""
    return {"requirement": "Create a simple navbar", "theme": "default", "responsive": True, "title": "Test Mockup"}


@pytest.fixture
def mock_params_with_components():
    """Parameters with predefined components"""
    return {
        "components": [{"type": "button", "props": {"text": "Click Me", "style": "primary"}}],
        "theme": "dark",
        "responsive": False,
        "title": "Dark Theme Test",
    }


@pytest.fixture
def mock_output_dir(tmp_path):
    """Temporary output directory"""
    return str(tmp_path / "mockup_output")


@pytest.fixture
def expected_html_structure():
    """Expected HTML structure elements"""
    return {
        "doctype": "<!DOCTYPE html>",
        "html_tag": '<html lang="zh-CN">',
        "head_tag": "<head>",
        "body_tag": "<body>",
        "charset": '<meta charset="UTF-8">',
        "viewport": '<meta name="viewport"',
    }


@pytest.fixture
def expected_css_elements():
    """Expected CSS elements"""
    return {"reset": "/* CSS Reset */", "box_sizing": "box-sizing: border-box", "body_font": "font-family"}


@pytest.fixture
def all_component_types():
    """All supported component types"""
    return ["button", "input", "card", "navbar", "form", "grid", "hero", "table", "modal", "footer"]


@pytest.fixture
def all_theme_names():
    """All available theme names"""
    return ["default", "dark", "nature", "sunset"]


@pytest.fixture
def responsive_breakpoints():
    """Responsive breakpoints configuration"""
    return {"mobile": "576px", "tablet": "768px", "desktop": "1024px", "wide": "1200px"}


@pytest.fixture
def theme_colors():
    """Expected theme color structures"""
    return {
        "default": {"primary": "#007bff", "secondary": "#6c757d", "success": "#28a745", "danger": "#dc3545"},
        "dark": {"primary": "#0d6efd", "background": "#1a1a1a", "text": "#f8f9fa"},
    }


@pytest.fixture
def component_keywords_mapping():
    """Component keyword mappings for requirement parsing"""
    return {
        "navbar": ["导航", "navbar", "导航栏", "header", "页头"],
        "hero": ["hero", "首屏", "banner", "横幅", "主区域"],
        "card": ["card", "卡片", "信息卡"],
        "form": ["form", "表单", "登录", "注册", "输入", "submit"],
        "button": ["button", "按钮", "btn", "点击"],
        "input": ["input", "输入框", "文本框", "表单项"],
        "table": ["table", "表格", "列表"],
        "grid": ["grid", "网格", "布局"],
        "modal": ["modal", "弹窗", "对话框", "popup"],
        "footer": ["footer", "页脚", "底部"],
    }
