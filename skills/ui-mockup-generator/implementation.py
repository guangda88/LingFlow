"""ui-mockup-generator 技能实现 - 从需求描述生成 HTML/CSS UI 原型

支持两种样式模式:
    - 传统 CSS: 内联样式表
    - Tailwind CSS: 使用 Tailwind CDN 和工具类

异常处理:
    - UIMockupError: UI 原型生成相关错误
    - ValueError: 组件类型或参数无效
    - (IOError, OSError): 文件读写错误
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入自定义异常
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from exceptions import UIMockupError

# 导入 Tailwind CSS 支持
try:
    from .tailwind_components import (
        TAILWIND_COMPONENTS,
        TAILWIND_THEMES,
        generate_tailwind_head,
        generate_tailwind_end,
        render_button_tailwind,
        render_input_tailwind,
        render_card_tailwind,
        render_navbar_tailwind,
        render_hero_tailwind,
        render_form_tailwind,
        render_grid_tailwind,
        render_table_tailwind,
        render_modal_tailwind,
        render_footer_tailwind,
    )
    TAILWIND_AVAILABLE = True
except ImportError:
    try:
        # 尝试直接导入（用于独立运行）
        from tailwind_components import (
            TAILWIND_COMPONENTS,
            TAILWIND_THEMES,
            generate_tailwind_head,
            generate_tailwind_end,
            render_button_tailwind,
            render_input_tailwind,
            render_card_tailwind,
            render_navbar_tailwind,
            render_hero_tailwind,
            render_form_tailwind,
            render_grid_tailwind,
            render_table_tailwind,
            render_modal_tailwind,
            render_footer_tailwind,
        )
        TAILWIND_AVAILABLE = True
    except ImportError:
        TAILWIND_AVAILABLE = False
        logger = logging.getLogger(__name__)
        logger.warning("Tailwind CSS 组件不可用，将仅使用传统 CSS")

# 导入 Pydantic 验证模型
try:
    from pydantic import ValidationError as PydanticValidationError
    from .validation import UIMockupParams
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============== 常量配置 ==============

# UI 组件模板库
COMPONENT_TEMPLATES = {
    'button': {
        'html': '<button class="btn {style}">{text}</button>',
        'styles': {
            'primary': '.btn.primary { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }',
            'secondary': '.btn.secondary { background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }',
            'outline': '.btn.outline { background: transparent; border: 1px solid #007bff; color: #007bff; padding: 10px 20px; border-radius: 4px; cursor: pointer; }'
        }
    },
    'input': {
        'html': '<input type="{type}" class="form-input" placeholder="{placeholder}">',
        'styles': {
            'default': '.form-input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }'
        }
    },
    'card': {
        'html': '''<div class="card">
    <div class="card-header">
        <h3>{title}</h3>
    </div>
    <div class="card-body">
        {content}
    </div>
</div>''',
        'styles': {
            'default': '''.card { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }
.card-header { background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }
.card-header h3 { margin: 0; font-size: 18px; }
.card-body { padding: 15px; }'''
        }
    },
    'navbar': {
        'html': '''<nav class="navbar">
    <div class="nav-brand">{brand}</div>
    <ul class="nav-links">
        {links}
    </ul>
</nav>''',
        'styles': {
            'default': '''.navbar { display: flex; justify-content: space-between; align-items: center; padding: 15px 30px; background: #333; color: white; }
.nav-brand { font-size: 20px; font-weight: bold; }
.nav-links { display: flex; list-style: none; gap: 20px; margin: 0; padding: 0; }
.nav-links a { color: white; text-decoration: none; }
.nav-links a:hover { opacity: 0.8; }'''
        }
    },
    'form': {
        'html': '''<form class="form">
    {fields}
    <button type="submit" class="btn primary">{submit_text}</button>
</form>''',
        'styles': {
            'default': '''.form { max-width: 400px; margin: 20px auto; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
.form-input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }'''
        }
    },
    'grid': {
        'html': '''<div class="grid" style="grid-template-columns: repeat({columns}, 1fr);">
    {items}
</div>''',
        'styles': {
            'default': '''.grid { display: grid; gap: 20px; }
.grid-item { padding: 20px; background: #f8f9fa; border-radius: 4px; }'''
        }
    },
    'hero': {
        'html': '''<section class="hero">
    <h1>{title}</h1>
    <p class="hero-subtitle">{subtitle}</p>
    <div class="hero-actions">
        {actions}
    </div>
</section>''',
        'styles': {
            'default': '''.hero { text-align: center; padding: 80px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.hero h1 { font-size: 48px; margin-bottom: 20px; }
.hero-subtitle { font-size: 20px; margin-bottom: 30px; opacity: 0.9; }
.hero-actions { display: flex; gap: 15px; justify-content: center; }'''
        }
    },
    'table': {
        'html': '''<table class="table">
    <thead>
        <tr>{headers}</tr>
    </thead>
    <tbody>
        {rows}
    </tbody>
</table>''',
        'styles': {
            'default': '''.table { width: 100%; border-collapse: collapse; }
.table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
.table th { background: #f8f9fa; font-weight: 600; }
.table tr:hover { background: #f8f9fa; }'''
        }
    },
    'modal': {
        'html': '''<div class="modal" id="{id}">
    <div class="modal-overlay"></div>
    <div class="modal-content">
        <div class="modal-header">
            <h3>{title}</h3>
            <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
            {content}
        </div>
    </div>
</div>''',
        'styles': {
            'default': '''.modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 1000; }
.modal.active { display: flex; align-items: center; justify-content: center; }
.modal-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
.modal-content { position: relative; background: white; border-radius: 8px; max-width: 500px; width: 90%; z-index: 1001; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 15px; border-bottom: 1px solid #ddd; }
.modal-close { background: none; border: none; font-size: 24px; cursor: pointer; }
.modal-body { padding: 15px; }'''
        }
    },
    'footer': {
        'html': '''<footer class="footer">
    <div class="footer-content">
        <p>&copy; {year} {company}. All rights reserved.</p>
    </div>
</footer>''',
        'styles': {
            'default': '''.footer { background: #333; color: white; padding: 30px; text-align: center; margin-top: 50px; }'''
        }
    }
}

# 颜色主题
COLOR_THEMES = {
    'default': {
        'primary': '#007bff',
        'secondary': '#6c757d',
        'success': '#28a745',
        'danger': '#dc3545',
        'background': '#ffffff',
        'text': '#333333'
    },
    'dark': {
        'primary': '#0d6efd',
        'secondary': '#6c757d',
        'success': '#198754',
        'danger': '#dc3545',
        'background': '#1a1a1a',
        'text': '#f8f9fa'
    },
    'nature': {
        'primary': '#2d6a4f',
        'secondary': '#52b788',
        'success': '#40916c',
        'danger': '#e63946',
        'background': '#f0f7f4',
        'text': '#1b4332'
    },
    'sunset': {
        'primary': '#f77f00',
        'secondary': '#fcbf49',
        'success': '#2a9d8f',
        'danger': '#e63946',
        'background': '#fff8e7',
        'text': '#264653'
    }
}

# 响应式断点
RESPONSIVE_BREAKPOINTS = {
    'mobile': '576px',
    'tablet': '768px',
    'desktop': '1024px',
    'wide': '1200px'
}


def generate_mockup(params: Dict) -> Dict:
    """生成 UI 原型

    Args:
        params: 生成参数，包含:
            - requirement: 需求描述 (自然语言)
            - components: 组件列表 (可选，如未提供则从需求解析)
            - theme: 主题名称 (可选，默认 'default')
            - responsive: 是否响应式 (默认 True)
            - title: 页面标题 (默认 'UI Mockup')
            - use_tailwind: 是否使用 Tailwind CSS (默认 False)
            - output_dir: 输出目录 (可选)

    Returns:
        生成结果字典，包含:
            - html: 生成的 HTML 代码
            - css: 生成的 CSS 代码 (Tailwind 模式下为空)
            - components_used: 使用的组件列表
            - metadata: 元数据 (包含使用的技术栈)

    Raises:
        UIMockupError: UI 原型生成过程中的错误
        ValueError: 参数无效时
    """
    requirement = params.get('requirement', '')
    components = params.get('components', [])
    theme = params.get('theme', 'default')
    responsive = params.get('responsive', True)
    title = params.get('title', 'UI Mockup')
    use_tailwind = params.get('use_tailwind', False)
    output_dir = params.get('output_dir', None)

    # 检查 Tailwind 可用性
    if use_tailwind and not TAILWIND_AVAILABLE:
        logger.warning("Tailwind CSS 不可用，回退到传统 CSS")
        use_tailwind = False

    # 验证 requirement 参数
    if not components:
        if not requirement or not requirement.strip():
            # 使用默认组件而不是抛出错误
            requirement = 'navbar and hero'

    # 验证主题
    if use_tailwind:
        valid_themes = list(TAILWIND_THEMES.keys()) if TAILWIND_AVAILABLE else []
    else:
        valid_themes = list(COLOR_THEMES.keys())

    if theme not in valid_themes:
        raise ValueError(f'不支持的主题: {theme}. 支持的主题: {valid_themes}')

    # 解析需求获取组件
    if not components:
        components = parse_requirements(requirement)

    # 根据 use_tailwind 选择生成方式
    if use_tailwind:
        html_content = generate_html_tailwind(title, components, theme, responsive)
        css_content = ''  # Tailwind 模式不需要独立 CSS
        tech_stack = 'Tailwind CSS (CDN)'
    else:
        html_content = generate_html(title, components, theme)
        css_content = generate_css(components, theme, responsive)
        tech_stack = 'Traditional CSS'

    return {
        'html': html_content,
        'css': css_content,
        'components_used': components,
        'metadata': {
            'theme': theme,
            'responsive': responsive,
            'tech_stack': tech_stack,
            'generated_at': datetime.now().isoformat()
        }
    }


def parse_requirements(requirement: str) -> List[Dict]:
    """解析自然语言需求，提取组件列表

    Args:
        requirement: 自然语言需求描述

    Returns:
        组件列表，每个组件包含 type 和 props
    """
    if requirement is None:
        requirement = ''

    components = []
    requirement_lower = requirement.lower()

    # 关键词到组件的映射
    component_keywords = {
        'navbar': ['导航', 'navbar', '导航栏', 'header', '页头'],
        'hero': ['hero', '首屏', 'banner', '横幅', '主区域'],
        'card': ['card', '卡片', '信息卡'],
        'form': ['form', '表单', '登录', '注册', '输入', 'submit'],
        'button': ['button', '按钮', 'btn', '点击'],
        'input': ['input', '输入框', '文本框', '表单项'],
        'table': ['table', '表格', '列表'],
        'grid': ['grid', '网格', '布局'],
        'modal': ['modal', '弹窗', '对话框', 'popup'],
        'footer': ['footer', '页脚', '底部']
    }

    # 检测组件
    for component_type, keywords in component_keywords.items():
        if any(keyword in requirement_lower for keyword in keywords):
            props = extract_component_props(requirement, component_type)
            components.append({'type': component_type, 'props': props})

    # 如果没有检测到任何组件，添加默认组件
    if not components:
        components = [
            {'type': 'navbar', 'props': {'brand': 'MyApp', 'links': ['Home', 'About', 'Contact']}},
            {'type': 'hero', 'props': {'title': 'Welcome', 'subtitle': 'Get started with our app'}}
        ]

    return components


def extract_component_props(requirement: str, component_type: str) -> Dict:
    """从需求中提取组件属性

    Args:
        requirement: 需求描述
        component_type: 组件类型

    Returns:
        组件属性字典
    """
    props = {}

    if component_type == 'navbar':
        # 提取品牌名称
        brand_match = re.search(r'(?:brand|品牌|标题)\s*[:：]?\s*["\']?([^"\'\n,]+)', requirement)
        props['brand'] = brand_match.group(1) if brand_match else 'MyApp'

        # 提取导航链接
        links_match = re.search(r'(?:links?|链接|导航)\s*[:：]?\s*\[?([^\]]+)\]?', requirement)
        if links_match:
            links_text = links_match.group(1)
            props['links'] = [l.strip().strip('"\'') for l in links_text.split(',')]
        else:
            props['links'] = ['Home', 'About', 'Contact']

    elif component_type == 'hero':
        # 提取标题
        title_match = re.search(r'(?:title|标题|主标题)\s*[:：]?\s*["\']?([^"\'\n]+)', requirement)
        props['title'] = title_match.group(1).strip() if title_match else 'Welcome to Our App'

        # 提取副标题
        subtitle_match = re.search(r'(?:subtitle|副标题|描述)\s*[:：]?\s*["\']?([^"\'\n]+)', requirement)
        props['subtitle'] = subtitle_match.group(1).strip() if subtitle_match else 'Build amazing things with us'

    elif component_type == 'button':
        # 提取按钮文本和样式
        text_match = re.search(r'(?:button|按钮)\s*(?:text|文本)?\s*[:：]?\s*["\']?([^"\'\n]+)', requirement)
        props['text'] = text_match.group(1).strip() if text_match else 'Click Me'

        # 检测按钮样式
        if 'primary' in requirement.lower() or '主要' in requirement:
            props['style'] = 'primary'
        elif 'outline' in requirement.lower():
            props['style'] = 'outline'
        else:
            props['style'] = 'secondary'

    elif component_type == 'card':
        # 提取卡片标题
        title_match = re.search(r'(?:card|卡片).*?(?:title|标题)\s*[:：]?\s*["\']?([^"\'\n]+)', requirement)
        props['title'] = title_match.group(1).strip() if title_match else 'Card Title'

        # 提取卡片内容
        content_match = re.search(r'(?:card|卡片).*?(?:content|内容)\s*[:：]?\s*["\']?([^"\'\n]+)', requirement)
        props['content'] = content_match.group(1).strip() if content_match else 'This is the card content.'

    elif component_type == 'form':
        # 提取表单字段
        fields_match = re.search(r'(?:form|表单).*?(?:fields?|字段)\s*[:：]?\s*\[?([^\]]+)\]?', requirement)
        if fields_match:
            fields_text = fields_match.group(1)
            props['fields'] = [f.strip().strip('"\'') for f in fields_text.split(',')]
        else:
            props['fields'] = ['Name', 'Email', 'Message']

        # 提取提交按钮文本
        submit_match = re.search(r'(?:submit|提交).*?(?:text|文本)?\s*[:：]?\s*["\']?([^"\'\n]+)', requirement)
        props['submit_text'] = submit_match.group(1).strip() if submit_match else 'Submit'

    elif component_type == 'grid':
        # 提取网格列数 - 支持 "grid with 4 columns" 和 "grid: columns: 4" 格式
        columns_match = re.search(r'(?:grid|网格)(?:\s+with\s+(\d+)\s+columns?|(?:.*?(?:columns?|列)\s*[:：]?\s*(\d+)))', requirement, re.IGNORECASE)
        if columns_match:
            # 检查两个捕获组，选择匹配的那个
            props['columns'] = int(columns_match.group(1) or columns_match.group(2))
        else:
            props['columns'] = 3

        # 提取项目数量 - 支持 "grid with 6 items" 和 "grid items: 6" 格式
        items_match = re.search(r'(?:grid|网格)(?:\s+with\s+(\d+)\s+items?|(?:.*?(?:items?|项目)\s*[:：]?\s*(\d+)))', requirement, re.IGNORECASE)
        if items_match:
            props['item_count'] = int(items_match.group(1) or items_match.group(2))
        else:
            props['item_count'] = 3

    elif component_type == 'table':
        # 提取表头
        headers_match = re.search(r'(?:table|表格).*?(?:headers?|表头)\s*[:：]?\s*\[?([^\]]+)\]?', requirement)
        if headers_match:
            headers_text = headers_match.group(1)
            props['headers'] = [h.strip().strip('"\'') for h in headers_text.split(',')]
        else:
            props['headers'] = ['Name', 'Description', 'Status']

        # 提取行数 - 支持 "table with 10 rows" 和 "table: rows: 10" 格式
        rows_match = re.search(r'(?:table|表格)(?:\s+with\s+(\d+)\s+rows?|(?:.*?(?:rows?|行)\s*[:：]?\s*(\d+)))', requirement, re.IGNORECASE)
        if rows_match:
            # 检查两个捕获组，选择匹配的那个
            props['row_count'] = int(rows_match.group(1) or rows_match.group(2))
        else:
            props['row_count'] = 3

    elif component_type == 'modal':
        # 提取模态框标题
        title_match = re.search(r'(?:modal|弹窗).*?(?:title|标题)\s*[:：]?\s*["\']?([^"\'\n]+)', requirement)
        props['title'] = title_match.group(1).strip() if title_match else 'Modal Title'

        # 提取模态框ID
        props['id'] = 'myModal'

    elif component_type == 'footer':
        # 提取公司名称
        company_match = re.search(r'(?:footer|页脚).*?(?:company|公司)\s*[:：]?\s*["\']?([^"\'\n]+)', requirement)
        props['company'] = company_match.group(1).strip() if company_match else 'My Company'

    return props


def generate_html(title: str, components: List[Dict], theme: str) -> str:
    """生成 HTML 代码

    Args:
        title: 页面标题
        components: 组件列表
        theme: 主题名称

    Returns:
        完整的 HTML 代码
    """
    if title is None:
        title = 'UI Mockup'

    import html as html_module

    # 转义标题中的特殊字符
    escaped_title = html_module.escape(title)

    # HTML 头部
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="zh-CN">',
        '<head>',
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f'    <title>{escaped_title}</title>',
        '    <link rel="stylesheet" href="styles.css">',
        '</head>',
        '<body>'
    ]

    # 生成各组件的 HTML
    for component in components:
        component_html = render_component(component)
        if component_html:
            html_parts.append(f'    {component_html}')

    # HTML 尾部
    html_parts.extend([
        '</body>',
        '</html>'
    ])

    return '\n'.join(html_parts)


def render_component(component: Dict) -> Optional[str]:
    """渲染单个组件

    Args:
        component: 组件字典，包含 type 和 props

    Returns:
        组件的 HTML 代码
    """
    if component is None:
        return None

    component_type = component.get('type')
    props = component.get('props') or {}

    if component_type not in COMPONENT_TEMPLATES:
        logger.warning(f"未知组件类型: {component_type}")
        return None

    template = COMPONENT_TEMPLATES[component_type]['html']

    # 根据组件类型渲染
    if component_type == 'button':
        return template.format(
            style=props.get('style', 'primary'),
            text=props.get('text', 'Click Me')
        )

    elif component_type == 'input':
        return template.format(
            type=props.get('type', 'text'),
            placeholder=props.get('placeholder', 'Enter text...')
        )

    elif component_type == 'card':
        return template.format(
            title=props.get('title', 'Card Title'),
            content=props.get('content', 'Card content goes here.')
        )

    elif component_type == 'navbar':
        links_html = '\n        '.join(
            f'<li><a href="#">{link}</a></li>'
            for link in props.get('links', ['Home', 'About', 'Contact'])
        )
        return template.format(
            brand=props.get('brand', 'MyApp'),
            links=links_html
        )

    elif component_type == 'form':
        fields_html = '\n    '.join(
            f'''<div class="form-group">
        <label>{field}</label>
        <input type="text" class="form-input" placeholder="Enter {field}...">
    </div>'''
            for field in props.get('fields', ['Name', 'Email'])
        )
        return template.format(
            fields=fields_html,
            submit_text=props.get('submit_text', 'Submit')
        )

    elif component_type == 'grid':
        items_html = '\n    '.join(
            f'<div class="grid-item">Item {i + 1}</div>'
            for i in range(props.get('item_count', 3))
        )
        return template.format(
            columns=props.get('columns', 3),
            items=items_html
        )

    elif component_type == 'hero':
        actions_html = f'<button class="btn primary">Get Started</button>'
        return template.format(
            title=props.get('title', 'Welcome'),
            subtitle=props.get('subtitle', 'Start your journey'),
            actions=actions_html
        )

    elif component_type == 'table':
        headers_html = '\n        '.join(
            f'<th>{header}</th>'
            for header in props.get('headers', ['Name', 'Description', 'Status'])
        )
        rows_html = '\n        '.join(
            f'''<tr>
            <td>Item {i + 1}</td>
            <td>Description for item {i + 1}</td>
            <td>Active</td>
        </tr>'''
            for i in range(props.get('row_count', 3))
        )
        return template.format(headers=headers_html, rows=rows_html)

    elif component_type == 'modal':
        return template.format(
            id=props.get('id', 'myModal'),
            title=props.get('title', 'Modal Title'),
            content=props.get('content', 'Modal content goes here.')
        )

    elif component_type == 'footer':
        return template.format(
            year=str(datetime.now().year),
            company=props.get('company', 'My Company')
        )

    return template


def generate_css(components: List[Dict], theme: str, responsive: bool) -> str:
    """生成 CSS 代码

    Args:
        components: 组件列表
        theme: 主题名称
        responsive: 是否生成响应式样式

    Returns:
        完整的 CSS 代码
    """
    css_parts = [
        '/* CSS Reset */',
        '* { margin: 0; padding: 0; box-sizing: border-box; }',
        'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; }',
        ''
    ]

    # 添加主题变量
    if theme in COLOR_THEMES:
        theme_colors = COLOR_THEMES[theme]
        css_parts.append('/* Theme Variables */')
        css_parts.append(':root {')
        for key, value in theme_colors.items():
            css_parts.append(f'    --color-{key}: {value};')
        css_parts.append('}')
        css_parts.append('')

    # 收集所有组件的样式
    used_types = set()
    if components:
        for c in components:
            if c and c.get('type') in COMPONENT_TEMPLATES:
                used_types.add(c.get('type'))

    # 添加组件样式
    for component_type in used_types:
        # 添加组件级注释
        css_parts.append(f'/* {component_type} */')
        styles = COMPONENT_TEMPLATES[component_type]['styles']
        for style_name, style_css in styles.items():
            css_parts.append(f'/* {component_type} - {style_name} */')
            css_parts.append(style_css)
            css_parts.append('')

    # 添加响应式样式
    if responsive:
        css_parts.append('/* Responsive Design */')
        css_parts.append(f'@media (max-width: {RESPONSIVE_BREAKPOINTS["tablet"]}) {{')
        css_parts.append('    .navbar { flex-direction: column; gap: 10px; }')
        css_parts.append('    .grid { grid-template-columns: 1fr !important; }')
        css_parts.append('    .hero h1 { font-size: 32px; }')
        css_parts.append('    .hero-actions { flex-direction: column; }')
        css_parts.append('}')
        css_parts.append('')

    return '\n'.join(css_parts)


def save_mockup(result: Dict, output_dir: str) -> Dict:
    """保存生成的原型文件

    Args:
        result: 生成结果
        output_dir: 输出目录

    Returns:
        保存的文件路径

    Raises:
        (IOError, OSError): 文件操作错误
    """
    from pathlib import Path

    output_path = Path(output_dir)

    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except (IOError, OSError) as e:
        raise UIMockupError(f"创建输出目录失败 {output_dir}: {str(e)}")

    # 保存 HTML 文件
    html_file = output_path / 'index.html'
    try:
        html_file.write_text(result['html'], encoding='utf-8')
    except (IOError, OSError) as e:
        raise UIMockupError(f"保存 HTML 文件失败: {str(e)}")

    # 保存 CSS 文件
    css_file = output_path / 'styles.css'
    try:
        css_file.write_text(result['css'], encoding='utf-8')
    except (IOError, OSError) as e:
        raise UIMockupError(f"保存 CSS 文件失败: {str(e)}")

    # 保存组件清单
    manifest_file = output_path / 'manifest.json'
    try:
        manifest_file.write_text(
            json.dumps({
                'components': result['components_used'],
                'metadata': result['metadata']
            }, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    except (IOError, OSError) as e:
        raise UIMockupError(f"保存 manifest 文件失败: {str(e)}")

    return {
        'html': str(html_file),
        'css': str(css_file),
        'manifest': str(manifest_file)
    }


def execute_skill(params: Dict) -> Dict:
    """执行技能

    Args:
        params: 技能参数
            - requirement: 需求描述
            - output_dir: 输出目录 (可选)
            - 其他参数同 generate_mockup

    Returns:
        执行结果
    """
    # 使用 Pydantic 验证输入参数
    if PYDANTIC_AVAILABLE:
        try:
            validated = UIMockupParams(**params)
            # 转换为字典用于后续处理
            params = validated.dict(exclude_unset=True)
        except PydanticValidationError as e:
            return {
                'success': False,
                'error': '输入参数验证失败',
                'validation_errors': e.errors()
            }

    try:
        result = generate_mockup(params)

        # 如果指定了输出目录，保存文件
        output_dir = params.get('output_dir')
        if output_dir:
            try:
                saved_files = save_mockup(result, output_dir)
                result['saved_files'] = saved_files
            except (IOError, OSError) as e:
                result['save_error'] = f'文件保存失败: {str(e)}'
                logger.error(f"保存 UI 原型时出错: {e}")

        return result

    except ValueError as e:
        logger.error(f"UI 原型生成参数错误: {e}")
        return {
            'success': False,
            'error': f'参数错误: {str(e)}'
        }
    except (IOError, OSError, PermissionError) as e:
        logger.error(f"UI 原型文件操作错误: {e}")
        return {
            'success': False,
            'error': f'文件操作失败: {str(e)}'
        }
    except UIMockupError as e:
        logger.error(f"UI 原型生成错误: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# ============== Tailwind CSS 支持 ==============

def generate_html_tailwind(
    title: str,
    components: List[Dict],
    theme: str = 'default',
    responsive: bool = True
) -> str:
    """生成 Tailwind CSS 版本的 HTML

    Args:
        title: 页面标题
        components: 组件列表
        theme: 主题名称
        responsive: 是否响应式

    Returns:
        完整的 HTML 代码
    """
    if not TAILWIND_AVAILABLE:
        raise UIMockupError("Tailwind CSS 组件不可用")

    # 生成 HTML 头部
    html = generate_tailwind_head(title, theme)

    # 生成主体内容
    for component in components:
        comp_type = component.get('type', '')
        props = component.get('props', {})

        try:
            if comp_type == 'navbar':
                brand = props.get('brand', 'Brand')
                links = props.get('links', ['Home', 'About', 'Contact'])
                html += render_navbar_tailwind(brand=brand, links=links)
            elif comp_type == 'hero':
                title_text = props.get('title', 'Welcome')
                subtitle = props.get('subtitle', 'Get Started')
                actions = props.get('actions', '')
                html += render_hero_tailwind(title=title_text, subtitle=subtitle, actions=actions)
            elif comp_type == 'button':
                text = props.get('text', 'Button')
                style = props.get('style', 'primary')
                html += render_button_tailwind(text=text, style=style)
            elif comp_type == 'card':
                card_title = props.get('title', 'Card Title')
                content = props.get('content', 'Card content')
                html += render_card_tailwind(title=card_title, content=content)
            elif comp_type == 'form':
                fields = props.get('fields', '')
                submit_text = props.get('submit_text', 'Submit')
                html += render_form_tailwind(fields=fields, submit_text=submit_text)
            elif comp_type == 'grid':
                items = props.get('items', '')
                columns = props.get('columns', 3)
                html += render_grid_tailwind(items=items, columns=columns)
            elif comp_type == 'table':
                headers = props.get('headers', '')
                rows = props.get('rows', '')
                html += render_table_tailwind(headers=headers, rows=rows)
            elif comp_type == 'modal':
                modal_id = props.get('id', 'modal')
                modal_title = props.get('title', 'Modal')
                content = props.get('content', 'Modal content')
                html += render_modal_tailwind(id=modal_id, title=modal_title, content=content)
            elif comp_type == 'footer':
                sections = props.get('sections', '')
                copyright = props.get('copyright', '© 2024')
                html += render_footer_tailwind(sections=sections, copyright=copyright)
            else:
                # 未知组件，使用占位符
                html += f'<div class="p-4 bg-gray-100 rounded">Unknown component: {comp_type}</div>'

        except Exception as e:
            logger.warning(f"渲染组件 {comp_type} 失败: {e}")
            html += f'<!-- Component {comp_type} failed to render: {e} -->'

    # 添加响应式元标签（如果需要）
    if responsive:
        html = html.replace(
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <meta name="description" content="Generated by LingFlow UI Mockup Generator">'
        )

    # 生成 HTML 结尾
    html += generate_tailwind_end()

    return html


def get_tailwind_theme_info(theme: str) -> Dict:
    """获取 Tailwind 主题信息

    Args:
        theme: 主题名称

    Returns:
        主题信息字典
    """
    if not TAILWIND_AVAILABLE:
        return {'error': 'Tailwind CSS 不可用'}

    theme_info = TAILWIND_THEMES.get(theme, TAILWIND_THEMES['default'])

    return {
        'theme': theme,
        'colors': theme_info,
        'cdn_version': '3.4.0',
        'available_themes': list(TAILWIND_THEMES.keys())
    }
