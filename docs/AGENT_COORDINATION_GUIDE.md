# Agent Coordination Guide

## Overview

lingflow's agent coordination system provides advanced multi-agent orchestration with automatic agent registration, dependency-aware scheduling, parallel execution, and context compression.

**Key Capabilities:**
- Automatic agent registration from configuration
- Parallel task execution (2-4x speedup)
- Dependency-aware task scheduling
- Context compression (30-50% token savings)
- Real-time monitoring and status tracking
- Automatic agent selection based on capabilities

## Quick Start

### Basic Usage

```python
from agent_coordinator import AgentCoordinator, Task

# Initialize coordinator (auto-registers agents from agents/agents.json)
coordinator = AgentCoordinator()

# Create a simple task
task = Task(
    id="task-1",
    description="Implement user authentication module",
    agent_type="implementation",
    context={
        "requirements": "JWT-based auth with role management",
        "files": ["src/auth/auth.py"]
    }
)

# Execute task
result = coordinator.dispatch_agent(task)
print(f"Result: {result.success}, Output: {result.output}")
```

### Parallel Execution

```python
from agent_coordinator import AgentCoordinator, Task
import asyncio

coordinator = AgentCoordinator(max_parallel_agents=3)

# Create independent tasks
tasks = [
    Task(
        id="task-1",
        description="Implement JWT token generation",
        agent_type="implementation",
        context={"spec": "Generate JWT tokens with 24h expiry"}
    ),
    Task(
        id="task-2",
        description="Write unit tests for auth module",
        agent_type="testing",
        context={"module": "src/auth/auth.py"}
    ),
    Task(
        id="task-3",
        description="Create API documentation",
        agent_type="documentation",
        context={"module": "src/auth/auth.py"}
    )
]

# Execute in parallel
results = asyncio.run(coordinator.execute_tasks_parallel(tasks))

for result in results:
    print(f"Task {result.task_id}: {'Success' if result.success else 'Failed'}")
```

### Workflow with Dependencies

```python
from agent_coordinator import AgentCoordinator, Task
from agent_coordinator import TaskPriority

coordinator = AgentCoordinator()

# Create tasks with dependencies
tasks = [
    Task(
        id="task-1",
        description="Define data models",
        agent_type="implementation",
        context={"schema": "User, Role, Permission models"},
        priority=TaskPriority.HIGH
    ),
    Task(
        id="task-2",
        description="Implement auth service",
        agent_type="implementation",
        context={"service": "Authentication with JWT"},
        dependencies=["task-1"],  # Depends on models
        priority=TaskPriority.CRITICAL
    ),
    Task(
        id="task-3",
        description="Write auth tests",
        agent_type="testing",
        context={"target": "src/auth/auth.py"},
        dependencies=["task-2"],  # Depends on implementation
        priority=TaskPriority.NORMAL
    ),
    Task(
        id="task-4",
        description="Code review auth module",
        agent_type="review",
        context={"files": ["src/auth/auth.py", "src/auth/models.py"]},
        dependencies=["task-2", "task-3"],  # Depends on implementation and tests
        priority=TaskPriority.HIGH
    )
]

# Execute workflow (auto-resolves dependencies)
results = asyncio.run(coordinator.execute_workflow(tasks))

# Check overall status
print(f"Workflow status: {coordinator.get_workflow_status()}")
```

## Agent Configuration

### Agent Types

lingflow comes with 6 pre-configured agent types:

| Agent Type | Capabilities | Use Case |
|------------|--------------|----------|
| `implementation` | Code generation, testing, documentation | Feature development |
| `review` | Code review, design review, security check | Quality assurance |
| `testing` | Test generation, execution, coverage analysis | Test automation |
| `debugging` | Error analysis, root cause, fix generation | Bug fixing |
| `architecture` | System design, architecture review | System planning |
| `documentation` | Doc generation, API writing | Documentation |

### Custom Agent Registration

Add custom agents in `agents/agents.json`:

```json
{
  "agents": [
    {
      "name": "my-custom-agent",
      "description": "Custom agent for specific tasks",
      "capabilities": ["custom-task-1", "custom-task-2"],
      "prompt_template": "You are a custom agent specialized in {capability}.",
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 2000
    }
  ]
}
```

The coordinator automatically registers all agents from this configuration on initialization.

### Agent Selection

The coordinator automatically selects the best agent based on task requirements:

```python
# Coordinator automatically picks the right agent
task = Task(
    id="task-1",
    description="Review authentication code",
    # No agent_type specified - coordinator will infer it
    context={
        "type": "code_review",
        "files": ["src/auth/auth.py"]
    }
)

# Coordinator matches based on capabilities
result = coordinator.dispatch_agent(task)
```

## Task Management

### Task Properties

```python
Task(
    id="unique-task-id",                    # Required: Unique identifier
    description="Task description",        # Required: Human-readable description
    agent_type="implementation",           # Optional: Specific agent type
    context={},                            # Required: Task context/data
    dependencies=[],                       # Optional: List of task IDs this depends on
    priority=TaskPriority.NORMAL,          # Optional: Task priority
    timeout=300                           # Optional: Timeout in seconds (default: 300)
)
```

