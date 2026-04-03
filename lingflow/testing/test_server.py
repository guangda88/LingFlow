#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码测试服务器
基于 Chrome DevTools MCP 的 TestServer 模式
创建和管理动态测试代码环境
"""

import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, List, Optional, Generator, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CodeTestServer:
    """代码测试服务器 - 创建和管理测试代码环境

    基于 Chrome DevTools MCP 的 TestServer 模式
    提供动态路由管理和资源清理功能

    特性:
    - 动态添加测试文件
    - 自动资源清理
    - 上下文管理器支持
    - 临时目录隔离
    - 测试固件管理
    """

    def __init__(self, temp_dir: Optional[Path] = None):
        """初始化测试服务器

        Args:
            temp_dir: 临时目录路径，None 则自动创建
        """
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp(prefix="lingflow_test_"))
        self.routes: Dict[str, Path] = {}
        self.test_files: Dict[str, Path] = {}
        self.requirements: List[str] = []
        self.created_at = datetime.now()

        logger.info(f"🚀 CodeTestServer 初始化: {self.temp_dir}")

    def add_python_route(self, name: str, code: str) -> Path:
        """添加测试 Python 文件

        Args:
            name: 模块名称
            code: Python 代码内容

        Returns:
            文件路径

        Example:
            >>> server = CodeTestServer()
            >>> file_path = server.add_python_route("test_module", "def foo(): pass")
            >>> print(file_path.name)
            test_module.py
        """
        file_path = self.temp_dir / f"{name}.py"
        file_path.write_text(code, encoding="utf-8")
        self.routes[name] = file_path

        logger.debug(f"✓ 添加 Python 路由: {name} -> {file_path}")
        return file_path

    def add_test_route(self, name: str, test_code: str) -> Path:
        """添加测试文件

        Args:
            name: 测试名称
            test_code: 测试代码内容

        Returns:
            测试文件路径

        Example:
            >>> server = CodeTestServer()
            >>> test_path = server.add_test_route("test_foo", "def test_foo(): assert True")
            >>> print(test_path.name)
            test_test_foo.py
        """
        file_path = self.temp_dir / f"test_{name}.py"
        file_path.write_text(test_code, encoding="utf-8")
        self.test_files[name] = file_path

        logger.debug(f"✓ 添加测试路由: {name} -> {file_path}")
        return file_path

    def add_requirements(self, packages: List[str]) -> Path:
        """添加依赖包列表

        Args:
            packages: 包名列表

        Returns:
            requirements.txt 文件路径

        Example:
            >>> server = CodeTestServer()
            >>> req_path = server.add_requirements(["pytest", "pytest-asyncio"])
            >>> print(req_path.read_text())
            pytest
            pytest-asyncio
        """
        self.requirements.extend(packages)
        file_path = self.temp_dir / "requirements.txt"
        content = "\n".join(packages)
        file_path.write_text(content, encoding="utf-8")

        logger.debug(f"✓ 添加依赖: {', '.join(packages)}")
        return file_path

    def add_fixture(self, name: str, content: Any) -> Path:
        """添加测试固件

        Args:
            name: 固件名称
            content: 固件内容（可以是字符串、字典等）

        Returns:
            固件文件路径

        Example:
            >>> server = CodeTestServer()
            >>> fixture_path = server.add_fixture("data.json", {"key": "value"})
            >>> import json
            >>> print(json.loads(fixture_path.read_text()))
            {'key': 'value'}
        """
        if isinstance(content, (dict, list)):
            import json

            # 如果 name 已经有 .json 后缀，不重复添加
            if not name.endswith(".json"):
                name = f"{name}.json"
            file_path = self.temp_dir / name
            file_path.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            file_path = self.temp_dir / name
            file_path.write_text(str(content), encoding="utf-8")

        logger.debug(f"✓ 添加固件: {name} -> {file_path}")
        return file_path

    def get_route(self, name: str) -> Optional[Path]:
        """获取路由路径

        Args:
            name: 路由名称

        Returns:
            文件路径，不存在返回 None
        """
        return self.routes.get(name)

    def get_test_route(self, name: str) -> Optional[Path]:
        """获取测试路由路径

        Args:
            name: 测试名称

        Returns:
            测试文件路径，不存在返回 None
        """
        return self.test_files.get(name)

    def list_routes(self) -> List[str]:
        """列出所有路由

        Returns:
            路由名称列表
        """
        return list(self.routes.keys())

    def list_tests(self) -> List[str]:
        """列出所有测试

        Returns:
            测试名称列表
        """
        return list(self.test_files.keys())

    @contextmanager
    def code_context(self, name: str, code: str) -> Generator[Path, None, None]:
        """代码上下文管理器

        自动清理测试代码

        Args:
            name: 模块名称
            code: Python 代码内容

        Yields:
            文件路径

        Example:
            >>> server = CodeTestServer()
            >>> with server.code_context("test_module", "def foo(): pass") as path:
            ...     # 使用代码文件
            ...     print(f"文件路径: {path}")
            ... # 自动清理
        """
        file_path = self.add_python_route(name, code)
        try:
            yield file_path
        finally:
            self.remove_route(name)

    @contextmanager
    def test_context(self, name: str, test_code: str) -> Generator[Path, None, None]:
        """测试上下文管理器

        自动清理测试文件

        Args:
            name: 测试名称
            test_code: 测试代码内容

        Yields:
            测试文件路径

        Example:
            >>> server = CodeTestServer()
            >>> with server.test_context("test_foo", "def test_foo(): assert True") as path:
            ...     # 运行测试
            ...     # 自动清理
        """
        file_path = self.add_test_route(name, test_code)
        try:
            yield file_path
        finally:
            self.remove_test_route(name)

    def remove_route(self, name: str) -> bool:
        """移除路由

        Args:
            name: 路由名称

        Returns:
            是否成功移除
        """
        if name in self.routes:
            path = self.routes[name]
            path.unlink(missing_ok=True)
            del self.routes[name]
            logger.debug(f"✓ 移除路由: {name}")
            return True
        return False

    def remove_test_route(self, name: str) -> bool:
        """移除测试路由

        Args:
            name: 测试名称

        Returns:
            是否成功移除
        """
        if name in self.test_files:
            path = self.test_files[name]
            path.unlink(missing_ok=True)
            del self.test_files[name]
            logger.debug(f"✓ 移除测试路由: {name}")
            return True
        return False

    def restore(self):
        """清理所有测试文件

        恢复到初始状态
        """
        # 清理路由
        for name in list(self.routes.keys()):
            self.remove_route(name)

        # 清理测试
        for name in list(self.test_files.keys()):
            self.remove_test_route(name)

        # 清理依赖
        self.requirements.clear()
        req_file = self.temp_dir / "requirements.txt"
        req_file.unlink(missing_ok=True)

        logger.info("✓ CodeTestServer 已清理")

    def cleanup(self):
        """完全清理临时目录

        删除所有文件和目录
        """
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info(f"✓ CodeTestServer 已完全清理: {self.temp_dir}")

    def __enter__(self):
        """进入上下文"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，自动清理"""
        self.restore()

    def __del__(self):
        """析构函数，清理资源"""
        try:
            self.cleanup()
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "temp_dir": str(self.temp_dir),
            "created_at": self.created_at.isoformat(),
            "routes_count": len(self.routes),
            "tests_count": len(self.test_files),
            "requirements_count": len(self.requirements),
            "routes": self.list_routes(),
            "tests": self.list_tests(),
        }


