"""lingflow 代理注册表"""

from typing import Any, Dict, List, Optional

from lingflow.common.models import Task
from lingflow.coordination.agent import Agent


class AgentRegistry:
    """简化的代理注册表"""

    def __init__(self) -> None:
        self.agents: Dict[str, Agent] = {}

    def register_agent(self, agent: Agent) -> None:
        """注册代理"""
        self.agents[agent.config.name] = agent

    def get_agent(self, name: str) -> Optional[Agent]:
        """获取代理"""
        return self.agents.get(name)

    def find_agents_for_task(self, task: Task) -> List[Agent]:
        """查找适合执行任务的代理"""
        capable_agents = []

        # 1. 如果指定了 agent_type，首先尝试精确匹配
        if task.agent_type:
            agent = self.get_agent(task.agent_type)
            if agent and agent.can_execute(task):
                return [agent]

        # 2. 否则，查找能力匹配的代理
        for agent in self.agents.values():
            if agent.can_execute(task):
                capable_agents.append(agent)

        return capable_agents

    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有代理"""
        return [agent.get_info() for agent in self.agents.values()]
