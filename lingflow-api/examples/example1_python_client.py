"""
示例 1: Python 客户端使用 LingFlow API
"""
import requests
import json

API_BASE = "http://localhost:8000"
API_KEY = "dev-key-12345"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 1. 列出所有技能
def list_skills():
    response = requests.get(
        f"{API_BASE}/api/v1/skills",
        headers=headers
    )
    return response.json()

# 2. 执行代码生成技能
def generate_code(prompt: str):
    payload = {
        "params": {
            "prompt": prompt,
            "language": "python"
        },
        "timeout": 60
    }

    response = requests.post(
        f"{API_BASE}/api/v1/skills/code-generation/execute",
        headers=headers,
        json=payload
    )
    return response.json()

# 3. 运行工作流
def run_workflow(workflow_id: str, params: dict):
    payload = {
        "params": params,
        "strategy": "hybrid"
    }

    response = requests.post(
        f"{API_BASE}/api/v1/workflows/{workflow_id}/run",
        headers=headers,
        json=payload
    )
    return response.json()

# 4. 代码审查
def review_code(path: str):
    payload = {
        "target_path": path,
        "dimensions": ["complexity", "security"],
        "output_format": "json"
    }

    response = requests.post(
        f"{API_BASE}/api/v1/review",
        headers=headers,
        json=payload
    )
    return response.json()

# 5. 查询 GitHub 趋势
def get_github_trends(keywords: str):
    params = {
        "keywords": keywords,
        "language": "python"
    }

    response = requests.get(
        f"{API_BASE}/api/v1/intelligence/github",
        headers=headers,
        params=params
    )
    return response.json()

if __name__ == "__main__":
    # 示例使用
    print("=== 列出技能 ===")
    skills = list_skills()
    print(f"找到 {skills['total']} 个技能")

    print("\n=== 执行代码生成 ===")
    result = generate_code("创建一个 FastAPI 用户认证端点")
    print(f"成功: {result['success']}")

    print("\n=== 代码审查 ===")
    review = review_code("./src")
    print(f"总分: {review['overall_score']}")
