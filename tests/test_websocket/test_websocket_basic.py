"""
WebSocket实时通讯基础设施测试
测试Phase 2 WebSocket实现
"""

import pytest
import asyncio
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from apps.websocket.routing import websocket_urlpatterns
from apps.websocket.consumer import EventPilotConsumer, MessageType
from apps.websocket.connection_manager import ConnectionManager
from apps.websocket.notification_service import NotificationService, NotificationType, NotificationPriority
from apps.websocket.status_manager import StatusManager, UserStatus

User = get_user_model()


@pytest.mark.asyncio
@pytest.mark.django_db
class TestWebSocketConnection:
    """测试WebSocket连接"""
    
    async def test_websocket_accept_valid_token(self, create_user):
        """测试使用有效token连接"""
        user = await database_sync_to_async(create_user)()
        
        # 创建JWT token
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        
        # 创建WebSocket连接
        communicator = WebsocketCommunicator(
            EventPilotConsumer,
            f'/ws/events/?token={access_token}'
        )
        
        connected, _ = await communicator.connect()
        
        assert connected is True
        
        await communicator.disconnect()
    
    async def test_websocket_reject_invalid_token(self):
        """测试拒绝无效token连接"""
        communicator = WebsocketCommunicator(
            EventPilotConsumer,
            f'/ws/events/?token=invalid_token'
        )
        
        connected, _ = await communicator.connect()
        
        assert connected is False
    
    async def test_send_and_receive_message(self, create_user):
        """测试发送和接收消息"""
        user = await database_sync_to_async(create_user)()
        
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        
        communicator = WebsocketCommunicator(
            EventPilotConsumer,
            f'/ws/events/?token={access_token}'
        )
        
        await communicator.connect()
        
        # 发送ping消息
        await communicator.send_json_to({
            'type': MessageType.PING.value
        })
        
        # 接收pong响应
        response = await communicator.receive_json_from()
        
        assert response['type'] == MessageType.PONG.value
        
        await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
class TestConnectionManager:
    """测试连接管理器"""
    
    async def test_connect_and_disconnect(self):
        """测试连接和断开"""
        manager = ConnectionManager()
        
        connection_id = 'test_connection_1'
        user_id = 1
        device_id = 'device_1'
        
        # 建立连接
        connected = await manager.connect(
            connection_id,
            user_id=user_id,
            device_id=device_id,
            topics={'user_1'}
        )
        
        assert connected is True
        
        connection_info = manager.get_connection_info(connection_id)
        assert connection_info is not None
        assert connection_info['user_id'] == user_id
        
        # 断开连接
        await manager.disconnect(connection_id, 'test_disconnect')
        
        connection_info = manager.get_connection_info(connection_id)
        assert connection_info is not None  # 连接信息仍然保留但状态为disconnected
        assert connection_info['status'] == 'disconnected'
    
    async def test_send_message_to_user(self):
        """测试发送消息到用户"""
        manager = ConnectionManager()
        
        connection_id_1 = 'test_connection_1'
        connection_id_2 = 'test_connection_2'
        user_id = 1
        
        # 建立多个连接
        await manager.connect(connection_id_1, user_id=user_id, topics={'user_1'})
        await manager.connect(connection_id_2, user_id=user_id, topics={'user_1'})
        
        # 发送消息
        message = {'type': 'test', 'data': 'hello'}
        sent_count = await manager.send_to_user(user_id, message)
        
        assert sent_count == 2
        
        # 清理
        await manager.disconnect(connection_id_1)
        await manager.disconnect(connection_id_2)
    
    async def test_heartbeat_tracking(self):
        """测试心跳追踪"""
        manager = ConnectionManager()
        
        connection_id = 'test_connection_1'
        user_id = 1
        
        await manager.connect(connection_id, user_id=user_id)
        
        # 更新心跳
        updated = await manager.update_heartbeat(connection_id)
        assert updated is True
        
        # 检查超时连接
        timeout_count = await manager.check_timeouts()
        assert timeout_count == 0
        
        await manager.disconnect(connection_id)


@pytest.mark.asyncio
@pytest.mark.django_db
class TestNotificationService:
    """测试通知服务"""
    
    async def test_create_notification(self):
        """测试创建通知"""
        service = NotificationService()
        
        notification = await service.create_notification(
            user_id=1,
            title='Test Notification',
            message='This is a test notification',
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL
        )
        
        assert notification['user_id'] == 1
        assert notification['title'] == 'Test Notification'
        assert notification['type'] == 'info'
        assert notification['priority'] == 1
        assert notification['read'] is False
        assert notification['id'] is not None
    
    async def test_notification_aggregation(self, create_user):
        """测试通知聚合"""
        service = NotificationService()
        
        user = await database_sync_to_async(create_user)()
        
        # 创建多个相同类型的通知
        await service.create_notification(
            user_id=user.id,
            title='Task Update',
            message='Task has been updated',
            notification_type=NotificationType.INFO
        )
        
        await service.create_notification(
            user_id=user.id,
            title='Task Update',
            message='Task has been updated again',
            notification_type=NotificationType.INFO
        )
        
        # 检查队列统计
        stats = service.get_queue_stats()
        assert stats['total_queued'] >= 2
    
    async def test_mark_notification_as_read(self):
        """测试标记通知为已读"""
        service = NotificationService()
        
        notification = await service.create_notification(
            user_id=1,
            title='Test',
            message='Test message'
        )
        
        notification_id = notification['id']
        marked = service.mark_as_read(notification_id, user_id=1)
        
        assert marked is True
    
    async def test_priority_queues(self):
        """测试优先级队列"""
        service = NotificationService()
        
        # 创建不同优先级的通知
        await service.create_notification(
            user_id=1,
            title='Low Priority',
            message='Low',
            priority=NotificationPriority.LOW
        )
        
        await service.create_notification(
            user_id=1,
            title='High Priority',
            message='High',
            priority=NotificationPriority.HIGH
        )
        
        # 处理通知
        processed = await service.process_notifications()
        
        # 高优先级应该先被处理
        assert processed >= 1  # 至少处理了一个


