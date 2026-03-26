"""api-doc-generator 技能实现 - OpenAPI 3.0 文档生成器

异常处理:
    - APIDocError: API 文档生成相关错误
    - FileNotFoundError: 输入文件不存在
    - SyntaxError: Python 代码语法错误
"""

import ast
import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field

# 保存 Path 类引用以避免在 mock 环境下递归导入
_path_cls = Path

# 导入自定义异常
import sys
sys.path.insert(0, str(_path_cls(__file__).parent.parent))
from exceptions import APIDocError

# 导入 Pydantic 验证模型
try:
    from pydantic import ValidationError as PydanticValidationError
    from .validation import APIDocParams
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============== 数据结构 ==============

@dataclass
class RouteInfo:
    """路由信息"""
    path: str
    method: str
    handler_name: str
    summary: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[Dict] = field(default_factory=list)
    request_body: Optional[Dict] = None
    responses: Dict = field(default_factory=dict)
    security: List[Dict] = field(default_factory=list)
    deprecated: bool = False


@dataclass
class SchemaInfo:
    """类型信息"""
    name: str
    type: str
    properties: Dict = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    description: str = ""
    enum: List[str] = field(default_factory=list)


# ============== 类型映射 ==============

PYTHON_TYPE_TO_JSON = {
    'str': 'string',
    'int': 'integer',
    'float': 'number',
    'bool': 'boolean',
    'list': 'array',
    'dict': 'object',
    'Any': 'object',
    'None': 'null',
    'datetime': 'string',
    'date': 'string',
    'time': 'string',
    'Optional[str]': 'string',
    'Optional[int]': 'integer',
    'Optional[float]': 'number',
    'Optional[bool]': 'boolean',
}


# ============== 主函数 ==============

def execute_skill(params: Dict) -> Dict:
    """执行技能 - 生成 OpenAPI 文档

    Args:
        params: 包含以下键的字典:
            - input: 输入文件或目录路径
            - output: 输出文件路径 (可选)
            - format: 输出格式 ('json' 或 'yaml', 默认 'yaml')
            - framework: 框架类型 ('fastapi', 'flask', 'auto', 默认 'auto')
            - title: API 标题 (可选)
            - version: API 版本 (默认 '1.0.0')
            - base_url: 基础 URL (可选)

    Returns:
        包含生成结果的字典
    """
    # 使用 Pydantic 验证输入参数
    if PYDANTIC_AVAILABLE:
        try:
            validated = APIDocParams(**params)
            # 使用验证后的参数
            input_path = validated.input
            output_path = validated.output
            output_format = validated.format
            framework = validated.framework
            title = validated.title
            version = validated.version
            base_url = validated.base_url or ''
        except PydanticValidationError as e:
            return {
                'success': False,
                'error': '输入参数验证失败',
                'validation_errors': e.errors()
            }
    else:
        # 回退到原有的简单验证
        input_path = params.get('input')
        output_path = params.get('output')
        output_format = params.get('format', 'yaml')
        framework = params.get('framework', 'auto')
        title = params.get('title', 'API Documentation')
        version = params.get('version', '1.0.0')
        base_url = params.get('base_url', '')

        if not input_path:
            return {
                'success': False,
                'error': '请指定输入文件或目录路径 (input 参数)'
            }

    # 扫描代码
    try:
        routes, schemas = scan_code(input_path, framework)
    except FileNotFoundError as e:
        logger.error(f"输入文件不存在: {e}")
        return {
            'success': False,
            'error': f'输入文件不存在: {str(e)}'
        }
    except APIDocError as e:
        logger.error(f"API 文档生成错误: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    except (SyntaxError, RecursionError) as e:
        logger.error(f"代码解析错误: {e}")
        return {
            'success': False,
            'error': f'代码解析错误: {str(e)}'
        }
    except (IOError, OSError) as e:
        logger.error(f"文件读取错误: {e}")
        return {
            'success': False,
            'error': f'文件读取失败: {str(e)}'
        }
    except ValueError as e:
        logger.error(f"参数值错误: {e}")
        return {
            'success': False,
            'error': f'参数值错误: {str(e)}'
        }

    if not routes:
        return {
            'success': False,
            'error': '未找到任何 API 路由',
            'hint': '请确保输入的代码包含 FastAPI 或 Flask 路由定义'
        }

    # 生成 OpenAPI 文档
    openapi_doc = generate_openapi_spec(
        routes=routes,
        schemas=schemas,
        title=title,
        version=version,
        base_url=base_url
    )

    # 输出结果
    result = {
        'success': True,
        'routes_count': len(routes),
        'schemas_count': len(schemas),
        'openapi': openapi_doc,
        'format': output_format
    }

    # 如果指定了输出路径，保存文件
    if output_path:
        try:
            save_document(openapi_doc, output_path, output_format)
            result['output_file'] = str(output_path)
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"保存文档时出错: {e}")
            result['save_error'] = f'文件保存失败: {str(e)}'

    return result


