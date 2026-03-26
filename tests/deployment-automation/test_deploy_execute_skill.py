"""Deployment Automation execute_skill 函数测试"""

import pytest


class TestExecuteSkill:
    """测试 execute_skill 函数"""

    def test_generate_dockerfile(self, deployment_module, docker_params):
        """测试生成 Dockerfile"""
        execute_skill = deployment_module.execute_skill
        result = execute_skill(docker_params)

        assert result.get('success') is True
        assert 'message' in result

    def test_generate_kubernetes_config(self, deployment_module, kubernetes_params):
        """测试生成 Kubernetes 配置"""
        execute_skill = deployment_module.execute_skill
        result = execute_skill(kubernetes_params)

        assert result.get('success') is True
        assert 'message' in result

    def test_generate_blue_green_deployment(self, deployment_module, blue_green_params):
        """测试生成蓝绿部署配置"""
        execute_skill = deployment_module.execute_skill
        result = execute_skill(blue_green_params)

        assert result.get('success') is True
        assert 'message' in result

    def test_supported_languages(self, deployment_module):
        """测试支持的语言"""
        execute_skill = deployment_module.execute_skill
        for lang in ['python', 'node', 'go', 'java']:
            result = execute_skill({
                'action': 'generate',
                'deployment_type': 'docker',
                'language': lang
            })
            assert result.get('success') is True

    def test_list_templates(self, deployment_module):
        """测试列出模板"""
        execute_skill = deployment_module.execute_skill
        result = execute_skill({'action': 'list'})

        assert result.get('success') is True
