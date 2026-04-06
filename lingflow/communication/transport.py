"""
传输适配器抽象基类 - TransportAdapter v1.0

定义传输适配器的抽象接口，支持多种传输实现:
- InMemoryTransport: 内存队列传输
- RedisTransport: Redis Pub/Sub 传输 (未来)
- FileTransport: 文件传输
- HTTPTransport: HTTP传输 (未来)
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Callable, Dict, List, Optional
import asyncio

from .envelope import MessageEnvelope


class TransportAdapter(ABC):
    """
    传输适配器抽象接口

    定义所有传输实现必须遵循的接口规范
    """

    @abstractmethod
    async def send(self, envelope: MessageEnvelope) -> bool:
        """
        发送消息

        Args:
            envelope: 消息信封

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        pass

    @abstractmethod
    async def receive(self, service: str, timeout: Optional[float] = None) -> Optional[MessageEnvelope]:
        """
        接收消息 (阻塞)

        Args:
            service: 接收服务的标识
            timeout: 超时时间(秒)，None 表示无限等待

        Returns:
            MessageEnvelope 或 None (超时/关闭)
        """
        pass

    @abstractmethod
    async def receive_stream(self, service: str) -> AsyncIterator[MessageEnvelope]:
        """
        接收消息流 (异步迭代器)

        Args:
            service: 接收服务的标识

        Yields:
            MessageEnvelope: 消息信封
        """
        pass

    @abstractmethod
    def subscribe(
        self,
        service: str,
        msg_type: str,
        handler: Callable[[MessageEnvelope], None],
    ) -> str:
        """
        订阅特定类型的消息

        Args:
            service: 订阅服务的标识
            msg_type: 消息类型 ("*" 表示订阅所有类型)
            handler: 消息处理回调函数

        Returns:
            str: 订阅ID，用于取消订阅
        """
        pass

    @abstractmethod
    def unsubscribe(self, service: str, subscription_id: str) -> bool:
        """
        取消订阅

        Args:
            service: 服务标识
            subscription_id: 订阅ID

        Returns:
            bool: 取消成功返回 True
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭传输连接，释放资源"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查传输连接是否活跃"""
        pass

    # === 可选的批量操作 ===

    async def send_batch(self, envelopes: List[MessageEnvelope]) -> int:
        """
        批量发送消息

        Args:
            envelopes: 消息信封列表

        Returns:
            int: 成功发送的数量
        """
        success_count = 0
        for envelope in envelopes:
            if await self.send(envelope):
                success_count += 1
        return success_count

    async def broadcast(self, envelope: MessageEnvelope, services: List[str]) -> int:
        """
        广播消息到多个服务

        Args:
            envelope: 消息信封 (to_service 会被覆盖)
            services: 目标服务列表

        Returns:
            int: 成功发送的数量
        """
        from dataclasses import replace
        success_count = 0
        for service in services:
            targeted = replace(envelope, to_service=service)
            if await self.send(targeted):
                success_count += 1
        return success_count


class MessageHandler(ABC):
    """
    消息处理器抽象基类

    提供结构化的消息处理方式
    """

    @abstractmethod
    async def handle(self, envelope: MessageEnvelope) -> Optional[MessageEnvelope]:
        """
        处理消息

        Args:
            envelope: 接收到的消息信封

        Returns:
            Optional[MessageEnvelope]: 可选的回复消息
        """
        pass

    @abstractmethod
    def can_handle(self, envelope: MessageEnvelope) -> bool:
        """
        判断是否可以处理该消息

        Args:
            envelope: 消息信封

        Returns:
            bool: 能处理返回 True
        """
        pass


class SimpleMessageHandler(MessageHandler):
    """简单的消息处理器实现"""

    def __init__(
        self,
        msg_type: str,
        handler_func: Callable[[MessageEnvelope], Optional[MessageEnvelope]],
    ):
        self.msg_type = msg_type
        self.handler_func = handler_func

    async def handle(self, envelope: MessageEnvelope) -> Optional[MessageEnvelope]:
        """调用处理函数"""
        if asyncio.iscoroutinefunction(self.handler_func):
            return await self.handler_func(envelope)
        return self.handler_func(envelope)

    def can_handle(self, envelope: MessageEnvelope) -> bool:
        """检查消息类型是否匹配"""
        return envelope.msg_type == self.msg_type


class RoutingMessageHandler(MessageHandler):
    """路由消息处理器 - 根据消息类型分发到不同的处理器"""

    def __init__(self):
        self.handlers: Dict[str, MessageHandler] = {}
        self.default_handler: Optional[MessageHandler] = None

    def register(self, msg_type: str, handler: MessageHandler) -> None:
        """注册特定类型的处理器"""
        self.handlers[msg_type] = handler

    def set_default(self, handler: MessageHandler) -> None:
        """设置默认处理器"""
        self.default_handler = handler

    async def handle(self, envelope: MessageEnvelope) -> Optional[MessageEnvelope]:
        """路由到对应的处理器"""
        handler = self.handlers.get(envelope.msg_type, self.default_handler)
        if handler:
            return await handler.handle(envelope)
        return None

    def can_handle(self, envelope: MessageEnvelope) -> bool:
        """检查是否有匹配的处理器"""
        return envelope.msg_type in self.handlers or self.default_handler is not None
