"""
LingFlow Agent Coordinator - Advanced Multi-Agent Coordination System

This module provides:
- Agent registration and discovery
- Task scheduling and dispatching
- Parallel execution with context isolation
- Context compression and optimization
- Agent lifecycle management
"""

import asyncio
import json
import logging
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent lifecycle status"""
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    COMPLETED = "completed"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class AgentConfig:
    """Agent configuration"""
    name: str
    description: str
    capabilities: List[str]
    max_tasks: int = 1
    context_limit: int = 8000  # Token limit for agent context
    timeout: int = 300  # Default timeout in seconds
    parallel_safe: bool = True
    requires_isolation: bool = False


@dataclass
class Task:
    """Task definition"""
    task_id: str
    name: str
    description: str
    priority: TaskPriority
    dependencies: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_used: Optional[str] = None
    compressed_context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextCompressor:
    """
    Context compression algorithm using multiple strategies
    
    Strategies:
    1. Token-aware truncation
    2. Information density ranking
    3. Semantic compression
    4. Pattern-based summarization
    """

    def __init__(self, target_tokens: int = 4000):
        self.target_tokens = target_tokens
        self.compression_stats = {
            'total_compressions': 0,
            'total_tokens_saved': 0,
            'average_compression_ratio': 0.0
        }

    def compress(self, context: Dict[str, Any], 
                preserve_sections: List[str] = None) -> Dict[str, Any]:
        """
        Compress context using multiple strategies
        
        Args:
            context: Original context dictionary
            preserve_sections: List of sections to always preserve
            
        Returns:
            Compressed context dictionary
        """
        logger.info(f"Compressing context (original size: {self._estimate_tokens(context)})")
        
        compressed = {}
        preserve = preserve_sections or []
        
        # Always preserve critical sections
        for section in preserve:
            if section in context:
                compressed[section] = context[section]
                logger.info(f"Preserved section: {section}")
        
        # Apply compression strategies
        for key, value in context.items():
            if key in preserve:
                continue
                
            if isinstance(value, dict):
                compressed[key] = self._compress_dict(value, key)
            elif isinstance(value, str):
                compressed[key] = self._compress_text(value, key)
            elif isinstance(value, list):
                compressed[key] = self._compress_list(value, key)
            else:
                compressed[key] = value
        
        # Calculate compression stats
        original_tokens = self._estimate_tokens(context)
        compressed_tokens = self._estimate_tokens(compressed)
        compression_ratio = 1 - (compressed_tokens / original_tokens)
        
        self.compression_stats['total_compressions'] += 1
        self.compression_stats['total_tokens_saved'] += (original_tokens - compressed_tokens)
        self.compression_stats['average_compression_ratio'] = (
            (self.compression_stats['average_compression_ratio'] * 
             (self.compression_stats['total_compressions'] - 1) + compression_ratio) /
            self.compression_stats['total_compressions']
        )
        
        logger.info(f"Compression complete: {original_tokens} → {compressed_tokens} tokens "
                   f"({compression_ratio:.1%} reduction)")
        
        return compressed

    def _compress_dict(self, data: Dict[str, Any], section_name: str) -> Dict[str, Any]:
        """Compress dictionary using information density ranking"""
        if not data:
            return data
        
        # Calculate information density for each key
        densities = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Density = unique words / total words
                words = re.findall(r'\w+', value.lower())
                if words:
                    density = len(set(words)) / len(words)
                    densities[key] = density
                else:
                    densities[key] = 0.0
        
        # Sort by density and keep high-value items
        sorted_keys = sorted(densities.keys(), 
                           key=lambda k: densities[k], 
                           reverse=True)
        
        # Keep top 70% of highest-density items
        keep_count = max(1, int(len(sorted_keys) * 0.7))
        compressed_dict = {k: data[k] for k in sorted_keys[:keep_count]}
        
        # Add note about truncation
        if len(sorted_keys) > keep_count:
            compressed_dict['_truncated'] = f"Removed {len(sorted_keys) - keep_count} low-priority items"
        
        return compressed_dict

    def _compress_text(self, text: str, context_key: str) -> str:
        """Compress text using semantic summarization"""
        if not text or len(text) < 500:
            return text
        
        # Calculate current tokens (rough estimate: ~4 chars per token)
        estimated_tokens = len(text) / 4
        
        if estimated_tokens <= self.target_tokens:
            return text
        
        # Strategy: Semantic compression
        # 1. Keep first and last 20%
        # 2. Summarize middle 60%
        
        first_part = text[:int(len(text) * 0.2)]
        last_part = text[int(len(text) * 0.8):]
        middle_part = text[int(len(text) * 0.2):int(len(text) * 0.8)]
        
        # Extract key sentences from middle part
        sentences = re.split(r'[.!?]+', middle_part)
        key_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Keep sentences with:
            # - Important keywords (must, should, critical, ensure, verify)
            # - Technical content (functions, classes, methods)
            keywords = ['must', 'should', 'critical', 'ensure', 'verify', 
                      'function', 'class', 'method', 'implement', 'test']
            
            if any(kw in sentence.lower() for kw in keywords):
                key_sentences.append(sentence)
        
        # Reassemble
        compressed_text = (
            f"{first_part}\n\n"
            f"[...] {len(key_sentences)} key instructions:\n"
            f"{' '.join(key_sentences)}\n[...]\n\n"
            f"{last_part}"
        )
        
        # Add compression note
        if estimated_tokens > self.target_tokens * 2:
            compressed_text = (
                f"[Context compressed from ~{estimated_tokens:.0f} to "
                f"~{len(compressed_text)/4:.0f} tokens]\n\n"
                f"{compressed_text}"
            )
        
        return compressed_text

    def _compress_list(self, items: List[Any], context_key: str) -> List[Any]:
        """Compress list by prioritizing items"""
        if not items or len(items) <= 5:
            return items
        
        # Keep first and last 2 items
        # If items are strings, also keep items with important keywords
        keep_indices = set([0, 1, -2, -1])
        
        if isinstance(items[0], str):
            keywords = ['must', 'should', 'critical', 'important', 'error', 'test']
            for i, item in enumerate(items):
                if any(kw in str(item).lower() for kw in keywords):
                    keep_indices.add(i)
        
        # Sort indices and build compressed list
        sorted_indices = sorted(list(keep_indices))
        compressed_list = [items[i] for i in sorted_indices if 0 <= i < len(items)]
        
        # Add truncation note
        if len(compressed_list) < len(items):
            compressed_list.append(
                f"[... {len(items) - len(compressed_list)} items omitted ...]"
            )
        
        return compressed_list

    def _estimate_tokens(self, data: Any) -> int:
        """Estimate token count (rough approximation)"""
        if isinstance(data, str):
            return len(data) // 4  # ~4 characters per token
        elif isinstance(data, (list, dict)):
            if isinstance(data, dict):
                data = data.values()
            return sum(self._estimate_tokens(item) for item in data)
        elif isinstance(data, (int, float, bool)):
            return 1
        else:
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        return self.compression_stats.copy()

    def reset_stats(self):
        """Reset compression statistics"""
        self.compression_stats = {
            'total_compressions': 0,
            'total_tokens_saved': 0,
            'average_compression_ratio': 0.0
        }


class Agent:
    """Individual agent instance"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.current_task_id: Optional[str] = None
        self.task_history: List[str] = []
        self.compressor = ContextCompressor(target_tokens=config.context_limit)

    async def execute_task(self, task: Task, 
                        context: Dict[str, Any]) -> TaskResult:
        """Execute a task"""
        logger.info(f"Agent {self.config.name} executing task {task.task_id}")
        
        self.status = AgentStatus.BUSY
        self.current_task_id = task.task_id
        start_time = time.time()
        
        try:
            # Compress context if needed
            compressed_context = self.compressor.compress(context)
            
            # In a real implementation, this would call the actual AI agent
            # For now, we simulate execution
            await asyncio.sleep(0.1)  # Simulate work
            
            # Simulate success
            result = TaskResult(
                task_id=task.task_id,
                success=True,
                output=f"Task {task.task_id} completed by {self.config.name}",
                execution_time=time.time() - start_time,
                agent_used=self.config.name,
                compressed_context=json.dumps(compressed_context, indent=2)
            )
            
            self.status = AgentStatus.COMPLETED
            self.task_history.append(task.task_id)
            
        except Exception as e:
            logger.error(f"Agent {self.config.name} failed task {task.task_id}: {e}")
            result = TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                agent_used=self.config.name
            )
            self.status = AgentStatus.FAILED
        
        finally:
            self.current_task_id = None
        
        return result

    def can_execute(self, task: Task) -> bool:
        """Check if agent can execute task"""
        if self.status != AgentStatus.IDLE:
            return False
        
        # Check capabilities
        if task.required_capabilities:
            has_all_capabilities = all(
                cap in self.config.capabilities 
                for cap in task.required_capabilities
            )
            if not has_all_capabilities:
                return False
        
        return True

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': self.config.name,
            'description': self.config.description,
            'capabilities': self.config.capabilities,
            'status': self.status.value,
            'current_task': self.current_task_id,
            'tasks_completed': len(self.task_history),
            'compression_stats': self.compressor.get_stats()
        }


