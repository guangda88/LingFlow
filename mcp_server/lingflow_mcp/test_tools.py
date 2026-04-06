"""MCP 测试运行工具

提供测试执行、覆盖率分析和报告生成功能。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.test_results = {}
        self.coverage_data = {}

    async def run_tests(
        self,
        test_path: str = ".",
        test_type: str = "all",
        verbose: bool = False,
        coverage: bool = True,
    ) -> Dict[str, Any]:
        """运行测试

        Args:
            test_path: 测试路径
            test_type: 测试类型 (all, unit, integration)
            verbose: 详细输出
            coverage: 是否计算覆盖率

        Returns:
            测试结果
        """
        import subprocess
        import sys

        try:
            # 构建测试命令
            cmd = [sys.executable, "-m", "pytest"]

            if test_type == "unit":
                cmd.extend(["-k", "unit"])
            elif test_type == "integration":
                cmd.extend(["-k", "integration"])

            if verbose:
                cmd.append("-v")

            if coverage:
                cmd.extend(["--cov=.", "--cov-report=term-missing"])

            cmd.append(test_path)

            # 运行测试
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
            )

            # 解析结果
            success = result.returncode == 0

            # 提取测试统计
            stats = self._parse_test_output(result.stdout + result.stderr)

            return {
                "success": success,
                "test_path": test_path,
                "test_type": test_type,
                "stats": stats,
                "stdout": result.stdout if verbose else None,
                "stderr": result.stderr if verbose else None,
                "execution_time": stats.get("duration", 0),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "测试执行超时（>5分钟）",
                "test_path": test_path,
            }
        except Exception as e:
            logger.error(f"运行测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_path": test_path,
            }

    def _parse_test_output(self, output: str) -> Dict[str, Any]:
        """解析测试输出"""
        import re

        stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 0.0,
        }

        # 解析测试数量
        # 示例: "382 items collected" 或 "382 passed in 10.5s"
        match = re.search(r'(\d+)\s+item', output)
        if match:
            stats["total"] = int(match.group(1))

        # 解析通过/失败数量
        match = re.search(r'(\d+)\s+passed', output)
        if match:
            stats["passed"] = int(match.group(1))

        match = re.search(r'(\d+)\s+failed', output)
        if match:
            stats["failed"] = int(match.group(1))

        match = re.search(r'(\d+)\s+skipped', output)
        if match:
            stats["skipped"] = int(match.group(1))

        match = re.search(r'(\d+)\s+error', output)
        if match:
            stats["errors"] = int(match.group(1))

        # 解析执行时间
        match = re.search(r'in\s+([\d.]+)s', output)
        if match:
            stats["duration"] = float(match.group(1))

        return stats

    async def get_coverage(
        self,
        target_path: str = ".",
        format_type: str = "summary",
    ) -> Dict[str, Any]:
        """获取测试覆盖率

        Args:
            target_path: 目标路径
            format_type: 格式类型 (summary, detailed, json)

        Returns:
            覆盖率信息
        """
        try:
            # 尝试读取覆盖率文件
            coverage_file = Path(target_path) / ".coverage"

            if not coverage_file.exists():
                # 运行覆盖率分析
                return await self._run_coverage_analysis(target_path, format_type)

            # 解析覆盖率数据
            return self._parse_coverage_data(target_path, format_type)

        except Exception as e:
            logger.error(f"获取覆盖率失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "target_path": target_path,
            }

    async def _run_coverage_analysis(
        self,
        target_path: str,
        format_type: str,
    ) -> Dict[str, Any]:
        """运行覆盖率分析"""
        import subprocess
        import sys

        cmd = [sys.executable, "-m", "pytest", f"--cov={target_path}"]
        cmd.extend(["--cov-report", "term"])
        cmd.extend(["--cov-report", "json"])
        cmd.append(target_path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return self._parse_coverage_output(result.stdout + result.stderr)

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _parse_coverage_data(
        self,
        target_path: str,
        format_type: str,
    ) -> Dict[str, Any]:
        """解析覆盖率数据"""
        coverage_file = Path(target_path) / "coverage.json"

        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    data = json.load(f)

                files = data.get("files", {})

                # 计算总体覆盖率
                total_lines = sum(f.get("summary", {}).get("num_statements", 0) for f in files.values())
                covered_lines = sum(f.get("summary", {}).get("covered_lines", 0) for f in files.values())

                overall_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0

                if format_type == "detailed":
                    return {
                        "success": True,
                        "overall_coverage": round(overall_coverage, 2),
                        "files": {
                            name: {
                                "coverage": round(f.get("summary", {}).get("percent_covered", 0), 2),
                                "statements": f.get("summary", {}).get("num_statements", 0),
                                "missing": f.get("summary", {}).get("missing_lines", 0),
                            }
                            for name, f in files.items()
                        },
                    }
                else:
                    return {
                        "success": True,
                        "overall_coverage": round(overall_coverage, 2),
                        "files_count": len(files),
                    }

            except Exception as e:
                logger.error(f"解析覆盖率文件失败: {e}")

        # Fallback: 简单版本
        return {
            "success": True,
            "overall_coverage": 0,
            "message": "覆盖率数据不可用",
        }

    def _parse_coverage_output(self, output: str) -> Dict[str, Any]:
        """解析覆盖率输出"""
        import re

        # 提取总体覆盖率
        match = re.search(r'TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%', output)
        if match:
            stmts = int(match.group(1))
            miss = int(match.group(2))
            cover = int(match.group(3))

            return {
                "success": True,
                "overall_coverage": cover,
                "statements": stmts,
                "missing": miss,
                "covered": stmts - miss,
            }

        return {
            "success": False,
            "error": "无法解析覆盖率输出",
        }

    async def generate_test_report(
        self,
        test_path: str = ".",
        output_format: str = "markdown",
    ) -> Dict[str, Any]:
        """生成测试报告

        Args:
            test_path: 测试路径
            output_format: 输出格式 (markdown, json, html)

        Returns:
            测试报告
        """
        try:
            # 运行测试获取数据
            test_result = await self.run_tests(
                test_path=test_path,
                verbose=False,
                coverage=True,
            )

            # 获取覆盖率数据
            coverage_result = await self.get_coverage(
                target_path=test_path,
                format_type="detailed" if output_format == "json" else "summary",
            )

            # 生成报告
            if output_format == "json":
                report = {
                    "test_results": test_result,
                    "coverage": coverage_result,
                    "generated_at": datetime.now().isoformat(),
                }
            elif output_format == "markdown":
                report = self._generate_markdown_report(test_result, coverage_result)
            else:  # html
                report = self._generate_html_report(test_result, coverage_result)

            return {
                "success": True,
                "report": report,
                "format": output_format,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"生成测试报告失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _generate_markdown_report(
        self,
        test_result: Dict[str, Any],
        coverage_result: Dict[str, Any],
    ) -> str:
        """生成 Markdown 报告"""
        stats = test_result.get("stats", {})
        coverage = coverage_result.get("overall_coverage", 0)

        report = f"""# LingFlow 测试报告

