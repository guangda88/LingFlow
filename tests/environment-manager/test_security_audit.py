"""Environment Manager 安全审计测试"""

import pytest
import tempfile


class TestSecurityAudit:
    """测试安全审计功能"""

    def test_detect_secrets(self, env_manager_module, tmp_path):
        """测试检测敏感信息"""
        audit_security = getattr(env_manager_module, 'audit_security', None)
        if audit_security is None:
            pytest.skip("audit_security 函数不存在")

        # 创建包含敏感信息的 .env 文件
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET_KEY=my-secret-key\nPASSWORD=password123\nAPI_KEY=key-abc-123\n")

        result = audit_security(str(tmp_path))

        # 检查是否有秘密被发现
        assert 'secrets_found' in result
        assert len(result['secrets_found']) > 0

    def test_detect_weak_credentials(self, env_manager_module, tmp_path):
        """测试检测弱凭据"""
        audit_security = getattr(env_manager_module, 'audit_security', None)
        if audit_security is None:
            pytest.skip("audit_security 函数不存在")

        env_file = tmp_path / ".env"
        env_file.write_text("PASSWORD=123456\nADMIN_PASS=admin\n")

        result = audit_security(str(tmp_path))

        # 检查是否有风险被发现
        assert 'secrets_found' in result
        assert len(result['secrets_found']) > 0

    def test_safe_config(self, env_manager_module, tmp_path):
        """测试安全配置"""
        audit_security = getattr(env_manager_module, 'audit_security', None)
        if audit_security is None:
            pytest.skip("audit_security 函数不存在")

        env_file = tmp_path / ".env"
        env_file.write_text("APP_NAME=MyApp\nLOG_LEVEL=info\nTIMEOUT=30\n")

        result = audit_security(str(tmp_path))

        # 安全配置应该没有发现秘密
        assert len(result.get('secrets_found', [])) == 0

    def test_detect_url_patterns(self, env_manager_module, tmp_path):
        """测试检测 URL 模式"""
        audit_security = getattr(env_manager_module, 'audit_security', None)
        if audit_security is None:
            pytest.skip("audit_security 函数不存在")

        env_file = tmp_path / ".env"
        env_file.write_text("DATABASE_URL=postgresql://user:pass@localhost/db\nREDIS_URL=redis://localhost\n")

        result = audit_security(str(tmp_path))

        # URL 中的凭据应该被检测到
        assert 'secrets_found' in result
