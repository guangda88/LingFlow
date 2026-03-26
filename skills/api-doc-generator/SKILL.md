# api-doc-generator 技能

## 技能概述

api-doc-generator 是一个自动生成 OpenAPI 3.0 规范文档的技能，支持从 FastAPI 和 Flask 代码中提取路由、类型注解和文档字符串，生成标准的 API 文档。

## 功能特性

### 支持的框架

- **FastAPI** - 完整支持 FastAPI 路由和 Pydantic 模型
- **Flask** - 支持 Flask 路由和蓝图
- **自动检测** - 自动检测使用的框架类型

### 文档生成能力

1. **路由提取**
   - HTTP 方法 (GET, POST, PUT, DELETE, PATCH, etc.)
   - 路径参数 (FastAPI: `{param}`, Flask: `<param>`)
   - 查询参数
   - 请求体 (JSON)

2. **类型推断**
   - 从类型注解自动推断参数类型
   - 支持 Optional、List 等泛型
   - 提取 Pydantic 模型定义

3. **文档解析**
   - 从 docstring 提取摘要和描述
   - 解析返回值说明
   - 生成响应定义

4. **输出格式**
   - JSON 格式
   - YAML 格式 (内置简单转换器，可选 PyYAML)

## 使用场景

- 从现有代码生成 API 文档
- 为 REST API 服务生成 OpenAPI 规范
- 集成到 CI/CD 流程自动更新文档
- 支持 Swagger UI、Redoc 等工具导入

## 触发条件

- `生成 API 文档`
- `generate api documentation`
- `openapi`
- `api docs`
- `generate openapi spec`

## 依赖关系

- 无强制依赖
- 可选: PyYAML (用于更好的 YAML 输出)

## 使用方法

### 1. 基本用法

```bash
# 生成 YAML 文档
lingflow run api-doc-generator --params '{"input": "./app.py"}'

# 生成 JSON 文档
lingflow run api-doc-generator --params '{"input": "./app.py", "format": "json"}'

# 指定输出文件
lingflow run api-doc-generator --params '{"input": "./app.py", "output": "./docs/openapi.yaml"}'
```

### 2. 扫描整个目录

```bash
lingflow run api-doc-generator --params '{"input": "./api/"}'
```

### 3. 指定框架

```bash
lingflow run api-doc-generator --params '{"input": "./app.py", "framework": "fastapi"}'
```

### 4. 自定义 API 信息

```bash
lingflow run api-doc-generator --params '{
  "input": "./app.py",
  "title": "My API",
  "version": "2.0.0",
  "base_url": "https://api.example.com"
}'
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input` | string | 必需 | 输入文件或目录路径 |
| `output` | string | 可选 | 输出文件路径 |
| `format` | string | `yaml` | 输出格式: `json` 或 `yaml` |
| `framework` | string | `auto` | 框架类型: `fastapi`, `flask`, `auto` |
| `title` | string | `API Documentation` | API 标题 |
| `version` | string | `1.0.0` | API 版本 |
| `base_url` | string | - | 基础 URL |

## 技能结构

```
skills/api-doc-generator/
├── SKILL.md           # 技能描述文件
├── __init__.py        # 技能初始化文件
├── implementation.py  # 技能实现文件
└── tests/             # 测试文件
    └── test_api_doc_generator.py
```

## 代码示例

### FastAPI 代码

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str
    age: int = None

@app.post("/users")
async def create_user(user: UserCreate):
    """创建新用户

    Args:
        user: 用户信息

    Returns:
        创建的用户信息
    """
    return {"id": 1, **user.dict()}
```

### Flask 代码

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """获取用户信息

    Args:
        user_id: 用户 ID

    Returns:
        用户信息
    """
    return jsonify({"id": user_id, "name": "Test User"})
```

## 最佳实践

1. **类型注解** - 使用完整的类型注解以获得准确的文档
2. **文档字符串** - 编写清晰的 docstring 说明每个端点的功能
3. **Pydantic 模型** - 使用 Pydantic 模型定义请求/响应结构
4. **定期更新** - 在代码变更后重新生成文档

## 故障排除

- **未找到路由** - 确保代码包含正确的路由装饰器
- **类型推断不准确** - 添加显式的类型注解
- **YAML 导出失败** - 安装 PyYAML: `pip install pyyaml`

## 相关技能

- `code-review` - 代码审查
- `code-analysis` - 代码分析
- `documentation` - 文档生成
