"""LingFlow Layered Skill Loader

Implements the three-layer architecture for skill loading:
- L1: Core scheduling (5 skills) - Never unload
- L2: Professional capabilities (12 skills) - Resident
- L3: Extended capabilities (16 skills) - Lazy load/unload after task

Version: 2.0
Date: 2026-03-26
"""

import asyncio
import logging
import os
import threading
import time
import yaml
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from lingflow.common.skill_manager import skill_manager
from lingflow.common.exceptions import SkillLoadError, SkillNotFoundError

logger = logging.getLogger(__name__)


class SkillLayer(str, Enum):
    """技能分层枚举"""
    L1 = "L1"  # 核心调度层 - 永不卸载
    L2 = "L2"  # 专业能力层 - 常驻内存
    L3 = "L3"  # 扩展能力层 - 按需加载


class LoadingStrategy(str, Enum):
    """加载策略"""
    EAGER = "eager"    # 启动时加载
    LAZY = "lazy"      # 按需加载


class UnloadingStrategy(str, Enum):
    """卸载策略"""
    NEVER = "never"          # 永不卸载
    AFTER_TASK = "after_task"  # 任务完成后卸载
    IDLE_TIMEOUT = "idle_timeout"  # 空闲超时后卸载


@dataclass
class SkillConfig:
    """技能配置"""
    name: str
    layer: SkillLayer
    category: str = ""
    description: str = ""
    triggers: List[str] = field(default_factory=list)
    loading_strategy: LoadingStrategy = LoadingStrategy.LAZY
    unloading_strategy: UnloadingStrategy = UnloadingStrategy.NEVER
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300
    priority: int = 5

    # 运行时状态
    loaded: bool = False
    load_time: float = 0
    last_used: float = 0
    use_count: int = 0


@dataclass
class LayerConfig:
    """层级配置"""
    layer: SkillLayer
    description: str
    loading_strategy: LoadingStrategy
    unloading_strategy: UnloadingStrategy
    memory_priority: str
    unload_timeout: int = 300  # 5分钟
    skills: Dict[str, SkillConfig] = field(default_factory=dict)

    # 运行时状态
    loaded_count: int = 0


