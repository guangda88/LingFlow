"""Tests for document saving functionality"""

import json
import sys
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Add skills directory to path
skills_dir = Path(__file__).parent.parent.parent / "skills"
sys.path.insert(0, str(skills_dir / "api-doc-generator"))

from implementation import (
    save_document,
    to_simple_yaml,
)


class TestSaveDocument:
    """Test save_document function"""

    def test_save_json_format(self, tmp_path):
        """Test saving document in JSON format"""
        doc = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

        output_path = tmp_path / "api.json"
        save_document(doc, str(output_path), "json")

        assert output_path.exists()

        with open(output_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["openapi"] == "3.0.0"
        assert loaded["info"]["title"] == "Test API"

    def test_save_yaml_format(self, tmp_path):
        """Test saving document in YAML format"""
        doc = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

        output_path = tmp_path / "api.yaml"
        save_document(doc, str(output_path), "yaml")

        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8")
        assert "openapi:" in content
        assert "Test API" in content

    def test_save_creates_directories(self, tmp_path):
        """Test that save creates parent directories"""
        doc = {"openapi": "3.0.0", "info": {"title": "API"}, "paths": {}}

        output_path = tmp_path / "deep" / "nested" / "dir" / "api.json"
        save_document(doc, str(output_path), "json")

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_save_json_indentation(self, tmp_path):
        """Test JSON output has proper indentation"""
        doc = {"openapi": "3.0.0", "info": {"title": "API", "version": "1.0.0"}, "paths": {"/test": {"get": {}}}}

        output_path = tmp_path / "api.json"
        save_document(doc, str(output_path), "json")

        content = output_path.read_text(encoding="utf-8")
        # Check for indentation
        assert "  " in content  # 2-space indentation

    def test_save_json_unicode(self, tmp_path):
        """Test JSON output handles Unicode correctly"""
        doc = {"openapi": "3.0.0", "info": {"title": "测试 API", "description": "API with émojis 🎉"}, "paths": {}}

        output_path = tmp_path / "api.json"
        save_document(doc, str(output_path), "json")

        with open(output_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["info"]["title"] == "测试 API"
        assert "🎉" in loaded["info"]["description"]

    def test_save_yaml_without_pyyaml(self, tmp_path):
        """Test YAML fallback when PyYAML is not available"""
        doc = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

        output_path = tmp_path / "api.yaml"

        # Mock the yaml import to fail
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args: (
                (_ for _ in ()).throw(ImportError(f"No module named {name}")) if name == "yaml" else __import__(name, *args)
            ),
        ):
            save_document(doc, str(output_path), "yaml")

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        # Should use simple YAML format
        assert "openapi:" in content

    def test_save_overwrites_existing(self, tmp_path):
        """Test that save overwrites existing file"""
        doc = {"openapi": "3.0.0", "info": {"title": "New API"}, "paths": {}}

        output_path = tmp_path / "api.json"
        # Create existing file
        output_path.write_text("old content")

        save_document(doc, str(output_path), "json")

        with open(output_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["info"]["title"] == "New API"


class TestSimpleYamlGenerator:
    """Test to_simple_yaml function"""

    def test_simple_dict(self):
        """Test converting simple dict to YAML"""
        doc = {"key": "value", "number": 42}
        result = to_simple_yaml(doc)

        assert "key: value" in result
        assert "number: 42" in result

    def test_nested_dict(self):
        """Test converting nested dict to YAML"""
        doc = {"level1": {"level2": {"level3": "value"}}}
        result = to_simple_yaml(doc)

        assert "level1:" in result
        assert "  level2:" in result
        assert "    level3: value" in result

    def test_list_of_primitives(self):
        """Test converting list of primitives to YAML"""
        doc = {"items": ["apple", "banana", "cherry"]}
        result = to_simple_yaml(doc)

        assert "items:" in result
        assert "- apple" in result
        assert "- banana" in result
        assert "- cherry" in result

    def test_list_of_dicts(self):
        """Test converting list of dicts to YAML"""
        doc = {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}
        result = to_simple_yaml(doc)

        assert "users:" in result
        assert "- name: Alice" in result
        assert "- name: Bob" in result

    def test_boolean_values(self):
        """Test converting boolean values"""
        doc = {"active": True, "deleted": False}
        result = to_simple_yaml(doc)

        assert "active: true" in result
        assert "deleted: false" in result

    def test_null_value(self):
        """Test converting null value"""
        doc = {"optional": None}
        result = to_simple_yaml(doc)

        assert "optional: null" in result

    def test_mixed_structure(self):
        """Test converting complex mixed structure"""
        doc = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/users": {"get": {"summary": "List users", "parameters": [{"name": "limit", "in": "query"}]}}},
        }
        result = to_simple_yaml(doc)

        assert "openapi: 3.0.0" in result
        assert "info:" in result
        assert "paths:" in result
        assert "- name: limit" in result

    def test_empty_dict(self):
        """Test converting empty dict"""
        result = to_simple_yaml({})
        assert result == ""

    def test_empty_list(self):
        """Test converting empty list"""
        doc = {"items": []}
        result = to_simple_yaml(doc)

        assert "items:" in result

    def test_special_characters_in_values(self):
        """Test handling special characters"""
        doc = {"description": "Text with \"quotes\" and 'apostrophes'", "path": "C:\\Users\\test"}
        result = to_simple_yaml(doc)

        assert "description:" in result
        assert "path:" in result

    def test_numeric_values(self):
        """Test various numeric types"""
        doc = {"integer": 42, "float": 3.14, "negative": -10, "zero": 0}
        result = to_simple_yaml(doc)

        assert "integer: 42" in result
        assert "float: 3.14" in result
        assert "negative: -10" in result
        assert "zero: 0" in result


class TestSaveDocumentIntegration:
    """Integration tests for save_document"""

    def test_save_and_load_json(self, tmp_path):
        """Test save and reload JSON document"""
        original = {
            "openapi": "3.0.0",
            "info": {"title": "Integration Test API", "version": "1.0.0"},
            "paths": {"/users": {"get": {"summary": "Get users", "responses": {"200": {"description": "OK"}}}}},
            "components": {"schemas": {"User": {"type": "object", "properties": {"id": {"type": "integer"}}}}},
        }

        output_path = tmp_path / "api.json"
        save_document(original, str(output_path), "json")

        with open(output_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded == original

    def test_save_multiple_documents(self, tmp_path):
        """Test saving multiple documents"""
        docs = [{"openapi": "3.0.0", "info": {"title": f"API {i}"}, "paths": {}} for i in range(5)]

        for i, doc in enumerate(docs):
            output_path = tmp_path / f"api_{i}.json"
            save_document(doc, str(output_path), "json")

        # Verify all files exist and have correct content
        for i, doc in enumerate(docs):
            output_path = tmp_path / f"api_{i}.json"
            assert output_path.exists()

            with open(output_path, "r") as f:
                loaded = json.load(f)
            assert loaded["info"]["title"] == f"API {i}"

    def test_save_to_nonexistent_nested_directory(self, tmp_path):
        """Test saving to deeply nested non-existent directory"""
        doc = {"openapi": "3.0.0", "info": {"title": "API"}, "paths": {}}

        nested_path = tmp_path / "a" / "b" / "c" / "d" / "api.json"
        save_document(doc, str(nested_path), "json")

        assert nested_path.exists()
        assert nested_path.parent.is_dir()


class TestSaveDocumentErrorHandling:
    """Test error handling in save_document"""

    def test_save_to_invalid_path(self):
        """Test handling invalid path"""
        doc = {"openapi": "3.0.0"}

        # Use an invalid path (e.g., trying to write to /root when not root)
        # This should raise an error
        with pytest.raises(Exception):
            save_document(doc, "/root/invalid/api.json", "json")

    def test_save_with_permission_error(self, tmp_path):
        """Test handling permission error"""
        doc = {"openapi": "3.0.0"}
        output_path = tmp_path / "api.json"

        # Create the file and make it read-only
        output_path.write_text("test")
        output_path.chmod(0o444)

        # This should raise an error
        with pytest.raises(Exception):
            save_document(doc, str(output_path), "json")
