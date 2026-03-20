"""task-runner 技能实现"""

import os
import json
from pathlib import Path


def run_task(skill_name, params):
    """执行单个任务"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 检查技能实现文件是否存在
    implementation_file = skill_dir / "implementation.py"
    if not implementation_file.exists():
        return {"error": f"技能 {skill_name} 缺少实现文件"}
    
    # 导入技能模块
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(skill_name, str(implementation_file))
        skill_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(skill_module)
    except Exception as e:
        return {"error": f"导入技能模块失败: {str(e)}"}
    
    # 检查技能模块是否有 execute_skill 函数
    if not hasattr(skill_module, "execute_skill"):
        return {"error": f"技能 {skill_name} 缺少 execute_skill 函数"}
    
    # 执行技能
    try:
        result = skill_module.execute_skill(params)
        return result
    except Exception as e:
        return {"error": f"执行技能失败: {str(e)}"}

def run_tasks(tasks):
    """执行多个任务"""
    results = []
    
    for task in tasks:
        skill_name = task.get("skill")
        params = task.get("params", {})
        
        if not skill_name:
            results.append({"error": "任务缺少 skill 字段"})
            continue
        
        result = run_task(skill_name, params)
        results.append(result)
    
    return {"results": results}

def execute_skill(params):
    """执行技能"""
    skill = params.get('skill')
    task_params = params.get('params', {})
    tasks = params.get('tasks')
    
    if skill:
        return run_task(skill, task_params)
    elif tasks:
        return run_tasks(tasks)
    else:
        return {"error": "请指定要执行的技能或任务列表"}
