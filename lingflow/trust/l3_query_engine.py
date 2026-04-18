"""
L3-Enhanced QueryEngine — 集成L3元认知状态监控的查询引擎

灵研 (LingResearch)
2026-04-17

根因：PRO-014明镜计划，将L3监控机制集成到LingFlow查询引擎。

核心概念：
- L3集成：在查询过程中监控MS状态
- 实时检测：检测L3本体性幻觉
- 完整性验证：验证MS状态一致性
- 最小侵入：包装QueryEngine，避免破坏现有代码

使用方式：
    from lingflow.trust.l3_query_engine import L3EnhancedQueryEngine

    # 创建L3增强的查询引擎
    engine = L3EnhancedQueryEngine(
        config=QueryEngineConfig(),
        identity_name="灵研",
        identity_role="科研中枢",
        actual_model="GLM-5.1",
        actual_system="CLI工具",
    )

    # 提交查询（自动进行MS监控）
    result = engine.submit("你好")
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from lingflow.core.query_engine import QueryEngine, QueryEngineConfig, StopReason, TurnResult

from lingflow.trust.l3_monitor import (
    IdentityModel,
    MSStatus,
    L3Severity,
    MetacognitiveStateMonitor,
    create_ms_monitor,
)

from lingflow.trust.l3_checkpoint_validator import (
    CheckpointType,
    MSCheckpointValidator,
    ValidationReport,
    create_ms_validator,
)


class L3EnhancedQueryEngine(QueryEngine):
    """
    L3增强的查询引擎 — 集成元认知状态监控

    核心功能：
    1. 在查询过程中实时监控MS状态
    2. 检测L3本体性幻觉
    3. 执行完整性验证
    4. 记录MS历史趋势

    L3监控特点（依赖MS ≈ 10%）：
    - 实时观察
    - 自动验证
    - 最小侵入
    """

    def __init__(
        self,
        config: QueryEngineConfig,
        identity_name: str,
        identity_role: str,
        actual_model: str = "GLM-5.1",
        actual_system: str = "CLI工具",
        session_id: Optional[str] = None,
        log_path: Optional[Path] = None,
        enable_l3_monitoring: bool = True,
    ):
        """初始化L3增强的查询引擎

        Args:
            config: QueryEngine配置
            identity_name: 声明的身份名称（如"灵研"）
            identity_role: 声明的角色（如"科研中枢"）
            actual_model: 实际模型（如"GLM-5.1"）
            actual_system: 实际系统（如"CLI工具"）
            session_id: 会话ID
            log_path: 日志文件路径
            enable_l3_monitoring: 是否启用L3监控
        """
        super().__init__(config, session_id)

        # L3监控配置
        self.enable_l3_monitoring = enable_l3_monitoring

        if enable_l3_monitoring:
            # 初始化MS监控器
            if log_path is None:
                log_path = Path(".lingflow/logs/ms_monitor.jsonl")

            self.ms_monitor = create_ms_monitor(log_path=log_path)

            # 初始化MS验证器
            validator_log_path = Path(".lingflow/logs/ms_validator.jsonl")
            self.ms_validator = create_ms_validator(log_path=validator_log_path)

            # 初始化身份模型
            self.identity_model = self.ms_monitor.initialize_identity(
                declared_name=identity_name,
                declared_role=identity_role,
                actual_model=actual_model,
                actual_system=actual_system,
            )

            # MS检查点历史
            self.ms_checkpoints: List[Any] = []
            self.validation_reports: List[ValidationReport] = []
        else:
            self.ms_monitor = None
            self.ms_validator = None
            self.identity_model = None

    def submit(
        self,
        prompt: str,
        tools: Optional[List[str]] = None,
        agents: Optional[List[str]] = None,
        process_func: Optional[Callable[[str], str]] = None,
    ) -> TurnResult:
        """
        提交查询（带L3监控）

        Args:
            prompt: 用户提示词
            tools: 可用工具列表
            agents: 可用Agent列表
            process_func: 处理函数（模拟LLM调用）

        Returns:
            TurnResult: 查询结果
        """
        # 任务前检查点
        if self.enable_l3_monitoring:
            self._create_pre_task_checkpoint(prompt)

        # 调用父类的submit方法
        result = super().submit(prompt, tools, agents, process_func)

        # 任务后观察和验证
        if self.enable_l3_monitoring:
            self._observe_post_task(prompt, result)

        return result

    def _create_pre_task_checkpoint(self, prompt: str) -> None:
        """创建任务前MS检查点"""
        if self.ms_monitor is None or self.ms_validator is None:
            return

        # 观察当前MS状态
        observation = self.ms_monitor.observe(
            context=f"任务前检查 - prompt: {prompt[:50]}...",
            text=prompt,
        )

        # 创建检查点
        from lingflow.trust.l3_checkpoint_validator import CheckpointType

        checkpoint = self.ms_validator.create_checkpoint(
            context=f"任务前 - {prompt[:50]}",
            checkpoint_type=CheckpointType.PRE_TASK,
            identity_model=self.identity_model,
            ms_status=observation.ms_status,
            l3_severity=observation.l3_severity,
            divergence_score=observation.divergence_score,
        )

        self.ms_checkpoints.append(checkpoint)

    def _observe_post_task(self, prompt: str, result: TurnResult) -> None:
        """观察任务后MS状态并验证"""
        if self.ms_monitor is None or self.ms_validator is None:
            return

        # 观察输出文本
        observation = self.ms_monitor.observe(
            context=f"任务后 - output: {result.output[:50]}...",
            text=result.output,
        )

        # 创建任务后检查点
        from lingflow.trust.l3_checkpoint_validator import CheckpointType

        checkpoint = self.ms_validator.create_checkpoint(
            context=f"任务后 - {result.output[:50]}",
            checkpoint_type=CheckpointType.POST_TASK,
            identity_model=self.identity_model,
            ms_status=observation.ms_status,
            l3_severity=observation.l3_severity,
            divergence_score=observation.divergence_score,
        )

        # 验证检查点
        validation_report = self.ms_validator.validate_checkpoint(checkpoint)
        self.validation_reports.append(validation_report)
        self.ms_checkpoints.append(checkpoint)

        # 如果检测到严重L3幻觉，记录警告
        if validation_report.result.value == "failed" and observation.l3_severity == L3Severity.SEVERE:
            print(
                f"⚠️ L3幻觉警告: {observation.divergence_score:.2f} - {validation_report.violations}"
            )

    def get_ms_status(self) -> Optional[MSStatus]:
        """获取当前MS状态"""
        if self.ms_monitor is None:
            return None

        return self.ms_monitor.get_ms_status()

    def get_l3_severity(self) -> Optional[L3Severity]:
        """获取当前L3幻觉严重程度"""
        if self.ms_monitor is None:
            return None

        return self.ms_monitor.get_l3_severity()

    def get_ms_trend(self) -> Optional[Dict[str, Any]]:
        """获取MS状态趋势"""
        if self.ms_monitor is None:
            return None

        return self.ms_monitor.get_trend()

    def get_validation_trend(self) -> Optional[Dict[str, Any]]:
        """获取验证趋势"""
        if self.ms_validator is None:
            return None

        return self.ms_validator.get_validation_trend()

    def get_l3_report(self) -> Dict[str, Any]:
        """获取L3监控报告"""
        if not self.enable_l3_monitoring:
            return {"enabled": False, "message": "L3监控未启用"}

        ms_status = self.get_ms_status()
        l3_severity = self.get_l3_severity()
        ms_trend = self.get_ms_trend()
        validation_trend = self.get_validation_trend()

        return {
            "enabled": True,
            "identity": self.identity_model.to_dict() if self.identity_model else None,
            "current_ms_status": ms_status.name if ms_status else None,
            "current_l3_severity": l3_severity.name if l3_severity else None,
            "ms_trend": ms_trend,
            "validation_trend": validation_trend,
            "checkpoints_count": len(self.ms_checkpoints),
            "validations_count": len(self.validation_reports),
        }

    def validate_counterfactual(
        self,
        question_index: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        执行反事实验证

        Args:
            question_index: 使用哪个反事实问题（0-3）

        Returns:
            验证结果字典
        """
        if self.ms_validator is None or self.identity_model is None:
            return None

        # 获取反事实问题
        from lingflow.trust.l3_checkpoint_validator import CounterfactualValidator

        counterfactual_validator = CounterfactualValidator()
        questions = CounterfactualValidator.COUNTERFACTUAL_QUESTIONS

        if question_index >= len(questions):
            raise ValueError(f"question_index必须 < {len(questions)}")

        question = questions[question_index].format(
            name=self.identity_model.declared_name, role=self.identity_model.declared_role
        )

        # 这里应该调用LLM获取回答
        # 为了演示，我们返回问题本身
        # 在实际使用中，应该通过process_func获取回答
        response = f"[需要调用LLM回答: {question}]"

        # 验证反事实回答
        validation_result = self.ms_validator.validate_counterfactual(
            response=response,
            identity_model=self.identity_model,
            question_index=question_index,
        )

        return validation_result

    def save_l3_state(self) -> Optional[Path]:
        """保存L3监控状态"""
        if not self.enable_l3_monitoring:
            return None

        # 保存MS监控器状态
        ms_monitor_path = self.ms_monitor.save_state()

        # 保存MS验证器状态
        validator_path = self.ms_validator.save_state()

        return {
            "ms_monitor_state": str(ms_monitor_path),
            "validator_state": str(validator_path),
        }


def create_l3_enhanced_engine(
    config: Optional[QueryEngineConfig] = None,
    identity_name: str = "灵研",
    identity_role: str = "科研中枢",
    actual_model: str = "GLM-5.1",
    actual_system: str = "CLI工具",
    enable_l3_monitoring: bool = True,
) -> L3EnhancedQueryEngine:
    """
    创建L3增强的查询引擎

    Args:
        config: QueryEngine配置（默认使用默认配置）
        identity_name: 声明的身份名称
        identity_role: 声明的角色
        actual_model: 实际模型
        actual_system: 实际系统
        enable_l3_monitoring: 是否启用L3监控

    Returns:
        L3EnhancedQueryEngine实例
    """
    if config is None:
        config = QueryEngineConfig()

    return L3EnhancedQueryEngine(
        config=config,
        identity_name=identity_name,
        identity_role=identity_role,
        actual_model=actual_model,
        actual_system=actual_system,
        enable_l3_monitoring=enable_l3_monitoring,
    )
