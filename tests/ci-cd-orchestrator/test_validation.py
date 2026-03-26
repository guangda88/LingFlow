"""CI/CD Orchestrator 参数验证测试"""

import pytest


class TestValidation:
    """测试参数验证"""

    def test_supported_platforms(self, ci_cd_module):
        """测试支持的平台列表"""
        assert 'github' in ci_cd_module.SUPPORTED_PLATFORMS
        assert 'jenkins' in ci_cd_module.SUPPORTED_PLATFORMS
        assert 'gitlab' in ci_cd_module.SUPPORTED_PLATFORMS
        assert 'azure' in ci_cd_module.SUPPORTED_PLATFORMS
        assert 'circleci' in ci_cd_module.SUPPORTED_PLATFORMS

    def test_language_configs(self, ci_cd_module):
        """测试语言配置"""
        assert 'python' in ci_cd_module.LANGUAGE_CONFIGS
        assert 'javascript' in ci_cd_module.LANGUAGE_CONFIGS
        assert 'go' in ci_cd_module.LANGUAGE_CONFIGS
        assert 'rust' in ci_cd_module.LANGUAGE_CONFIGS
        assert 'java' in ci_cd_module.LANGUAGE_CONFIGS

        # 验证 Python 配置
        python_config = ci_cd_module.LANGUAGE_CONFIGS['python']
        assert 'test_commands' in python_config
        assert 'build_commands' in python_config
        assert 'package_managers' in python_config

    def test_deploy_targets(self, ci_cd_module):
        """测试部署目标"""
        assert 'docker' in ci_cd_module.DEPLOY_TARGETS
        assert 'kubernetes' in ci_cd_module.DEPLOY_TARGETS
        assert 'serverless' in ci_cd_module.DEPLOY_TARGETS
        assert 'static' in ci_cd_module.DEPLOY_TARGETS


class TestVersionMatrix:
    """测试版本矩阵"""

    def test_python_versions(self, ci_cd_module):
        """测试 Python 版本矩阵"""
        versions = ci_cd_module._get_version_matrix('python')
        assert len(versions) >= 3
        assert '3.11' in versions or '3.12' in versions

    def test_javascript_versions(self, ci_cd_module):
        """测试 JavaScript 版本矩阵"""
        versions = ci_cd_module._get_version_matrix('javascript')
        assert len(versions) >= 2
        assert any('18' in v or '20' in v for v in versions)

    def test_unknown_language_versions(self, ci_cd_module):
        """测试未知语言的版本矩阵"""
        versions = ci_cd_module._get_version_matrix('unknown')
        assert versions == ['latest']
