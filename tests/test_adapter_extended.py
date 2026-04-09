import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from lingflow.coordination.adapter import (
    AgentAdapter,
    CapabilityMatcher,
    SkillAdapter,
    create_matcher,
    load_agents,
    load_skills,
)


class TestAgentAdapterDetectVersion:
    def test_detect_v1_with_version_key_absent(self):
        v1 = {"agents": [{"name": "impl", "capabilities": ["code_generation"]}]}
        assert AgentAdapter.detect_version(v1) == "v1"

    def test_detect_v2_with_version_key(self):
        v2 = {"version": "2.0", "agents": []}
        assert AgentAdapter.detect_version(v2) == "v2"

    def test_detect_v2_by_capabilities_dict(self):
        v2 = {"agents": [{"name": "impl", "capabilities": {"code_generation": {}}}]}
        assert AgentAdapter.detect_version(v2) == "v2"

    def test_detect_v1_empty_agents(self):
        assert AgentAdapter.detect_version({}) == "v1"
        assert AgentAdapter.detect_version({"agents": []}) == "v1"


class TestAgentAdapterConversion:
    def test_v1_to_v2_full_conversion(self):
        v1 = {
            "agents": [
                {
                    "name": "review",
                    "description": "Review agent",
                    "capabilities": ["code_review", "design_review"],
                    "max_tasks": 2,
                    "context_limit": 12000,
                    "timeout": 180,
                    "parallel_safe": True,
                }
            ],
            "settings": {
                "default_max_parallel": 3,
                "compression_enabled": True,
            },
        }
        v2 = AgentAdapter.v1_to_v2(v1)
        assert v2["version"] == "2.0"
        assert len(v2["agents"]) == 1
        agent = v2["agents"][0]
        assert agent["name"] == "reviewer"
        assert "code_review" in agent["capabilities"]
        assert "design_review" in agent["capabilities"]
        assert agent["constraints"]["max_concurrent"] == 2
        assert agent["constraints"]["parallel_safe"] is True

    def test_v1_to_v2_no_settings(self):
        v1 = {"agents": [{"name": "implementation", "capabilities": ["code_generation"]}]}
        v2 = AgentAdapter.v1_to_v2(v1)
        assert "settings" not in v2

    def test_v1_to_v2_unknown_name_preserved(self):
        v1 = {"agents": [{"name": "custom_agent", "capabilities": ["custom_cap"]}]}
        v2 = AgentAdapter.v1_to_v2(v1)
        assert v2["agents"][0]["name"] == "custom_agent"

    def test_v1_to_v2_empty_agents(self):
        v2 = AgentAdapter.v1_to_v2({"agents": []})
        assert v2["agents"] == []

    def test_v1_to_v2_settings_migration(self):
        v1 = {
            "agents": [],
            "settings": {
                "default_max_parallel": 5,
                "task_timeout": 600,
                "retry_failed_tasks": False,
                "max_retries": 5,
                "compression_enabled": False,
                "compression_target_tokens": 8000,
                "context_preserve_sections": ["requirements"],
            },
        }
        v2 = AgentAdapter.v1_to_v2(v1)
        s = v2["settings"]
        assert s["default_max_parallel"] == 5
        assert s["task_timeout"] == 600
        assert s["retry_failed_tasks"] is False
        assert s["max_retries"] == 5
        assert s["capability_matching"]["strategy"] == "exact_or_broader"
        assert s["capability_matching"]["fallback_enabled"] is True

    def test_v1_to_v2_defaults(self):
        v1 = {"agents": [{"name": "implementation", "capabilities": ["code_generation"]}]}
        v2 = AgentAdapter.v1_to_v2(v1)
        agent = v2["agents"][0]
        cap = agent["capabilities"]["code_generation"]
        assert cap["context_limit"] == 8000
        assert cap["timeout"] == 300
        assert agent["constraints"]["max_concurrent"] == 1
        assert agent["constraints"]["parallel_safe"] is True
        assert agent["constraints"]["requires_isolation"] is False


class TestAgentAdapterLoadSave:
    def test_load_v1_file(self, tmp_path):
        v1 = {"agents": [{"name": "review", "capabilities": ["code_review"]}]}
        p = tmp_path / "agents.json"
        p.write_text(json.dumps(v1))
        result = AgentAdapter.load(p)
        assert result["version"] == "2.0"

    def test_load_v2_file(self, tmp_path):
        v2 = {"version": "2.0", "agents": [{"name": "reviewer", "capabilities": {"code_review": {}}}]}
        p = tmp_path / "agents.json"
        p.write_text(json.dumps(v2))
        result = AgentAdapter.load(p)
        assert result["version"] == "2.0"

    def test_save_config(self, tmp_path):
        config = {"version": "2.0", "agents": []}
        p = tmp_path / "output.json"
        AgentAdapter.save(config, p)
        loaded = json.loads(p.read_text())
        assert loaded == config

    def test_load_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            AgentAdapter.load(tmp_path / "nonexistent.json")


