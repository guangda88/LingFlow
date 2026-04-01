"""
配置管理
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional

# 尝试从 LingFlow 读取版本号
def _get_version() -> str:
    """获取版本号（优先从 lingflow 读取）"""
    try:
        from lingflow import __version__
        return __version__
    except ImportError:
        # lingflow 未安装时使用默认版本
        return "3.8.0"

class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "LingFlow API"
    APP_VERSION: str = _get_version()
    APP_DESCRIPTION: str = "AI-enhanced software engineering workflow system"

    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # API Keys
    API_KEYS: str = ""

    # LingFlow
    WORK_DIR: str = "."
    LOG_LEVEL: str = "INFO"

    # CORS
    # 允许的跨域来源，逗号分隔。生产环境应该设置具体域名而非 "*"
    # 示例: "http://localhost:3000,https://example.com"
    # 安全警告: "*" 允许所有来源，仅用于开发环境
    CORS_ORIGINS: str = os.getenv("LINGFLOW_CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
    GITHUB_TOKEN: Optional[str] = None
    NPM_TOKEN: Optional[str] = None

    # 任务
    DEFAULT_TIMEOUT: int = 300
    MAX_TASKS: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True

# 全局配置实例
settings = Settings()