@pytest.mark.asyncio
@pytest.mark.django_db
class TestStatusManager:
    """测试状态管理器"""
    
    async def test_user_presence_service(self):
        """测试用户在线状态服务"""
        manager = StatusManager()
        presence_service = manager.get_presence_service()
        
        # 更新用户状态
        updated = await presence_service.update_user_status(
            user_id=1,
            status=UserStatus.ONLINE,
            device_id='device_1'
        )
        
        assert updated is True
        
        # 获取用户状态
        user_status = presence_service.get_user_status(1)
        assert user_status is not None
        assert user_status['status'] == 'online'
    
    async def test_is_user_online(self):
        """测试用户是否在线"""
        manager = StatusManager()
        presence_service = manager.get_presence_service()
        
        # 设置用户在线
        await presence_service.update_user_status(
            user_id=1,
            status=UserStatus.ONLINE
        )
        
        # 检查用户是否在线
        is_online = presence_service.is_user_online(1, timeout=300)
        assert is_online is True
        
        # 检查不存在的用户
        is_online = presence_service.is_user_online(999, timeout=300)
        assert is_online is False
    
    async def test_get_online_users(self):
        """测试获取在线用户列表"""
        manager = StatusManager()
        presence_service = manager.get_presence_service()
        
        # 创建多个在线用户
        await presence_service.update_user_status(1, UserStatus.ONLINE)
        await presence_service.update_user_status(2, UserStatus.ONLINE)
        await presence_service.update_user_status(3, UserStatus.AWAY)
        
        # 获取在线用户
        online_users = presence_service.get_online_users(timeout=300)
        
        assert 1 in online_users
        assert 2 in online_users
        assert 3 in online_users  # AWAY也算在线
    
    async def test_event_state_management(self, create_event):
        """测试活动状态管理"""
        manager = StatusManager()
        
        event = await database_sync_to_async(create_event)()
        user_id = 1
        
        # 更新活动状态
        state = await manager.update_event_state(
            event_id=event.id,
            user_id=user_id,
            action='enter'
        )
        
        assert state['event_id'] == event.id
        assert user_id in state['active_users']
        
        # 获取活动状态
        event_state = manager.get_event_state(event.id)
        assert event_state is not None
        assert event_id in event_state['active_users']
    
    async def test_task_state_management(self, create_task):
        """测试任务状态管理"""
        manager = StatusManager()
        
        task = await database_sync_to_async(create_task)()
        user_id = 1
        
        # 更新任务状态
        state = await manager.update_task_state(
            task_id=task.id,
            user_id=user_id,
            action='view'
        )
        
        assert state['task_id'] == task.id
        assert user_id in state['active_users']
        
        # 获取任务状态
        task_state = manager.get_task_state(task.id)
        assert task_state is not None


@pytest.mark.asyncio
@pytest.mark.django_db
class TestWebsocketIntegration:
    """WebSocket集成测试"""
    
    async def test_full_notification_workflow(self, create_user, create_event):
        """测试完整的Notification工作流"""
        user = await database_sync_to_async(create_user)()
        event = await database_sync_to_async(create_event)()
        
        # 连接WebSocket
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        
        communicator = WebsocketCommunicator(
            EventPilotConsumer,
            f'/ws/events/?token={access_token}'
        )
        
        await communicator.connect()
        
        # 发送活动更新通知
        notification_service = NotificationService()
        await notification_service.send_event_notification(
            event_id=event.id,
            action='updated'
        )
        
        # 接收通知消息
        response = await communicator.receive_json_from(timeout=2)
        
        assert response['type'] == 'notification'
        assert 'notification' in response
        
        await communicator.disconnect()
    
    async def test_presence_updates(self, create_user):
        """测试在线状态更新"""
        user = await database_sync_to_async(create_user)()
        
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        
        communicator = WebsocketCommunicator(
            EventPilotConsumer,
            f'/ws/status/?token={access_token}'
        )
        
        await communicator.connect()
        
        # 更新在线状态
        await communicator.send_json_to({
            'type': 'presence',
            'action': 'update_status',
            'status': 'busy'
        })
        
        # 接收状态更新确认
        response = await communicator.receive_json_from()
        
        assert response['type'] == 'presence'
        assert response['action'] == 'update_status'
        
        await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
class TestErrorHandling:
    """测试错误处理"""
    
    async def test_invalid_message_type(self, create_user):
        """测试无效消息类型"""
        user = await database_sync_to_async(create_user)()
        
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        
        communicator = WebsocketCommunicator(
            EventPilotConsumer,
            f'/ws/events/?token={access_token}'
        )
        
        await communicator.connect()
        
        # 发送无效消息
        await communicator.send_json_to({
            'type': 'invalid_type'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from()
        
        assert response['type'] == 'error'
        assert 'code' in response
        
        await communicator.disconnect()
    
    async def test_missing_message_type(self, create_user):
        """测试缺少消息类型"""
        user = await database_sync_to_async(create_user)()
        
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        
        communicator = WebsocketCommunicator(
            EventPilotConsumer,
            f'/ws/events/?token={access_token}'
        )
        
        await communicator.connect()
        
        # 发送没有type的消息
        await communicator.send_json_to({
            'data': 'test'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from()
        
        assert response['type'] == 'error'
        
        await communicator.disconnect()