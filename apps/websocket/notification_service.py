import json
import logging
import asyncio
import zlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import uuid

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings

from apps.events.models import Event
from apps.tasks.models import Task
from apps.checklists.models import ChecklistInstance

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class NotificationType(Enum):
    """通知类型"""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    SUCCESS = 'success'


class NotificationService:
    """
    通知服务
    负责创建、发送和管理实时通知
    """
    
    def __init__(self):
        self._channel_layer = get_channel_layer()
        self._notification_queue = deque(maxlen=1000)
        self._processing = False
        self._batch_size = 10
        self._batch_timeout = 1.0  # 秒
        
        # 通知聚合配置
        self._aggregation_window = 60  # 聚合窗口(秒)
        self._aggregated_notifications: Dict[str, List[Dict]] = {}
        
        # 优先级队列
        self._priority_queues: Dict[int, deque] = {
            priority.value: deque(maxlen=500)
            for priority in NotificationPriority
        }
        
    async def create_notification(self, user_id: int, title: str, message: str,
                                 notification_type: NotificationType = NotificationType.INFO,
                                 priority: NotificationPriority = NotificationPriority.NORMAL,
                                 data: Optional[Dict] = None) -> Dict:
        """
        创建通知
        
        Args:
            user_id: 用户ID
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型
            priority: 优先级
            data: 附加数据
            
        Returns:
            创建的通知对象
        """
        notification = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'title': title,
            'message': message,
            'type': notification_type.value,
            'priority': priority.value,
            'data': data or {},
            'created_at': datetime.now().isoformat(),
            'read_at': None,
            'read': False
        }
        
        # 添加到优先级队列
        self._priority_queues[priority.value].append(notification)
        
        # 添加到聚合检查
        await self._check_aggregation(notification)
        
        logger.info(f"Created notification for user {user_id}: {title}")
        return notification
    
    async def send_notification(self, notification: Dict) -> bool:
        """
        发送通知到WebSocket
        
        Args:
            notification: 通知对象
            
        Returns:
            是否发送成功
        """
        try:
            # 发送到用户特定的频道
            user_channel = f'user_{notification["user_id"]}'
            
            # 压缩消息（如果消息较大）
            payload = self._prepare_payload(notification)
            
            await self._channel_layer.group_send(
                user_channel,
                {
                    'type': 'notification.send',
                    'notification': payload
                }
            )
            
            logger.info(f"Sent notification to user {notification['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    async def _prepare_payload(self, notification: Dict) -> Dict:
        """准备发送负载，可选压缩"""
        payload = notification.copy()
        
        # 如果数据较大，进行压缩
        if payload.get('data') and len(str(payload.get('data'))) > 4096:
            try:
                data_str = json.dumps(payload['data'])
                compressed = zlib.compress(data_str.encode())
                payload['data'] = f'compressed:{len(compressed)}'
                payload['compressed_data'] = compressed.hex()
            except Exception as e:
                logger.warning(f"Failed to compress notification data: {str(e)}")
        
        return payload
    
    async def _check_aggregation(self, notification: Dict) -> bool:
        """
        检查通知聚合
        
        Args:
            notification: 新通知
            
        Returns:
            是否需要聚合
        """
        # 聚合键：根据用户、类型、标题生成
        aggregation_key = f"{notification['user_id']}_{notification['type']}_{notification['title']}"
        
        if aggregation_key in self._aggregated_notifications:
            window = self._aggregated_notifications[aggregation_key]
            
            # 按时间清理
            now = datetime.now()
            window[:] = [
                n for n in window
                if (now - datetime.fromisoformat(n['created_at'])).total_seconds() < self._aggregation_window
            ]
            
            if len(window) >= 3:  # 达到聚合阈值
                await self._create_aggregated_notification(window)
                return True
            
            window.append(notification)
        else:
            self._aggregated_notifications[aggregation_key] = [notification]
            
        return False
    
    async def _create_aggregated_notification(self, notifications: List[Dict]) -> Dict:
        """
        创建聚合通知
        
        Args:
            notifications: 要聚合的通知列表
            
        Returns:
            聚合后的通知
        """
        if not notifications:
            return {}
            
        first_notif = notifications[0]
        aggregated = {
            'id': str(uuid.uuid4()),
            'user_id': first_notif['user_id'],
            'title': f"{first_notif['title']} ({len(notifications)} 条)",
            'message': f"您有 {len(notifications)} 条新通知",
            'type': first_notif['type'],
            'priority': max(n['priority'] for n in notifications),
            'data': {
                'count': len(notifications),
                'notifications': notifications[-5:]  # 只保留最近5条
            },
            'created_at': datetime.now().isoformat(),
            'read_at': None,
            'read': False,
            'aggregated': True
        }
        
        # 清空聚合列表
        aggregation_key = f"{first_notif['user_id']}_{first_notif['type']}_{first_notif['title']}"
        self._aggregated_notifications[aggregation_key] = []
        
        await self.send_notification(aggregated)
        return aggregated
    
    def mark_as_read(self, notification_id: str, user_id: int) -> bool:
        """
        标记通知为已读
        
        Args:
            notification_id: 通知ID
            user_id: 用户ID
            
        Returns:
            是否标记成功
        """
        # 这里可以更新数据库中的已读状态
        # 当前实现仅在内存中
        return True
    
    async def broadcast_notification(self, title: str, message: str,
                                     notification_type: NotificationType = NotificationType.INFO,
                                     priority: NotificationPriority = NotificationPriority.NORMAL) -> bool:
        """
        广播通知到所有连接用户
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型
            priority: 优先级
            
        Returns:
            是否发送成功
        """
        try:
            payload = {
                'type': 'notification.broadcast',
                'notification': {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'message': message,
                    'type': notification_type.value,
                    'priority': priority.value,
                    'created_at': datetime.now().isoformat()
                }
            }
            
            await self._channel_layer.group_send(
                'global_notifications',
                payload
            )
            
            logger.info(f"Broadcasted notification: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast notification: {str(e)}")
            return False
    
    async def send_event_notification(self, event_id: int, action: str,
                                     user_id: Optional[int] = None,
                                     data: Optional[Dict] = None) -> bool:
        """
        发送活动相关通知
        
        Args:
            event_id: 活动ID
            action: 动作类型
            user_id: 用户ID（None表示广播给所有相关用户）
            data: 附加数据
            
        Returns:
            是否发送成功
        """
        try:
            # 获取活动信息
            event = await self._get_event_info(event_id)
            if not event:
                logger.warning(f"Event {event_id} not found")
                return False
            
            title = f"活动更新: {event['title']}"
            message = self._get_event_message(action, event)
            priority = self._get_event_priority(action)
            
            if user_id:
                notification = await self.create_notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    priority=priority,
                    data={'event_id': event_id, 'action': action, **(data or {})}
                )
                return await self.send_notification(notification)
            else:
                # 广播给相关用户
                # 这里需要获取活动相关用户列表
                return await self.broadcast_notification(title, message, priority=priority)
            
        except Exception as e:
            logger.error(f"Failed to send event notification: {str(e)}")
            return False
    
    async def send_task_notification(self, task_id: int, action: str, user_id: int,
                                   data: Optional[Dict] = None) -> bool:
        """
        发送任务相关通知
        
        Args:
            task_id: 任务ID
            action: 动作类型
            user_id: 用户ID
            data: 附加数据
            
        Returns:
            是否发送成功
        """
        try:
            task = await self._get_task_info(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found")
                return False
            
            title = f"任务更新: {task['title']}"
            message = self._get_task_message(action, task)
            priority = self._get_task_priority(action)
            
            notification = await self.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                priority=priority,
                data={'task_id': task_id, 'action': action, **(data or {})}
            )
            return await self.send_notification(notification)
            
        except Exception as e:
            logger.error(f"Failed to send task notification: {str(e)}")
            return False
    
    async def _get_event_info(self, event_id: int) -> Optional[Dict]:
        """获取活动信息"""
        try:
            event = await Event.objects.aget(id=event_id)
            return {
                'id': event.id,
                'title': event.title,
                'status': event.status
            }
        except Event.DoesNotExist:
            return None
    
    async def _get_task_info(self, task_id: int) -> Optional[Dict]:
        """获取任务信息"""
        try:
            task = await Task.objects.aget(id=task_id)
            return {
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'assignee_id': task.assignee_id
            }
        except Task.DoesNotExist:
            return None
    
    def _get_event_message(self, action: str, event: Dict) -> str:
        """生成活动通知消息"""
        messages = {
            'created': f"活动 '{event['title']}' 已创建",
            'updated': f"活动 '{event['title']}' 已更新",
            'deleted': f"活动 '{event['title']}' 已删除",
            'completed': f"活动 '{event['title']}' 已完成",
            'status_changed': f"活动 '{event['title']}' 状态已变更"
        }
        return messages.get(action, f"活动 '{event['title']}' 有更新")
    
    def _get_task_message(self, action: str, task: Dict) -> str:
        """生成任务通知消息"""
        messages = {
            'created': f"任务 '{task['title']}' 已创建",
            'updated': f"任务 '{task['title']}' 已更新",
            'deleted': f"任务 '{task['title']}' 已删除",
            'completed': f"任务 '{task['title']}' 已完成",
            'assigned': f"任务 '{task['title']}' 已分配给您",
            'status_changed': f"任务 '{task['title']}' 状态已变更"
        }
        return messages.get(action, f"任务 '{task['title']}' 有更新")
    
    def _get_event_priority(self, action: str) -> NotificationPriority:
        """获取活动通知优先级"""
        priorities = {
            'deleted': NotificationPriority.HIGH,
            'completed': NotificationPriority.NORMAL,
            'status_changed': NotificationPriority.NORMAL,
        }
        return priorities.get(action, NotificationPriority.NORMAL)
    
    def _get_task_priority(self, action: str) -> NotificationPriority:
        """获取任务通知优先级"""
        priorities = {
            'assigned': NotificationPriority.NORMAL,
            'deleted': NotificationPriority.HIGH,
            'completed': NotificationPriority.NORMAL,
            'status_changed': NotificationPriority.NORMAL
        }
        return priorities.get(action, NotificationPriority.NORMAL)
    
    async def process_notifications(self) -> int:
        """
        处理通知队列（批量处理）
        
        Returns:
            处理的通知数量
        """
        processed = 0
        notifications = []
        
        # 按优先级收集通知
        for priority in sorted(NotificationPriority.__members__.values(), 
                              key=lambda x: x.value, reverse=True):
            if priority.value in self._priority_queues:
                while (len(notifications) < self._batch_size and 
                       self._priority_queues[priority.value]):
                    notifications.append(
                        self._priority_queues[priority.value].popleft()
                    )
        
        # 批量发送
        for notification in notifications:
            if await self.send_notification(notification):
                processed += 1
        
        return processed
    
    def get_queue_stats(self) -> Dict:
        """获取队列统计信息"""
        return {
            'total_queued': sum(
                len(queue) for queue in self._priority_queues.values()
            ),
            'by_priority': {
                name: len(self._priority_queues[priority.value])
                for name, priority in NotificationPriority.__members__.items()
            },
            'aggregated_keys': len(self._aggregated_notifications)
        }