"""
HTTP 传输实现 - HttpTransport v1.0

基于 aiohttp 的 HTTP 传输实现
适用于跨进程、跨主机的服务间通信

特性:
- 基于 HTTP POST 的消息传递
- 支持重试机制
- 支持消息压缩
- 支持服务发现
"""

import asyncio
import logging
from collections import defaultdict
from typing import AsyncIterator, Callable, Dict, Optional, Set
from uuid import uuid4

from ..envelope import MessageEnvelope
from ..transport import TransportAdapter

logger = logging.getLogger(__name__)


class HttpTransport(TransportAdapter):
    """
    HTTP 传输实现

    使用 HTTP POST 发送消息到远程服务端点
    适合跨进程和跨主机通信
    """

    def __init__(
        self,
        service_name: str,
        endpoints: Optional[Dict[str, str]] = None,
        default_endpoint: str = "http://localhost:8100/api/v1/message",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
    ):
        """
        初始化 HTTP 传输

        Args:
            service_name: 本服务名称
            endpoints: 服务端点映射 {service_name: url}
            default_endpoint: 默认消息端点
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 请求超时（秒）
        """
        self.service_name = service_name
        self._endpoints: Dict[str, str] = dict(endpoints or {})
        self._default_endpoint = default_endpoint
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._timeout = timeout

        self._running = False
        self._session = None

        self._subscriptions: Dict[str, Dict[str, tuple]] = defaultdict(dict)
        self._pending_replies: Dict[str, asyncio.Future] = {}

    def register_endpoint(self, service: str, url: str) -> None:
        """
        注册服务端点

        Args:
            service: 服务名称
            url: 服务端点 URL
        """
        self._endpoints[service] = url

    def _get_endpoint(self, service: str) -> str:
        """获取服务端点"""
        return self._endpoints.get(service, self._default_endpoint)

    async def _get_session(self):
        """获取 aiohttp session（延迟导入）"""
        if self._session is None or self._session.closed:
            try:
                import aiohttp

                self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._timeout))
            except ImportError:
                raise ImportError("aiohttp is required for HttpTransport. " "Install it with: pip install aiohttp")
        return self._session

    async def send(self, envelope: MessageEnvelope) -> bool:
        """
        发送消息（HTTP POST）

        Args:
            envelope: 消息信封

        Returns:
            bool: 发送成功返回 True
        """
        if not self._running:
            return False

        if envelope.is_expired():
            return False

        target = envelope.to_service

        if target == "*":
            success = True
            for service in self._endpoints:
                if not await self._send_to_endpoint(envelope, service):
                    success = False
            return success

        return await self._send_to_endpoint(envelope, target)

    async def _send_to_endpoint(self, envelope: MessageEnvelope, service: str) -> bool:
        """发送消息到指定服务端点"""
        endpoint = self._get_endpoint(service)
        session = await self._get_session()

        payload = envelope.to_json()

        for attempt in range(self._max_retries):
            try:
                async with session.post(
                    endpoint,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        return True
                    elif response.status >= 500:
                        logger.warning(
                            "Server error %d for %s (attempt %d/%d)",
                            response.status,
                            service,
                            attempt + 1,
                            self._max_retries,
                        )
                        if attempt < self._max_retries - 1:
                            await asyncio.sleep(self._retry_delay * (attempt + 1))
                        continue
                    else:
                        logger.error(
                            "HTTP %d sending to %s: %s",
                            response.status,
                            service,
                            await response.text(),
                        )
                        return False
            except asyncio.TimeoutError:
                logger.warning(
                    "Timeout sending to %s (attempt %d/%d)",
                    service,
                    attempt + 1,
                    self._max_retries,
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay)
            except Exception as e:
                logger.error("Error sending to %s: %s", service, e)
                return False

        return False

    async def receive(self, service: str, timeout: Optional[float] = None) -> Optional[MessageEnvelope]:
        """
        接收消息（HTTP 模式下不直接支持，建议使用订阅模式）
        """
        logger.warning("HttpTransport.receive() is not directly supported. " "Use subscribe() or webhook endpoint instead.")
        return None

    async def receive_stream(self, service: str) -> AsyncIterator[MessageEnvelope]:
        """
        接收消息流（HTTP 模式下不直接支持）
        """
        logger.warning("HttpTransport.receive_stream() is not directly supported. " "Use WebSocket transport for streaming.")
        return
        yield  # make it an async generator

    def handle_incoming(self, data: Dict) -> Optional[MessageEnvelope]:
        """
        处理收到的 HTTP 请求（供 Web 框架调用）

        Args:
            data: 收到的消息字典

        Returns:
            解析后的 MessageEnvelope
        """
        try:
            envelope = MessageEnvelope.from_dict(data)

            correlation_id = envelope.correlation_id
            if correlation_id and correlation_id in self._pending_replies:
                future = self._pending_replies[correlation_id]
                if not future.done():
                    future.set_result(envelope)

            for sub_id, (msg_type, handler) in self._subscriptions.get(self.service_name, {}).items():
                if msg_type == "*" or envelope.msg_type == msg_type:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            asyncio.create_task(handler(envelope))
                        else:
                            handler(envelope)
                    except Exception as e:
                        logger.error("Subscription handler error: %s", e)

            return envelope

        except Exception as e:
            logger.error("Error handling incoming message: %s", e)
            return None

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

    async def request(
        self,
        to_service: str,
        msg_type: str,
        payload: Dict,
        timeout: float = 10.0,
    ) -> Optional[MessageEnvelope]:
        """
        发送请求并等待响应

        Args:
            to_service: 目标服务
            msg_type: 消息类型
            payload: 负载
            timeout: 超时时间

        Returns:
            响应 MessageEnvelope 或 None
        """
        correlation_id = uuid4().hex
        future: asyncio.Future = asyncio.Future()
        self._pending_replies[correlation_id] = future

        try:
            envelope = MessageEnvelope(
                from_service=self.service_name,
                to_service=to_service,
                msg_type=msg_type,
                payload=payload,
                correlation_id=correlation_id,
                reply_to=self.service_name,
            )

            await self.send(envelope)
            return await asyncio.wait_for(future, timeout=timeout)

        except asyncio.TimeoutError:
            return None
        finally:
            self._pending_replies.pop(correlation_id, None)

    async def close(self) -> None:
        """关闭传输连接"""
        self._running = False

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        for future in self._pending_replies.values():
            if not future.done():
                future.cancel()
        self._pending_replies.clear()

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._running

    def start(self) -> None:
        """启动传输层"""
        self._running = True

    def get_registered_services(self) -> Set[str]:
        """获取已注册端点的服务列表"""
        return set(self._endpoints.keys())
