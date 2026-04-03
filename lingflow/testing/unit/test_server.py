#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试 - 测试服务器
"""

import pytest
import tempfile
from pathlib import Path

from lingflow.testing import CodeTestServer


class TestCodeTestServer:
    """测试 CodeTestServer"""

    @pytest.fixture
    def server(self):
        """创建测试服务器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield CodeTestServer(Path(temp_dir))

    def test_init_creates_temp_dir(self, server):
        """测试初始化创建临时目录"""
        assert server.temp_dir.exists()
        assert server.temp_dir.is_dir()

    def test_init_with_custom_temp_dir(self):
        """测试使用自定义临时目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            server = CodeTestServer(Path(temp_dir))

            assert server.temp_dir == Path(temp_dir)

    def test_add_python_route(self, server):
        """测试添加 Python 路由"""
        code = "def foo(): pass"
        path = server.add_python_route("test_module", code)

        assert path.exists()
        assert path.name == "test_module.py"
        assert "test_module" in server.routes
        assert server.routes["test_module"] == path

    def test_add_test_route(self, server):
        """测试添加测试路由"""
        test_code = "def test_foo(): assert True"
        path = server.add_test_route("test_foo", test_code)

        assert path.exists()
        assert path.name == "test_test_foo.py"
        assert "test_foo" in server.test_files

    def test_add_requirements(self, server):
        """测试添加依赖"""
        packages = ["pytest", "pytest-asyncio", "pytest-cov"]
        path = server.add_requirements(packages)

        assert path.exists()
        assert path.name == "requirements.txt"

        content = path.read_text()
        assert "pytest" in content
        assert "pytest-asyncio" in content
        assert "pytest-cov" in content

    def test_add_fixture_dict(self, server):
        """测试添加字典固件"""
        import json

        data = {"key": "value", "number": 42}
        path = server.add_fixture("data.json", data)

        assert path.exists()
        assert path.name == "data.json"

        loaded_data = json.loads(path.read_text())
        assert loaded_data == data

    def test_add_fixture_text(self, server):
        """测试添加文本固件"""
        text = "Hello, World!"
        path = server.add_fixture("hello.txt", text)

        assert path.exists()
        assert path.read_text() == text

    def test_get_route_exists(self, server):
        """测试获取存在的路由"""
        code = "x = 1"
        server.add_python_route("module1", code)

        path = server.get_route("module1")

        assert path is not None
        assert path.exists()

    def test_get_route_not_exists(self, server):
        """测试获取不存在的路由"""
        path = server.get_route("nonexistent")

        assert path is None

    def test_get_test_route_exists(self, server):
        """测试获取存在的测试路由"""
        test_code = "def test_x(): pass"
        server.add_test_route("test_x", test_code)

        path = server.get_test_route("test_x")

        assert path is not None
        assert path.exists()

    def test_list_routes(self, server):
        """测试列出路由"""
        server.add_python_route("module1", "x = 1")
        server.add_python_route("module2", "y = 2")
        server.add_python_route("module3", "z = 3")

        routes = server.list_routes()

        assert len(routes) == 3
        assert "module1" in routes
        assert "module2" in routes
        assert "module3" in routes

    def test_list_tests(self, server):
        """测试列出测试"""
        server.add_test_route("test1", "def test1(): pass")
        server.add_test_route("test2", "def test2(): pass")

        tests = server.list_tests()

        assert len(tests) == 2
        assert "test1" in tests
        assert "test2" in tests

    def test_code_context(self, server):
        """测试代码上下文管理器"""
        code = "temp = 42"

        with server.code_context("temp_module", code) as path:
            assert path.exists()
            assert "temp_module" in server.routes

        # 清理后应该不存在
        assert "temp_module" not in server.routes
        assert not path.exists()

    def test_test_context(self, server):
        """测试测试上下文管理器"""
        test_code = "def test_temp(): pass"

        with server.test_context("test_temp", test_code) as path:
            assert path.exists()
            assert "test_temp" in server.test_files

        # 清理后应该不存在
        assert "test_temp" not in server.test_files
        assert not path.exists()

    def test_remove_route(self, server):
        """测试移除路由"""
        code = "x = 1"
        path = server.add_python_route("module1", code)

        assert path.exists()

        result = server.remove_route("module1")

        assert result is True
        assert "module1" not in server.routes
        assert not path.exists()

    def test_remove_nonexistent_route(self, server):
        """测试移除不存在的路由"""
        result = server.remove_route("nonexistent")

        assert result is False

    def test_remove_test_route(self, server):
        """测试移除测试路由"""
        test_code = "def test_x(): pass"
        path = server.add_test_route("test_x", test_code)

        assert path.exists()

        result = server.remove_test_route("test_x")

        assert result is True
        assert "test_x" not in server.test_files
        assert not path.exists()

    def test_restore(self, server):
        """测试恢复"""
        # 添加一些内容
        server.add_python_route("module1", "x = 1")
        server.add_test_route("test1", "def test1(): pass")
        server.add_requirements(["pytest"])

        assert len(server.routes) > 0
        assert len(server.test_files) > 0
        assert len(server.requirements) > 0

        # 恢复
        server.restore()

        assert len(server.routes) == 0
        assert len(server.test_files) == 0
        assert len(server.requirements) == 0

    def test_cleanup(self, server):
        """测试完全清理"""
        # 添加一些内容
        server.add_python_route("module1", "x = 1")

        temp_dir = server.temp_dir
        assert temp_dir.exists()

        # 清理
        server.cleanup()

        assert not temp_dir.exists()

    def test_context_manager(self):
        """测试上下文管理器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with CodeTestServer(Path(temp_dir)) as server:
                server.add_python_route("module1", "x = 1")
                assert len(server.routes) == 1

            # 退出后应该已恢复
            assert len(server.routes) == 0

    def test_get_stats(self, server):
        """测试获取统计信息"""
        server.add_python_route("module1", "x = 1")
        server.add_test_route("test1", "def test1(): pass")
        server.add_requirements(["pytest"])

        stats = server.get_stats()

        assert stats["routes_count"] == 1
        assert stats["tests_count"] == 1
        assert stats["requirements_count"] == 1
        assert "module1" in stats["routes"]
        assert "test1" in stats["tests"]


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
