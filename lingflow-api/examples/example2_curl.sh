"""
示例 2: cURL 使用 lingflow API
"""

API_BASE="http://localhost:8000"
API_KEY="dev-key-12345"

# 1. 列出所有技能
echo "=== 列出技能 ==="
curl -X GET "$API_BASE/api/v1/skills" \
  -H "X-API-Key: $API_KEY"

# 2. 获取技能详情
echo -e "\n=== 获取技能详情 ==="
curl -X GET "$API_BASE/api/v1/skills/code-generation" \
  -H "X-API-Key: $API_KEY"

# 3. 执行技能
echo -e "\n=== 执行技能 ==="
curl -X POST "$API_BASE/api/v1/skills/code-generation/execute" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "prompt": "创建一个 REST API",
      "language": "python"
    },
    "timeout": 60
  }'

# 4. 批量执行技能
echo -e "\n=== 批量执行技能 ==="
curl -X POST "$API_BASE/api/v1/skills/batch" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"name": "code-review", "params": {"target": "./src"}},
      {"name": "test-generation", "params": {"target": "./src"}}
    ],
    "max_workers": 2
  }'

# 5. 代码审查
echo -e "\n=== 代码审查 ==="
curl -X POST "$API_BASE/api/v1/review" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "target_path": "./src",
    "dimensions": ["complexity", "security", "style"],
    "output_format": "json"
  }'

# 6. GitHub 趋势
echo -e "\n=== GitHub 趋势 ==="
curl -X GET "$API_BASE/api/v1/intelligence/github?keywords=python,ai&language=python" \
  -H "X-API-Key: $API_KEY"

# 7. 查看指标
echo -e "\n=== Prometheus 指标 ==="
curl -X GET "$API_BASE/metrics" \
  -H "X-API-Key: $API_KEY"