class TestAgentAdapterNameMappings:
    def test_all_mappings(self):
        assert AgentAdapter.NAME_MAPPINGS["review"] == "reviewer"
        assert AgentAdapter.NAME_MAPPINGS["testing"] == "tester"
        assert AgentAdapter.NAME_MAPPINGS["debugging"] == "debugger"
        assert AgentAdapter.NAME_MAPPINGS["architecture"] == "architect"
        assert AgentAdapter.NAME_MAPPINGS["documentation"] == "documentation"
        assert AgentAdapter.NAME_MAPPINGS["implementation"] == "implementation"


class TestSkillAdapterDetectVersion:
    def test_detect_v1(self):
        assert SkillAdapter.detect_version({"skills": []}) == "v1"

    def test_detect_v2(self):
        assert SkillAdapter.detect_version({"version": "2.0", "skills": []}) == "v2"


class TestSkillAdapterConversion:
    def test_v1_to_v2_basic(self):
        v1 = {
            "skills": [
                {
                    "name": "code-review",
                    "description": "Code review",
                    "triggers": ["review"],
                    "depends_on": [],
                }
            ],
            "settings": {"auto_trigger": True},
        }
        v2 = SkillAdapter.v1_to_v2(v1)
        assert v2["version"] == "2.0"
        assert len(v2["skills"]) == 1
        assert v2["skills"][0]["name"] == "code-review"
        assert v2["skills"][0]["category"] == "code-quality"
        assert v2["skills"][0]["phase"] == "review"
        assert v2["skills"][0]["requires_capability"] == "code_review"
        assert v2["skills"][0]["preferred_agent"] == "reviewer"

    def test_v1_to_v2_deprecated_skills(self):
        v1 = {
            "skills": [
                {"name": "requesting-code-review", "triggers": ["request"]},
                {"name": "receiving-code-review", "triggers": ["receive"]},
            ]
        }
        v2 = SkillAdapter.v1_to_v2(v1)
        assert len(v2["skills"]) == 0
        deprecated_names = [s["name"] for s in v2["deprecated"]["skills"]]
        assert "requesting-code-review" in deprecated_names
        assert "receiving-code-review" in deprecated_names

    def test_v1_to_v2_category_mapping(self):
        v1 = {
            "skills": [
                {"name": "brainstorming", "triggers": ["idea"]},
                {"name": "using-git-worktrees", "triggers": ["worktree"]},
                {"name": "notification", "triggers": ["notify"]},
                {"name": "database-export", "triggers": ["export"]},
                {"name": "skill-creator", "triggers": ["create"]},
                {"name": "workflow-executor", "triggers": ["workflow"]},
                {"name": "unknown-skill", "triggers": ["unknown"]},
            ]
        }
        v2 = SkillAdapter.v1_to_v2(v1)
        cats = {s["name"]: s["category"] for s in v2["skills"]}
        assert cats["brainstorming"] == "development-workflow"
        assert cats["using-git-worktrees"] == "version-control"
        assert cats["notification"] == "integration"
        assert cats["database-export"] == "data"
        assert cats["skill-creator"] == "skill-management"
        assert cats["workflow-executor"] == "workflow-control"
        assert cats["unknown-skill"] == "other"

    def test_v1_to_v2_capability_mapping(self):
        v1 = {
            "skills": [
                {"name": "writing-plans", "triggers": ["plan"]},
                {"name": "test-driven-development", "triggers": ["tdd"]},
                {"name": "systematic-debugging", "triggers": ["debug"]},
            ]
        }
        v2 = SkillAdapter.v1_to_v2(v1)
        caps = {s["name"]: s["requires_capability"] for s in v2["skills"]}
        assert caps["writing-plans"] == "system_design"
        assert caps["test-driven-development"] == ["test_generation", "test_execution"]
        assert caps["systematic-debugging"] == ["error_analysis", "log_analysis"]

    def test_v1_to_v2_phase_mapping(self):
        v1 = {
            "skills": [
                {"name": "brainstorming", "triggers": []},
                {"name": "writing-plans", "triggers": []},
                {"name": "test-driven-development", "triggers": []},
                {"name": "systematic-debugging", "triggers": []},
                {"name": "subagent-driven-development", "triggers": []},
                {"name": "verification-before-completion", "triggers": []},
            ]
        }
        v2 = SkillAdapter.v1_to_v2(v1)
        phases = {s["name"]: s["phase"] for s in v2["skills"]}
        assert phases["brainstorming"] == "requirements"
        assert phases["writing-plans"] == "design"
        assert phases["test-driven-development"] == "testing"
        assert phases["systematic-debugging"] == "debugging"
        assert phases["subagent-driven-development"] == "implementation"
        assert phases["verification-before-completion"] == "testing"

    def test_v1_to_v2_no_settings(self):
        v2 = SkillAdapter.v1_to_v2({"skills": []})
        assert v2["settings"] == {}


