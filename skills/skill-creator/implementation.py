"""Skill Creator 技能实现"""

import os
import json
from pathlib import Path


def create_skill(skill_name, description, triggers=None, depends_on=None):
    """创建新技能"""
    # 创建技能目录
    skill_dir = Path(f"skills/{skill_name}")
    skill_dir.mkdir(exist_ok=True)
    
    # 创建 SKILL.md 文件
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(f"# {skill_name} 技能\n\n## 技能概述\n\n{description}\n\n## 功能特性\n\n- 功能 1\n- 功能 2\n\n## 使用场景\n\n- 使用场景 1\n- 使用场景 2\n\n## 触发条件\n\n{chr(10).join([f"- `{t}`" for t in (triggers or [])])}\n\n## 依赖关系\n\n{chr(10).join([f"- `{d}`" for d in (depends_on or [])])}\n")
    
    # 创建 __init__.py 文件
    init_py = skill_dir / "__init__.py"
    init_py.write_text(f"""{skill_name} 技能初始化""")
    
    # 更新 skills.json
    update_skills_json(skill_name, description, triggers or [], depends_on or [])
    
    return f"技能 {skill_name} 创建成功"


def modify_skill(skill_name, description=None, triggers=None, depends_on=None):
    """修改现有技能"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return f"技能 {skill_name} 不存在"
    
    # 更新 SKILL.md 文件
    if description:
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text()
        # 简单的替换逻辑，实际应用中可能需要更复杂的处理
        if "## 技能概述" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line == "## 技能概述":
                    # 替换下一行的描述
                    if i + 1 < len(lines) and lines[i + 1].strip() == "":
                        if i + 2 < len(lines):
                            lines[i + 2] = description
            content = '\n'.join(lines)
            skill_md.write_text(content)
    
    # 更新 skills.json
    update_skills_json(skill_name, description, triggers, depends_on)
    
    return f"技能 {skill_name} 修改成功"


def validate_skill(skill_name):
    """验证技能配置"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return f"技能 {skill_name} 不存在"
    
    # 检查 SKILL.md 文件
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return f"技能 {skill_name} 缺少 SKILL.md 文件"
    
    # 检查 skills.json 中的配置
    with open("skills/skills.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    skill_config = next((s for s in data['skills'] if s['name'] == skill_name), None)
    if not skill_config:
        return f"技能 {skill_name} 未在 skills.json 中注册"
    
    return f"技能 {skill_name} 配置验证通过"


def update_skills_json(skill_name, description=None, triggers=None, depends_on=None):
    """更新 skills.json 文件"""
    with open("skills/skills.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 查找现有技能
    skill_index = next((i for i, s in enumerate(data['skills']) if s['name'] == skill_name), None)
    
    if skill_index is not None:
        # 更新现有技能
        if description:
            data['skills'][skill_index]['description'] = description
        if triggers is not None:
            data['skills'][skill_index]['triggers'] = triggers
        if depends_on is not None:
            data['skills'][skill_index]['depends_on'] = depends_on
    else:
        # 添加新技能
        new_skill = {
            "name": skill_name,
            "description": description or "",
            "path": f"skills/{skill_name}/SKILL.md",
            "triggers": triggers or [],
            "depends_on": depends_on or []
        }
        data['skills'].append(new_skill)
    
    # 写回文件
    with open("skills/skills.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def execute_skill(params):
    """执行技能"""
    action = params.get('action')
    skill_name = params.get('skill_name')
    
    if action == 'create':
        description = params.get('description', '')
        triggers = params.get('triggers', [])
        depends_on = params.get('depends_on', [])
        return create_skill(skill_name, description, triggers, depends_on)
    elif action == 'modify':
        description = params.get('description')
        triggers = params.get('triggers')
        depends_on = params.get('depends_on')
        return modify_skill(skill_name, description, triggers, depends_on)
    elif action == 'validate':
        return validate_skill(skill_name)
    else:
        return f"未知操作: {action}"
