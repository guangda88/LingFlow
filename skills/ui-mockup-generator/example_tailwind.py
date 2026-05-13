"""UI Mockup Generator - Tailwind CSS 使用示例

演示如何在 ui-mockup-generator 技能中使用 Tailwind CSS
"""

import sys
sys.path.insert(0, '/home/ai/lingflow/skills/ui-mockup-generator')

from implementation import generate_mockup

# 示例 1: 使用 Tailwind CSS 生成简单页面
print("=" * 60)
print("示例 1: Tailwind CSS - 导航栏 + 首屏")
print("=" * 60)

result = generate_mockup({
    'requirement': '创建一个带有导航栏和首屏的页面',
    'title': 'Tailwind 演示页面',
    'use_tailwind': True,
    'theme': 'ocean'
})

print(f"技术栈: {result['metadata']['tech_stack']}")
print(f"使用组件: {[c['type'] for c in result['components_used']]}")

# 示例 2: 不同主题
print("\n" + "=" * 60)
print("示例 2: 可用主题")
print("=" * 60)

from tailwind_components import TAILWIND_THEMES

for theme_name, colors in TAILWIND_THEMES.items():
    print(f"  {theme_name}: primary={colors['primary']}, secondary={colors['secondary']}")

# 示例 3: 生成完整页面并保存
print("\n" + "=" * 60)
print("示例 3: 生成完整页面")
print("=" * 60)

result = generate_mockup({
    'requirement': '创建企业官网首页，包含导航栏、首屏横幅、产品卡片、表单和页脚',
    'title': '企业官网',
    'use_tailwind': True,
    'theme': 'default',
    'responsive': True,
    'output_dir': '/tmp/ui_mockup_demo'
})

print(f"HTML 长度: {len(result['html'])} 字符")
print(f"组件数量: {len(result['components_used'])}")

# 保存文件
import os
os.makedirs('/tmp/ui_mockup_demo', exist_ok=True)

with open('/tmp/ui_mockup_demo/index.html', 'w') as f:
    f.write(result['html'])

print(f"\n✅ 已生成文件: /tmp/ui_mockup_demo/index.html")
print(f"在浏览器中打开查看效果")

# 显示 HTML 预览
print("\n" + "=" * 60)
print("HTML 预览")
print("=" * 60)
print(result['html'][:500] + "...")
