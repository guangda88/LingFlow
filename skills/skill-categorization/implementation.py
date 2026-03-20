"""skill-categorization 技能实现"""

import os
import json
from pathlib import Path


def categorize_skill(skill_name, category):
    """为技能添加分类"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 加载 skills.json 文件
    with open("skills/skills.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 查找技能
    skill_index = next((i for i, s in enumerate(data['skills']) if s['name'] == skill_name), None)
    if skill_index is None:
        return {"error": f"技能 {skill_name} 未在 skills.json 中注册"}
    
    # 添加分类信息
    if 'category' not in data['skills'][skill_index]:
        data['skills'][skill_index]['category'] = category
    else:
        data['skills'][skill_index]['category'] = category
    
    # 写回 skills.json 文件
    with open("skills/skills.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return {"success": True, "skill_name": skill_name, "category": category}

def list_categories():
    """查看分类列表"""
    # 加载 skills.json 文件
    with open("skills/skills.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取所有分类
    categories = set()
    for skill in data['skills']:
        if 'category' in skill:
            categories.add(skill['category'])
    
    # 转换为列表并排序
    categories = sorted(list(categories))
    
    return {"categories": categories}

def get_skills_by_category(category):
    """按分类查询技能"""
    # 加载 skills.json 文件
    with open("skills/skills.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取指定分类的技能
    skills = []
    for skill in data['skills']:
        if 'category' in skill and skill['category'] == category:
            skills.append({
                "name": skill['name'],
                "description": skill['description']
            })
    
    return {"category": category, "skills": skills}

def get_category_stats():
    """生成分类统计"""
    # 加载 skills.json 文件
    with open("skills/skills.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 统计各分类的技能数量
    stats = {}
    for skill in data['skills']:
        category = skill.get('category', '未分类')
        if category not in stats:
            stats[category] = 0
        stats[category] += 1
    
    # 转换为列表并排序
    stats_list = [{
        "category": category,
        "count": count
    } for category, count in stats.items()]
    stats_list.sort(key=lambda x: x["count"], reverse=True)
    
    return {"stats": stats_list}

def execute_skill(params):
    """执行技能"""
    action = params.get('action', 'categorize')
    
    if action == 'categorize':
        skill_name = params.get('skill_name')
        category = params.get('category')
        
        if not skill_name or not category:
            return {"error": "请指定技能名称和分类"}
        
        return categorize_skill(skill_name, category)
    elif action == 'list_categories':
        return list_categories()
    elif action == 'skills_by_category':
        category = params.get('category')
        
        if not category:
            return {"error": "请指定分类"}
        
        return get_skills_by_category(category)
    elif action == 'category_stats':
        return get_category_stats()
    else:
        return {"error": f"未知操作: {action}"}