class TestSkillAdapterLoadSave:
    def test_load_v1_file(self, tmp_path):
        v1 = {"skills": [{"name": "brainstorming", "triggers": ["idea"]}]}
        p = tmp_path / "skills.json"
        p.write_text(json.dumps(v1))
        result = SkillAdapter.load(p)
        assert result["version"] == "2.0"

    def test_load_v2_file(self, tmp_path):
        v2 = {"version": "2.0", "skills": [{"name": "brainstorming"}]}
        p = tmp_path / "skills.json"
        p.write_text(json.dumps(v2))
        result = SkillAdapter.load(p)
        assert result["version"] == "2.0"

    def test_save_config(self, tmp_path):
        config = {"version": "2.0", "skills": []}
        p = tmp_path / "output.json"
        SkillAdapter.save(config, p)
        loaded = json.loads(p.read_text())
        assert loaded == config


class TestCapabilityMatcherExtended:
    @pytest.fixture
    def agents_config(self):
        return {
            "version": "2.0",
            "agents": [
                {
                    "name": "reviewer",
                    "capabilities": {
                        "code_review": {},
                        "design_review": {},
                        "security_check": {},
                    },
                },
                {
                    "name": "tester",
                    "capabilities": {
                        "test_generation": {},
                        "test_execution": {},
                        "coverage_analysis": {},
                    },
                },
                {
                    "name": "debugger",
                    "capabilities": {
                        "error_analysis": {},
                        "root_cause": {},
                    },
                },
            ],
        }

    def test_empty_agents_config(self):
        matcher = CapabilityMatcher({"agents": []})
        assert matcher.find_agents_for_capability("code_review") == []

    def test_find_nonexistent_capability(self, agents_config):
        matcher = CapabilityMatcher(agents_config)
        assert matcher.find_agents_for_capability("nonexistent") == []

    def test_find_multiple_caps_intersection(self, agents_config):
        matcher = CapabilityMatcher(agents_config)
        result = matcher.find_agents_for_capability(["code_review", "design_review"])
        assert len(result) == 1
        assert result[0]["name"] == "reviewer"

    def test_find_multiple_caps_no_intersection(self, agents_config):
        matcher = CapabilityMatcher(agents_config)
        result = matcher.find_agents_for_capability(["code_review", "test_generation"])
        assert len(result) == 0

    def test_find_empty_list_capability(self, agents_config):
        matcher = CapabilityMatcher(agents_config)
        result = matcher.find_agents_for_capability([])
        assert result == []

    def test_match_skill_no_capability_no_preferred(self, agents_config):
        matcher = CapabilityMatcher(agents_config)
        assert matcher.match_skill_to_agent({"name": "unknown"}) is None

    def test_match_skill_with_requires_capability(self, agents_config):
        matcher = CapabilityMatcher(agents_config)
        result = matcher.match_skill_to_agent(
            {
                "name": "test-skill",
                "requires_capability": "error_analysis",
            }
        )
        assert result is not None
        assert result["name"] == "debugger"

    def test_match_skill_preferred_agent_overrides(self, agents_config):
        matcher = CapabilityMatcher(agents_config)
        result = matcher.match_skill_to_agent(
            {
                "name": "test-skill",
                "preferred_agent": "tester",
                "requires_capability": "code_review",
            }
        )
        assert result["name"] == "tester"

    def test_match_skill_unresolvable_capability(self, agents_config):
        matcher = CapabilityMatcher(agents_config)
        assert (
            matcher.match_skill_to_agent(
                {
                    "name": "test-skill",
                    "requires_capability": "nonexistent",
                }
            )
            is None
        )


class TestConvenienceFunctions:
    def test_load_agents_prefers_v2(self):
        result = load_agents("agents/agents.json")
        assert result["version"] == "2.0"

    def test_load_agents_v2_direct(self):
        result = load_agents("agents/agents.v2.json")
        assert result["version"] == "2.0"

    def test_load_agents_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            load_agents("nonexistent/agents.json")

    def test_load_skills_prefers_v2(self):
        result = load_skills("skills/skills.json")
        assert result["version"] == "2.0"

    def test_load_skills_v2_direct(self):
        result = load_skills("skills/skills.v2.json")
        assert result["version"] == "2.0"

    def test_load_skills_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            load_skills("nonexistent/skills.json")

    def test_create_matcher(self):
        agents = load_agents("agents/agents.v2.json")
        matcher = create_matcher(agents)
        assert isinstance(matcher, CapabilityMatcher)

    def test_roundtrip_v1_to_load(self, tmp_path):
        v1 = {"agents": [{"name": "review", "capabilities": ["code_review"]}]}
        p = tmp_path / "agents.json"
        p.write_text(json.dumps(v1))
        result = AgentAdapter.load(p)
        assert result["version"] == "2.0"
        assert result["agents"][0]["name"] == "reviewer"
