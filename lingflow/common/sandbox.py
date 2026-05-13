"""
lingflow 安全沙箱执行器

提供进程隔离的安全环境，用于执行不可信的技能代码。

安全特性：
- 进程隔离：在单独的进程中执行技能代码
- 超时限制：防止无限循环和长时间运行
- 资源限制：限制 CPU 和内存使用
- 模块白名单：只允许访问安全的模块
- 异常隔离：捕获所有异常，防止影响主进程
"""

import logging
import multiprocessing
import resource
import sys
import time
from typing import Any, Callable, Dict, Optional

from lingflow.common.security_analyzer import (
    SecurityAnalyzer,
    analyze_code_security,
    get_security_report,
)


class SandboxError(Exception):
    """沙箱执行错误"""


class SandboxTimeoutError(SandboxError):
    """沙箱执行超时"""


class SandboxMemoryLimitError(SandboxError):
    """沙箱内存超限"""


class SandboxCPULimitError(SandboxError):
    """沙箱CPU时间超限"""


class SandboxLoopLimitError(SandboxError):
    """沙箱循环迭代超限"""


# 模块级别的安全导入函数


def _create_safe_import(allowed_modules):
    """创建安全的 __import__ 函数"""

    def safe_import(name, *args, **kwargs):
        """安全的导入函数，只允许白名单模块"""
        # 解析完整的模块名
        if "." in name:
            base_module = name.split(".")[0]
        else:
            base_module = name

        # 检查是否在白名单中
        if base_module not in allowed_modules:
            raise ImportError(f"Import of '{name}' is not allowed")

        # 使用原始的 __import__
        import builtins

        return builtins.__import__(name, *args, **kwargs)

    return safe_import


