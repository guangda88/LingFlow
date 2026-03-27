# ui-mockup-generator 技能

## 技能概述

ui-mockup-generator 是一个用于从自然语言需求描述生成 HTML/CSS UI 原型的技能。它可以快速将设计想法转化为可交互的网页原型。

### 核心功能

1. **自然语言解析** - 从需求描述中提取组件和属性
2. **组件库** - 内置10+常用UI组件模板
3. **多主题支持** - 预设多种配色方案
4. **响应式设计** - 自动生成移动端适配样式

## 功能特性

### 支持的组件

| 组件 | 描述 | 关键词 |
|------|------|--------|
| navbar | 导航栏 | 导航, navbar, 导航栏, header, 页头 |
| hero | 首屏横幅 | hero, 首屏, banner, 横幅, 主区域 |
| card | 卡片 | card, 卡片, 信息卡 |
| form | 表单 | form, 表单, 登录, 注册, 输入 |
| button | 按钮 | button, 按钮, btn, 点击 |
| input | 输入框 | input, 输入框, 文本框 |
| table | 表格 | table, 表格, 列表 |
| grid | 网格布局 | grid, 网格, 布局 |
| modal | 弹窗 | modal, 弹窗, 对话框, popup |
| footer | 页脚 | footer, 页脚, 底部 |

### 支持的主题

**传统 CSS 模式:**
- **default** - 默认蓝色主题
- **dark** - 深色模式
- **nature** - 自然绿色主题
- **sunset** - 日落橙色主题

**Tailwind CSS 模式:**
- **default** - 蓝色/紫色渐变
- **ocean** - 青色/青绿色
- **sunset** - 橙色/红色
- **forest** - 绿色/翠绿
- **dark** - 深灰/锌色

## 使用场景

- 快速创建网页原型
- 设计方案验证
- 前端开发脚手架
- UI/UX 设计演示
- 登陆页面生成

## 触发条件

### 通用触发
- `ui mockup`
- `generate ui`
- `create prototype`
- `ui prototype`
- `mockup generator`
- `html template`

### 中文触发
- `UI原型`
- `生成界面`
- `创建网页`
- `界面原型`

## 依赖关系

- 无外部依赖

## 使用方法

### 1. 基础用法 - 自然语言描述

```bash
# 使用自然语言描述生成原型
lingflow run ui-mockup-generator --params '{
    "requirement": "创建一个带有导航栏和首屏横幅的页面，导航栏包含Home、About、Contact链接"
}'
```

### 2. 指定组件

```bash
# 指定具体组件生成
lingflow run ui-mockup-generator --params '{
    "components": [
        {"type": "navbar", "props": {"brand": "MyApp", "links": ["Home", "About"]}},
        {"type": "hero", "props": {"title": "Welcome", "subtitle": "Get Started"}}
    ]
}'
```

### 3. 自定义主题

```bash
# 使用深色主题
lingflow run ui-mockup-generator --params '{
    "requirement": "创建登录页面",
    "theme": "dark"
}'
```

### 4. 保存到文件

```bash
# 生成并保存到指定目录
lingflow run ui-mockup-generator --params '{
    "requirement": "创建产品展示页面",
    "output_dir": "./output"
}'
```

### 5. 使用 Tailwind CSS

```bash
# 使用 Tailwind CSS 生成现代 UI
lingflow run ui-mockup-generator --params '{
    "requirement": "创建带有导航栏和首屏的页面",
    "use_tailwind": true,
    "theme": "ocean"
}'
```

### 6. 完整参数示例

```bash
lingflow run ui-mockup-generator --params '{
    "requirement": "创建企业官网首页，包含导航栏、首屏横幅、产品卡片网格、表单和页脚",
    "title": "My Company Website",
    "theme": "nature",
    "responsive": true,
    "use_tailwind": false,
    "output_dir": "./website-prototype"
}'
```

## 技能结构

```
skills/ui-mockup-generator/
├── SKILL.md              # 技能描述文件
├── __init__.py           # 技能初始化文件
├── implementation.py     # 技能实现文件
└── templates/            # 组件模板目录 (可选扩展)
```

## 输出格式

技能执行后返回：

```json
{
    "html": "<!DOCTYPE html>...",
    "css": "/* CSS Reset */...",
    "components_used": [
        {"type": "navbar", "props": {...}},
        {"type": "hero", "props": {...}}
    ],
    "metadata": {
        "theme": "default",
        "responsive": true,
        "generated_at": "2025-01-01T00:00:00"
    },
    "saved_files": {
        "html": "/path/to/index.html",
        "css": "/path/to/styles.css",
        "manifest": "/path/to/manifest.json"
    }
}
```

## 最佳实践

1. **明确需求** - 提供清晰的需求描述，包含组件类型和关键属性
2. **选择主题** - 根据产品定位选择合适的主题
3. **响应式设计** - 默认开启响应式设计以适配移动设备
4. **组件组合** - 合理组合多个组件构建完整页面
5. **迭代优化** - 生成原型后可根据需求进一步调整

## 高级用法

### 自定义组件

在 implementation.py 中扩展 COMPONENT_TEMPLATES 字典添加自定义组件：

```python
COMPONENT_TEMPLATES['my_component'] = {
    'html': '<div class="my-component">{content}</div>',
    'styles': {
        'default': '.my-component { ... }'
    }
}
```

### 自定义主题

扩展 COLOR_THEMES 字典添加新主题：

```python
COLOR_THEMES['my_theme'] = {
    'primary': '#ff0000',
    'secondary': '#00ff00',
    ...
}
```

## 故障排除

- **组件未生成** - 检查需求描述中是否包含组件关键词
- **样式错误** - 验证主题名称是否正确
- **保存失败** - 确保输出目录有写入权限
- **编码问题** - 确保使用 UTF-8 编码

## 相关技能

- `code-review` - 用于审查生成的代码质量
- `workflow-executor` - 用于在工作流中执行UI生成