class AgentRegistry:
    """Registry for all available agents"""

    def __init__(self, config_path: str = "agents/agents.json"):
        self.config_path = Path(config_path)
        self.agents: Dict[str, Agent] = {}
        self._load_agent_configs()

    def _load_agent_configs(self):
        """Load agent configurations from file"""
        if not self.config_path.exists():
            logger.warning(f"Agent config file not found: {self.config_path}")
            # Create default configuration
            self._create_default_config()
        
        with open(self.config_path, 'r') as f:
            configs = json.load(f)
        
        for config_data in configs.get('agents', []):
            config = AgentConfig(**config_data)
            agent = Agent(config)
            self.agents[config.name] = agent
            logger.info(f"Registered agent: {config.name}")

    def _create_default_config(self):
        """Create default agent configuration"""
        default_config = {
            "agents": [
                {
                    "name": "implementation",
                    "description": "Agent for implementing features based on plans",
                    "capabilities": ["code_generation", "testing", "documentation"],
                    "max_tasks": 3,
                    "context_limit": 8000,
                    "timeout": 300,
                    "parallel_safe": True
                },
                {
                    "name": "review",
                    "description": "Agent for code and design review",
                    "capabilities": ["code_review", "design_review", "security_check"],
                    "max_tasks": 2,
                    "context_limit": 12000,
                    "timeout": 180,
                    "parallel_safe": True
                },
                {
                    "name": "testing",
                    "description": "Agent for writing and running tests",
                    "capabilities": ["test_generation", "test_execution", "coverage_analysis"],
                    "max_tasks": 2,
                    "context_limit": 6000,
                    "timeout": 600,
                    "parallel_safe": True
                },
                {
                    "name": "debugging",
                    "description": "Agent for debugging and troubleshooting",
                    "capabilities": ["error_analysis", "root_cause", "fix_generation"],
                    "max_tasks": 1,
                    "context_limit": 10000,
                    "timeout": 300,
                    "parallel_safe": False
                }
            ]
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default agent config: {self.config_path}")

    def register_agent(self, agent: Agent):
        """Register a new agent"""
        self.agents[agent.config.name] = agent
        logger.info(f"Registered agent: {agent.config.name}")

    def unregister_agent(self, agent_name: str):
        """Unregister an agent"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        return self.agents.get(name)

    def find_agents_for_task(self, task: Task) -> List[Agent]:
        """Find all agents capable of executing a task"""
        capable_agents = []
        
        for agent in self.agents.values():
            if agent.can_execute(task):
                capable_agents.append(agent)
        
        return capable_agents

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [agent.get_info() for agent in self.agents.values()]


class AgentCoordinator:
    """
    Advanced multi-agent coordinator
    
    Features:
    - Parallel task execution
    - Dependency-aware scheduling
    - Automatic agent selection
    - Context optimization
    - Real-time monitoring
    """

    def __init__(self, registry: AgentRegistry = None):
        self.registry = registry or AgentRegistry()
        self.task_queue: List[Task] = []
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.failed_tasks: Dict[str, TaskResult] = {}
        self.task_dependencies: Dict[str, Set[str]] = {}
        self.execution_lock = threading.Lock()
        self.compressor = ContextCompressor()
        
    def submit_task(self, task: Task):
        """Submit a task to the coordinator"""
        self.task_queue.append(task)
        
        # Build dependency graph
        if task.task_id not in self.task_dependencies:
            self.task_dependencies[task.task_id] = set(task.dependencies)
        
        logger.info(f"Submitted task: {task.task_id} (priority: {task.priority.name})")

    def schedule_tasks(self) -> List[Task]:
        """
        Schedule tasks based on dependencies and priority

        Returns:
            List of tasks ready to execute
        """
        ready_tasks = []

        for task in self.task_queue:
            # Skip completed or failed tasks
            if task.task_id in self.completed_tasks or task.task_id in self.failed_tasks:
                continue

            # Check if dependencies are satisfied
            dependencies_met = all(
                dep_id in self.completed_tasks
                for dep_id in task.dependencies
            )

            if dependencies_met:
                ready_tasks.append(task)

        # Sort by priority
        ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)

        return ready_tasks

    async def execute_parallel(self, tasks: List[Task], 
                           max_parallel: int = 3) -> Dict[str, TaskResult]:
        """
        Execute tasks in parallel with automatic agent assignment
        
        Args:
            tasks: List of tasks to execute
            max_parallel: Maximum number of parallel executions
            
        Returns:
            Dictionary mapping task IDs to results
        """
        logger.info(f"Executing {len(tasks)} tasks with max {max_parallel} parallel agents")
        
        results = {}
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def execute_with_semaphore(task: Task):
            async with semaphore:
                # Find suitable agent
                agents = self.registry.find_agents_for_task(task)
                
                if not agents:
                    logger.error(f"No suitable agent found for task {task.task_id}")
                    return TaskResult(
                        task_id=task.task_id,
                        success=False,
                        error="No suitable agent found"
                    )
                
                # Select first available agent
                agent = agents[0]
                
                # Execute task
                result = await agent.execute_task(
                    task, 
                    task.context
                )
                
                return result
        
        # Execute all tasks in parallel
        results_dict = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # Process results
        for result in results_dict:
            if isinstance(result, Exception):
                logger.error(f"Task execution failed with exception: {result}")
                continue
            
            results[result.task_id] = result
            
            if result.success:
                self.completed_tasks[result.task_id] = result
                logger.info(f"Task {result.task_id} completed successfully")
            else:
                self.failed_tasks[result.task_id] = result
                logger.error(f"Task {result.task_id} failed: {result.error}")
        
        return results

    async def execute_workflow(self, tasks: List[Task]) -> Dict[str, TaskResult]:
        """
        Execute a workflow with dependencies
        
        Args:
            tasks: List of tasks with dependencies
            
        Returns:
            Dictionary mapping task IDs to results
        """
        logger.info(f"Executing workflow with {len(tasks)} tasks")
        
        results = {}
        
        while len(self.completed_tasks) + len(self.failed_tasks) < len(tasks):
            # Schedule ready tasks
            ready_tasks = self.schedule_tasks()
            
            if not ready_tasks:
                logger.warning("No ready tasks found - checking for circular dependencies")
                break
            
            # Execute ready tasks in parallel
            batch_results = await self.execute_parallel(ready_tasks, max_parallel=3)
            results.update(batch_results)
            
            # Small delay to allow agent status updates
            await asyncio.sleep(0.1)
        
        logger.info(f"Workflow execution complete: "
                   f"{len(self.completed_tasks)} succeeded, "
                   f"{len(self.failed_tasks)} failed")
        
        return results

    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status"""
        return {
            'total_tasks': len(self.task_queue) + len(self.completed_tasks),
            'pending_tasks': len([t for t in self.task_queue 
                                 if t.task_id not in self.completed_tasks]),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'agents': self.registry.list_agents(),
            'compression_stats': self.compressor.get_stats()
        }

    def reset(self):
        """Reset coordinator state"""
        self.task_queue.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.task_dependencies.clear()
        logger.info("Coordinator reset")


async def main():
    """Main test function"""
    print("=" * 60)
    print("LingFlow Agent Coordinator - Advanced Multi-Agent System")
    print("=" * 60)
    
    # Initialize coordinator
    coordinator = AgentCoordinator()
    
    print("\n" + "=" * 60)
    print("Registered Agents:")
    print("=" * 60)
    for agent_info in coordinator.registry.list_agents():
        print(f"\n{agent_info['name']}:")
        print(f"  Description: {agent_info['description']}")
        print(f"  Capabilities: {', '.join(agent_info['capabilities'])}")
        print(f"  Status: {agent_info['status']}")
    
    # Test context compression
    print("\n" + "=" * 60)
    print("Context Compression Test:")
    print("=" * 60)
    
    test_context = {
        'project_info': {
            'name': 'LingFlow',
            'description': 'Intelligent software development workflow engine',
            'version': '1.0.0',
            'components': ['skill_trigger', 'lingflow_integration', 'test_engines']
        },
        'task_description': "Implement a new feature for user authentication with JWT tokens. " * 20,
        'instructions': [
            "Step 1: Create authentication module",
            "Step 2: Implement JWT token generation",
            "Step 3: Add token validation middleware",
            "Step 4: Write unit tests for all functions",
            "Step 5: Update documentation",
            "Step 6: Verify security requirements",
            "Step 7: Test with integration tests"
        ],
        'requirements': {
            'critical': 'Must implement JWT-based authentication',
            'important': 'Should include role-based access control',
            'nice_to_have': 'Could add OAuth2 support in future'
        }
    }
    
    print(f"\nOriginal context size: ~{coordinator.compressor._estimate_tokens(test_context)} tokens")
    
    compressed = coordinator.compressor.compress(
        test_context, 
        preserve_sections=['requirements']
    )
    
    print(f"Compressed context size: ~{coordinator.compressor._estimate_tokens(compressed)} tokens")
    print(f"Compression ratio: {coordinator.compressor.get_stats()['average_compression_ratio']:.1%}")
    
    # Test parallel task execution
    print("\n" + "=" * 60)
    print("Parallel Task Execution Test:")
    print("=" * 60)
    
    tasks = [
        Task(
            task_id="task_1",
            name="Implement authentication module",
            description="Create base authentication module",
            priority=TaskPriority.HIGH,
            required_capabilities=["code_generation"],
            context={"module": "auth", "features": ["login", "logout"]}
        ),
        Task(
            task_id="task_2",
            name="Write unit tests",
            description="Write comprehensive unit tests",
            priority=TaskPriority.NORMAL,
            required_capabilities=["test_generation"],
            context={"coverage_target": "90%"}
        ),
        Task(
            task_id="task_3",
            name="Code review",
            description="Review implementation for quality",
            priority=TaskPriority.NORMAL,
            dependencies=["task_1"],
            required_capabilities=["code_review"],
            context={"review_focus": "security"}
        )
    ]
    
    for task in tasks:
        coordinator.submit_task(task)
    
    results = await coordinator.execute_parallel(tasks, max_parallel=2)
    
    print("\nTask Results:")
    for task_id, result in results.items():
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        print(f"\n{task_id}: {status}")
        print(f"  Agent: {result.agent_used}")
        print(f"  Time: {result.execution_time:.2f}s")
        if result.error:
            print(f"  Error: {result.error}")
    
    # Test workflow execution
    print("\n" + "=" * 60)
    print("Workflow Execution Test:")
    print("=" * 60)
    
    coordinator.reset()
    
    workflow_tasks = [
        Task(
            task_id="design",
            name="Design authentication system",
            description="Create system design",
            priority=TaskPriority.CRITICAL,
            required_capabilities=["design_review"],
            context={}
        ),
        Task(
            task_id="implement",
            name="Implement authentication",
            description="Implement the designed system",
            priority=TaskPriority.HIGH,
            dependencies=["design"],
            required_capabilities=["code_generation"],
            context={}
        ),
        Task(
            task_id="test",
            name="Test authentication",
            description="Write and run tests",
            priority=TaskPriority.HIGH,
            dependencies=["implement"],
            required_capabilities=["test_generation"],
            context={}
        ),
        Task(
            task_id="review",
            name="Review implementation",
            description="Code review",
            priority=TaskPriority.NORMAL,
            dependencies=["test"],
            required_capabilities=["code_review"],
            context={}
        )
    ]
    
    for task in workflow_tasks:
        coordinator.submit_task(task)
    
    results = await coordinator.execute_workflow(workflow_tasks)
    
    print("\nWorkflow Results:")
    for task_id, result in results.items():
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        print(f"{task_id}: {status}")
    
    # Print final status
    print("\n" + "=" * 60)
    print("Coordinator Status:")
    print("=" * 60)
    status = coordinator.get_status()
    print(f"Total tasks: {status['total_tasks']}")
    print(f"Completed: {status['completed_tasks']}")
    print(f"Failed: {status['failed_tasks']}")
    print(f"\nCompression Statistics:")
    comp_stats = status['compression_stats']
    print(f"  Total compressions: {comp_stats['total_compressions']}")
    print(f"  Tokens saved: {comp_stats['total_tokens_saved']}")
    print(f"  Avg compression ratio: {comp_stats['average_compression_ratio']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
