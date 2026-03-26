"""environment-manager 技能实现 - 环境配置管理

异常处理:
    - EnvironmentManagerError: 环境配置管理相关错误
    - (IOError, OSError): 文件读写错误
"""

import os
import re
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 导入自定义异常
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from exceptions import EnvironmentManagerError

# 导入 Pydantic 验证模型
try:
    from pydantic import ValidationError as PydanticValidationError
    from .validation import EnvironmentManagerParams
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============== 常量配置 ==============
DEFAULT_ENV_FILES = [
    '.env',
    '.env.local',
    '.env.production',
    '.env.development',
    '.env.test',
    '.env.example',
    'config/.env',
]

SECRET_PATTERNS = [
    r'password\s*=\s*["\']?[^"\'\s]+["\']?',
    r'passwd\s*=\s*["\']?[^"\'\s]+["\']?',
    r'api_key\s*=\s*["\']?[^"\'\s]+["\']?',
    r'apikey\s*=\s*["\']?[^"\'\s]+["\']?',
    r'secret\s*=\s*["\']?[^"\'\s]+["\']?',
    r'token\s*=\s*["\']?[^"\'\s]+["\']?',
    r'private_key\s*=\s*["\']?[^"\'\s]+["\']?',
    r'auth_token\s*=\s*["\']?[^"\'\s]+["\']?',
    r'access_token\s*=\s*["\']?[^"\'\s]+["\']?',
    r'aws_access_key\s*=\s*["\']?[^"\'\s]+["\']?',
    r'aws_secret_key\s*=\s*["\']?[^"\'\s]+["\']?',
    r'database_url\s*=\s*["\']?[^"\']+["\']?',
    r'db_password\s*=\s*["\']?[^"\'\s]+["\']?',
    r'redis_password\s*=\s*["\']?[^"\'\s]+["\']?',
]

REQUIRED_ENV_VARS = [
    'PATH',
    'HOME',
]

# 配置验证规则
CONFIG_SCHEMAS = {
    'database': {
        'required_fields': ['host', 'port', 'name'],
        'optional_fields': ['user', 'password', 'ssl', 'pool_size'],
        'validators': {
            'port': r'^\d+$',
            'host': r'^[\w\.-]+$',
        }
    },
    'api': {
        'required_fields': ['base_url', 'timeout'],
        'optional_fields': ['api_key', 'retry_count', 'rate_limit'],
        'validators': {
            'timeout': r'^\d+$',
            'base_url': r'^https?://[\w\.-]+',
        }
    },
    'logging': {
        'required_fields': ['level'],
        'optional_fields': ['file', 'format', 'max_size'],
        'validators': {
            'level': r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$',
        }
    }
}


def execute_skill(params: Dict) -> Dict:
    """执行技能 - 环境配置管理

    Args:
        params: 技能参数，包含:
            - action: 操作类型 (detect, generate, validate, audit)
            - project_dir: 项目目录路径
            - env_file: 环境文件路径 (可选)
            - config_type: 配置类型 (database, api, logging 等，用于 validate)
            - output_format: 输出格式 (json, env, yaml)

    Returns:
        操作结果字典

    Raises:
        EnvironmentManagerError: 环境配置管理过程中的错误
        FileNotFoundError: 项目目录不存在
    """
    # 使用 Pydantic 验证输入参数
    if PYDANTIC_AVAILABLE:
        try:
            validated = EnvironmentManagerParams(**params)
            # 转换为字典用于后续处理
            params = validated.dict(exclude_unset=True)
        except PydanticValidationError as e:
            return {
                'success': False,
                'error': '输入参数验证失败',
                'validation_errors': e.errors()
            }

    action = params.get('action', 'detect')
    project_dir = params.get('project_dir', os.getcwd())
    env_file = params.get('env_file')
    config_type = params.get('config_type')
    output_format = params.get('output_format', 'json')

    result = {
        'action': action,
        'project_dir': project_dir,
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'data': None,
        'warnings': [],
        'errors': []
    }

    try:
        if action == 'detect':
            result['data'] = detect_environment_diff(project_dir)
            result['success'] = True

        elif action == 'generate':
            result['data'] = generate_config(
                project_dir,
                env_file=env_file,
                output_format=output_format
            )
            result['success'] = True

        elif action == 'validate':
            if not config_type:
                result['errors'].append('config_type is required for validate action')
            else:
                result['data'] = validate_config(
                    project_dir,
                    config_type,
                    env_file=env_file
                )
                result['success'] = True

        elif action == 'audit':
            result['data'] = audit_security(project_dir)
            result['success'] = True

        else:
            result['errors'].append(f'Unknown action: {action}')

    except FileNotFoundError as e:
        logger.error(f"环境检测错误 - 文件不存在: {e}")
        result['errors'].append(f'文件不存在: {str(e)}')
    except (IOError, OSError) as e:
        logger.error(f"环境检测错误 - 文件操作失败: {e}")
        result['errors'].append(f'文件操作失败: {str(e)}')
    except EnvironmentManagerError as e:
        logger.error(f"环境配置管理错误: {e}")
        result['errors'].append(str(e))
    except Exception as e:
        logger.error(f"执行 environment-manager 技能时出现未预期错误: {str(e)}")
        result['errors'].append(f'未预期的错误: {str(e)}')

    return result