### Priority Levels

- `CRITICAL` - Highest priority, executed first
- `HIGH` - Important tasks, executed before normal
- `NORMAL` - Default priority
- `LOW` - Lowest priority, executed last

### Task Dependencies

Dependencies define execution order:

```python
tasks = [
    Task(id="build", description="Build project", dependencies=[]),
    Task(id="test", description="Run tests", dependencies=["build"]),
    Task(id="deploy", description="Deploy", dependencies=["test"])
]

# Coordinator automatically builds dependency graph
# and executes in correct order
```

The coordinator:
- Detects circular dependencies (raises error)
- Identifies parallelizable tasks
- Executes ready tasks in priority order
- Tracks completion status

## Context Compression

### Automatic Compression

Context is automatically compressed when dispatching agents:

```python
task = Task(
    id="task-1",
    description="Implement feature",
    context={
        "requirements": very_long_text,  # Will be compressed
        "spec": detailed_specification   # Will be compressed
    }
)

# Coordinator applies compression before sending to agent
# Achieves 30-50% token reduction
```

### Manual Compression Control

```python
from agent_coordinator import ContextCompressor

compressor = ContextCompressor()

# Compress text
compressed = compressor.compress(
    text="Very long text to compress...",
    target_ratio=0.5  # Target 50% of original size
)

print(f"Original: {len(text)} chars")
print(f"Compressed: {len(compressed)} chars")
print(f"Ratio: {len(compressed)/len(text):.1%}")
```

### Compression Strategies

The coordinator uses multiple strategies:

1. **Information Density Ranking** - Keeps high-density sections
2. **Semantic Compression** - Preserves key sentences
3. **List Compression** - Keeps important list items
4. **Token Estimation** - Based on character/token ratio

## Monitoring and Status

### Real-time Status

```python
coordinator = AgentCoordinator()

# Get overall coordinator status
status = coordinator.get_status()
print(status)
# {
#   "total_agents": 6,
#   "idle_agents": 4,
#   "busy_agents": 2,
#   "failed_agents": 0
# }

# Get specific agent status
agent_status = coordinator.get_agent_status("implementation")
print(agent_status)
# {
#   "name": "implementation",
#   "status": "BUSY",
#   "current_task": "task-1",
#   "completed_tasks": 5,
#   "failed_tasks": 0
# }

# Get workflow status
workflow_status = coordinator.get_workflow_status()
print(workflow_status)
# {
#   "total_tasks": 10,
#   "completed": 7,
#   "in_progress": 2,
#   "pending": 1,
#   "failed": 0
# }
```

### Agent History

```python
# Get task history for an agent
history = coordinator.get_agent_history("implementation")
for task_record in history:
    print(f"Task: {task_record.task_id}")
    print(f"  Status: {task_record.status}")
    print(f"  Duration: {task_record.duration}s")
    print(f"  Success: {task_record.success}")
```

## Best Practices

### 1. Use Parallel Execution for Independent Tasks

```python
# ✅ Good: Independent tasks in parallel
tasks = [
    Task(id="1", description="Write tests", context={"module": "auth"}),
    Task(id="2", description="Write tests", context={"module": "user"}),
    Task(id="3", description="Write tests", context={"module": "api"})
]
coordinator.execute_tasks_parallel(tasks)
```

### 2. Define Dependencies Explicitly

```python
# ✅ Good: Clear dependencies
Task(id="build", dependencies=[]),
Task(id="test", dependencies=["build"]),
Task(id="deploy", dependencies=["test"])
```

### 3. Use Appropriate Priorities

```python
# ✅ Good: Critical tasks first
Task(id="security-fix", priority=TaskPriority.CRITICAL),
Task(id="feature", priority=TaskPriority.NORMAL),
Task(id="documentation", priority=TaskPriority.LOW)
```

### 4. Provide Sufficient Context

```python
# ✅ Good: Rich context
Task(
    id="task-1",
    description="Implement JWT auth",
    context={
        "requirements": "JWT with 24h expiry, refresh tokens",
        "files": ["src/auth/auth.py"],
        "dependencies": ["cryptography"],
        "constraints": ["Must follow OAuth2 spec"]
    }
)
```

### 5. Monitor Execution

```python
# ✅ Good: Check status and handle failures
results = coordinator.execute_workflow(tasks)

for result in results:
    if not result.success:
        print(f"Task {result.task_id} failed: {result.error}")
        # Handle failure appropriately
```

## Integration with lingflow Skills

### Subagent-Driven Development

```python
# From subagent-driven-development skill
# Can switch to parallel execution for independent tasks

# Sequential (default)
for task in tasks:
    result = coordinator.dispatch_agent(task)
    # Two-stage review after each task

# Parallel (switch to dispatching-parallel-agents)
if all(t.dependencies == [] for t in tasks):
    results = coordinator.execute_tasks_parallel(tasks)
    # Two-stage review for each task in parallel
```

