"""skill-templates 技能实现"""

import os
import json
from pathlib import Path


def list_templates():
    """列出可用模板"""
    template_dir = Path("skills/skill-templates/templates")
    templates = []
    
    if template_dir.exists():
        for template_type in template_dir.iterdir():
            if template_type.is_dir():
                templates.append({
                    "type": template_type.name,
                    "path": str(template_type)
                })
    
    return templates

def get_template_info(template_type):
    """获取模板详情"""
    template_dir = Path(f"skills/skill-templates/templates/{template_type}")
    
    if not template_dir.exists():
        return {"error": f"模板 {template_type} 不存在"}
    
    # 读取模板文件
    template_files = []
    for file in template_dir.iterdir():
        if file.is_file():
            template_files.append({
                "name": file.name,
                "path": str(file)
            })
    
    return {
        "template_type": template_type,
        "files": template_files
    }

def create_skill_from_template(template_type, skill_name, description):
    """基于模板创建新技能"""
    # 检查模板是否存在
    template_dir = Path(f"skills/skill-templates/templates/{template_type}")
    if not template_dir.exists():
        return {"error": f"模板 {template_type} 不存在"}
    
    # 创建技能目录
    skill_dir = Path(f"skills/{skill_name}")
    skill_dir.mkdir(exist_ok=True)
    
    # 复制模板文件
    for template_file in template_dir.iterdir():
        if template_file.is_file():
            # 读取模板内容
            content = template_file.read_text(encoding='utf-8')
            
            # 替换模板变量
            content = content.replace("{{SKILL_NAME}}", skill_name)
            content = content.replace("{{DESCRIPTION}}", description)
            content = content.replace("{{CLASS_NAME}}", skill_name.replace('-', ' ').title().replace(' ', ''))
            
            # 写入技能文件
            skill_file = skill_dir / template_file.name
            skill_file.write_text(content, encoding='utf-8')
    
    # 更新 skills.json
    update_skills_json(skill_name, description)
    
    return {"success": True, "skill_name": skill_name, "template_type": template_type}

def update_skills_json(skill_name, description):
    """更新 skills.json 文件"""
    with open("skills/skills.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 查找现有技能
    skill_index = next((i for i, s in enumerate(data['skills']) if s['name'] == skill_name), None)
    
    if skill_index is not None:
        # 更新现有技能
        data['skills'][skill_index]['description'] = description
    else:
        # 添加新技能
        new_skill = {
            "name": skill_name,
            "description": description,
            "path": f"skills/{skill_name}/SKILL.md",
            "triggers": [skill_name],
            "depends_on": []
        }
        data['skills'].append(new_skill)
    
    # 写回文件
    with open("skills/skills.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def execute_skill(params):
    """执行技能"""
    action = params.get('action', 'create')
    
    if action == 'list_templates':
        return {"templates": list_templates()}
    elif action == 'template_info':
        template_type = params.get('template_type')
        return get_template_info(template_type)
    elif action == 'create' or action is None:
        template_type = params.get('template_type')
        skill_name = params.get('skill_name')
        description = params.get('description', '')
        
        if not template_type or not skill_name:
            return {"error": "请指定模板类型和技能名称"}
        
        return create_skill_from_template(template_type, skill_name, description)
    else:
        return {"error": f"未知操作: {action}"}
