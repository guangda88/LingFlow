"""
内存队列传输实现 - InMemoryTransport v1.0

基于 asyncio.Queue 的内存传输实现
适用于同进程内的服务间通信

特性:
- 异步队列保证线程安全
- 支持订阅模式
- 支持消息过滤
- 支持广播
"""

import asyncio
import threading
from collections import defaultdict
from typing import AsyncIterator, Callable, Dict, Optional, Set
from uuid import uuid4

from ..transport import TransportAdapter
from ..envelope import MessageEnvelope


class InMemoryTransport(TransportAdapter):
    """
    内存队列传输实现

    使用 asyncio.Queue 实现同进程内的服务间通信
    线程安全，支持订阅模式
    """

    def __init__(self):
        # 每个服务的消息队列
        self._queues: Dict[str, asyncio.Queue] = defaultdict(lambda: asyncio.Queue())

        # 订阅信息: {service: {subscription_id: (msg_type, handler)}}
        self._subscriptions: Dict[str, Dict[str, tuple]] = defaultdict(dict)

        # 后台任务
        self._dispatcher_tasks: Dict[str, asyncio.Task] = {}
        self._running = False

        # 线程锁（用于跨线程操作）
        self._lock = threading.Lock()

        # 事件循环（用于跨线程调用）
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread_id: Optional[int] = None

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """确保在正确的事件循环中运行"""
        current_loop = asyncio.get_event_loop()
        current_tid = threading.get_ident()

        if self._loop is None:
            self._loop = current_loop
            self._loop_thread_id = current_tid
        elif self._loop_thread_id != current_tid:
            # 跨线程调用，需要使用 asyncio.run_coroutine_threadsafe
            pass

        return current_loop

    async def send(self, envelope: MessageEnvelope) -> bool:
        """
        发送消息

        Args:
            envelope: 消息信封

        Returns:
            bool: 发送成功返回 True
        """
        if not self._running:
            return False

        try:
            # 检查消息是否过期
            if envelope.is_expired():
                return False

            target = envelope.to_service

            # 广播模式
            if target == "*":
                success = True
                for service in self._queues.keys():
                    try:
                        await self._queues[service].put(envelope)
                    except asyncio.QueueFull:
                        success = False
                return success

            # 单播模式
            if target in self._queues:
                await self._queues[target].put(envelope)
                return True

            # 目标服务不存在，创建队列
            await self._queues[target].put(envelope)
            return True

        except Exception:
            return False

    async def receive(self, service: str, timeout: Optional[float] = None) -> Optional[MessageEnvelope]:
        """
        接收消息 (阻塞)

        Args:
            service: 接收服务的标识
            timeout: 超时时间(秒)

        Returns:
            MessageEnvelope 或 None
        """
        try:
            queue = self._queues[service]

            if timeout is None:
                return await queue.get()

            try:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                return None

        except Exception:
            return None

    async def receive_stream(self, service: str) -> AsyncIterator[MessageEnvelope]:
        """
        接收消息流

        Args:
            service: 接收服务的标识

        Yields:
            MessageEnvelope
        """
        while self._running:
            envelope = await self.receive(service, timeout=1.0)
            if envelope:
                yield envelope

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
            msg_type: 消息类型 ("*" 表示所有类型)
            handler: 消息处理回调

        Returns:
            str: 订阅ID
        """
        subscription_id = uuid4().hex

        with self._lock:
            self._subscriptions[service][subscription_id] = (msg_type, handler)

            # 启动分发任务（如果尚未启动）
            if service not in self._dispatcher_tasks or self._dispatcher_tasks[service].done():
                self._dispatcher_tasks[service] = asyncio.create_task(self._dispatch_loop(service))

        return subscription_id

    def unsubscribe(self, service: str, subscription_id: str) -> bool:
        """
        取消订阅

        Args:
            service: 服务标识
            subscription_id: 订阅ID

        Returns:
            bool: 取消成功返回 True
        """
        with self._lock:
            if service in self._subscriptions and subscription_id in self._subscriptions[service]:
                del self._subscriptions[service][subscription_id]
                return True
        return False

    async def _dispatch_loop(self, service: str) -> None:
        """消息分发循环"""
        while self._running:
            # 获取订阅信息（快照）
            with self._lock:
                subscriptions = dict(self._subscriptions.get(service, {}))

            if not subscriptions:
                await asyncio.sleep(0.1)
                continue

            # 接收消息
            envelope = await self.receive(service, timeout=0.5)
            if not envelope:
                continue

            # 分发消息
            for sub_id, (msg_type, handler) in subscriptions.items():
                # 检查消息类型是否匹配
                if msg_type != "*" and envelope.msg_type != msg_type:
                    continue

                try:
                    # 调用处理器
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(envelope))
                    else:
                        handler(envelope)
                except Exception:
                    # 处理器异常不影响其他订阅者
                    pass

    async def close(self) -> None:
        """关闭传输连接"""
        self._running = False

        # 取消所有分发任务
        for task in self._dispatcher_tasks.values():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._dispatcher_tasks.clear()
        self._queues.clear()
        self._subscriptions.clear()

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._running

    def start(self) -> None:
        """启动传输层"""
        self._running = True

    def get_queue_size(self, service: str) -> int:
        """获取指定服务的队列大小"""
        queue = self._queues.get(service)
        return queue.qsize() if queue else 0

    def get_services(self) -> Set[str]:
        """获取所有已注册的服务"""
        return set(self._queues.keys())


class InMemoryMessageBus:
    """
    内存消息总线 - 高级封装

    提供更简单的消息总线接口，支持请求-响应模式
    """

    def __init__(self):
        self.transport = InMemoryTransport()
        self.transport.start()
        self._pending_requests: Dict[str, asyncio.Future] = {}

    async def send(
        self,
        from_service: str,
        to_service: str,
        msg_type: str,
        payload: dict,
        priority: int = 0,
    ) -> bool:
        """发送消息"""
        envelope = MessageEnvelope(
            from_service=from_service,
            to_service=to_service,
            msg_type=msg_type,
            payload=payload,
            priority=priority,
        )
        return await self.transport.send(envelope)

    async def request(
        self,
        from_service: str,
        to_service: str,
        msg_type: str,
        payload: dict,
        timeout: float = 5.0,
    ) -> Optional[dict]:
        """
        发送请求并等待响应

        Args:
            from_service: 发送服务
            to_service: 目标服务
            msg_type: 消息类型
            payload: 请求负载
            timeout: 超时时间

        Returns:
            响应负载或 None
        """
        correlation_id = uuid4().hex
        future = asyncio.Future()

        self._pending_requests[correlation_id] = future

        try:
            envelope = MessageEnvelope(
                from_service=from_service,
                to_service=to_service,
                msg_type=msg_type,
                payload=payload,
                correlation_id=correlation_id,
                reply_to=from_service,
            )
            await self.transport.send(envelope)

            # 等待响应
            response = await asyncio.wait_for(future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            return None
        finally:
            self._pending_requests.pop(correlation_id, None)

    async def respond(
        self,
        request: MessageEnvelope,
        response_payload: dict,
        response_type: str,
    ) -> bool:
        """响应请求"""
        if request.correlation_id and request.correlation_id in self._pending_requests:
            # 设置响应
            future = self._pending_requests[request.correlation_id]
            if not future.done():
                future.set_result(response_payload)

        # 发送响应消息
        reply = request.create_reply(
            reply_payload=response_payload,
            reply_type=response_type,
            from_service=request.to_service,
        )
        return await self.transport.send(reply)

    def subscribe(
        self,
        service: str,
        msg_type: str,
        handler: Callable,
    ) -> str:
        """订阅消息"""
        return self.transport.subscribe(service, msg_type, handler)

    async def close(self) -> None:
        """关闭消息总线"""
        await self.transport.close()

        # 取消所有等待中的请求
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
