#!/usr/bin/env python3
"""
LingFlow 自学习系统激活脚本

功能:
1. 初始化知识库
2. 运行AI工具扫描代码库
3. 从反馈中提取规则
4. 存入知识库

使用:
    python scripts/activate_self_learning.py [--scan] [--learn] [--report]
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lingflow.self_optimizer.phase5.knowledge import KnowledgeBase
from lingflow.self_optimizer.phase5.learning import RuleExtractor, RuleDeduplicator, RuleValidator
from lingflow.self_optimizer.phase5.patterns import PatternRecognizer
from lingflow.self_optimizer.phase5.adapters.ruff_adapter import RuffAdapter
from lingflow.self_optimizer.phase5.adapters.semgrep_adapter import SemgrepAdapter
from lingflow.self_optimizer.phase5.adapters.pylint_adapter import PylintAdapter
from lingflow.self_optimizer.phase5.models import (
    FeedbackItem,
    FeedbackCategory,
    ToolType,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(project_root / ".lingflow" / "logs" / "self_learning.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class SelfLearningSystem:
    """自学习系统 - 统一管理学习流程"""

    def __init__(self, project_root: Path = None):
        """初始化自学习系统"""
        self.project_root = project_root or Path.cwd()

        # 确保必要目录存在
        (self.project_root / ".lingflow" / "knowledge").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".lingflow" / "logs").mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.knowledge_base = KnowledgeBase()
        self.rule_extractor = RuleExtractor(min_frequency=2, min_confidence=0.5)
        self.deduplicator = RuleDeduplicator()
        self.validator = RuleValidator(min_quality_score=0.3)  # 降低阈值
        self.pattern_recognizer = PatternRecognizer()

        # AI工具适配器
        self.adapters = self._initialize_adapters()

    def _initialize_adapters(self) -> Dict[str, Any]:
        """初始化AI工具适配器"""
        adapters = {}

        # Ruff适配器
        try:
            ruff = RuffAdapter()
            if ruff.check_available():
                adapters["ruff"] = ruff
                logger.info(f"Ruff 可用: 版本 {ruff.get_version()}")
            else:
                logger.warning("Ruff 不可用")
        except Exception as e:
            logger.warning(f"Ruff 初始化失败: {e}")

        # Semgrep适配器
        try:
            semgrep = SemgrepAdapter()
            if semgrep.check_available():
                adapters["semgrep"] = semgrep
                logger.info(f"Semgrep 可用: 版本 {semgrep.get_version()}")
            else:
                logger.warning("Semgrep 不可用")
        except Exception as e:
            logger.warning(f"Semgrep 初始化失败: {e}")

        # Pylint适配器
        try:
            pylint = PylintAdapter()
            if pylint.check_available():
                adapters["pylint"] = pylint
                logger.info(f"Pylint 可用: 版本 {pylint.get_version()}")
            else:
                logger.warning("Pylint 不可用")
        except Exception as e:
            logger.warning(f"Pylint 初始化失败: {e}")

        return adapters

    def scan_codebase(self, target_path: str = None) -> List[FeedbackItem]:
        """扫描代码库，收集反馈

        Args:
            target_path: 目标路径，默认扫描整个项目

        Returns:
            反馈项列表
        """
        if target_path is None:
            target_path = str(self.project_root)

        all_feedback = []

        for name, adapter in self.adapters.items():
            logger.info(f"运行 {name} 扫描...")
            try:
                feedback = adapter.run_scan(target_path)
                all_feedback.extend(feedback)
                logger.info(f"{name} 发现 {len(feedback)} 条反馈")
            except Exception as e:
                logger.error(f"{name} 扫描失败: {e}")

        return all_feedback

    def learn_from_feedback(self, feedback_items: List[FeedbackItem]) -> int:
        """从反馈中学习规则

        Args:
            feedback_items: 反馈项列表

        Returns:
            学习到的规则数量
        """
        if not feedback_items:
            logger.warning("没有反馈可供学习")
            return 0

        logger.info(f"从 {len(feedback_items)} 条反馈中提取规则...")

        # 提取规则
        rules = self.rule_extractor.extract_rules(feedback_items)
        logger.info(f"提取了 {len(rules)} 条原始规则")

        # 去重
        rules = self.deduplicator.deduplicate(rules)
        logger.info(f"去重后剩余 {len(rules)} 条规则")

        # 验证
        rules = self.validator.validate_batch(rules)
        logger.info(f"验证通过 {len(rules)} 条规则")

        # 存入知识库
        count = self.knowledge_base.add_rules_batch(rules)
        logger.info(f"成功存储 {count} 条规则到知识库")

        return count

    def recognize_patterns(self, source_dir: str = None) -> List[Dict[str, Any]]:
        """识别代码模式

        Args:
            source_dir: 源代码目录

        Returns:
            识别的模式列表
        """
        if source_dir is None:
            source_dir = str(self.project_root / "lingflow")

        patterns = []
        source_path = Path(source_dir)

        if not source_path.exists():
            logger.warning(f"源目录不存在: {source_dir}")
            return patterns

        # 扫描Python文件
        for py_file in source_path.rglob("*.py"):
            try:
                file_patterns = self.pattern_recognizer.recognize_from_file(str(py_file))
                patterns.extend(file_patterns)
            except Exception as e:
                logger.debug(f"模式识别失败 {py_file}: {e}")

        logger.info(f"识别到 {len(patterns)} 个代码模式")
        return patterns

    def generate_report(self) -> Dict[str, Any]:
        """生成学习报告

        Returns:
            报告字典
        """
        stats = self.knowledge_base.get_statistics()
        pattern_stats = self.pattern_recognizer.get_statistics()

        # 按类别统计规则
        category_rules = {}
        for category in FeedbackCategory:
            rules = self.knowledge_base.get_all_rules(category=category, limit=1000)
            category_rules[category.value] = len(rules)

        return {
            "timestamp": datetime.now().isoformat(),
            "knowledge_base": {
                "total_rules": stats["total_rules"],
                "by_category": stats["by_category"],
                "by_status": stats["by_status"],
                "average_quality": stats["average_quality"],
            },
            "category_breakdown": category_rules,
            "pattern_recognition": {
                "total_detectors": pattern_stats["total_detectors"],
                "total_detections": pattern_stats["total_detections"],
            },
            "available_tools": {
                name: {"available": adapter.check_available(), "version": adapter.get_version()}
                for name, adapter in self.adapters.items()
            },
        }

    def run_full_cycle(self, target_path: str = None) -> Dict[str, Any]:
        """运行完整学习周期

        Args:
            target_path: 目标路径

        Returns:
            学习结果
        """
        start_time = datetime.now()

        logger.info("=" * 50)
        logger.info("开始自学习周期")
        logger.info("=" * 50)

        # 1. 扫描代码库
        feedback = self.scan_codebase(target_path)

        # 2. 转换为FeedbackItem格式
        feedback_items = self._convert_to_feedback_items(feedback)

        # 3. 学习规则
        learned_count = self.learn_from_feedback(feedback_items)

        # 4. 识别模式
        patterns = self.recognize_patterns()

        # 5. 生成报告
        report = self.generate_report()

        duration = (datetime.now() - start_time).total_seconds()

        result = {
            "feedback_collected": len(feedback_items),
            "rules_learned": learned_count,
            "patterns_recognized": len(patterns),
            "duration_seconds": duration,
            "report": report,
        }

        logger.info("=" * 50)
        logger.info(f"学习周期完成: 耗时 {duration:.2f}秒")
        logger.info(f"  收集反馈: {len(feedback_items)}")
        logger.info(f"  学习规则: {learned_count}")
        logger.info(f"  识别模式: {len(patterns)}")
        logger.info("=" * 50)

        return result

    def _convert_to_feedback_items(self, feedback: List[Any]) -> List[FeedbackItem]:
        """转换反馈为FeedbackItem格式

        Args:
            feedback: 原始反馈列表

        Returns:
            FeedbackItem列表
        """
        items = []
        errors = []

        for item in feedback:
            try:
                # 根据类型转换
                if hasattr(item, "source"):
                    # AIFeedback类型
                    items.append(
                        FeedbackItem(
                            tool_name=item.source.value,
                            tool_type=ToolType.STATIC_ANALYZER,
                            rule_id=item.rule_id or "unknown",
                            rule_name=item.rule_id or "unknown",
                            category=item.category,
                            severity=item.severity,
                            message=item.message,
                            file_path=item.file_path,
                            line=item.line_no,
                            snippet=item.code_snippet,
                            suggestion=item.suggestion,
                            confidence=0.8,
                        )
                    )
            except Exception as e:
                errors.append(str(e))
                logger.debug(f"反馈转换失败: {e}")
                continue

        if errors:
            logger.warning(f"转换中有 {len(errors)} 个错误")
            # 只记录前几个错误
            for err in errors[:3]:
                logger.debug(f"  错误: {err}")

        return items


def save_report(report: Dict[str, Any], output_path: Path):
    """保存报告到文件

    Args:
        report: 报告字典
        output_path: 输出路径
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"报告已保存: {output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LingFlow 自学习系统")
    parser.add_argument("--scan", action="store_true", help="运行代码扫描")
    parser.add_argument("--learn", action="store_true", help="从反馈中学习规则")
    parser.add_argument("--pattern", action="store_true", help="识别代码模式")
    parser.add_argument("--report", action="store_true", help="生成报告")
    parser.add_argument("--full", action="store_true", help="运行完整学习周期")
    parser.add_argument("--target", type=str, help="目标路径 (默认: 项目根目录)")
    parser.add_argument("--output", type=str, help="报告输出路径")

    args = parser.parse_args()

    # 初始化系统
    system = SelfLearningSystem(project_root)

    # 如果没有指定任何操作，默认运行完整周期
    if not any([args.scan, args.learn, args.pattern, args.report, args.full]):
        args.full = True

    result = {}

    try:
        if args.full:
            result = system.run_full_cycle(args.target)

            # 保存报告
            if args.output:
                save_report(result["report"], Path(args.output))
            else:
                report_path = (
                    project_root
                    / ".lingflow"
                    / "reports"
                    / f"self_learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                save_report(result["report"], report_path)

        if args.scan:
            feedback = system.scan_codebase(args.target)
            print(f"扫描完成，收集 {len(feedback)} 条反馈")

        if args.learn:
            feedback = system.scan_codebase(args.target)
            items = system._convert_to_feedback_items(feedback)
            count = system.learn_from_feedback(items)
            print(f"学习完成，学习 {count} 条规则")

        if args.pattern:
            patterns = system.recognize_patterns(args.target)
            print(f"模式识别完成，识别 {len(patterns)} 个模式")

        if args.report:
            report = system.generate_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))

            if args.output:
                save_report(report, Path(args.output))

    except KeyboardInterrupt:
        logger.info("用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