class SkillSandbox:
    """
    安全沙箱执行器

    在隔离的进程中执行技能代码，提供超时和资源限制。
    """

    # 安全的内置函数白名单
    SAFE_BUILTINS = {
        "__builtins__": {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "isinstance": isinstance,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "range": range,
            "reversed": reversed,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }
    }

    # 允许的模块白名单
    # 基础层：类型与数据
    _SAFE_CORE = {
        "typing",
        "dataclasses",
        "datetime",
        "math",
        "time",
        "enum",
        "collections",
        "functools",
        "itertools",
        "operator",
        "copy",
        "abc",
        "numbers",
        "decimal",
        "fractions",
        "statistics",
        "hashlib",
        "re",
        "string",
        "textwrap",
        "unicodedata",
        "difflib",
        "csv",
    }
    # I/O 层：文件与路径（只读安全）
    _SAFE_IO = {
        "pathlib",
        "os.path",
        "json",
        "yaml",
        "importlib",
    }
    # 运行时层：日志与并发
    _SAFE_RUNTIME = {
        "logging",
        "asyncio",
        "threading",
        "queue",
    }
    # lingflow 层：lingflow 自有模块
    _SAFE_LINGFLOW = {
        "lingflow.trust",
    }
    ALLOWED_MODULES = _SAFE_CORE | _SAFE_IO | _SAFE_RUNTIME | _SAFE_LINGFLOW

    def __init__(
        self,
        timeout: float = 30.0,
        memory_limit: Optional[int] = None,
        max_processes: Optional[int] = None,
        max_recursion_depth: int = 100,
        max_loop_iterations: int = 1000000,
        enable_ast_analysis: bool = True,
    ):
        """
        初始化沙箱

        Args:
            timeout: 执行超时时间（秒）
            memory_limit: 内存限制（字节），None 表示不限制
            max_processes: 最大进程数，None 表示不限制
            max_recursion_depth: 最大递归深度
            max_loop_iterations: 最大循环迭代次数
            enable_ast_analysis: 是否启用AST静态分析
        """
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.max_processes = max_processes
        self.max_recursion_depth = max_recursion_depth
        self.max_loop_iterations = max_loop_iterations
        self.enable_ast_analysis = enable_ast_analysis
        self.security_analyzer = SecurityAnalyzer(self.ALLOWED_MODULES)
        self.logger = logging.getLogger(__name__)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        在沙箱中执行函数

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            SandboxError: 沙箱执行错误
            SandboxTimeoutError: 执行超时
            Exception: 函数执行时抛出的异常
        """
        # 使用 Manager 创建队列，确保跨进程共享
        manager = multiprocessing.Manager()
        result_queue = manager.Queue()
        error_queue = manager.Queue()

        # 创建并启动子进程
        process = multiprocessing.Process(target=self._execute_wrapper, args=(func, args, kwargs, result_queue, error_queue))

        # 启动进程
        process.start()

        # 等待结果或超时
        process.join(timeout=self.timeout)

        # 检查执行状态
        if process.is_alive():
            # 超时，终止进程
            process.terminate()
            process.join(timeout=1.0)
            if process.is_alive():
                process.kill()
                process.join()

            raise SandboxTimeoutError(f"Skill execution timed out after {self.timeout} seconds")

        # 检查是否有错误
        if not error_queue.empty():
            error = error_queue.get()
            raise error

        # 获取结果
        # 等待一小段时间以确保结果已写入队列
        import time

        time.sleep(0.01)

        if result_queue.empty():
            raise SandboxError("No result returned from sandbox")

        return result_queue.get()

    def _execute_wrapper(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        result_queue: multiprocessing.Queue,
        error_queue: multiprocessing.Queue,
    ) -> None:
        """
        在子进程中执行函数的包装器

        Args:
            func: 要执行的函数
            args: 位置参数
            kwargs: 关键字参数
            result_queue: 结果队列
            error_queue: 错误队列
        """
        try:
            # 执行函数
            result = func(*args, **kwargs)
            result_queue.put(result)
        except Exception as e:
            # 捕获所有异常并保留异常链
            error_queue.put(e)

    def execute_code(
        self, code: str, globals_dict: Optional[Dict[str, Any]] = None, locals_dict: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        在沙箱中执行代码

        Args:
            code: 要执行的 Python 代码
            globals_dict: 全局命名空间
            locals_dict: 局部命名空间

        Returns:
            执行结果

        Raises:
            SandboxError: 沙箱执行错误
            SandboxTimeoutError: 执行超时
            SyntaxError: 代码语法错误
            Exception: 代码执行时抛出的异常
        """
        # 编译代码以验证语法
        try:
            compile(code, "<sandbox>", "exec")
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in skill code: {e}")

        # 准备安全的执行环境
        final_globals = self._create_safe_globals()
        if globals_dict:
            final_globals.update(globals_dict)

        final_locals = locals_dict or {}

        # 使用 _execute_code_wrapper 在子进程中执行
        return self.execute(self._execute_code_wrapper, code, final_globals, final_locals)

    def _setup_memory_limit(self) -> Optional[Any]:
        """设置内存限制，返回原始限制值"""
        if not self.memory_limit:
            return None
        original = None
        try:
            original = resource.getrlimit(resource.RLIMIT_AS)
        except (ValueError, resource.error):
            self.logger.warning("Could not read current memory limit")
        try:
            resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))
        except (ValueError, resource.error):
            self.logger.warning("Could not set memory limit")
        return original

    def _restore_memory_limit(self, original: Optional[Any]) -> None:
        """恢复原始内存限制"""
        if self.memory_limit and original is not None:
            try:
                resource.setrlimit(resource.RLIMIT_AS, original)
            except (ValueError, resource.error):
                pass

    def _filter_serializable(self, locals_dict: Dict[str, Any]) -> Dict[str, Any]:
        """过滤掉不可序列化的对象"""
        result = {}
        for key, value in locals_dict.items():
            try:
                import pickle

                pickle.dumps(value)
                result[key] = value
            except (pickle.PickleError, TypeError):
                pass
        return result

    def _execute_code_wrapper(self, code: str, globals_dict: Dict[str, Any], locals_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        在子进程中执行代码的包装器

        Args:
            code: 要执行的代码字符串
            globals_dict: 全局命名空间
            locals_dict: 局部命名空间

        Returns:
            执行后的局部命名空间
        """
        start_cpu = time.process_time()
        start_memory = self._get_memory_usage()

        original_recursion_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(self.max_recursion_depth)

        original_mem_limit = self._setup_memory_limit()

        loop_counter = {"count": 0}

        def trace_hook(frame, event, arg):
            """跟踪函数，用于监控循环迭代"""
            if event == "line":
                if loop_counter["count"] >= self.max_loop_iterations:
                    raise SandboxLoopLimitError(f"Loop iteration count exceeded limit: {self.max_loop_iterations}")
                loop_counter["count"] += 1
            return trace_hook

        try:
            if self.max_loop_iterations < float("inf"):
                sys.settrace(trace_hook)

            compiled_code = compile(code, "<sandbox>", "exec")
            exec(compiled_code, globals_dict, locals_dict)

            sys.settrace(None)
            sys.setrecursionlimit(original_recursion_limit)

            if self.memory_limit:
                end_memory = self._get_memory_usage()
                memory_used = end_memory - start_memory
                if memory_used > self.memory_limit:
                    raise SandboxMemoryLimitError(f"Memory usage {memory_used} bytes exceeded limit {self.memory_limit} bytes")

            elapsed_cpu = time.process_time() - start_cpu
            if elapsed_cpu > self.timeout:
                raise SandboxCPULimitError(f"CPU time {elapsed_cpu:.2f}s exceeded timeout {self.timeout}s")

            return self._filter_serializable(locals_dict)

        except MemoryError:
            self.logger.warning(f"Memory limit exceeded: {self.memory_limit} bytes")
            raise SandboxMemoryLimitError(f"Memory limit exceeded: {self.memory_limit} bytes")

        except RecursionError:
            self.logger.warning(f"Recursion depth exceeded limit: {self.max_recursion_depth}")
            raise SandboxMemoryLimitError(f"Recursion depth exceeded limit: {self.max_recursion_depth}")

        except SandboxLoopLimitError as e:
            self.logger.warning(str(e))
            raise

        finally:
            sys.settrace(None)
            sys.setrecursionlimit(original_recursion_limit)
            self._restore_memory_limit(original_mem_limit)

    def _get_memory_usage(self) -> int:
        """
        获取当前内存使用量（字节）

        Returns:
            内存使用量（字节）
        """
        try:
            import resource

            # 在Unix系统上获取RSS（驻留集大小）
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024  # 转换为字节
        except (ImportError, AttributeError):
            # 在不支持resource的平台上返回0
            return 0

    def _create_safe_globals(self) -> Dict[str, Any]:
        """
        创建安全的全局命名空间

        Returns:
            安全的全局命名空间字典
        """
        # 创建安全的 __import__ 函数
        safe_import = _create_safe_import(self.ALLOWED_MODULES)

        # 创建安全的 builtins 字典
        safe_builtins = {
            "__import__": safe_import,
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "isinstance": isinstance,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "range": range,
            "reversed": reversed,
            "round": round,
            "set": set,
            "sorted": sorted,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }

        return {
            "__builtins__": safe_builtins,
            "__import__": safe_import,
        }

    def validate_code(self, code: str) -> bool:
        """
        验证代码是否安全

        Args:
            code: 要验证的代码

        Returns:
            True 如果代码安全，False 否则
        """
        # 首先检查语法
        try:
            compile(code, "<sandbox>", "exec")
        except SyntaxError:
            return False

        # 如果启用AST分析，使用SecurityAnalyzer
        if self.enable_ast_analysis:
            try:
                is_safe, violations = analyze_code_security(code, self.ALLOWED_MODULES)

                if not is_safe:
                    report = get_security_report(code, self.ALLOWED_MODULES)
                    self.logger.warning(f"Security violations detected: {report['total_violations']} violations")

                    for severity in ["CRITICAL", "HIGH"]:
                        for violation in report["by_severity"][severity]:
                            self.logger.warning(
                                f"  [{severity}] {violation['violation_type']}: "
                                f"{violation['message']} at line {violation['line']}"
                            )

                    return False

                return True
            except Exception as e:
                self.logger.error(f"Security analysis failed: {e}")
                return False
        else:
            self.logger.warning("AST analysis disabled; code validation skipped")
            return False

    def _validate_code_simple(self, code: str) -> bool:
        """
        简单的代码验证（回退方法）

        Args:
            code: 要验证的代码

        Returns:
            True 如果代码安全，False 否则
        """
        try:
            # 检查危险的导入
            dangerous_imports = [
                "import os",
                "import sys",
                "import subprocess",
                "os.",
                "sys.",
                "subprocess.",
                "eval(",
                "exec(",
                "compile(",
                "__import__",
                "open(",
                "open  ",
            ]

            code_lower = code.lower()
            for dangerous in dangerous_imports:
                if dangerous in code_lower:
                    return False

            return True
        except SyntaxError:
            return False

    def get_security_report(self, code: str) -> Dict[str, Any]:
        """
        获取代码的安全报告

        Args:
            code: 要分析的代码

        Returns:
            安全报告字典
        """
        if self.enable_ast_analysis:
            return get_security_report(code, self.ALLOWED_MODULES)
        else:
            return {
                "is_safe": False,
                "total_violations": 0,
                "by_severity": {"HIGH": []},
                "by_type": {},
                "has_recursion": False,
                "max_loop_depth": 0,
            }


# 单例实例
_default_sandbox: Optional[SkillSandbox] = None


def get_default_sandbox() -> SkillSandbox:
    """获取默认沙箱实例"""
    global _default_sandbox
    if _default_sandbox is None:
        _default_sandbox = SkillSandbox(
            timeout=30.0,
            memory_limit=100 * 1024 * 1024,  # 100MB
            max_processes=1,
            max_recursion_depth=100,
            max_loop_iterations=1000000,
            enable_ast_analysis=True,
        )
    return _default_sandbox


def execute_in_sandbox(func: Callable, *args, timeout: Optional[float] = None, **kwargs) -> Any:
    """
    在沙箱中执行函数（便捷函数）

    Args:
        func: 要执行的函数
        *args: 位置参数
        timeout: 超时时间（秒），None 使用默认值
        **kwargs: 关键字参数

    Returns:
        函数执行结果
    """
    sandbox = get_default_sandbox()
    if timeout is not None:
        sandbox.timeout = timeout
    return sandbox.execute(func, *args, **kwargs)
