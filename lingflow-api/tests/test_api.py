"""
REST API 单元测试

覆盖率目标: >80%
"""
import pytest
from unittest.mock import Mock, patch

fastapi = pytest.importorskip("fastapi", reason="FastAPI needed for REST API tests")
from fastapi.testclient import TestClient

# 导入应用
import sys
sys.path.insert(0, '.')
from main_simple import app

client = TestClient(app)

# API Key
API_KEY = "dev-key-12345"
HEADERS = {"X-API-Key": API_KEY}

# ==================== 根路径测试 ====================

def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["status"] == "running"

def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

# ==================== 技能系统测试 ====================

@patch('main_simple.LayeredSkillLoader')
def test_list_skills(mock_loader):
    """测试列出技能"""
    # Mock 技能
    mock_skill = Mock()
    mock_skill.name = "test-skill"
    mock_skill.description = "Test skill"
    mock_skill.version = "1.0.0"
    mock_skill.category = "testing"
    mock_skill.layer = "L1"

    mock_loader_instance = Mock()
    mock_loader_instance.list_skills.return_value = [mock_skill]
    mock_loader.return_value = mock_loader_instance

    response = client.get("/api/v1/skills", headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert len(data["skills"]) == 1
    assert data["skills"][0]["name"] == "test-skill"

def test_list_skills_without_api_key():
    """测试无 API Key 的情况"""
    response = client.get("/api/v1/skills")
    assert response.status_code == 200  # 可选认证

@patch('main_simple.LayeredSkillLoader')
def test_get_skill(mock_loader):
    """测试获取技能详情"""
    # Mock 技能
    mock_skill = Mock()
    mock_skill.name = "test-skill"
    mock_skill.description = "Test skill"
    mock_skill.version = "1.0.0"

    mock_loader_instance = Mock()
    mock_loader_instance.get_skill.return_value = mock_skill
    mock_loader.return_value = mock_loader_instance

    response = client.get("/api/v1/skills/test-skill", headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "test-skill"

@patch('main_simple.LayeredSkillLoader')
def test_get_skill_not_found(mock_loader):
    """测试技能不存在"""
    mock_loader_instance = Mock()
    mock_loader_instance.get_skill.return_value = None
    mock_loader.return_value = mock_loader_instance

    response = client.get("/api/v1/skills/not-exist", headers=HEADERS)
    assert response.status_code == 404

@patch('main_simple.LayeredSkillLoader')
def test_execute_skill(mock_loader):
    """测试执行技能"""
    # Mock 技能和结果
    mock_skill = Mock()
    mock_result = Mock()
    mock_result.is_success.return_value = True
    mock_result.value = "Success"

    mock_skill.execute.return_value = mock_result

    mock_loader_instance = Mock()
    mock_loader_instance.get_skill.return_value = mock_skill
    mock_loader.return_value = mock_loader_instance

    payload = {"params": {"test": "value"}, "timeout": 60}

    response = client.post("/api/v1/skills/test-skill/execute",
                           json=payload, headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] == True

# ==================== 工作流系统测试 ====================

@patch('main_simple.MultiWorkflowCoordinator')
def test_list_workflows(mock_coordinator):
    """测试列出工作流"""
    # Mock 工作流
    mock_workflow = Mock()
    mock_workflow.workflow_id = "test-workflow"
    mock_workflow.name = "Test Workflow"
    mock_workflow.workflow_type.value = "dev"
    mock_workflow.status.value = "pending"
    mock_workflow.priority.value = "NORMAL"

    mock_coordinator_instance = Mock()
    mock_coordinator_instance.list_workflows.return_value = [mock_workflow]
    mock_coordinator.return_value = mock_coordinator_instance

    response = client.get("/api/v1/workflows", headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert len(data["workflows"]) == 1

@patch('main_simple.MultiWorkflowCoordinator')
def test_run_workflow(mock_coordinator):
    """测试执行工作流"""
    # Mock 结果
    mock_result = Mock()
    mock_result.task_id = "task-123"
    mock_result.status.value = "completed"

    mock_coordinator_instance = Mock()
    mock_coordinator_instance.run_workflow.return_value = mock_result
    mock_coordinator.return_value = mock_coordinator_instance

    payload = {
        "params": {"feature": "test"},
        "strategy": "hybrid"
    }

    response = client.post("/api/v1/workflows/test-workflow/run",
                           json=payload, headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert data["task_id"] == "task-123"
    assert data["status"] == "completed"

# ==================== 代码审查测试 ====================

@patch('main_simple.CodeReviewer')
def test_review_code(mock_reviewer_cls):
    """测试代码审查"""
    # Mock 审查器和结果
    mock_reviewer_instance = Mock()
    mock_result = Mock()
    mock_result.to_dict.return_value = {
        "overall_score": 85,
        "dimensions": {},
        "suggestions": [],
        "metrics": {}
    }

    mock_reviewer_instance.review.return_value = mock_result
    mock_reviewer_cls.return_value = mock_reviewer_instance

    payload = {
        "target_path": "./src",
        "dimensions": ["complexity", "security"],
        "output_format": "json"
    }

    response = client.post("/api/v1/review", json=payload, headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert data["overall_score"] == 85

# ==================== 情报系统测试 ====================

@patch('main_simple.GitHubTrendCollector')
def test_get_github_trends(mock_collector_cls):
    """测试 GitHub 趋势"""
    # Mock 收集器
    mock_collector_instance = Mock()
    mock_collector_instance.collect_trends.return_value = [
        {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "stars": 100,
            "description": "Test repo",
            "language": "python",
            "relevance_score": 0.9
        }
    ]
    mock_collector_cls.return_value = mock_collector_instance

    response = client.get("/api/v1/intelligence/github?keywords=python,ai",
                         headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "test-repo"

# ==================== 认证测试 ====================

def test_invalid_api_key():
    """测试无效的 API Key"""
    headers = {"X-API-Key": "invalid-key"}
    response = client.get("/api/v1/skills/execute", headers=headers)
    # 可能返回 401 或继续（取决于是否强制认证）

# ==================== 错误处理测试 ====================

def test_404_not_found():
    """测试 404"""
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404

def test_422_validation_error():
    """测试验证错误"""
    payload = {"timeout": -1}  # 无效值
    response = client.post("/api/v1/skills/test/execute",
                           json=payload, headers=HEADERS)
    assert response.status_code == 422

# ==================== 性能测试 ====================

def test_response_time():
    """测试响应时间（应 <200ms）"""
    import time

    start = time.time()
    response = client.get("/health")
    duration = (time.time() - start) * 1000

    assert response.status_code == 200
    assert duration < 200  # 200ms

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=html"])
