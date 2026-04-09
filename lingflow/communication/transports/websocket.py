"""
WebSocket 传输实现 - WebSocketTransport v1.0

基于 aiohttp WebSocket 的实时传输实现
适用于需要双向实时通信的场景

特性:
- 双向实时通信
- 自动重连机制
- 心跳保活
- 支持订阅模式
"""

import asyncio
import json
import logging
from collections import defaultdict
from typing import AsyncIterator, Callable, Dict, Optional
from uuid import uuid4

from ..envelope import MessageEnvelope
from ..transport import TransportAdapter

logger = logging.getLogger(__name__)


class WebSocketTransport(TransportAdapter):
    """
    WebSocket 传输实现

    使用 WebSocket 进行双向实时通信
    适合需要即时消息传递的场景
    """

    def __init__(
        self,
        service_name: str,
        hub_url: str = "ws://localhost:8100/ws",
        reconnect_interval: float = 5.0,
        heartbeat_interval: float = 30.0,
        max_reconnects: int = 10,
    ):
        """
        初始化 WebSocket 传输

        Args:
            service_name: 本服务名称
            hub_url: WebSocket Hub URL
            reconnect_interval: 重连间隔（秒）
            heartbeat_interval: 心跳间隔（秒）
            max_reconnects: 最大重连次数
        """
        self.service_name = service_name
        self._hub_url = hub_url
        self._reconnect_interval = reconnect_interval
        self._heartbeat_interval = heartbeat_interval
        self._max_reconnects = max_reconnects

        self._running = False
        self._ws = None
        self._session = None

        self._receive_queue: asyncio.Queue = asyncio.Queue()
        self._subscriptions: Dict[str, Dict[str, tuple]] = defaultdict(dict)

        self._recv_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._dispatch_tasks: set = set()

    async def _get_session(self):
        """获取 aiohttp session"""
        if self._session is None or self._session.closed:
            try:
                import aiohttp

                self._session = aiohttp.ClientSession()
            except ImportError:
                raise ImportError("aiohttp is required for WebSocketTransport. " "Install it with: pip install aiohttp")
        return self._session

    async def _connect(self) -> bool:
        """连接到 WebSocket Hub"""
        session = await self._get_session()
        try:
            ws_url = f"{self._hub_url}?service={self.service_name}"
            self._ws = await session.ws_connect(ws_url)
            logger.info("WebSocket connected to %s", self._hub_url)
            return True
        except Exception as e:
            logger.error("WebSocket connection failed: %s", e)
            return False

    async def _connect_with_retries(self) -> bool:
        """带重试的连接"""
        for attempt in range(self._max_reconnects):
            if await self._connect():
                return True
            if attempt < self._max_reconnects - 1:
                logger.info(
                    "Retrying in %.1fs (attempt %d/%d)",
                    self._reconnect_interval,
                    attempt + 1,
                    self._max_reconnects,
                )
                await asyncio.sleep(self._reconnect_interval)
        return False

    async def _recv_loop(self) -> None:
        """接收消息循环"""
        while self._running:
            try:
                if self._ws is None or self._ws.closed:
                    if not await self._connect_with_retries():
                        break
                    continue

                msg = await self._ws.receive()

                if msg.type == 0x1:  # aiohttp.WSMsgType.TEXT
                    try:
                        data = json.loads(msg.data)
                        envelope = MessageEnvelope.from_dict(data)

                        if not envelope.is_expired():
                            await self._receive_queue.put(envelope)
                            await self._dispatch(envelope)
                    except Exception as e:
                        logger.error("Error parsing message: %s", e)

                elif msg.type in (0x8, 0x100):  # CLOSE or ERROR
                    logger.warning("WebSocket closed, reconnecting...")
                    self._ws = None
                    if self._running:
                        await asyncio.sleep(self._reconnect_interval)

                elif msg.type == 0x101:  # CLOSED
                    self._ws = None

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Receive loop error: %s", e)
                if self._running:
                    await asyncio.sleep(1.0)

    async def _heartbeat_loop(self) -> None:
        """心跳保活循环"""
        while self._running:
            try:
                if self._ws and not self._ws.closed:
                    from ..registry import MessageTypeRegistry

                    heartbeat = MessageEnvelope(
                        from_service=self.service_name,
                        to_service="*",
                        msg_type=MessageTypeRegistry.Family.HEARTBEAT,
                        payload={"service": self.service_name},
                    )
                    await self._ws.send_str(heartbeat.to_json())
            except Exception as e:
                logger.debug("Heartbeat failed: %s", e)

            await asyncio.sleep(self._heartbeat_interval)

    async def _dispatch(self, envelope: MessageEnvelope) -> None:
        """分发消息到订阅者"""
        for service in self._subscriptions:
            for sub_id, (msg_type, handler) in self._subscriptions[service].items():
                if msg_type == "*" or envelope.msg_type == msg_type:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            task = asyncio.create_task(handler(envelope))
                            self._dispatch_tasks.add(task)
                            task.add_done_callback(self._dispatch_tasks.discard)
                        else:
                            handler(envelope)
                    except Exception as e:
                        logger.error("Dispatch handler error: %s", e)

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

        if envelope.is_expired():
            return False

        try:
            if self._ws is None or self._ws.closed:
                if not await self._connect_with_retries():
                    return False

            await self._ws.send_str(envelope.to_json())
            return True

        except Exception as e:
            logger.error("WebSocket send error: %s", e)
            self._ws = None
            return False

    async def receive(self, service: str, timeout: Optional[float] = None) -> Optional[MessageEnvelope]:
        """
        接收消息

        Args:
            service: 服务标识
            timeout: 超时时间

        Returns:
            MessageEnvelope 或 None
        """
        try:
            if timeout is None:
                return await self._receive_queue.get()
            return await asyncio.wait_for(self._receive_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def receive_stream(self, service: str) -> AsyncIterator[MessageEnvelope]:
        """
        接收消息流

        Args:
            service: 服务标识

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
        """订阅特定类型的消息"""
        subscription_id = uuid4().hex
        self._subscriptions[service][subscription_id] = (msg_type, handler)
        return subscription_id

    def unsubscribe(self, service: str, subscription_id: str) -> bool:
        """取消订阅"""
        if service in self._subscriptions and subscription_id in self._subscriptions[service]:
            del self._subscriptions[service][subscription_id]
            return True
        return False

    async def close(self) -> None:
        """关闭传输连接"""
        self._running = False

        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass

        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        for task in self._dispatch_tasks:
            if not task.done():
                task.cancel()

        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._running and self._ws is not None and not self._ws.closed

    def start(self) -> None:
        """启动传输层"""
        self._running = True
        self._recv_task = asyncio.create_task(self._recv_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
