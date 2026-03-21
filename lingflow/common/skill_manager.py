"""LingFlow 技能管理模块"""

import os
import importlib.util
import re
from typing import Dict, List, Optional, Any
from lingflow.common.config import get_config
from lingflow.common.exceptions import SkillNotFoundError, SkillLoadError

class SkillManager:
    """技能管理器"""
    
    def __init__(self):
        self.skills_path = get_config('skills.path', 'skills')
        self.skills_cache: Dict[str, Any] = {}
        self.skill_metadata: Dict[str, Dict[str, Any]] = {}
        self._load_skills_metadata()
    
    def _load_skills_metadata(self):
        """加载所有技能的元数据"""
        if not os.path.exists(self.skills_path):
            return
        
        for skill_name in os.listdir(self.skills_path):
            skill_dir = os.path.join(self.skills_path, skill_name)
            if not os.path.isdir(skill_dir):
                continue
            
            # 加载 SKILL.md 文件
            skill_md_path = os.path.join(skill_dir, 'SKILL.md')
            if os.path.exists(skill_md_path):
                try:
                    with open(skill_md_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    metadata = self._parse_skill_md(content)
                    self.skill_metadata[skill_name] = metadata
                except Exception as e:
                    print(f"加载技能 {skill_name} 的元数据失败: {str(e)}")
    
    def _parse_skill_md(self, content: str) -> Dict[str, Any]:
        """解析 SKILL.md 文件"""
        metadata = {}
        lines = content.strip().split('\n')
        
        # 解析基本信息
        for line in lines:
            line = line.strip()
            if line.startswith('name:'):
                metadata['name'] = line.split(':', 1)[1].strip()
            elif line.startswith('description:'):
                metadata['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('version:'):
                metadata['version'] = line.split(':', 1)[1].strip()
            elif line.startswith('dependencies:'):
                metadata['dependencies'] = []
            elif metadata.get('dependencies') is not None and line.strip().startswith('-'):
                metadata['dependencies'].append(line.strip().lstrip('- '))
        
        return metadata
    
    def get_skill_path(self, skill_name: str) -> Optional[str]:
        """获取技能文件路径"""
        # 验证技能名称
        if not skill_name or not re.match(r'^[a-zA-Z0-9_-]+$', skill_name):
            return None
        
        # 构建技能路径
        skill_path = os.path.join(self.skills_path, skill_name, 'implementation.py')
        
        # 安全检查：确保路径在 skills 目录内
        skills_dir = os.path.abspath(self.skills_path)
        skill_path_abs = os.path.abspath(skill_path)
        
        if not skill_path_abs.startswith(skills_dir):
            return None
        
        return skill_path if os.path.exists(skill_path) else None
    
    def load_skill(self, skill_name: str) -> Any:
        """加载技能模块"""
        # 检查缓存
        if skill_name in self.skills_cache:
            return self.skills_cache[skill_name]
        
        # 获取技能路径
        skill_path = self.get_skill_path(skill_name)
        if not skill_path:
            raise SkillNotFoundError(f"技能 {skill_name} 不存在")
        
        # 检查依赖
        self._check_dependencies(skill_name)
        
        # 加载技能模块
        try:
            spec = importlib.util.spec_from_file_location(f"skills.{skill_name}.implementation", skill_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 缓存技能模块
            self.skills_cache[skill_name] = module
            return module
        except Exception as e:
            raise SkillLoadError(f"加载技能 {skill_name} 失败: {str(e)}")
    
    def _check_dependencies(self, skill_name: str):
        """检查技能依赖"""
        metadata = self.skill_metadata.get(skill_name, {})
        dependencies = metadata.get('dependencies', [])
        
        for dep in dependencies:
            if not self.get_skill_path(dep):
                raise SkillNotFoundError(f"技能 {skill_name} 的依赖 {dep} 不存在")
            # 递归加载依赖
            self.load_skill(dep)
    
    def list_skills(self) -> List[str]:
        """列出所有可用技能"""
        skills = []
        if not os.path.exists(self.skills_path):
            return skills
        
        for skill_name in os.listdir(self.skills_path):
            skill_dir = os.path.join(self.skills_path, skill_name)
            if os.path.isdir(skill_dir) and os.path.exists(os.path.join(skill_dir, 'implementation.py')):
                skills.append(skill_name)
        
        return skills
    
    def get_skill_metadata(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取技能元数据"""
        return self.skill_metadata.get(skill_name)

# 创建全局技能管理器实例
skill_manager = SkillManager()

# 导出函数
def load_skill(skill_name: str) -> Any:
    """加载技能"""
    return skill_manager.load_skill(skill_name)

def get_skill_path(skill_name: str) -> Optional[str]:
    """获取技能路径"""
    return skill_manager.get_skill_path(skill_name)

def list_skills() -> List[str]:
    """列出所有技能"""
    return skill_manager.list_skills()

def get_skill_metadata(skill_name: str) -> Optional[Dict[str, Any]]:
    """获取技能元数据"""
    return skill_manager.get_skill_metadata(skill_name)
