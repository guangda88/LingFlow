"""skill-versioning 技能实现"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime


def create_version(skill_name, version, changes):
    """创建新版本"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 创建版本目录
    versions_dir = skill_dir / "versions"
    versions_dir.mkdir(exist_ok=True)
    
    # 创建版本子目录
    version_dir = versions_dir / f"v{version}"
    if version_dir.exists():
        return {"error": f"版本 v{version} 已存在"}
    version_dir.mkdir()
    
    # 复制当前技能文件到版本目录
    for file in skill_dir.iterdir():
        if file.is_file() and file.name not in ["CHANGELOG.md"] and not file.name.startswith("."):
            shutil.copy2(file, version_dir)
    
    # 更新变更日志
    update_changelog(skill_dir, version, changes)
    
    # 更新当前版本链接
    update_current_version(skill_dir, version)
    
    return {"success": True, "version": f"v{version}"}

def rollback_version(skill_name, version):
    """回滚到历史版本"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 检查版本是否存在
    version_dir = skill_dir / "versions" / f"v{version}"
    if not version_dir.exists():
        return {"error": f"版本 v{version} 不存在"}
    
    # 复制版本文件到技能目录
    for file in version_dir.iterdir():
        if file.is_file():
            shutil.copy2(file, skill_dir)
    
    # 更新当前版本链接
    update_current_version(skill_dir, version)
    
    return {"success": True, "version": f"v{version}"}

def get_version_history(skill_name):
    """查看版本历史"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 检查版本目录是否存在
    versions_dir = skill_dir / "versions"
    if not versions_dir.exists():
        return {"versions": []}
    
    # 获取版本列表
    versions = []
    for version_dir in versions_dir.iterdir():
        if version_dir.is_dir():
            versions.append({
                "version": version_dir.name,
                "created_at": datetime.fromtimestamp(version_dir.stat().st_ctime).isoformat()
            })
    
    # 按版本号排序
    versions.sort(key=lambda x: x["version"])
    
    return {"versions": versions}

def generate_changelog(skill_name):
    """生成变更日志"""
    # 检查技能是否存在
    skill_dir = Path(f"skills/{skill_name}")
    if not skill_dir.exists():
        return {"error": f"技能 {skill_name} 不存在"}
    
    # 检查变更日志文件是否存在
    changelog_file = skill_dir / "CHANGELOG.md"
    if not changelog_file.exists():
        return {"error": "变更日志文件不存在"}
    
    # 读取变更日志
    changelog = changelog_file.read_text(encoding='utf-8')
    
    return {"changelog": changelog}

def update_changelog(skill_dir, version, changes):
    """更新变更日志"""
    changelog_file = skill_dir / "CHANGELOG.md"
    
    # 生成变更日志条目
    today = datetime.now().strftime("%Y-%m-%d")
    changelog_entry = f"## v{version} ({today})\n\n"
    changelog_entry += f"### 变更\n"
    changelog_entry += f"- {changes}\n\n"
    
    # 如果变更日志文件存在，读取现有内容
    if changelog_file.exists():
        existing_content = changelog_file.read_text(encoding='utf-8')
        # 检查是否已经有 # CHANGELOG 标题
        if existing_content.startswith("# CHANGELOG"):
            # 在标题后插入新条目
            new_content = "# CHANGELOG\n\n" + changelog_entry + existing_content.split("# CHANGELOG\n\n", 1)[1]
        else:
            # 添加标题和新条目
            new_content = "# CHANGELOG\n\n" + changelog_entry + existing_content
    else:
        # 创建新的变更日志文件
        new_content = "# CHANGELOG\n\n" + changelog_entry
    
    # 写回变更日志文件
    changelog_file.write_text(new_content, encoding='utf-8')

def update_current_version(skill_dir, version):
    """更新当前版本链接"""
    # 在Windows上，创建一个current目录来模拟符号链接
    current_dir = skill_dir / "current"
    if current_dir.exists():
        if current_dir.is_dir():
            shutil.rmtree(current_dir)
        else:
            current_dir.unlink()
    
    # 创建current目录
    current_dir.mkdir()
    
    # 复制版本文件到current目录
    version_dir = skill_dir / "versions" / f"v{version}"
    for file in version_dir.iterdir():
        if file.is_file():
            shutil.copy2(file, current_dir)

def execute_skill(params):
    """执行技能"""
    action = params.get('action', 'create')
    skill_name = params.get('skill_name')
    
    if not skill_name:
        return {"error": "请指定技能名称"}
    
    if action == 'create':
        version = params.get('version')
        changes = params.get('changes', '无变更记录')
        
        if not version:
            return {"error": "请指定版本号"}
        
        return create_version(skill_name, version, changes)
    elif action == 'rollback':
        version = params.get('version')
        
        if not version:
            return {"error": "请指定要回滚的版本号"}
        
        return rollback_version(skill_name, version)
    elif action == 'history':
        return get_version_history(skill_name)
    elif action == 'changelog':
        return generate_changelog(skill_name)
    else:
        return {"error": f"未知操作: {action}"}
