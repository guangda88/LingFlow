"""LingFlow 统一入口"""

from .coordination.coordinator import AgentCoordinator
from .workflow.orchestrator import WorkflowOrchestrator


class LingFlow:
    """LingFlow 统一入口 - 封装所有复杂性"""
    
    def __init__(self, config=None):
        self._coordinator = AgentCoordinator()
        self._orchestrator = WorkflowOrchestrator(self._coordinator)
    
    # 技能执行
    def run_skill(self, skill_name: str, params: dict = None):
        """直接执行单个技能"""
        return self._coordinator.execute_skill(skill_name, params or {})
    
    # 从文件加载工作流
    def run_workflow_file(self, filepath: str):
        """从YAML/JSON文件加载并执行工作流"""
        import yaml
        with open(filepath, encoding='utf-8') as f:
            workflow_def = yaml.safe_load(f)
        return self._orchestrator.execute(workflow_def['tasks'])
    
    # 直接执行工作流定义
    def run_workflow(self, workflow_def: dict):
        """直接执行工作流定义"""
        tasks = workflow_def.get('tasks', [])
        return self._orchestrator.execute(tasks)
