# LingMessage v1.0 - 灵字辈统一通信协议

LingMessage 是灵字辈大家庭的统一消息通信协议，实现跨项目的消息传递和服务协作。

## 特性

- **统一消息格式**: MessageEnvelope 提供标准化的消息信封
- **类型安全**: MessageTypeRegistry 定义所有消息类型常量
- **多种传输方式**: 支持内存队列、文件传输等
- **异步支持**: 基于 asyncio 的全异步实现
- **订阅模式**: 支持按消息类型订阅和过滤
- **请求-响应**: 支持同步请求-响应模式

## 快速开始

### 基本使用

```python
import asyncio
from lingflow.communication import (
    MessageEnvelope,
    InMemoryTransport,
    MessageTypeRegistry,
)

async def main():
    # 创建传输层
    transport = InMemoryTransport()
    transport.start()

    # 创建消息
    envelope = MessageEnvelope(
        from_service="lingyi",
        to_service="lingzhi",
        msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
        payload={"query": "什么是多智能体系统?"}
    )

    # 发送消息
    await transport.send(envelope)

    # 接收消息
    received = await transport.receive("lingzhi", timeout=5.0)
    print(f"收到消息: {received.payload}")

    await transport.close()

asyncio.run(main())
```

### 订阅模式

```python
async def handle_message(envelope: MessageEnvelope):
    print(f"处理消息: {envelope.msg_type} - {envelope.payload}")

# 订阅特定类型的消息
transport.subscribe(
    service="lingzhi",
    msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
    handler=handle_message,
)

# 订阅所有消息
transport.subscribe(
    service="lingzhi",
    msg_type="*",
    handler=handle_message,
)
```

### 请求-响应模式

```python
from lingflow.communication.transports.memory import InMemoryMessageBus

bus = InMemoryMessageBus()

# 设置响应处理器
async def handle_request(envelope):
    await bus.respond(
        request=envelope,
        response_payload={"answer": "这是响应"},
        response_type="response.type",
    )

bus.subscribe("lingzhi", MessageTypeRegistry.Family.KNOWLEDGE_QUERY, handle_request)

# 发送请求并等待响应
response = await bus.request(
    from_service="lingyi",
    to_service="lingzhi",
    msg_type=MessageTypeRegistry.Family.KNOWLEDGE_QUERY,
    payload={"query": "测试查询"},
)

print(f"收到响应: {response}")
```

## 消息类型

### LingFlow 消息类型

| 类型 | 描述 |
|------|------|
| `lingflow.task.submit` | 提交新任务 |
| `lingflow.task.result` | 任务执行结果 |
| `lingflow.skill.execute` | 执行技能命令 |
| `lingflow.workflow.start` | 启动工作流 |
| `lingflow.workflow.complete` | 工作流完成 |

### LingTongAsk 消息类型

| 类型 | 描述 |
|------|------|
| `lingtongask.comment.new` | 新粉丝评论 |
| `lingtongask.message.new` | 新粉丝消息 |
| `lingtongask.reply.draft` | 回复草稿 |
| `lingtongask.content.generate` | 生成内容 |

### 通用消息类型

| 类型 | 描述 |
|------|------|
| `family.heartbeat` | 成员心跳 |
| `family.status.update` | 状态更新 |
| `family.knowledge.query` | 知识查询 |
| `family.handoff.request` | 交接请求 |
| `family.handoff.response` | 交接响应 |

## API 文档

### MessageEnvelope

```python
@dataclass(frozen=True)
class MessageEnvelope:
    msg_id: str                      # 消息唯一ID
    from_service: str                 # 发送服务
    to_service: str                   # 接收服务 (* 为广播)
    msg_type: str                     # 消息类型
    correlation_id: Optional[str]     # 关联ID
    payload: Dict[str, Any]           # 消息负载
    timestamp: datetime               # 时间戳
    ttl: Optional[int]                # 存活时间(秒)
    priority: int                     # 优先级 (0/1/2)
    reply_to: Optional[str]           # 回复地址
    trace_id: Optional[str]           # 追踪ID
```

### TransportAdapter

```python
class TransportAdapter(ABC):
    async def send(envelope: MessageEnvelope) -> bool: ...
    async def receive(service: str, timeout: float) -> Optional[MessageEnvelope]: ...
    def subscribe(service: str, msg_type: str, handler: Callable) -> str: ...
    def unsubscribe(service: str, subscription_id: str) -> bool: ...
    async def close() -> None: ...
```

### 传输实现

| 传输类型 | 类名 | 适用场景 |
|----------|------|----------|
| 内存队列 | `InMemoryTransport` | 同进程通信 |
| 文件传输 | `FileTransport` | 离线场景、持久化 |
| HTTP 传输 | `HttpTransport` | 跨进程、跨主机通信 |
| WebSocket 传输 | `WebSocketTransport` | 双向实时通信 |

## 运行测试

```bash
# 运行所有测试
pytest lingflow/communication/tests/

# 运行特定测试
pytest lingflow/communication/tests/test_envelope.py -v
pytest lingflow/communication/tests/test_memory_transport.py -v
pytest lingflow/communication/tests/test_registry.py -v
```

## 设计原则

1. **不可变性**: MessageEnvelope 使用 frozen dataclass
2. **类型安全**: 所有消息类型在注册表中定义
3. **异步优先**: 全异步 API 设计
4. **可扩展**: 支持自定义传输适配器
5. **简洁性**: 最小化依赖，保持简单

## 版本历史

- **v1.0** (2026-04-04): 初始版本
  - MessageEnvelope 实现
  - MessageTypeRegistry 实现
  - InMemoryTransport 实现
  - FileTransport 实现
  - 完整单元测试

## 作者

灵信 (LingXin) - 灵字辈通信协议负责人
