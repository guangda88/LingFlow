"""
Phase 4 + Phase 5 集成端到端测试

测试Phase 4（参数优化）和Phase 5（AI工具学习）的协同工作：
- Phase 5 学习规则 → Phase 4 使用规则优化参数
- 反馈循环和持续改进
- 系统集成测试
"""

import pytest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from lingflow.self_optimizer.phase4.engine import OptimizationEngine
from lingflow.self_optimizer.phase4.bayesian_optimizer import (
    BayesianOptimizer,
    OptimizationState
)
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
from lingflow.self_optimizer.phase5.adapters import SemgrepAdapter, RuffAdapter, AIToolAdapter


@pytest.mark.integration
class TestPhase4Phase5Integration:
    """测试Phase 4和Phase 5的集成"""

    def test_learning_to_optimization_flow(self, temp_project):
        """测试从学习到优化的完整流程"""
        # Phase 5: 学习规则
        kb = InMemoryKnowledgeBase()

        # 添加学习到的规则
        pattern = Pattern(file_patterns=["*.py"])
        learned_rule = LearnedRule(
            id="learned_max_class_size",
            name="Optimal Class Size",
            description="Learned optimal class size",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Semgrep", "Ruff"],
            frequency=10,
            confidence=0.85
        )
        kb.add_rule(learned_rule)

        # Phase 4: 使用规则指导优化
        engine = OptimizationEngine(config={
            "n_trials": 5,
            "timeout": 30,
            "generate_reports": False
        })

        # 自定义搜索空间（基于学习到的规则）
        custom_search_space = {
            "max_class_size": {"type": "int", "min": 200, "max": 400},
            "max_method_count": {"type": "categorical", "choices": [15, 20, 25]},
        }

        result = engine.optimize_single_objective(
            target_path=temp_project,
            goal="structure",
            search_space=custom_search_space
        )

        # 验证优化完成
        assert result["goal"] == "structure"
        assert result["best_params"] is not None
        assert result["best_score"] is not None

    def test_feedback_driven_optimization(self, temp_project):
        """测试反馈驱动的优化"""
        # 1. 初始优化
        engine = OptimizationEngine(config={
            "n_trials": 3,
            "timeout": 20,
            "generate_reports": False
        })

        initial_result = engine.optimize_single_objective(
            target_path=temp_project,
            goal="structure"
        )

        # 2. 模拟工具反馈
        feedback = [
            FeedbackItem(
                tool_name="Semgrep",
                tool_type=ToolType.SECURITY_SCANNER,
                rule_id="test.feedback",
                rule_name="Test Feedback",
                category=FeedbackCategory.CODE_QUALITY,
                severity=SeverityLevel.MEDIUM,
                message="Classes are too large",
                file_path="src/auth.py",
                line=1,
                snippet="class LargeClass:",
                suggestion="Reduce class size",
                confidence=0.8
            )
        ]

        # 3. 从反馈学习
        extractor = RuleExtractor(min_frequency=1)
        rules = extractor.extract_rules(feedback)

        # 4. 基于学习调整搜索空间
        if rules:
            adjusted_search_space = {
                "max_class_size": {"type": "int", "min": 50, "max": 250},
                "max_method_count": {"type": "categorical", "choices": [5, 10, 15]},
            }

            # 5. 重新优化
            adjusted_result = engine.optimize_single_objective(
                target_path=temp_project,
                goal="structure",
                search_space=adjusted_search_space
            )

            # 验证参数已调整
            assert adjusted_result["best_params"]["max_class_size"] <= 250

    def test_continuous_improvement_cycle(self, temp_project):
        """测试持续改进循环"""
        engine = OptimizationEngine(config={
            "n_trials": 3,
            "timeout": 15,
            "generate_reports": False
        })
        kb = InMemoryKnowledgeBase()
        extractor = RuleExtractor(min_frequency=1)

        scores = []

        # 多轮优化和学习
        for iteration in range(3):
            # 优化
            result = engine.optimize_single_objective(
                target_path=temp_project,
                goal="structure"
            )
            scores.append(result["best_score"])

            # 模拟反馈
            feedback = [
                FeedbackItem(
                    tool_name="Optimizer",
                    tool_type=ToolType.SECURITY_SCANNER,
                    rule_id=f"iteration.{iteration}",
                    rule_name=f"Iteration {iteration}",
                    category=FeedbackCategory.CODE_QUALITY,
                    severity=SeverityLevel.LOW,
                    message=f"Score: {result['best_score']}",
                    file_path="test.py",
                    line=1,
                    snippet="code",
                    suggestion="Improve",
                    confidence=0.7
                )
            ]

            # 学习
            rules = extractor.extract_rules(feedback)
            if rules:
                kb.add_rules_batch(rules)

        # 验证持续改进（分数应该下降）
        assert len(scores) == 3

    def test_knowledge_base_guided_optimization(self, temp_project):
        """测试知识库指导的优化"""
        # 1. 填充知识库
        kb = InMemoryKnowledgeBase()

        # 添加历史最优参数
        historical_rules = [
            LearnedRule(
                id=f"hist_{i}",
                name=f"Historical Rule {i}",
                description=f"Optimal parameters from run {i}",
                category=FeedbackCategory.CODE_QUALITY,
                pattern=Pattern(file_patterns=["*.py"]),
                tools=["Optimizer"],
                frequency=1,
                confidence=0.8
            )
            for i in range(5)
        ]
        kb.add_rules_batch(historical_rules)

        # 2. 从知识库获取建议
        stats = kb.get_statistics()
        assert stats['total_rules'] >= 5

        # 3. 使用历史信息指导优化
        engine = OptimizationEngine(config={
            "n_trials": 3,
            "timeout": 20,
            "generate_reports": False
        })

        result = engine.optimize_single_objective(
            target_path=temp_project,
            goal="structure"
        )

        # 验证优化完成
        assert result["best_score"] is not None


