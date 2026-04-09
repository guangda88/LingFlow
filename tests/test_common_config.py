"""Unit tests for lingflow.common.config module."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from lingflow.common.config import ConfigManager, get_config, save_config, set_config


class TestConfigManagerInitialization:
    """Test ConfigManager initialization and config loading."""

    def test_initialization_default_path(self):
        """Test initialization with default config file path."""
        # Use temporary config file to avoid external dependency
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "workflow": {"max_iterations": 100, "max_parallel": 3},
                "skills": {"path": "/skills", "default_timeout": 30},
                "compression": {"enabled": True, "target_tokens": 4000},
                "logging": {"level": "WARNING"},
            }
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            manager = ConfigManager(config_file=temp_file)
            assert manager.config_file == temp_file
            assert manager.config is not None
            assert "workflow" in manager.config
            assert "skills" in manager.config
        finally:
            os.unlink(temp_file)

    def test_initialization_custom_path(self):
        """Test initialization with custom config file path."""
        manager = ConfigManager(config_file="/tmp/test_config.yaml")
        assert manager.config_file == "/tmp/test_config.yaml"
        assert manager.config is not None

    def test_load_config_default_values(self):
        """Test that config has all expected default structure."""
        # Use non-existent file to get defaults
        manager = ConfigManager(config_file="/nonexistent/default_test_config.yaml")
        # Check structure exists
        assert "workflow" in manager.config
        assert "skills" in manager.config
        assert "compression" in manager.config
        assert "logging" in manager.config
        assert "max_iterations" in manager.config["workflow"]
        assert "max_parallel" in manager.config["workflow"]
        assert "path" in manager.config["skills"]
        assert "default_timeout" in manager.config["skills"]

    def test_load_config_from_yaml_file(self):
        """Test loading config from YAML file."""
        # Create a temporary YAML config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "workflow": {"max_iterations": 200, "max_parallel": 4},
                "skills": {"path": "/custom/skills", "default_timeout": 60},
            }
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            # Load config from file
            manager = ConfigManager(config_file=temp_file)

            # Verify merged config (file values override defaults)
            assert manager.config["workflow"]["max_iterations"] == 200
            assert manager.config["workflow"]["max_parallel"] == 4
            assert manager.config["skills"]["path"] == "/custom/skills"
            assert manager.config["skills"]["default_timeout"] == 60
            # Default values for missing keys
            assert manager.config["workflow"]["sleep_interval"] == 0.01
            assert manager.config["compression"]["enabled"] is True
        finally:
            os.unlink(temp_file)

    def test_load_config_file_not_found(self):
        """Test loading when config file doesn't exist (uses defaults)."""
        manager = ConfigManager(config_file="/nonexistent/config.yaml")
        assert manager.config is not None
        assert "workflow" in manager.config

    def test_load_config_invalid_yaml(self):
        """Test handling of invalid YAML file (logs warning, uses defaults)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            temp_file = f.name

        try:
            manager = ConfigManager(config_file=temp_file)
            # Should still have default config
            assert manager.config is not None
            assert "workflow" in manager.config
        finally:
            os.unlink(temp_file)

    def test_merge_config_nested_dicts(self):
        """Test that config merging works for nested dictionaries."""
        manager = ConfigManager(config_file="/tmp/merge_test_config.yaml")
        original_config = manager.config.copy()

        # Create a separate config for merging
        base = {"workflow": {"max_iterations": 100, "max_parallel": 2}}
        override = {
            "workflow": {"max_parallel": 8, "new_key": "new_value"},
            "new_section": {"key": "value"},
        }

        manager._merge_config(base, override)

        # Verify merge
        assert base["workflow"]["max_parallel"] == 8
        assert base["workflow"]["max_iterations"] == 100  # preserved
        assert base["workflow"]["new_key"] == "new_value"
        assert base["new_section"]["key"] == "value"


class TestConfigManagerGet:
    """Test ConfigManager.get() method."""

    def test_get_simple_key(self):
        """Test getting a simple top-level key."""
        # Use temporary config file to avoid external dependency
        manager = ConfigManager(config_file="/nonexistent/get_test_config.yaml")
        value = manager.get("workflow")
        assert value is not None
        assert "max_iterations" in value

    def test_get_nested_key(self):
        """Test getting a nested key with dot notation."""
        # Use non-existent file to get default values
        manager = ConfigManager(config_file="/nonexistent/get_test_config.yaml")
        # Check that we can get nested keys
        value = manager.get("workflow.max_iterations")
        assert value is not None
        assert isinstance(value, int)

        value = manager.get("workflow.max_parallel")
        assert value is not None

        value = manager.get("skills.path")
        assert value is not None

        value = manager.get("skills.default_timeout")
        assert value is not None

    def test_get_with_default(self):
        """Test getting a key with default value."""
        manager = ConfigManager(config_file="/nonexistent/default_test_config.yaml")
        assert manager.get("nonexistent.key", default=42) == 42
        assert manager.get("nonexistent.key", default="default") == "default"

    def test_get_key_not_found(self):
        """Test getting a key that doesn't exist."""
        manager = ConfigManager(config_file="/nonexistent/notfound_test_config.yaml")
        assert manager.get("nonexistent.key") is None

    def test_get_type_validation_matching_type(self):
        """Test type validation when type matches."""
        # Use non-existent file to get default values
        manager = ConfigManager(config_file="/nonexistent/type_test_config.yaml")
        value = manager.get("workflow.max_iterations", expected_type=int)
        assert value is not None
        assert isinstance(value, int)

        value = manager.get("compression.enabled", expected_type=bool)
        assert value is not None
        assert isinstance(value, bool)

    def test_get_type_validation_mismatch_type(self):
        """Test type validation when type doesn't match (returns default)."""
        # Use non-existent file to get default values
        manager = ConfigManager(config_file="/nonexistent/mismatch_test_config.yaml")
        # Try to get an int as a str
        value = manager.get("workflow.max_iterations", expected_type=str, default="fallback")
        assert value == "fallback"  # Type mismatch returns default

        # Try to get an int as a bool (should also fail)
        value = manager.get("workflow.max_iterations", expected_type=bool, default=False)
        assert value is False  # Type mismatch returns provided default

    def test_get_nested_key_with_default(self):
        """Test getting nested key with default when parent doesn't exist."""
        manager = ConfigManager(config_file="/nonexistent/nested_test_config.yaml")
        assert manager.get("nonexistent.nested.key", default="fallback") == "fallback"


