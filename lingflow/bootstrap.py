"""LingFlow 启动引导模块

规范 LingFlow 的启动顺序，确保各模块按正确顺序初始化。

启动顺序:
1. 版本信息加载
2. 日志系统初始化
3. 智能压缩器初始化
4. 上下文管理器初始化
5. 钩子系统初始化
6. 会话恢复显示
"""

import logging
import sys
from typing import Optional

# 版本信息
__version__ = "3.6.0"

# 启动状态
_startup_completed = False
_startup_errors = []


def get_version() -> str:
    """获取版本号"""
    return __version__


def init_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> None:
    """初始化日志系统

    Args:
        level: 日志级别
        format_string: 日志格式字符串
    """
    format_string = format_string or (
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.basicConfig(
        level=level,
        format=format_string,
        force=True  # 允许重新配置
    )


def init_smart_compression(
    max_tokens: int = 180000,
    warning_threshold: float = 0.75,
    compress_threshold: float = 0.85,
    enabled: bool = True
) -> Optional[object]:
    """初始化智能上下文压缩器

    Args:
        max_tokens: 最大 token 数量
        warning_threshold: 警告阈值 (0-1)
        compress_threshold: 压缩阈值 (0-1)
        enabled: 是否启用

    Returns:
        压缩器实例，如果禁用则返回 None
    """
    if not enabled:
        return None

    try:
        from lingflow.compression import enable_smart_compression
        compressor = enable_smart_compression(
            max_tokens=max_tokens,
            warning_threshold=warning_threshold,
            compress_threshold=compress_threshold
        )
        return compressor
    except Exception as e:
        _startup_errors.append(f"压缩器初始化失败: {e}")
        return None


def init_context_manager() -> Optional[object]:
    """初始化上下文管理器

    Returns:
        上下文管理器实例
    """
    try:
        from lingflow.context import get_context_manager
        return get_context_manager()
    except Exception as e:
        _startup_errors.append(f"上下文管理器初始化失败: {e}")
        return None


def show_session_resume(
    enabled: bool = True,
    force: bool = False
) -> None:
    """显示会话恢复信息

    Args:
        enabled: 是否启用自动显示
        force: 是否强制显示（忽略已显示标记）
    """
    if not enabled:
        return

    try:
        from lingflow.context.auto_resume import auto_resume, SESSION_FILE

        if not SESSION_FILE.exists():
            return

        resume_text = auto_resume()
        if resume_text:
            print(resume_text, file=sys.stderr)
    except Exception as e:
        _startup_errors.append(f"会话恢复显示失败: {e}")


def init_hooks(enabled: bool = True) -> Optional[object]:
    """初始化自优化钩子系统

    Args:
        enabled: 是否启用钩子系统

    Returns:
        钩子实例，如果禁用或初始化失败则返回 None
    """
    if not enabled:
        return None

    try:
        from lingflow.hooks import get_global_hook
        hook = get_global_hook()
        return hook
    except Exception as e:
        _startup_errors.append(f"钩子系统初始化失败: {e}")
        return None


def bootstrap(
    compression: bool = True,
    auto_resume: bool = True,
    hooks: bool = True,
    verbose: bool = False
) -> dict:
    """执行完整的启动流程

    Args:
        compression: 是否启用智能压缩
        auto_resume: 是否显示会话恢复
        hooks: 是否启用钩子系统
        verbose: 是否输出详细信息

    Returns:
        启动状态字典
    """
    global _startup_completed

    status = {
        "version": __version__,
        "compression": None,
        "context_manager": None,
        "hooks": None,
        "errors": [],
        "success": True
    }

    # 1. 初始化日志
    log_level = logging.DEBUG if verbose else logging.WARNING
    init_logging(level=log_level)

    # 2. 初始化智能压缩
    if compression:
        status["compression"] = init_smart_compression()

    # 3. 初始化上下文管理器
    status["context_manager"] = init_context_manager()

    # 4. 初始化钩子系统
    if hooks:
        status["hooks"] = init_hooks()

    # 5. 显示会话恢复
    if auto_resume:
        show_session_resume()

    # 收集错误
    status["errors"] = _startup_errors.copy()
    if _startup_errors:
        status["success"] = False

    _startup_completed = True
    return status


def is_startup_completed() -> bool:
    """检查启动是否完成"""
    return _startup_completed


def get_startup_errors() -> list:
    """获取启动过程中的错误"""
    return _startup_errors.copy()


# ============================================================================
# 自动启动（模块导入时执行）
# ============================================================================

def _auto_bootstrap():
    """模块导入时自动执行启动"""
    if not _startup_completed:
        bootstrap(
            compression=True,
            auto_resume=True,
            hooks=True,
            verbose=False
        )


# 延迟启动 - 由 __init__.py 显式调用
# 不在模块导入时自动执行
