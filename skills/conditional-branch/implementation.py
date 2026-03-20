"""conditional-branch 技能实现"""

import os
import json
import re


def execute_conditional_branch(params):
    """执行条件分支"""
    condition = params.get('condition')
    branches = params.get('branches', [])
    default_branch = params.get('default_branch', [])
    variables = params.get('variables', {})
    
    # 验证参数
    if not branches:
        return {"error": "请指定分支配置"}
    
    # 执行条件判断
    executed_branch = None
    branch_results = []
    
    for branch in branches:
        branch_condition = branch.get('condition')
        branch_tasks = branch.get('tasks', [])
        
        if not branch_condition:
            continue
        
        # 替换变量
        evaluated_condition = replace_variables(branch_condition, variables)
        
        # 评估条件
        try:
            condition_result = evaluate_condition(evaluated_condition)
        except Exception as e:
            return {"error": f"条件表达式评估失败: {str(e)}"}
        
        if condition_result:
            # 执行分支任务
            executed_branch = branch_condition
            
            # 模拟执行任务
            # 实际应用中，这里应该调用 task-runner 技能
            for task in branch_tasks:
                skill_name = task.get("skill")
                task_params = task.get("params", {})
                print(f"执行分支任务: {skill_name}, 参数: {task_params}")
                branch_results.append({"skill": skill_name, "result": "执行成功"})
            
            break
    
    # 如果没有分支被执行，执行默认分支
    if not executed_branch and default_branch:
        executed_branch = "default"
        for task in default_branch:
            skill_name = task.get("skill")
            task_params = task.get("params", {})
            print(f"执行默认分支任务: {skill_name}, 参数: {task_params}")
            branch_results.append({"skill": skill_name, "result": "执行成功"})
    
    return {
        "success": True,
        "executed_branch": executed_branch,
        "branch_results": branch_results
    }

def replace_variables(condition, variables):
    """替换条件表达式中的变量"""
    # 查找 ${var} 格式的变量
    pattern = r"\$\{([^}]+)\}"
    
    def replace_var(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))
    
    return re.sub(pattern, replace_var, condition)

def evaluate_condition(condition):
    """评估条件表达式"""
    # 简单的条件表达式评估
    # 实际应用中，可能需要更复杂的表达式解析器
    try:
        # 安全评估条件表达式
        # 注意：这里使用 eval 存在安全风险，实际应用中应该使用更安全的表达式评估方法
        return bool(eval(condition))
    except Exception as e:
        raise Exception(f"条件表达式评估错误: {str(e)}")

def execute_skill(params):
    """执行技能"""
    return execute_conditional_branch(params)
