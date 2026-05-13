"""lingflow PromptRouter - 基于Claude Code设计的智能Prompt路由系统

特性:
- 基于关键词的智能匹配
- 评分和排序系统
- 多路由策略支持
- 可扩展的规则引擎
- 完整的路由历史追踪
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class RouteStrategy(Enum):
    """路由策略"""

    KEYWORD_MATCH = "keyword_match"
    PATTERN_MATCH = "pattern_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    CUSTOM = "custom"


@dataclass
class RouteRule:
    """路由规则"""

    name: str
    keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    priority: int = 0
    strategy: RouteStrategy = RouteStrategy.KEYWORD_MATCH
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, prompt: str) -> Tuple[bool, float]:
        """检查prompt是否匹配此规则

        Args:
            prompt: 待检查的提示词

        Returns:
            Tuple[bool, float]: (是否匹配, 匹配分数)
        """
        score = 0.0

        if self.strategy == RouteStrategy.KEYWORD_MATCH:
            score = self._keyword_match_score(prompt)
        elif self.strategy == RouteStrategy.PATTERN_MATCH:
            score = self._pattern_match_score(prompt)
        else:
            score = 0.0

        return score > 0, score

    def _keyword_match_score(self, prompt: str) -> float:
        """关键词匹配评分

        Args:
            prompt: 待检查的提示词

        Returns:
            float: 匹配分数 (0.0-1.0)
        """
        if not self.keywords:
            return 0.0

        prompt_lower = prompt.lower()
        matched_count = 0

        for keyword in self.keywords:
            if keyword.lower() in prompt_lower:
                matched_count += 1

        # 评分：匹配的关键词数量 / 总关键词数量
        return matched_count / len(self.keywords) if self.keywords else 0.0

    def _pattern_match_score(self, prompt: str) -> float:
        """正则表达式匹配评分

        Args:
            prompt: 待检查的提示词

        Returns:
            float: 匹配分数 (0.0-1.0)
        """
        if not self.patterns:
            return 0.0

        matched_count = 0
        for pattern in self.patterns:
            try:
                if re.search(pattern, prompt, re.IGNORECASE):
                    matched_count += 1
            except re.error:
                continue

        return matched_count / len(self.patterns) if self.patterns else 0.0


@dataclass
class RouteTarget:
    """路由目标"""

    name: str
    agent_type: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteResult:
    """路由结果"""

    prompt: str
    matched_rules: List[Tuple[str, float]]  # (rule_name, score)
    selected_target: Optional[RouteTarget]
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def best_match(self) -> Optional[Tuple[str, float]]:
        """Optional[Tuple[str, float]]: 最佳匹配的规则名称和分数"""
        if not self.matched_rules:
            return None
        return max(self.matched_rules, key=lambda x: x[1])


class PromptRouter:
    """智能Prompt路由器

    功能:
    - 基于关键词和模式的智能匹配
    - 多目标路由
    - 评分和排序
    - 路由历史记录
    """

    def __init__(self):
        self._rules: Dict[str, RouteRule] = {}
        self._targets: Dict[str, RouteTarget] = {}
        self._history: List[RouteResult] = []
        self._default_target: Optional[RouteTarget] = None

    def add_rule(self, rule: RouteRule) -> "PromptRouter":
        """添加路由规则

        Args:
            rule: 路由规则对象

        Returns:
            PromptRouter: 返回自身以支持链式调用
        """
        self._rules[rule.name] = rule
        return self

    def add_target(self, target: RouteTarget) -> "PromptRouter":
        """添加路由目标

        Args:
            target: 路由目标对象

        Returns:
            PromptRouter: 返回自身以支持链式调用
        """
        self._targets[target.name] = target
        return self

    def set_default_target(self, target: RouteTarget) -> "PromptRouter":
        """设置默认目标

        Args:
            target: 默认路由目标对象

        Returns:
            PromptRouter: 返回自身以支持链式调用
        """
        self._default_target = target
        return self

    def route(self, prompt: str, top_k: int = 3) -> RouteResult:
        """
        路由prompt到最佳目标

        Args:
            prompt: 用户提示词
            top_k: 返回前k个匹配规则

        Returns:
            RouteResult: 路由结果
        """
        # 1. 匹配所有规则
        matched_rules = []
        for rule_name, rule in self._rules.items():
            matches, score = rule.matches(prompt)
            if matches:
                # 加上优先级权重
                weighted_score = score + (rule.priority * 0.1)
                matched_rules.append((rule_name, weighted_score))

        # 2. 排序（按分数降序）
        matched_rules.sort(key=lambda x: x[1], reverse=True)

        # 3. 取前k个
        top_matches = matched_rules[:top_k]

        # 4. 选择最佳目标
        selected_target = self._select_target(top_matches)

        # 5. 计算置信度
        confidence = self._calculate_confidence(top_matches)

        # 6. 创建结果
        result = RouteResult(prompt=prompt, matched_rules=top_matches, selected_target=selected_target, confidence=confidence)

        # 7. 保存历史
        self._history.append(result)

        return result

    def _select_target(self, matched_rules: List[Tuple[str, float]]) -> Optional[RouteTarget]:
        """根据匹配规则选择目标

        Args:
            matched_rules: 匹配的规则列表，包含规则名称和分数

        Returns:
            Optional[RouteTarget]: 选中的路由目标，如果没有匹配则返回默认目标
        """
        if not matched_rules:
            return self._default_target

        # 获取最佳匹配的规则名称
        best_rule_name = matched_rules[0][0]

        # 根据规则名称查找对应的目标
        # 这里我们使用元数据来关联规则和目标
        if best_rule_name in self._rules:
            rule = self._rules[best_rule_name]
            target_name = rule.metadata.get("target_name")
            if target_name and target_name in self._targets:
                return self._targets[target_name]

        return self._default_target

    def _calculate_confidence(self, matched_rules: List[Tuple[str, float]]) -> float:
        """计算路由置信度

        Args:
            matched_rules: 匹配的规则列表

        Returns:
            float: 置信度分数 (0.0-1.0)
        """
        if not matched_rules:
            return 0.0

        # 简单策略：最佳匹配的分数
        return min(matched_rules[0][1], 1.0)

    def get_statistics(self) -> Dict[str, Any]:
        """获取路由统计

        Returns:
            Dict[str, Any]: 包含路由总数、平均置信度、常用目标和规则的统计信息
        """
        if not self._history:
            return {"total_routes": 0, "avg_confidence": 0.0, "most_used_targets": [], "most_matched_rules": []}

        total_routes = len(self._history)
        avg_confidence = sum(r.confidence for r in self._history) / total_routes

        # 统计最常用的目标
        target_counts: dict[str, int] = {}
        for result in self._history:
            if result.selected_target:
                target_name = result.selected_target.name
                target_counts[target_name] = target_counts.get(target_name, 0) + 1

        most_used_targets = sorted(target_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # 统计最常匹配的规则
        rule_counts: dict[str, int] = {}
        for result in self._history:
            for rule_name, _ in result.matched_rules:
                rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1

        most_matched_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_routes": total_routes,
            "avg_confidence": avg_confidence,
            "most_used_targets": most_used_targets,
            "most_matched_rules": most_matched_rules,
        }

    def save_config(self, path: Optional[Path] = None) -> Path:
        """保存路由器配置

        Args:
            path: 配置文件保存路径，默认为 .lingflow/prompt_router_config.json

        Returns:
            Path: 保存的配置文件路径
        """
        if path is None:
            path = Path(".lingflow/prompt_router_config.json")

        # 序列化规则
        rules_data = {
            name: {
                "keywords": rule.keywords,
                "patterns": rule.patterns,
                "priority": rule.priority,
                "strategy": rule.strategy.value,
                "metadata": rule.metadata,
            }
            for name, rule in self._rules.items()
        }

        # 序列化目标
        targets_data = {
            name: {
                "agent_type": target.agent_type,
                "description": target.description,
                "capabilities": target.capabilities,
                "metadata": target.metadata,
            }
            for name, target in self._targets.items()
        }

        config = {
            "rules": rules_data,
            "targets": targets_data,
            "default_target": self._default_target.name if self._default_target else None,
            "saved_at": datetime.now().isoformat(),
        }

        with open(path, "w") as f:
            json.dump(config, f, indent=2)

        return path

    @classmethod
    def load_config(cls, path: Path) -> "PromptRouter":
        """加载路由器配置

        Args:
            path: 配置文件路径

        Returns:
            PromptRouter: 加载的路由器实例

        Raises:
            FileNotFoundError: 如果配置文件不存在
            json.JSONDecodeError: 如果配置文件格式无效
        """
        with open(path) as f:
            config = json.load(f)

        router = cls()

        # 加载规则
        for name, rule_data in config["rules"].items():
            rule = RouteRule(
                name=name,
                keywords=rule_data["keywords"],
                patterns=rule_data["patterns"],
                priority=rule_data["priority"],
                strategy=RouteStrategy(rule_data["strategy"]),
                metadata=rule_data["metadata"],
            )
            router.add_rule(rule)

        # 加载目标
        for name, target_data in config["targets"].items():
            target = RouteTarget(
                name=name,
                agent_type=target_data["agent_type"],
                description=target_data["description"],
                capabilities=target_data["capabilities"],
                metadata=target_data["metadata"],
            )
            router.add_target(target)

        # 设置默认目标
        if config["default_target"]:
            default_target = router._targets.get(config["default_target"])
            if default_target:
                router.set_default_target(default_target)

        return router

    def clear_history(self):
        """清除路由历史记录"""
        self._history.clear()


# ============================================================================
# 预定义路由配置
# ============================================================================


def create_default_router() -> PromptRouter:
    """创建默认的 PromptRouter 配置

    预定义了四个路由目标：
    - code_analyzer: 代码分析和优化
    - writer: 文档和内容生成
    - tester: 测试代码生成
    - explainer: 概念解释和教学

    Returns:
        PromptRouter: 配置好的路由器实例
    """

    router = PromptRouter()

    # 定义路由目标
    targets = [
        RouteTarget(
            name="code_analyzer",
            agent_type="CodeAnalysisAgent",
            description="代码分析和优化",
            capabilities=["静态分析", "性能优化", "代码重构"],
        ),
        RouteTarget(
            name="writer",
            agent_type="WriterAgent",
            description="文档和内容生成",
            capabilities=["文档生成", "内容创作", "翻译"],
        ),
        RouteTarget(
            name="tester",
            agent_type="TestingAgent",
            description="测试代码生成",
            capabilities=["单元测试", "集成测试", "测试优化"],
        ),
        RouteTarget(
            name="explainer",
            agent_type="ExplainerAgent",
            description="概念解释和教学",
            capabilities=["概念解释", "教程生成", "知识解答"],
        ),
    ]

    for target in targets:
        router.add_target(target)

    # 定义路由规则
    rules = [
        RouteRule(
            name="code_analysis",
            keywords=["代码", "优化", "重构", "性能", "分析"],
            priority=1,
            metadata={"target_name": "code_analyzer"},
        ),
        RouteRule(
            name="testing",
            keywords=["测试", "单元测试", "测试用例", "测试覆盖"],
            priority=1,
            metadata={"target_name": "tester"},
        ),
        RouteRule(
            name="writing", keywords=["写", "文档", "生成文档", "创作", "翻译"], priority=1, metadata={"target_name": "writer"}
        ),
        RouteRule(
            name="explanation",
            keywords=["解释", "什么是", "如何", "为什么", "原理"],
            priority=1,
            metadata={"target_name": "explainer"},
        ),
    ]

    for rule in rules:
        router.add_rule(rule)

    # 设置默认目标
    router.set_default_target(targets[0])

    return router


def create_code_focused_router() -> PromptRouter:
    """创建代码导向的 PromptRouter

    预定义了三个代码相关的路由目标：
    - python_expert: Python 专家
    - web_dev: Web 开发专家
    - data_science: 数据科学专家

    Returns:
        PromptRouter: 配置好的代码导向路由器实例
    """

    router = PromptRouter()

    # 代码相关目标
    targets = [
        RouteTarget(name="python_expert", agent_type="PythonExpertAgent", description="Python专家"),
        RouteTarget(name="web_dev", agent_type="WebDevAgent", description="Web开发专家"),
        RouteTarget(name="data_science", agent_type="DataScienceAgent", description="数据科学专家"),
    ]

    for target in targets:
        router.add_target(target)

    # 代码相关规则
    rules = [
        RouteRule(
            name="python",
            keywords=["python", "django", "flask", "pandas"],
            priority=2,
            metadata={"target_name": "python_expert"},
        ),
        RouteRule(
            name="web", keywords=["html", "css", "javascript", "react", "vue"], priority=2, metadata={"target_name": "web_dev"}
        ),
        RouteRule(
            name="data",
            keywords=["数据", "机器学习", "深度学习", "ai", "模型"],
            priority=2,
            metadata={"target_name": "data_science"},
        ),
    ]

    for rule in rules:
        router.add_rule(rule)

    return router