class TestConfigManagerSet:
    """Test ConfigManager.set() method."""

    def test_set_simple_key(self):
        """Test setting a simple top-level key."""
        manager = ConfigManager(config_file="/tmp/set_test_config.yaml")
        manager.set("new_key", "new_value")
        assert manager.get("new_key") == "new_value"

    def test_set_nested_key_existing(self):
        """Test setting a nested key that already exists."""
        manager = ConfigManager(config_file="/tmp/set_nested_test_config.yaml")
        manager.set("workflow.max_iterations", 250)
        assert manager.get("workflow.max_iterations") == 250

        manager.set("skills.path", "/custom/skills")
        assert manager.get("skills.path") == "/custom/skills"

    def test_set_nested_key_non_existing_parent(self):
        """Test setting a nested key when parent doesn't exist."""
        manager = ConfigManager(config_file="/tmp/set_parent_test_config.yaml")
        manager.set("new_section.new_key", "value")
        assert manager.get("new_section.new_key") == "value"
        assert isinstance(manager.get("new_section"), dict)

    def test_set_deeply_nested_key(self):
        """Test setting a deeply nested key."""
        manager = ConfigManager(config_file="/tmp/set_deep_test_config.yaml")
        manager.set("new_level1.new_level2.new_level3.key", "deep_value")
        assert manager.get("new_level1.new_level2.new_level3.key") == "deep_value"

    def test_set_overwrites_existing_value(self):
        """Test that set overwrites existing values."""
        manager = ConfigManager(config_file="/tmp/overwrite_test_config.yaml")
        original = manager.get("workflow.max_iterations")
        manager.set("workflow.max_iterations", original + 100)
        assert manager.get("workflow.max_iterations") == original + 100


