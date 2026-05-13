# Parallel Execution Guide

## Overview

lingflow's parallel execution system enables concurrent task execution with dependency-aware scheduling, automatic agent selection, and real-time monitoring. This provides 2-4x speedup for workflows with independent tasks.

**Key Capabilities:**
- Parallel task execution (2-4x speedup)
- Dependency-aware scheduling
- Automatic agent selection
- Real-time monitoring
- Context optimization per task
- Token savings through context compression

## Why Parallel Execution?

### Performance Benefits

**Sequential Execution:**
```
Task 1: 2 minutes
Task 2: 2 minutes
Task 3: 2 minutes
Task 4: 2 minutes
Task 5: 2 minutes
Total: 10 minutes
```

**Parallel Execution (3 agents):**
```
[T1: 2min] [T2: 2min] [T3: 2min]
           [T4: 2min] [T5: 2min]
Total: 4 minutes (2.5x speedup)
```

### Cost Efficiency

With context compression and parallel execution:
- **Token savings**: 30-50% through compression
- **Time savings**: 2-4x through parallel execution
- **Overall efficiency**: 60-80% improvement

## When to Use Parallel Execution

### ✅ Ideal for Parallel Execution

1. **Independent Tasks**
   - Tasks with no dependencies
   - Different modules/components
   - Non-overlapping file sets

   ```python
   tasks = [
       Task(id="1", context={"module": "auth"}),
       Task(id="2", context={"module": "user"}),
       Task(id="3", context={"module": "api"})
   ]
   # All independent - perfect for parallel
   ```

2. **Same Task Type, Different Targets**
   - Testing multiple modules
   - Documentation for multiple files
   - Code review for different components

   ```python
   tasks = [
       Task(id="1", agent_type="testing", context={"module": "auth"}),
       Task(id="2", agent_type="testing", context={"module": "user"}),
       Task(id="3", agent_type="testing", context={"module": "api"})
   ]
   # Same agent type, different contexts
   ```

3. **Large Task Lists**
   - 5+ independent tasks
   - Time-critical development
   - Resource-constrained timeline

4. **CPU/Network Bound Tasks**
   - API integration tests
   - External service calls
   - Long-running operations

### ❌ Not Ideal for Parallel Execution

1. **Dependent Tasks**
   ```python
   tasks = [
       Task(id="1", context={"create": "model"}),
       Task(id="2", dependencies=["1"], context={"use": "model"}),
       Task(id="3", dependencies=["2"], context={"test": "model"})
   ]
   # Dependencies force sequential execution
   ```

2. **Shared Resources**
   - Database schema changes
   - Shared file modifications
   - Configuration updates

3. **Complex Interactions**
   - Tightly coupled modules
   - Complex state management
   - Shared in-memory data

4. **Debugging/Investigation**
   - Need sequential analysis
   - State-dependent debugging
   - Error investigation

## Quick Start

### Basic Parallel Execution

```python
from agent_coordinator import AgentCoordinator, Task
import asyncio

# Initialize coordinator
coordinator = AgentCoordinator(max_parallel_agents=3)

# Create independent tasks
tasks = [
    Task(
        id="task-1",
        description="Write tests for auth module",
        agent_type="testing",
        context={
            "module": "src/auth/auth.py",
            "test_types": ["unit", "integration"]
        }
    ),
    Task(
        id="task-2",
        description="Write tests for user module",
        agent_type="testing",
        context={
            "module": "src/user/user.py",
            "test_types": ["unit", "integration"]
        }
    ),
    Task(
        id="task-3",
        description="Write tests for API module",
        agent_type="testing",
        context={
            "module": "src/api/api.py",
            "test_types": ["unit", "integration"]
        }
    )
]

# Execute in parallel
results = asyncio.run(coordinator.execute_tasks_parallel(tasks))

# Check results
for result in results:
    status = "✅ Success" if result.success else "❌ Failed"
    print(f"{result.task_id}: {status}")
    if not result.success:
        print(f"  Error: {result.error}")
```

### Workflow with Mixed Parallel/Sequential

