"""
LingFlow CLI 辅助函数

用于降低主命令函数的复杂度，提取可重用的逻辑。
"""

import sys
from typing import List, Tuple, Dict, Any
from lingflow.self_optimizer.phase5.adapters import (
    SemgrepAdapter,
    RuffAdapter,
    PylintAdapter,
)
from lingflow.self_optimizer.phase5 import (
    RuleExtractor,
    InMemoryKnowledgeBase,
)
from lingflow.self_optimizer.phase5.patterns import PatternRecognizer


def detect_available_tools(verbose: bool = False) -> List[str]:
    """检测可用的AI工具

    Args:
        verbose: 是否显示详细信息

    Returns:
        可用工具名称列表
    """
    tool_list = []
    available_adapters = [
        ("semgrep", SemgrepAdapter),
        ("ruff", RuffAdapter),
        ("pylint", PylintAdapter),
    ]

    for tool_name, adapter_cls in available_adapters:
        try:
            adapter = adapter_cls({})
            if adapter.check_available():
                tool_list.append(tool_name)
                if verbose:
                    version = adapter.get_version()
                    print(f"  ✓ {tool_name}: {version}")
        except Exception as e:
            if verbose:
                print(f"  ✗ {tool_name}: 不可用")

    return tool_list


def run_tool_scans(
    tool_list: List[str],
    target: str,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """运行AI工具扫描

    Args:
        tool_list: 工具名称列表
        target: 目标路径
        verbose: 是否显示详细信息

    Returns:
        收集到的所有反馈列表
    """
    all_feedback = []
    adapter_map = {
        "semgrep": SemgrepAdapter,
        "ruff": RuffAdapter,
        "pylint": PylintAdapter,
    }

    with click_progressbar(tool_list, label="收集反馈") as bar:
        for tool_name in bar:
            adapter_cls = adapter_map.get(tool_name)
            if not adapter_cls:
                continue

            adapter = adapter_cls({})
            try:
                feedback = adapter.run_scan(target)
                all_feedback.extend(feedback)
                if verbose:
                    print(f"\n  {tool_name}: 发现 {len(feedback)} 个问题")
            except Exception as e:
                if verbose:
                    print(f"\n  {tool_name}: 扫描失败 - {e}")

    return all_feedback


def extract_and_save_rules(
    all_feedback: List[Dict[str, Any]],
    target: str,
    rules_only: bool = False,
    verbose: bool = False
) -> Tuple[List[Dict], List, object]:
    """从反馈中提取规则并保存

    Args:
        all_feedback: 收集到的反馈
        target: 目标路径
        rules_only: 是否仅提取规则
        verbose: 是否显示详细信息

    Returns:
        (规则列表, 模式列表, 知识库对象) 元组
    """
    # 提取规则
    if verbose:
        print(f"\n🔍 提取规则...")

    extractor = RuleExtractor(
        min_frequency=2,
        min_confidence=0.6,
        max_rules=500
    )

    rules = extractor.extract_rules(all_feedback)
    print(f"✓ 提取了 {len(rules)} 条规则")

    # 模式识别
    patterns = []
    if not rules_only:
        if verbose:
            print(f"\n🔍 识别模式...")

        recognizer = PatternRecognizer()

        for detector in recognizer.detectors:
            try:
                found = detector.detect(target)
                patterns.extend(found)
            except Exception as e:
                if verbose:
                    print(f"  ✗ {detector.__class__.__name__}: {e}")

        print(f"✓ 识别了 {len(patterns)} 个模式")

    # 保存到知识库
    knowledge_base = InMemoryKnowledgeBase()

    for rule in rules:
        knowledge_base.add_rule(rule)

    for pattern in patterns:
        knowledge_base.add_pattern(pattern)

    return rules, patterns, knowledge_base


def click_progressbar(iterable, **kwargs):
    """进度条的兼容包装器"""
    try:
        from click import progressbar
        return progressbar(iterable, **kwargs)
    except ImportError:
        # 如果没有click，返回简单的迭代器
        return iterable
