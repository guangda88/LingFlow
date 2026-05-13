"""
lingflow Phase 4: 参数敏感性分析器

分析参数对优化目标的影响程度，识别关键参数和敏感区域。
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SensitivityResult:
    """敏感性分析结果"""

    parameter_name: str
    sensitivity_score: float  # 0-1，越高越敏感
    method: str
    baseline_value: float
    variations: List[float] = field(default_factory=list)
    variation_impacts: List[float] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "parameter": self.parameter_name,
            "sensitivity_score": self.sensitivity_score,
            "method": self.method,
            "baseline_value": self.baseline_value,
            "variations": self.variations,
            "variation_impacts": self.variation_impacts,
        }


@dataclass
class SobolResult:
    """Sobol敏感性分析结果（全局敏感性）"""

    first_order: Dict[str, float]  # 一阶效应（主效应）
    total_order: Dict[str, float]  # 总效应（包含交互）
    parameters: List[str]
    timestamp: float = field(default_factory=time.time)

    def get_most_sensitive(self, n: int = 5) -> List[tuple]:
        """获取最敏感的n个参数"""
        sorted_params = sorted(self.total_order.items(), key=lambda x: x[1], reverse=True)
        return sorted_params[:n]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"first_order": self.first_order, "total_order": self.total_order, "parameters": self.parameters}


class SensitivityAnalyzer:
    """参数敏感性分析器

    提供局部敏感性分析和全局敏感性分析（Sobol）。
    """

    def __init__(
        self, search_space: Dict[str, Any], objective: Callable[[Dict[str, Any]], float], base_params: Dict[str, Any] = None
    ):
        """初始化敏感性分析器

        Args:
            search_space: 搜索空间定义
            objective: 目标函数
            base_params: 基线参数（用于局部分析）
        """
        self.search_space = search_space
        self.objective = objective
        self.base_params = base_params or self._get_default_params()

    def _get_default_params(self) -> Dict[str, Any]:
        """获取默认参数（搜索空间的中点）"""
        params = {}

        for name, space in self.search_space.items():
            space_type = space.get("type")

            if space_type == "categorical":
                params[name] = space["choices"][0]
            elif space_type in ("int", "float"):
                params[name] = (space["min"] + space["max"]) / 2
            elif space_type == "log":
                import math

                params[name] = math.sqrt(space["min"] * space["max"])

        return params

    def analyze_local(self, n_samples: int = 10, perturbation_ratio: float = 0.1) -> Dict[str, SensitivityResult]:
        """局部敏感性分析

        通过单变量扰动分析参数敏感性。

        Args:
            n_samples: 每个参数的采样数
            perturbation_ratio: 扰动比例

        Returns:
            参数名 -> 敏感性结果
        """
        results = {}

        # 计算基线分数
        baseline_score = self.objective(self.base_params)

        # 对每个参数进行分析
        for param_name, space in self.search_space.items():
            result = self._analyze_parameter_local(param_name, space, baseline_score, n_samples, perturbation_ratio)
            results[param_name] = result

        return results

    def _analyze_parameter_local(
        self, param_name: str, space: Dict[str, Any], baseline_score: float, n_samples: int, perturbation_ratio: float
    ) -> SensitivityResult:
        """分析单个参数的局部敏感性"""
        variations = []
        impacts = []

        space_type = space.get("type")

        if space_type == "categorical":
            # 测试所有类别
            for value in space["choices"]:
                params = self.base_params.copy()
                params[param_name] = value

                try:
                    score = self.objective(params)
                    impact = abs(score - baseline_score) / (baseline_score + 1e-6)
                except Exception:
                    impact = 0.0

                variations.append(value)
                impacts.append(impact)

        elif space_type in ("int", "float"):
            # 在范围内采样
            min_val = space["min"]
            max_val = space["max"]

            for i in range(n_samples):
                # 计算扰动值
                if space_type == "int":
                    base_value = self.base_params.get(param_name, min_val)
                    perturbation = int((max_val - min_val) * perturbation_ratio)
                    test_value = base_value + np.random.randint(-perturbation, perturbation + 1)
                    test_value = max(min_val, min(max_val, test_value))
                else:
                    base_value = self.base_params.get(param_name, min_val)
                    perturbation = (max_val - min_val) * perturbation_ratio
                    test_value = base_value + np.random.uniform(-perturbation, perturbation)
                    test_value = max(min_val, min(max_val, test_value))

                params = self.base_params.copy()
                params[param_name] = test_value

                try:
                    score = self.objective(params)
                    impact = abs(score - baseline_score) / (baseline_score + 1e-6)
                except Exception:
                    impact = 0.0

                variations.append(test_value)
                impacts.append(impact)

        # 计算敏感性分数（归一化到0-1）
        # 使用相对变化的标准差
        if impacts:
            sensitivity_score = min(1.0, np.std(impacts) / (np.mean(impacts) + 1e-6) if np.mean(impacts) > 0 else 0.0)
        else:
            sensitivity_score = 0.0

        return SensitivityResult(
            parameter_name=param_name,
            sensitivity_score=sensitivity_score,
            method="local_perturbation",
            baseline_value=self.base_params.get(param_name),
            variations=variations,
            variation_impacts=impacts,
        )

    def analyze_global_sobol(self, n_samples: int = 100, calc_second_order: bool = False) -> SobolResult:
        """全局敏感性分析（Sobol方法）

        使用Sobol序列进行采样，计算一阶和总效应指数。

        Args:
            n_samples: 样本数
            calc_second_order: 是否计算二阶效应

        Returns:
            Sobol分析结果
        """
        try:
            from SALib.analyze import sobol
            from SALib.sample import saltelli
        except ImportError:
            logger.warning("SALib未安装，使用简化的全局敏感性分析")
            return self._analyze_global_simple(n_samples)

        # 定义SALib问题
        problem = {"num_vars": len(self.search_space), "names": list(self.search_space.keys()), "bounds": []}

        for name, space in self.search_space.items():
            space_type = space.get("type")

            if space_type == "categorical":
                # 对类别变量，使用0到n-1的范围
                problem["bounds"].append([0, len(space["choices"]) - 1])
            else:
                problem["bounds"].append([space["min"], space["max"]])

        # 生成样本
        param_values = saltelli.sample(problem, n_samples, calc_second_order=calc_second_order)

        # 评估目标函数
        Y = []
        for params_dict in self._convert_samples_to_dicts(param_values):
            try:
                score = self.objective(params_dict)
                Y.append(score)
            except Exception as e:
                logger.error(f"评估失败: {e}")
                Y.append(float("inf"))

        # 执行Sobol分析
        Si = sobol.analyze(problem, np.array(Y), calc_second_order=calc_second_order)

        # 提取结果
        first_order = {}
        total_order = {}

        for i, name in enumerate(problem["names"]):
            first_order[name] = Si["S1"][i] if "S1" in Si else 0.0
            total_order[name] = Si["ST"][i] if "ST" in Si else 0.0

        return SobolResult(first_order=first_order, total_order=total_order, parameters=list(problem["names"]))

    def _analyze_global_simple(self, n_samples: int) -> SobolResult:
        """简化的全局敏感性分析（不依赖SALib）"""
        # 随机采样
        first_order = {}
        total_order = {}

        # 为每个参数生成随机值并评估
        param_ranges = {}

        for name, space in self.search_space.items():
            space_type = space.get("type")

            if space_type == "categorical":
                param_ranges[name] = space["choices"]
            else:
                param_ranges[name] = (space["min"], space["max"])

        # 评估所有参数组合的方差贡献
        base_score = self.objective(self.base_params)

        for param_name in self.search_space.keys():
            # 单独变化该参数

            if param_name in param_ranges:
                rng = param_ranges[param_name]

                if isinstance(rng, list):
                    # 类别变量
                    test_values = rng
                else:
                    # 数值变量
                    test_values = np.linspace(rng[0], rng[1], min(10, n_samples))

                impacts = []
                for val in test_values:
                    params = self.base_params.copy()
                    params[param_name] = val

                    try:
                        score = self.objective(params)
                        impact = abs(score - base_score)
                        impacts.append(impact)
                    except Exception:
                        continue

                # 计算敏感性（归一化）
                sensitivity = np.mean(impacts) / (base_score + 1e-6) if impacts else 0.0
                sensitivity = min(1.0, sensitivity)

                first_order[param_name] = sensitivity
                total_order[param_name] = sensitivity  # 简化：不考虑交互效应

        return SobolResult(first_order=first_order, total_order=total_order, parameters=list(self.search_space.keys()))

    def _convert_samples_to_dicts(self, param_values: np.ndarray) -> List[Dict[str, Any]]:
        """将SALib样本转换为参数字典"""
        param_dicts = []

        for sample in param_values:
            params = {}

            for i, (name, value) in enumerate(zip(self.search_space.keys(), sample)):
                space = self.search_space[name]
                space_type = space.get("type")

                if space_type == "categorical":
                    # 转换为整数索引并选择类别
                    idx = int(round(value))
                    idx = max(0, min(idx, len(space["choices"]) - 1))
                    params[name] = space["choices"][idx]
                elif space_type == "int":
                    params[name] = int(round(value))
                else:
                    params[name] = float(value)

            param_dicts.append(params)

        return param_dicts

    def analyze_morris(self, n_trajectories: int = 20) -> Dict[str, Dict[str, float]]:
        """Morris方法敏感性分析

        适合高维问题的筛选。

        Args:
            n_trajectories: 轨迹数

        Returns:
            参数 -> {mu, mu_star, sigma}
        """
        try:
            from SALib.analyze import morris
            from SALib.sample import morris as morris_sample
        except ImportError:
            logger.warning("SALib未安装，Morris分析不可用")
            return {}

        # 定义问题
        problem = {"num_vars": len(self.search_space), "names": list(self.search_space.keys()), "bounds": []}

        for name, space in self.search_space.items():
            space_type = space.get("type")

            if space_type == "categorical":
                problem["bounds"].append([0, len(space["choices"]) - 1])
            else:
                problem["bounds"].append([space["min"], space["max"]])

        # 生成样本
        param_values = morris_sample.sample(problem, n_trajectories, optimal_trajectories=None)

        # 评估
        Y = []
        for params_dict in self._convert_samples_to_dicts(param_values):
            try:
                score = self.objective(params_dict)
                Y.append(score)
            except Exception:
                Y.append(float("inf"))

        # 分析
        Si = morris.analyze(problem, param_values, np.array(Y))

        # 提取结果
        results = {}
        for i, name in enumerate(problem["names"]):
            results[name] = {"mu": Si["mu"][i], "mu_star": Si["mu_star"][i], "sigma": Si["sigma"][i]}

        return results


def analyze_sensitivity(
    search_space: Dict[str, Any],
    objective: Callable[[Dict[str, Any]], float],
    base_params: Dict[str, Any] = None,
    method: str = "local",
    n_samples: int = 50,
):
    """敏感性分析便捷函数

    Args:
        search_space: 搜索空间
        objective: 目标函数
        base_params: 基线参数
        method: 分析方法 (local, sobol, morris)
        n_samples: 样本数

    Returns:
        敏感性分析结果
    """
    analyzer = SensitivityAnalyzer(search_space, objective, base_params)

    if method == "local":
        return analyzer.analyze_local(n_samples=n_samples)
    elif method == "sobol":
        return analyzer.analyze_global_sobol(n_samples=n_samples)
    elif method == "morris":
        return analyzer.analyze_morris(n_trajectories=n_samples // 4)
    else:
        raise ValueError(f"未知的分析方法: {method}")


if __name__ == "__main__":  # pragma: no cover
    # 测试
    def test_objective(params):
        """测试目标函数"""
        x = params.get("x", 0)
        y = params.get("y", 0)
        z = params.get("z", 0)
        # x影响最大，y次之，z几乎无影响
        return 100 * x**2 + 10 * y + 0.1 * z

    search_space = {
        "x": {"type": "float", "min": -5, "max": 5},
        "y": {"type": "float", "min": -10, "max": 10},
        "z": {"type": "float", "min": 0, "max": 100},
    }

    base_params = {"x": 0, "y": 0, "z": 0}

    # 局部敏感性分析
    print("=== 局部敏感性分析 ===")
    local_results = analyze_sensitivity(search_space, test_objective, base_params, method="local", n_samples=20)

    for param_name, result in local_results.items():
        print(f"{param_name}: {result.sensitivity_score:.4f}")

    # 全局敏感性分析
    print("\n=== 全局敏感性分析 (Sobol) ===")
    try:
        sobol_results = analyze_sensitivity(search_space, test_objective, base_params, method="sobol", n_samples=100)

        print("总效应 (Total Order):")
        for param, score in sorted(sobol_results.total_order.items(), key=lambda x: -x[1]):
            print(f"  {param}: {score:.4f}")
    except Exception as e:
        print(f"Sobol分析失败: {e}")