# 示例使用

if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("CodeTestServer 示例")
    print("=" * 70)

    # 创建测试服务器
    with CodeTestServer() as server:
        print(f"\n📁 临时目录: {server.temp_dir}")

        # 添加 Python 模块
        code = """
def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b
"""
        module_path = server.add_python_route("calculator", code)
        print(f"\n✓ 添加模块: {module_path}")
        print(f"  内容: {code.strip()}")

        # 添加测试
        test_code = """
from calculator import calculate_sum, calculate_product

def test_calculate_sum():
    assert calculate_sum(1, 2) == 3
    assert calculate_sum(-1, 1) == 0

def test_calculate_product():
    assert calculate_product(2, 3) == 6
    assert calculate_product(0, 5) == 0

def test_calculate_product_negative():
    assert calculate_product(-2, 3) == -6
"""
        test_path = server.add_test_route("calculator", test_code)
        print(f"\n✓ 添加测试: {test_path}")

        # 添加依赖
        req_path = server.add_requirements(["pytest", "pytest-cov"])
        print(f"\n✓ 添加依赖: {req_path}")
        print("  包: pytest, pytest-cov")

        # 使用上下文管理器
        print("\n" + "-" * 70)
        print("使用上下文管理器:")
        print("-" * 70)

        with server.code_context("temp_module", "x = 42") as path:
            print(f"  临时文件: {path}")
            print(f"  内容: {path.read_text()}")
            print(f"  存在: {path.exists()}")
        print(f"  清理后: {path.exists()}")

        # 显示统计信息
        print("\n" + "-" * 70)
        print("统计信息:")
        print("-" * 70)
        stats = server.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    print("\n✅ 服务器已自动清理")
