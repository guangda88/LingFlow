"""
消息类型注册表 - MessageTypeRegistry v1.0

定义灵字辈大家庭所有消息类型常量
提供消息类型验证和查询功能
"""

from enum import Enum
from typing import Dict, List, Set


class MessageTypeRegistry:
    """
    灵字辈消息类型注册表

    所有消息类型使用点分命名法: <project>.<category>.<action>

    设计原则:
    - 统一命名规范，避免冲突
    - 按项目分组，便于管理
    - 支持消息类型验证
    """

    # === LingFlow 消息类型 ===
    class LingFlow:
        """LingFlow 工作流引擎消息类型"""

        TASK_SUBMIT = "lingflow.task.submit"
        TASK_RESULT = "lingflow.task.result"
        SKILL_EXECUTE = "lingflow.skill.execute"
        SKILL_RESULT = "lingflow.skill.result"
        STATUS_QUERY = "lingflow.status.query"
        STATUS_UPDATE = "lingflow.status.update"
        WORKFLOW_START = "lingflow.workflow.start"
        WORKFLOW_COMPLETE = "lingflow.workflow.complete"
        WORKFLOW_ERROR = "lingflow.workflow.error"

    # === LingTongAsk 消息类型 ===
    class LingTongAsk:
        """LingTongAsk 气功播客平台消息类型"""

        FAN_COMMENT = "lingtongask.comment.new"
        FAN_MESSAGE = "lingtongask.message.new"
        REPLY_DRAFT = "lingtongask.reply.draft"
        ANALYSIS_REPORT = "lingtongask.report.ready"
        CONTENT_GENERATE = "lingtongask.content.generate"
        CONTENT_PUBLISH = "lingtongask.content.publish"
        FEEDBACK_COLLECT = "lingtongask.feedback.collect"

    # === LingYi 消息类型 ===
    class LingYi:
        """LingYi 私人助理消息类型"""

        INTELLIGENCE_SYNC = "lingyi.intelligence.sync"
        SCHEDULE_UPDATE = "lingyi.schedule.update"
        REMINDER_SET = "lingyi.reminder.set"
        REMINDER_TRIGGER = "lingyi.reminder.trigger"
        DAILY_SUMMARY = "lingyi.summary.daily"
        WEEKLY_REPORT = "lingyi.report.weekly"

    # === LingClaude 消息类型 ===
    class LingClaude:
        """LingClaude AI编程助手消息类型"""

        CODE_REQUEST = "lingclaude.code.request"
        CODE_RESULT = "lingclaude.code.result"
        REFACTOR_ANALYZE = "lingclaude.refactor.analyze"
        REFACTOR_APPLY = "lingclaude.refactor.apply"
        SELF_LEARNING_RUN = "lingclaude.self_learning.run"
        CODE_REVIEW = "lingclaude.code.review"

    # === LingMinOpt 消息类型 ===
    class LingMinOpt:
        """LingMinOpt 自优化框架消息类型"""

        OPTIMIZE_START = "lingminopt.optimize.start"
        OPTIMIZE_RESULT = "lingminopt.optimize.result"
        METRIC_COLLECT = "lingminopt.metric.collect"
        PARAMETER_UPDATE = "lingminopt.parameter.update"
        VIOLATION_FOUND = "lingminopt.violation.found"
        VIOLATION_FIXED = "lingminopt.violation.fixed"

    # === Knowledge-System 消息类型 ===
    class KnowledgeSystem:
        """Knowledge-System 知识库消息类型"""

        KNOWLEDGE_QUERY = "knowledge.query"
        KNOWLEDGE_ADD = "knowledge.add"
        KNOWLEDGE_UPDATE = "knowledge.update"
        KNOWLEDGE_DELETE = "knowledge.delete"
        KNOWLEDGE_SYNC = "knowledge.sync"
        VECTOR_SEARCH = "knowledge.vector.search"

    # === 灵字辈通用消息类型 ===
    class Family:
        """灵字辈通用消息类型"""

        HEARTBEAT = "family.heartbeat"
        STATUS_UPDATE = "family.status.update"
        INTELLIGENCE_REPORT = "family.intelligence.report"
        KNOWLEDGE_QUERY = "family.knowledge.query"
        SHUTDOWN = "family.shutdown"
        ERROR = "family.error"
        NOTIFICATION = "family.notification"

    # === 协作消息类型 ===
    class Collaboration:
        """成员间协作消息类型"""

        HANDOFF_REQUEST = "family.handoff.request"
        HANDOFF_RESPONSE = "family.handoff.response"
        WORKFLOW_START = "family.workflow.start"
        WORKFLOW_COMPLETE = "family.workflow.complete"
        WORKFLOW_FAIL = "family.workflow.fail"
        TASK_ASSIGNED = "family.task.assigned"
        TASK_COMPLETED = "family.task.completed"

    @classmethod
    def all_types(cls) -> Set[str]:
        """获取所有注册的消息类型"""
        types: Set[str] = set()

        for group_class in [
            cls.LingFlow,
            cls.LingTongAsk,
            cls.LingYi,
            cls.LingClaude,
            cls.LingMinOpt,
            cls.KnowledgeSystem,
            cls.Family,
            cls.Collaboration,
        ]:
            for attr_name in dir(group_class):
                if attr_name.isupper():
                    types.add(getattr(group_class, attr_name))

        return types

    @classmethod
    def is_valid_type(cls, msg_type: str) -> bool:
        """验证消息类型是否已注册"""
        return msg_type in cls.all_types()

    @classmethod
    def get_project_types(cls, project: str) -> List[str]:
        """获取指定项目的所有消息类型

        Args:
            project: 项目名称 (如 "lingflow", "lingtongask")

        Returns:
            该项目的消息类型列表
        """
        all_types = cls.all_types()
        prefix = f"{project}."
        return [t for t in all_types if t.startswith(prefix)]

    @classmethod
    def get_category(cls, msg_type: str) -> str:
        """获取消息类型的分类

        Args:
            msg_type: 消息类型

        Returns:
            分类名称 (如 "lingflow", "family")
        """
        if not msg_type:
            return "unknown"

        parts = msg_type.split(".")
        if len(parts) >= 2:
            return parts[0]
        return "unknown"

    @classmethod
    def validate(cls, msg_type: str) -> None:
        """验证消息类型，无效则抛出异常

        Args:
            msg_type: 消息类型

        Raises:
            ValueError: 如果消息类型未注册
        """
        if not cls.is_valid_type(msg_type):
            raise ValueError(f"未注册的消息类型: {msg_type}")

    @classmethod
    def get_description(cls, msg_type: str) -> str:
        """获取消息类型的描述

        Args:
            msg_type: 消息类型

        Returns:
            消息类型描述
        """
        descriptions: Dict[str, str] = {
            # LingFlow
            "lingflow.task.submit": "提交新任务到工作流",
            "lingflow.task.result": "任务执行结果",
            "lingflow.skill.execute": "执行技能命令",
            "lingflow.skill.result": "技能执行结果",
            "lingflow.status.query": "查询系统状态",
            "lingflow.status.update": "系统状态更新",
            "lingflow.workflow.start": "启动工作流",
            "lingflow.workflow.complete": "工作流完成",
            "lingflow.workflow.error": "工作流错误",
            # LingTongAsk
            "lingtongask.comment.new": "新粉丝评论",
            "lingtongask.message.new": "新粉丝消息",
            "lingtongask.reply.draft": "回复草稿",
            "lingtongask.report.ready": "分析报告就绪",
            "lingtongask.content.generate": "生成内容",
            "lingtongask.content.publish": "发布内容",
            "lingtongask.feedback.collect": "收集反馈",
            # Family
            "family.heartbeat": "成员心跳",
            "family.status.update": "成员状态更新",
            "family.intelligence.report": "情报报告",
            "family.knowledge.query": "知识查询",
            "family.shutdown": "关闭通知",
            "family.error": "错误通知",
            "family.notification": "通用通知",
            # Collaboration
            "family.handoff.request": "交接请求",
            "family.handoff.response": "交接响应",
            "family.workflow.start": "协作工作流启动",
            "family.workflow.complete": "协作工作流完成",
            "family.workflow.fail": "协作工作流失败",
            "family.task.assigned": "任务分配",
            "family.task.completed": "任务完成",
        }
        return descriptions.get(msg_type, "无描述")


