"""Tests for LayeredSkillLoader

Tests the three-layer architecture skill loading system.
"""

import asyncio
import os
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import yaml

from lingflow.core.layered_skill_loader import (
    LayeredSkillLoader,
    SkillConfig,
    SkillLayer,
    get_layered_loader,
    load_skill,
    unload_skill,
    mark_task_complete,
    get_layer_stats,
    get_memory_usage,
)


class TestSkillConfig(unittest.TestCase):
    """Tests for SkillConfig"""

    def test_skill_config_creation(self):
        """Test creating a skill configuration"""
        config = SkillConfig(
            name="test-skill",
            layer=SkillLayer.L3,
            category="test",
            description="Test skill",
            triggers=["test", "mock"],
        )

        self.assertEqual(config.name, "test-skill")
        self.assertEqual(config.layer, SkillLayer.L3)
        self.assertFalse(config.loaded)
        self.assertEqual(config.use_count, 0)


class TestSkillRouter(unittest.TestCase):
    """Tests for SkillRouter"""

    def setUp(self):
        """Create a temporary config file"""
        self.config_fd, self.config_path = tempfile.mkstemp(suffix=".yaml")

        config = {
            "routing": {
                "priority_rules": [
                    {"pattern": "workflow", "route": "L1.workflow-executor", "priority": 10},
                    {"pattern": "review", "route": "L2.code-review", "priority": 9},
                    {"pattern": "api.*doc", "route": "L3.api-doc-generator", "priority": 7},
                ],
                "mutex_constraints": {
                    "code_quality": ["L2-code-review", "L2-code-refactor"],
                },
                "dependency_chains": [
                    ["brainstorming", "systematic-debugging", "verification-before-completion"],
                ],
            },
        }

        with os.fdopen(self.config_fd, "w") as f:
            yaml.dump(config, f)

    def tearDown(self):
        """Clean up temp file"""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_router_initialization(self):
        """Test router initialization"""
        from lingflow.core.layered_skill_loader import SkillRouter

        router = SkillRouter(self.config_path)

        self.assertEqual(len(router.routing_rules), 3)
        self.assertIn("code_quality", router.mutex_groups)

    def test_route_matching(self):
        """Test skill routing"""
        from lingflow.core.layered_skill_loader import SkillRouter

        router = SkillRouter(self.config_path)

        # Test direct pattern match
        result = router.route("run workflow", set())
        self.assertIsNotNone(result)
        self.assertIn("workflow", result.lower())

        # Test priority routing
        result = router.route("code review", set())
        self.assertIsNotNone(result)
        self.assertIn("review", result.lower())

    def test_mutex_constraints(self):
        """Test mutex constraint checking"""
        from lingflow.core.layered_skill_loader import SkillRouter

        router = SkillRouter(self.config_path)

        # Should allow when no conflict
        result = router.route("code review", set())
        self.assertIsNotNone(result)

        # Should block when mutex group has active skill
        # Note: active skills should use the same naming format as the route returns
        result = router.route("code review", {"L2-code-refactor"})
        self.assertIsNone(result)


