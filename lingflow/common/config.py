"""LingFlow 配置管理模块

Single source of truth for LingFlow configuration.
Loading priority: LINGFLOW_ env vars > config.yaml > DEFAULT_CONFIG.
"""

import logging
import os
from typing import Any, Dict, Optional, Type, TypeVar

import yaml

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T")

# 默认配置
DEFAULT_CONFIG = {
    # 工作流配置
    "workflow": {"max_iterations": 100, "sleep_interval": 0.01, "max_parallel": 2},
    # 技能配置
    "skills": {"path": "skills", "default_timeout": 30},
    # 代理配置
    "agents": {
        "default_agents": [
            {
                "name": "implementation",
                "description": "Code implementation agent",
                "capabilities": ["code_generation", "testing", "documentation"],
            },
            {
                "name": "review",
                "description": "Code review agent",
                "capabilities": ["code_review", "design_review", "security_check"],
            },
            {
                "name": "testing",
                "description": "Testing agent",
                "capabilities": ["test_generation", "test_execution", "coverage_analysis"],
            },
            {
                "name": "debugging",
                "description": "Debugging agent",
                "capabilities": ["error_analysis", "root_cause", "fix_generation"],
            },
            {
                "name": "architecture",
                "description": "Architecture agent",
                "capabilities": ["system_design", "architecture_review", "api_design"],
            },
            {
                "name": "documentation",
                "description": "Documentation agent",
                "capabilities": ["doc_generation", "api_doc_writing", "readme_generation"],
            },
        ]
    },
    # 压缩配置
    "compression": {"enabled": True, "max_length": 10000},
    # 日志配置
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
    },
}


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(os.getcwd(), "config.yaml")
        self._cache: Dict[str, Any] = {}  # 配置缓存
        self.config = self._load_config()

    # Supported LINGFLOW_ env var overrides (env name -> dot-notation key)
    ENV_OVERRIDES = {
        "LINGFLOW_LOG_LEVEL": "logging.level",
        "LINGFLOW_MAX_PARALLEL": "workflow.max_parallel",
        "LINGFLOW_MAX_ITERATIONS": "workflow.max_iterations",
        "LINGFLOW_SKILLS_PATH": "skills.path",
        "LINGFLOW_SKILL_TIMEOUT": "skills.default_timeout",
        "LINGFLOW_COMPRESSION_ENABLED": "compression.enabled",
        "LINGFLOW_AGENT_TIMEOUT": "agents.timeout",
    }

    def _load_config(self) -> dict:
        """加载配置（优先级：环境变量 > 配置文件 > 默认值）"""
        config = DEFAULT_CONFIG.copy()

        # 加载配置文件
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
                if file_config:
                    self._merge_config(config, file_config)
                    self._cache.clear()
            except Exception as e:
                logger.warning(f"加载配置文件失败: {str(e)}")

        # 环境变量覆盖
        for env_key, config_key in self.ENV_OVERRIDES.items():
            env_val = os.environ.get(env_key)
            if env_val is not None:
                self._set_nested(config, config_key, self._parse_env_value(env_val))

        return config

    @staticmethod
    def _set_nested(config: dict, key: str, value: Any) -> None:
        """Set a nested dict value using dot-notation key."""
        keys = key.split(".")
        d = config
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """Parse env var string to appropriate Python type."""
        if value.lower() in ("true", "1", "yes"):
            return True
        if value.lower() in ("false", "0", "no"):
            return False
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    def _merge_config(self, base: dict, override: dict):
        """合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Optional[T] = None, expected_type: Optional[Type[T]] = None) -> Optional[T]:
        """获取配置值（支持类型验证和缓存）

        Args:
            key: 配置键（支持点号分隔的嵌套键，如 "workflow.max_iterations"）
            default: 默认值
            expected_type: 期望的返回类型（如果提供，会进行类型验证）

        Returns:
            配置值，或默认值（如果键不存在或类型不匹配）

        Examples:
            >>> config.get("workflow.max_iterations")
            100
            >>> config.get("workflow.max_iterations", expected_type=int)
            100
            >>> config.get("nonexistent.key", default=10)
            10
        """
        # 检查缓存
        if key in self._cache:
            return self._cache[key]

        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = default
                break

        # 如果指定了期望类型，进行验证
        if expected_type is not None and value is not None and not isinstance(value, expected_type):
            logger.warning(f"配置类型不匹配: {key} 期望 {expected_type.__name__}, " f"实际 {type(value).__name__}，返回默认值")
            value = default

        # 只有当值不是默认值时才缓存（避免不同默认值的冲突）
        if value != default and value is not None:
            self._cache[key] = value
        return value

    def set(self, key: str, value):
        """设置配置"""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

        # 清除相关缓存（包括该键本身和所有可能的父级键）
        cache_key = key
        while cache_key:
            if cache_key in self._cache:
                del self._cache[cache_key]
            # 移除最后一部分来获取父级键
            parts = cache_key.split(".")
            if len(parts) > 1:
                cache_key = ".".join(parts[:-1])
            else:
                cache_key = ""

    def save(self):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file) or ".", exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            return False


# 创建全局配置实例
config_manager = ConfigManager()


# 导出配置获取函数
def get_config(key: str, default=None):
    """获取配置"""
    return config_manager.get(key, default)


def set_config(key: str, value):
    """设置配置"""
    config_manager.set(key, value)


def save_config():
    """保存配置"""
    return config_manager.save()