### Test Verification

```python
from lingflow_integration import lingflowIntegration

# Run tests after parallel execution
results = coordinator.execute_workflow(tasks)

# Verify all implementations with lingflow
integration = lingflowIntegration()
for result in results:
    if result.success:
        verification = integration.run_tests(result.task_id)
        print(f"Tests passed: {verification.all_passed}")
```

## Performance Optimization

### Token Savings

Context compression reduces costs significantly:

```python
# Without compression
cost_per_task = 5000 tokens * $0.00003 = $0.15
total_cost = 8 tasks * $0.15 = $1.20

# With 43% compression
cost_per_task = 2850 tokens * $0.00003 = $0.085
total_cost = 8 tasks * $0.085 = $0.68

# Savings: $0.52 (43%)
```

### Execution Speed

Parallel execution provides 2-4x speedup:

```python
# Sequential: 8 tasks * 2 minutes = 16 minutes
# Parallel (3 agents): 16 minutes / 3 = 5.3 minutes
# Speedup: 3.0x
```

### Resource Management

Configure based on available resources:

```python
# For limited resources
coordinator = AgentCoordinator(max_parallel_agents=2)

# For high-performance setup
coordinator = AgentCoordinator(max_parallel_agents=4)
```

## Troubleshooting

### Agent Not Found

**Error:** `Agent type 'xyz' not found`

**Solution:** Register agent in `agents/agents.json` or use correct agent type:

```python
# Check available agents
agents = coordinator.list_agents()
print(agents)  # Lists all registered agents
```

### Circular Dependency Detected

**Error:** `Circular dependency detected: task-1 -> task-2 -> task-1`

**Solution:** Review and fix dependency graph:

```python
# Remove circular reference
Task(id="task-1", dependencies=["task-2"]),
Task(id="task-2", dependencies=["task-1"]),  # ❌ Circular!

# Fix
Task(id="task-1", dependencies=[]),
Task(id="task-2", dependencies=["task-1"])
```

### Task Timeout

**Error:** Task exceeds timeout limit

**Solution:** Increase timeout or optimize task:

```python
# Increase timeout
Task(id="task-1", timeout=600)  # 10 minutes

# Or optimize context
Task(
    id="task-1",
    context=compressor.compress(context, target_ratio=0.4)
)
```

## Advanced Features

### Custom Agent Behaviors

```python
from agent_coordinator import Agent

class CustomAgent(Agent):
    def execute(self, task: Task) -> TaskResult:
        # Custom execution logic
        try:
            # Your custom implementation
            result = self.custom_execution(task)
            return TaskResult(
                task_id=task.id,
                success=True,
                output=result,
                duration=10.5
            )
        except Exception as e:
            return TaskResult(
                task_id=task.id,
                success=False,
                error=str(e),
                duration=5.2
            )

# Register custom agent
coordinator.registry.register(CustomAgent(
    name="custom",
    capabilities=["custom-task"]
))
```

### Custom Compression Strategies

```python
from agent_coordinator import ContextCompressor

class CustomCompressor(ContextCompressor):
    def compress_list(self, items):
        # Custom list compression logic
        # Keep items based on custom criteria
        return custom_selection(items)

# Use custom compressor
coordinator = AgentCoordinator(compressor=CustomCompressor())
```

## API Reference

### AgentCoordinator

```python
class AgentCoordinator:
    def __init__(
        self,
        max_parallel_agents: int = 3,
        enable_compression: bool = True,
        compression_ratio: float = 0.5
    ):
        """Initialize coordinator."""

    async def dispatch_agent(self, task: Task) -> TaskResult:
        """Dispatch task to appropriate agent."""

    async def execute_tasks_parallel(
        self,
        tasks: List[Task]
    ) -> List[TaskResult]:
        """Execute multiple tasks in parallel."""

    async def execute_workflow(
        self,
        tasks: List[Task]
    ) -> List[TaskResult]:
        """Execute workflow with dependencies."""

    def list_agents(self) -> List[Agent]:
        """List all registered agents."""

    def get_status(self) -> Dict:
        """Get overall coordinator status."""

    def get_agent_status(self, agent_type: str) -> Dict:
        """Get specific agent status."""

    def get_workflow_status(self) -> Dict:
        """Get workflow execution status."""
```

## Examples

See `agent_coordinator.py` main() function for complete examples:
- Agent registration and listing
- Context compression with statistics
- Parallel task execution
- Workflow execution with dependencies
- Coordinator status reporting

```bash
python agent_coordinator.py
```

## Related Documentation

- Context Compression Guide: `docs/CONTEXT_COMPRESSION_GUIDE.md`
- Parallel Execution Guide: `docs/PARALLEL_EXECUTION_GUIDE.md`
- Dispatching Parallel Agents Skill: `skills/dispatching-parallel-agents/SKILL.md`
- Agent Configuration: `agents/agents.json`
