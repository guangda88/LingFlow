"""workflow-executor 技能实现"""

import os
import json
import yaml
from pathlib import Path


def execute_workflow_file(workflow_file):
    """执行工作流文件"""
    # 检查文件是否存在
    file = Path(workflow_file)
    if not file.exists():
        return {"error": f"工作流文件 {workflow_file} 不存在"}
    
    # 读取文件内容
    try:
        with open(file, 'r', encoding='utf-8') as f:
            if file.suffix == '.yaml' or file.suffix == '.yml':
                workflow = yaml.safe_load(f)
            elif file.suffix == '.json':
                workflow = json.load(f)
            else:
                return {"error": "不支持的文件格式，仅支持 YAML 和 JSON"}
    except Exception as e:
        return {"error": f"读取工作流文件失败: {str(e)}"}
    
    # 执行工作流
    return execute_workflow(workflow)

def execute_workflow(workflow):
    """执行工作流配置"""
    # 验证工作流配置
    if not isinstance(workflow, dict):
        return {"error": "工作流配置必须是字典格式"}
    
    if "tasks" not in workflow:
        return {"error": "工作流配置中缺少 tasks 字段"}
    
    # 提取任务
    tasks = workflow.get("tasks", [])
    
    # 构建任务依赖关系
    task_map = {}
    for task in tasks:
        task_name = task.get("name")
        if not task_name:
            return {"error": "任务缺少 name 字段"}
        task_map[task_name] = task
    
    # 检查依赖关系
    for task_name, task in task_map.items():
        depends_on = task.get("depends_on", [])
        for dep in depends_on:
            if dep not in task_map:
                return {"error": f"任务 {task_name} 依赖的任务 {dep} 不存在"}
    
    # 执行任务
    executed_tasks = set()
    task_results = {}
    
    while len(executed_tasks) < len(tasks):
        # 找出可执行的任务（所有依赖都已执行）
        executable_tasks = []
        for task_name, task in task_map.items():
            if task_name not in executed_tasks:
                depends_on = task.get("depends_on", [])
                if all(dep in executed_tasks for dep in depends_on):
                    executable_tasks.append(task)
        
        if not executable_tasks:
            return {"error": "无法解析任务依赖关系，可能存在循环依赖"}
        
        # 执行任务
        for task in executable_tasks:
            task_name = task.get("name")
            skill_name = task.get("skill")
            params = task.get("params", {})
            
            if not skill_name:
                return {"error": f"任务 {task_name} 缺少 skill 字段"}
            
            # 执行任务（这里应该调用 task-runner 技能）
            # 模拟执行
            print(f"执行任务: {task_name}, 技能: {skill_name}, 参数: {params}")
            
            # 模拟执行结果
            task_results[task_name] = {
                "success": True,
                "result": f"任务 {task_name} 执行成功"
            }
            
            # 标记任务为已执行
            executed_tasks.add(task_name)
    
    return {
        "success": True,
        "workflow_name": workflow.get("name", "unnamed"),
        "task_results": task_results
    }

def execute_skill(params):
    """执行技能"""
    workflow_file = params.get('workflow_file')
    workflow = params.get('workflow')
    
    if workflow_file:
        return execute_workflow_file(workflow_file)
    elif workflow:
        return execute_workflow(workflow)
    else:
        return {"error": "请指定工作流文件或工作流配置"}