def scan_code(input_path: str, framework: str) -> Tuple[List[RouteInfo], Dict[str, SchemaInfo]]:
    """扫描代码提取路由和类型信息

    Args:
        input_path: 输入文件或目录路径
        framework: 框架类型

    Returns:
        (路由列表, 类型定义字典)
    """
    input_file = Path(input_path)
    routes = []
    schemas = {}

    if not input_file.exists():
        raise APIDocError(f'输入文件不存在: {input_path}')

    # 收集要处理的 Python 文件
    python_files = []
    if input_file.is_file() and input_file.suffix == '.py':
        python_files = [input_file]
    elif input_file.is_dir():
        python_files = list(input_file.rglob('*.py'))

    # 扫描每个文件
    for py_file in python_files:
        try:
            content = py_file.read_text(encoding='utf-8')
            tree = ast.parse(content)

            # 检测框架类型
            detected_framework = framework
            if framework == 'auto':
                detected_framework = detect_framework(tree)

            # 提取路由前缀 (如 APIRouter(prefix="/api"), Blueprint(url_prefix="/api"))
            route_prefixes = extract_route_prefixes(tree, content, detected_framework)

            # 提取路由
            file_routes = extract_routes(tree, content, str(py_file), detected_framework, route_prefixes)
            routes.extend(file_routes)

            # 提取类型定义
            file_schemas = extract_schemas(tree, content)
            schemas.update(file_schemas)

        except SyntaxError as e:
            logger.warning(f"解析文件 {py_file} 时出现语法错误: {e}")
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"读取文件 {py_file} 时出错: {e}")
        except RecursionError:
            logger.error(f"解析文件 {py_file} 时遇到递归深度限制")

    return routes, schemas


def extract_route_prefixes(tree: ast.AST, content: str, framework: str) -> Dict[str, str]:
    """提取路由前缀 (如 APIRouter(prefix="/api"), Blueprint(url_prefix="/api"))

    Returns:
        字典，键为路由器名称 (如 'router', 'bp')，值为前缀路径
    """
    prefixes = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    # 检查赋值表达式
                    if isinstance(node.value, ast.Call):
                        callee_str = _unparse(node.value.func)
                        # FastAPI: APIRouter(prefix="/api") or router = APIRouter(prefix="/api")
                        # Flask: Blueprint('api', __name__, url_prefix='/api')

                        if framework == 'fastapi' and ('APIRouter' in callee_str or 'router' in callee_str):
                            for keyword in node.value.keywords:
                                if keyword.arg == 'prefix':
                                    prefix_value = _unparse(keyword.value)
                                    # Remove quotes
                                    prefix_value = prefix_value.strip('"\'')
                                    prefixes[var_name] = prefix_value

                        elif framework == 'flask' and 'Blueprint' in callee_str:
                            # Blueprint('api', __name__, url_prefix='/api')
                            for keyword in node.value.keywords:
                                if keyword.arg == 'url_prefix':
                                    prefix_value = _unparse(keyword.value)
                                    prefix_value = prefix_value.strip('"\'')
                                    prefixes[var_name] = prefix_value

    return prefixes


