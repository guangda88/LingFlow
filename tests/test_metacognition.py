"""Tests for Metacognition System (Knowledge Boundary Awareness)

Tests the ability of AI agents to:
1. Declare their knowledge boundaries
2. Recognize capability gaps before starting tasks
3. Plan evolution paths to learn new capabilities
4. Track learning progress
"""

from datetime import datetime

import pytest

from lingflow.trust.metacognition import (
    Capability,
    CapabilityLevel,
    EvolutionPath,
    MetacognitiveAgent,
    TaskRequirements,
    get_metacognitive_agent,
)


@pytest.fixture
def agent():
    """Create a fresh metacognitive agent for each test"""
    return MetacognitiveAgent()


class TestCapabilityLevel:
    """Test capability level enumeration"""

    def test_level_values(self):
        """Test capability levels have correct values"""
        assert CapabilityLevel.UNKNOWN.value == 0
        assert CapabilityLevel.FAMILIAR.value == 1
        assert CapabilityLevel.PARTIAL.value == 2
        assert CapabilityLevel.MASTERED.value == 3

    def test_can_handle_simple_task(self):
        """Test FAMILIAR can handle simple tasks"""
        assert CapabilityLevel.FAMILIAR.can_handle("simple")
        assert not CapabilityLevel.FAMILIAR.can_handle("medium")
        assert not CapabilityLevel.FAMILIAR.can_handle("complex")

    def test_can_handle_medium_task(self):
        """Test PARTIAL can handle medium tasks"""
        assert CapabilityLevel.PARTIAL.can_handle("simple")
        assert CapabilityLevel.PARTIAL.can_handle("medium")
        assert not CapabilityLevel.PARTIAL.can_handle("complex")

    def test_can_handle_complex_task(self):
        """Test MASTERED can handle all tasks"""
        assert CapabilityLevel.MASTERED.can_handle("simple")
        assert CapabilityLevel.MASTERED.can_handle("medium")
        assert CapabilityLevel.MASTERED.can_handle("complex")


class TestCapability:
    """Test capability dataclass"""

    def test_create_capability(self):
        """Test creating a capability"""
        capability = Capability(
            name="Python", category="programming", level=CapabilityLevel.MASTERED, notes="Experienced Python developer"
        )
        assert capability.name == "Python"
        assert capability.category == "programming"
        assert capability.level == CapabilityLevel.MASTERED
        assert capability.notes == "Experienced Python developer"

    def test_can_handle_task(self):
        """Test capability task handling"""
        capability = Capability(name="Python", category="programming", level=CapabilityLevel.PARTIAL)
        assert capability.can_handle_task("simple")
        assert capability.can_handle_task("medium")
        assert not capability.can_handle_task("complex")

    def test_needs_evolution(self):
        """Test evolution need detection"""
        capability = Capability(name="Python", category="programming", level=CapabilityLevel.PARTIAL)
        assert not capability.needs_evolution("medium")
        assert capability.needs_evolution("complex")


