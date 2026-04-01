"""
LingMinOpt 搜索空间定义
支持离散、连续、分类参数
"""

from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

class ParameterType(Enum):
    """参数类型"""
    DISCRETE = "discrete"       # 离散参数（从选项中选择）
    CONTINUOUS = "continuous"   # 连续参数（在范围内）
    CATEGORICAL = "categorical" # 分类参数（非数值）

@dataclass
class Parameter:
    """参数定义"""
    name: str
    type: ParameterType
    choices: Optional[List[Any]] = None     # 离散/分类参数的选项
    min_value: Optional[float] = None       # 连续参数的最小值
    max_value: Optional[float] = None       # 连续参数的最大值

    def validate(self, value: Any) -> bool:
        """验证参数值"""
        if self.type == ParameterType.DISCRETE:
            return value in self.choices
        elif self.type == ParameterType.CONTINUOUS:
            return self.min_value <= value <= self.max_value
        elif self.type == ParameterType.CATEGORICAL:
            return value in self.choices
        return False

class SearchSpace:
    """搜索空间"""

    def __init__(self):
        self.parameters: Dict[str, Parameter] = {}

    def add_discrete(self, name: str, choices: List[Any]):
        """添加离散参数

        Example:
            search_space.add_discrete("max_depth", [5, 10, 15, 20])
        """
        self.parameters[name] = Parameter(
            name=name,
            type=ParameterType.DISCRETE,
            choices=choices
        )

    def add_continuous(self, name: str, min_value: float, max_value: float):
        """添加连续参数

        Example:
            search_space.add_continuous("learning_rate", 0.001, 0.1)
        """
        self.parameters[name] = Parameter(
            name=name,
            type=ParameterType.CONTINUOUS,
            min_value=min_value,
            max_value=max_value
        )

    def add_categorical(self, name: str, choices: List[str]):
        """添加分类参数

        Example:
            search_space.add_categorical("optimizer", ["adam", "sgd", "rmsprop"])
        """
        self.parameters[name] = Parameter(
            name=name,
            type=ParameterType.CATEGORICAL,
            choices=choices
        )

    def sample(self) -> Dict[str, Any]:
        """随机采样"""
        import random

        params = {}
        for name, param in self.parameters.items():
            if param.type == ParameterType.DISCRETE:
                params[name] = random.choice(param.choices)
            elif param.type == ParameterType.CONTINUOUS:
                params[name] = random.uniform(param.min_value, param.max_value)
            elif param.type == ParameterType.CATEGORICAL:
                params[name] = random.choice(param.choices)

        return params

    def map_to_vector(self, params: Dict[str, Any]) -> np.ndarray:
        """将参数映射到向量空间（归一化到[0,1]）

        Example:
            vector = search_space.map_to_vector({"max_depth": 10, "lr": 0.01})
        """
        vector = []

        for name, param in self.parameters.items():
            value = params.get(name)

            if param.type == ParameterType.DISCRETE or param.type == ParameterType.CATEGORICAL:
                # One-hot编码
                for choice in param.choices:
                    vector.append(1.0 if value == choice else 0.0)

            elif param.type == ParameterType.CONTINUOUS:
                # 归一化到[0,1]
                normalized = (value - param.min_value) / (param.max_value - param.min_value)
                vector.append(normalized)

        return np.array(vector)

    def map_to_params(self, vector: np.ndarray) -> Dict[str, Any]:
        """将向量映射回参数空间

        Example:
            params = search_space.map_to_params(np.array([0.5, 0.3, 1.0, 0.0]))
        """
        params = {}
        idx = 0

        for name, param in self.parameters.items():
            if param.type == ParameterType.DISCRETE or param.type == ParameterType.CATEGORICAL:
                # One-hot解码
                one_hot = vector[idx:idx + len(param.choices)]
                choice_idx = int(np.argmax(one_hot))
                params[name] = param.choices[choice_idx]
                idx += len(param.choices)

            elif param.type == ParameterType.CONTINUOUS:
                # 反归一化
                normalized = vector[idx]
                value = normalized * (param.max_value - param.min_value) + param.min_value
                params[name] = value
                idx += 1

        return params

    @property
    def dimension(self) -> int:
        """搜索空间维度（编码后的向量长度）"""
        dim = 0
        for param in self.parameters.values():
            if param.type in [ParameterType.DISCRETE, ParameterType.CATEGORICAL]:
                dim += len(param.choices)
            elif param.type == ParameterType.CONTINUOUS:
                dim += 1
        return dim

    def summary(self) -> str:
        """获取搜索空间摘要"""
        lines = ["SearchSpace Summary:", ""]

        for name, param in self.parameters.items():
            if param.type == ParameterType.DISCRETE:
                lines.append(f"  {name}: discrete, choices={param.choices}")
            elif param.type == ParameterType.CONTINUOUS:
                lines.append(f"  {name}: continuous, range=[{param.min_value}, {param.max_value}]")
            elif param.type == ParameterType.CATEGORICAL:
                lines.append(f"  {name}: categorical, choices={param.choices}")

        lines.append(f"\nTotal parameters: {len(self.parameters)}")
        lines.append(f"Encoded dimension: {self.dimension}")

        return "\n".join(lines)
