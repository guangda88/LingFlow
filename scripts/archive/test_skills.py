#!/usr/bin/env python3
"""测试技能"""

import json
from lingflow import LingFlow

lf = LingFlow()

# 测试 code-analysis 技能
print("测试 code-analysis 技能...")
params = {
    "target": "./lingflow/",
    "metrics": ["complexity", "duplication", "dead_code"]
}
result = lf.run_skill("code-analysis", params)
print(json.dumps(result, indent=2, ensure_ascii=False))
print("\n")

# 测试 code-optimizer 技能
print("测试 code-optimizer 技能...")
optimizer_params = {
    "issues": {
        "duplication_rate": 0.2,
        "dead_code": [{"file": "file.py", "issues": ["未使用的函数: test"]}],
        "complexity": {"file.py": 10}
    },
    "strategy": "refactor_duplicates"
}
optimizer_result = lf.run_skill("code-optimizer", optimizer_params)
print(json.dumps(optimizer_result, indent=2, ensure_ascii=False))
print("\n")

# 测试 test-runner 技能
print("测试 test-runner 技能...")
test_params = {
    "file": "./lingflow",
    "test_type": "unit"
}
test_result = lf.run_skill("test-runner", test_params)
print(json.dumps(test_result, indent=2, ensure_ascii=False))
print("\n")

# 测试 notification 技能
print("测试 notification 技能...")
notification_params = {
    "message": "测试通知",
    "level": "info"
}
notification_result = lf.run_skill("notification", notification_params)
print(json.dumps(notification_result, indent=2, ensure_ascii=False))
print("\n")

# 测试 code-review 技能
print("测试 code-review 技能...")
review_params = {
    "focus": "duplicate_code",
    "files": ["./lingflow/"]
}
review_result = lf.run_skill("code-review", review_params)
print(json.dumps(review_result, indent=2, ensure_ascii=False))