class TestMetacognitiveAgent:
    """Test metacognitive agent"""

    def test_declare_capability(self, agent):
        """Test declaring a capability"""
        agent.declare_capability(
            name="Python", category="programming", level=CapabilityLevel.MASTERED, notes="Extensive experience"
        )

        capability = agent.get_capability("Python")
        assert capability is not None
        assert capability.name == "Python"
        assert capability.level == CapabilityLevel.MASTERED
        assert capability.notes == "Extensive experience"

    def test_declare_capability_with_evolution_steps(self, agent):
        """Test declaring capability with evolution path"""
        agent.declare_capability(
            name="Python",
            category="programming",
            level=CapabilityLevel.PARTIAL,
            evolution_steps=["Read PEP 8", "Build 5 projects", "Contribute to open source"],
        )

        capability = agent.get_capability("Python")
        assert len(capability.evolution_paths) == 1
        assert capability.evolution_paths[0].target_level == CapabilityLevel.MASTERED

    def test_analyze_task_requirements_no_gaps(self, agent):
        """Test task analysis with no capability gaps"""
        agent.declare_capability("Python", "programming", CapabilityLevel.MASTERED)
        agent.declare_capability("pytest", "testing", CapabilityLevel.MASTERED)

        requirements = agent.analyze_task_requirements(
            task_id="test-1",
            task_description="Write Python tests using pytest",
            required_capabilities=["Python", "pytest"],
            complexity="medium",
        )

        assert len(requirements.gaps) == 0
        assert requirements.complexity == "medium"

    def test_analyze_task_requirements_with_gaps(self, agent):
        """Test task analysis with capability gaps"""
        agent.declare_capability("Python", "programming", CapabilityLevel.MASTERED)
        # PostgreSQL not declared

        requirements = agent.analyze_task_requirements(
            task_id="test-2",
            task_description="Migrate database to PostgreSQL",
            required_capabilities=["Python", "PostgreSQL"],
            complexity="complex",
        )

        assert len(requirements.gaps) == 1
        assert "PostgreSQL" in requirements.gaps[0]
        assert len(requirements.recommendations) > 0
        assert len(requirements.alternative_approaches) > 0

    def test_analyze_task_requirements_insufficient_level(self, agent):
        """Test task analysis with insufficient capability level"""
        agent.declare_capability("Python", "programming", CapabilityLevel.FAMILIAR)

        requirements = agent.analyze_task_requirements(
            task_id="test-3",
            task_description="Build complex Python application",
            required_capabilities=["Python"],
            complexity="complex",
        )

        assert len(requirements.gaps) == 1
        assert "insufficient" in requirements.gaps[0].lower()

    def test_propose_evolution(self, agent):
        """Test proposing evolution path"""
        agent.declare_capability("Python", "programming", CapabilityLevel.FAMILIAR)

        evolution_path = agent.propose_evolution(
            capability_name="Python",
            target_level=CapabilityLevel.MASTERED,
            steps=["Read 'Fluent Python' book", "Build 10 production projects", "Review 50 pull requests"],
        )

        assert evolution_path.source_level == CapabilityLevel.FAMILIAR
        assert evolution_path.target_level == CapabilityLevel.MASTERED
        assert len(evolution_path.steps) == 3
        assert evolution_path.status == "planned"

    def test_start_evolution(self, agent):
        """Test starting evolution"""
        agent.declare_capability("Python", "programming", CapabilityLevel.FAMILIAR)
        agent.propose_evolution(capability_name="Python", target_level=CapabilityLevel.MASTERED, steps=["Step 1", "Step 2"])

        started = agent.start_evolution("Python")
        assert started is True

        capability = agent.get_capability("Python")
        assert capability.evolution_paths[0].status == "in_progress"

    def test_complete_evolution(self, agent):
        """Test completing evolution"""
        agent.declare_capability("Python", "programming", CapabilityLevel.FAMILIAR)
        agent.propose_evolution(capability_name="Python", target_level=CapabilityLevel.MASTERED, steps=["Step 1", "Step 2"])

        completed = agent.complete_evolution("Python", CapabilityLevel.MASTERED)
        assert completed is True

        capability = agent.get_capability("Python")
        assert capability.level == CapabilityLevel.MASTERED
        assert capability.evolution_paths[0].status == "completed"
        assert len(agent.learning_history) == 1

    def test_can_declare_completion_with_all_capabilities(self, agent):
        """Test completion declaration with sufficient capabilities"""
        agent.declare_capability("Python", "programming", CapabilityLevel.MASTERED)

        requirements = agent.analyze_task_requirements(
            task_id="test-4", task_description="Write Python code", required_capabilities=["Python"], complexity="medium"
        )

        can_complete, reason = agent.can_declare_completion(requirements)
        assert can_complete is True
        assert "All required capabilities available" in reason

    def test_can_declare_completion_with_gaps(self, agent):
        """Test completion declaration with capability gaps"""
        # No capabilities declared

        requirements = agent.analyze_task_requirements(
            task_id="test-5", task_description="Use TensorFlow", required_capabilities=["TensorFlow"], complexity="complex"
        )

        can_complete, reason = agent.can_declare_completion(requirements)
        assert can_complete is False
        assert "capability gaps" in reason.lower()

    def test_get_knowledge_boundaries_report(self, agent):
        """Test generating knowledge boundaries report"""
        agent.declare_capability("Python", "programming", CapabilityLevel.MASTERED)
        agent.declare_capability("pytest", "testing", CapabilityLevel.PARTIAL)
        agent.declare_capability("Kubernetes", "devops", CapabilityLevel.FAMILIAR)

        report = agent.get_knowledge_boundaries_report()

        assert len(report["mastered"]) == 1
        assert report["mastered"][0]["name"] == "Python"
        assert len(report["partial"]) == 1
        assert report["partial"][0]["name"] == "pytest"
        assert len(report["familiar"]) == 1
        assert report["familiar"][0]["name"] == "Kubernetes"
        assert "unknown" in report


