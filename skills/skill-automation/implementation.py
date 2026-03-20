"""skill-automation 技能实现"""

import os
import json
from pathlib import Path


def generate_skill(skill_name, description, skill_type):
    """自动生成技能"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if skill_dir.exists():
        return {"error": f"技能 {skill_name} 已存在"}
    
    # 检查模板是否存在
    template_dir = Path(f"skills/skill-templates/templates/{skill_type}")
    if not template_dir.exists():
        return {"error": f"模板 {skill_type} 不存在"}
    
    # 创建技能目录
    skill_dir.mkdir()
    
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
    
    return {"success": True, "skill_name": skill_name, "skill_type": skill_type}

def batch_generate_skills(skills):
    """批量生成技能"""
    results = []
    
    for skill in skills:
        skill_name = skill.get('name')
        description = skill.get('description', '')
        skill_type = skill.get('type', 'api-skill')
        
        result = generate_skill(skill_name, description, skill_type)
        results.append(result)
    
    return {"results": results}

def generate_tests(skill_name):
    """生成技能测试"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 创建测试目录
    test_dir = skill_dir / "tests"
    test_dir.mkdir(exist_ok=True)
    
    # 生成测试文件
    test_file = test_dir / "test_skill.py"
    test_content = f"""测试 {skill_name} 技能"""
    test_content += f"\n\nimport unittest\nfrom skills.{skill_name}.implementation import execute_skill\n\n"
    test_content += f"class Test{skill_name.replace('-', ' ').title().replace(' ', '')}(unittest.TestCase):\n"
    test_content += f"    \"\"\"测试 {skill_name} 技能\"\"\"\n\n"
    test_content += f"    def test_basic_execution(self):\n"
    test_content += f"        \"\"\"测试基本执行\"\"\"\n"
    test_content += f"        params = {{}}\n"
    test_content += f"        result = execute_skill(params)\n"
    test_content += f"        self.assertIn('success', result)\n\n"
    test_content += f"    def test_error_handling(self):\n"
    test_content += f"        \"\"\"测试错误处理\"\"\"\n"
    test_content += f"        params = {{'test': 'error'}}\n"
    test_content += f"        result = execute_skill(params)\n"
    test_content += f"        self.assertIn('success', result)\n\n"
    test_content += f"if __name__ == '__main__':\n"
    test_content += f"    unittest.main()\n"
    
    test_file.write_text(test_content, encoding='utf-8')
    
    return {"success": True, "skill_name": skill_name, "test_path": str(test_file)}

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
    action = params.get('action', 'generate')
    
    if action == 'generate':
        skill_name = params.get('skill_name')
        description = params.get('description', '')
        skill_type = params.get('skill_type', 'api-skill')
        
        if not skill_name:
            return {"error": "请指定技能名称"}
        
        return generate_skill(skill_name, description, skill_type)
    elif action == 'batch_generate':
        skills = params.get('skills', [])
        
        if not skills:
            return {"error": "请指定要生成的技能列表"}
        
        return batch_generate_skills(skills)
    elif action == 'generate_tests':
        skill_name = params.get('skill_name')
        
        if not skill_name:
            return {"error": "请指定技能名称"}
        
        return generate_tests(skill_name)
    else:
        return {"error": f"未知操作: {action}"}