**生成时间**: {test_result.get('generated_at', datetime.now().isoformat())}

## 📊 测试结果摘要

| 指标 | 数值 |
|------|------|
| 总测试数 | {stats.get('total', 0)} |
| 通过 | {stats.get('passed', 0)} |
| 失败 | {stats.get('failed', 0)} |
| 跳过 | {stats.get('skipped', 0)} |
| 错误 | {stats.get('errors', 0)} |
| 执行时间 | {stats.get('duration', 0):.2f}s |
| 通过率 | {(stats.get('passed', 0) / max(stats.get('total', 1), 1) * 100):.1f}% |

## 📈 覆盖率

| 类型 | 覆盖率 |
|------|--------|
| 总体覆盖率 | {coverage}% |

## 🎯 结论

"""

        if test_result.get("success"):
            report += "✅ 所有测试通过！\n"
        else:
            report += "❌ 存在失败的测试，请检查日志。\n"

        return report

    def _generate_html_report(
        self,
        test_result: Dict[str, Any],
        coverage_result: Dict[str, Any],
    ) -> str:
        """生成 HTML 报告"""
        stats = test_result.get("stats", {})
        coverage = coverage_result.get("overall_coverage", 0)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>LingFlow 测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
    </style>
</head>
<body>
    <h1>🧪 LingFlow 测试报告</h1>
    <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>📊 测试结果</h2>
    <table>
        <tr>
            <th>指标</th>
            <th>数值</th>
        </tr>
        <tr>
            <td>总测试数</td>
            <td>{stats.get('total', 0)}</td>
        </tr>
        <tr>
            <td>通过</td>
            <td class="success">{stats.get('passed', 0)}</td>
        </tr>
        <tr>
            <td>失败</td>
            <td class="failure">{stats.get('failed', 0)}</td>
        </tr>
        <tr>
            <td>跳过</td>
            <td>{stats.get('skipped', 0)}</td>
        </tr>
        <tr>
            <td>执行时间</td>
            <td>{stats.get('duration', 0):.2f}s</td>
        </tr>
    </table>

    <h2>📈 覆盖率</h2>
    <table>
        <tr>
            <th>类型</th>
            <th>覆盖率</th>
        </tr>
        <tr>
            <td>总体覆盖率</td>
            <td>{coverage}%</td>
        </tr>
    </table>
</body>
</html>"""

        return html
