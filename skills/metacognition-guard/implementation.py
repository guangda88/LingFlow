"""Metacognition Guard Skill Implementation

Performs pre-task capability checks to ensure AI agent has sufficient
knowledge before starting work.
"""

from typing import Dict, Any
from lingflow.trust import (
    MetacognitiveAgent,
    get_metacognitive_agent,
    CapabilityLevel,
)


def execute_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute metacognition guard check.

    Args:
        params: Dictionary containing:
            - task_id: Task identifier
            - task_description: Task description
            - required_capabilities: List of required capability names
            - complexity: Task complexity (simple, medium, complex)
            - current_capabilities: Dict of {capability_name: level_name}
            - propose_evolution: Whether to propose evolution paths (default: False)

    Returns:
        Dict with:
            - can_start: bool - Whether task can start
            - gaps: list - Capability gaps found
            - reason: str - Explanation
            - recommendations: list - Recommendations
            - evolution_proposed: dict - Evolution path (if requested)
    """
    agent = get_metacognitive_agent()

    # Extract parameters
    task_id = params.get("task_id", "unknown")
    task_description = params.get("task_description", "")
    required_capabilities = params.get("required_capabilities", [])
    complexity = params.get("complexity", "medium")
    current_capabilities = params.get("current_capabilities", {})
    propose_evolution = params.get("propose_evolution", False)

    # Step 1: Declare current capabilities
    for cap_name, level_name in current_capabilities.items():
        try:
            level = CapabilityLevel[level_name.upper()]
            agent.declare_capability(
                name=cap_name,
                category="general",
                level=level,
                notes="Declared at task start"
            )
        except KeyError:
            # Invalid level name, skip
            continue

    # Step 2: Analyze task requirements
    requirements = agent.analyze_task_requirements(
        task_id=task_id,
        task_description=task_description,
        required_capabilities=required_capabilities,
        complexity=complexity
    )

    # Step 3: Check if can start
    can_start, reason = agent.can_declare_completion(requirements)

    # Step 4: Propose evolution if requested
    evolution_proposed = None
    if propose_evolution and requirements.gaps:
        evolution_proposed = _propose_evolution_for_gaps(agent, requirements.gaps)

    # Step 5: Generate knowledge boundaries report
    knowledge_report = agent.get_knowledge_boundaries_report()

    return {
        "can_start": can_start,
        "gaps": requirements.gaps,
        "reason": reason,
        "recommendations": requirements.recommendations,
        "alternative_approaches": requirements.alternative_approaches,
        "evolution_proposed": evolution_proposed,
        "knowledge_summary": {
            "mastered_count": len(knowledge_report["mastered"]),
            "partial_count": len(knowledge_report["partial"]),
            "familiar_count": len(knowledge_report["familiar"]),
            "unknown_count": len(knowledge_report["unknown"]),
        }
    }


def _propose_evolution_for_gaps(
    agent: MetacognitiveAgent,
    gaps: list
) -> Dict[str, Any]:
    """Propose evolution paths for identified gaps

    Args:
        agent: Metacognitive agent instance
        gaps: List of gap descriptions

    Returns:
        Evolution proposal dict
    """
    evolution_proposals = []

    # Extract capability names from gaps
    for gap in gaps:
        if "UNKNOWN:" in gap:
            # Extract capability name from gap description
            # Format: "UNKNOWN: CapabilityName - description"
            parts = gap.split(":")
            if len(parts) > 1:
                cap_name = parts[1].split("-")[0].strip()

                # Propose evolution to PARTIAL level
                evolution_path = agent.propose_evolution(
                    capability_name=cap_name,
                    target_level=CapabilityLevel.PARTIAL,
                    steps=[
                        f"Read {cap_name} documentation and tutorials",
                        f"Set up local {cap_name} environment",
                        f"Practice with sample {cap_name} projects",
                        f"Build a small project using {cap_name}"
                    ]
                )
                evolution_proposals.append({
                    "capability": cap_name,
                    "from_level": "UNKNOWN",
                    "to_level": "PARTIAL",
                    "steps": evolution_path.steps,
                    "estimated_time": "1-2 weeks"
                })

        elif "INSUFFICIENT:" in gap:
            # Extract capability name and suggest evolution
            parts = gap.split(":")
            if len(parts) > 1:
                # Format: "INSUFFICIENT: SQL - Current level PARTIAL, need COMPLEX complexity"
                remaining = parts[1].strip()
                cap_name = remaining.split("-")[0].strip().split(" ")[0]

                capability = agent.get_capability(cap_name)
                if capability:
                    current_level = capability.level
                    target_level = CapabilityLevel(min(current_level.value + 1, 3))

                    evolution_path = agent.propose_evolution(
                        capability_name=cap_name,
                        target_level=target_level,
                        steps=[
                            f"Advanced {cap_name} tutorials",
                            f"Production-level {cap_name} patterns",
                            f"Review {cap_name} best practices"
                        ]
                    )
                    evolution_proposals.append({
                        "capability": cap_name,
                        "from_level": current_level.name,
                        "to_level": target_level.name,
                        "steps": evolution_path.steps,
                        "estimated_time": "1 week"
                    })

    return {
        "total_proposals": len(evolution_proposals),
        "proposals": evolution_proposals,
        "total_estimated_time": f"{len(evolution_proposals) * 1}-2 weeks"
    }


# Example usage functions

def example_simple_task():
    """Example: Simple task with no capability gaps"""
    result = execute_skill({
        "task_id": "simple-task",
        "task_description": "Write a Python function",
        "required_capabilities": ["Python"],
        "complexity": "simple",
        "current_capabilities": {
            "Python": "MASTERED"
        }
    })

    if result["can_start"]:
        print(f"✓ Can start task: {result['reason']}")
    else:
        print(f"✗ Cannot start: {result['reason']}")
        print(f"  Gaps: {result['gaps']}")

    return result


def example_complex_task_with_gaps():
    """Example: Complex task with capability gaps"""
    result = execute_skill({
        "task_id": "complex-task",
        "task_description": "Migrate to PostgreSQL with partitioning",
        "required_capabilities": ["Python", "SQL", "PostgreSQL"],
        "complexity": "complex",
        "current_capabilities": {
            "Python": "MASTERED",
            "SQL": "PARTIAL"
        },
        "propose_evolution": True
    })

    if result["can_start"]:
        print(f"✓ Can start task: {result['reason']}")
    else:
        print(f"✗ Cannot start: {result['reason']}")
        print(f"  Gaps: {result['gaps']}")
        print(f"  Recommendations:")
        for rec in result['recommendations']:
            print(f"    - {rec}")

        if result['evolution_proposed']:
            print(f"\n  Evolution proposals:")
            for prop in result['evolution_proposed']['proposals']:
                print(f"    - {prop['capability']}: {prop['from_level']} → {prop['to_level']}")
                print(f"      Time: {prop['estimated_time']}")
                print(f"      Steps:")
                for step in prop['steps']:
                    print(f"        {step}")

    return result


def example_knowledge_boundary_check():
    """Example: Check overall knowledge boundaries"""
    agent = get_metacognitive_agent()

    # Declare capabilities
    agent.declare_capability("Python", "programming", CapabilityLevel.MASTERED)
    agent.declare_capability("pytest", "testing", CapabilityLevel.PARTIAL)
    agent.declare_capability("Kubernetes", "devops", CapabilityLevel.FAMILIAR)

    # Get report
    result = execute_skill({
        "task_id": "check-boundaries",
        "task_description": "Check knowledge boundaries",
        "required_capabilities": ["Python", "pytest", "Kubernetes"],
        "complexity": "medium",
        "current_capabilities": {
            "Python": "MASTERED",
            "pytest": "PARTIAL",
            "Kubernetes": "FAMILIAR"
        }
    })

    print(f"\nKnowledge Boundaries Summary:")
    print(f"  Mastered: {result['knowledge_summary']['mastered_count']}")
    print(f"  Partial: {result['knowledge_summary']['partial_count']}")
    print(f"  Familiar: {result['knowledge_summary']['familiar_count']}")
    print(f"  Unknown: {result['knowledge_summary']['unknown_count']}")

    return result


if __name__ == "__main__":
    print("Metacognition Guard Skill Examples\n")
    print("=" * 60)

    print("\n1. Simple Task (No Gaps):")
    print("-" * 60)
    example_simple_task()

    print("\n2. Complex Task (With Gaps):")
    print("-" * 60)
    example_complex_task_with_gaps()

    print("\n3. Knowledge Boundary Check:")
    print("-" * 60)
    example_knowledge_boundary_check()

    print("\n" + "=" * 60)
