"""Tailwind CSS 组件模板库

用于 ui-mockup-generator 技能生成 Tailwind CSS 原型
"""

# Tailwind CSS 组件模板
TAILWIND_COMPONENTS = {
    'button': {
        'html': {
            'primary': '<button class="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">{text}</button>',
            'secondary': '<button class="px-6 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors">{text}</button>',
            'outline': '<button class="px-6 py-3 border-2 border-blue-600 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors">{text}</button>',
            'danger': '<button class="px-6 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors">{text}</button>',
        }
    },
    'input': {
        'html': '<input type="{type}" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="{placeholder}">',
    },
    'card': {
        'html': '''<div class="bg-white rounded-xl shadow-lg overflow-hidden">
    <div class="bg-gray-50 px-6 py-4 border-b">
        <h3 class="text-lg font-semibold">{title}</h3>
    </div>
    <div class="p-6">
        {content}
    </div>
</div>''',
    },
    'navbar': {
        'html': '''<nav class="flex justify-between items-center px-8 py-4 bg-gray-900 text-white">
    <div class="text-xl font-bold">{brand}</div>
    <ul class="flex space-x-8">
        {links}
    </ul>
</nav>''',
        'link_template': '<li><a href="#" class="hover:text-blue-400 transition-colors">{text}</a></li>',
    },
    'form': {
        'html': '''<form class="max-w-md mx-auto space-y-4">
    {fields}
    <button type="submit" class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">{submit_text}</button>
</form>''',
        'field': '''<div>
    <label class="block text-sm font-medium text-gray-700 mb-1">{label}</label>
    <input type="{type}" name="{name}" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="{placeholder}">
</div>''',
    },
    'grid': {
        'html': '<div class="grid grid-cols-{columns} gap-6">{items}</div>',
        'item': '<div class="p-6 bg-gray-50 rounded-lg">{content}</div>',
    },
    'hero': {
        'html': '''<section class="text-center py-24 bg-gradient-to-r from-purple-600 to-blue-600 text-white">
    <h1 class="text-5xl font-bold mb-6">{title}</h1>
    <p class="text-xl mb-8 opacity-90">{subtitle}</p>
    <div class="flex justify-center gap-4">
        {actions}
    </div>
</section>''',
    },
    'table': {
        'html': '''<table class="w-full border-collapse">
    <thead>
        <tr class="bg-gray-100">{headers}</tr>
    </thead>
    <tbody>
        {rows}
    </tbody>
</table>''',
        'header': '<th class="px-6 py-3 text-left text-sm font-semibold text-gray-700">{text}</th>',
        'cell': '<td class="px-6 py-4 border-b">{text}</td>',
    },
    'modal': {
        'html': '''<div class="modal fixed inset-0 z-50 hidden" id="{id}">
    <div class="absolute inset-0 bg-black/50"></div>
    <div class="relative flex items-center justify-center min-h-screen p-4">
        <div class="relative bg-white rounded-xl shadow-2xl max-w-lg w-full p-6">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold">{title}</h3>
                <button class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
            </div>
            <div class="modal-body">
                {content}
            </div>
        </div>
    </div>
</div>''',
    },
    'footer': {
        'html': '''<footer class="bg-gray-900 text-gray-400 py-12">
    <div class="max-w-6xl mx-auto px-8">
        <div class="grid grid-cols-3 gap-8">
            {sections}
        </div>
        <div class="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
            {copyright}
        </div>
    </div>
</footer>''',
        'section': '<div><h4 class="text-white font-semibold mb-4">{title}</h4><ul class="space-y-2">{links}</ul></div>',
    },
}

# Tailwind 配色主题
TAILWIND_THEMES = {
    'default': {
        'primary': 'blue',
        'secondary': 'purple',
        'accent': 'indigo',
    },
    'ocean': {
        'primary': 'cyan',
        'secondary': 'teal',
        'accent': 'sky',
    },
    'sunset': {
        'primary': 'orange',
        'secondary': 'red',
        'accent': 'amber',
    },
    'forest': {
        'primary': 'green',
        'secondary': 'emerald',
        'accent': 'lime',
    },
    'dark': {
        'primary': 'slate',
        'secondary': 'zinc',
        'accent': 'gray',
    },
}