def detect_framework(tree: ast.AST) -> str:
    """检测使用的 Web 框架"""
    # 先检查导入 - FastAPI 优先
    for node in ast.walk(tree):
        # 检查导入
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('fastapi'):
                    return 'fastapi'
                elif alias.name == 'flask':
                    return 'flask'
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.module.startswith('fastapi'):
                    return 'fastapi'
                elif node.module == 'flask':
                    return 'flask'

    # 检查装饰器 - FastAPI 装饰器模式
    fastapi_methods = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']
    fastapi_prefixes = ['app', 'router', 'APIRouter']

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                decorator_str = ast.unparse(decorator) if hasattr(ast, 'unparse') else str(decorator)

                # 检查 FastAPI 装饰器: @app.get, @router.post, @APIRouter.put 等
                for prefix in fastapi_prefixes:
                    for method in fastapi_methods:
                        if f'{prefix}.{method}(' in decorator_str:
                            return 'fastapi'

                # 检查 Flask 装饰器: @app.route, @bp.route
                if '@app.route' in decorator_str or '@bp.route' in decorator_str or '@blueprint.route' in decorator_str:
                    return 'flask'

    return 'flask'  # 默认


def extract_routes(tree: ast.AST, content: str, file_path: str, framework: str,
                   route_prefixes: Dict[str, str] = None) -> List[RouteInfo]:
    """从 AST 中提取路由信息"""
    routes = []
    if route_prefixes is None:
        # 如果没有提供前缀，自动提取
        route_prefixes = extract_route_prefixes(tree, content, framework)

    # 只处理顶层函数定义 (避免重复遍历)
    for node in ast.iter_child_nodes(tree):
        # 支持同步和异步函数
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            route_list = parse_route_decorator(node, framework, route_prefixes)
            for route_info in route_list:
                # 提取文档字符串
                docstring = ast.get_docstring(node) or ""
                route_info.summary, route_info.description = parse_docstring(docstring)

                # 提取类型信息
                route_info.parameters = extract_parameters(node, framework, route_info.path)
                route_info.request_body = extract_request_body(node, framework)
                route_info.responses = extract_responses(node, docstring)

                routes.append(route_info)

        # 处理类中的方法 (如视图类)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    route_list = parse_route_decorator(child, framework, route_prefixes)
                    for route_info in route_list:
                        docstring = ast.get_docstring(child) or ""
                        route_info.summary, route_info.description = parse_docstring(docstring)
                        route_info.parameters = extract_parameters(child, framework, route_info.path)
                        route_info.request_body = extract_request_body(child, framework)
                        route_info.responses = extract_responses(child, docstring)
                        routes.append(route_info)

    return routes