def detect_environment_diff(project_dir: str) -> Dict:
    """检测环境差异

    Args:
        project_dir: 项目目录路径

    Returns:
        环境差异检测结果
    """
    project_path = Path(project_dir)

    if not project_path.exists():
        raise EnvironmentManagerError(f"项目目录不存在: {project_dir}")

    result = {
        'project_dir': str(project_path.absolute()),
        'env_files_found': [],
        'env_files_missing': [],
        'system_env': {},
        'dotenv_vars': {},
        'differences': [],
        'recommendations': []
    }

    # 1. 检查环境文件
    for env_file in DEFAULT_ENV_FILES:
        env_path = project_path / env_file
        if env_path.exists():
            result['env_files_found'].append(env_file)
            # 读取环境变量
            env_vars = parse_env_file(env_path)
            result['dotenv_vars'].update(env_vars)
        else:
            result['env_files_missing'].append(env_file)

    # 2. 检查系统环境变量
    system_env = {}
    for key in REQUIRED_ENV_VARS:
        if key in os.environ:
            system_env[key] = os.environ[key]

    result['system_env'] = system_env

    # 3. 检查Python环境
    python_info = detect_python_env()
    result['python_env'] = python_info

    # 4. 检测差异
    result['differences'] = find_environment_differences(
        system_env,
        result['dotenv_vars']
    )

    # 5. 生成建议
    result['recommendations'] = generate_env_recommendations(result)

    return result


def parse_env_file(env_path: Path) -> Dict[str, str]:
    """解析 .env 文件

    Args:
        env_path: .env 文件路径

    Returns:
        环境变量字典
    """
    env_vars = {}

    try:
        content = env_path.read_text(encoding='utf-8')
    except (IOError, OSError) as e:
        logger.warning(f"读取环境文件 {env_path} 时出错: {str(e)}")
        return env_vars

    for line in content.split('\n'):
        line = line.strip()
        # 跳过注释和空行
        if not line or line.startswith('#'):
            continue

        # 解析 KEY=VALUE
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env_vars[key] = value

    return env_vars


def detect_python_env() -> Dict:
    """检测 Python 环境

    Returns:
        Python 环境信息
    """
    python_info = {
        'version': os.sys.version,
        'executable': os.sys.executable,
        'path': os.sys.path[:5],  # 前5个路径
        'packages': []
    }

    # 尝试检测已安装的包
    try:
        import pkg_resources
        installed_packages = [
            f"{d.project_name}=={d.version}"
            for d in sorted(pkg_resources.working_set)
        ]
        python_info['packages'] = installed_packages[:20]  # 限制数量
    except ImportError:
        pass

    return python_info


def find_environment_differences(
    system_env: Dict[str, str],
    dotenv_vars: Dict[str, str]
) -> List[Dict]:
    """查找环境差异

    Args:
        system_env: 系统环境变量
        dotenv_vars: .env 文件中的变量

    Returns:
        差异列表
    """
    differences = []

    # 检查 .env 中定义但在系统环境中缺失的变量
    for key, value in dotenv_vars.items():
        if key not in system_env:
            differences.append({
                'type': 'missing_in_system',
                'key': key,
                'env_value': value,
                'severity': 'info'
            })
        elif system_env[key] != value:
            differences.append({
                'type': 'value_mismatch',
                'key': key,
                'system_value': system_env[key],
                'env_value': value,
                'severity': 'warning'
            })

    return differences


def generate_env_recommendations(result: Dict) -> List[str]:
    """生成环境配置建议

    Args:
        result: 环境检测结果

    Returns:
        建议列表
    """
    recommendations = []

    # 检查是否有 .env.example
    if '.env.example' not in result['env_files_found']:
        recommendations.append(
            "建议创建 .env.example 文件作为环境变量模板"
        )

    # 检查是否有 .env.local
    if '.env.local' not in result['env_files_found']:
        recommendations.append(
            "建议使用 .env.local 存储本地特定的环境变量"
        )

    # 检查 .env 是否在 .gitignore 中
    project_path = Path(result['project_dir'])
    gitignore_path = project_path / '.gitignore'
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
        if '.env' not in gitignore_content:
            recommendations.append(
                "警告: .env 文件未在 .gitignore 中，可能导致敏感信息泄露"
            )

    return recommendations


