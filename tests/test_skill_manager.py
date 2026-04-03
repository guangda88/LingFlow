import pytest
import tempfile
import os
from unittest.mock import patch

from lingflow.common.skill_manager import SkillManager


class TestSkillManagerInit:
    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_init(self, mock_config):
        m = SkillManager()
        assert m.skills_path == "skills"


class TestGetSkillPath:
    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_invalid_name_empty(self, mock_config):
        m = SkillManager()
        assert m.get_skill_path("") is None

    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_invalid_name_chars(self, mock_config):
        m = SkillManager()
        assert m.get_skill_path("../etc/passwd") is None

    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_valid_name_not_exists(self, mock_config):
        m = SkillManager()
        assert m.get_skill_path("nonexistent_skill") is None

    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_valid_name_exists(self, mock_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = os.path.join(tmpdir, "test-skill")
            os.makedirs(skill_dir)
            impl_path = os.path.join(skill_dir, "implementation.py")
            with open(impl_path, "w") as f:
                f.write("def execute_skill(params): return params\n")

            m = SkillManager()
            m.skills_path = tmpdir
            result = m.get_skill_path("test-skill")
            assert result is not None
            assert result.endswith("implementation.py")


class TestLoadSkill:
    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_load_nonexistent(self, mock_config):
        m = SkillManager()
        from lingflow.common.exceptions import SkillNotFoundError
        with pytest.raises(SkillNotFoundError):
            m.load_skill("nonexistent")

    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_load_and_cache(self, mock_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = os.path.join(tmpdir, "my-skill")
            os.makedirs(skill_dir)
            impl_path = os.path.join(skill_dir, "implementation.py")
            with open(impl_path, "w") as f:
                f.write("def execute_skill(params): return {'ok': True}\n")

            m = SkillManager()
            m.skills_path = tmpdir
            module = m.load_skill("my-skill")
            assert module is not None
            assert "my-skill" in m.skills_cache

            cached = m.load_skill("my-skill")
            assert cached is module


class TestListSkills:
    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_list_skills_empty(self, mock_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            m = SkillManager()
            m.skills_path = tmpdir
            assert m.list_skills() == []

    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_list_skills_with_impl(self, mock_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["skill-a", "skill-b"]:
                d = os.path.join(tmpdir, name)
                os.makedirs(d)
                with open(os.path.join(d, "implementation.py"), "w") as f:
                    f.write("pass\n")
            d = os.path.join(tmpdir, "no-impl")
            os.makedirs(d)

            m = SkillManager()
            m.skills_path = tmpdir
            skills = m.list_skills()
            assert "skill-a" in skills
            assert "skill-b" in skills
            assert "no-impl" not in skills


class TestParseSkillMd:
    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_parse_basic(self, mock_config):
        m = SkillManager()
        content = """name: test-skill
description: A test skill
version: 1.0
dependencies:
- dep1
- dep2
"""
        meta = m._parse_skill_md(content)
        assert meta["name"] == "test-skill"
        assert meta["description"] == "A test skill"
        assert meta["version"] == "1.0"
        assert meta["dependencies"] == ["dep1", "dep2"]


class TestGetSkillMetadata:
    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_get_existing(self, mock_config):
        m = SkillManager()
        m.skill_metadata["test"] = {"name": "test"}
        assert m.get_skill_metadata("test") == {"name": "test"}

    @patch("lingflow.common.skill_manager.get_config", return_value="skills")
    def test_get_missing(self, mock_config):
        m = SkillManager()
        assert m.get_skill_metadata("missing") is None
