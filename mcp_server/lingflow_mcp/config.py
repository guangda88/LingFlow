"""MCP 服务器配置"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List


@dataclass
class ServerConfig:
    """LingFlow 服务器配置"""

    # 工作目录
    work_dir: Path = field(default_factory=lambda: Path.cwd())

    # 数据库路径
    db_path: Optional[Path] = None

    # API 配置
    github_token: Optional[str] = None
    npm_token: Optional[str] = None

    # 异步任务配置
    max_async_tasks: int = 10
    task_timeout: int = 300  # 5 分钟

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 小时

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    # 安全配置
    allowed_paths: List[Path] = field(default_factory=list)
    read_only: bool = False

    def __post_init__(self):
        """初始化后处理"""
        # 设置默认数据库路径
        if self.db_path is None:
            self.db_path = self.work_dir / ".lingflow" / "lingflow.db"

        # 设置默认允许路径
        if not self.allowed_paths:
            self.allowed_paths = [self.work_dir]

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """从环境变量加载配置"""
        import os

        work_dir = Path(os.getenv("LINGFLOW_WORK_DIR", str(Path.cwd())))

        return cls(
            work_dir=work_dir,
            github_token=os.getenv("GITHUB_TOKEN"),
            npm_token=os.getenv("NPM_TOKEN"),
            log_level=os.getenv("LINGFLOW_LOG_LEVEL", "INFO"),
            read_only=os.getenv("LINGFLOW_READ_ONLY", "false").lower() == "true",
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "work_dir": str(self.work_dir),
            "db_path": str(self.db_path),
            "github_token": "***" if self.github_token else None,
            "npm_token": "***" if self.npm_token else None,
            "max_async_tasks": self.max_async_tasks,
            "task_timeout": self.task_timeout,
            "enable_cache": self.enable_cache,
            "cache_ttl": self.cache_ttl,
            "log_level": self.log_level,
            "read_only": self.read_only,
        }
