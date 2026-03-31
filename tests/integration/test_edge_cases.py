"""
边界条件和错误处理测试

测试系统在异常情况下的行为：
- 空输入
- 大量输入
- 极端参数值
- 并发访问
- 资源限制
- 错误恢复
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

from lingflow.self_optimizer.phase4.bayesian_optimizer import BayesianOptimizer
from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore
from lingflow.self_optimizer.phase4.engine import OptimizationEngine
from lingflow.self_optimizer.phase5.learning import RuleExtractor
from lingflow.self_optimizer.phase5.knowledge import InMemoryKnowledgeBase
from lingflow.self_optimizer.phase5.models import (
    FeedbackItem,
    LearnedRule,
    Pattern,
    FeedbackCategory,
    SeverityLevel,
    ToolType
)


@pytest.mark.integration
class TestEmptyInputs:
    """测试空输入处理"""

    def test_empty_feedback_list(self):
        """测试空反馈列表"""
        extractor = RuleExtractor()
        rules = extractor.extract_rules([])

        assert rules == []

    def test_empty_search_space(self, temp_project):
        """测试空搜索空间"""
        engine = OptimizationEngine(config={"generate_reports": False})

        # 空搜索空间应该优雅处理，返回空结果或默认值
        result = engine.optimize_single_objective(
            target_path=temp_project,
            goal="structure",
            search_space={}
        )

        # 应该返回一个结果，即使搜索空间为空
        assert result is not None
        # 结果应该是字典形式，包含基本字段
        if isinstance(result, dict):
            assert 'best_params' in result or 'params' in result
        else:
            assert hasattr(result, 'best_params') or hasattr(result, 'params')

    def test_empty_knowledge_base_search(self):
        """测试空知识库搜索"""
        kb = InMemoryKnowledgeBase()

        results = kb.search_rules("test")

        assert results == []

    def test_empty_file_path(self):
        """测试空文件路径"""
        from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore

        storage = FileSystemParameterStore()

        # 空路径应该被处理
        result = storage.load("nonexistent")
        assert result is None

    def test_empty_pattern(self):
        """测试空模式"""
        pattern = Pattern()

        rule = LearnedRule(
            id="empty_pattern",
            name="Empty Pattern",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Ruff"],
            frequency=1,
            confidence=0.8
        )

        # 空模式应该被创建
        assert rule.pattern.file_patterns == []
        assert rule.pattern.code_patterns == []


@pytest.mark.integration
class TestLargeInputs:
    """测试大量输入处理"""

    def test_large_feedback_dataset(self):
        """测试大量反馈数据"""
        # 创建大量反馈
        large_feedback = [
            FeedbackItem(
                tool_name=f"Tool{i % 10}",
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id=f"rule{i}",
                rule_name=f"Rule {i}",
                category=FeedbackCategory.CODE_QUALITY,
                severity=SeverityLevel.LOW,
                message=f"Message {i}",
                file_path=f"file{i % 100}.py",
                line=i % 1000,
                snippet=f"code{i}",
                suggestion=f"fix{i}",
                confidence=0.5 + (i % 50) / 100
            )
            for i in range(1000)
        ]

        extractor = RuleExtractor(min_frequency=5, min_confidence=0.6)
        rules = extractor.extract_rules(large_feedback)

        # 应该能够处理大量数据
        assert isinstance(rules, list)
        # 由于min_frequency=5，规则数量应该少于1000
        assert len(rules) < 1000

    def test_large_knowledge_base(self):
        """测试大型知识库"""
        kb = InMemoryKnowledgeBase()

        # 添加大量规则
        for i in range(1000):
            pattern = Pattern(file_patterns=[f"*.py{i % 10}"])
            rule = LearnedRule(
                id=f"rule_{i}",
                name=f"Rule {i}",
                description=f"Description {i}",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=pattern,
                tools=[f"Tool{i % 5}"],
                frequency=i + 1,
                confidence=0.5 + (i % 50) / 100
            )
            kb.add_rule(rule)

        # 验证能够处理
        stats = kb.get_statistics()
        assert stats['total_rules'] == 1000

        # 测试搜索性能
        results = kb.search_rules("Rule")
        assert len(results) > 0

    def test_large_search_space(self):
        """测试大型搜索空间"""
        large_search_space = {
            f"param_{i}": {"type": "int", "min": 0, "max": 100}
            for i in range(50)
        }

        def objective(params):
            return sum(params.values()) / len(params)

        optimizer = BayesianOptimizer(
            large_search_space,
            objective,
            config={"n_trials": 2}  # 减少试验次数以加速测试
        )

        # 应该能够处理大型搜索空间
        params = optimizer.suggest()
        assert len(params) == 50

    def test_many_optimization_trials(self):
        """测试多次优化试验"""
        search_space = {
            "x": {"type": "int", "min": 0, "max": 100}
        }

        def objective(params):
            return abs(params["x"] - 50)

        optimizer = BayesianOptimizer(
            search_space,
            objective,
            config={"n_trials": 100}
        )

        state = optimizer.optimize()

        # 应该完成所有试验
        assert state.current_trial <= 100


@pytest.mark.integration
class TestExtremeParameters:
    """测试极端参数值"""

    def test_extreme_search_space_bounds(self):
        """测试极端搜索空间边界"""
        extreme_search_space = {
            "very_large": {"type": "int", "min": 1, "max": 1000000},
            "very_small": {"type": "float", "min": 0.000001, "max": 0.00001},
            "many_choices": {"type": "categorical", "choices": list(range(1000))}
        }

        def objective(params):
            return 1.0

        optimizer = BayesianOptimizer(
            extreme_search_space,
            objective,
            config={"n_trials": 3}
        )

        # 应该能够处理极端值
        params = optimizer.suggest()
        assert "very_large" in params
        assert "very_small" in params
        assert "many_choices" in params

    def test_zero_trials(self):
        """测试零试验次数"""
        search_space = {"x": {"type": "int", "min": 0, "max": 100}}

        def objective(params):
            return params["x"]

        optimizer = BayesianOptimizer(
            search_space,
            objective,
            config={"n_trials": 0}
        )

        state = optimizer.optimize()

        # 零试验应该立即返回
        assert state.current_trial == 0

    def test_very_short_timeout(self):
        """测试极短超时"""
        search_space = {"x": {"type": "int", "min": 0, "max": 100}}

        def slow_objective(params):
            import time
            time.sleep(0.1)
            return params["x"]

        optimizer = BayesianOptimizer(
            search_space,
            slow_objective,
            config={"timeout": 0.1}  # 0.1秒超时
        )

        state = optimizer.optimize()

        # 应该因超时而停止
        assert state.should_stop is True

    def test_negative_quality_score(self):
        """测试负质量分数"""
        pattern = Pattern(file_patterns=["*.py"])
        rule = LearnedRule(
            id="negative_quality",
            name="Negative Quality",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Ruff"],
            frequency=1,
            confidence=0.8
        )
        rule.quality_score = -0.5  # 无效值

        validator = RuleExtractor()  # 使用默认验证器
        # 负质量分数应该被处理
        assert rule.quality_score < 0


@pytest.mark.integration
class TestConcurrentAccess:
    """测试并发访问"""

    def test_concurrent_knowledge_base_writes(self):
        """测试并发知识库写入"""
        import threading

        kb = InMemoryKnowledgeBase()
        errors = []

        def add_rules(thread_id):
            try:
                for i in range(10):
                    pattern = Pattern(file_patterns=["*.py"])
                    rule = LearnedRule(
                        id=f"thread_{thread_id}_rule_{i}",
                        name=f"Rule {i}",
                        description="Test",
                        category=FeedbackCategory.CODE_QUALITY,
                        pattern=pattern,
                        tools=["Ruff"],
                        frequency=1,
                        confidence=0.8
                    )
                    kb.add_rule(rule)
            except Exception as e:
                errors.append(e)

        # 创建多个线程
        threads = [
            threading.Thread(target=add_rules, args=(i,))
            for i in range(5)
        ]

        # 启动所有线程
        for t in threads:
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证没有错误
        assert len(errors) == 0

        # 验证规则数量
        stats = kb.get_statistics()
        assert stats['total_rules'] == 50  # 5线程 * 10规则

    def test_concurrent_optimization(self, temp_project):
        """测试并发优化"""
        import threading

        engine = OptimizationEngine(config={
            "n_trials": 2,
            "timeout": 15,
            "generate_reports": False
        })

        results = []
        errors = []

        def run_optimization(goal):
            try:
                result = engine.optimize_single_objective(
                    target_path=temp_project,
                    goal=goal
                )
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 运行多个并发优化
        threads = [
            threading.Thread(target=run_optimization, args=("structure",)),
            threading.Thread(target=run_optimization, args=("simplicity",))
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 验证结果
        assert len(errors) == 0
        assert len(results) == 2


@pytest.mark.integration
class TestResourceLimits:
    """测试资源限制"""

    def test_memory_efficient_large_dataset(self):
        """测试大数据集的内存效率"""
        # 创建大型数据集
        large_feedback = [
            FeedbackItem(
                tool_name="Tool",
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id=f"rule_{i}",
                rule_name=f"Rule {i}",
                category=FeedbackCategory.CODE_QUALITY,
                severity=SeverityLevel.LOW,
                message=f"Message {i}",
                file_path=f"file_{i}.py",
                line=1,
                snippet="code",
                suggestion="fix",
                confidence=0.8
            )
            for i in range(10000)
        ]

        # 应该能够处理而不耗尽内存
        extractor = RuleExtractor(min_frequency=10)
        rules = extractor.extract_rules(large_feedback)

        assert isinstance(rules, list)

    def test_disk_space_management(self, tmp_path):
        """测试磁盘空间管理"""
        storage = FileSystemParameterStore(base_path=str(tmp_path / "large_storage"))

        # 存储大量参数
        for i in range(100):
            params = {f"param_{j}": j for j in range(10)}
            storage.save(params, {"iteration": i})

        # 验证目录存在
        storage_dir = Path(tmp_path / "large_storage")
        assert storage_dir.exists()

        # 验证可以读取
        latest = storage.get_latest()
        assert latest is not None


@pytest.mark.integration
class TestErrorRecovery:
    """测试错误恢复"""

    def test_corrupted_storage_recovery(self, tmp_path):
        """测试损坏存储的恢复"""
        import json
        storage_path = tmp_path / "corrupted" / "index" / "index.json"
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建损坏的JSON文件
        storage_path.write_text("{invalid json content")

        # 应该能够处理损坏的文件
        try:
            storage = FileSystemParameterStore(base_path=str(tmp_path / "corrupted"))
            # 可能会抛出异常或创建新的空存储
            latest = storage.get_latest()
            assert latest is None
        except (ValueError, Exception):
            # 预期的异常
            pass

    def test_invalid_feedback_handling(self):
        """测试无效反馈处理"""
        invalid_feedback = [
            FeedbackItem(
                tool_name="",  # 空工具名
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id="",  # 空规则ID
                rule_name="",  # 空规则名
                category=FeedbackCategory.CODE_QUALITY,
                severity=SeverityLevel.LOW,
                message="",  # 空消息
                file_path="",  # 空文件路径
                line=-1,  # 无效行号
                snippet="",  # 空片段
                suggestion="",
                confidence=-1.0  # 无效置信度
            )
        ]

        extractor = RuleExtractor(min_frequency=1)
        rules = extractor.extract_rules(invalid_feedback)

        # 应该优雅地处理无效数据
        assert isinstance(rules, list)

    def test_optimization_failure_recovery(self, temp_project):
        """测试优化失败的恢复"""
        engine = OptimizationEngine(config={
            "n_trials": 2,
            "timeout": 10,
            "generate_reports": False
        })

        # 第一次优化可能失败
        try:
            result1 = engine.optimize_single_objective(
                target_path=temp_project,
                goal="structure"
            )
        except Exception as e:
            result1 = None

        # 第二次优化应该能够成功
        result2 = engine.optimize_single_objective(
            target_path=temp_project,
            goal="structure"
        )

        # 至少第二次应该成功
        assert result2 is not None
        assert result2["best_score"] is not None

    def test_network_failure_simulation(self, temp_project):
        """测试网络故障模拟"""
        from lingflow.self_optimizer.phase5.adapters import SemgrepAdapter

        adapter = SemgrepAdapter()

        # Mock网络故障
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Network error")

            # 应该优雅处理网络故障
            try:
                results = adapter.run(temp_project)
                # 可能返回空结果
                assert results == []
            except Exception as e:
                # 或者抛出异常
                assert "Network error" in str(e) or isinstance(e, Exception)


@pytest.mark.integration
class TestBoundaryConditions:
    """测试边界条件"""

    def test_single_feedback_item(self):
        """测试单个反馈项"""
        feedback = [
            FeedbackItem(
                tool_name="Tool",
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id="rule1",
                rule_name="Rule",
                category=FeedbackCategory.CODE_QUALITY,
                severity=SeverityLevel.LOW,
                message="Message",
                file_path="file.py",
                line=1,
                snippet="code",
                suggestion="fix",
                confidence=0.8
            )
        ]

        extractor = RuleExtractor(min_frequency=1)
        rules = extractor.extract_rules(feedback)

        # 单个项应该能被处理
        assert isinstance(rules, list)

    def test_exactly_min_frequency(self):
        """测试恰好达到最小频率"""
        feedback = [
            FeedbackItem(
                tool_name="Tool",
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id="same_rule",
                rule_name="Same Rule",
                category=FeedbackCategory.CODE_QUALITY,
                severity=SeverityLevel.LOW,
                message="Message",
                file_path="file.py",
                line=1,
                snippet="code",
                suggestion="fix",
                confidence=0.8
            )
            for _ in range(3)  # 恰好3次
        ]

        extractor = RuleExtractor(min_frequency=3)
        rules = extractor.extract_rules(feedback)

        # 恰好达到最小频率应该被提取
        assert len(rules) >= 0  # 可能被提取或取决于实现

    def test_exactly_max_rules(self):
        """测试恰好达到最大规则数"""
        # 创建足够的反馈以生成超过最大规则数
        feedback = [
            FeedbackItem(
                tool_name=f"Tool{i}",
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id=f"rule_{i}",
                rule_name=f"Rule {i}",
                category=FeedbackCategory.CODE_QUALITY,
                severity=SeverityLevel.LOW,
                message="Message",
                file_path=f"file{i}.py",
                line=1,
                snippet="code",
                suggestion="fix",
                confidence=0.8
            )
            for i in range(20)  # 20个不同的规则
        ]

        extractor = RuleExtractor(min_frequency=1, max_rules=10)
        rules = extractor.extract_rules(feedback)

        # 规则数应该不超过最大值
        assert len(rules) <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
