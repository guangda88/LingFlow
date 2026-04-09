"""
文件传输实现 - FileTransport v1.0

基于文件系统的传输实现
适用于离线场景和跨进程通信

特性:
- 基于文件系统的消息持久化
- 支持断点续传
- 支持消息重放
- 支持目录监控
"""

import asyncio
import threading
import time
from pathlib import Path
from typing import AsyncIterator, Callable, Dict, List, Optional, Set
from uuid import uuid4

from ..envelope import MessageEnvelope
from ..transport import TransportAdapter


class FileTransport(TransportAdapter):
    """
    文件传输实现

    使用文件系统存储和传递消息
    适合离线场景和需要消息持久化的情况
    """

    def __init__(self, base_dir: str = "/tmp/lingmessage"):
        """
        初始化文件传输

        Args:
            base_dir: 消息存储基础目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # 每个服务的消息目录
        self.service_dirs: Dict[str, Path] = {}

        # 待处理文件队列
        self._queues: Dict[str, asyncio.Queue] = {}

        # 订阅信息
        self._subscriptions: Dict[str, Dict[str, tuple]] = {}

        # 运行状态
        self._running = False
        self._watcher_tasks: Dict[str, asyncio.Task] = {}

        # 锁
        self._lock = threading.Lock()

        # 消息处理标记
        self._processed_suffix = ".processed"

    def _get_service_dir(self, service: str) -> Path:
        """获取服务的消息目录"""
        if service not in self.service_dirs:
            service_dir = self.base_dir / service
            service_dir.mkdir(parents=True, exist_ok=True)
            self.service_dirs[service] = service_dir
        return self.service_dirs[service]

    def _get_message_path(self, service: str, msg_id: str) -> Path:
        """获取消息文件路径"""
        service_dir = self._get_service_dir(service)
        return service_dir / f"{msg_id}.json"

    async def send(self, envelope: MessageEnvelope) -> bool:
        """
        发送消息（写入文件）

        Args:
            envelope: 消息信封

        Returns:
            bool: 发送成功返回 True
        """
        if not self._running:
            return False

        try:
            target = envelope.to_service

            # 广播模式
            if target == "*":
                success = True
                for service in self.service_dirs.keys():
                    if not await self._send_to_service(envelope, service):
                        success = False
                return success

            # 单播模式
            return await self._send_to_service(envelope, target)

        except Exception:
            return False

    async def _send_to_service(self, envelope: MessageEnvelope, service: str) -> bool:
        """发送消息到指定服务"""
        try:
            msg_path = self._get_message_path(service, envelope.msg_id)

            # 写入消息文件
            with open(msg_path, "w", encoding="utf-8") as f:
                f.write(envelope.to_json())

            # 如果有队列，通知新消息
            if service in self._queues:
                await self._queues[service].put(envelope.msg_id)

            return True

        except Exception:
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
            # 确保队列存在
            if service not in self._queues:
                self._queues[service] = asyncio.Queue()
                # 启动文件监控任务
                if self._running:
                    self._watcher_tasks[service] = asyncio.create_task(self._watch_service_dir(service))

            # 等待消息ID
            if timeout is None:
                msg_id = await self._queues[service].get()
            else:
                try:
                    msg_id = await asyncio.wait_for(self._queues[service].get(), timeout=timeout)
                except asyncio.TimeoutError:
                    return None

            # 读取消息
            return await self._load_message(service, msg_id)

        except Exception:
            return None

    async def receive_stream(self, service: str) -> AsyncIterator[MessageEnvelope]:
        """接收消息流"""
        while self._running:
            envelope = await self.receive(service, timeout=1.0)
            if envelope:
                yield envelope

    async def _load_message(self, service: str, msg_id: str) -> Optional[MessageEnvelope]:
        """从文件加载消息"""
        try:
            msg_path = self._get_message_path(service, msg_id)

            if not msg_path.exists():
                return None

            with open(msg_path, "r", encoding="utf-8") as f:
                content = f.read()

            envelope = MessageEnvelope.from_json(content)

            # 标记为已处理
            processed_path = msg_path.with_suffix(f".json{self._processed_suffix}")
            msg_path.rename(processed_path)

            return envelope

        except Exception:
            return None

    async def _watch_service_dir(self, service: str) -> None:
        """监控服务目录的新消息"""
        service_dir = self._get_service_dir(service)
        known_files: Set[str] = set()

        while self._running:
            try:
                # 扫描新文件
                current_files: Set[str] = set()
                for file_path in service_dir.glob("*.json"):
                    if not file_path.name.endswith(self._processed_suffix):
                        msg_id = file_path.stem
                        current_files.add(msg_id)

                        # 新文件
                        if msg_id not in known_files:
                            if service in self._queues:
                                await self._queues[service].put(msg_id)

                known_files = current_files
                await asyncio.sleep(0.5)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1.0)

    def subscribe(
        self,
        service: str,
        msg_type: str,
        handler: Callable[[MessageEnvelope], None],
    ) -> str:
        """订阅消息"""
        subscription_id = uuid4().hex

        with self._lock:
            if service not in self._subscriptions:
                self._subscriptions[service] = {}
            self._subscriptions[service][subscription_id] = (msg_type, handler)

        return subscription_id

    def unsubscribe(self, service: str, subscription_id: str) -> bool:
        """取消订阅"""
        with self._lock:
            if service in self._subscriptions and subscription_id in self._subscriptions[service]:
                del self._subscriptions[service][subscription_id]
                return True
        return False

    async def close(self) -> None:
        """关闭传输连接"""
        self._running = False

        # 取消监控任务
        for task in self._watcher_tasks.values():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._watcher_tasks.clear()

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._running

    def start(self) -> None:
        """启动传输层"""
        self._running = True

    async def replay(self, service: str, limit: Optional[int] = None) -> List[MessageEnvelope]:
        """
        重放历史消息

        Args:
            service: 服务标识
            limit: 最大重放数量

        Returns:
            历史消息列表
        """
        messages: List[MessageEnvelope] = []
        service_dir = self._get_service_dir(service)

        # 扫描所有消息文件
        msg_files = sorted(service_dir.glob(f"*{self._processed_suffix}"), key=lambda p: p.stat().st_mtime)

        for msg_file in msg_files:
            if limit and len(messages) >= limit:
                break

            try:
                with open(msg_file, "r", encoding="utf-8") as f:
                    content = f.read()
                envelope = MessageEnvelope.from_json(content)
                messages.append(envelope)
            except Exception:
                continue

        return messages

    async def cleanup(self, service: str, older_than_seconds: int = 86400) -> int:
        """
        清理旧消息

        Args:
            service: 服务标识
            older_than_seconds: 消息年龄阈值（秒）

        Returns:
            清理的文件数量
        """
        service_dir = self._get_service_dir(service)
        count = 0
        cutoff_time = time.time() - older_than_seconds

        for msg_file in service_dir.glob(f"*{self._processed_suffix}"):
            try:
                if msg_file.stat().st_mtime < cutoff_time:
                    msg_file.unlink()
                    count += 1
            except Exception:
                continue

        return count

    def get_stats(self, service: str) -> Dict[str, int]:
        """获取服务统计信息"""
        service_dir = self._get_service_dir(service)

        pending = len(list(service_dir.glob("*.json"))) - len(list(service_dir.glob(f"*{self._processed_suffix}")))
        processed = len(list(service_dir.glob(f"*{self._processed_suffix}")))

        return {
            "pending": pending,
            "processed": processed,
            "total": pending + processed,
        }
