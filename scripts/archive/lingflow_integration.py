"""
LingFlow Integration Module

Integrates existing test engines and analysis tools with the new skill system.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import json


class LingFlowIntegration:
    """Integrates LingFlow's existing capabilities with the skill system."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the integration module.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.test_engines = self._discover_test_engines()
        self.analysis_tools = self._discover_analysis_tools()

    def _discover_test_engines(self) -> Dict[str, Dict[str, Any]]:
        """Discover available test engines.

        Returns:
            Dictionary of test engines with metadata
        """
        engines = {
            "comprehensive": {
                "path": "comprehensive_test_runner.py",
                "description": "Comprehensive test runner with multiple dimensions",
                "dimensions": [
                    "functionality", "performance", "stability",
                    "security", "compatibility", "usability",
                    "maintainability", "integration", "documentation"
                ],
                "args_format": "--dimensions {dimensions}"
            },
            "end_to_end": {
                "path": "end_to_end_test_engine.py",
                "description": "End-to-end test engine",
                "dimensions": None,
                "args_format": ""
            },
            "quick_12s": {
                "path": "12_seconds_test_engine_demo.py",
                "description": "12-second quick test engine",
                "dimensions": ["functionality"],
                "args_format": ""
            }
        }

        # Check which engines actually exist
        available_engines = {}
        for name, engine in engines.items():
            engine_path = self.project_root / engine["path"]
            if engine_path.exists():
                available_engines[name] = engine

        return available_engines

    def _discover_analysis_tools(self) -> Dict[str, Dict[str, Any]]:
        """Discover available analysis tools.

        Returns:
            Dictionary of analysis tools with metadata
        """
        tools = {
            "code_analysis": {
                "available": True,
                "description": "Full-dimension code analysis"
            },
            "token_analysis": {
                "available": True,
                "description": "Token usage and cost analysis"
            },
            "pre_production": {
                "available": True,
                "description": "Pre-production acceptance testing"
            }
        }

        # Check which tools actually exist
        available_tools = {}
        for name, tool in tools.items():
            # For now, assume all tools are available
            # In production, you'd check for actual files/configs
            available_tools[name] = tool

        return available_tools

    def run_comprehensive_tests(
        self,
        dimensions: Optional[List[str]] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run comprehensive tests.

        Args:
            dimensions: List of dimensions to test (default: all)
            output_file: Optional file to save results

        Returns:
            Test results dictionary
        """
        engine = self.test_engines.get("comprehensive")
        if not engine:
            return {
                "success": False,
                "error": "Comprehensive test engine not available"
            }

        cmd = ["python", engine["path"]]

        if dimensions:
            dim_str = ",".join(dimensions)
            cmd.extend(["--dimensions", dim_str])

        if output_file:
            cmd.extend(["--report", output_file])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def run_end_to_end_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests.

        Returns:
            Test results dictionary
        """
        engine = self.test_engines.get("end_to_end")
        if not engine:
            return {
                "success": False,
                "error": "End-to-end test engine not available"
            }

        cmd = ["python", engine["path"]]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "exit_code": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def run_quick_tests(self) -> Dict[str, Any]:
        """Run quick 12-second tests.

        Returns:
            Test results dictionary
        """
        engine = self.test_engines.get("quick_12s")
        if not engine:
            return {
                "success": False,
                "error": "Quick test engine not available"
            }

        cmd = ["python", engine["path"]]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "exit_code": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_available_test_dimensions(self) -> List[str]:
        """Get list of available test dimensions.

        Returns:
            List of dimension names
        """
        engine = self.test_engines.get("comprehensive")
        if engine:
            return engine.get("dimensions", [])
        return []

    def analyze_code(
        self,
        dimensions: Optional[List[str]] = None,
        paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run code analysis.

        Args:
            dimensions: Dimensions to analyze (default: all)
            paths: Paths to analyze (default: entire project)

        Returns:
            Analysis results dictionary
        """
        # This would integrate with the actual code analyzer
        # For now, return a placeholder

        return {
            "success": True,
            "message": "Code analysis would be performed here",
            "dimensions": dimensions or self.get_available_test_dimensions(),
            "paths": paths or [str(self.project_root)]
        }

    def get_test_report_summary(self) -> Dict[str, Any]:
        """Get summary of available test reports.

        Returns:
            Summary dictionary
        """
        # This would scan for existing test reports
        # For now, return placeholder

        return {
            "available_reports": [],
            "total_reports": 0,
            "last_updated": None
        }

    def list_available_engines(self) -> List[str]:
        """List all available test engines.

        Returns:
            List of engine names
        """
        return list(self.test_engines.keys())

    def list_available_tools(self) -> List[str]:
        """List all available analysis tools.

        Returns:
            List of tool names
        """
        return list(self.analysis_tools.keys())

    def get_engine_info(self, engine_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific test engine.

        Args:
            engine_name: Name of the engine

        Returns:
            Engine information or None
        """
        return self.test_engines.get(engine_name)

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific analysis tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool information or None
        """
        return self.analysis_tools.get(tool_name)


def main():
    """Main entry point for testing the integration."""

    print("=" * 60)
    print("LingFlow Integration Module")
    print("=" * 60)

    # Initialize integration
    integration = LingFlowIntegration()

    # List available engines
    print("\nAvailable Test Engines:")
    for engine_name in integration.list_available_engines():
        engine_info = integration.get_engine_info(engine_name)
        print(f"  • {engine_name}: {engine_info.get('description', '')}")

    # List available tools
    print("\nAvailable Analysis Tools:")
    for tool_name in integration.list_available_tools():
        tool_info = integration.get_tool_info(tool_name)
        print(f"  • {tool_name}: {tool_info.get('description', '')}")

    # List available test dimensions
    dimensions = integration.get_available_test_dimensions()
    print(f"\nAvailable Test Dimensions ({len(dimensions)}):")
    for dim in dimensions:
        print(f"  • {dim}")

    print("\n" + "=" * 60)
    print("Integration initialized successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
