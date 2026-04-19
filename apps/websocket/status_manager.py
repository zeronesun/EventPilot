import json
import logging
import asyncio
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from apps.users.models import User

logger = logging.getLogger(__name__)


class UserStatus(Enum):
    """用户状态"""
    OFFLINE = 'offline'
    ONLINE = 'online'
    AWAY = 'away'
    BUSY = 'busy'
    DO_NOT_DISTURB = 'do_not_disturb'


class PresenceService:
    """
    在线状态服务
    管理用户在线状态和最后活跃时间
    """
    
    def __init__(self):
        self._channel_layer = get_channel_layer()
        self._user_status: Dict[int, Dict] = {}
        self._user_presence: Dict[int, Dict[str, datetime]] = {}  # {user_id: {device_id: last_seen}}
        self._support_concurrent_devices = getattr(settings, 'WEBSOCKET_CONCURRENT_DEVICES', 3)
        
    async def update_user_status(self, user_id: int, status: UserStatus,
                                 device_id: Optional[str] = None) -> bool:
        """
        更新用户状态
        
        Args:
            user_id: 用户ID
            status: 用户状态
            device_id: 设备ID
            
        Returns:
            是否更新成功
        """
        try:
            now = datetime.now()
            
            if user_id not in self._user_status:
                self._user_status[user_id] = {
                    'user_id': user_id,
                    'status': status.value,
                    'since': now,
                    'devices': {},
                    'last_active': now
                }
                # 用户加入 Presence 组
                await self._add_to_presence_group(user_id)
            else:
                user_data = self._user_status[user_id]
                user_data['status'] = status.value
                user_data['last_active'] = now
                
            # 更新设备活动时间
            if device_id:
                if user_id not in self._user_presence:
                    self._user_presence[user_id] = {}
                
                self._user_presence[user_id][device_id] = now
                self._user_status[user_id]['devices'][device_id] = now
                
                # 清理过期设备记录
                self._cleanup_inactive_devices(user_id)
            
            # 广播状态更新
            await self._broadcast_status_update(user_id, status)
            
            logger.info(f"Updated user {user_id} status to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user status: {str(e)}")
            return False
    
    async def _add_to_presence_group(self, user_id: int):
        """添加用户到Presence组"""
        try:
            await self._channel_layer.group_add(
                f'user_{user_id}_presence',
                f'user_{user_id}_presence'
            )
        except Exception as e:
            logger.warning(f"Failed to add user to presence group: {str(e)}")
    
    async def _remove_from_presence_group(self, user_id: int):
        """从Presence组移除用户"""
        try:
            await self._channel_layer.group_discard(
                f'user_{user_id}_presence',
                f'user_{user_id}_presence'
            )
        except Exception as e:
            logger.warning(f"Failed to remove user from presence group: {str(e)}")
    
    async def _broadcast_status_update(self, user_id: int, status: UserStatus):
        """广播状态更新"""
        user_data = self._user_status.get(user_id, {})
        
        # 发送到用户的设备
        await self._channel_layer.group_send(
            f'user_{user_id}_presence',
            {
                'type': 'presence.status_update',
                'user_id': user_id,
                'status': status.value,
                'timestamp': datetime.now().isoformat(),
                'devices': user_data.get('devices', {})
            }
        )
        
        # 发送到关注此用户的其他用户
        # 这里可以实现权限控制
        await self._send_to_watchers(user_id, {
            'type': 'presence.user_status',
            'user_id': user_id,
            'status': status.value,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _send_to_watchers(self, user_id: int, message: dict):
        """发送给关注此用户的其他用户"""
        # TODO: 实现关注/权限系统
        pass
    
    def get_user_status(self, user_id: int) -> Optional[Dict]:
        """
        获取用户状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户状态信息
        """
        return self._user_status.get(user_id)
    
    def is_user_online(self, user_id: int, timeout: int = 300) -> bool:
        """
        检查用户是否在线
        
        Args:
            user_id: 用户ID
            timeout: 超时时间(秒)
            
        Returns:
            是否在线
        """
        user_data = self._user_status.get(user_id)
        if not user_data:
            return False
            
        last_active = user_data.get('last_active')
        if not last_active:
            return False
            
        return (datetime.now() - last_active).total_seconds() < timeout
    
    def get_online_users(self, timeout: int = 300) -> Set[int]:
        """
        获取在线用户列表
        
        Args:
            timeout: 超时时间(秒)
            
        Returns:
            在线用户ID集合
        """
        now = datetime.now()
        online_users = set()
        
        for user_id, user_data in self._user_status.items():
            last_active = user_data.get('last_active')
            if last_active and (now - last_active).total_seconds() < timeout:
                online_users.add(user_id)
                
        return online_users
    
    async def user_disconnected(self, user_id: int, device_id: Optional[str] = None):
        """
        处理用户断开连接
        
        Args:
            user_id: 用户ID
            device_id: 设备ID
        """
        try:
            # 更新设备状态
            if device_id and user_id in self._user_presence:
                self._user_presence[user_id].pop(device_id, None)
            
            # 检查是否还有其他设备在线
            if user_id in self._user_presence:
                if not self._user_presence[user_id]:
                    # 所有设备都已断开，更新为离线
                    await self.update_user_status(user_id, UserStatus.OFFLINE)
                else:
                    # 还有其他设备在线，保持当前状态
                    pass
            else:
                # 没有设备记录，标记为离线
                await self.update_user_status(user_id, UserStatus.OFFLINE)
                
        except Exception as e:
            logger.error(f"Failed to handle user disconnect: {str(e)}")
    
    def _cleanup_inactive_devices(self, user_id: int):
        """清理不活跃的设备"""
        if user_id not in self._user_presence:
            return
            
        now = datetime.now()
        timeout = timedelta(hours=1)  # 1小时不活跃
        
        inactive_devices = []
        for device_id, last_seen in self._user_presence[user_id].items():
            if now - last_seen > timeout:
                inactive_devices.append(device_id)
        
        for device_id in inactive_devices:
            del self._user_presence[user_id][device_id]
            
            if user_id in self._user_status and device_id in self._user_status[user_id].get('devices', {}):
                del self._user_status[user_id]['devices'][device_id]
    
    async def get_status_for_watchers(self, user_id: int) -> Dict:
        """
        获取观察者可见的状态信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            状态信息
        """
        user_data = self._user_status.get(user_id)
        if not user_data:
            return {
                'user_id': user_id,
                'status': UserStatus.OFFLINE.value,
                'online': False
            }
        
        return {
            'user_id': user_id,
            'status': user_data.get('status', UserStatus.OFFLINE.value),
            'online': user_data.get('status') != UserStatus.OFFLINE.value,
            'last_active': user_data.get('last_active').isoformat() if user_data.get('last_active') else None,
            'since': user_data.get('since').isoformat() if user_data.get('since') else None
        }
    
    async def update_last_active(self, user_id: int, device_id: Optional[str] = None):
        """
        更新用户最后活跃时间
        
        Args:
            user_id: 用户ID
            device_id: 设备ID
        """
        now = datetime.now()
        
        if user_id in self._user_status:
            self._user_status[user_id]['last_active'] = now
            
        if device_id and user_id in self._user_presence:
            self._user_presence[user_id][device_id] = now
            if user_id in self._user_status:
                self._user_status[user_id]['devices'][device_id] = now


class StatusManager:
    """
    状态管理器
    综合管理各种实时状态（用户状态、活动状态、任务状态等）
    """
    
    def __init__(self):
        self._presence_service = PresenceService()
        self._event_states: Dict[int, Dict] = {}
        self._task_states: Dict[int, Dict] = {}
        self._state_subscribers: Dict[str, Set[int]] = defaultdict(set)
        
    def get_presence_service(self) -> PresenceService:
        """获取在线状态服务"""
        return self._presence_service
    
    async def update_event_state(self, event_id: int, user_id: int,
                                 action: str, **kwargs) -> Dict:
        """
        更新活动状态
        
        Args:
            event_id: 活动ID
            user_id: 用户ID
            action: 动作
            **kwargs: 状态数据
            
        Returns:
            更新后的状态
        """
        if event_id not in self._event_states:
            self._event_states[event_id] = {
                'event_id': event_id,
                'status': 'active',
                'active_users': set(),
                'last_updated': datetime.now()
            }
        
        state = self._event_states[event_id]
        
        if action == 'enter':
            state['active_users'].add(user_id)
        elif action == 'exit':
            state['active_users'].discard(user_id)
        
        state['last_updated'] = datetime.now()
        state['action'] = action
        
        # 通知订阅者
        await self._notify_event_state_subscribers(event_id, state)
        
        return state
    
    async def _notify_event_state_subscribers(self, event_id: int, state: Dict):
        """通知活动状态订阅者"""
        from apps.websocket.notification_service import NotificationService
        
        notification_service = NotificationService()
        
        for subscriber_id in self._state_subscribers.get(f'event_{event_id}', set()):
            await notification_service.send_notification(
                user_id=subscriber_id,
                title=f"活动状态更新",
                message=f"活动 {event_id} 有新活动: {state.get('action')}",
                data={'event_id': event_id, 'state': state}
            )
    
    async def update_task_state(self, task_id: int, user_id: int,
                               action: str, **kwargs) -> Dict:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            action: 动作
            **kwargs: 状态数据
            
        Returns:
            更新后的状态
        """
        if task_id not in self._task_states:
            self._task_states[task_id] = {
                'task_id': task_id,
                'status': 'active',
                'active_users': set(),
                'last_updated': datetime.now()
            }
        
        state = self._task_states[task_id]
        
        if action == 'view':
            state['active_users'].add(user_id)
        elif action == 'leave':
            state['active_users'].discard(user_id)
        
        state['last_updated'] = datetime.now()
        state['action'] = action
        
        # 通知订阅者
        await self._notify_task_state_subscribers(task_id, state)
        
        return state
    
    async def _notify_task_state_subscribers(self, task_id: int, state: Dict):
        """通知任务状态订阅者"""
        from apps.websocket.notification_service import NotificationService
        
        notification_service = NotificationService()
        
        for subscriber_id in self._state_subscribers.get(f'task_{task_id}', set()):
            await notification_service.send_notification(
                user_id=subscriber_id,
                title=f"任务状态更新",
                message=f"任务 {task_id} 有新活动: {state.get('action')}",
                data={'task_id': task_id, 'state': state}
            )
    
    def subscribe_to_state(self, state_type: str, state_id: int, user_id: int):
        """
        订阅状态更新
        
        Args:
            state_type: 状态类型（'event' 或 'task'）
            state_id: 状态ID
            user_id: 用户ID
        """
        state_key = f"{state_type}_{state_id}"
        self._state_subscribers[state_key].add(user_id)
    
    def unsubscribe_from_state(self, state_type: str, state_id: int, user_id: int):
        """
        取消订阅状态更新
        
        Args:
            state_type: 状态类型
            state_id: 状态ID
            user_id: 用户ID
        """
        state_key = f"{state_type}_{state_id}"
        self._state_subscribers[state_key].discard(user_id)
        
        if not self._state_subscribers[state_key]:
            del self._state_subscribers[state_key]
    
    def get_event_state(self, event_id: int) -> Optional[Dict]:
        """获取活动状态"""
        state = self._event_states.get(event_id)
        if state:
            state_copy = state.copy()
            state_copy['active_users'] = list(state_copy.get('active_users', set()))
            return state_copy
        return None
    
    def get_task_state(self, task_id: int) -> Optional[Dict]:
        """获取任务状态"""
        state = self._task_states.get(task_id)
        if state:
            state_copy = state.copy()
            state_copy['active_users'] = list(state_copy.get('active_users', set()))
            return state_copy
        return None
    
    async def cleanup_old_states(self, max_age: int = 3600):
        """
        清理旧的状态记录
        
        Args:
            max_age: 最大年龄(秒)
        """
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=max_age)
        
        # 清理活动状态
        old_event_states = [
            event_id for event_id, state in self._event_states.items()
            if state.get('last_updated', now) < cutoff_time
        ]
        
        for event_id in old_event_states:
            del self._event_states[event_id]
            logger.info(f"Cleaned up old event state: {event_id}")
        
        # 清理任务状态
        old_task_states = [
            task_id for task_id, state in self._task_states.items()
            if state.get('last_updated', now) < cutoff_time
        ]
        
        for task_id in old_task_states:
            del self._task_states[task_id]
            logger.info(f"Cleaned up old task state: {task_id}")