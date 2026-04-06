"""
消息信封模块 - MessageEnvelope v1.0

统一消息信封格式，支持:
- 路由信息 (from_service, to_service)
- 消息类型 (msg_type, correlation_id)
- 负载 (payload)
- 元数据 (timestamp, ttl, priority)
- 传递追踪 (reply_to, trace_id)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4
import json


@dataclass(frozen=True)
class MessageEnvelope:
    """
    统一消息信封 - 灵信协议核心

    设计原则:
    - 使用 frozen dataclass 确保不可变性
    - 所有字段都有明确的类型注解
    - 支持序列化和反序列化

    Attributes:
        msg_id: 消息唯一标识符
        from_service: 发送服务标识 (如 "lingyi", "lingzhi")
        to_service: 接收服务标识 ("*" 为广播)
        msg_type: 消息类型标识 (参考 MessageTypeRegistry)
        correlation_id: 关联ID，用于请求响应匹配
        payload: 消息负载数据
        timestamp: 消息创建时间戳
        ttl: 存活时间(秒)，None表示永不过期
        priority: 优先级 (0=普通, 1=重要, 2=紧急)
        reply_to: 回复地址，用于请求响应模式
        trace_id: 追踪ID，用于分布式追踪
    """

    # === 路由信息 ===
    msg_id: str = field(default_factory=lambda: uuid4().hex)
    from_service: str = ""
    to_service: str = ""

    # === 消息类型 ===
    msg_type: str = ""
    correlation_id: Optional[str] = None

    # === 负载 ===
    payload: Dict[str, Any] = field(default_factory=dict)

    # === 元数据 ===
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None
    priority: int = 0

    # === 传递追踪 ===
    reply_to: Optional[str] = None
    trace_id: Optional[str] = None

    def __post_init__(self):
        """验证消息信封的有效性"""
        if not self.from_service:
            raise ValueError("from_service 不能为空")
        if not self.to_service:
            raise ValueError("to_service 不能为空")
        if not self.msg_type:
            raise ValueError("msg_type 不能为空")
        if self.priority not in (0, 1, 2):
            raise ValueError("priority 必须是 0, 1, 或 2")

    def is_broadcast(self) -> bool:
        """检查是否为广播消息"""
        return self.to_service == "*"

    def is_expired(self) -> bool:
        """检查消息是否已过期"""
        if self.ttl is None:
            return False
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl

    def age_seconds(self) -> float:
        """获取消息年龄（秒）"""
        return (datetime.now() - self.timestamp).total_seconds()

    def with_reply(self, reply_service: str) -> "MessageEnvelope":
        """创建带有回复地址的新消息信封"""
        # frozen dataclass 需要通过 object.__setattr__ 修改
        # 或者使用 dataclasses.replace
        from dataclasses import replace
        return replace(self, reply_to=reply_service)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "msg_id": self.msg_id,
            "from_service": self.from_service,
            "to_service": self.to_service,
            "msg_type": self.msg_type,
            "correlation_id": self.correlation_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
            "priority": self.priority,
            "reply_to": self.reply_to,
            "trace_id": self.trace_id,
        }

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageEnvelope":
        """从字典反序列化"""
        # 处理 timestamp
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # 过滤 None 值，保持字段默认值
        filtered_data = {k: v for k, v in data.items() if v is not None or k in cls.__dataclass_fields__}
        return cls(**filtered_data)

    @classmethod
    def from_json(cls, json_str: str) -> "MessageEnvelope":
        """从 JSON 字符串反序列化"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def create_reply(
        self,
        reply_payload: Dict[str, Any],
        reply_type: str,
        from_service: str,
    ) -> "MessageEnvelope":
        """
        创建回复消息

        Args:
            reply_payload: 回复负载数据
            reply_type: 回复消息类型
            from_service: 回复发送方服务标识

        Returns:
            新的 MessageEnvelope 作为回复
        """
        from dataclasses import replace
        return replace(
            self,
            msg_id=uuid4().hex,
            from_service=from_service,
            to_service=self.from_service,
            msg_type=reply_type,
            payload=reply_payload,
            correlation_id=self.msg_id,
            timestamp=datetime.now(),
            reply_to=None,
        )

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"MessageEnvelope("
            f"id={self.msg_id[:8]}..., "
            f"{self.from_service}->{self.to_service}, "
            f"type={self.msg_type}"
            f")"
        )


def create_envelope(
    from_service: str,
    to_service: str,
    msg_type: str,
    payload: Dict[str, Any],
    priority: int = 0,
    ttl: Optional[int] = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> MessageEnvelope:
    """
    创建消息信封的工厂函数

    Args:
        from_service: 发送服务标识
        to_service: 接收服务标识
        msg_type: 消息类型
        payload: 消息负载数据
        priority: 优先级 (0=普通, 1=重要, 2=紧急)
        ttl: 存活时间(秒)
        correlation_id: 关联ID
        trace_id: 追踪ID

    Returns:
        MessageEnvelope 实例
    """
    return MessageEnvelope(
        from_service=from_service,
        to_service=to_service,
        msg_type=msg_type,
        payload=payload,
        priority=priority,
        ttl=ttl,
        correlation_id=correlation_id,
        trace_id=trace_id,
    )
