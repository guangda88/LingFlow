"""Tests for lingflow.coordination.registry module"""

import pytest

from lingflow.coordination.registry import AgentRegistry
from lingflow.coordination.agent import Agent
from lingflow.common.models import AgentConfig, Task, TaskPriority


class TestAgentRegistry:
    """Test AgentRegistry class"""

    def test_init(self):
        """Test initialization"""
        registry = AgentRegistry()
        assert registry.agents == {}
        assert isinstance(registry.agents, dict)

    def test_register_agent(self):
        """Test registering an agent"""
        registry = AgentRegistry()
        config = AgentConfig(
            name="test_agent",
            description="Test agent",
            capabilities=["test", "demo"]
        )
        agent = Agent(config)

        registry.register_agent(agent)

        assert "test_agent" in registry.agents
        assert registry.agents["test_agent"] == agent

    def test_register_multiple_agents(self):
        """Test registering multiple agents"""
        registry = AgentRegistry()

        for i in range(5):
            config = AgentConfig(
                name=f"agent_{i}",
                description=f"Agent {i}",
                capabilities=[f"cap{i}"]
            )
            agent = Agent(config)
            registry.register_agent(agent)

        assert len(registry.agents) == 5

    def test_register_agent_overwrite(self):
        """Test that registering with same name overwrites"""
        registry = AgentRegistry()

        config1 = AgentConfig(
            name="agent",
            description="First",
            capabilities=["first"]
        )
        agent1 = Agent(config1)
        registry.register_agent(agent1)

        config2 = AgentConfig(
            name="agent",
            description="Second",
            capabilities=["second"]
        )
        agent2 = Agent(config2)
        registry.register_agent(agent2)

        assert len(registry.agents) == 1
        assert registry.agents["agent"] == agent2
        assert registry.agents["agent"].config.description == "Second"

    def test_get_agent_exists(self):
        """Test getting existing agent"""
        registry = AgentRegistry()
        config = AgentConfig(
            name="test_agent",
            description="Test",
            capabilities=["test"]
        )
        agent = Agent(config)
        registry.register_agent(agent)

        retrieved = registry.get_agent("test_agent")

        assert retrieved is not None
        assert retrieved == agent

    def test_get_agent_not_exists(self):
        """Test getting non-existent agent"""
        registry = AgentRegistry()

        retrieved = registry.get_agent("nonexistent")

        assert retrieved is None

    def test_list_agents_empty(self):
        """Test listing agents when registry is empty"""
        registry = AgentRegistry()
        agents = registry.list_agents()

        assert agents == []

    def test_list_agents_with_agents(self):
        """Test listing agents with registered agents"""
        registry = AgentRegistry()

        registry.register_agent(Agent(AgentConfig(
            name="agent1",
            description="Agent 1",
            capabilities=["a1"]
        )))
        registry.register_agent(Agent(AgentConfig(
            name="agent2",
            description="Agent 2",
            capabilities=["a2"]
        )))

        agents = registry.list_agents()

        assert len(agents) == 2
        assert all(isinstance(a, dict) for a in agents)

        # Check agent info structure
        assert "name" in agents[0]
        assert "description" in agents[0]
        assert "capabilities" in agents[0]
        assert "status" in agents[0]

    def test_find_agents_for_task_with_agent_type(self):
        """Test finding agents for task with specific agent_type"""
        registry = AgentRegistry()

        config = AgentConfig(
            name="python_expert",
            description="Python expert",
            capabilities=["python"]
        )
        registry.register_agent(Agent(config))

        task = Task(
            task_id="test",
            name="Test",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type="python_expert"
        )
        agents = registry.find_agents_for_task(task)

        assert len(agents) == 1
        assert agents[0].config.name == "python_expert"

    def test_find_agents_for_task_without_agent_type(self):
        """Test finding agents for task without agent_type"""
        registry = AgentRegistry()

        registry.register_agent(Agent(AgentConfig(
            name="agent1",
            description="A1",
            capabilities=["general"]
        )))
        registry.register_agent(Agent(AgentConfig(
            name="agent2",
            description="A2",
            capabilities=["general"]
        )))

        task = Task(
            task_id="test",
            name="Generic",
            description="Generic task",
            priority=TaskPriority.NORMAL,
            agent_type=""
        )
        agents = registry.find_agents_for_task(task)

        # Should return all agents that can execute (all in this case)
        assert len(agents) >= 2

    def test_find_agents_for_task_nonexistent_agent_type(self):
        """Test finding agents for task with non-existent agent_type"""
        registry = AgentRegistry()

        registry.register_agent(Agent(AgentConfig(
            name="agent1",
            description="A1",
            capabilities=["a1"]
        )))

        task = Task(
            task_id="test",
            name="Test",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type="nonexistent"
        )
        agents = registry.find_agents_for_task(task)

        # Should return empty list since no agent matches
        assert agents == []

    def test_list_agents_info_completeness(self):
        """Test that list_agents returns complete info"""
        registry = AgentRegistry()

        config = AgentConfig(
            name="complete_agent",
            description="Complete",
            capabilities=["cap1", "cap2"]
        )
        agent = Agent(config)
        registry.register_agent(agent)

        agents = registry.list_agents()
        agent_info = agents[0]

        assert agent_info["name"] == "complete_agent"
        assert agent_info["description"] == "Complete"
        assert agent_info["capabilities"] == ["cap1", "cap2"]
        assert "status" in agent_info
        assert "tasks_completed" in agent_info
        assert "tasks_failed" in agent_info


class TestAgentRegistryIntegration:
    """Test AgentRegistry integration with other components"""

    def test_registry_with_different_agent_types(self):
        """Test registry with various agent types"""
        registry = AgentRegistry()

        agent_types = [
            ("implementation", "Code implementation agent", ["code", "impl"]),
            ("review", "Code review agent", ["review", "audit"]),
            ("testing", "Testing agent", ["test", "verify"]),
            ("documentation", "Documentation agent", ["doc", "write"]),
        ]

        for name, desc, caps in agent_types:
            config = AgentConfig(
                name=name,
                description=desc,
                capabilities=caps
            )
            agent = Agent(config)
            registry.register_agent(agent)

        assert len(registry.agents) == len(agent_types)

        # Verify all can be retrieved
        for name, _, _ in agent_types:
            agent = registry.get_agent(name)
            assert agent is not None
            assert agent.config.name == name

    def test_registry_task_matching(self):
        """Test task-agent matching through registry"""
        registry = AgentRegistry()

        # Register specialized agents
        python_config = AgentConfig(
            name="python_agent",
            description="Python expert",
            capabilities=["python", "django", "flask"]
        )
        registry.register_agent(Agent(python_config))

        js_config = AgentConfig(
            name="js_agent",
            description="JavaScript expert",
            capabilities=["javascript", "react", "vue"]
        )
        registry.register_agent(Agent(js_config))

        # Task with specific agent type
        task = Task(
            task_id="test",
            name="Test",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type="python_agent"
        )
        agents = registry.find_agents_for_task(task)

        assert len(agents) == 1
        assert agents[0].config.name == "python_agent"

        # Generic task - should match capable agents
        generic_task = Task(
            task_id="generic",
            name="Generic",
            description="Need help",
            priority=TaskPriority.NORMAL,
            agent_type=""
        )
        capable_agents = registry.find_agents_for_task(generic_task)

        # Should return at least the python agent
        assert len(capable_agents) > 0
