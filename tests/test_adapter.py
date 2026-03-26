"""Tests for Agent/Skill Configuration Adapter"""

import json
import pytest
from pathlib import Path

from lingflow.coordination.adapter import (
    AgentAdapter,
    SkillAdapter,
    CapabilityMatcher,
    load_agents,
    load_skills,
    create_matcher
)


class TestAgentAdapter:
    """测试 Agent 适配器"""

    def test_detect_v1_format(self):
        """测试识别 v1 格式"""
        v1_config = {
            "agents": [
                {
                    "name": "review",
                    "capabilities": ["code_review", "design_review"],
                    "max_tasks": 2
                }
            ]
        }
        assert AgentAdapter.detect_version(v1_config) == "v1"

    def test_detect_v2_format(self):
        """测试识别 v2 格式"""
        v2_config = {
            "version": "2.0",
            "agents": [
                {
                    "name": "reviewer",
                    "capabilities": {
                        "code_review": {"context_limit": 12000}
                    }
                }
            ]
        }
        assert AgentAdapter.detect_version(v2_config) == "v2"

    def test_v1_to_v2_conversion(self):
        """测试 v1 到 v2 转换"""
        v1_config = {
            "agents": [
                {
                    "name": "review",
                    "description": "Review agent",
                    "capabilities": ["code_review", "design_review"],
                    "max_tasks": 2,
                    "context_limit": 12000,
                    "timeout": 180,
                    "parallel_safe": True
                }
            ],
            "settings": {
                "default_max_parallel": 3,
                "compression_enabled": True
            }
        }

        v2_config = AgentAdapter.v1_to_v2(v1_config)

        # 验证结构
        assert v2_config["version"] == "2.0"
        assert len(v2_config["agents"]) == 1

        agent = v2_config["agents"][0]
        assert agent["name"] == "reviewer"  # 名称映射
        assert isinstance(agent["capabilities"], dict)
        assert "code_review" in agent["capabilities"]
        assert agent["constraints"]["max_concurrent"] == 2

    def test_name_mapping(self):
        """测试 Agent 名称映射"""
        assert AgentAdapter.NAME_MAPPINGS["review"] == "reviewer"
        assert AgentAdapter.NAME_MAPPINGS["testing"] == "tester"
        assert AgentAdapter.NAME_MAPPINGS["debugging"] == "debugger"


class TestSkillAdapter:
    """测试 Skill 适配器"""

    def test_detect_v1_format(self):
        """测试识别 v1 格式"""
        v1_config = {
            "skills": [
                {
                    "name": "code-review",
                    "triggers": ["review"]
                }
            ]
        }
        assert SkillAdapter.detect_version(v1_config) == "v1"

    def test_detect_v2_format(self):
        """测试识别 v2 格式"""
        v2_config = {
            "version": "2.0",
            "skills": [
                {
                    "name": "code-review",
                    "requires_capability": "code_review"
                }
            ]
        }
        assert SkillAdapter.detect_version(v2_config) == "v2"

    def test_v1_to_v2_conversion(self):
        """测试 v1 到 v2 转换"""
        v1_config = {
            "skills": [
                {
                    "name": "code-review",
                    "description": "Execute code review",
                    "path": "skills/code-review/SKILL.md",
                    "triggers": ["code review"],
                    "depends_on": []
                },
                {
                    "name": "requesting-code-review",
                    "description": "Request code review",
                    "triggers": ["request review"]
                }
            ],
            "settings": {
                "auto_trigger": True
            }
        }

        v2_config = SkillAdapter.v1_to_v2(v1_config)

        # 验证结构
        assert v2_config["version"] == "2.0"
        assert "deprecated" in v2_config

        # requesting-code-review 应该被标记为废弃
        deprecated_names = [s["name"] for s in v2_config["deprecated"]["skills"]]
        assert "requesting-code-review" in deprecated_names


class TestCapabilityMatcher:
    """测试 Capability 匹配器"""

    @pytest.fixture
    def sample_agents(self):
        """示例 agents 配置"""
        return {
            "version": "2.0",
            "agents": [
                {
                    "name": "reviewer",
                    "capabilities": {
                        "code_review": {},
                        "design_review": {},
                        "security_check": {}
                    }
                },
                {
                    "name": "tester",
                    "capabilities": {
                        "test_generation": {},
                        "test_execution": {},
                        "coverage_analysis": {}
                    }
                },
                {
                    "name": "debugger",
                    "capabilities": {
                        "error_analysis": {},
                        "root_cause": {}
                    }
                }
            ]
        }

    def test_build_capability_index(self, sample_agents):
        """测试构建 capability 索引"""
        matcher = CapabilityMatcher(sample_agents)

        assert "code_review" in matcher.agents
        assert "test_generation" in matcher.agents
        assert "error_analysis" in matcher.agents

    def test_find_single_capability(self, sample_agents):
        """测试查询单个 capability"""
        matcher = CapabilityMatcher(sample_agents)

        agents = matcher.find_agents_for_capability("code_review")
        assert len(agents) == 1
        assert agents[0]["name"] == "reviewer"

    def test_find_multiple_capabilities(self, sample_agents):
        """测试查询多个 capabilities"""
        matcher = CapabilityMatcher(sample_agents)

        agents = matcher.find_agents_for_capability(["test_generation", "test_execution"])
        assert len(agents) == 1
        assert agents[0]["name"] == "tester"

    def test_match_skill_to_agent(self, sample_agents):
        """测试 Skill 到 Agent 匹配"""
        matcher = CapabilityMatcher(sample_agents)

        skill = {
            "name": "code-review",
            "requires_capability": "code_review"
        }

        agent = matcher.match_skill_to_agent(skill)
        assert agent["name"] == "reviewer"

    def test_match_skill_with_preferred_agent(self, sample_agents):
        """测试使用首选 agent"""
        matcher = CapabilityMatcher(sample_agents)

        skill = {
            "name": "custom-review",
            "preferred_agent": "tester"
        }

        agent = matcher.match_skill_to_agent(skill)
        assert agent["name"] == "tester"


class TestIntegration:
    """集成测试"""

    def test_load_existing_v1_configs(self):
        """测试加载现有的 v1 配置"""
        # 加载 agents
        agents = load_agents("agents/agents.json")
        assert agents["version"] == "2.0"

        # 加载 skills
        skills = load_skills("skills/skills.json")
        assert skills["version"] == "2.0"

    def test_load_v2_configs(self):
        """测试加载 v2 配置"""
        agents = load_agents("agents/agents.v2.json")
        assert agents["version"] == "2.0"

        skills = load_skills("skills/skills.v2.json")
        assert skills["version"] == "2.0"

    def test_create_matcher_from_loaded_config(self):
        """测试从加载的配置创建匹配器"""
        agents = load_agents("agents/agents.v2.json")
        matcher = create_matcher(agents)

        # 验证可以匹配
        agents = matcher.find_agents_for_capability("code_review")
        assert len(agents) > 0

    def test_skill_agent_mapping_consistency(self):
        """测试 Skill-Agent 映射一致性"""
        agents = load_agents("agents/agents.v2.json")
        skills = load_skills("skills/skills.v2.json")
        matcher = create_matcher(agents)

        # 检查每个有 requires_capability 的 skill 都能找到匹配
        unmatched = []
        for skill in skills["skills"]:
            required = skill.get("requires_capability")
            if required:
                agent = matcher.match_skill_to_agent(skill)
                if not agent:
                    unmatched.append(skill["name"])

        # 应该没有未匹配的 skill
        assert len(unmatched) == 0, f"Unmatched skills: {unmatched}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
