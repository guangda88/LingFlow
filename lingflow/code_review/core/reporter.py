"""
报告生成器 - 生成代码审查报告
"""

import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    """
    代码审查报告生成器

    负责将审查结果格式化为各种输出格式
    """

    def __init__(self, output_format: str = "text"):
        """
        初始化报告生成器

        Args:
            output_format: 输出格式 (text, json, html, markdown)
        """
        self.output_format = output_format

    def generate(self, review_result: Dict[str, Any]) -> str:
        """
        生成报告

        Args:
            review_result: 审查结果字典

        Returns:
            str: 格式化的报告字符串
        """
        if self.output_format == "json":
            return self._generate_json(review_result)
        elif self.output_format == "markdown":
            return self._generate_markdown(review_result)
        else:
            return self._generate_text(review_result)

    def _generate_text(self, result: Dict[str, Any]) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("代码审查报告")
        lines.append("=" * 60)

        if "overall_score" in result:
            score = result["overall_score"]
            lines.append(f"总体评分: {score:.2f}/5.0")

        if "dimensions" in result:
            lines.append("\n各维度评分:")
            for dim_name, dim_data in result["dimensions"].items():
                score = dim_data.get("score", 0)
                issues_count = len(dim_data.get("issues", []))
                lines.append(f"  {dim_name}: {score:.2f} ({issues_count} 个问题)")

        if "reviewed_files" in result:
            lines.append(f"\n审查文件数: {len(result['reviewed_files'])}")

        return "\n".join(lines)

    def _generate_json(self, result: Dict[str, Any]) -> str:
        """生成 JSON 格式报告"""
        return json.dumps(result, indent=2, ensure_ascii=False)

    def _generate_markdown(self, result: Dict[str, Any]) -> str:
        """生成 Markdown 格式报告"""
        lines = []
        lines.append("# 代码审查报告\n")

        if "overall_score" in result:
            score = result["overall_score"]
            lines.append(f"## 总体评分: {score:.2f}/5.0\n")

        if "dimensions" in result:
            lines.append("## 各维度详情\n")
            for dim_name, dim_data in result["dimensions"].items():
                lines.append(f"### {dim_name}")
                score = dim_data.get("score", 0)
                lines.append(f"**评分**: {score:.2f}/5.0\n")

                issues = dim_data.get("issues", [])
                if issues:
                    lines.append("**问题**:")
                    for issue in issues[:10]:  # 只显示前10个
                        lines.append(f"- {issue}")
                lines.append("")

        return "\n".join(lines)

    def save_to_file(self, report: str, file_path: Path) -> None:
        """
        保存报告到文件

        Args:
            report: 报告内容
            file_path: 目标文件路径
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(report, encoding="utf-8")

    def generate_filename(self, prefix: str = "review") -> str:
        """
        生成带时间戳的文件名

        Args:
            prefix: 文件名前缀

        Returns:
            str: 生成的文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}"