class TestKnowledgeBoundaryScenario:
    """Test realistic knowledge boundary scenarios"""

    def test_postgresql_migration_scenario(self):
        """Test PostgreSQL migration scenario (LingYi problem)"""
        agent = MetacognitiveAgent()

        # Declare what AI knows
        agent.declare_capability("Python", "programming", CapabilityLevel.MASTERED, notes="Extensive experience with Python")
        agent.declare_capability(
            "SQL", "database", CapabilityLevel.PARTIAL, notes="Basic SQL queries, but not database-specific features"
        )

        # Analyze migration task
        requirements = agent.analyze_task_requirements(
            task_id="migrate-to-postgresql",
            task_description="Migrate application to PostgreSQL",
            required_capabilities=["Python", "SQL", "PostgreSQL"],
            complexity="complex",
        )

        # Should detect PostgreSQL is unknown and SQL is insufficient
        assert len(requirements.gaps) == 2
        assert any("PostgreSQL" in gap for gap in requirements.gaps)

        # Cannot declare completion
        can_complete, reason = agent.can_declare_completion(requirements)
        assert can_complete is False

        # Propose evolution
        agent.propose_evolution(
            capability_name="PostgreSQL",
            target_level=CapabilityLevel.PARTIAL,
            steps=["Read PostgreSQL documentation", "Set up local PostgreSQL instance", "Practice with sample data"],
        )

        # Check evolution queue
        assert len(agent.evolution_queue) == 1

    def test_energy_pct_data_hallucination_scenario(self):
        """Test energy_pct data hallucination scenario"""
        agent = MetacognitiveAgent()

        # AI claims to add energy_pct field
        agent.declare_capability("Python", "programming", CapabilityLevel.MASTERED)

        # Analyze requirements for adding field with update logic
        requirements = agent.analyze_task_requirements(
            task_id="add-energy-pct",
            task_description="Add energy_pct field to database and UI with update logic",
            required_capabilities=["Python", "Database Schema Design", "Data Flow Management"],
            complexity="medium",
        )

        # Should detect missing data flow capability
        assert len(requirements.gaps) > 0

        # AI must acknowledge what it doesn't know
        can_complete, reason = agent.can_declare_completion(requirements)
        assert can_complete is False

        # Verify recommendations include learning data flow
        assert any("data" in rec.lower() for rec in requirements.recommendations)


class TestSingleton:
    """Test singleton metacognitive agent"""

    def test_get_metacognitive_agent(self):
        """Test singleton pattern"""
        agent1 = get_metacognitive_agent()
        agent2 = get_metacognitive_agent()

        assert agent1 is agent2

    def test_singleton_persistence(self):
        """Test data persistence across singleton calls"""
        agent = get_metacognitive_agent()
        agent.declare_capability("Test", "test", CapabilityLevel.MASTERED)

        agent2 = get_metacognitive_agent()
        capability = agent2.get_capability("Test")

        assert capability is not None
        assert capability.level == CapabilityLevel.MASTERED
