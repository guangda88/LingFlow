"""
LingFlow 自优化评估器
评估代码结构质量
"""

import ast
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


def _get_code_review_module():
    """获取code-review模块（可选）"""
    try:
        skills_path = Path(__file__).parent.parent.parent / "skills" / "code-review"
        impl_path = skills_path / "implementation.py"

        if impl_path.exists():
            spec = importlib.util.spec_from_file_location("code_review_impl", impl_path)
            module = importlib.util.module_from_spec(spec)
            return module, spec
    except Exception:
        pass

    return None, None


@dataclass
class StructureMetrics:
    """结构指标"""

    total_classes: int
    large_classes: int
    total_methods: int
    complex_methods: int
    avg_complexity: float
    avg_class_size: float
    avg_method_count: float
    high_coupling: int
    violations: int


class StructureEvaluator:
    """结构评估器"""

    def __init__(self, target_path: str = "."):
        """
        Args:
            target_path: 目标代码路径
        """
        self.target_path = Path(target_path)

    def evaluate(self, params: Dict[str, Any]) -> float:
        """评估结构质量（用于LingMinOpt）

        Args:
            params: 优化参数
                - max_class_size: 最大类大小
                - max_method_count: 最大方法数
                - max_complexity: 最大复杂度
                - max_nesting_depth: 最大嵌套深度
                - coupling_limit: 耦合度限制

        Returns:
            结构质量分数（越低越好）
        """
        # 1. 分析代码结构
        metrics = self._analyze_structure(params)

        # 2. 计算违规分数
        violations = metrics.violations

        # 3. 返回分数（越低越好）
        return float(violations)

    def _analyze_structure(self, params: Dict[str, Any]) -> StructureMetrics:
        """分析代码结构"""
        max_class_size = params.get("max_class_size", 200)
        max_method_count = params.get("max_method_count", 15)
        max_complexity = params.get("max_complexity", 10)

        total_classes = 0
        large_classes = 0
        total_methods = 0
        complex_methods = 0
        complexity_sum = 0
        class_sizes = []
        method_counts = []
        violations = 0
        high_coupling = 0

        # 遍历Python文件
        for py_file in self.target_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    source = f.read()

                tree = ast.parse(source)

                # 分析每个类
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        total_classes += 1
                        class_size = self._count_class_lines(node, source)
                        class_sizes.append(class_size)

                        if class_size > max_class_size:
                            large_classes += 1
                            violations += 1

                        # 统计方法数
                        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                        method_counts.append(method_count)
                        total_methods += method_count

                        if method_count > max_method_count:
                            violations += 1

                        # 分析方法复杂度
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                complexity = self._calculate_complexity(item)
                                complexity_sum += complexity

                                if complexity > max_complexity:
                                    complex_methods += 1
                                    violations += 1

            except (SyntaxError, UnicodeDecodeError, PermissionError, OSError) as e:
                # 跳过解析错误的文件
                import logging

                logging.getLogger(__name__).warning(f"无法解析文件 {py_file}: {e}")
                continue

        # 计算平均值
        avg_class_size = sum(class_sizes) / len(class_sizes) if class_sizes else 0
        avg_method_count = sum(method_counts) / len(method_counts) if method_counts else 0
        avg_complexity = complexity_sum / total_methods if total_methods > 0 else 0

        return StructureMetrics(
            total_classes=total_classes,
            large_classes=large_classes,
            total_methods=total_methods,
            complex_methods=complex_methods,
            avg_complexity=avg_complexity,
            avg_class_size=avg_class_size,
            avg_method_count=avg_method_count,
            high_coupling=high_coupling,
            violations=violations,
        )

    def _count_class_lines(self, class_node: ast.ClassDef, source: str) -> int:
        """计算类的行数"""
        if not class_node.body:
            return 0

        start_line = class_node.lineno
        end_line = class_node.body[-1].end_lineno if class_node.body[-1].end_lineno else start_line
        return end_line - start_line + 1

    def _calculate_complexity(self, func_node: ast.FunctionDef) -> int:
        """计算圈复杂度（简化版）"""
        complexity = 1  # 基础复杂度

        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前代码指标（不含参数优化）"""
        # 使用默认参数
        default_params = {
            "max_class_size": 500,
            "max_method_count": 25,
            "max_complexity": 20,
            "max_nesting_depth": 6,
            "coupling_limit": 15.0,
        }

        metrics = self._analyze_structure(default_params)

        return {
            "structure_violations": metrics.violations,
            "large_classes_count": metrics.large_classes,
            "complex_methods_count": metrics.complex_methods,
            "avg_complexity": metrics.avg_complexity,
            "avg_class_size": metrics.avg_class_size,
            "avg_method_count": metrics.avg_method_count,
            "total_classes": metrics.total_classes,
            "total_methods": metrics.total_methods,
        }

    def run_code_review(self) -> Optional[Dict[str, Any]]:
        """运行代码审查（使用现有技能，可选）"""
        try:
            # 尝试动态加载code-review技能
            module, spec = _get_code_review_module()
            if module and spec:
                spec.loader.exec_module(module)

                params = {"focus": "architecture", "files": [str(self.target_path)], "strict": True}

                return getattr(module, "review_code", lambda x: {})(params)
        except Exception:
            pass

        # 如果加载失败，返回空结果
        return None


def fallback_evaluate(params: Dict[str, Any], target_path: str = ".") -> float:
    """降级评估函数（无LingMinOpt时的网格搜索）

    Args:
        params: 优化参数
        target_path: 目标路径

    Returns:
        评分（越低越好）
    """
    evaluator = StructureEvaluator(target_path)
    return evaluator.evaluate(params)


if __name__ == "__main__":  # pragma: no cover
    # 测试
    evaluator = StructureEvaluator("/home/ai/LingFlow")

    params = {
        "max_class_size": 200,
        "max_method_count": 15,
        "max_complexity": 10,
        "max_nesting_depth": 4,
        "coupling_limit": 10.0,
    }

    score = evaluator.evaluate(params)
    print(f"结构评分: {score}")

    metrics = evaluator.get_current_metrics()
    print(f"当前指标: {metrics}")