class SkillRouter:
    """技能路由器 - 根据触发词和上下文路由到合适的技能"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "skills", "skills-layer-configuration.yaml"
        )
        self.routing_rules: List[Dict] = []
        self.mutex_groups: Dict[str, Set[str]] = {}
        self.dependency_chains: List[List[str]] = []
        self._load_routing_config()

    def _load_routing_config(self):
        """加载路由配置"""
        if not os.path.exists(self.config_path):
            logger.warning(f"路由配置文件不存在: {self.config_path}")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 提取路由规则
            routing = config.get("routing", {})
            if "priority_rules" in routing:
                self.routing_rules = routing["priority_rules"]
            if "mutex_constraints" in routing:
                for group_name, skills in routing["mutex_constraints"].items():
                    self.mutex_groups[group_name] = set(skills)
            if "dependency_chains" in routing:
                self.dependency_chains = routing["dependency_chains"]

            logger.info(f"加载路由配置成功: {len(self.routing_rules)} 条规则")
        except Exception as e:
            logger.error(f"加载路由配置失败: {e}")

    def route(self, input_text: str, active_skills: Set[str]) -> Optional[str]:
        """根据输入文本路由到合适的技能

        Args:
            input_text: 用户输入或触发词
            active_skills: 当前活跃的技能集合

        Returns:
            路由到的技能名称，如果没有匹配则返回 None
        """
        input_lower = input_text.lower()

        # 按优先级匹配路由规则
        for rule in sorted(self.routing_rules, key=lambda r: r.get("priority", 0), reverse=True):
            pattern = rule.get("pattern", "")
            if pattern and pattern.lower() in input_lower:
                skill_name = rule.get("route", "")
                # 检查互斥约束
                if self._check_mutex(skill_name, active_skills):
                    return skill_name.replace(".", "-")  # 转换命名格式
                else:
                    logger.debug(f"技能 {skill_name} 被互斥规则阻止")

        return None

    def _check_mutex(self, skill_name: str, active_skills: Set[str]) -> bool:
        """检查互斥约束

        Args:
            skill_name: 要激活的技能
            active_skills: 当前活跃的技能

        Returns:
            True 如果可以激活，False 如果被互斥规则阻止
        """
        for group_name, group_skills in self.mutex_groups.items():
            # 标准化技能名称进行比较
            normalized_name = skill_name.replace(".", "-").replace("_", "-").lower()
            normalized_group = {s.replace(".", "-").replace("_", "-").lower() for s in group_skills}
            normalized_active = {s.replace(".", "-").replace("_", "-").lower() for s in active_skills}

            if normalized_name in normalized_group:
                # 检查组内是否有其他活跃技能
                if normalized_active & normalized_group:
                    return False
        return True

    def get_dependencies(self, skill_name: str) -> List[str]:
        """获取技能的依赖链"""
        for chain in self.dependency_chains:
            if skill_name in chain:
                idx = chain.index(skill_name)
                return chain[:idx]
        return []


class LayeredSkillLoader:
    """分层技能加载器

    实现三层架构的技能加载和卸载管理：
    - L1: 核心调度层 (5个) - 永不卸载
    - L2: 专业能力层 (12个) - 常驻内存
    - L3: 扩展能力层 (16个) - 按需加载/卸载
    """

    # 默认的 L1 和 L2 技能清单 (核心常驻)
    L1_SKILLS = {
        "workflow-executor",
        "task-runner",
        "conditional-branch",
        "loop-iterator",
        "error-handler",
    }

    L2_SKILLS = {
        # 代码质量组
        "code-review",
        "code-refactor",
        # 开发流程组
        "brainstorming",
        "systematic-debugging",
        "verification-before-completion",
        # 测试验证组
        "test-runner",
        "test-driven-development",
        # 版本控制组
        "using-git-worktrees",
        "finishing-a-development-branch",
        # 通用服务
        "notification",
        "skill-creator",
        "writing-plans",
    }

    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "skills", "skills-layer-configuration.yaml"
        )

        # 层级配置
        self.layers: Dict[SkillLayer, LayerConfig] = {
            SkillLayer.L1: LayerConfig(
                layer=SkillLayer.L1,
                description="核心调度层",
                loading_strategy=LoadingStrategy.EAGER,
                unloading_strategy=UnloadingStrategy.NEVER,
                memory_priority="critical",
            ),
            SkillLayer.L2: LayerConfig(
                layer=SkillLayer.L2,
                description="专业能力层",
                loading_strategy=LoadingStrategy.EAGER,
                unloading_strategy=UnloadingStrategy.NEVER,
                memory_priority="high",
            ),
            SkillLayer.L3: LayerConfig(
                layer=SkillLayer.L3,
                description="扩展能力层",
                loading_strategy=LoadingStrategy.LAZY,
                unloading_strategy=UnloadingStrategy.AFTER_TASK,
                memory_priority="normal",
                unload_timeout=300,
            ),
        }

        # 技能配置
        self.skills: Dict[str, SkillConfig] = {}

        # 活跃的 L3 技能 (正在使用中)
        self._active_l3_skills: Set[str] = set()

        # 锁
        self._lock = threading.RLock()

        # 路由器
        self.router = SkillRouter(self.config_path)

        # 卸载任务
        self._unload_task: Optional[asyncio.Task] = None
        self._unload_event = asyncio.Event()

        # 加载配置
        self._load_configuration()

        # 启动时加载 L1 和 L2
        self._load_core_skills()

    def _load_configuration(self):
        """加载技能分层配置"""
        if not os.path.exists(self.config_path):
            logger.warning(f"分层配置文件不存在: {self.config_path}")
            self._load_default_configuration()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 解析 L1 配置
            for skill_def in config.get("L1", {}).get("skills", []):
                self._register_skill(skill_def, SkillLayer.L1)

            # 解析 L2 配置
            l2_config = config.get("L2", {})
            for group_name, group_def in l2_config.get("groups", {}).items():
                for skill_def in group_def.get("skills", []):
                    skill_def["group"] = group_name
                    self._register_skill(skill_def, SkillLayer.L2)

            # 解析 L3 配置
            l3_config = config.get("L3", {})
            for category_name, category_def in l3_config.get("categories", {}).items():
                for skill_def in category_def.get("skills", []):
                    skill_def["category"] = category_name
                    self._register_skill(skill_def, SkillLayer.L3)

            logger.info(f"加载分层配置成功: L1={self.layers[SkillLayer.L1].loaded_count}, "
                       f"L2={self.layers[SkillLayer.L2].loaded_count}, "
                       f"L3={len([s for s in self.skills.values() if s.layer == SkillLayer.L3])}")
        except Exception as e:
            logger.error(f"加载分层配置失败: {e}")
            self._load_default_configuration()

    def _load_default_configuration(self):
        """加载默认配置"""
        for skill_name in self.L1_SKILLS:
            self.skills[skill_name] = SkillConfig(
                name=skill_name,
                layer=SkillLayer.L1,
                loading_strategy=LoadingStrategy.EAGER,
                unloading_strategy=UnloadingStrategy.NEVER,
            )
        for skill_name in self.L2_SKILLS:
            self.skills[skill_name] = SkillConfig(
                name=skill_name,
                layer=SkillLayer.L2,
                loading_strategy=LoadingStrategy.EAGER,
                unloading_strategy=UnloadingStrategy.NEVER,
            )

    def _register_skill(self, skill_def: Dict, layer: SkillLayer):
        """注册技能配置"""
        name = skill_def.get("name", "")
        if not name:
            return

        # 转换命名格式 (驼峰转短横线)
        normalized_name = name.replace("_", "-")

        self.skills[normalized_name] = SkillConfig(
            name=normalized_name,
            layer=layer,
            category=skill_def.get("category", ""),
            description=skill_def.get("description", ""),
            triggers=skill_def.get("triggers", []),
            loading_strategy=LoadingStrategy(skill_def.get("loading_strategy", "lazy")),
            unloading_strategy=UnloadingStrategy(skill_def.get("unloading_strategy", "never")),
            dependencies=skill_def.get("depends_on", []),
            timeout=skill_def.get("timeout", 300),
            priority=skill_def.get("priority", 5),
        )

    def _load_core_skills(self):
        """启动时加载核心技能 (L1 + L2)"""
        logger.info("开始加载核心技能 (L1 + L2)...")

        with self._lock:
            # 加载 L1
            for skill_name in self.L1_SKILLS:
                self._load_skill(skill_name)

            # 加载 L2
            for skill_name in self.L2_SKILLS:
                self._load_skill(skill_name)

        logger.info(f"核心技能加载完成: L1={self.layers[SkillLayer.L1].loaded_count}, "
                   f"L2={self.layers[SkillLayer.L2].loaded_count}")

    def _load_skill(self, skill_name: str) -> bool:
        """加载单个技能

        Args:
            skill_name: 技能名称

        Returns:
            True 如果加载成功，否则 False
        """
        if skill_name not in self.skills:
            # 动态添加到配置
            self.skills[skill_name] = SkillConfig(
                name=skill_name,
                layer=SkillLayer.L3,  # 未知技能默认为 L3
                loading_strategy=LoadingStrategy.LAZY,
            )

        config = self.skills[skill_name]

        # 检查是否已加载
        if config.loaded:
            return True

        try:
            # 加载技能模块
            skill_manager.load_skill(skill_name)

            # 更新状态
            config.loaded = True
            config.load_time = time.time()
            config.last_used = time.time()
            config.use_count += 1

            # 更新层级统计
            self.layers[config.layer].loaded_count += 1

            logger.info(f"加载技能: {skill_name} (L{config.layer.value})")
            return True

        except (SkillLoadError, SkillNotFoundError) as e:
            logger.warning(f"加载技能 {skill_name} 失败: {e}")
            return False

    def load_skill(self, skill_name: str) -> bool:
        """加载技能 (公开接口)

        Args:
            skill_name: 技能名称

        Returns:
            True 如果加载成功，否则 False
        """
        with self._lock:
            # 检查是否已加载
            if skill_name in self.skills and self.skills[skill_name].loaded:
                self.skills[skill_name].last_used = time.time()
                return True

            # 加载依赖
            dependencies = self.router.get_dependencies(skill_name)
            for dep in dependencies:
                self._load_skill(dep)

            # 加载技能
            success = self._load_skill(skill_name)

            if success and self.skills[skill_name].layer == SkillLayer.L3:
                self._active_l3_skills.add(skill_name)

            return success

    def unload_skill(self, skill_name: str) -> bool:
        """卸载技能 (仅 L3)

        Args:
            skill_name: 技能名称

        Returns:
            True 如果卸载成功，否则 False
        """
        with self._lock:
            if skill_name not in self.skills:
                return False

            config = self.skills[skill_name]

            # L1 和 L2 不允许卸载
            if config.layer in (SkillLayer.L1, SkillLayer.L2):
                logger.debug(f"L{config.layer.value} 技能不允许卸载: {skill_name}")
                return False

            if not config.loaded:
                return True

            # 从缓存中移除
            if skill_name in skill_manager.skills_cache:
                del skill_manager.skills_cache[skill_name]
            if skill_name in skill_manager.skill_mtime:
                del skill_manager.skill_mtime[skill_name]

            # 更新状态
            config.loaded = False
            self.layers[config.layer].loaded_count -= 1
            self._active_l3_skills.discard(skill_name)

            logger.info(f"卸载技能: {skill_name}")
            return True

    def unload_idle_l3_skills(self, idle_timeout: int = 300) -> int:
        """卸载空闲的 L3 技能

        Args:
            idle_timeout: 空闲超时时间 (秒)

        Returns:
            卸载的技能数量
        """
        with self._lock:
            now = time.time()
            unloaded = 0

            for skill_name in list(self._active_l3_skills):
                if skill_name not in self.skills:
                    continue

                config = self.skills[skill_name]
                if config.layer != SkillLayer.L3:
                    continue

                # 检查空闲时间
                idle_time = now - config.last_used
                if idle_time > idle_timeout:
                    if self.unload_skill(skill_name):
                        unloaded += 1

            return unloaded

    def mark_task_complete(self, skill_name: str = None):
        """标记任务完成，触发 L3 技能卸载检查

        Args:
            skill_name: 完成的技能名称，如果为 None 则检查所有 L3
        """
        if skill_name:
            # 只卸载指定的技能
            if skill_name in self.skills and self.skills[skill_name].layer == SkillLayer.L3:
                self.unload_skill(skill_name)
        else:
            # 卸载所有空闲的 L3 技能
            self.unload_idle_l3_skills(idle_timeout=0)  # 立即卸载

    def route(self, input_text: str) -> Optional[str]:
        """路由到合适的技能

        Args:
            input_text: 输入文本

        Returns:
            路由到的技能名称
        """
        return self.router.route(input_text, self._active_l3_skills)

    def get_skill_config(self, skill_name: str) -> Optional[SkillConfig]:
        """获取技能配置

        Args:
            skill_name: 技能名称

        Returns:
            技能配置，如果不存在则返回 None
        """
        return self.skills.get(skill_name)

    def get_layer_stats(self) -> Dict[str, Dict]:
        """获取各层统计信息

        Returns:
            各层的统计信息
        """
        stats = {}
        for layer, config in self.layers.items():
            layer_skills = [s for s in self.skills.values() if s.layer == layer]
            stats[layer.value] = {
                "total": len(layer_skills),
                "loaded": config.loaded_count,
                "active": len([s for s in layer_skills if s.loaded]),
            }
        return stats

    def list_active_l3_skills(self) -> List[str]:
        """列出当前活跃的 L3 技能

        Returns:
            活跃的 L3 技能名称列表
        """
        with self._lock:
            return list(self._active_l3_skills)

    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况

        Returns:
            内存使用统计
        """
        total_cached = len(skill_manager.skills_cache)
        l1_loaded = sum(1 for s in self.skills.values() if s.layer == SkillLayer.L1 and s.loaded)
        l2_loaded = sum(1 for s in self.skills.values() if s.layer == SkillLayer.L2 and s.loaded)
        l3_loaded = sum(1 for s in self.skills.values() if s.layer == SkillLayer.L3 and s.loaded)

        return {
            "total_cached": total_cached,
            "l1_loaded": l1_loaded,
            "l2_loaded": l2_loaded,
            "l3_loaded": l3_loaded,
            "l3_active": len(self._active_l3_skills),
            "target_l3_max": 15,
        }


