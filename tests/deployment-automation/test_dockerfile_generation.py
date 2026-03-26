"""Deployment Automation Dockerfile 生成测试"""

import pytest


class TestDockerfileGeneration:
    """测试 Dockerfile 生成"""

    def test_python_dockerfile(self, deployment_module):
        """测试 Python Dockerfile 生成"""
        generate_dockerfile = getattr(deployment_module, 'generate_dockerfile', None)
        if generate_dockerfile is None:
            pytest.skip("generate_dockerfile 函数不存在")

        result = generate_dockerfile('python')

        assert 'FROM' in result
        assert 'python' in result.lower()
        assert 'WORKDIR' in result or 'workdir' in result.lower()

    def test_node_dockerfile(self, deployment_module):
        """测试 Node.js Dockerfile 生成"""
        generate_dockerfile = getattr(deployment_module, 'generate_dockerfile', None)
        if generate_dockerfile is None:
            pytest.skip("generate_dockerfile 函数不存在")

        result = generate_dockerfile('node')

        assert 'FROM' in result
        assert 'node' in result.lower()

    def test_multi_stage_build(self, deployment_module):
        """测试多阶段构建"""
        generate_dockerfile = getattr(deployment_module, 'generate_dockerfile', None)
        if generate_dockerfile is None:
            pytest.skip("generate_dockerfile 函数不存在")

        result = generate_dockerfile('python', multi_stage=True)

        # 多阶段构建应该有多个 FROM 指令
        assert result.count('FROM') >= 2
