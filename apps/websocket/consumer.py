import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Set, Any, List
from enum import Enum
import uuid

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from apps.users.models import User
from apps.events.models import Event
from apps.tasks.models import Task
from apps.websocket.connection_manager import ConnectionManager
from apps.websocket.notification_service import NotificationService, NotificationType, NotificationPriority
from apps.websocket.status_manager import StatusManager, UserStatus
from apps.websocket.message_validator import WebSocketMessageValidator

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket消息类型"""
    # 连接管理
    HEARTBEAT = 'heartbeat'
    PING = 'ping'
    PONG = 'pong'
    
    # 认证相关
    AUTHENTICATE = 'authenticate'
    
    # 主题订阅
    SUBSCRIBE = 'subscribe'
    UNSUBSCRIBE = 'unsubscribe'
    
    # 实时通知
    NOTIFICATION = 'notification'
    NOTIFICATION_READ = 'notification_read'
    
    # 活动相关
    EVENT_UPDATE = 'event_update'
    EVENT_STATUS_CHANGE = 'event_status_change'
    
    # 任务相关
    TASK_UPDATE = 'task_update'
    TASK_ASSIGNMENT = 'task_assignment'
    TASK_STATUS_CHANGE = 'task_status_change'
    
    # 在线状态
    PRESENCE = 'presence'
    USER_STATUS = 'user_status'
    
    # 协作
    COLLABORATION = 'collaboration'
    EDIT_LOCK = 'edit_lock'
    
    # 错误
    ERROR = 'error'


class EventPilotConsumer(AsyncJsonWebsocketConsumer):
    """
    EventPilot WebSocket Consumer
    处理所有WebSocket连接和消息
    """
    
    # 全局管理器实例 (在类级别创建单例)
    _connection_manager: Optional[ConnectionManager] = None
    _notification_service: Optional[NotificationService] = None
    _status_manager: Optional[StatusManager] = None
    
    @classmethod
    def get_connection_manager(cls) -> ConnectionManager:
        if cls._connection_manager is None:
            cls._connection_manager = ConnectionManager()
        return cls._connection_manager
    
    @classmethod
    def get_notification_service(cls) -> NotificationService:
        if cls._notification_service is None:
            cls._notification_service = NotificationService()
        return cls._notification_service
    
    @classmethod
    def get_status_manager(cls) -> StatusManager:
        if cls._status_manager is None:
            cls._status_manager = StatusManager()
        return cls._status_manager
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_id: Optional[str] = None
        self.user: Any = AnonymousUser()
        self.user_id: Optional[int] = None
        self.device_id: Optional[str] = None
        self.subscribed_topics: Set[str] = set()
        
        # 心跳检测
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30  # 秒
        
        # 离线消息队列
        self._offline_queue: List[Dict] = []
        self._max_offline_messages = 100
        
    async def connect(self):
        """处理WebSocket连接"""
        self.connection_id = str(uuid.uuid4())
        self.device_id = self._get_device_id()
        
        # 检查用户认证
        if isinstance(self.scope['user'], AnonymousUser):
            logger.warning(f"Unauthorized connection attempt: {self.connection_id}")
            await self.send_error(
                code='UNAUTHORIZED',
                message='Authentication required'
            )
            await self.close(code=4001)
            return
        
        self.user = self.scope['user']
        self.user_id = self.user.id
        
        # 获取管理器实例
        connection_manager = self.get_connection_manager()
        status_manager = self.get_status_manager()
        
        # 初始主题订阅
        initial_topics = {
            f'user_{self.user_id}',
            f'user_{self.user_id}_presence',
            'global_notifications'
        }
        if hasattr(self, 'event_id'):
            initial_topics.add(f'event_{self.event_id}')
        
        # 建立连接
        await connection_manager.connect(
            self.connection_id,
            user_id=self.user_id,
            device_id=self.device_id,
            topics=initial_topics
        )
        
        # 更新在线状态
        await status_manager.get_presence_service().update_user_status(
            self.user_id, UserStatus.ONLINE, self.device_id
        )
        
        # 加入用户组
        await self.channel_layer.group_add(
            f'user_{self.user_id}',
            self.channel_name
        )
        
        # 加入presence组
        await self.channel_layer.group_add(
            f'user_{self.user_id}_presence',
            self.channel_name
        )
        
        # 加入全局通知组
        await self.channel_layer.group_add(
            'global_notifications',
            self.channel_name
        )
        
        self.subscribed_topics = initial_topics
        
        # 启动心跳检测
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # 发送连接成功消息
        await self.send_json({
            'type': MessageType.PRESENCE.value,
            'event': 'connected',
            'connection_id': self.connection_id,
            'user_id': self.user_id,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"WebSocket connected: {self.connection_id} for user {self.user_id}")
        await self.accept()
    
    async def disconnect(self, close_code):
        """处理WebSocket断开"""
        connection_manager = self.get_connection_manager()
        status_manager = self.get_status_manager()
        
        # 停止心跳
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 断开连接
        await connection_manager.disconnect(self.connection_id)
        
        # 更新在线状态
        await status_manager.get_presence_service().user_disconnected(
            self.user_id, self.device_id
        )
        
        # 离开用户组
        if self.user_id:
            await self.channel_layer.group_discard(
                f'user_{self.user_id}',
                self.channel_name
            )
            await self.channel_layer.group_discard(
                f'user_{self.user_id}_presence',
                self.channel_name
            )
        
        # 离开全局通知组
        await self.channel_layer.group_discard(
            'global_notifications',
            self.channel_name
        )
        
        # 离开主题组
        for topic in self.subscribed_topics:
            await self.channel_layer.group_discard(
                topic,
                self.channel_name
            )
        
        logger.info(f"WebSocket disconnected: {self.connection_id} (code: {close_code})")
    
    async def receive_json(self, content: dict):
        """处理接收到的JSON消息"""
        try:
            message_type = content.get('type')
            
            if not message_type:
                await self.send_error(code='INVALID_MESSAGE', message='Message type required')
                return
            
            # 更新最后活跃时间
            connection_manager = self.get_connection_manager()
            await connection_manager.update_heartbeat(self.connection_id)
            
            # 消息验证（安全检查）
            if message_type not in ['ping', 'pong']:
                validator = WebSocketMessageValidator()
                if not validator.validate_message(content, self.user_id):
                    await self.send_error(
                        code='MESSAGE_VALIDATION_FAILED',
                        message='Message validation failed'
                    )
                    logger.warning(f"Message validation failed: {message_type} from {self.connection_id}")
                    return
            
            # 分发消息处理
            await self._handle_message(message_type, content)
            
            # 记录消息
            logger.debug(f"Received message: {message_type} from {self.connection_id}")
            
        except json.JSONDecodeError:
            await self.send_error(code='JSON_DECODE_ERROR', message='Invalid JSON')
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_error(code='PROCESSING_ERROR', message=str(e))
    
    async def _handle_message(self, message_type: str, content: dict):
        """分发消息处理"""
        handlers = {
            MessageType.HEARTBEAT.value: self._handle_heartbeat,
            MessageType.PING.value: self._handle_ping,
            MessageType.PONG.value: self._handle_pong,
            MessageType.SUBSCRIBE.value: self._handle_subscribe,
            MessageType.UNSUBSCRIBE.value: self._handle_unsubscribe,
            MessageType.NOTIFICATION_READ.value: self._handle_notification_read,
            MessageType.PRESENCE.value: self._handle_presence,
            MessageType.COLLABORATION.value: self._handle_collaboration,
        }
        
        handler = handlers.get(message_type)
        if handler:
            await handler(content)
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await self.send_error(
                code='UNKNOWN_MESSAGE_TYPE',
                message=f'Unknown message type: {message_type}'
            )
    
    async def _handle_heartbeat(self, content: dict):
        """处理心跳消息"""
        await self.send_json({
            'type': MessageType.HEARTBEAT.value,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _handle_ping(self, content: dict):
        """处理ping消息"""
        await self.send_json({
            'type': MessageType.PONG.value,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _handle_pong(self, content: dict):
        """处理pong消息（心跳响应）"""
        pass
    
    async def _handle_subscribe(self, content: dict):
        """处理订阅请求"""
        topics = content.get('topics', [])
        if not isinstance(topics, list):
            await self.send_error(code='INVALID_TOPICS', message='Topics must be a list')
            return
        
        connection_manager = self.get_connection_manager()
        
        for topic in topics:
            if not topic in self.subscribed_topics:
                await self.channel_layer.group_add(topic, self.channel_name)
                self.subscribed_topics.add(topic)
        
        await connection_manager.subscribe(self.connection_id, set(topics))
        
        await self.send_json({
            'type': MessageType.SUBSCRIBE.value,
            'status': 'success',
            'topics': topics
        })
    
    async def _handle_unsubscribe(self, content: dict):
        """处理取消订阅请求"""
        topics = content.get('topics', [])
        if not isinstance(topics, list):
            await self.send_error(code='INVALID_TOPICS', message='Topics must be a list')
            return
        
        connection_manager = self.get_connection_manager()
        
        for topic in topics:
            if topic in self.subscribed_topics:
                await self.channel_layer.group_discard(topic, self.channel_name)
                self.subscribed_topics.discard(topic)
        
        await connection_manager.unsubscribe(self.connection_id, set(topics))
        
        await self.send_json({
            'type': MessageType.UNSUBSCRIBE.value,
            'status': 'success',
            'topics': topics
        })
    
    async def _handle_notification_read(self, content: dict):
        """处理通知已读"""
        notification_id = content.get('notification_id')
        if not notification_id:
            await self.send_error(code='INVALID_NOTIFICATION', message='Notification ID required')
            return
        
        notification_service = self.get_notification_service()
        notification_service.mark_as_read(notification_id, self.user_id)
        
        await self.send_json({
            'type': MessageType.NOTIFICATION_READ.value,
            'status': 'success',
            'notification_id': notification_id
        })
    
    async def _handle_presence(self, content: dict):
        """处理在线状态更新"""
        action = content.get('action')
        
        status_manager = self.get_status_manager()
        
        if action == 'update_status':
            status_str = content.get('status')
            try:
                status = UserStatus(status_str)
                await status_manager.get_presence_service().update_user_status(
                    self.user_id, status, self.device_id
                )
            except ValueError:
                await self.send_error(code='INVALID_STATUS', message=f'Invalid status: {status_str}')
        elif action == 'update_last_active':
            await status_manager.get_presence_service().update_last_active(self.user_id, self.device_id)
        
        await self.send_json({
            'type': MessageType.PRESENCE.value,
            'action': action,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _handle_collaboration(self, content: dict):
        """处理协作消息"""
        action = content.get('action')
        
        status_manager = self.get_status_manager()
        
        if action == 'enter_event':
            event_id = content.get('event_id')
            if event_id:
                await status_manager.update_event_state(event_id, self.user_id, 'enter')
        elif action == 'exit_event':
            event_id = content.get('event_id')
            if event_id:
                await status_manager.update_event_state(event_id, self.user_id, 'exit')
        elif action == 'view_task':
            task_id = content.get('task_id')
            if task_id:
                await status_manager.update_task_state(task_id, self.user_id, 'view')
        elif action == 'leave_task':
            task_id = content.get('task_id')
            if task_id:
                await status_manager.update_task_state(task_id, self.user_id, 'leave')
        
        # 广播协作消息给其他相关用户
        await self._broadcast_collaboration(content)
    
    async def _broadcast_collaboration(self, content: dict):
        """广播协作消息"""
        event_id = content.get('event_id')
        task_id = content.get('task_id')
        
        if event_id:
            await self.channel_layer.group_send(
                f'event_{event_id}',
                {
                    'type': 'collaboration.event',
                    'user_id': self.user_id,
                    'content': content
                }
            )
        
        if task_id:
            await self.channel_layer.group_send(
                f'task_{task_id}',
                {
                    'type': 'collaboration.task',
                    'user_id': self.user_id,
                    'content': content
                }
            )
    
    async def _heartbeat_loop(self):
        """心跳检测循环"""
        try:
            while True:
                await asyncio.sleep(self._heartbeat_interval)
                await self.send_json({
                    'type': MessageType.PING.value,
                    'timestamp': datetime.now().isoformat()
                })
        except asyncio.CancelledError:
            pass
    
    def _get_device_id(self) -> Optional[str]:
        """获取设备ID"""
        # 从查询参数或头部获取设备ID
        query_string = self.scope.get('query_string', b'').decode()
        if 'device_id=' in query_string:
            try:
                device_id = query_string.split('device_id=')[1].split('&')[0]
                return device_id
            except (IndexError, ValueError):
                pass
        
        # 尝试从headers获取
        headers = dict(self.scope.get('headers', []))
        user_agent = headers.get(b'user-agent', b'').decode()
        
        # 简单的用户代理解析
        if user_agent:
            import hashlib
            device_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
            return f"device_{device_hash}"
        
        return None
    
    async def send_error(self, code: str, message: str):
        """发送错误消息"""
        await self.send_json({
            'type': MessageType.ERROR.value,
            'code': code,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    # Channel handlers
    async def notification_send(self, event: dict):
        """处理通知发送"""
        notification = event.get('notification', {})
        await self.send_json({
            'type': MessageType.NOTIFICATION.value,
            'notification': notification
        })
    
    async def notification_broadcast(self, event: dict):
        """处理广播通知"""
        notification = event.get('notification', {})
        await self.send_json({
            'type': MessageType.NOTIFICATION.value,
            'notification': notification,
            'broadcast': True
        })
    
    async def presence_status_update(self, event: dict):
        """处理 Presence 状态更新"""
        await self.send_json({
            'type': MessageType.PRESENCE.value,
            **event
        })
    
    async def presence_user_status(self, event: dict):
        """处理用户状态更新"""
        await self.send_json({
            'type': MessageType.USER_STATUS.value,
            **event
        })
    
    async def collaboration_event(self, event: dict):
        """处理活动协作消息"""
        await self.send_json({
            'type': MessageType.COLLABORATION.value,
            'event': event.get('content', {})
        })
    
    async def collaboration_task(self, event: dict):
        """处理任务协作消息"""
        await self.send_json({
            'type': MessageType.COLLABORATION.value,
            'task': event.get('content', {})
        })