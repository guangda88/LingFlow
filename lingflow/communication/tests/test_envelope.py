"""
MessageEnvelope 单元测试
"""

from datetime import datetime, timedelta

import pytest

from lingflow.communication.envelope import MessageEnvelope, create_envelope
from lingflow.communication.registry import MessageTypeRegistry


class TestMessageEnvelope:
    """MessageEnvelope 测试类"""

    def test_create_basic_envelope(self):
        """测试基本消息信封创建"""
        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
            payload={"query": "测试查询"},
        )

        assert envelope.from_service == "lingyi"
        assert envelope.to_service == "lingzhi"
        assert envelope.msg_type == MessageTypeRegistry.Family.KNOWLEDGE_QUERY
        assert envelope.payload == {"query": "测试查询"}
        assert envelope.msg_id is not None
        assert len(envelope.msg_id) == 32  # uuid4 hex length

    def test_validation_empty_fields(self):
        """测试字段验证"""
        with pytest.raises(ValueError, match="from_service"):
            MessageEnvelope(
                from_service="",
                to_service="lingzhi",
                msg_type="test.type",
            )

        with pytest.raises(ValueError, match="to_service"):
            MessageEnvelope(
                from_service="lingyi",
                to_service="",
                msg_type="test.type",
            )

        with pytest.raises(ValueError, match="msg_type"):
            MessageEnvelope(
                from_service="lingyi",
                to_service="lingzhi",
                msg_type="",
            )

        with pytest.raises(ValueError, match="priority"):
            MessageEnvelope(
                from_service="lingyi",
                to_service="lingzhi",
                msg_type="test.type",
                priority=5,
            )

    def test_is_broadcast(self):
        """测试广播检测"""
        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="*",
            msg_type="test.type",
        )

        assert envelope.is_broadcast() is True

        envelope2 = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type="test.type",
        )

        assert envelope2.is_broadcast() is False

    def test_ttl_expiration(self):
        """测试TTL过期检测"""
        # 过期的消息
        old_timestamp = datetime.now() - timedelta(seconds=10)
        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type="test.type",
            ttl=5,
            timestamp=old_timestamp,
        )

        assert envelope.is_expired() is True

        # 未过期的消息
        envelope2 = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type="test.type",
            ttl=60,
        )

        assert envelope2.is_expired() is False

        # 无TTL的消息
        envelope3 = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type="test.type",
        )

        assert envelope3.is_expired() is False

    def test_age_seconds(self):
        """测试消息年龄计算"""
        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type="test.type",
        )

        age = envelope.age_seconds()
        assert age >= 0
        assert age < 1  # 应该很快

    def test_serialization(self):
        """测试序列化和反序列化"""
        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
            payload={"query": "测试查询", "limit": 10},
            priority=1,
            correlation_id="test-123",
        )

        # 转字典
        data = envelope.to_dict()
        assert data["from_service"] == "lingyi"
        assert data["to_service"] == "lingzhi"
        assert data["payload"]["query"] == "测试查询"

        # 转JSON
        json_str = envelope.to_json()
        assert isinstance(json_str, str)

        # 从字典恢复
        envelope2 = MessageEnvelope.from_dict(data)
        assert envelope2.from_service == envelope.from_service
        assert envelope2.to_service == envelope.to_service
        assert envelope2.payload == envelope.payload
        assert envelope2.priority == envelope.priority

        # 从JSON恢复
        envelope3 = MessageEnvelope.from_json(json_str)
        assert envelope3.from_service == envelope.from_service
        assert envelope3.msg_type == envelope.msg_type

    def test_create_reply(self):
        """测试创建回复消息"""
        original = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
            payload={"query": "测试"},
            correlation_id="original-123",
        )

        reply = original.create_reply(
            reply_payload={"answer": "回复内容"},
            reply_type=MessageTypeRegistry.Family.NOTIFICATION,
            from_service="lingzhi",
        )

        assert reply.from_service == "lingzhi"
        assert reply.to_service == "lingyi"
        assert reply.msg_type == MessageTypeRegistry.Family.NOTIFICATION
        assert reply.payload == {"answer": "回复内容"}
        assert reply.correlation_id == original.msg_id
        assert reply.msg_id != original.msg_id

    def test_factory_function(self):
        """测试工厂函数"""
        envelope = create_envelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type="test.type",
            payload={"data": "test"},
            priority=2,
            ttl=300,
        )

        assert envelope.from_service == "lingyi"
        assert envelope.to_service == "lingzhi"
        assert envelope.priority == 2
        assert envelope.ttl == 300

    def test_str_representation(self):
        """测试字符串表示"""
        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type="test.type",
        )

        str_repr = str(envelope)
        assert "MessageEnvelope" in str_repr
        assert "lingyi" in str_repr
        assert "lingzhi" in str_repr
        assert "test.type" in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
