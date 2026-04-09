"""
LingMessage v1.0 - 灵字辈统一通信协议

该模块实现灵字辈大家庭的统一消息通信协议，包括:
- MessageEnvelope: 统一消息信封
- MessageTypeRegistry: 消息类型注册表
- TransportAdapter: 传输适配器抽象接口
- InMemoryTransport: 内存队列传输实现
- FileTransport: 文件传输实现
- HttpTransport: HTTP 传输实现
- WebSocketTransport: WebSocket 传输实现

使用示例:
    from lingflow.communication import MessageEnvelope, InMemoryTransport, MessageTypeRegistry

    # 创建传输层
    transport = InMemoryTransport()

    # 创建消息
    envelope = MessageEnvelope(
        from_service="lingyi",
        to_service="lingzhi",
        msg_type=MessageTypeRegistry.KNOWLEDGE_QUERY,
        payload={"query": "什么是多智能体系统?"}
    )

    # 发送消息
    await transport.send(envelope)
"""

__version__ = "1.0.0"
__author__ = "灵信 (LingXin)"

from .envelope import MessageEnvelope, create_envelope
from .registry import MessageTypeRegistry
from .transport import TransportAdapter
from .transports.file import FileTransport
from .transports.http import HttpTransport
from .transports.memory import InMemoryTransport
from .transports.websocket import WebSocketTransport

__all__ = [
    "MessageEnvelope",
    "create_envelope",
    "MessageTypeRegistry",
    "TransportAdapter",
    "InMemoryTransport",
    "FileTransport",
    "HttpTransport",
    "WebSocketTransport",
]
