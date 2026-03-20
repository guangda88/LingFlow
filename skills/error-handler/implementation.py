"""error-handler 技能实现"""

import os
import json
import time


def execute_with_error_handling(params):
    """执行带错误处理的任务"""
    task = params.get('task')
    retries = params.get('retries', 0)
    retry_interval = params.get('retry_interval', 1)
    fallback = params.get('fallback')
    
    # 验证参数
    if not task:
        return {"error": "请指定要执行的任务"}
    
    skill_name = task.get('skill')
    task_params = task.get('params', {})
    
    if not skill_name:
        return {"error": "任务缺少 skill 字段"}
    
    # 执行任务，支持重试
    attempt = 0
    last_error = None
    
    while attempt <= retries:
        print(f"执行任务 (尝试 {attempt}/{retries}): {skill_name}")
        
        try:
            # 模拟执行任务
            # 实际应用中，这里应该调用 task-runner 技能
            result = simulate_task_execution(skill_name, task_params, attempt)
            
            # 检查任务是否成功
            if "error" not in result:
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt + 1
                }
            else:
                last_error = result["error"]
                print(f"任务执行失败: {last_error}")
        except Exception as e:
            last_error = str(e)
            print(f"任务执行异常: {last_error}")
        
        # 重试
        if attempt < retries:
            print(f"等待 {retry_interval} 秒后重试...")
            time.sleep(retry_interval)
            attempt += 1
        else:
            break
    
    # 执行降级策略
    if fallback:
        print("执行降级策略")
        fallback_skill = fallback.get('skill')
        fallback_params = fallback.get('params', {})
        
        if fallback_skill:
            try:
                # 模拟执行降级任务
                fallback_result = simulate_task_execution(fallback_skill, fallback_params, 0)
                return {
                    "success": True,
                    "result": fallback_result,
                    "attempts": retries + 1,
                    "fallback": True
                }
            except Exception as e:
                return {
                    "error": f"任务执行失败且降级策略也失败: {last_error}, 降级错误: {str(e)}",
                    "attempts": retries + 1
                }
    
    # 所有尝试都失败
    return {
        "error": f"任务执行失败: {last_error}",
        "attempts": retries + 1
    }

def simulate_task_execution(skill_name, params, attempt):
    """模拟任务执行"""
    # 模拟任务执行
    # 实际应用中，这里应该调用真实的任务执行
    
    # 模拟一些任务失败的情况
    if skill_name == "flaky-service" and attempt < 2:
        return {"error": "服务暂时不可用"}
    elif skill_name == "always-fail":
        return {"error": "任务总是失败"}
    
    # 模拟成功执行
    return {
        "success": True,
        "message": f"任务 {skill_name} 执行成功",
        "params": params
    }

def execute_skill(params):
    """执行技能"""
    return execute_with_error_handling(params)