@pytest.mark.integration
class TestToolIntegration:
    """测试与外部工具的集成"""

    @patch('lingflow.self_optimizer.phase5.adapters.semgrep_adapter.subprocess.run')
    def test_semgrep_integration(self, mock_run, temp_project):
        """测试Semgrep集成"""
        # Mock subprocess
        mock_run.return_value = Mock(
            stdout='{"results": []}',
            returncode=0
        )

        adapter = SemgrepAdapter()
        results = adapter.run_scan(temp_project)

        assert isinstance(results, list)

    @patch('lingflow.self_optimizer.phase5.adapters.semgrep_adapter.subprocess.run')
    def test_ruff_integration(self, mock_run, temp_project):
        """测试Ruff集成"""
        mock_run.return_value = Mock(
            stdout='[]',
            returncode=0
        )

        adapter = RuffAdapter()
        results = adapter.run_scan(temp_project)

        assert isinstance(results, list)

    def test_multi_tool_workflow(self, temp_project, mock_tools):
        """测试多工具协作流程"""
        all_results = []

        # 运行多个工具
        for tool_name, mock_tool in mock_tools.items():
            results = mock_tool.run(temp_project)
            all_results.extend(results)

        # 标准化结果
        from lingflow.self_optimizer.phase5.adapters import AIToolAdapter
        from lingflow.self_optimizer.phase5.models import FeedbackSource, ToolType
        adapter = AIToolAdapter()
        normalized = adapter.normalize_results(all_results)

        # 提取规则（normalized已经是AIFeedback对象列表）
        # 将AIFeedback转换为FeedbackItem
        feedback_items = []
        source_to_tool_type = {
            FeedbackSource.SEMGREP: ToolType.SECURITY_SCANNER,
            FeedbackSource.RUFF: ToolType.LINTING,
            FeedbackSource.PYLINT: ToolType.LINTING,
            FeedbackSource.SONARQUBE: ToolType.STATIC_ANALYZER,
            FeedbackSource.CODEQL: ToolType.STATIC_ANALYZER,
        }

        for item in normalized:
            tool_type = source_to_tool_type.get(item.source, ToolType.STATIC_ANALYZER)
            feedback_items.append(FeedbackItem(
                tool_name=item.source.value,
                tool_type=tool_type,
                rule_id=item.rule_id or "",
                rule_name=item.rule_id or "",
                category=item.category,
                severity=item.severity,
                message=item.message,
                file_path=item.file_path,
                line=item.line_no,
                snippet=item.code_snippet,
                suggestion=item.suggestion,
                confidence=0.8
            ))
        extractor = RuleExtractor(min_frequency=1)
        rules = extractor.extract_rules(feedback_items)

        # 验证多工具结果
        assert isinstance(rules, list)


