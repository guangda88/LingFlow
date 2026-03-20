"""loop-iterator 技能实现"""

import os
import json
import re


def execute_loop(params):
    """执行循环"""
    items = params.get('items', [])
    tasks = params.get('tasks', [])
    max_iterations = params.get('max_iterations', 1000)
    
    # 验证参数
    if not items:
        return {"error": "请指定要遍历的数据集"}
    if not tasks:
        return {"error": "请指定要执行的任务"}
    
    # 限制循环次数
    if len(items) > max_iterations:
        items = items[:max_iterations]
    
    # 执行循环
    results = []
    
    for i, item in enumerate(items):
        iteration_results = []
        
        for task in tasks:
            skill_name = task.get("skill")
            task_params = task.get("params", {})
            
            # 替换任务参数中的变量
            resolved_params = resolve_variables(task_params, item, i)
            
            # 模拟执行任务
            # 实际应用中，这里应该调用 task-runner 技能
            print(f"执行循环任务: {skill_name}, 参数: {resolved_params}, 索引: {i}")
            iteration_results.append({"skill": skill_name, "result": "执行成功"})
        
        results.append({"index": i, "item": item, "results": iteration_results})
    
    return {
        "success": True,
        "loop_count": len(results),
        "results": results
    }

def resolve_variables(params, item, index):
    """解析参数中的变量"""
    if isinstance(params, dict):
        resolved = {}
        for key, value in params.items():
            resolved[key] = resolve_variables(value, item, index)
        return resolved
    elif isinstance(params, list):
        resolved = []
        for value in params:
            resolved.append(resolve_variables(value, item, index))
        return resolved
    elif isinstance(params, str):
        # 替换 ${item} 和 ${index} 变量
        resolved = params.replace("${index}", str(index))
        
        # 替换 ${item} 和 ${item.property} 变量
        pattern = r"\$\{item(\.([^}]+))?\}"
        
        def replace_item(match):
            if match.group(2):
                # 处理 ${item.property} 格式
                property_name = match.group(2)
                if isinstance(item, dict) and property_name in item:
                    return str(item[property_name])
                else:
                    return match.group(0)
            else:
                # 处理 ${item} 格式
                return str(item)
        
        resolved = re.sub(pattern, replace_item, resolved)
        return resolved
    else:
        return params

def execute_skill(params):
    """执行技能"""
    return execute_loop(params)
