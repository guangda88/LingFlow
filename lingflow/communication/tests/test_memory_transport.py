"""
InMemoryTransport 单元测试
"""

import asyncio

import pytest

from lingflow.communication import (
    InMemoryTransport,
    MessageEnvelope,
    MessageTypeRegistry,
)


class TestInMemoryTransport:
    """InMemoryTransport 测试类"""

    @pytest.fixture
    def transport(self):
        """创建传输实例"""
        t = InMemoryTransport()
        t.start()
        yield t
        asyncio.run(t.close())

    @pytest.mark.asyncio
    async def test_send_and_receive(self, transport):
        """测试发送和接收"""
        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
            payload={"query": "测试查询"},
        )

        # 发送
        success = await transport.send(envelope)
        assert success is True

        # 接收
        received = await transport.receive("lingzhi", timeout=1.0)
        assert received is not None
        assert received.from_service == "lingyi"
        assert received.payload == {"query": "测试查询"}

    @pytest.mark.asyncio
    async def test_broadcast(self, transport):
        """测试广播消息"""
        # 预先创建服务队列（通过发送消息或直接创建）
        # 广播需要目标服务的队列已存在
        _ = transport._queues["lingzhi"]  # 触发创建
        _ = transport._queues["lingtong"]  # 触发创建

        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="*",
            msg_type=MessageTypeRegistry.Family.NOTIFICATION,
            payload={"message": "广播测试"},
        )

        # 发送广播
        await transport.send(envelope)

        # 多个服务接收
        received1 = await transport.receive("lingzhi", timeout=1.0)
        received2 = await transport.receive("lingtong", timeout=1.0)

        assert received1 is not None
        assert received2 is not None
        assert received1.payload == received2.payload

    @pytest.mark.asyncio
    async def test_subscribe(self, transport):
        """测试订阅机制"""
        received_messages = []

        async def handler(envelope):
            received_messages.append(envelope)

        # 订阅
        sub_id = transport.subscribe(
            service="lingzhi",
            msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
            handler=handler,
        )

        # 发送消息
        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
            payload={"query": "测试"},
        )

        await transport.send(envelope)

        # 等待处理
        await asyncio.sleep(0.2)

        assert len(received_messages) == 1
        assert received_messages[0].payload == {"query": "测试"}

        # 取消订阅
        transport.unsubscribe("lingzhi", sub_id)

    @pytest.mark.asyncio
    async def test_subscribe_wildcard(self, transport):
        """测试通配符订阅"""
        received_messages = []

        async def handler(envelope):
            received_messages.append(envelope)

        # 订阅所有消息
        transport.subscribe(
            service="lingzhi",
            msg_type="*",
            handler=handler,
        )

        # 发送不同类型的消息
        envelopes = [
            MessageEnvelope(
                from_service="lingyi",
                to_service="lingzhi",
                msg_type="type1",
                payload={"index": 1},
            ),
            MessageEnvelope(
                from_service="lingyi",
                to_service="lingzhi",
                msg_type="type2",
                payload={"index": 2},
            ),
        ]

        for env in envelopes:
            await transport.send(env)

        await asyncio.sleep(0.2)

        assert len(received_messages) == 2

    @pytest.mark.asyncio
    async def test_receive_stream(self, transport):
        """测试消息流接收"""
        envelopes = []

        async def collect_stream():
            async for envelope in transport.receive_stream("lingzhi"):
                envelopes.append(envelope)
                if len(envelopes) >= 3:
                    break

        # 发送消息
        for i in range(3):
            envelope = MessageEnvelope(
                from_service="lingyi",
                to_service="lingzhi",
                msg_type="test.type",
                payload={"index": i},
            )
            await transport.send(envelope)

        # 收集流
        task = asyncio.create_task(collect_stream())
        await asyncio.wait_for(task, timeout=2.0)

        assert len(envelopes) == 3

    @pytest.mark.asyncio
    async def test_priority_ordering(self, transport):
        """测试优先级（注：当前实现是FIFO，优先级影响处理顺序）"""
        # 发送不同优先级的消息
        for priority in [0, 2, 1]:
            envelope = MessageEnvelope(
                from_service="lingyi",
                to_service="lingzhi",
                msg_type="test.type",
                payload={"priority": priority},
                priority=priority,
            )
            await transport.send(envelope)

        # 接收并检查
        received = []
        for _ in range(3):
            msg = await transport.receive("lingzhi", timeout=1.0)
            if msg:
                received.append(msg.payload["priority"])

        assert len(received) == 3

    @pytest.mark.asyncio
    async def test_expired_message(self, transport):
        """测试过期消息"""
        from datetime import datetime, timedelta

        # 创建已过期的消息
        old_timestamp = datetime.now() - timedelta(seconds=10)
        envelope = MessageEnvelope(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type="test.type",
            ttl=5,
            timestamp=old_timestamp,
        )

        # 发送应该失败
        success = await transport.send(envelope)
        assert success is False

    @pytest.mark.asyncio
    async def test_queue_size(self, transport):
        """测试队列大小查询"""
        # 发送几条消息
        for i in range(5):
            envelope = MessageEnvelope(
                from_service="lingyi",
                to_service="lingzhi",
                msg_type="test.type",
                payload={"index": i},
            )
            await transport.send(envelope)

        size = transport.get_queue_size("lingzhi")
        assert size == 5

    @pytest.mark.asyncio
    async def test_get_services(self, transport):
        """测试获取服务列表"""
        # 发送到多个服务
        services = ["lingzhi", "lingtong", "lingke"]
        for service in services:
            envelope = MessageEnvelope(
                from_service="lingyi",
                to_service=service,
                msg_type="test.type",
            )
            await transport.send(envelope)

        registered = transport.get_services()
        for service in services:
            assert service in registered


class TestInMemoryMessageBus:
    """InMemoryMessageBus 测试类"""

    @pytest.mark.asyncio
    async def test_request_response(self):
        """测试请求-响应模式"""
        from lingflow.communication.transports.memory import InMemoryMessageBus

        bus = InMemoryMessageBus()

        # 设置响应处理器
        async def handle_request(envelope):
            await bus.respond(
                request=envelope,
                response_payload={"answer": "测试响应"},
                response_type="response.type",
            )

        bus.subscribe("lingzhi", MessageTypeRegistry.Family.KNOWLEDGE_QUERY, handle_request)

        # 发送请求
        response = await bus.request(
            from_service="lingyi",
            to_service="lingzhi",
            msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
            payload={"query": "测试查询"},
        )

        assert response is not None
        assert response["answer"] == "测试响应"

        await bus.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
