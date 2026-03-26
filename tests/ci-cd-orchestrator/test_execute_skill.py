"""CI/CD Orchestrator execute_skill 函数测试"""

import pytest


class TestExecuteSkill:
    """测试 execute_skill 函数"""

    def test_generate_github_action(self, ci_cd_module, github_params):
        """测试生成 GitHub Actions 配置"""
        execute_skill = ci_cd_module.execute_skill
        result = execute_skill(github_params)

        assert 'error' not in result
        assert result['platform'] == 'github'
        assert result['format'] == 'yaml'
        assert 'content' in result
        assert 'recommended_path' in result

    def test_generate_jenkins_pipeline(self, ci_cd_module, jenkins_params):
        """测试生成 Jenkins Pipeline"""
        execute_skill = ci_cd_module.execute_skill
        result = execute_skill(jenkins_params)

        assert 'error' not in result
        assert result['platform'] == 'jenkins'
        assert result['format'] == 'groovy'
        assert 'content' in result
        assert 'pipeline' in result['content']

    def test_generate_gitlab_ci(self, ci_cd_module, gitlab_params):
        """测试生成 GitLab CI 配置"""
        execute_skill = ci_cd_module.execute_skill
        result = execute_skill(gitlab_params)

        assert 'error' not in result
        assert result['platform'] == 'gitlab'
        assert result['format'] == 'yaml'

    def test_unsupported_platform(self, ci_cd_module):
        """测试不支持的平台"""
        execute_skill = ci_cd_module.execute_skill
        result = execute_skill({
            'action': 'generate',
            'platform': 'unsupported_platform',
            'language': 'python'
        })

        assert result['success'] is False
        assert 'error' in result

    def test_list_templates(self, ci_cd_module):
        """测试列出模板"""
        execute_skill = ci_cd_module.execute_skill
        result = execute_skill({'action': 'list'})

        assert 'platforms' in result
        assert 'languages' in result
        assert 'templates' in result
        assert 'github' in result['platforms']

    def test_help_action(self, ci_cd_module):
        """测试帮助操作"""
        execute_skill = ci_cd_module.execute_skill
        result = execute_skill({'action': 'help'})

        assert 'description' in result
        assert 'actions' in result
        assert 'platforms' in result

    def test_invalid_action(self, ci_cd_module):
        """测试无效操作"""
        execute_skill = ci_cd_module.execute_skill
        result = execute_skill({'action': 'invalid_action'})

        assert result['success'] is False
        assert 'error' in result