class TestLayeredSkillLoader(unittest.TestCase):
    """Tests for LayeredSkillLoader"""

    def setUp(self):
        """Create a temporary config file"""
        self.config_fd, self.config_path = tempfile.mkstemp(suffix=".yaml")

        config = {
            "L1": {
                "description": "Core layer",
                "loading_strategy": "eager",
                "unloading_strategy": "never",
                "memory_priority": "critical",
                "skills": [
                    {"name": "workflow-executor", "triggers": ["workflow"], "timeout": 600},
                    {"name": "task-runner", "triggers": ["run", "execute"], "timeout": 300},
                ],
            },
            "L2": {
                "description": "Professional layer",
                "loading_strategy": "eager",
                "unloading_strategy": "never",
                "memory_priority": "high",
                "groups": {
                    "code_quality": {
                        "type": "mutex",
                        "skills": [
                            {"name": "code-review", "triggers": ["review"], "priority": 10},
                        ],
                    },
                },
            },
            "L3": {
                "description": "Extended layer",
                "loading_strategy": "lazy",
                "unloading_strategy": "after_task",
                "memory_priority": "normal",
                "categories": {
                    "design": {
                        "trigger_keywords": ["api", "ui", "design"],
                        "skills": [
                            {"name": "api-doc-generator", "triggers": ["api doc"]},
                            {"name": "ui-mockup-generator", "triggers": ["ui mockup"]},
                        ],
                    },
                },
            },
            "routing": {
                "priority_rules": [
                    {"pattern": "workflow", "route": "L1.workflow-executor", "priority": 10},
                    {"pattern": "api.*doc", "route": "L3.api-doc-generator", "priority": 7},
                ],
                "mutex_constraints": {},
                "dependency_chains": [],
            },
        }

        with os.fdopen(self.config_fd, "w") as f:
            yaml.dump(config, f)

    def tearDown(self):
        """Clean up temp file"""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def test_loader_initialization(self):
        """Test loader initialization"""
        loader = LayeredSkillLoader(self.config_path)

        # Check that L1 and L2 skills are registered
        self.assertIn("workflow-executor", loader.skills)
        self.assertIn("task-runner", loader.skills)
        self.assertIn("code-review", loader.skills)

        # Check L3 skills
        self.assertIn("api-doc-generator", loader.skills)
        self.assertIn("ui-mockup-generator", loader.skills)

    def test_layer_assignment(self):
        """Test skill layer assignment"""
        loader = LayeredSkillLoader(self.config_path)

        # L1 skills
        self.assertEqual(loader.skills["workflow-executor"].layer, SkillLayer.L1)
        self.assertEqual(loader.skills["task-runner"].layer, SkillLayer.L1)

        # L2 skills
        self.assertEqual(loader.skills["code-review"].layer, SkillLayer.L2)

        # L3 skills
        self.assertEqual(loader.skills["api-doc-generator"].layer, SkillLayer.L3)
        self.assertEqual(loader.skills["ui-mockup-generator"].layer, SkillLayer.L3)

    def test_get_layer_stats(self):
        """Test getting layer statistics"""
        loader = LayeredSkillLoader(self.config_path)
        stats = loader.get_layer_stats()

        self.assertIn("L1", stats)
        self.assertIn("L2", stats)
        self.assertIn("L3", stats)

        # Check structure
        self.assertIn("total", stats["L1"])
        self.assertIn("loaded", stats["L1"])
        self.assertIn("active", stats["L1"])

    def test_get_memory_usage(self):
        """Test getting memory usage"""
        loader = LayeredSkillLoader(self.config_path)
        usage = loader.get_memory_usage()

        self.assertIn("total_cached", usage)
        self.assertIn("l1_loaded", usage)
        self.assertIn("l2_loaded", usage)
        self.assertIn("l3_loaded", usage)
        self.assertIn("l3_active", usage)
        self.assertIn("target_l3_max", usage)

    def test_l3_unload_allowed(self):
        """Test that L3 skills can be unloaded"""
        loader = LayeredSkillLoader(self.config_path)

        # Mock successful load
        with patch.object(loader, "_load_skill", return_value=True):
            loader.load_skill("api-doc-generator")
            loader.skills["api-doc-generator"].loaded = True
            loader._active_l3_skills.add("api-doc-generator")

            # Unload should succeed
            result = loader.unload_skill("api-doc-generator")
            self.assertTrue(result)
            self.assertNotIn("api-doc-generator", loader._active_l3_skills)

    def test_l2_unload_not_allowed(self):
        """Test that L2 skills cannot be unloaded"""
        loader = LayeredSkillLoader(self.config_path)

        # Mock load
        with patch.object(loader, "_load_skill", return_value=True):
            loader.load_skill("code-review")
            loader.skills["code-review"].loaded = True

            # Unload should fail for L2
            result = loader.unload_skill("code-review")
            self.assertFalse(result)
            # Should still be loaded
            self.assertTrue(loader.skills["code-review"].loaded)

    def test_mark_task_complete(self):
        """Test marking task as complete"""
        loader = LayeredSkillLoader(self.config_path)

        # Mock load L3 skill
        with patch.object(loader, "_load_skill", return_value=True):
            loader.load_skill("api-doc-generator")
            loader.skills["api-doc-generator"].loaded = True
            loader._active_l3_skills.add("api-doc-generator")

            # Mark complete
            loader.mark_task_complete("api-doc-generator")

            # Should be unloaded
            self.assertNotIn("api-doc-generator", loader._active_l3_skills)

    def test_unload_idle_skills(self):
        """Test unloading idle L3 skills"""
        loader = LayeredSkillLoader(self.config_path)

        # Mock load L3 skills with different last_used times
        with patch.object(loader, "_load_skill", return_value=True):
            for skill_name in ["api-doc-generator", "ui-mockup-generator"]:
                loader.load_skill(skill_name)
                loader.skills[skill_name].loaded = True
                loader._active_l3_skills.add(skill_name)
                # Set initial last_used for both
                loader.skills[skill_name].last_used = time.time() - 200  # 200 seconds ago

            # Make one skill more idle (400 seconds ago)
            loader.skills["api-doc-generator"].last_used = time.time() - 400
            # Keep the other recent (50 seconds ago)
            loader.skills["ui-mockup-generator"].last_used = time.time() - 50

            # Unload idle skills with 300s timeout
            unloaded = loader.unload_idle_l3_skills(idle_timeout=300)

            self.assertEqual(unloaded, 1)
            self.assertNotIn("api-doc-generator", loader._active_l3_skills)
            self.assertIn("ui-mockup-generator", loader._active_l3_skills)


class TestGlobalFunctions(unittest.TestCase):
    """Tests for global convenience functions"""

    def test_get_layered_loader_singleton(self):
        """Test that get_layered_loader returns a singleton"""
        loader1 = get_layered_loader()
        loader2 = get_layered_loader()

        self.assertIs(loader1, loader2)

    def test_get_layer_stats(self):
        """Test get_layer_stats function"""
        stats = get_layer_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn("L1", stats)
        self.assertIn("L2", stats)
        self.assertIn("L3", stats)

    def test_get_memory_usage(self):
        """Test get_memory_usage function"""
        usage = get_memory_usage()

        self.assertIsInstance(usage, dict)
        self.assertIn("l1_loaded", usage)
        self.assertIn("l2_loaded", usage)
        self.assertIn("l3_loaded", usage)


if __name__ == "__main__":
    unittest.main()
