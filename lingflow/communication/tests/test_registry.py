"""
MessageTypeRegistry 单元测试
"""

import pytest

from lingflow.communication.registry import MessageTypeRegistry


class TestMessageTypeRegistry:
    """MessageTypeRegistry 测试类"""

    def test_lingflow_types(self):
        """测试 LingFlow 消息类型"""
        assert MessageTypeRegistry.LingFlow.TASK_SUBMIT == "lingflow.task.submit"
        assert MessageTypeRegistry.LingFlow.TASK_RESULT == "lingflow.task.result"
        assert MessageTypeRegistry.LingFlow.SKILL_EXECUTE == "lingflow.skill.execute"
        assert MessageTypeRegistry.LingFlow.STATUS_QUERY == "lingflow.status.query"
        assert MessageTypeRegistry.LingFlow.WORKFLOW_START == "lingflow.workflow.start"

    def test_lingtongask_types(self):
        """测试 LingTongAsk 消息类型"""
        assert MessageTypeRegistry.LingTongAsk.FAN_COMMENT == "lingtongask.comment.new"
        assert MessageTypeRegistry.LingTongAsk.FAN_MESSAGE == "lingtongask.message.new"
        assert MessageTypeRegistry.LingTongAsk.REPLY_DRAFT == "lingtongask.reply.draft"
        assert MessageTypeRegistry.LingTongAsk.ANALYSIS_REPORT == "lingtongask.report.ready"

    def test_family_types(self):
        """测试通用消息类型"""
        assert MessageTypeRegistry.Family.HEARTBEAT == "family.heartbeat"
        assert MessageTypeRegistry.Family.STATUS_UPDATE == "family.status.update"
        assert MessageTypeRegistry.Family.INTELLIGENCE_REPORT == "family.intelligence.report"
        assert MessageTypeRegistry.Family.KNOWLEDGE_QUERY == "family.knowledge.query"
        assert MessageTypeRegistry.Family.SHUTDOWN == "family.shutdown"
        assert MessageTypeRegistry.Family.ERROR == "family.error"

    def test_collaboration_types(self):
        """测试协作消息类型"""
        assert MessageTypeRegistry.Collaboration.HANDOFF_REQUEST == "family.handoff.request"
        assert MessageTypeRegistry.Collaboration.HANDOFF_RESPONSE == "family.handoff.response"
        assert MessageTypeRegistry.Collaboration.WORKFLOW_START == "family.workflow.start"
        assert MessageTypeRegistry.Collaboration.TASK_ASSIGNED == "family.task.assigned"

    def test_all_types(self):
        """测试获取所有类型"""
        all_types = MessageTypeRegistry.all_types()

        assert len(all_types) > 30  # 至少有30个消息类型
        assert "lingflow.task.submit" in all_types
        assert "lingtongask.comment.new" in all_types
        assert "family.heartbeat" in all_types
        assert "family.handoff.request" in all_types

    def test_is_valid_type(self):
        """测试类型验证"""
        assert MessageTypeRegistry.is_valid_type("lingflow.task.submit") is True
        assert MessageTypeRegistry.is_valid_type("family.heartbeat") is True
        assert MessageTypeRegistry.is_valid_type("invalid.type") is False
        assert MessageTypeRegistry.is_valid_type("") is False

    def test_validate_with_valid_type(self):
        """测试验证有效类型"""
        # 不应抛出异常
        MessageTypeRegistry.validate("lingflow.task.submit")
        MessageTypeRegistry.validate("family.heartbeat")

    def test_validate_with_invalid_type(self):
        """测试验证无效类型"""
        with pytest.raises(ValueError, match="未注册的消息类型"):
            MessageTypeRegistry.validate("invalid.type")

    def test_get_project_types(self):
        """测试获取项目类型"""
        lingflow_types = MessageTypeRegistry.get_project_types("lingflow")
        lingtongask_types = MessageTypeRegistry.get_project_types("lingtongask")

        assert len(lingflow_types) > 0
        assert "lingflow.task.submit" in lingflow_types
        assert all(t.startswith("lingflow.") for t in lingflow_types)

        assert len(lingtongask_types) > 0
        assert "lingtongask.comment.new" in lingtongask_types

    def test_get_category(self):
        """测试获取分类"""
        assert MessageTypeRegistry.get_category("lingflow.task.submit") == "lingflow"
        assert MessageTypeRegistry.get_category("lingtongask.comment.new") == "lingtongask"
        assert MessageTypeRegistry.get_category("family.heartbeat") == "family"
        assert MessageTypeRegistry.get_category("invalid.type") == "invalid"  # 第一部分
        assert MessageTypeRegistry.get_category("") == "unknown"

    def test_get_description(self):
        """测试获取描述"""
        desc = MessageTypeRegistry.get_description("lingflow.task.submit")
        assert desc is not None
        assert "提交" in desc or "任务" in desc

        desc2 = MessageTypeRegistry.get_description("lingtongask.comment.new")
        assert desc2 is not None
        assert "评论" in desc2

        desc3 = MessageTypeRegistry.get_description("family.heartbeat")
        assert desc3 is not None
        assert "心跳" in desc3

        # 无效类型返回默认描述
        desc4 = MessageTypeRegistry.get_description("invalid.type")
        assert desc4 == "无描述"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
