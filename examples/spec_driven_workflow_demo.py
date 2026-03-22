#!/usr/bin/env python3
"""
LingFlow v3.3.0 - Spec-Driven Secure Development Workflow Demo

This script demonstrates the complete multi-agent secure development workflow:
1. Constitutional constraint loading
2. TDD test specification
3. Code generation with security
4. Multi-layer security validation
5. Test validation
6. Context cleanup
7. Final deployment decision

Based on research findings from:
- Constitutional Spec-Driven Development (73% vulnerability reduction)
- Securing AI-Assisted Cloud Engineering (97.8% prevention rate)
- Ten Simple Rules for AI-Assisted Coding (TDD enforcement)
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add lingflow to path
sys.path.insert(0, str(Path(__file__).parent))

from lingflow.core.constitution import Constitution, EnforcementLevel
from lingflow.core.compliance_matrix import ComplianceMatrix
from lingflow.guardrail import GuardrailValidator, DeploymentGate
from lingflow.tdd import TDDValidator
from lingflow.context import CodeCleanup, DocumentationOptimizer


class SpecDrivenWorkflowDemo:
    """Demo of spec-driven secure development workflow"""

    def __init__(self):
        """Initialize workflow components"""
        print("=" * 80)
        print("LingFlow v3.3.0 - Spec-Driven Secure Development Workflow")
        print("=" * 80)
        print()

        # Initialize components
        self.constitution = Constitution(".lingflow/constitution.yaml")
        self.compliance_matrix = ComplianceMatrix()
        self.guardrail = GuardrailValidator(".lingflow/policies/security.yaml")
        self.deployment_gate = DeploymentGate()
        self.tdd = TDDValidator(coverage_target=80.0)
        self.code_cleanup = CodeCleanup()

    def run_demo(self):
        """Run complete workflow demo"""
        start_time = time.time()

        # Task description
        task = {
            "name": "user_authentication",
            "description": "实现用户认证功能，包括登录、注册、密码重置",
            "security_requirements": [
                "密码必须使用bcrypt加密",
                "实现CSRF保护",
                "实现会话管理",
                "防止SQL注入",
                "防止XSS攻击"
            ]
        }

        print(f"📋 Task: {task['name']}")
        print(f"   Description: {task['description']}")
        print()

        # ===== Phase 1: Constitutional Constraint =====
        print("=" * 80)
        print("🔐 Phase 1: Constitutional Constraint")
        print("=" * 80)
        print()

        applicable_principles = self.constitution.get_principles(EnforcementLevel.MUST)
        print(f"✓ Loaded {len(applicable_principles)} MUST-level security principles")
        for principle in applicable_principles[:3]:  # Show first 3
            print(f"  - {principle.id}: {principle.name}")
        print(f"  ... and {len(applicable_principles) - 3} more")
        print()

        # ===== Phase 2: TDD Planning =====
        print("=" * 80)
        print("🧪 Phase 2: TDD Planning")
        print("=" * 80)
        print()

        test_spec = self.tdd.generate_test_specification(
            feature_description=task['description'],
            requirements=task['security_requirements'],
            security_principles=[p.name for p in applicable_principles]
        )
        print(f"✓ Generated {len(test_spec.test_cases)} test cases")
        for tc in test_spec.test_cases[:3]:
            print(f"  - {tc.name}")
            print(f"    Scenarios: {', '.join(tc.edge_cases[:2])}")
        print()
        print(f"✓ Target coverage: {test_spec.coverage_target}%")
        print()

        # ===== Phase 3: Code Generation (Simulated) =====
        print("=" * 80)
        print("💻 Phase 3: Code Generation")
        print("=" * 80)
        print()

        # Simulate code generation
        generated_code = self._generate_sample_code()
        print("✓ Generated implementation code")
        print(f"  - Lines of code: {len(generated_code.split(chr(10)))}")
        print()

        # ===== Phase 4: Security Validation =====
        print("=" * 80)
        print("🛡️ Phase 4: Security Validation (AGCEF)")
        print("=" * 80)
        print()

        security_report = self.guardrail.validate_agcef(
            code=generated_code,
            file_path="services/auth_service.py"
        )
        print(f"✓ Security score: {security_report.overall_score:.2f}/100")
        print(f"✓ Risk level: {security_report.risk_level}")
        print(f"✓ Total violations: {security_report.total_violations}")
        print(f"✓ Critical violations: {security_report.critical_violations}")
        print()

        if security_report.violations:
            print("Violations found:")
            for v in security_report.violations[:3]:
                print(f"  🔴 {v.code} ({v.severity.value}): {v.description}")
        print()

        # ===== Phase 5: Human Decision (if needed) =====
        if security_report.overall_score < 80:
            print("=" * 80)
            print("👤 Phase 5: Human Decision Required")
            print("=" * 80)
            print()
            print(f"⚠️ Security score {security_report.overall_score:.2f} is below 80")
            print("Human review required before proceeding")
            print()
        else:
            print("✓ Security score is sufficient, auto-approved")
            print()

        # ===== Phase 6: Test Validation =====
        print("=" * 80)
        print("🧪 Phase 6: Test Validation")
        print("=" * 80)
        print()

        # Simulate test file
        test_code = self._generate_sample_tests()
        test_report = self.tdd.validate_tests("tests/test_auth.py")
        print(f"✓ Total tests: {test_report.total_tests}")
        print(f"✓ Paper tests: {test_report.paper_tests}")
        print(f"✓ Test coverage: {test_report.test_coverage:.2%}")
        print(f"✓ Valid: {'✅' if test_report.is_valid else '❌'}")
        print()

        if test_report.violations:
            print("Test violations:")
            for v in test_report.violations[:3]:
                print(f"  ⚠️ {v.type}: {v.description}")
        print()

        # ===== Phase 7: Context Cleanup =====
        print("=" * 80)
        print("🧹 Phase 7: Context Cleanup")
        print("=" * 80)
        print()

        # Simulate cleanup
        cleanup_items = self.code_cleanup.analyze_file("services/auth_service.py")
        print(f"✓ Found {len(cleanup_items)} cleanup opportunities")
        for item in cleanup_items[:3]:
            print(f"  - {item.type}: {item.description}")
        print()

        # ===== Phase 8: Final Validation & Deployment =====
        print("=" * 80)
        print("✅ Phase 8: Final Validation & Deployment")
        print("=" * 80)
        print()

        # Check deployment gates
        is_ready, issues = self.deployment_gate.check_deployment_readiness(
            security_report=security_report,
            test_coverage=test_report.test_coverage,
            paper_tests=test_report.paper_tests
        )

        print("Deployment gate checks:")
        print(f"  - Security violations: {'✅' if security_report.critical_violations == 0 else '❌'}")
        print(f"  - Test coverage: {'✅' if test_report.test_coverage >= 80 else '❌'} ({test_report.test_coverage:.2%})")
        print(f"  - Paper tests: {'✅' if test_report.paper_tests == 0 else '❌'}")
        print()

        if is_ready:
            print("✅ DEPLOYMENT APPROVED")
            print()
            print("Summary:")
            print(f"  - Security score: {security_report.overall_score:.2f}")
            print(f"  - Test coverage: {test_report.test_coverage:.2%}")
            print(f"  - Total violations: {security_report.total_violations}")
            print(f"  - Execution time: {time.time() - start_time:.2f}s")
        else:
            print("❌ DEPLOYMENT BLOCKED")
            print()
            print("Issues:")
            for issue in issues:
                print(f"  - {issue}")
        print()

        # ===== Metrics =====
        print("=" * 80)
        print("📊 Metrics")
        print("=" * 80)
        print()

        print("Expected outcomes based on research:")
        print(f"  - Security vulnerability reduction: 73%")
        print(f"  - Vulnerability prevention rate: 97.8%")
        print(f"  - Time to first secure build: -56%")
        print(f"  - Token savings: 30-50%")
        print()

    def _generate_sample_code(self) -> str:
        """Generate sample code for demo"""
        return '''
# User Authentication Service

import bcrypt
from flask import request, session, jsonify
from sqlalchemy import text

class AuthService:
    """User authentication service with security features"""

    def __init__(self, db):
        self.db = db

    def register(self, username: str, password: str, email: str) -> dict:
        """Register new user"""
        # Hash password with bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Use parameterized query (SQL Injection protection)
        query = text("""
            INSERT INTO users (username, password_hash, email)
            VALUES (:username, :password, :email)
        """)

        result = self.db.execute(query, {
            'username': username,
            'password': hashed,
            'email': email
        })

        return {'success': True, 'user_id': result.lastrowid}

    def login(self, username: str, password: str) -> dict:
        """Authenticate user"""
        # Use parameterized query
        query = text("""
            SELECT id, password_hash FROM users
            WHERE username = :username
        """)

        result = self.db.execute(query, {'username': username})
        user = result.fetchone()

        if user:
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
                # Create session (CSRF protection via Flask session)
                session['user_id'] = user['id']
                session['csrf_token'] = bcrypt.gensalt().hex()

                return {'success': True, 'user_id': user['id']}

        return {'success': False, 'error': 'Invalid credentials'}

    def logout(self) -> dict:
        """Logout user"""
        session.clear()
        return {'success': True}

    def reset_password(self, email: str) -> dict:
        """Reset user password"""
        # Use parameterized query
        query = text("""
            SELECT id FROM users WHERE email = :email
        """)

        result = self.db.execute(query, {'email': email})
        user = result.fetchone()

        if user:
            # Generate secure token
            import secrets
            reset_token = secrets.token_urlsafe(32)

            # In production, send email with token
            return {'success': True, 'token': reset_token}

        return {'success': False, 'error': 'User not found'}
'''

    def _generate_sample_tests(self) -> str:
        """Generate sample tests for demo"""
        return '''
# Tests for Authentication Service

import pytest
from services.auth_service import AuthService

class TestAuthService:
    """Test cases for authentication service"""

    def test_register_success(self, db):
        """Test successful user registration"""
        auth = AuthService(db)
        result = auth.register('testuser', 'SecurePass123!', 'test@example.com')

        assert result['success'] is True
        assert 'user_id' in result
        assert result['user_id'] > 0

    def test_register_duplicate_user(self, db):
        """Test registration with duplicate username"""
        auth = AuthService(db)
        auth.register('testuser', 'password1', 'test@example.com')

        result = auth.register('testuser', 'password2', 'test2@example.com')

        assert result['success'] is False
        assert 'error' in result

    def test_login_success(self, db):
        """Test successful login"""
        auth = AuthService(db)
        auth.register('testuser', 'SecurePass123!', 'test@example.com')

        result = auth.login('testuser', 'SecurePass123!')

        assert result['success'] is True
        assert result['user_id'] > 0
        assert 'csrf_token' in session

    def test_login_wrong_password(self, db):
        """Test login with wrong password"""
        auth = AuthService(db)
        auth.register('testuser', 'SecurePass123!', 'test@example.com')

        result = auth.login('testuser', 'WrongPassword')

        assert result['success'] is False
        assert 'error' in result

    def test_login_nonexistent_user(self, db):
        """Test login with non-existent user"""
        auth = AuthService(db)

        result = auth.login('nonexistent', 'password')

        assert result['success'] is False
        assert 'error' in result

    def test_logout(self, db):
        """Test logout"""
        auth = AuthService(db)
        auth.register('testuser', 'password', 'test@example.com')
        auth.login('testuser', 'password')

        result = auth.logout()

        assert result['success'] is True
        assert 'user_id' not in session

    def test_reset_password(self, db):
        """Test password reset"""
        auth = AuthService(db)
        auth.register('testuser', 'password', 'test@example.com')

        result = auth.reset_password('test@example.com')

        assert result['success'] is True
        assert 'token' in result

    def test_reset_password_nonexistent_user(self, db):
        """Test password reset for non-existent user"""
        auth = AuthService(db)

        result = auth.reset_password('nonexistent@example.com')

        assert result['success'] is False
        assert 'error' in result

    def test_sql_injection_protection(self, db):
        """Test SQL injection protection"""
        auth = AuthService(db)

        # Attempt SQL injection
        result = auth.register("' OR '1'='1", "password", "test@example.com")

        # Should not execute SQL injection
        assert result['success'] is False or 'error' in result

    def test_empty_username(self, db):
        """Test registration with empty username"""
        auth = AuthService(db)

        result = auth.register('', 'password', 'test@example.com')

        assert result['success'] is False

    def test_empty_password(self, db):
        """Test registration with empty password"""
        auth = AuthService(db)

        result = auth.register('testuser', '', 'test@example.com')

        assert result['success'] is False
'''


def main():
    """Main entry point"""
    demo = SpecDrivenWorkflowDemo()
    demo.run_demo()


if __name__ == '__main__':
    main()