def generate_config(
    project_dir: str,
    env_file: Optional[str] = None,
    output_format: str = 'json'
) -> Dict:
    """生成配置文件

    Args:
        project_dir: 项目目录路径
        env_file: 环境文件路径 (可选)
        output_format: 输出格式 (json, env, yaml)

    Returns:
        生成的配置内容
    """
    project_path = Path(project_dir)

    result = {
        'config': {},
        'format': output_format,
        'file_path': None
    }

    # 收集环境变量
    env_vars = {}

    # 从系统环境变量收集
    env_vars.update({
        k: v for k, v in os.environ.items()
        if not k.startswith('_') and k.isupper()
    })

    # 从 .env 文件收集
    if env_file:
        env_path = project_path / env_file
        if env_path.exists():
            env_vars.update(parse_env_file(env_path))
            result['source_file'] = env_file

    # 生成配置
    if output_format == 'json':
        result['config'] = json.dumps(env_vars, indent=2, ensure_ascii=False)
        result['file_path'] = str(project_path / 'config.json')

    elif output_format == 'env':
        lines = []
        for key, value in sorted(env_vars.items()):
            lines.append(f'{key}={value}')
        result['config'] = '\n'.join(lines)
        result['file_path'] = str(project_path / '.env.generated')

    elif output_format == 'yaml':
        try:
            import yaml
            result['config'] = yaml.dump(env_vars, default_flow_style=False)
            result['file_path'] = str(project_path / 'config.yaml')
        except ImportError:
            result['config'] = '# PyYAML 未安装，无法生成 YAML 格式'
            result['warnings'] = ['Install PyYAML for YAML support']

    else:
        result['config'] = json.dumps(env_vars, indent=2)
        result['warnings'] = [f'Unknown format: {output_format}, using JSON']

    return result


def validate_config(
    project_dir: str,
    config_type: str,
    env_file: Optional[str] = None
) -> Dict:
    """验证配置

    Args:
        project_dir: 项目目录路径
        config_type: 配置类型 (database, api, logging)
        env_file: 环境文件路径 (可选)

    Returns:
        验证结果
    """
    project_path = Path(project_dir)

    result = {
        'config_type': config_type,
        'valid': True,
        'errors': [],
        'warnings': [],
        'missing_fields': [],
        'invalid_fields': []
    }

    # 获取配置 schema
    schema = CONFIG_SCHEMAS.get(config_type)
    if not schema:
        result['valid'] = False
        result['errors'].append(f'Unknown config type: {config_type}')
        return result

    # 读取配置
    config_vars = {}
    if env_file:
        env_path = project_path / env_file
        if env_path.exists():
            config_vars = parse_env_file(env_path)

    # 检查必需字段
    for field in schema['required_fields']:
        env_key = f'{config_type.upper()}_{field.upper()}'
        if env_key not in config_vars:
            result['missing_fields'].append({
                'field': field,
                'env_key': env_key
            })
            result['valid'] = False

    # 验证字段值
    validators = schema.get('validators', {})
    for field, pattern in validators.items():
        env_key = f'{config_type.upper()}_{field.upper()}'
        if env_key in config_vars:
            value = config_vars[env_key]
            if not re.match(pattern, str(value)):
                result['invalid_fields'].append({
                    'field': field,
                    'env_key': env_key,
                    'value': value,
                    'pattern': pattern
                })
                result['valid'] = False

    # 生成建议
    if result['valid']:
        result['message'] = f'{config_type} 配置验证通过'
    else:
        result['message'] = f'{config_type} 配置验证失败'

    return result


