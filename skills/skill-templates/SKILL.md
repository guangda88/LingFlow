# skill-templates 技能

## 技能概述

skill-templates 是一个提供技能模板的库，让用户可以快速创建新技能。它包含了各种类型的技能模板，如数据处理类、API调用类、分析类等，用户可以基于这些模板快速创建符合自己需求的技能。

## 功能特性

- **提供多种技能模板**：包含数据处理、API调用、分析、通知和集成等多种类型的模板
- **快速创建技能**：基于模板快速生成技能的基本结构和代码
- **自定义模板**：允许用户根据需要自定义模板
- **模板管理**：管理和维护模板库

## 使用场景

- 当你需要快速创建一个新技能时
- 当你需要基于现有模板创建类似功能的技能时
- 当你需要标准化技能的结构和代码风格时
- 当你需要为团队提供统一的技能开发规范时

## 触发条件

- `create skill from template`
- `use skill template`
- `skill template`
- `template library`
- `quick start`

## 依赖关系

- `skill-creator` - 用于创建技能

## 模板库结构

```
templates/
├── data-skill/           # 数据处理类技能模板
│   ├── SKILL.md
│   ├── template.py
│   └── requirements.txt
├── api-skill/            # API调用类技能模板
│   ├── SKILL.md
│   ├── template.py
│   └── config.yaml
├── analysis-skill/       # 分析类技能模板
├── notification-skill/   # 通知类技能模板
└── integration-skill/    # 集成类技能模板
```

## 模板示例

### API调用类技能模板（templates/api-skill/template.py）

```python
"""{{SKILL_NAME}} - {{DESCRIPTION}}"""

from lingflow.skills.base import Skill
import requests

class {{CLASS_NAME}}(Skill):
    """{{DESCRIPTION}}"""
    
    name = "{{SKILL_NAME}}"
    version = "1.0.0"
    
    async def execute(self, context: dict) -> dict:
        """
        执行技能
        
        Args:
            context: 包含以下参数
                - api_key: API密钥（可选）
                - endpoint: API端点
                - payload: 请求数据
        
        Returns:
            dict: API响应结果
        """
        endpoint = context.get('endpoint')
        payload = context.get('payload', {})
        api_key = context.get('api_key')
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

## 使用方法

### 1. 基于模板创建新技能

```bash
# 使用命令行基于模板创建新技能
lingflow run skill-templates --params '{"template_type": "api-skill", "skill_name": "my-api-skill", "description": "我的API调用技能"}'
```

### 2. 列出可用模板

```bash
# 列出可用模板
lingflow run skill-templates --params '{"action": "list_templates"}'
```

### 3. 查看模板详情

```bash
# 查看模板详情
lingflow run skill-templates --params '{"action": "template_info", "template_type": "api-skill"}'
```

## 技能结构

```
skills/skill-templates/
├── SKILL.md          # 技能描述文件
├── __init__.py       # 技能初始化文件
├── implementation.py # 技能实现文件
└── templates/        # 模板目录
    ├── data-skill/
    ├── api-skill/
    ├── analysis-skill/
    ├── notification-skill/
    └── integration-skill/
```

## 最佳实践

1. **选择合适的模板**：根据技能的功能选择最适合的模板类型
2. **自定义模板**：根据具体需求修改模板，添加必要的功能
3. **遵循模板结构**：保持技能的结构和代码风格与模板一致
4. **测试模板**：使用 skill-testing 技能测试基于模板创建的技能
5. **分享模板**：将自定义的模板分享给团队成员，提高开发效率

## 故障排除

- **模板不存在**：检查模板类型是否正确，以及模板是否已正确安装
- **创建失败**：检查技能名称是否已存在，以及权限是否正确
- **代码错误**：检查生成的代码是否有语法错误或逻辑问题
- **依赖问题**：确保技能的依赖项已正确安装

## 相关技能

- `skill-creator` - 用于创建和管理技能
- `skill-testing` - 用于测试基于模板创建的技能
- `skill-versioning` - 用于管理技能的版本
- `skill-categorization` - 用于对基于模板创建的技能进行分类