def parse_route_decorator(node: Union[ast.FunctionDef, ast.AsyncFunctionDef], framework: str,
                          route_prefixes: Dict[str, str] = None) -> List[RouteInfo]:
    """解析路由装饰器，返回路由列表 (Flask 多方法支持)"""
    routes = []
    if route_prefixes is None:
        route_prefixes = {}

    # 类型检查 - 确保节点是函数定义
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return routes

    for decorator in node.decorator_list:
        decorator_str = _unparse(decorator)

        if framework == 'fastapi':
            # FastAPI: @app.get("/path"), @router.post("/path"), @APIRouter.put("/path")
            # ast.unparse 不包含 @ 符号
            match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\.(get|post|put|delete|patch|options|head|trace)\(["\']([^"\']+)["\']', decorator_str)
            if match:
                router_name = match.group(1)  # app, router, APIRouter
                method = match.group(2).upper()
                path = match.group(3)

                # 应用路由前缀
                if router_name in route_prefixes:
                    prefix = route_prefixes[router_name]
                    if not path.startswith('/'):
                        path = '/' + path
                    if not prefix.endswith('/'):
                        prefix = prefix + '/'
                    path = prefix + path.lstrip('/')

                # 提取 tags 参数
                tags = _extract_decorator_tags(decorator)

                routes.append(RouteInfo(
                    path=path,
                    method=method,
                    handler_name=node.name,
                    tags=tags
                ))

        elif framework == 'flask':
            # Flask: @app.route("/path", methods=["GET"]), @bp.route("/path")
            match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\.route\(["\']([^"\']+)["\']', decorator_str)
            if match:
                router_name = match.group(1)  # app, bp, blueprint
                path = match.group(2)

                # 应用路由前缀
                if router_name in route_prefixes:
                    prefix = route_prefixes[router_name]
                    if not path.startswith('/'):
                        path = '/' + path
                    if not prefix.endswith('/'):
                        prefix = prefix + '/'
                    path = prefix + path.lstrip('/')

                # 提取 methods
                methods_match = re.search(r'methods=\[([^\]]+)\]', decorator_str)
                if methods_match:
                    methods_str = methods_match.group(1)
                    methods = re.findall(r'["\']([A-Z]+)["\']', methods_str)
                else:
                    methods = ['GET']

                # 为每个方法创建路由
                for method in methods:
                    routes.append(RouteInfo(
                        path=path,
                        method=method.upper(),
                        handler_name=node.name
                    ))

    return routes


def _extract_decorator_tags(decorator: ast.AST) -> List[str]:
    """从装饰器中提取 tags 参数"""
    tags = []

    if not isinstance(decorator, ast.Call):
        return tags

    for keyword in decorator.keywords:
        if keyword.arg == 'tags':
            # tags 是一个列表
            if isinstance(keyword.value, ast.List):
                for elt in keyword.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        tags.append(elt.value)
            break

    return tags


def extract_parameters(node: Union[ast.FunctionDef, ast.AsyncFunctionDef], framework: str, path: str = '') -> List[Dict]:
    """提取路径参数和查询参数"""
    parameters = []

    if not path:
        # 从装饰器中提取路径
        for decorator in node.decorator_list:
            decorator_str = _unparse(decorator)
            if framework == 'fastapi':
                match = re.search(r'(app|router|APIRouter)\.\w+\(["\']([^"\']+)["\']', decorator_str)
                if match:
                    path = match.group(2)
            elif framework == 'flask':
                match = re.search(r'(app|bp|blueprint)\.route\(["\']([^"\']+)["\']', decorator_str)
                if match:
                    path = match.group(2)

    # 提取路径参数
    if framework == 'fastapi' and path:
        # FastAPI 使用 {param}
        path_params = re.findall(r'\{(\w+)\}', path)
        for param in path_params:
            parameters.append({
                'name': param,
                'in': 'path',
                'required': True,
                'schema': {'type': 'string'}
            })
    elif framework == 'flask' and path:
        # Flask 使用 <param> 或 <param:type>
        path_params = re.findall(r'<(?:(\w+):)?(\w+)>', path)
        for param_type, param_name in path_params:
            param_type = param_type or 'string'
            parameters.append({
                'name': param_name,
                'in': 'path',
                'required': True,
                'schema': {'type': map_flask_type(param_type)}
            })

    # 查询参数 (从函数参数中提取)
    for arg in node.args.args:
        if arg.arg in ['self', 'cls', 'request']:
            continue

        # 检查是否有默认值
        has_default = False
        if node.args.defaults:
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            if node.args.args.index(arg) >= defaults_offset:
                has_default = True

        # 跳过已经在路径参数中的
        if any(p['name'] == arg.arg for p in parameters):
            continue

        # 推断类型
        param_type = 'string'
        if arg.annotation:
            param_type = infer_type_from_annotation(arg.annotation)

        parameters.append({
            'name': arg.arg,
            'in': 'query',
            'required': not has_default,
            'schema': {'type': param_type}
        })

    return parameters


def extract_request_body(node: Union[ast.FunctionDef, ast.AsyncFunctionDef], framework: str) -> Optional[Dict]:
    """提取请求体信息"""
    if framework != 'fastapi':
        return None

    # 检查参数默认值和注解
    for i, arg in enumerate(node.args.args):
        if arg.arg in ['self', 'cls', 'request']:
            continue

        # 检查默认值是否是 Body() 调用
        if node.args.defaults:
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            default_index = node.args.args.index(arg) - defaults_offset
            if 0 <= default_index < len(node.args.defaults):
                default_value = node.args.defaults[default_index]
                default_str = _unparse(default_value)
                if 'Body(' in default_str or 'Body (' in default_str:
                    return {
                        'content': {
                            'application/json': {
                                'schema': {'type': 'object'}
                            }
                        }
                    }

        # 检查注解
        if arg.annotation:
            annotation_str = _unparse(arg.annotation)
            if 'Body' in annotation_str:
                return {
                    'content': {
                        'application/json': {
                            'schema': {'type': 'object'}
                        }
                    }
                }
            # Pydantic 模型 (假设首字母大写的是模型)
            if annotation_str and annotation_str[0].isupper() and annotation_str[0].isalpha():
                return {
                    'content': {
                        'application/json': {
                            'schema': {'$ref': f'#/components/schemas/{annotation_str}'}
                        }
                    },
                    'required': True
                }

    return None


def extract_responses(node: Union[ast.FunctionDef, ast.AsyncFunctionDef], docstring: str) -> Dict:
    """提取响应信息"""
    responses = {}

    # 从文档字符串中提取响应信息
    # 格式: Returns: 200: 成功响应
    returns_match = re.search(r'(?:返回|Returns?)(?:\s*:\s*)?\n(?:\s*(\d+)\s*:\s*([^\n]+))?', docstring, re.IGNORECASE)
    if returns_match:
        status_code = returns_match.group(1) or '200'
        description = returns_match.group(2) or '成功'
        responses[status_code] = {
            'description': description
        }

    # 默认响应
    if not responses:
        responses['200'] = {'description': '成功'}

    # 从类型注解中提取返回类型
    if node.returns:
        return_type = infer_type_from_annotation(node.returns)
        if '200' in responses:
            responses['200']['content'] = {
                'application/json': {
                    'schema': {'type': return_type}
                }
            }

    return responses


def extract_schemas(tree: ast.AST, content: str) -> Dict[str, SchemaInfo]:
    """提取类型定义 (Pydantic 模型 / dataclass)"""
    schemas = {}
    pydantic_classes = {}  # 存储所有 Pydantic 类名
    class_schemas = {}  # 先创建所有 schema，再处理继承

    # 第一次遍历：收集所有 Pydantic 类名
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # 检查是否是 Pydantic 模型或 dataclass
            is_pydantic = _is_pydantic_model(node, content)
            is_dataclass = _is_dataclass(node)

            if is_pydantic:
                pydantic_classes[node.name] = True
            elif is_dataclass:
                pydantic_classes[node.name] = True

    # 第二次遍历：为所有 Pydantic/dataclass 类创建基础 schema
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name

            # 检查是否是 Pydantic 模型或 dataclass (直接或间接)
            is_model = _is_pydantic_model(node, content) or _is_dataclass(node)

            # 检查是否继承自已知的 Pydantic 类
            has_pydantic_base = False
            for base in node.bases:
                base_name = _unparse(base)
                if base_name in pydantic_classes or base_name in ['BaseModel', 'GenericModel']:
                    has_pydantic_base = True
                    break

            if is_model or has_pydantic_base:
                schema = SchemaInfo(
                    name=class_name,
                    type='object'
                )

                # 收集基类信息
                bases = [_unparse(base) for base in node.bases]

                # 提取当前类的属性
                for child in node.body:
                    if isinstance(child, ast.AnnAssign):
                        prop_name = child.target.id if isinstance(child.target, ast.Name) else None
                        if prop_name:
                            prop_type = infer_type_from_annotation(child.annotation) if child.annotation else 'string'
                            schema.properties[prop_name] = {'type': prop_type}

                            # 检查是否必需 (通过是否有默认值判断)
                            if child.value is None and not _has_default(child):
                                schema.required.append(prop_name)

                class_schemas[class_name] = {
                    'schema': schema,
                    'bases': bases
                }

    # 第三次遍历：处理继承，合并基类属性
    for class_name, info in class_schemas.items():
        schema = info['schema']
        bases = info['bases']

        # 按继承顺序处理基类
        for base_name in bases:
            # 跳过标准库和 pydantic 的基类
            if base_name in ['BaseModel', 'GenericModel', 'object', 'object']:
                continue

            # 如果基类在当前文件中也定义了，继承其属性
            if base_name in class_schemas:
                parent_schema = class_schemas[base_name]['schema']
                # 合并基类的属性 (如果子类没有覆盖)
                for prop_name, prop_def in parent_schema.properties.items():
                    if prop_name not in schema.properties:
                        schema.properties[prop_name] = prop_def

        schemas[class_name] = schema

    return schemas


def generate_openapi_spec(routes: List[RouteInfo], schemas: Dict[str, SchemaInfo],
                          title: str, version: str, base_url: str) -> Dict:
    """生成 OpenAPI 3.0 规范文档"""
    doc = {
        'openapi': '3.0.0',
        'info': {
            'title': title,
            'version': version,
            'description': f'Auto-generated API documentation\n\nGenerated at: {datetime.now().isoformat()}'
        },
        'paths': {},
        'components': {
            'schemas': {}
        }
    }

    if base_url:
        doc['servers'] = [{'url': base_url}]

    # 添加路由
    for route in routes:
        path = route.path
        method = route.method.lower()

        if path not in doc['paths']:
            doc['paths'][path] = {}

        doc['paths'][path][method] = {
            'summary': route.summary or route.handler_name,
            'operationId': route.handler_name,
            'responses': route.responses or {'200': {'description': 'Success'}}
        }

        if route.description:
            doc['paths'][path][method]['description'] = route.description

        # 添加 tags (即使是空列表)
        doc['paths'][path][method]['tags'] = route.tags

        if route.parameters:
            doc['paths'][path][method]['parameters'] = route.parameters

        if route.request_body:
            doc['paths'][path][method]['requestBody'] = route.request_body

        if route.deprecated:
            doc['paths'][path][method]['deprecated'] = True

    # 添加类型定义
    for name, schema in schemas.items():
        doc['components']['schemas'][name] = {
            'type': schema.type,
            'properties': schema.properties
        }
        if schema.required:
            doc['components']['schemas'][name]['required'] = schema.required
        if schema.description:
            doc['components']['schemas'][name]['description'] = schema.description

    return doc


def save_document(doc: Dict, output_path: str, format: str):
    """保存文档到文件"""
    # 使用 os.path 而不是 Path 以避免 mock __import__ 导致的递归问题
    # 确保目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
    else:
        # YAML 格式 - 直接使用简单格式以避免 import 问题
        yaml_content = to_simple_yaml(doc)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)


# ============== 辅助函数 ==============

def _unparse(node: ast.AST) -> str:
    """将 AST 节点转换为代码字符串"""
    if hasattr(ast, 'unparse'):
        return ast.unparse(node)
    return str(node)


def infer_type_from_annotation(annotation: ast.AST) -> str:
    """从类型注解推断 JSON 类型"""
    annotation_str = _unparse(annotation)

    # 直接类型
    if annotation_str in PYTHON_TYPE_TO_JSON:
        return PYTHON_TYPE_TO_JSON[annotation_str]

    # Optional 类型
    optional_match = re.match(r'Optional\[(\w+)\]', annotation_str)
    if optional_match:
        inner_type = optional_match.group(1)
        return PYTHON_TYPE_TO_JSON.get(inner_type, 'string')

    # List 类型
    list_match = re.match(r'List\[(\w+)\]', annotation_str)
    if list_match:
        return 'array'

    # Union 类型
    if 'Union' in annotation_str:
        return 'object'

    # 默认
    return 'string'


def map_flask_type(flask_type: str) -> str:
    """映射 Flask 路径参数类型到 JSON 类型"""
    type_map = {
        'string': 'string',
        'int': 'integer',
        'float': 'number',
        'path': 'string',
        'uuid': 'string',
        'slug': 'string'
    }
    return type_map.get(flask_type, 'string')


def parse_docstring(docstring: str) -> Tuple[str, str]:
    """解析文档字符串，提取摘要和描述"""
    if not docstring:
        return "", ""

    lines = docstring.strip().split('\n')
    summary = lines[0] if lines else ""
    description = '\n'.join(lines[1:]) if len(lines) > 1 else ""

    return summary, description


def _is_pydantic_model(node: ast.ClassDef, content: str, all_classes: Dict[str, ast.ClassDef] = None) -> bool:
    """检查是否是 Pydantic 模型

    Args:
        node: 类定义节点
        content: 源代码内容
        all_classes: 所有类的字典 (用于检查继承链)
    """
    # 检查基类
    for base in node.bases:
        base_str = _unparse(base)
        if 'BaseModel' in base_str or 'GenericModel' in base_str:
            return True

    # 检查是否有 Config 类 (Pydantic 特有)
    for child in node.body:
        if isinstance(child, ast.ClassDef) and child.name == 'Config':
            return True

    return False


def _is_dataclass(node: ast.ClassDef) -> bool:
    """检查是否是 dataclass"""
    for decorator in node.decorator_list:
        decorator_str = _unparse(decorator)
        if 'dataclass' in decorator_str:
            return True
    return False


def _has_default(node: ast.AnnAssign) -> bool:
    """检查是否有默认值"""
    return node.value is not None


def to_simple_yaml(doc: Dict, indent: int = 0, max_depth: int = 100) -> str:
    """简单的 YAML 转换器 (不依赖 PyYAML)

    Args:
        doc: 要转换的字典
        indent: 缩进级别
        max_depth: 最大递归深度 (防止 RecursionError)

    Returns:
        YAML 格式的字符串
    """
    if indent > max_depth:
        return ''

    lines = []
    prefix = '  ' * indent

    for key, value in doc.items():
        if isinstance(value, dict):
            if value:
                lines.append(f"{prefix}{key}:")
                nested = to_simple_yaml(value, indent + 1, max_depth)
                if nested:
                    lines.append(nested)
            else:
                lines.append(f"{prefix}{key}: {{}}")
        elif isinstance(value, list):
            if value:
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        if item:
                            # 获取第一个键，将 - 和键放在同一行
                            first_key = list(item.keys())[0]
                            first_value = item[first_key]
                            lines.append(f"{prefix}  - {first_key}: {_format_yaml_value(first_value, indent + 2, max_depth)}")
                            # 处理其余键
                            for k, v in list(item.items())[1:]:
                                lines.append(f"{prefix}    {k}: {_format_yaml_value(v, indent + 2, max_depth)}")
                        else:
                            lines.append(f"{prefix}  - {{}}")
                    else:
                        # 简单值
                        lines.append(f"{prefix}  - {_format_yaml_value(item, indent + 1, max_depth)}")
            else:
                lines.append(f"{prefix}{key}: []")
        else:
            lines.append(f"{prefix}{key}: {_format_yaml_value(value, indent, max_depth)}")

    return '\n'.join(lines)


def _format_yaml_value(value: Any, indent: int, max_depth: int) -> str:
    """格式化 YAML 值"""
    if isinstance(value, dict):
        # 嵌套字典需要多行
        lines = []
        prefix = '  ' * (indent + 1)
        for k, v in value.items():
            lines.append(f"{prefix}{k}: {_format_yaml_value(v, indent + 1, max_depth)}")
        return '\n' + '\n'.join(lines)
    elif isinstance(value, list):
        return str(value)
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    elif value is None:
        return 'null'
    elif isinstance(value, str):
        # 如果字符串包含特殊字符，用引号
        if ':' in value or value.startswith('#') or value.startswith(' ') or value.startswith('['):
            return f"'{value}'"
        return value
    else:
        return str(value)