# Tailwind CDN 配置
TAILWIND_CDN_CONFIG = {
    'script': '<script src="https://cdn.tailwindcss.com"></script>',
    'config_template': '''<script>
tailwind.config = {{
  theme: {{
    extend: {{
      colors: {{
        primary: '{primary_color}',
        secondary: '{secondary_color}',
      }}
    }}
  }}
}}
</script>''',
}

# 生成 Tailwind HTML 头部
def generate_tailwind_head(title: str, theme: str = 'default') -> str:
    """生成 Tailwind HTML 头部"""
    colors = TAILWIND_THEMES.get(theme, TAILWIND_THEMES['default'])

    primary_colors = {
        'blue': '#3b82f6',
        'purple': '#9333ea',
        'cyan': '#06b6d4',
        'green': '#22c55e',
        'orange': '#f97316',
        'slate': '#64748b',
    }

    config = TAILWIND_CDN_CONFIG['config_template'].format(
        primary_color=primary_colors.get(colors['primary'], '#3b82f6'),
        secondary_color=primary_colors.get(colors['secondary'], '#9333ea'),
    )

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {TAILWIND_CDN_CONFIG['script']}
    {config}
</head>
<body class="bg-gray-50 text-gray-900">
'''

# 生成 Tailwind HTML 结尾
def generate_tailwind_end() -> str:
    """生成 Tailwind HTML 结尾"""
    return '''</body>
</html>'''


# 组件渲染函数
def render_button_tailwind(text: str, style: str = 'primary', **kwargs) -> str:
    """渲染 Tailwind 按钮"""
    template = TAILWIND_COMPONENTS['button']['html'].get(style, TAILWIND_COMPONENTS['button']['html']['primary'])
    return template.format(text=text)


def render_input_tailwind(**kwargs) -> str:
    """渲染 Tailwind 输入框"""
    return TAILWIND_COMPONENTS['input']['html'].format(**kwargs)


def render_card_tailwind(title: str, content: str, **kwargs) -> str:
    """渲染 Tailwind 卡片"""
    return TAILWIND_COMPONENTS['card']['html'].format(title=title, content=content)


def render_navbar_tailwind(brand: str, links: list, **kwargs) -> str:
    """渲染 Tailwind 导航栏"""
    link_template = TAILWIND_COMPONENTS['navbar']['link_template']
    links_html = ''.join(link_template.format(text=link) for link in links)
    return TAILWIND_COMPONENTS['navbar']['html'].format(brand=brand, links=links_html)


def render_hero_tailwind(title: str, subtitle: str, actions: str = '', **kwargs) -> str:
    """渲染 Tailwind 首屏"""
    return TAILWIND_COMPONENTS['hero']['html'].format(title=title, subtitle=subtitle, actions=actions)


def render_form_tailwind(fields: str, submit_text: str = '提交', **kwargs) -> str:
    """渲染 Tailwind 表单"""
    return TAILWIND_COMPONENTS['form']['html'].format(fields=fields, submit_text=submit_text)


def render_grid_tailwind(items: str, columns: int = 3, **kwargs) -> str:
    """渲染 Tailwind 网格"""
    return TAILWIND_COMPONENTS['grid']['html'].format(items=items, columns=columns)


def render_table_tailwind(headers: str, rows: str, **kwargs) -> str:
    """渲染 Tailwind 表格"""
    return TAILWIND_COMPONENTS['table']['html'].format(headers=headers, rows=rows)


def render_modal_tailwind(id: str, title: str, content: str, **kwargs) -> str:
    """渲染 Tailwind 模态框"""
    return TAILWIND_COMPONENTS['modal']['html'].format(id=id, title=title, content=content)


def render_footer_tailwind(sections: str, copyright: str, **kwargs) -> str:
    """渲染 Tailwind 页脚"""
    return TAILWIND_COMPONENTS['footer']['html'].format(sections=sections, copyright=copyright)


# 工具函数
def get_available_themes() -> list:
    """获取可用主题列表"""
    return list(TAILWIND_THEMES.keys())


def get_theme_colors(theme: str) -> dict:
    """获取主题颜色"""
    return TAILWIND_THEMES.get(theme, TAILWIND_THEMES['default'])
