"""
Simple LingFlow initialization test
Avoids unicode encoding issues
"""
import sys
from pathlib import Path

# Add LingFlow to path
lingflow_path = Path(__file__).parent
sys.path.insert(0, str(lingflow_path))

def test_imports():
    """Test all main imports"""
    print("[TEST] Testing imports...")
    from agent_coordinator import (
        AgentCoordinator,
        Task,
        TaskPriority,
        AgentConfig,
        AgentStatus
    )
    print("[PASS] All main classes imported successfully")
    return True

def test_coordinator_init():
    """Test coordinator initialization"""
    print("\n[TEST] Testing coordinator initialization...")
    from agent_coordinator import AgentCoordinator
    coordinator = AgentCoordinator()
    assert coordinator is not None, "Coordinator should be initialized"
    print("[PASS] AgentCoordinator initialized")
    print(f"       - Config loaded from agents/agents.json")
    return True

def test_task_creation():
    """Test task creation"""
    print("\n[TEST] Testing task creation...")
    from agent_coordinator import Task, TaskPriority

    task = Task(
        task_id="test-1",
        name="Test Task",
        description="A simple test task",
        priority=TaskPriority.NORMAL,
        agent_type="implementation",
        context={}
    )
    assert task.task_id == "test-1", "Task ID should match"
    assert task.name == "Test Task", "Task name should match"
    assert task.priority == TaskPriority.NORMAL, "Task priority should match"
    print(f"[PASS] Task created: {task.task_id}")
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("LingFlow Simple Initialization Test")
    print("="*60)

    results = []
    results.append(test_imports())
    results.append(test_coordinator_init())
    results.append(test_task_creation())

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    print("="*60)

    if all(results):
        print("\n[SUCCESS] LingFlow is initialized and ready to use!")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
