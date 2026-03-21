"""LingFlow 统一入口"""

from typing import Dict, Any, Optional, List
from .coordination.coordinator import AgentCoordinator
from .workflow.orchestrator import WorkflowOrchestrator


class LingFlow:
    """LingFlow 统一入口 - 封装所有复杂性"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 LingFlow
        
        Args:
            config: 配置字典
        """
        self._coordinator = AgentCoordinator()
        self._orchestrator = WorkflowOrchestrator(self._coordinator)
    
    def run_skill(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """直接执行单个技能
        
        Args:
            skill_name: 技能名称
            params: 技能参数
            
        Returns:
            技能执行结果
        """
        return self._coordinator.execute_skill(skill_name, params or {})
    
    def run_workflow_file(self, filepath: str) -> Dict[str, Any]:
        """从YAML/JSON文件加载并执行工作流
        
        Args:
            filepath: 工作流文件路径
            
        Returns:
            工作流执行结果
        """
        import yaml
        with open(filepath, encoding='utf-8') as f:
            workflow_def = yaml.safe_load(f)
        return self._orchestrator.execute(workflow_def['tasks'])
    
    def run_workflow(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """直接执行工作流定义
        
        Args:
            workflow_def: 工作流定义
            
        Returns:
            工作流执行结果
        """
        tasks = workflow_def.get('tasks', [])
        return self._orchestrator.execute(tasks)
