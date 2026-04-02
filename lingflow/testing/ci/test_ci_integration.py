#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CI/CD 集成测试
测试 GitHub Actions 工作流配置和集成
"""

import pytest
import yaml
from pathlib import Path
from typing import Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCIWorkflowConfiguration:
    """CI 工作流配置测试"""

    @property
    def _workflow_path(self) -> Path:
        """获取工作流文件路径"""
        return Path(__file__).parent.parent.parent.parent / ".github" / "workflows" / "testing-framework.yml"

    def test_workflow_file_exists(self):
        """测试工作流文件存在"""
        root_dir = Path(__file__).parent.parent.parent.parent
        workflow_path = root_dir / ".github" / "workflows" / "testing-framework.yml"
        assert workflow_path.exists(), "CI 工作流文件应该存在"

    def test_workflow_yaml_valid(self):
        """测试工作流 YAML 格式有效"""
        root_dir = Path(__file__).parent.parent.parent.parent
        workflow_path = root_dir / ".github" / "workflows" / "testing-framework.yml"

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        assert workflow is not None
        assert "name" in workflow
        assert "jobs" in workflow

    def test_workflow_has_required_jobs(self):
        """测试工作流包含必需的任务"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get("jobs", {})
        required_jobs = [
            "unit-tests",
            "snapshot-tests",
            "scenario-tests",
            "e2e-tests",
            "test-coverage"
        ]

        for job in required_jobs:
            assert job in jobs, f"工作流应该包含 {job} 任务"

    def test_unit_tests_matrix(self):
        """测试单元测试矩阵配置"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        unit_tests = workflow["jobs"]["unit-tests"]
        assert "strategy" in unit_tests
        assert "matrix" in unit_tests["strategy"]
        assert "python-version" in unit_tests["strategy"]["matrix"]

        python_versions = unit_tests["strategy"]["matrix"]["python-version"]
        assert "3.12" in python_versions

    def test_coverage_threshold(self):
        """测试覆盖率阈值配置"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        coverage_job = workflow["jobs"]["test-coverage"]
        steps = coverage_job.get("steps", [])

        # 检查是否有覆盖率阈值检查
        coverage_check_found = False
        for step in steps:
            if "run" in step:
                run_command = step["run"]
                if "coverage report --fail-under" in run_command:
                    coverage_check_found = True
                    assert "--fail-under=80" in run_command, "覆盖率阈值应该至少为 80%"
                    break

        assert coverage_check_found, "工作流应该包含覆盖率阈值检查"

    def test_codecov_integration(self):
        """测试 Codecov 集成配置"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        # 检查是否有使用 codecov-action
        codecov_used = False
        for job_name, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                if "uses" in step and "codecov/codecov-action" in step["uses"]:
                    codecov_used = True
                    break

        assert codecov_used, "工作流应该集成 Codecov"

    def test_parallel_execution(self):
        """测试并行执行配置"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        parallel_job = workflow["jobs"].get("parallel-tests")
        assert parallel_job is not None, "工作流应该包含并行测试任务"

        # 检查是否使用 pytest-xdist
        steps = parallel_job.get("steps", [])
        xdist_used = False
        for step in steps:
            if "run" in step and "pytest-xdist" in step.get("run", ""):
                xdist_used = True
                break

        assert xdist_used, "并行测试应该使用 pytest-xdist"

    def test_security_scan(self):
        """测试安全扫描配置"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        security_job = workflow["jobs"].get("security-scan")
        assert security_job is not None, "工作流应该包含安全扫描任务"

        # 检查是否使用 bandit
        steps = security_job.get("steps", [])
        bandit_used = False
        for step in steps:
            if "run" in step and "bandit" in step.get("run", ""):
                bandit_used = True
                break

        assert bandit_used, "安全扫描应该使用 bandit"

    def test_test_report_job(self):
        """测试测试报告任务配置"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        report_job = workflow["jobs"].get("test-report")
        assert report_job is not None, "工作流应该包含测试报告任务"

        # 检查是否总是运行
        assert report_job.get("if") == "always()", "测试报告应该总是运行"

        # 检查是否使用发布测试结果 action
        steps = report_job.get("steps", [])
        publish_used = False
        for step in steps:
            if "uses" in step and "publish-unit-test-result-action" in step["uses"]:
                publish_used = True
                break

        assert publish_used, "测试报告应该使用发布测试结果 action"

    def test_workflow_triggers(self):
        """测试工作流触发器配置"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        # YAML 解析时 'on' 会被解析为 True
        assert "on" in workflow or True in workflow

        # 获取触发器配置
        triggers = workflow.get("on", workflow.get(True, {}))

        # 检查 push 触发器
        assert "push" in triggers

        # 检查 pull_request 触发器
        assert "pull_request" in triggers

        # 检查 workflow_dispatch 触发器
        assert "workflow_dispatch" in triggers

    def test_artifact_upload(self):
        """测试工件上传配置"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        # 检查是否有上传工件的操作
        artifact_upload_found = False
        for job_name, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                if "uses" in step and "upload-artifact" in step["uses"]:
                    artifact_upload_found = True
                    break

        assert artifact_upload_found, "工作流应该包含工件上传"