```python
from agent_coordinator import AgentCoordinator, Task, TaskPriority

coordinator = AgentCoordinator(max_parallel_agents=3)

# Tasks with dependencies
tasks = [
    # Phase 1: Parallel setup tasks
    Task(
        id="setup-1",
        description="Configure database",
        agent_type="implementation",
        context={"db": "PostgreSQL"},
        priority=TaskPriority.HIGH
    ),
    Task(
        id="setup-2",
        description="Configure Redis",
        agent_type="implementation",
        context={"cache": "Redis"},
        priority=TaskPriority.HIGH
    ),
    Task(
        id="setup-3",
        description="Configure S3",
        agent_type="implementation",
        context={"storage": "S3"},
        priority=TaskPriority.HIGH
    ),

    # Phase 2: Depends on setup (sequential after setup)
    Task(
        id="impl-1",
        description="Implement auth service",
        agent_type="implementation",
        context={"service": "auth"},
        dependencies=["setup-1", "setup-2"],
        priority=TaskPriority.CRITICAL
    ),

    # Phase 3: Parallel implementation (after auth)
    Task(
        id="impl-2",
        description="Implement user service",
        agent_type="implementation",
        context={"service": "user"},
        dependencies=["impl-1"],
        priority=TaskPriority.HIGH
    ),
    Task(
        id="impl-3",
        description="Implement API endpoints",
        agent_type="implementation",
        context={"api": "REST"},
        dependencies=["impl-1"],
        priority=TaskPriority.HIGH
    ),

    # Phase 4: Testing (after implementations)
    Task(
        id="test-1",
        description="Test auth service",
        agent_type="testing",
        context={"target": "auth"},
        dependencies=["impl-1"]
    ),
    Task(
        id="test-2",
        description="Test user service",
        agent_type="testing",
        context={"target": "user"},
        dependencies=["impl-2"]
    ),
    Task(
        id="test-3",
        description="Test API endpoints",
        agent_type="testing",
        context={"target": "api"},
        dependencies=["impl-3"]
    )
]

# Execute workflow (auto-schedules parallel tasks)
results = asyncio.run(coordinator.execute_workflow(tasks))

# Analyze execution
print(f"Total tasks: {len(results)}")
print(f"Successful: {sum(1 for r in results if r.success)}")
print(f"Failed: {sum(1 for r in results if not r.success)}")
```

## Configuration

### Max Parallel Agents

Control parallelism level:

```python
# Conservative (limited resources)
coordinator = AgentCoordinator(max_parallel_agents=2)

# Standard (balanced)
coordinator = AgentCoordinator(max_parallel_agents=3)

# Aggressive (high-performance setup)
coordinator = AgentCoordinator(max_parallel_agents=4)
```

**Trade-offs:**
- More agents = Faster execution but higher resource usage
- Fewer agents = Slower but more stable
- Optimal: 2-4 agents for most workflows

### Timeout Configuration

Set appropriate timeouts:

```python
task = Task(
    id="task-1",
    description="Long-running task",
    context={...},
    timeout=600  # 10 minutes
)
```

### Context Compression

Enable/disable per workflow:

```python
# Enable compression (default)
coordinator = AgentCoordinator(
    enable_compression=True,
    compression_ratio=0.5
)

# Disable for tasks needing full context
coordinator = AgentCoordinator(
    enable_compression=False
)
```

## Monitoring and Debugging

### Real-Time Status

```python
from agent_coordinator import AgentCoordinator

coordinator = AgentCoordinator()

# Start parallel execution (non-blocking)
task_future = asyncio.create_task(
    coordinator.execute_tasks_parallel(tasks)
)

# Monitor progress
while not task_future.done():
    status = coordinator.get_status()
    print(f"Busy agents: {status['busy_agents']}")
    print(f"Idle agents: {status['idle_agents']}")
    await asyncio.sleep(1)

# Get final results
results = await task_future
```

### Workflow Status

```python
# Check workflow progress
status = coordinator.get_workflow_status()

print(f"Total tasks: {status['total_tasks']}")
print(f"Completed: {status['completed']}")
print(f"In progress: {status['in_progress']}")
print(f"Pending: {status['pending']}")
print(f"Failed: {status['failed']}")

# Calculate completion percentage
completion = status['completed'] / status['total_tasks'] * 100
print(f"Completion: {completion:.1f}%")
```

### Agent Status

```python
# Check specific agent
agent_status = coordinator.get_agent_status("testing")

print(f"Status: {agent_status['status']}")
print(f"Current task: {agent_status.get('current_task', 'None')}")
print(f"Completed tasks: {agent_status['completed_tasks']}")
print(f"Failed tasks: {agent_status['failed_tasks']}")
```

### Execution History

```python
# Get task history
history = coordinator.get_agent_history("implementation")

for record in history:
    print(f"\nTask: {record.task_id}")
    print(f"  Status: {record.status}")
    print(f"  Duration: {record.duration:.2f}s")
    print(f"  Success: {record.success}")
    if not record.success:
        print(f"  Error: {record.error}")
```

## Best Practices

### 1. Validate Independence