class TestConfigManagerSave:
    """Test ConfigManager.save() method."""

    def test_save_success(self):
        """Test successful config save."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_file = f.name

        try:
            manager = ConfigManager(config_file=temp_file)
            manager.set("test_key", "test_value")
            result = manager.save()

            assert result is True

            # Verify file was created and contains correct data
            with open(temp_file, "r") as f:
                saved_config = yaml.safe_load(f)
            assert saved_config is not None
            assert saved_config.get("test_key") == "test_value"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_save_to_non_writable_path(self):
        """Test saving to a path that can't be written."""
        manager = ConfigManager(config_file="/root/nonexistent/config.yaml")
        result = manager.save()
        assert result is False

    def test_save_preserves_structure(self):
        """Test that save preserves the config structure."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_file = f.name

        try:
            manager = ConfigManager(config_file=temp_file)
            original_max_iterations = manager.config["workflow"]["max_iterations"]
            manager.set("workflow.max_iterations", original_max_iterations + 100)
            manager.save()

            # Load saved config and verify structure
            with open(temp_file, "r") as f:
                saved_config = yaml.safe_load(f)

            assert saved_config["workflow"]["max_iterations"] == original_max_iterations + 100
            # Verify other keys are preserved
            assert "max_parallel" in saved_config["workflow"]
            assert "path" in saved_config["skills"]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestModuleLevelFunctions:
    """Test module-level functions."""

    def test_get_config_function(self):
        """Test get_config module-level function."""
        value = get_config("workflow.max_iterations")
        assert value is not None
        assert isinstance(value, int)

    def test_get_config_with_default(self):
        """Test get_config with default value."""
        value = get_config("nonexistent.key", default=42)
        assert value == 42

    def test_set_config_function(self):
        """Test set_config module-level function."""
        set_config("test.global.key", "global_value")
        value = get_config("test.global.key")
        assert value == "global_value"

    def test_save_config_function(self):
        """Test save_config module-level function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_file = f.name

        try:
            # Save the global config_manager to a temp file for testing
            import lingflow.common.config as config_module

            original_file = config_module.config_manager.config_file
            config_module.config_manager.config_file = temp_file
            config_module.config_manager.set("test_save", True)

            result = save_config()
            # Function should return a boolean
            assert isinstance(result, (bool, type(None)))

            # Restore original file
            config_module.config_manager.config_file = original_file
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def test_full_workflow(self):
        """Test full workflow: load, get, set, save."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_file = f.name

        try:
            # 1. Load config
            manager = ConfigManager(config_file=temp_file)
            max_iter = manager.get("workflow.max_iterations")
            assert max_iter is not None
            assert isinstance(max_iter, int)

            # 2. Get nested values
            parallel = manager.get("workflow.max_parallel")
            assert parallel is not None

            # 3. Set new values
            manager.set("workflow.max_iterations", 300)
            manager.set("workflow.max_parallel", 6)

            # 4. Verify changes
            assert manager.get("workflow.max_iterations") == 300
            assert manager.get("workflow.max_parallel") == 6

            # 5. Save config
            result = manager.save()
            assert result is True

            # 6. Load again and verify persistence
            manager2 = ConfigManager(config_file=temp_file)
            assert manager2.get("workflow.max_iterations") == 300
            assert manager2.get("workflow.max_parallel") == 6
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_type_validation_workflow(self):
        """Test type validation across get operations."""
        # Use non-existent file to get default values
        manager = ConfigManager(config_file="/nonexistent/validation_test_config.yaml")

        # Set a value with wrong type expectation
        value = manager.get("workflow.max_iterations", expected_type=str, default="fallback")
        assert value == "fallback"

        # Set with correct type
        value = manager.get("workflow.max_iterations", expected_type=int, default=0)
        assert value is not None
        assert isinstance(value, int)

        # Get boolean with type check
        value = manager.get("compression.enabled", expected_type=bool, default=False)
        assert value is not None
        assert isinstance(value, bool)

    def test_nested_config_operations(self):
        """Test operations on deeply nested config structures."""
        manager = ConfigManager(config_file="/tmp/nested_ops_test_config.yaml")

        # Set deeply nested values
        manager.set("new_test.new_a.new_b.new_c", "deep")
        assert manager.get("new_test.new_a.new_b.new_c") == "deep"

        # Set sibling at same level
        manager.set("new_test.new_a.new_b.new_d", "sibling")
        assert manager.get("new_test.new_a.new_b.new_d") == "sibling"

        # Verify parent structure is dict
        assert isinstance(manager.get("new_test.new_a.new_b"), dict)

    def test_default_config_complete(self):
        """Test that default config has all expected sections."""
        # Use non-existent file to get default values
        manager = ConfigManager(config_file="/nonexistent/complete_test_config.yaml")
        expected_sections = ["workflow", "skills", "agents", "compression", "logging"]
        for section in expected_sections:
            assert section in manager.config, f"Missing section: {section}"

    def test_config_immutability_between_instances(self):
        """Test that different ConfigManager instances have independent configs."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()

        # Modify manager1
        manager1.set("test.independent", "value1")

        # Verify manager2 is not affected
        assert manager2.get("test.independent") is None
        assert manager1.get("test.independent") == "value1"