class TestCIBestPractices:
    """CI 最佳实践测试"""

    def test_python_version_matrix(self):
        """测试 Python 版本矩阵"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        unit_tests = workflow["jobs"]["unit-tests"]
        python_versions = unit_tests["strategy"]["matrix"]["python-version"]

        # 检查是否测试多个 Python 版本
        assert len(python_versions) >= 2, "应该测试至少 2 个 Python 版本"

        # 检查是否包含最新版本
        assert "3.12" in python_versions, "应该测试 Python 3.12"

    def test_coverage_report_generation(self):
        """测试覆盖率报告生成"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        coverage_job = workflow["jobs"]["test-coverage"]
        steps = coverage_job.get("steps", [])

        # 检查是否生成 HTML 报告
        html_report_found = False
        for step in steps:
            if "run" in step:
                run_command = step["run"]
                if "--cov-report=html" in run_command:
                    html_report_found = True
                    break

        assert html_report_found, "应该生成 HTML 覆盖率报告"

    def test_junit_xml_output(self):
        """测试 JUnit XML 输出"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        # 检查测试任务是否输出 JUnit XML
        test_jobs = ["unit-tests", "snapshot-tests", "scenario-tests", "e2e-tests"]
        for job_name in test_jobs:
            job = workflow["jobs"].get(job_name)
            if job:
                steps = job.get("steps", [])
                junit_found = False
                for step in steps:
                    if "run" in step and "--junitxml=" in step.get("run", ""):
                        junit_found = True
                        break

                assert junit_found, f"{job_name} 应该输出 JUnit XML"

    def test_cache_usage(self):
        """测试缓存使用（可选）"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        # 检查是否有使用缓存（这是最佳实践，但不是必需的）
        cache_used = False
        for job_name, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                if "uses" in step and "actions/cache" in step["uses"]:
                    cache_used = True
                    break

        # 只是一个警告，不是必需的
        if not cache_used:
            print("建议：考虑使用 GitHub Actions 缓存来加快构建速度")


class TestCIIntegration:
    """CI 集成测试"""

    def test_workflow_tests_correct_directory(self):
        """测试工作流测试正确的目录"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        # 检查测试命令是否指向正确的目录
        for job_name, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                if "run" in step and "pytest" in step.get("run", ""):
                    run_command = step["run"]
                    if "lingflow/testing/" in run_command:
                        return  # 找到正确的目录

        # 如果没找到，发出警告
        print("警告：确保 pytest 命令指向 lingflow/testing/ 目录")

    def test_dependencies_installation(self):
        """测试依赖安装"""
        workflow_path = self._workflow_path

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        # 检查是否安装 pytest
        pytest_installed = False
        for job_name, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                if "run" in step and "pip install pytest" in step.get("run", ""):
                    pytest_installed = True
                    break

        assert pytest_installed, "工作流应该安装 pytest"


# 主测试入口
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("CI/CD 集成测试")
    print("=" * 70)

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
