"""ci-cd-orchestrator 技能实现 - CI/CD 流水线编排器

异常处理:
    - CICDError: CI/CD 流水线生成相关错误
    - ValueError: 不支持的平台或语言
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入自定义异常
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from exceptions import CICDError

# 导入 Pydantic 验证模型
try:
    from pydantic import ValidationError as PydanticValidationError
    from .validation import CICDOrchestratorParams
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============== 常量配置 ==============

# 支持的 CI/CD 平台
SUPPORTED_PLATFORMS = ['github', 'jenkins', 'gitlab', 'azure', 'circleci']

# 工作流阶段默认配置
DEFAULT_STAGES = {
    'test': {
        'enabled': True,
        'timeout': 10,
        'parallel': False
    },
    'build': {
        'enabled': True,
        'timeout': 15,
        'parallel': False
    },
    'deploy': {
        'enabled': False,
        'timeout': 20,
        'parallel': False
    }
}

# 支持的语言及其配置
LANGUAGE_CONFIGS = {
    'python': {
        'test_commands': ['pytest', 'python -m pytest', 'coverage run'],
        'build_commands': ['python -m build', 'poetry build'],
        'package_managers': ['pip', 'poetry', 'uv']
    },
    'javascript': {
        'test_commands': ['npm test', 'yarn test', 'pnpm test'],
        'build_commands': ['npm run build', 'yarn build', 'pnpm build'],
        'package_managers': ['npm', 'yarn', 'pnpm']
    },
    'go': {
        'test_commands': ['go test ./...', 'gotestsum'],
        'build_commands': ['go build', 'gox'],
        'package_managers': ['go']
    },
    'rust': {
        'test_commands': ['cargo test'],
        'build_commands': ['cargo build --release'],
        'package_managers': ['cargo']
    },
    'java': {
        'test_commands': ['mvn test', 'gradle test'],
        'build_commands': ['mvn package', 'gradle build'],
        'package_managers': ['maven', 'gradle']
    }
}

# 支持的部署目标
DEPLOY_TARGETS = {
    'docker': {
        'registry': ['docker.io', 'ghcr.io', 'gcr.io'],
        'commands': ['docker build', 'docker push']
    },
    'kubernetes': {
        'tools': ['kubectl', 'helm', 'kustomize'],
        'commands': ['kubectl apply', 'helm upgrade']
    },
    'serverless': {
        'providers': ['aws', 'azure', 'gcp'],
        'commands': ['serverless deploy', 'sam deploy']
    },
    'static': {
        'providers': ['vercel', 'netlify', 'cloudflare'],
        'commands': ['vercel deploy', 'netlify deploy']
    }
}


def generate_workflow(params):
    """生成 CI/CD 流水线配置

    Args:
        params: 包含以下参数:
            - platform: CI/CD 平台 (github, jenkins, gitlab, azure, circleci)
            - language: 编程语言 (python, javascript, go, rust, java)
            - stages: 要启用的阶段 (test, build, deploy)
            - deploy_target: 部署目标 (docker, kubernetes, serverless, static)
            - output_file: 输出文件路径 (可选)
            - custom_config: 自定义配置 (可选)

    Returns:
        生成的配置内容

    Raises:
        CICDError: CI/CD 配置生成过程中的错误
        ValueError: 不支持的平台或语言
    """
    platform = params.get('platform', 'github')
    language = params.get('language', 'python')
    stages = params.get('stages', ['test', 'build'])
    deploy_target = params.get('deploy_target')
    output_file = params.get('output_file')
    custom_config = params.get('custom_config', {})

    # 验证平台
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f'不支持的平台: {platform}. 支持的平台: {SUPPORTED_PLATFORMS}')

    # 生成配置
    try:
        if platform == 'github':
            config = generate_github_actions(language, stages, deploy_target, custom_config)
        elif platform == 'jenkins':
            config = generate_jenkins_pipeline(language, stages, deploy_target, custom_config)
        elif platform == 'gitlab':
            config = generate_gitlab_ci(language, stages, deploy_target, custom_config)
        elif platform == 'azure':
            config = generate_azure_pipeline(language, stages, deploy_target, custom_config)
        elif platform == 'circleci':
            config = generate_circleci_config(language, stages, deploy_target, custom_config)
        else:
            raise CICDError(f'未实现的平台: {platform}')
    except Exception as e:
        if isinstance(e, (ValueError, CICDError)):
            raise
        raise CICDError(f'生成配置时出错: {str(e)}')

    # 写入文件
    if output_file and 'error' not in config:
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(config['content'], encoding='utf-8')
            config['file'] = str(output_path)
        except (IOError, OSError) as e:
            raise CICDError(f'写入配置文件失败: {str(e)}')

    return config


def generate_github_actions(language: str, stages: List[str],
                          deploy_target: Optional[str],
                          custom_config: Dict) -> Dict:
    """生成 GitHub Actions 工作流配置"""
    lang_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])

    workflow = {
        'name': 'CI/CD Pipeline',
        'on': {
            'push': {'branches': ['main', 'develop']},
            'pull_request': {'branches': ['main', 'develop']}
        },
        'jobs': {}
    }

    # 测试阶段
    if 'test' in stages:
        workflow['jobs']['test'] = {
            'runs-on': 'ubuntu-latest',
            'strategy': {
                'matrix': {
                    'version': _get_version_matrix(language)
                }
            },
            'steps': _generate_test_steps('github', language, lang_config)
        }

    # 构建阶段
    if 'build' in stages:
        workflow['jobs']['build'] = {
            'runs-on': 'ubuntu-latest',
            'needs': ['test'] if 'test' in stages else [],
            'steps': _generate_build_steps('github', language, lang_config)
        }

    # 部署阶段
    if 'deploy' in stages and deploy_target:
        workflow['jobs']['deploy'] = {
            'runs-on': 'ubuntu-latest',
            'needs': ['build'] if 'build' in stages else [],
            'if': "github.ref == 'refs/heads/main'",
            'steps': _generate_deploy_steps('github', deploy_target, custom_config)
        }

    # 转换为 YAML 格式
    content = _dict_to_yaml(workflow)

    return {
        'platform': 'github',
        'format': 'yaml',
        'content': content,
        'recommended_path': '.github/workflows/ci-cd.yml'
    }


def generate_jenkins_pipeline(language: str, stages: List[str],
                             deploy_target: Optional[str],
                             custom_config: Dict) -> Dict:
    """生成 Jenkins Pipeline 配置"""
    lang_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])

    pipeline = [
        'pipeline {',
        '    agent any',
        '',
        '    environment {',
        "        PROJECT_NAME = '${PROJECT_NAME:-my-project}'",
        '        BRANCH_NAME = "${env.GIT_BRANCH ?: \'main\'}"',
        '    }',
        '',
        '    stages {'
    ]

    # 测试阶段
    if 'test' in stages:
        pipeline.extend([
            '        stage("Test") {',
            '            steps {',
            "                echo 'Running tests...'"
        ])
        pipeline.extend(_generate_test_steps('jenkins', language, lang_config))
        pipeline.extend([
            '            }',
            '        }'
        ])

    # 构建阶段
    if 'build' in stages:
        pipeline.extend([
            '        stage("Build") {',
            '            steps {',
            "                echo 'Building project...'"
        ])
        pipeline.extend(_generate_build_steps('jenkins', language, lang_config))
        pipeline.extend([
            '            }',
            '        }'
        ])

    # 部署阶段
    if 'deploy' in stages and deploy_target:
        pipeline.extend([
            '        stage("Deploy") {',
            '            when {',
            "                branch 'main'",
            '            }',
            '            steps {',
            "                echo 'Deploying...'"
        ])
        pipeline.extend(_generate_deploy_steps('jenkins', deploy_target, custom_config))
        pipeline.extend([
            '            }',
            '        }'
        ])

    pipeline.extend([
        '    }',
        '',
        '    post {',
        '        success {',
        "            echo 'Pipeline succeeded!'",
        '        }',
        '        failure {',
        "            echo 'Pipeline failed!'",
        '        }',
        '    }',
        '}'
    ])

    content = '\n'.join(pipeline)

    return {
        'platform': 'jenkins',
        'format': 'groovy',
        'content': content,
        'recommended_path': 'Jenkinsfile'
    }


def generate_gitlab_ci(language: str, stages: List[str],
                      deploy_target: Optional[str],
                      custom_config: Dict) -> Dict:
    """生成 GitLab CI 配置"""
    lang_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])

    config = {
        'stages': [s for s in stages if s in ['test', 'build', 'deploy']],
        'variables': {
            'PROJECT_NAME': '$CI_PROJECT_NAME',
            'BRANCH': '$CI_COMMIT_REF_NAME'
        }
    }

    # 默认配置
    config.setdefault('default', {})['image'] = _get_base_image(language)

    # 测试阶段
    if 'test' in stages:
        config['test'] = {
            'stage': 'test',
            'script': _get_test_scripts(language, lang_config),
            'parallel': _get_parallel_matrix(language),
            'coverage': '/Code coverage: \d+\.\d+/'
        }

    # 构建阶段
    if 'build' in stages:
        config['build'] = {
            'stage': 'build',
            'script': _get_build_scripts(language, lang_config),
            'artifacts': {
                'paths': _get_artifact_paths(language),
                'expire_in': '1 week'
            }
        }

    # 部署阶段
    if 'deploy' in stages and deploy_target:
        config['deploy'] = {
            'stage': 'deploy',
            'script': _get_deploy_scripts(deploy_target, custom_config),
            'only': ['main'],
            'when': 'manual'
        }

    content = _dict_to_yaml(config)

    return {
        'platform': 'gitlab',
        'format': 'yaml',
        'content': content,
        'recommended_path': '.gitlab-ci.yml'
    }


def generate_azure_pipeline(language: str, stages: List[str],
                           deploy_target: Optional[str],
                           custom_config: Dict) -> Dict:
    """生成 Azure Pipelines 配置"""
    lang_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])

    config = {
        'trigger': ['main', 'develop'],
        'variables': {
            'PROJECT_NAME': '$(Build.Repository.Name)',
            'BRANCH': '$(Build.SourceBranchName)'
        },
        'stages': []
    }

    # 测试阶段
    if 'test' in stages:
        test_stage = {
            'stage': 'Test',
            'jobs': [{
                'job': 'Test',
                'steps': _generate_azure_steps('test', language, lang_config)
            }]
        }
        config['stages'].append(test_stage)

    # 构建阶段
    if 'build' in stages:
        build_stage = {
            'stage': 'Build',
            'jobs': [{
                'job': 'Build',
                'steps': _generate_azure_steps('build', language, lang_config)
            }]
        }
        config['stages'].append(build_stage)

    # 部署阶段
    if 'deploy' in stages and deploy_target:
        deploy_stage = {
            'stage': 'Deploy',
            'condition': "and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))",
            'jobs': [{
                'job': 'Deploy',
                'steps': _generate_azure_steps('deploy', language, lang_config)
            }]
        }
        config['stages'].append(deploy_stage)

    content = _dict_to_yaml(config)

    return {
        'platform': 'azure',
        'format': 'yaml',
        'content': content,
        'recommended_path': 'azure-pipelines.yml'
    }


def generate_circleci_config(language: str, stages: List[str],
                             deploy_target: Optional[str],
                             custom_config: Dict) -> Dict:
    """生成 CircleCI 配置"""
    lang_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['python'])

    config = {
        'version': 2.1,
        'executors': {
            'default': {
                'docker': [{'image': _get_base_image(language)}]
            }
        },
        'jobs': {}
    }

    # 测试阶段
    if 'test' in stages:
        config['jobs']['test'] = {
            'executor': 'default',
            'steps': [
                'checkout',
                *_get_circleci_steps('test', language, lang_config)
            ]
        }

    # 构建阶段
    if 'build' in stages:
        config['jobs']['build'] = {
            'executor': 'default',
            'steps': [
                'checkout',
                *_get_circleci_steps('build', language, lang_config)
            ]
        }

    # 工作流
    workflows = {'workflows': {'build-test-deploy': {'jobs': []}}}

    if 'test' in stages:
        workflows['workflows']['build-test-deploy']['jobs'].append('test')

    if 'build' in stages:
        jobs_dict = {'build': {}}
        if 'test' in stages:
            jobs_dict['build']['requires'] = ['test']
        workflows['workflows']['build-test-deploy']['jobs'].append(jobs_dict)

    if 'deploy' in stages and deploy_target:
        config['jobs']['deploy'] = {
            'executor': 'default',
            'steps': [
                'checkout',
                *_get_circleci_steps('deploy', language, lang_config)
            ]
        }
        deploy_job = {'deploy': {'filters': {'branches': {'only': 'main'}}}}
        if 'build' in stages:
            deploy_job['deploy']['requires'] = ['build']
        workflows['workflows']['build-test-deploy']['jobs'].append(deploy_job)

    config.update(workflows)
    content = _dict_to_yaml(config)

    return {
        'platform': 'circleci',
        'format': 'yaml',
        'content': content,
        'recommended_path': '.circleci/config.yml'
    }


# ============== 辅助函数 ==============

def _get_version_matrix(language: str) -> List[str]:
    """获取版本矩阵"""
    versions = {
        'python': ['3.9', '3.10', '3.11', '3.12'],
        'javascript': ['16.x', '18.x', '20.x'],
        'go': ['1.20', '1.21', '1.22'],
        'rust': ['stable', 'beta'],
        'java': ['11', '17', '21']
    }
    return versions.get(language, ['latest'])


def _get_base_image(language: str) -> str:
    """获取基础镜像"""
    images = {
        'python': 'python:3.11-slim',
        'javascript': 'node:20-slim',
        'go': 'golang:1.21',
        'rust': 'rust:1.75-slim',
        'java': 'eclipse-temurin:17-jdk'
    }
    return images.get(language, 'ubuntu:latest')


def _generate_test_steps(platform: str, language: str,
                        lang_config: Dict) -> List[Dict]:
    """生成测试步骤"""
    steps = []
    test_commands = lang_config.get('test_commands', [])

    if platform == 'github':
        steps = [
            {'uses': 'actions/checkout@v4'},
            {'name': f'Set up {language}', 'uses': f'{_get_action_name(language)}'}
        ]

        # 安装依赖
        for pm in lang_config.get('package_managers', []):
            if pm == 'pip':
                steps.append({'name': 'Install dependencies', 'run': 'pip install -e .[test]'})
            elif pm == 'npm':
                steps.append({'name': 'Install dependencies', 'run': 'npm ci'})
            elif pm == 'yarn':
                steps.append({'name': 'Install dependencies', 'run': 'yarn install --frozen-lockfile'})

        # 运行测试
        if test_commands:
            steps.append({'name': 'Run tests', 'run': test_commands[0]})

    elif platform == 'jenkins':
        steps = [
            "sh 'git checkout ${env.GIT_BRANCH}'",
            "echo 'Installing dependencies...'"
        ]
        if test_commands:
            steps.append(f"sh '{test_commands[0]}'")

    return steps


def _generate_build_steps(platform: str, language: str,
                         lang_config: Dict) -> List[Dict]:
    """生成构建步骤"""
    steps = []
    build_commands = lang_config.get('build_commands', [])

    if platform == 'github':
        steps = [
            {'uses': 'actions/checkout@v4'}
        ]

        if build_commands:
            steps.append({'name': 'Build', 'run': build_commands[0]})

        # 上传构建产物
        steps.append({
            'name': 'Upload artifacts',
            'uses': 'actions/upload-artifact@v4',
            'with': {
                'name': 'build-artifacts',
                'path': _get_artifact_paths(language)[0] if _get_artifact_paths(language) else 'dist/'
            }
        })

    elif platform == 'jenkins':
        steps = ["echo 'Building...'"]
        if build_commands:
            steps.append(f"sh '{build_commands[0]}'")

    return steps


def _generate_deploy_steps(platform: str, deploy_target: str,
                          custom_config: Dict) -> List[Dict]:
    """生成部署步骤"""
    steps = []

    if platform == 'github':
        if deploy_target == 'docker':
            steps = [
                {'name': 'Set up Docker Buildx', 'uses': 'docker/setup-buildx-action@v3'},
                {'name': 'Login to registry', 'uses': 'docker/login-action@v3',
                 'with': {'registry': '${{ secrets.DOCKER_REGISTRY }}', 'username': '${{ secrets.DOCKER_USERNAME }}', 'password': '${{ secrets.DOCKER_PASSWORD }}'}},
                {'name': 'Build and push', 'uses': 'docker/build-push-action@v5',
                 'with': {'context': '.', 'push': True, 'tags': '${{ secrets.DOCKER_REGISTRY }}/${{ github.repository }}:latest'}}
            ]
        elif deploy_target == 'kubernetes':
            steps = [
                {'name': 'Deploy to Kubernetes', 'run': 'kubectl apply -f k8s/'}
            ]
        elif deploy_target == 'static':
            steps = [
                {'name': 'Deploy to Vercel', 'uses': 'amondnet/vercel-action@v25',
                 'with': {'vercel-token': '${{ secrets.VERCEL_TOKEN }}', 'vercel-org-id': '${{ secrets.VERCEL_ORG_ID }}', 'vercel-project-id': '${{ secrets.VERCEL_PROJECT_ID }}'}}
            ]
    elif platform == 'jenkins':
        if deploy_target == 'docker':
            steps = [
                "sh 'docker build -t ${PROJECT_NAME}:${BUILD_NUMBER} .'",
                "sh 'docker push ${PROJECT_NAME}:${BUILD_NUMBER}'"
            ]

    return steps


def _get_action_name(language: str) -> str:
    """获取 GitHub Action 名称"""
    actions = {
        'python': 'actions/setup-python@v5',
        'javascript': 'actions/setup-node@v4',
        'go': 'actions/setup-go@v5',
        'rust': 'dtolnay/rust-toolchain@stable',
        'java': 'actions/setup-java@v4'
    }
    return actions.get(language, 'actions/setup-python@v5')


def _get_test_scripts(language: str, lang_config: Dict) -> List[str]:
    """获取测试脚本"""
    return lang_config.get('test_commands', ['echo "No test command configured"'])


def _get_build_scripts(language: str, lang_config: Dict) -> List[str]:
    """获取构建脚本"""
    return lang_config.get('build_commands', ['echo "No build command configured"'])


def _get_deploy_scripts(deploy_target: str, custom_config: Dict) -> List[str]:
    """获取部署脚本"""
    if deploy_target == 'docker':
        return [
            'docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY',
            'docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .',
            'docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA'
        ]
    elif deploy_target == 'kubernetes':
        return ['kubectl apply -f k8s/']
    return ['echo "Deployment not configured"']


def _get_artifact_paths(language: str) -> List[str]:
    """获取构建产物路径"""
    paths = {
        'python': ['dist/'],
        'javascript': ['dist/', 'build/'],
        'go': ['bin/'],
        'rust': ['target/release/'],
        'java': ['target/*.jar']
    }
    return paths.get(language, ['dist/'])


def _get_parallel_matrix(language: str) -> Dict:
    """获取并行矩阵配置"""
    return {'matrix': _get_version_matrix(language)}


def _generate_azure_steps(stage: str, language: str, lang_config: Dict) -> List[Dict]:
    """生成 Azure Pipelines 步骤"""
    steps = []

    if stage == 'test':
        steps.append({'task': 'UsePythonVersion', 'inputs': {'versionSpec': '3.x'}})
        steps.append({'script': 'pip install -e .[test]'})
        test_cmd = lang_config.get('test_commands', ['echo "No test command"'])[0]
        steps.append({'script': test_cmd})
    elif stage == 'build':
        build_cmd = lang_config.get('build_commands', ['echo "No build command"'])[0]
        steps.append({'script': build_cmd})
        steps.append({'task': 'PublishBuildArtifacts', 'inputs': {'PathtoPublish': 'dist/'}})

    return steps


def _get_circleci_steps(stage: str, language: str, lang_config: Dict) -> List:
    """获取 CircleCI 步骤"""
    steps = []

    if stage == 'test':
        steps.append({'run': {'name': 'Install dependencies', 'command': 'pip install -e .[test]'}})
        test_cmd = lang_config.get('test_commands', ['echo "No test command"'])[0]
        steps.append({'run': {'name': 'Run tests', 'command': test_cmd}})
    elif stage == 'build':
        build_cmd = lang_config.get('build_commands', ['echo "No build command"'])[0]
        steps.append({'run': {'name': 'Build', 'command': build_cmd}})

    return steps


def _dict_to_yaml(data: Dict) -> str:
    """将字典转换为 YAML 格式字符串"""
    lines = []
    _dict_to_yaml_lines(data, lines, 0)
    return '\n'.join(lines)


def _dict_to_yaml_lines(data: Any, lines: List[str], indent: int):
    """递归转换字典为 YAML 行"""
    indent_str = '  ' * indent

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                _dict_to_yaml_lines(value, lines, indent + 1)
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"{indent_str}  -")
                        _dict_to_yaml_lines(item, lines, indent + 2)
                    else:
                        lines.append(f"{indent_str}  - {item}")
            else:
                lines.append(f"{indent_str}{key}: {value}")
    else:
        lines.append(f"{indent_str}{data}")


def validate_workflow(config_path: str) -> Dict:
    """验证工作流配置

    Args:
        config_path: 配置文件路径

    Returns:
        验证结果
    """
    config_file = Path(config_path)

    if not config_file.exists():
        return {'valid': False, 'error': f'配置文件不存在: {config_path}'}

    try:
        content = config_file.read_text(encoding='utf-8')

        # 简单验证 - 检查基本结构
        if config_path.endswith('.yml') or config_path.endswith('.yaml'):
            # 检查 YAML 基本结构
            if 'jobs' in content or 'stages' in content or 'workflow' in content:
                return {'valid': True, 'message': '配置文件结构有效'}
            else:
                return {'valid': False, 'error': '缺少必要的配置项 (jobs/stages/workflow)'}

        elif config_path == 'Jenkinsfile':
            if 'pipeline' in content and 'stages' in content:
                return {'valid': True, 'message': 'Jenkinsfile 结构有效'}
            else:
                return {'valid': False, 'error': 'Jenkinsfile 缺少 pipeline 或 stages 块'}

        return {'valid': True, 'message': '配置文件已加载'}

    except Exception as e:
        return {'valid': False, 'error': f'读取配置文件失败: {str(e)}'}


def list_templates() -> Dict:
    """列出可用的流水线模板"""
    return {
        'platforms': SUPPORTED_PLATFORMS,
        'languages': list(LANGUAGE_CONFIGS.keys()),
        'stages': ['test', 'build', 'deploy'],
        'deploy_targets': list(DEPLOY_TARGETS.keys()),
        'templates': {
            'github-python': 'GitHub Actions for Python',
            'github-node': 'GitHub Actions for Node.js',
            'jenkins-python': 'Jenkins Pipeline for Python',
            'gitlab-go': 'GitLab CI for Go',
            'docker-deploy': 'Docker 部署模板',
            'k8s-deploy': 'Kubernetes 部署模板'
        }
    }


def execute_skill(params):
    """执行技能

    Args:
        params: 技能参数

    Returns:
        执行结果

    Raises:
        CICDError: CI/CD 操作过程中的错误
    """
    # 使用 Pydantic 验证输入参数
    if PYDANTIC_AVAILABLE:
        try:
            validated = CICDOrchestratorParams(**params)
            # 转换为字典用于后续处理
            params = validated.dict(exclude_unset=True)
        except PydanticValidationError as e:
            return {
                'success': False,
                'error': '输入参数验证失败',
                'validation_errors': e.errors()
            }

    action = params.get('action', 'generate')

    try:
        if action == 'generate':
            return generate_workflow(params)
        elif action == 'validate':
            config_path = params.get('config_path')
            if not config_path:
                return {'error': '请指定配置文件路径'}
            return validate_workflow(config_path)
        elif action == 'list':
            return list_templates()
        elif action == 'help':
            return {
                'description': 'CI/CD 流水线编排器',
                'actions': ['generate', 'validate', 'list'],
                'platforms': SUPPORTED_PLATFORMS,
                'languages': list(LANGUAGE_CONFIGS.keys()),
                'example': {
                    'action': 'generate',
                    'platform': 'github',
                    'language': 'python',
                    'stages': ['test', 'build', 'deploy'],
                    'deploy_target': 'docker',
                    'output_file': '.github/workflows/ci.yml'
                }
            }
        else:
            raise ValueError(f'未知操作: {action}. 支持的操作: generate, validate, list, help')
    except ValueError as e:
        logger.error(f"CI/CD 参数错误: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    except CICDError as e:
        logger.error(f"CI/CD 操作错误: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"CI/CD 操作时出现未预期错误: {e}")
        return {
            'success': False,
            'error': f'操作失败: {str(e)}'
        }