# 全局单例
_layered_loader: Optional[LayeredSkillLoader] = None
_loader_lock = threading.Lock()


def get_layered_loader() -> LayeredSkillLoader:
    """获取分层技能加载器单例"""
    global _layered_loader
    if _layered_loader is None:
        with _loader_lock:
            if _layered_loader is None:
                _layered_loader = LayeredSkillLoader()
    return _layered_loader


def load_skill(skill_name: str) -> bool:
    """加载技能 (使用分层加载器)

    Args:
        skill_name: 技能名称

    Returns:
        True 如果加载成功，否则 False
    """
    return get_layered_loader().load_skill(skill_name)


def unload_skill(skill_name: str) -> bool:
    """卸载技能 (使用分层加载器)

    Args:
        skill_name: 技能名称

    Returns:
        True 如果卸载成功，否则 False
    """
    return get_layered_loader().unload_skill(skill_name)


def mark_task_complete(skill_name: str = None):
    """标记任务完成

    Args:
        skill_name: 完成的技能名称
    """
    get_layered_loader().mark_task_complete(skill_name)


def route_skill(input_text: str) -> Optional[str]:
    """路由到合适的技能

    Args:
        input_text: 输入文本

    Returns:
        路由到的技能名称
    """
    return get_layered_loader().route(input_text)


def get_layer_stats() -> Dict[str, Dict]:
    """获取层级统计信息

    Returns:
        各层的统计信息
    """
    return get_layered_loader().get_layer_stats()


def get_memory_usage() -> Dict[str, Any]:
    """获取内存使用情况

    Returns:
        内存使用统计
    """
    return get_layered_loader().get_memory_usage()
