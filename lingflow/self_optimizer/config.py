"""
lingflow 自优化配置管理
"""

from pathlib import Path
from typing import Any, Dict

# 默认配置
DEFAULT_CONFIG = {
    # 触发条件配置
    "triggers": {
        # 质量相关
        "quality": {
            "review_score_below": 70,  # 代码审查得分低于阈值
            "coverage_drop_above": 5,  # 测试覆盖率下降超过5%
            "test_failure_rate_above": 10,  # 测试失败率超过10%
        },
        # 结构相关
        "structure": {
            "complexity_above": 15,  # 平均圈复杂度超过阈值
            "large_classes_count_above": 5,  # 大型类数量超过阈值
            "duplication_rate_above": 0.05,  # 重复代码率超过5%
            "coupling_above": 10,  # 平均耦合度超过阈值
        },
        # 性能相关
        "performance": {
            "execution_time_increase_ratio": 1.5,  # 执行时间增加50%
            "memory_usage_above_mb": 500,  # 内存使用超过500MB
            "response_time_above_ms": 100,  # API响应时间超过100ms
        },
        # 规模相关
        "scale": {
            "new_lines_above": 500,  # 新增代码超过500行
            "new_files_above": 10,  # 新增文件超过10个
            "deleted_lines_above": 200,  # 删除代码超过200行
        },
        # 技术债务
        "tech_debt": {
            "todo_count_above": 20,  # TODO注释超过20个
            "deprecated_count_above": 5,  # 废弃代码超过5处
            "hack_comments_above": 3,  # HACK标记超过3个
        },
        # 时间相关
        "time": {
            "days_since_last_optimization": 7,  # 距上次优化超过7天
            "commits_since_last_check": 20,  # 距上次检查超过20次提交
        },
    },
    # 优化限制配置
    "optimization": {
        "max_experiments": 20,  # 最大实验次数
        "time_budget": 300,  # 时间预算（秒）
        "min_improvement_threshold": 0.1,  # 最小改进阈值
        "early_stopping_patience": 10,  # 早停耐心值
    },
    # 钩子配置
    "hooks": {
        "enable_on_review": True,  # 代码审查后启用
        "enable_on_test": True,  # 测试完成后启用
        "enable_on_commit": False,  # Git commit后启用（暂不启用）
        "require_confirmation": True,  # 需要用户确认
    },
    # 异步执行配置
    "async": {
        "enabled": True,  # 启用异步执行
        "max_concurrent": 1,  # 最大并发数
        "process_isolation": True,  # 进程隔离
    },
    # 报告配置
    "report": {
        "auto_save": True,  # 自动保存报告
        "report_dir": ".",  # 报告目录
        "include_comparison": True,  # 包含对比表格
        "include_steps": True,  # 包含实施步骤
    },
}


class OptimizationConfig:
    """自优化系统配置管理器"""

    def __init__(self, config_path: str = None):
        """
        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path
        self.config = DEFAULT_CONFIG.copy()

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str) -> None:
        """加载配置文件"""
        import yaml

        path = Path(config_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                self._merge_config(user_config)

    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """合并用户配置"""
        for key, value in user_config.items():
            if key in self.config and isinstance(self.config[key], dict):
                self.config[key].update(value)
            else:
                self.config[key] = value

    def get(self, key_path: str, default=None):
        """获取配置值

        Args:
            key_path: 配置路径，如 "triggers.quality.review_score_below"
            default: 默认值

        Returns:
            配置值
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """设置配置值"""
        keys = key_path.split(".")
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self, path: str = None) -> None:
        """保存配置到文件"""
        import yaml

        save_path = path or self.config_path
        if not save_path:
            raise ValueError("未指定配置文件路径")

        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

    def get_trigger_config(self, trigger_type: str) -> Dict[str, Any]:
        """获取触发器配置"""
        return self.config.get("triggers", {}).get(trigger_type, {})

    def get_optimization_config(self) -> Dict[str, Any]:
        """获取优化配置"""
        return self.config.get("optimization", {})

    def get_hooks_config(self) -> Dict[str, Any]:
        """获取钩子配置"""
        return self.config.get("hooks", {})


# 全局配置管理器实例
_global_config: OptimizationConfig = None


def get_global_config() -> OptimizationConfig:
    """获取全局配置管理器"""
    global _global_config
    if _global_config is None:
        _global_config = OptimizationConfig()
    return _global_config


def set_global_config(config: OptimizationConfig) -> None:
    """设置全局配置管理器"""
    global _global_config
    _global_config = config
