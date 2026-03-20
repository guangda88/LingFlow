"""skill-analytics 技能实现"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta


def analyze_skill(skill_name):
    """分析技能使用情况"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 模拟使用数据
    # 实际应用中，这里应该从数据库或日志文件中读取真实的使用数据
    usage_data = generate_mock_usage_data(skill_name)
    
    # 分析使用情况
    analysis = {
        "skill_name": skill_name,
        "total_usage": len(usage_data),
        "average_execution_time": sum(item["execution_time"] for item in usage_data) / len(usage_data) if usage_data else 0,
        "success_rate": sum(1 for item in usage_data if item["success"]) / len(usage_data) if usage_data else 0,
        "recent_usage": [item for item in usage_data if item["timestamp"] > (datetime.now() - timedelta(days=7)).isoformat()]
    }
    
    # 生成改进建议
    analysis["suggestions"] = generate_suggestions(analysis)
    
    return analysis

def analyze_all_skills():
    """分析所有技能"""
    # 加载 skills.json 文件
    with open("skills/skills.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 分析每个技能
    all_analysis = []
    for skill in data['skills']:
        skill_name = skill['name']
        analysis = analyze_skill(skill_name)
        if "error" not in analysis:
            all_analysis.append(analysis)
    
    # 按使用次数排序
    all_analysis.sort(key=lambda x: x["total_usage"], reverse=True)
    
    return {"skills": all_analysis}

def get_usage_trend(skill_name):
    """查看使用趋势"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 模拟使用数据
    usage_data = generate_mock_usage_data(skill_name)
    
    # 按日期分组
    trend = {}
    for item in usage_data:
        date = item["timestamp"].split('T')[0]
        if date not in trend:
            trend[date] = 0
        trend[date] += 1
    
    # 转换为列表并排序
    trend_list = [{"date": date, "count": count} for date, count in trend.items()]
    trend_list.sort(key=lambda x: x["date"])
    
    return {"skill_name": skill_name, "trend": trend_list}

def generate_performance_report(skill_name):
    """生成性能报告"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 模拟使用数据
    usage_data = generate_mock_usage_data(skill_name)
    
    # 分析性能数据
    if not usage_data:
        return {"error": "没有性能数据"}
    
    execution_times = [item["execution_time"] for item in usage_data]
    performance = {
        "skill_name": skill_name,
        "average_execution_time": sum(execution_times) / len(execution_times),
        "min_execution_time": min(execution_times),
        "max_execution_time": max(execution_times),
        "median_execution_time": sorted(execution_times)[len(execution_times) // 2],
        "success_rate": sum(1 for item in usage_data if item["success"]) / len(usage_data)
    }
    
    # 生成性能评级
    if performance["average_execution_time"] < 0.5:
        performance["performance_rating"] = "优秀"
    elif performance["average_execution_time"] < 1:
        performance["performance_rating"] = "良好"
    else:
        performance["performance_rating"] = "一般"
    
    return performance

def generate_mock_usage_data(skill_name):
    """生成模拟使用数据"""
    # 生成过去30天的模拟数据
    usage_data = []
    for i in range(30):
        # 每天生成1-5次使用记录
        for j in range(1, 6):
            timestamp = (datetime.now() - timedelta(days=i)).isoformat()
            execution_time = 0.1 + (j * 0.1)  # 执行时间从0.2到0.6秒
            success = j != 5  # 第5次执行模拟失败
            
            usage_data.append({
                "timestamp": timestamp,
                "execution_time": execution_time,
                "success": success,
                "params": {"test": "data"}
            })
    
    return usage_data

def generate_suggestions(analysis):
    """生成改进建议"""
    suggestions = []
    
    if analysis["average_execution_time"] > 1:
        suggestions.append("执行时间较长，建议优化代码结构或使用异步处理")
    
    if analysis["success_rate"] < 0.9:
        suggestions.append("成功率较低，建议加强错误处理和边界情况测试")
    
    if len(analysis["recent_usage"]) < 5:
        suggestions.append("近期使用频率较低，建议检查技能是否满足用户需求")
    
    if not suggestions:
        suggestions.append("技能运行良好，继续保持")
    
    return suggestions

def execute_skill(params):
    """执行技能"""
    action = params.get('action', 'analyze')
    skill_name = params.get('skill_name')
    
    if action == 'analyze':
        if not skill_name:
            return {"error": "请指定技能名称"}
        return analyze_skill(skill_name)
    elif action == 'analyze_all':
        return analyze_all_skills()
    elif action == 'usage_trend':
        if not skill_name:
            return {"error": "请指定技能名称"}
        return get_usage_trend(skill_name)
    elif action == 'performance':
        if not skill_name:
            return {"error": "请指定技能名称"}
        return generate_performance_report(skill_name)
    else:
        return {"error": f"未知操作: {action}"}
