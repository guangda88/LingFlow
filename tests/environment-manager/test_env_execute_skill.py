"""Environment Manager execute_skill 函数测试"""

import tempfile

import pytest


class TestExecuteSkill:
    """测试 execute_skill 函数"""

    def test_detect_environment(self, env_manager_module, tmp_path):
        """测试环境检测"""
        execute_skill = env_manager_module.execute_skill
        result = execute_skill({"action": "detect", "project_dir": str(tmp_path)})

        assert result["success"] is True
        assert "data" in result

    def test_generate_config(self, env_manager_module, tmp_path):
        """测试配置生成"""
        execute_skill = env_manager_module.execute_skill
        result = execute_skill({"action": "generate", "project_dir": str(tmp_path), "output_format": "json"})

        assert result["success"] is True
        assert "data" in result

    def test_validate_config(self, env_manager_module, tmp_path):
        """测试配置验证"""
        execute_skill = env_manager_module.execute_skill

        # 创建一个 .env 文件
        env_file = tmp_path / ".env"
        env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\n")

        result = execute_skill(
            {"action": "validate", "project_dir": str(tmp_path), "config_type": "database", "env_file": str(env_file)}
        )

        assert "data" in result

    def test_security_audit(self, env_manager_module, tmp_path):
        """测试安全审计"""
        execute_skill = env_manager_module.execute_skill

        # 创建包含敏感信息的 .env 文件
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET_KEY=my-secret\nPASSWORD=password123\n")

        result = execute_skill({"action": "audit", "project_dir": str(tmp_path)})

        assert "data" in result

    def test_unknown_action(self, env_manager_module):
        """测试未知操作"""
        execute_skill = env_manager_module.execute_skill
        result = execute_skill({"action": "unknown"})

        assert result["success"] is False
        assert "errors" in result
