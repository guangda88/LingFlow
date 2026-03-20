from lingflow import LingFlow

lf = LingFlow()

# 测试code-analysis技能
params = {
    "target": "./lingflow/",
    "metrics": ["complexity", "duplication", "dead_code"]
}

result = lf.run_skill("code-analysis", params)
print(result)