```python
# ✅ Good: Confirm tasks are independent
def validate_independent(tasks):
    """Check if tasks have no dependencies"""
    for task in tasks:
        if task.dependencies:
            return False
    return True

if validate_independent(tasks):
    results = await coordinator.execute_tasks_parallel(tasks)
else:
    # Use workflow instead
    results = await coordinator.execute_workflow(tasks)
```

### 2. Handle Failures Gracefully

```python
# ✅ Good: Handle individual task failures
results = await coordinator.execute_tasks_parallel(tasks)

failed_tasks = [r for r in results if not r.success]
if failed_tasks:
    print(f"{len(failed_tasks)} tasks failed")

    # Retry failed tasks
    retry_tasks = [
        create_task_from_result(r) for r in failed_tasks
    ]
    retry_results = await coordinator.execute_tasks_parallel(retry_tasks)
```

### 3. Use Appropriate Priorities

```python
# ✅ Good: Prioritize critical tasks in workflows
Task(
    id="security-fix",
    description="Fix security vulnerability",
    priority=TaskPriority.CRITICAL  # Executed first
),

Task(
    id="documentation",
    description="Update docs",
    priority=TaskPriority.LOW  # Executed last
)
```

### 4. Optimize Task Size

```python
# ✅ Good: Split large tasks into smaller ones
# Bad: One large task
Task(id="test-all", description="Test everything", context={...})

# Good: Multiple smaller tasks
Task(id="test-auth", description="Test auth", context={"module": "auth"}),
Task(id="test-user", description="Test user", context={"module": "user"}),
Task(id="test-api", description="Test API", context={"module": "api"})
```

### 5. Monitor Resource Usage

```python
# ✅ Good: Adjust parallelism based on system load
import psutil

def get_optimal_parallel_agents():
    """Calculate optimal parallelism based on CPU"""
    cpu_count = psutil.cpu_count()
    cpu_usage = psutil.cpu_percent()

    if cpu_usage < 50:
        return min(4, cpu_count)
    elif cpu_usage < 80:
        return min(3, cpu_count)
    else:
        return max(2, cpu_count // 2)

optimal_agents = get_optimal_parallel_agents()
coordinator = AgentCoordinator(max_parallel_agents=optimal_agents)
```

## Integration with lingflow

### Skill-Based Execution

```python
# From dispatching-parallel-agents skill
# Switch from subagent-driven-development to parallel

# Original (sequential)
for task in tasks:
    result = await coordinator.dispatch_agent(task)
    # Two-stage review after each task

# Switch to parallel (independent tasks)
if are_tasks_independent(tasks):
    print("Switching to parallel execution...")

    # Build task definitions
    task_definitions = build_task_definitions(tasks)

    # Execute in parallel
    results = await coordinator.execute_tasks_parallel(task_definitions)

    # Two-stage review for each task
    for result in results:
        if result.success:
            review = two_stage_review(result.task_id)
            if not review.passed:
                # Handle review failure
                pass
```

### Test Verification

```python
from lingflow_integration import lingflowIntegration

# Run parallel tasks
results = await coordinator.execute_tasks_parallel(tasks)

# Verify with lingflow test engine
integration = lingflowIntegration()
verifications = []

for result in results:
    if result.success:
        # Run comprehensive tests
        verification = integration.run_tests(
            task_id=result.task_id,
            dimensions=['functionality', 'stability']
        )
        verifications.append(verification)

# Check overall verification status
all_passed = all(v.all_passed for v in verifications)
print(f"All tests passed: {all_passed}")
```

### Code Review Integration

```python
# Parallel execution + parallel code review

# Phase 1: Implement in parallel
impl_results = await coordinator.execute_tasks_parallel(implementation_tasks)

# Phase 2: Review in parallel (only successful implementations)
review_tasks = [
    Task(
        id=f"review-{r.task_id}",
        description=f"Review {r.task_id}",
        agent_type="review",
        context={"files": r.output_files}
    )
    for r in impl_results
    if r.success
]

review_results = await coordinator.execute_tasks_parallel(review_tasks)
```

## Performance Analysis

### Speedup Calculation

```python
def calculate_speedup(sequential_time, parallel_time, num_agents):
    """Calculate parallel speedup efficiency"""
    ideal_speedup = num_agents
    actual_speedup = sequential_time / parallel_time
    efficiency = actual_speedup / ideal_speedup

    print(f"Ideal speedup: {ideal_speedup}x")
    print(f"Actual speedup: {actual_speedup:.2f}x")
    print(f"Efficiency: {efficiency:.1%}")

    return efficiency

# Example
sequential_time = 600  # 10 minutes sequential
parallel_time = 240   # 4 minutes parallel
num_agents = 3

efficiency = calculate_speedup(sequential_time, parallel_time, num_agents)
# Output:
# Ideal speedup: 3x
# Actual speedup: 2.50x
# Efficiency: 83.3%
```