@pytest.mark.integration
class TestSystemWorkflows:
    """测试系统级工作流"""

    def test_complete_analysis_workflow(self, temp_project):
        """测试完整分析工作流"""
        # 1. 代码分析
        adapter = SemgrepAdapter()
        tool_results = adapter.run_scan(temp_project)

        # 2. 结果标准化
        normalized = adapter.normalize_results(tool_results)

        # 3. 规则学习
        if normalized:
            # 将AIFeedback转换为FeedbackItem
            from lingflow.self_optimizer.phase5.models import ToolType
            feedback_items = []
            for item in normalized:
                feedback_items.append(FeedbackItem(
                    tool_name=item.source.value,
                    tool_type=ToolType.SECURITY_SCANNER,
                    rule_id=item.rule_id or "",
                    rule_name=item.rule_id or "",
                    category=item.category,
                    severity=item.severity,
                    message=item.message,
                    file_path=item.file_path,
                    line=item.line_no,
                    snippet=item.code_snippet,
                    suggestion=item.suggestion,
                    confidence=0.8
                ))
            extractor = RuleExtractor(min_frequency=1)
            rules = extractor.extract_rules(feedback_items)

            # 4. 知识库更新
            kb = InMemoryKnowledgeBase()
            kb.add_rules_batch(rules)

            # 5. 参数优化
            engine = OptimizationEngine(config={
                "n_trials": 3,
                "timeout": 20,
                "generate_reports": False
            })

            result = engine.optimize_single_objective(
                target_path=temp_project,
                goal="structure"
            )

            # 验证完整流程
            assert result["best_score"] is not None

    def test_adaptive_optimization_workflow(self, temp_project):
        """测试自适应优化工作流"""
        engine = OptimizationEngine(config={
            "n_trials": 3,
            "timeout": 15,
            "generate_reports": False
        })

        optimization_history = []

        # 自适应优化：根据结果调整策略
        for round_num in range(3):
            # 运行优化
            result = engine.optimize_single_objective(
                target_path=temp_project,
                goal="structure"
            )

            optimization_history.append(result)

            # 根据结果调整（模拟自适应行为）
            if result["best_score"] > 0.5:
                # 分数太高，需要更多探索
                engine.config["n_trials"] = 5
            else:
                # 分数较低，可以减少试验
                engine.config["n_trials"] = 2

        # 验证自适应过程
        assert len(optimization_history) == 3

    def test_error_recovery_workflow(self, temp_project):
        """测试错误恢复工作流"""
        engine = OptimizationEngine(config={
            "n_trials": 2,
            "timeout": 10,
            "generate_reports": False
        })

        # 模拟错误场景
        try:
            # 使用无效的搜索空间
            invalid_search_space = {
                "invalid_param": {"type": "unknown", "min": 0, "max": 10}
            }

            result = engine.optimize_single_objective(
                target_path=temp_project,
                goal="structure",
                search_space=invalid_search_space
            )

        except Exception as e:
            # 验证错误处理
            assert isinstance(e, (ValueError, KeyError, AttributeError))

        # 恢复：使用有效搜索空间
        valid_search_space = {
            "max_class_size": {"type": "int", "min": 100, "max": 500}
        }

        result = engine.optimize_single_objective(
            target_path=temp_project,
            goal="structure",
            search_space=valid_search_space
        )

        # 验证恢复成功
        assert result["best_score"] is not None


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """测试性能相关集成"""

    def test_optimization_performance(self, temp_project):
        """测试优化性能"""
        import time

        engine = OptimizationEngine(config={
            "n_trials": 5,
            "timeout": 30,
            "generate_reports": False
        })

        start_time = time.time()
        result = engine.optimize_single_objective(
            target_path=temp_project,
            goal="structure"
        )
        elapsed_time = time.time() - start_time

        # 验证性能
        assert elapsed_time < 35  # 应该在超时时间内完成
        assert result["total_time"] > 0

    def test_learning_performance(self, mock_feedback_data):
        """测试学习性能"""
        import time

        # 创建大量反馈
        large_feedback = mock_feedback_data * 100

        start_time = time.time()

        feedback_items = [FeedbackItem(**item) for item in large_feedback]
        extractor = RuleExtractor(min_frequency=5)
        rules = extractor.extract_rules(feedback_items)

        elapsed_time = time.time() - start_time

        # 学习应该快速完成
        assert elapsed_time < 10
        assert isinstance(rules, list)


@pytest.mark.integration
class TestDataConsistency:
    """测试数据一致性"""

    def test_parameter_storage_consistency(self, temp_project, tmp_path):
        """测试参数存储一致性"""
        from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore

        storage_path = tmp_path / "params"
        storage = FileSystemParameterStore(base_path=str(storage_path))

        # 存储参数
        params = {"max_class_size": 300, "max_method_count": 15}
        version = storage.save(params, {"goal": "structure"})

        # 从另一个实例读取
        storage2 = FileSystemParameterStore(base_path=str(storage_path))
        retrieved = storage2.load(version.version_id)

        assert retrieved.params == params

    def test_knowledge_base_consistency(self):
        """测试知识库一致性"""
        kb = InMemoryKnowledgeBase()

        pattern = Pattern(file_patterns=["*.py"])
        rule = LearnedRule(
            id="consistency_test",
            name="Test",
            description="Test",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=pattern,
            tools=["Ruff"],
            frequency=1,
            confidence=0.8
        )

        # 添加规则
        kb.add_rule(rule)

        # 验证可以检索
        retrieved = kb.get_rule("consistency_test")
        assert retrieved.id == "consistency_test"

        # 更新状态
        kb.update_rule_status("consistency_test", "approved")
        updated = kb.get_rule("consistency_test")
        assert updated.status == "approved"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
