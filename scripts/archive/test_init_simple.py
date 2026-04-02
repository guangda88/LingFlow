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
    from lingflow import LingFlow
    from lingflow.coordination.coordinator import AgentCoordinator
    print("[PASS] All main classes imported successfully")
    assert True

def test_coordinator_init():
    """Test coordinator initialization"""
    print("\n[TEST] Testing coordinator initialization...")
    from lingflow.coordination.coordinator import AgentCoordinator
    coordinator = AgentCoordinator()
    print("[PASS] AgentCoordinator initialized")
    assert coordinator is not None

def test_task_creation():
    """Test task creation"""
    print("\n[TEST] Testing task creation...")
    task = {
        'id': 'test-1',
        'skill': 'test-skill',
        'params': {'test': 'value'}
    }
    print(f"[PASS] Task created: {task['id']}")
    assert task is not None

def test_skill_execution():
    """Test skill execution"""
    print("\n[TEST] Testing skill execution...")
    from lingflow import LingFlow
    lf = LingFlow()
    result = lf.run_skill('notification', {'message': 'Test notification'})
    print("[PASS] Skill executed successfully")
    assert result.get('result', {}).get('success') is True

def test_workflow_execution():
    """Test workflow execution"""
    print("\n[TEST] Testing workflow execution...")
    from lingflow import LingFlow
    lf = LingFlow()
    workflow = {
        'name': 'Test Workflow',
        'tasks': [
            {
                'id': 'test_task',
                'skill': 'notification',
                'params': {'message': 'Workflow test'}
            }
        ]
    }
    result = lf.run_workflow(workflow)
    print("[PASS] Workflow executed successfully")
    assert result.get('status') == 'completed'

def main():
    """Run all tests"""
    print("="*60)
    print("LingFlow Simple Initialization Test")
    print("="*60)

    results = []
    try:
        test_imports()
        results.append(True)
    except Exception as e:
        print(f"[FAIL] test_imports: {e}")
        results.append(False)
    
    try:
        test_coordinator_init()
        results.append(True)
    except Exception as e:
        print(f"[FAIL] test_coordinator_init: {e}")
        results.append(False)
    
    try:
        test_task_creation()
        results.append(True)
    except Exception as e:
        print(f"[FAIL] test_task_creation: {e}")
        results.append(False)
    
    try:
        test_skill_execution()
        results.append(True)
    except Exception as e:
        print(f"[FAIL] test_skill_execution: {e}")
        results.append(False)
    
    try:
        test_workflow_execution()
        results.append(True)
    except Exception as e:
        print(f"[FAIL] test_workflow_execution: {e}")
        results.append(False)

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