### Bottleneck Analysis

```python
# Analyze workflow bottlenecks
status = coordinator.get_workflow_status()

if status['in_progress'] > 0:
    # Tasks stuck in progress
    print(f"{status['in_progress']} tasks stuck")

if status['pending'] > 0:
    # Tasks waiting for dependencies
    print(f"{status['pending']} tasks waiting for dependencies")

# Check agent distribution
agent_status = coordinator.get_agent_status("implementation")
if agent_status['status'] == "BUSY":
    print(f"Implementation agent busy on {agent_status['current_task']}")
```

## Troubleshooting

### Slow Parallel Execution

**Problem:** Parallel execution not faster than sequential

**Solutions:**
1. Check for hidden dependencies
2. Increase max_parallel_agents
3. Optimize task context size (compression)
4. Check for resource contention

### Dependencies Not Resolving

**Problem:** Tasks stuck in PENDING state

**Solutions:**
1. Verify dependency graph is correct
2. Check for circular dependencies
3. Ensure dependent tasks completed successfully

### Agent Exhaustion

**Problem:** All agents busy, tasks queued

**Solutions:**
1. Increase max_parallel_agents
2. Reduce task count or dependencies
3. Use workflow mode instead

### Token Limit Errors

**Problem:** Context too large after compression

**Solutions:**
1. Increase compression ratio
2. Split tasks into smaller units
3. Disable compression for specific tasks

## Advanced Patterns

### Adaptive Parallelism

```python
import asyncio

class AdaptiveCoordinator(AgentCoordinator):
    def __init__(self):
        super().__init__(max_parallel_agents=2)
        self.performance_history = []

    async def execute_adaptive(self, tasks):
        """Adjust parallelism based on performance"""

        # Try with current parallelism
        start = asyncio.get_event_loop().time()
        results = await self.execute_tasks_parallel(tasks)
        duration = asyncio.get_event_loop().time() - start

        # Record performance
        self.performance_history.append(duration)

        # Adjust if needed
        if len(self.performance_history) >= 3:
            avg_duration = sum(self.performance_history[-3:]) / 3

            if avg_duration > 300:  # 5 minutes - too slow
                self.max_parallel_agents = min(4, self.max_parallel_agents + 1)
                print(f"Increased parallelism to {self.max_parallel_agents}")
```

### Fail-Fast vs Fail-Safe

```python
# Fail-fast: Stop on first error
async def execute_fail_fast(coordinator, tasks):
    for result in await coordinator.execute_tasks_parallel(tasks):
        if not result.success:
            raise Exception(f"Task failed: {result.error}")
    return results

# Fail-safe: Continue despite errors
async def execute_fail_safe(coordinator, tasks):
    results = await coordinator.execute_tasks_parallel(tasks)

    failed = [r for r in results if not r.success]
    if failed:
        print(f"{len(failed)} tasks failed, but continuing")

    return results
```

## API Reference

### AgentCoordinator (Parallel Methods)

```python
class AgentCoordinator:
    async def execute_tasks_parallel(
        self,
        tasks: List[Task]
    ) -> List[TaskResult]:
        """Execute tasks in parallel (no dependencies)."""

    async def execute_workflow(
        self,
        tasks: List[Task]
    ) -> List[TaskResult]:
        """Execute workflow with dependencies."""

    def get_workflow_status(self) -> Dict:
        """Get workflow execution status."""

    def get_agent_status(
        self, agent_type: str
    ) -> Dict:
        """Get specific agent status."""

    def get_agent_history(
        self, agent_type: str
    ) -> List[TaskRecord]:
        """Get agent task history."""
```

## Examples

See `agent_coordinator.py` main() function for complete examples:

```bash
python agent_coordinator.py
```

Demo includes:
- Parallel task execution
- Workflow with dependencies
- Real-time status monitoring
- Performance analysis

## Related Documentation

- Agent Coordination Guide: `docs/AGENT_COORDINATION_GUIDE.md`
- Context Compression Guide: `docs/CONTEXT_COMPRESSION_GUIDE.md`
- Dispatching Parallel Agents Skill: `skills/dispatching-parallel-agents/SKILL.md`
- Subagent Driven Development: `skills/subagent-driven-development/SKILL.md`