# 预定义的消息类型枚举（用于类型提示）
class MessageType(str, Enum):
    """预定义消息类型枚举"""

    # === 通用消息 ===
    HEARTBEAT = MessageTypeRegistry.Family.HEARTBEAT
    STATUS_UPDATE = MessageTypeRegistry.Family.STATUS_UPDATE
    INTELLIGENCE_REPORT = MessageTypeRegistry.Family.INTELLIGENCE_REPORT
    KNOWLEDGE_QUERY = MessageTypeRegistry.Family.KNOWLEDGE_QUERY
    SHUTDOWN = MessageTypeRegistry.Family.SHUTDOWN
    ERROR = MessageTypeRegistry.Family.ERROR
    NOTIFICATION = MessageTypeRegistry.Family.NOTIFICATION

    # === 协作消息 ===
    HANDOFF_REQUEST = MessageTypeRegistry.Collaboration.HANDOFF_REQUEST
    HANDOFF_RESPONSE = MessageTypeRegistry.Collaboration.HANDOFF_RESPONSE
    WORKFLOW_START = MessageTypeRegistry.Collaboration.WORKFLOW_START
    WORKFLOW_COMPLETE = MessageTypeRegistry.Collaboration.WORKFLOW_COMPLETE

    # === LingFlow ===
    TASK_SUBMIT = MessageTypeRegistry.LingFlow.TASK_SUBMIT
    TASK_RESULT = MessageTypeRegistry.LingFlow.TASK_RESULT
    SKILL_EXECUTE = MessageTypeRegistry.LingFlow.SKILL_EXECUTE
    SKILL_RESULT = MessageTypeRegistry.LingFlow.SKILL_RESULT
