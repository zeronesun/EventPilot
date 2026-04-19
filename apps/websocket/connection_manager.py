import json
import logging
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket连接管理器
    负责管理所有WebSocket连接的生命周期
    """
    
    def __init__(self):
        # 连接存储: {connection_id: connection_data}
        self._active_connections: Dict[str, Dict[str, Any]] = {}
        
        # 用户连接映射: {user_id: Set[connection_id]}
        self._user_connections: Dict[int, Set[str]] = defaultdict(set)
        
        # 主题订阅映射: {topic: Set[connection_id]}
        self._topic_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # 设备连接映射: {(user_id, device_id): connection_id}
        self._device_connections: Dict[tuple, str] = {}
        
        # 连接统计
        self._connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0
        }
        
        # 心跳检测
        self._heartbeat_tracker: Dict[str, datetime] = {}
        self._heartbeat_interval = 30  # 秒
        self._heartbeat_timeout = 90  # 秒
        
        # 锁
        self._lock = asyncio.Lock()
        
    async def connect(self, connection_id: str, user_id: Optional[int] = None,
                     device_id: Optional[str] = None, topics: Optional[Set[str]] = None) -> bool:
        """
        建立新连接
        
        Args:
            connection_id: 连接唯一标识
            user_id: 用户ID
            device_id: 设备ID
            topics: 订阅的主题列表
            
        Returns:
            是否连接成功
        """
        async with self._lock:
            now = datetime.now()
            
            # 检查连接是否存在
            if connection_id in self._active_connections:
                logger.warning(f"Connection {connection_id} already exists")
                return False
                
            # 存储连接信息
            connection_data = {
                'connection_id': connection_id,
                'user_id': user_id,
                'device_id': device_id,
                'topics': topics or set(),
                'connected_at': now,
                'last_active': now,
                'status': 'connected'
            }
            
            self._active_connections[connection_id] = connection_data
            self._heartbeat_tracker[connection_id] = now
            
            # 更新用户连接映射
            if user_id:
                self._user_connections[user_id].add(connection_id)
                
                # 更新设备连接映射
                if device_id:
                    device_key = (user_id, device_id)
                    # 关闭同一设备的旧连接
                    old_connection_id = self._device_connections.get(device_key)
                    if old_connection_id and old_connection_id != connection_id:
                        await self.disconnect(old_connection_id, reason='new_connection')
                    
                    self._device_connections[device_key] = connection_id
            
            # 更新主题订阅
            if topics:
                for topic in topics:
                    self._topic_subscriptions[topic].add(connection_id)
            
            # 更新统计
            self._connection_stats['total_connections'] += 1
            self._connection_stats['active_connections'] += 1
            
            logger.info(f"Connected: {connection_id} (user_id: {user_id}, device: {device_id})")
            return True
    
    async def disconnect(self, connection_id: str, reason: str = 'normal'):
        """
        断开连接
        
        Args:
            connection_id: 连接标识
            reason: 断开原因
        """
        async with self._lock:
            if connection_id not in self._active_connections:
                logger.warning(f"Unknown connection {connection_id} disconnect attempt")
                return
                
            connection_data = self._active_connections[connection_id]
            user_id = connection_data.get('user_id')
            device_id = connection_data.get('device_id')
            
            # 从用户连接映射中移除
            if user_id:
                self._user_connections[user_id].discard(connection_id)
                
                # 从设备连接映射中移除
                if device_id:
                    device_key = (user_id, device_id)
                    self._device_connections.pop(device_key, None)
            
            # 从主题订阅中移除
            for topic in list(self._topic_subscriptions.keys()):
                self._topic_subscriptions[topic].discard(connection_id)
                # 清理空主题
                if not self._topic_subscriptions[topic]:
                    del self._topic_subscriptions[topic]
            
            # 从心跳追踪中移除
            self._heartbeat_tracker.pop(connection_id, None)
            
            # 更新连接状态
            connection_data['disconnected_at'] = datetime.now()
            connection_data['disconnect_reason'] = reason
            connection_data['status'] = 'disconnected'
            
            # 更新统计
            self._connection_stats['active_connections'] -= 1
            
            logger.info(f"Disconnected: {connection_id} (reason: {reason})")
    
    async def send_message(self, connection_id: str, message: dict) -> bool:
        """
        发送消息到指定连接
        
        Args:
            connection_id: 连接标识
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        if connection_id not in self._active_connections:
            logger.warning(f"Cannot send to unknown connection: {connection_id}")
            return False
            
        connection_data = self._active_connections[connection_id]
        connection_data['last_active'] = datetime.now()
        
        # 实际发送逻辑在Consumer中实现
        self._connection_stats['messages_sent'] += 1
        
        return True
    
    async def send_to_user(self, user_id: int, message: dict, exclude_connection: Optional[str] = None) -> int:
        """
        发送消息到用户的所有连接
        
        Args:
            user_id: 用户ID
            message: 消息内容
            exclude_connection: 排除的连接
            
        Returns:
            实际发送的连接数
        """
        if user_id not in self._user_connections:
            return 0
            
        connection_ids = self._user_connections[user_id].copy()
        sent_count = 0
        
        for connection_id in connection_ids:
            if exclude_connection and connection_id == exclude_connection:
                continue
                
            if await self.send_message(connection_id, message):
                sent_count += 1
                
        return sent_count
    
    async def send_to_topic(self, topic: str, message: dict) -> int:
        """
        发送消息到主题订阅者
        
        Args:
            topic: 主题名称
            message: 消息内容
            
        Returns:
            实际发送的连接数
        """
        if topic not in self._topic_subscriptions:
            return 0
            
        connection_ids = self._topic_subscriptions[topic].copy()
        sent_count = 0
        
        for connection_id in connection_ids:
            if await self.send_message(connection_id, message):
                sent_count += 1
                
        return sent_count
    
    async def broadcast(self, message: dict, exclude_connections: Optional[Set[str]] = None) -> int:
        """
        广播消息到所有连接
        
        Args:
            message: 消息内容
            exclude_connections: 排除的连接集合
            
        Returns:
            实际发送的连接数
        """
        sent_count = 0
        exclude = exclude_connections or set()
        
        for connection_id in list(self._active_connections.keys()):
            if connection_id not in exclude:
                if await self.send_message(connection_id, message):
                    sent_count += 1
                    
        return sent_count
    
    async def subscribe(self, connection_id: str, topics: Set[str]) -> bool:
        """
        订阅主题
        
        Args:
            connection_id: 连接标识
            topics: 主题列表
            
        Returns:
            是否订阅成功
        """
        async with self._lock:
            if connection_id not in self._active_connections:
                return False
                
            connection_data = self._active_connections[connection_id]
            connection_data['topics'].update(topics)
            
            for topic in topics:
                self._topic_subscriptions[topic].add(connection_id)
                
            logger.info(f"Subscribed {connection_id} to topics: {topics}")
            return True
    
    async def unsubscribe(self, connection_id: str, topics: Set[str]) -> bool:
        """
        取消订阅主题
        
        Args:
            connection_id: 连接标识
            topics: 主题列表
            
        Returns:
            是否取消成功
        """
        async with self._lock:
            if connection_id not in self._active_connections:
                return False
                
            connection_data = self._active_connections[connection_id]
            connection_data['topics'].difference_update(topics)
            
            for topic in topics:
                self._topic_subscriptions[topic].discard(connection_id)
                if not self._topic_subscriptions[topic]:
                    del self._topic_subscriptions[topic]
                    
            logger.info(f"Unsubscribed {connection_id} from topics: {topics}")
            return True
    
    async def update_heartbeat(self, connection_id: str) -> bool:
        """
        更新连接心跳
        
        Args:
            connection_id: 连接标识
            
        Returns:
            是否更新成功
        """
        if connection_id in self._heartbeat_tracker:
            self._heartbeat_tracker[connection_id] = datetime.now()
            return True
        return False
    
    async def check_timeouts(self) -> int:
        """
        检查并断开超时连接
        
        Returns:
            断开的连接数
        """
        now = datetime.now()
        timeout_connections = []
        
        for connection_id, last_heartbeat in list(self._heartbeat_tracker.items()):
            if (now - last_heartbeat).total_seconds() > self._heartbeat_timeout:
                timeout_connections.append(connection_id)
        
        timeout_count = len(timeout_connections)
        for connection_id in timeout_connections:
            await self.disconnect(connection_id, reason='heartbeat_timeout')
            
        if timeout_count > 0:
            logger.warning(f"Disconnected {timeout_count} connections due to timeout")
            
        return timeout_count
    
    def get_connection_info(self, connection_id: str) -> Optional[dict]:
        """获取连接详情"""
        return self._active_connections.get(connection_id)
    
    def get_user_connections(self, user_id: int) -> Set[str]:
        """获取用户的所有连接"""
        return self._user_connections.get(user_id, set()).copy()
    
    def get_device_connection(self, user_id: int, device_id: str) -> Optional[str]:
        """获取设备连接"""
        return self._device_connections.get((user_id, device_id))
    
    def get_stats(self) -> dict:
        """获取连接统计信息"""
        return {
            **self._connection_stats,
            'unique_users': len(self._user_connections),
            'active_topics': len(self._topic_subscriptions),
            'current_time': datetime.now().isoformat()
        }