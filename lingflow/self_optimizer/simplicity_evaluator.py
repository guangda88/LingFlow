"""
lingflow 简洁性评估器
评估代码简洁性和重复度
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class SimplicityMetrics:
    """简洁性指标"""

    total_lines: int  # 总行数
    code_lines: int  # 代码行数
    comment_lines: int  # 注释行数
    blank_lines: int  # 空行数
    avg_line_length: float  # 平均行长度
    max_line_length: int  # 最大行长度
    long_lines_count: int  # 长行数量
    duplication_rate: float  # 重复率
    complex_lines: int  # 复杂行数


class SimplicityEvaluator:
    """简洁性评估器"""

    def __init__(self, target_path: str = "."):
        """
        Args:
            target_path: 目标代码路径
        """
        self.target_path = Path(target_path)

    def evaluate(self, params: Dict[str, Any]) -> float:
        """评估简洁性（用于lingminopt）

        Args:
            params: 优化参数
                - complexity_threshold: 复杂度阈值
                - duplication_penalty: 重复惩罚
                - max_line_length: 最大行长度

        Returns:
            简洁性分数（越低越好）
        """
        # 1. 分析代码
        metrics = self._analyze_simplicity(params)

        # 2. 计算分数
        score = 0.0

        # 长行惩罚

        long_lines_penalty = metrics.long_lines_count * 2.0
        score += long_lines_penalty

        # 重复惩罚
        duplication_penalty = params.get("duplication_penalty", 1.0)
        duplication_score = metrics.duplication_rate * 100 * duplication_penalty
        score += duplication_score

        # 复杂度惩罚

        complexity_penalty = metrics.complex_lines * 1.0
        score += complexity_penalty

        return float(score)

    def _analyze_simplicity(self, params: Dict[str, Any]) -> SimplicityMetrics:
        """分析代码简洁性"""
        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        line_lengths = []
        long_lines_count = 0

        max_line_length = params.get("max_line_length", 100)

        # 分析每个Python文件
        for py_file in self.target_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                for line in lines:
                    total_lines += 1
                    line_len = len(line.rstrip("\n\r"))
                    line_lengths.append(line_len)

                    # 空行
                    if not line.strip():
                        blank_lines += 1
                    # 注释行
                    elif line.strip().startswith("#"):
                        comment_lines += 1
                    # 代码行
                    else:
                        code_lines += 1

                    # 长行
                    if line_len > max_line_length:
                        long_lines_count += 1

            except Exception:
                continue

        # 计算平均值
        avg_line_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0
        max_line = max(line_lengths) if line_lengths else 0

        # 计算重复率
        duplication_rate = self._calculate_duplication_rate()

        # 计算复杂行
        complex_lines = self._count_complex_lines()

        return SimplicityMetrics(
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            avg_line_length=avg_line_length,
            max_line_length=max_line,
            long_lines_count=long_lines_count,
            duplication_rate=duplication_rate,
            complex_lines=complex_lines,
        )

    def _calculate_duplication_rate(self) -> float:
        """计算代码重复率（简化版：基于行重复）"""
        line_counts: dict[str, int] = {}

        # 统计每行出现次数
        for py_file in self.target_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    for line in f:
                        # 移除空白和注释
                        line = line.strip()
                        if line and not line.startswith("#"):
                            line_counts[line] = line_counts.get(line, 0) + 1
            except Exception:
                continue

        if not line_counts:
            return 0.0

        # 计算重复行比例
        total_lines = sum(line_counts.values())
        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)

        return duplicate_lines / total_lines if total_lines > 0 else 0.0

    def _count_complex_lines(self) -> int:
        """统计复杂行（包含多个操作符或嵌套的行）"""
        complex_lines = 0
        complex_patterns = [
            r".*and.*and.*",  # 多个and
            r".*or.*or.*",  # 多个or
            r".*if.*if.*",  # 嵌套if
            r".*for.*for.*",  # 嵌套for
            r".*\{.*\{.*",  # 嵌套大括号
            r".*\(.*\(.*",  # 嵌套括号
        ]

        for py_file in self.target_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # 检查是否匹配复杂模式
                            for pattern in complex_patterns:
                                if re.match(pattern, line):
                                    complex_lines += 1
                                    break
            except Exception:
                continue

        return complex_lines

    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前简洁性指标"""
        # 使用默认参数
        default_params = {
            "complexity_threshold": 10,
            "duplication_penalty": 1.0,
            "max_line_length": 100,
        }

        metrics = self._analyze_simplicity(default_params)

        return {
            "total_lines": metrics.total_lines,
            "code_lines": metrics.code_lines,
            "comment_lines": metrics.comment_lines,
            "blank_lines": metrics.blank_lines,
            "avg_line_length": metrics.avg_line_length,
            "max_line_length": metrics.max_line_length,
            "long_lines_count": metrics.long_lines_count,
            "duplication_rate": metrics.duplication_rate,
            "complex_lines": metrics.complex_lines,
        }

    def find_duplicate_code_blocks(self, min_lines: int = 5) -> List[Dict[str, Any]]:
        """查找重复代码块（更高级的重复检测）

        Args:
            min_lines: 最小行数

        Returns:
            重复代码块列表
        """
        duplicates = []

        # 收集所有代码块
        blocks: dict[tuple[str, ...], list[tuple[str, int]]] = {}  # (file, start_line) -> block_lines

        for py_file in self.target_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # 滑动窗口提取代码块
                for i in range(len(lines) - min_lines + 1):
                    block = tuple(lines[i : i + min_lines])
                    if block not in blocks:
                        blocks[block] = []
                    blocks[block].append((str(py_file), i + 1))

            except Exception:
                continue

        # 查找重复
        for block, locations in blocks.items():
            if len(locations) > 1:
                duplicates.append(
                    {
                        "occurrences": len(locations),
                        "locations": locations,
                        "lines": min_lines,
                    }
                )

        # 按重复次数排序
        duplicates.sort(key=lambda x: x["occurrences"], reverse=True)

        return duplicates[:10]  # 返回前10个


def fallback_evaluate(params: Dict[str, Any], target_path: str = ".") -> float:
    """降级评估函数（无lingminopt时）

    Args:
        params: 优化参数
        target_path: 目标路径

    Returns:
        评分（越低越好）
    """
    evaluator = SimplicityEvaluator(target_path)
    return evaluator.evaluate(params)


if __name__ == "__main__":  # pragma: no cover
    # 测试
    evaluator = SimplicityEvaluator("/home/ai/lingflow/lingflow")

    params = {"complexity_threshold": 10, "duplication_penalty": 1.0, "max_line_length": 100}

    score = evaluator.evaluate(params)
    print(f"简洁性评分: {score:.2f}")

    metrics = evaluator.get_current_metrics()
    print(f"当前指标: {metrics}")

    # 查找重复代码
    print("\n查找重复代码块...")
    duplicates = evaluator.find_duplicate_code_blocks(min_lines=5)
    print(f"找到 {len(duplicates)} 个重复代码块")
    for dup in duplicates[:5]:
        print(f"  重复 {dup['occurrences']} 次，{dup['lines']} 行")
