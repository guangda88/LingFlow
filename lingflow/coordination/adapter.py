"""lingflow Agent/Skill 配置适配器

支持 v1 和 v2 配置格式的转换和兼容。

使用示例:
    from lingflow.coordination.adapter import AgentAdapter, SkillAdapter

    # 自动检测版本并转换
    adapter = AgentAdapter()
    v2_config = adapter.load("agents/agents.json")  # 自动识别 v1/v2

    # 显式转换
    v1_config = {...}  # 旧格式
    v2_config = AgentAdapter.v1_to_v2(v1_config)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class AgentAdapter:
    """Agent 配置适配器 - 支持 v1/v2 格式转换"""

    # v1 Agent 名称到 v2 的映射 (部分重命名)
    NAME_MAPPINGS = {
        "review": "reviewer",
        "testing": "tester",
        "debugging": "debugger",
        "architecture": "architect",
        "documentation": "documentation",  # 保持不变
        "implementation": "implementation",  # 保持不变
    }

    # v1 capability 到 v2 capability 的映射
    CAPABILITY_MAPPINGS = {
        "code_review": "code_review",
        "design_review": "design_review",
        "security_check": "security_check",
        "quality_analysis": "quality_analysis",
        "test_generation": "test_generation",
        "test_execution": "test_execution",
        "coverage_analysis": "coverage_analysis",
        "performance_testing": "performance_testing",
        "error_analysis": "error_analysis",
        "root_cause": "root_cause",
        "fix_generation": "fix_generation",
        "log_analysis": "log_analysis",
        "system_design": "system_design",
        "architecture_review": "architecture_review",
        "api_design": "api_design",
        "schema_design": "schema_design",
        "doc_generation": "doc_generation",
        "api_doc_writing": "api_doc_writing",
        "tutorial_creation": "tutorial_creation",
        "readme_generation": "readme_generation",
        "code_generation": "code_generation",
        "refactoring": "refactoring",
        "testing": "testing",
        "documentation": "documentation",
    }

    @classmethod
    def detect_version(cls, config: Dict[str, Any]) -> str:
        """检测配置文件版本

        Args:
            config: 配置字典

        Returns:
            "v1" 或 "v2"
        """
        # v2 格式包含 "version" 字段
        if "version" in config:
            return "v2"

        # 检查 agents 数组中的第一个元素
        if "agents" in config and len(config["agents"]) > 0:
            first_agent = config["agents"][0]

            # v2 格式的 capabilities 是字典
            if isinstance(first_agent.get("capabilities"), dict):
                return "v2"

            # v1 格式的 capabilities 是列表
            if isinstance(first_agent.get("capabilities"), list):
                return "v1"

        # 默认认为是 v1
        return "v1"

    @classmethod
    def v1_to_v2(cls, v1_config: Dict[str, Any]) -> Dict[str, Any]:
        """将 v1 格式转换为 v2 格式

        Args:
            v1_config: v1 格式的配置

        Returns:
            v2 格式的配置
        """
        v2_config = {"version": "2.0", "description": v1_config.get("description", "Migrated from v1"), "agents": []}

        # 转换 settings
        if "settings" in v1_config:
            v2_config["settings"] = cls._migrate_settings(v1_config["settings"])

        # 转换每个 agent
        for v1_agent in v1_config.get("agents", []):
            v2_agent = cls._migrate_agent(v1_agent)
            v2_config["agents"].append(v2_agent)

        return v2_config

    @classmethod
    def _migrate_agent(cls, v1_agent: Dict[str, Any]) -> Dict[str, Any]:
        """迁移单个 agent 配置"""
        name = v1_agent["name"]
        v2_name = cls.NAME_MAPPINGS.get(name, name)

        # 构建新的 capabilities 结构
        capabilities = {}
        for cap in v1_agent.get("capabilities", []):
            v2_cap = cls.CAPABILITY_MAPPINGS.get(cap, cap)
            capabilities[v2_cap] = {
                "description": f"{cap} capability",
                "context_limit": v1_agent.get("context_limit", 8000),
                "timeout": v1_agent.get("timeout", 300),
            }

        return {
            "name": v2_name,
            "description": v1_agent.get("description", ""),
            "capabilities": capabilities,
            "constraints": {
                "max_concurrent": v1_agent.get("max_tasks", 1),
                "parallel_safe": v1_agent.get("parallel_safe", True),
                "requires_isolation": v1_agent.get("requires_isolation", False),
            },
        }

    @classmethod
    def _migrate_settings(cls, v1_settings: Dict[str, Any]) -> Dict[str, Any]:
        """迁移 settings 配置"""
        return {
            "default_max_parallel": v1_settings.get("default_max_parallel", 3),
            "task_timeout": v1_settings.get("task_timeout", 300),
            "retry_failed_tasks": v1_settings.get("retry_failed_tasks", True),
            "max_retries": v1_settings.get("max_retries", 2),
            "compression_enabled": v1_settings.get("compression_enabled", True),
            "compression_target_tokens": v1_settings.get("compression_target_tokens", 4000),
            "context_preserve_sections": v1_settings.get("context_preserve_sections", []),
            "capability_matching": {"strategy": "exact_or_broader", "fallback_enabled": True},
        }

    @classmethod
    def load(cls, path: Union[str, Path]) -> Dict[str, Any]:
        """加载配置文件，自动识别版本并返回 v2 格式

        Args:
            path: 配置文件路径

        Returns:
            v2 格式的配置
        """
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)

        version = cls.detect_version(config)

        if version == "v2":
            logger.info(f"Loaded v2 config from {path}")
            return config
        else:
            logger.info(f"Migrating v1 config from {path} to v2")
            return cls.v1_to_v2(config)

    @classmethod
    def save(cls, config: Dict[str, Any], path: Union[str, Path]) -> None:
        """保存配置文件

        Args:
            config: 配置字典 (v2 格式)
            path: 保存路径
        """
        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved config to {path}")


class SkillAdapter:
    """Skill 配置适配器 - 支持 v1/v2 格式转换"""

    @classmethod
    def detect_version(cls, config: Dict[str, Any]) -> str:
        """检测配置文件版本"""
        if "version" in config:
            return "v2"
        return "v1"

    @classmethod
    def v1_to_v2(cls, v1_config: Dict[str, Any]) -> Dict[str, Any]:
        """将 v1 格式转换为 v2 格式"""
        v2_config = {
            "version": "2.0",
            "description": "Migrated from v1",
            "skills": [],
            "settings": v1_config.get("settings", {}),
            "deprecated": {
                "skills": [
                    {"name": "requesting-code-review", "replaced_by": "code-review", "since": "v2.0", "remove_in": "v4.0"}
                ]
            },
        }

        # Skill 类别映射
        categories = {
            "development-workflow": [
                "brainstorming",
                "writing-plans",
                "test-driven-development",
                "systematic-debugging",
                "subagent-driven-development",
                "verification-before-completion",
            ],
            "version-control": ["using-git-worktrees", "finishing-a-development-branch"],
            "code-quality": ["code-review", "code-review-js"],
            "workflow-control": [
                "dispatching-parallel-agents",
                "workflow-executor",
                "task-runner",
                "conditional-branch",
                "loop-iterator",
                "error-handler",
            ],
            "integration": ["notification"],
            "skill-management": ["skill-creator"],
            "data": ["database-export"],
        }

        def get_category(skill_name: str) -> str:
            for cat, skills in categories.items():
                if skill_name in skills:
                    return cat
            return "other"

        # Phase 映射
        phase_map = {
            "brainstorming": "requirements",
            "writing-plans": "design",
            "test-driven-development": "testing",
            "systematic-debugging": "debugging",
            "subagent-driven-development": "implementation",
            "verification-before-completion": "testing",
            "code-review": "review",
            "code-review-js": "review",
        }

        # Capability 映射
        capability_map = {
            "writing-plans": "system_design",
            "test-driven-development": ["test_generation", "test_execution"],
            "systematic-debugging": ["error_analysis", "log_analysis"],
            "subagent-driven-development": "code_generation",
            "verification-before-completion": "test_execution",
            "code-review": "code_review",
            "code-review-js": "code_review",
            "skill-creator": "doc_generation",
        }

        # Agent 映射
        agent_map = {
            "writing-plans": "architect",
            "test-driven-development": "tester",
            "systematic-debugging": "debugger",
            "subagent-driven-development": "implementation",
            "verification-before-completion": "tester",
            "code-review": "reviewer",
            "code-review-js": "reviewer",
            "skill-creator": "documentation",
        }

        for v1_skill in v1_config.get("skills", []):
            name = v1_skill["name"]

            v2_skill = {
                "name": name,
                "description": v1_skill.get("description", ""),
                "version": "2.0",
                "category": get_category(name),
                "triggers": v1_skill.get("triggers", []),
                "phase": phase_map.get(name, "any"),
                "requires_capability": capability_map.get(name),
                "preferred_agent": agent_map.get(name),
                "depends_on": v1_skill.get("depends_on", []),
                "config": {},
            }

            # 检查是否在废弃列表中
            if name in ["requesting-code-review", "receiving-code-review"]:
                v2_config["deprecated"]["skills"].append(
                    {"name": name, "replaced_by": "code-review", "since": "v2.0", "remove_in": "v4.0"}
                )
                continue

            v2_config["skills"].append(v2_skill)

        return v2_config

    @classmethod
    def load(cls, path: Union[str, Path]) -> Dict[str, Any]:
        """加载配置文件，自动识别版本并返回 v2 格式"""
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)

        version = cls.detect_version(config)

        if version == "v2":
            logger.info(f"Loaded v2 config from {path}")
            return config
        else:
            logger.info(f"Migrating v1 config from {path} to v2")
            return cls.v1_to_v2(config)

    @classmethod
    def save(cls, config: Dict[str, Any], path: Union[str, Path]) -> None:
        """保存配置文件"""
        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved config to {path}")


class CapabilityMatcher:
    """Capability 匹配器 - 将 Skill 需求映射到合适的 Agent"""

    def __init__(self, agents_config: Dict[str, Any]):
        """初始化匹配器

        Args:
            agents_config: v2 格式的 agents 配置
        """
        self.agents = self._build_capability_index(agents_config)

    def _build_capability_index(self, config: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """构建 capability 索引

        返回: {capability: [agents_with_capability]}
        """
        index: dict[str, list[dict[str, Any]]] = {}

        for agent in config.get("agents", []):
            agent_name = agent["name"]
            for capability in agent.get("capabilities", {}).keys():
                if capability not in index:
                    index[capability] = []
                index[capability].append({"name": agent_name, "agent": agent})

        return index

    def find_agents_for_capability(self, capability: Union[str, List[str]]) -> List[Dict]:
        """查找支持指定 capability 的 agents

        Args:
            capability: 单个 capability 或 capability 列表

        Returns:
            匹配的 agents 列表
        """
        if isinstance(capability, str):
            return self.agents.get(capability, [])

        # 多个 capability - 需要同时支持
        # 使用 agent 名称集合来求交集
        result_name_sets = []
        for cap in capability:
            agent_names = {a["name"] for a in self.agents.get(cap, [])}
            result_name_sets.append(agent_names)

        if not result_name_sets:
            return []

        # 取交集
        intersection = result_name_sets[0].copy()
        for name_set in result_name_sets[1:]:
            intersection &= name_set

        # 根据名称重建 agent 字典列表
        all_agents = {}
        for agents_list in self.agents.values():
            for agent_info in agents_list:
                all_agents[agent_info["name"]] = agent_info

        return [all_agents[name] for name in intersection if name in all_agents]

    def match_skill_to_agent(self, skill: Dict[str, Any]) -> Optional[Dict]:
        """为 Skill 匹配最佳 Agent

        Args:
            skill: v2 格式的 skill 配置

        Returns:
            匹配的 agent，如果没有匹配则返回 None
        """
        # 1. 首选 agent
        if skill.get("preferred_agent"):
            return {"name": skill["preferred_agent"]}

        # 2. 按 capability 匹配
        required = skill.get("requires_capability")
        if required:
            candidates = self.find_agents_for_capability(required)
            if candidates:
                # 返回第一个候选 (可以扩展负载均衡逻辑)
                return candidates[0]

        return None


# 便捷函数
def load_agents(path: Union[str, Path] = "agents/agents.json") -> Dict[str, Any]:
    """加载 agents 配置，自动返回 v2 格式"""
    # 优先尝试 v2
    v2_path = Path(path).parent / f"{Path(path).stem}.v2.json"
    if v2_path.exists():
        return AgentAdapter.load(v2_path)

    # 回退到原文件
    if Path(path).exists():
        return AgentAdapter.load(path)

    raise FileNotFoundError(f"No agents config found at {path} or {v2_path}")


def load_skills(path: Union[str, Path] = "skills/skills.json") -> Dict[str, Any]:
    """加载 skills 配置，自动返回 v2 格式"""
    # 优先尝试 v2
    v2_path = Path(path).parent / f"{Path(path).stem}.v2.json"
    if v2_path.exists():
        return SkillAdapter.load(v2_path)

    # 回退到原文件
    if Path(path).exists():
        return SkillAdapter.load(path)

    raise FileNotFoundError(f"No skills config found at {path} or {v2_path}")


def create_matcher(agents_config: Dict[str, Any]) -> CapabilityMatcher:
    """创建 Capability 匹配器"""
    return CapabilityMatcher(agents_config)