def audit_security(project_dir: str) -> Dict:
    """审计安全风险

    Args:
        project_dir: 项目目录路径

    Returns:
        安全审计结果
    """
    project_path = Path(project_dir)

    result = {
        'scan_dir': str(project_path.absolute()),
        'files_scanned': 0,
        'secrets_found': [],
        'risk_level': 'low',
        'recommendations': []
    }

    # 扫描常见文件类型
    extensions = ['.py', '.js', '.ts', '.json', '.yml', '.yaml', '.env', '.sh', '.bash']
    files_to_scan = []

    for ext in extensions:
        files_to_scan.extend(project_path.rglob(f'*{ext}'))

    # 扫描文件
    for file_path in files_to_scan:
        # 跳过 node_modules, venv 等目录
        if any(skip in str(file_path) for skip in ['node_modules', 'venv', '__pycache__', '.git']):
            continue

        result['files_scanned'] += 1

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            secrets = scan_for_secrets(content, file_path)
            result['secrets_found'].extend(secrets)

        except Exception as e:
            logger.debug(f"扫描文件 {file_path} 时出错: {str(e)}")

    # 计算风险等级
    critical_count = sum(1 for s in result['secrets_found'] if s['severity'] == 'critical')
    high_count = sum(1 for s in result['secrets_found'] if s['severity'] == 'high')

    if critical_count > 0:
        result['risk_level'] = 'critical'
    elif high_count > 0:
        result['risk_level'] = 'high'
    elif len(result['secrets_found']) > 0:
        result['risk_level'] = 'medium'

    # 生成建议
    result['recommendations'] = generate_security_recommendations(result)

    return result


def scan_for_secrets(content: str, file_path: Path) -> List[Dict]:
    """扫描内容中的敏感信息

    Args:
        content: 文件内容
        file_path: 文件路径

    Returns:
        发现的敏感信息列表
    """
    secrets = []
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # 确定严重程度
                severity = 'medium'
                if any(keyword in line.lower() for keyword in ['secret', 'password', 'key']):
                    severity = 'high'
                if any(keyword in line.lower() for keyword in ['private', 'token', 'aws_secret']):
                    severity = 'critical'

                secrets.append({
                    'file': str(file_path.relative_to(file_path.anchor)),
                    'line': i,
                    'pattern': pattern,
                    'content': line.strip()[:50],  # 截断显示
                    'severity': severity
                })
                break  # 每行只记录一次

    return secrets


def generate_security_recommendations(result: Dict) -> List[str]:
    """生成安全建议

    Args:
        result: 安全审计结果

    Returns:
        建议列表
    """
    recommendations = []

    if result['risk_level'] == 'critical':
        recommendations.append(
            "严重风险: 发现潜在的私钥或敏感凭证，请立即移除并轮换"
        )

    if result['risk_level'] in ['critical', 'high']:
        recommendations.append(
            "高风险: 建议使用环境变量或密钥管理服务存储敏感信息"
        )

    # 检查是否有 .env 文件被提交
    env_secrets = [
        s for s in result['secrets_found']
        if '.env' in s['file'] and s['severity'] in ['high', 'critical']
    ]
    if env_secrets:
        recommendations.append(
            "警告: .env 文件可能包含敏感信息，确保其在 .gitignore 中"
        )

    # 检查代码中的硬编码密钥
    code_secrets = [
        s for s in result['secrets_found']
        if s['file'].endswith(('.py', '.js', '.ts'))
    ]
    if code_secrets:
        recommendations.append(
            "建议: 将代码中的硬编码密钥移至环境变量"
        )

    if len(recommendations) == 0:
        recommendations.append("未发现明显的安全风险，继续保持良好的安全实践")

    return recommendations


def manage_secrets(
    action: str,
    key: str,
    value: Optional[str] = None,
    project_dir: str = None
) -> Dict:
    """管理密钥

    Args:
        action: 操作类型 (set, get, delete, list)
        key: 密钥名称
        value: 密钥值 (set 操作需要)
        project_dir: 项目目录路径

    Returns:
        操作结果
    """
    project_path = Path(project_dir or os.getcwd())
    secrets_file = project_path / '.secrets.json'

    result = {
        'action': action,
        'key': key,
        'success': False
    }

    # 读取现有密钥
    secrets = {}
    if secrets_file.exists():
        try:
            secrets = json.loads(secrets_file.read_text())
        except Exception as e:
            result['error'] = f"读取密钥文件失败: {str(e)}"
            return result

    if action == 'set':
        if not value:
            result['error'] = "set 操作需要提供 value"
            return result
        secrets[key] = value
        result['success'] = True

    elif action == 'get':
        if key in secrets:
            result['value'] = secrets[key]
            result['success'] = True
        else:
            result['error'] = f"密钥不存在: {key}"

    elif action == 'delete':
        if key in secrets:
            del secrets[key]
            result['success'] = True
        else:
            result['error'] = f"密钥不存在: {key}"

    elif action == 'list':
        result['keys'] = list(secrets.keys())
        result['success'] = True

    else:
        result['error'] = f"未知操作: {action}"
        return result

    # 保存密钥 (如果修改了)
    if action in ['set', 'delete'] and result['success']:
        try:
            secrets_file.write_text(json.dumps(secrets, indent=2))
        except Exception as e:
            result['error'] = f"保存密钥文件失败: {str(e)}"
            result['success'] = False

    return result
